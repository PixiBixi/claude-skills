#!/usr/bin/env python3
"""Estimate the node count and list-price impact of a requests/replicas change.

Reads a live cluster snapshot (kubectl get nodes/pods -o json), applies the
changes from a JSON file, and bin-packs every workload pod (DaemonSets excluded)
into the node group it runs on today. A node group is the set of nodes sharing
compute class, spot/on-demand, architecture and taints: a pod never leaves its
group, which is how nodeSelector, tolerations and arch are honored.

Blast radius: one node never holds more than --max-share of a workload's
replicas (at least 1), and a required hostname anti-affinity means 1.

Usage:
  python3 node_impact.py --nodes nodes.json --pods pods.json \
      --changes changes.json [--prices prices.json] [--fill 0.75] \
      [--max-share 0.25] [--shapes c4d-highmem-8,c4d-standard-8]

changes.json, keyed by "<namespace>/<owner>" (Deployment, StatefulSet...):
  {"ns/app": {"replicas": 36, "cpu": "250m", "memory": "8Gi", "spread": "soft"}}
Every key is optional. "spread": "soft" drops a required hostname anti-affinity.

prices.json, from fetch_prices.py: {"<type>[:spot]": {"usd_h", "vcpu", "mem_gib", "arch"}}.
--shapes compares other machine types per group (same arch, priced in prices.json).
"""
import argparse
import json
import math
import re
from collections import Counter, defaultdict

HOURS_PER_MONTH = 730


def cpu(v):
    if v in (None, ""):
        return 0.0
    v = str(v)
    return float(v[:-1]) / 1000 if v.endswith("m") else float(v)


def mem(v):
    """Quantity string to GiB."""
    if v in (None, ""):
        return 0.0
    v = str(v)
    for unit, factor in (("Ki", 2**10), ("Mi", 2**20), ("Gi", 2**30), ("Ti", 2**40),
                         ("k", 1e3), ("M", 1e6), ("G", 1e9), ("T", 1e12)):
        if v.endswith(unit):
            return float(v[: -len(unit)]) * factor / 2**30
    return float(v) / 2**30


def gke_allocatable(vcpu, mem_gib):
    """GKE kube-reserved + eviction threshold, applied to the kernel-visible memory."""
    cap = mem_gib * 0.98
    tiers = ((4, 0.25), (4, 0.20), (8, 0.10), (112, 0.06), (math.inf, 0.02))
    left, reserved = cap, 0.0
    for size, rate in tiers:
        take = min(left, size)
        reserved += take * rate
        left -= take
    c_tiers = ((1, 0.06), (1, 0.01), (2, 0.005), (math.inf, 0.0025))
    left, c_res = vcpu, 0.0
    for size, rate in c_tiers:
        take = min(left, size)
        c_res += take * rate
        left -= take
    return vcpu - c_res, cap - reserved - 0.1


def pod_requests(spec):
    c = sum(cpu(k.get("resources", {}).get("requests", {}).get("cpu")) for k in spec["containers"])
    m = sum(mem(k.get("resources", {}).get("requests", {}).get("memory")) for k in spec["containers"])
    for k in spec.get("initContainers", []):
        r = k.get("resources", {}).get("requests", {})
        c, m = max(c, cpu(r.get("cpu"))), max(m, mem(r.get("memory")))
    return c, m


def first(spec, kind, key):
    for k in spec["containers"]:
        v = k.get("resources", {}).get(kind, {}).get(key)
        if v:
            return v
    return "-"


def workload(pod):
    ns = pod["metadata"]["namespace"]
    refs = pod["metadata"].get("ownerReferences") or []
    if not refs:
        return ns, pod["metadata"]["name"], None
    kind, name = refs[0]["kind"], refs[0]["name"]
    if kind == "ReplicaSet":
        kind, name = "Deployment", re.sub(r"-[a-z0-9]{6,10}$", "", name)
    return ns, name, kind


def hard_hostname_spread(spec):
    terms = (spec.get("affinity", {}).get("podAntiAffinity", {})
             .get("requiredDuringSchedulingIgnoredDuringExecution") or [])
    return any(t.get("topologyKey") == "kubernetes.io/hostname" for t in terms)


def group_of(node):
    labels = node["metadata"]["labels"]
    taints = sorted(f'{t["key"]}={t.get("value", "")}:{t["effect"]}'
                    for t in node["spec"].get("taints", [])
                    if not t["key"].startswith("node.kubernetes.io/"))
    return (
        labels.get("cloud.google.com/compute-class")
        or labels.get("karpenter.sh/nodepool")
        or labels.get("cloud.google.com/gke-nodepool")
        or labels.get("eks.amazonaws.com/nodegroup")
        or labels.get("kubernetes.azure.com/agentpool", "-"),
        "spot" if labels.get("cloud.google.com/gke-spot") == "true"
        or labels.get("karpenter.sh/capacity-type") == "spot" else "on-demand",
        labels.get("kubernetes.io/arch", "-"),
        ",".join(taints),
    )


def pack(items, cap_c, cap_m, per_node_max):
    """First-fit decreasing on memory then CPU, capped per workload per node.

    Returns (bins, worst) where worst is the highest share of one workload's
    replicas sitting on a single node."""
    bins = []
    for key, c, m in sorted(items, key=lambda x: (-x[2], -x[1])):
        if c > cap_c or m > cap_m:
            return math.inf, 1.0
        for b in bins:
            if b["c"] + c <= cap_c and b["m"] + m <= cap_m and b["n"][key] < per_node_max[key]:
                break
        else:
            b = {"c": 0.0, "m": 0.0, "n": Counter()}
            bins.append(b)
        b["c"] += c
        b["m"] += m
        b["n"][key] += 1
    total = Counter(k for k, *_ in items)
    worst = max((b["n"][k] / total[k] for b in bins for k in b["n"] if total[k] > 1), default=0.0)
    return len(bins), worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", required=True)
    ap.add_argument("--pods", required=True)
    ap.add_argument("--changes", required=True)
    ap.add_argument("--prices")
    ap.add_argument("--fill", type=float, default=0.75,
                    help="real packing efficiency vs ideal FFD; calibrate on a cluster already in the target state")
    ap.add_argument("--max-share", type=float, default=0.25,
                    help="blast radius: max share of a workload's replicas on one node (min 1 pod)")
    ap.add_argument("--shapes", default="", help="comma-separated machine types to compare per group")
    a = ap.parse_args()

    nodes = {n["metadata"]["name"]: n for n in json.load(open(a.nodes))["items"]}
    pods = [p for p in json.load(open(a.pods))["items"] if p["status"].get("phase") == "Running"]
    changes = json.load(open(a.changes))
    prices = {k: (v if isinstance(v, dict) else {"usd_h": v})
              for k, v in (json.load(open(a.prices)) if a.prices else {}).items()}
    extra_shapes = [s for s in a.shapes.split(",") if s]

    groups = defaultdict(lambda: {"nodes": [], "ds": defaultdict(lambda: [0.0, 0.0]), "pods": []})
    node_group = {name: group_of(n) for name, n in nodes.items()}
    for name, gk in node_group.items():
        groups[gk]["nodes"].append(name)

    before_rows = {}
    for p in pods:
        n = p["spec"].get("nodeName")
        if n not in nodes:
            continue
        g = groups[node_group[n]]
        ns, name, kind = workload(p)
        c, m = pod_requests(p["spec"])
        if kind == "DaemonSet":
            g["ds"][n][0] += c
            g["ds"][n][1] += m
            continue
        key = f"{ns}/{name}"
        hard = hard_hostname_spread(p["spec"])
        g["pods"].append((key, c, m))
        row = before_rows.setdefault(key, {"replicas": 0, "cpu": c, "memory": m, "hard": hard,
                                           "cpu_limit": first(p["spec"], "limits", "cpu"),
                                           "memory_limit": first(p["spec"], "limits", "memory"),
                                           "groups": set()})
        row["replicas"] += 1
        row["groups"].add(node_group[n])

    missing = [k for k in changes if k not in before_rows]
    if missing:
        raise SystemExit(f"workloads not found running: {missing}")

    def price_of(mtype, spot):
        return prices.get(mtype + (":spot" if spot else ""), {}).get("usd_h")

    def node_price(n):
        lab = nodes[n]["metadata"]["labels"]
        spot = lab.get("cloud.google.com/gke-spot") == "true" or lab.get("karpenter.sh/capacity-type") == "spot"
        return price_of(lab.get("node.kubernetes.io/instance-type", "?"), spot)

    shapes = {}
    for gk, g in groups.items():
        if not g["pods"]:
            continue
        mtype = Counter(nodes[n]["metadata"]["labels"].get("node.kubernetes.io/instance-type", "?")
                        for n in g["nodes"]).most_common(1)[0][0]
        ref = next(n for n in g["nodes"] if nodes[n]["metadata"]["labels"].get("node.kubernetes.io/instance-type") == mtype)
        alloc = nodes[ref]["status"]["allocatable"]
        ds_c, ds_m = g["ds"][ref]
        shapes[gk] = {"mtype": mtype, "usd_h": node_price(ref), "ds": (ds_c, ds_m),
                      "cap": (cpu(alloc["cpu"]) - ds_c, mem(alloc["memory"]) - ds_m)}

    def per_node_max(chs):
        out = {}
        for key, row in before_rows.items():
            ch = chs.get(key, {})
            replicas = ch.get("replicas", row["replicas"])
            hard = row["hard"] and ch.get("spread") != "soft"
            out[key] = 1 if hard else max(1, math.floor(replicas * a.max_share))
        return out

    def items_after(gk, chs):
        g = groups[gk]
        after = []
        for key, c, m in g["pods"]:
            ch = chs.get(key, {})
            after.append((key, cpu(ch["cpu"]) if "cpu" in ch else c, mem(ch["memory"]) if "memory" in ch else m))
        here = Counter(k for k, *_ in g["pods"])
        for key, ch in chs.items():
            if key in here and "replicas" in ch:
                proto = next(x for x in after if x[0] == key)
                target = round(ch["replicas"] * here[key] / before_rows[key]["replicas"])
                after = [x for x in after if x[0] != key] + [proto] * target
        return after

    def simulate(gk, chs, cap=None):
        return pack(items_after(gk, chs), *(cap or shapes[gk]["cap"]), per_node_max(chs))[0]

    def at_fill(ideal, today):
        return min(today, math.ceil(ideal / a.fill)) if a.fill < 1 else ideal

    ideal_all = {gk: simulate(gk, changes) for gk in shapes}

    # 1. Workloads
    print("## Workloads\n")
    print("| Workload | Replicas | CPU req | CPU limit | Mem req | Mem limit | Spread | Nodes saved by this change alone |")
    print("|---|---|---|---|---|---|---|---|")
    fmt = lambda b, a2: b if str(b) == str(a2) else f"{b} → {a2}"
    for key in sorted(changes):
        b, ch = before_rows[key], changes[key]
        without = {k: v for k, v in changes.items() if k != key}
        marginal = sum(simulate(gk, without) - ideal_all[gk] for gk in b["groups"] if gk in shapes)
        c_after = cpu(ch["cpu"]) if "cpu" in ch else b["cpu"]
        m_after = mem(ch["memory"]) if "memory" in ch else b["memory"]
        spread = "hard" if b["hard"] else "soft"
        print(f'| {key} | {fmt(b["replicas"], ch.get("replicas", b["replicas"]))} '
              f'| {fmt(f"{b["cpu"]:.2f}", f"{c_after:.2f}")} | {fmt(b["cpu_limit"], ch.get("cpu_limit", b["cpu_limit"]))} '
              f'| {fmt(f"{b["memory"]:.2f}Gi", f"{m_after:.2f}Gi")} | {fmt(b["memory_limit"], ch.get("memory_limit", b["memory_limit"]))} '
              f'| {fmt(spread, ch.get("spread", spread))} | {marginal} |')
        if len(b["groups"]) > 1:
            print(f"\nWARNING {key} runs in {len(b['groups'])} node groups: replica changes are applied per group pro rata.")

    # 2. Nodes per group, current machine type
    print(f"\n## Nodes per group (blast radius: at most {a.max_share:.0%} of a workload per node)\n")
    print("| Group (class, capacity, arch) | Packed into | Today | Model today | After, ideal | After, at fill | $/month today | $/month after (fill to ideal) |")
    print("|---|---|---|---|---|---|---|---|")
    tot = [0.0, 0.0, 0.0]
    for gk in sorted(shapes, key=lambda k: -len(groups[k]["nodes"])):
        s = shapes[gk]
        today, model_today, ideal = len(groups[gk]["nodes"]), simulate(gk, {}), ideal_all[gk]
        real = at_fill(ideal, today)
        node_prices = [node_price(n) for n in groups[gk]["nodes"]]
        if s["usd_h"] is None or None in node_prices:
            cost = "n/a (no price)", "n/a"
        else:
            # Removed nodes priced at the packing shape; kept nodes keep their real price.
            now = sum(node_prices) * HOURS_PER_MONTH
            hi = now - max(0, today - real) * s["usd_h"] * HOURS_PER_MONTH
            lo = now - max(0, today - ideal) * s["usd_h"] * HOURS_PER_MONTH
            tot[0] += now
            tot[1] += hi
            tot[2] += lo
            cost = f"{now:,.0f}", f"{hi:,.0f} to {lo:,.0f}"
        print(f"| {gk[0]}, {gk[1]}, {gk[2]} | {s['mtype']} | {today} | {model_today} | {ideal} | {real} | {cost[0]} | {cost[1]} |")
        if model_today != today:
            print(f"\nCALIBRATION {gk[0]}: model gives {model_today} nodes for today's state, cluster has {today}. "
                  "Explain the gap (mixed machine types, pending pods, scale-down lag, blast-radius cap) before trusting the after.\n")
    print(f"\nList price, USD/month: today {tot[0]:,.0f}, after {tot[1]:,.0f} to {tot[2]:,.0f} "
          f"(saving {tot[0] - tot[1]:,.0f} to {tot[0] - tot[2]:,.0f}; fill {a.fill} to ideal packing).")

    # 3. Gain per change: structural first, each row on top of the previous ones.
    def fleet(chs):
        return {gk: (lambda i: (i, at_fill(i, len(groups[gk]["nodes"]))))(simulate(gk, chs)) for gk in shapes}

    def usd(prev, cur, idx):
        return sum((prev[gk][idx] - cur[gk][idx]) * (shapes[gk]["usd_h"] or 0) * HOURS_PER_MONTH for gk in shapes)

    alone = {k: sum(simulate(gk, {x: v for x, v in changes.items() if x != k}) - ideal_all[gk] for gk in shapes)
             for k in changes}
    order = sorted(changes, key=lambda k: (not ({"spread", "replicas"} & changes[k].keys()), -alone[k], k))
    print("\n## Gain per change, applied in this order\n")
    print("| # | Change | Nodes removed (fill to ideal) | USD/month saved (fill to ideal) |")
    print("|---|---|---|---|")
    applied, prev = {}, fleet({})
    for i, key in enumerate(order, 1):
        applied[key] = changes[key]
        cur = fleet(applied)
        d_real = sum(prev[g][1] - cur[g][1] for g in shapes)
        d_ideal = sum(prev[g][0] - cur[g][0] for g in shapes)
        print(f"| {i} | {key} {json.dumps(changes[key])} | {d_real} to {d_ideal} "
              f"| {usd(prev, cur, 1):,.0f} to {usd(prev, cur, 0):,.0f} |")
        prev = cur

    # 4. Other machine types, after all changes, same arch and blast-radius cap.
    if not extra_shapes:
        return
    print(f"\n## Machine types, after all changes (blast radius {a.max_share:.0%} per node)\n")
    print("| Group | Machine | Nodes, ideal | Nodes, at fill | USD/month (fill to ideal) | Worst share of one workload on a node | One node lost = share of the group |")
    print("|---|---|---|---|---|---|---|")
    for gk in sorted(shapes, key=lambda k: -len(groups[k]["nodes"])):
        spot = gk[1] == "spot"
        today = len(groups[gk]["nodes"])
        ds_c, ds_m = shapes[gk]["ds"]
        for mtype in [shapes[gk]["mtype"], *extra_shapes]:
            spec = prices.get(mtype + (":spot" if spot else ""), {})
            if mtype != shapes[gk]["mtype"] and spec.get("arch") not in (None, gk[2]):
                continue
            if mtype == shapes[gk]["mtype"]:
                cap = shapes[gk]["cap"]
            elif "vcpu" in spec:
                ac, am = gke_allocatable(spec["vcpu"], spec["mem_gib"])
                cap = (ac - ds_c, am - ds_m)
            else:
                print(f"| {gk[0]} | {mtype} | no spec in prices.json | | | |")
                continue
            n, worst = pack(items_after(gk, changes), *cap, per_node_max(changes))
            if n == math.inf:
                print(f"| {gk[0]} | {mtype} | a pod does not fit | | | |")
                continue
            real = math.ceil(n / a.fill) if a.fill < 1 else n
            usd_h = spec.get("usd_h")
            cost = "n/a" if usd_h is None else f"{real * usd_h * HOURS_PER_MONTH:,.0f} to {n * usd_h * HOURS_PER_MONTH:,.0f}"
            print(f"| {gk[0]}, {gk[1]}, {gk[2]} | {mtype} | {n} | {real} | {cost} | {worst:.0%} | {1 / n:.0%} |")


if __name__ == "__main__":
    main()
