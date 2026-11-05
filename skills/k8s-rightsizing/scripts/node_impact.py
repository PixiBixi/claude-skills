#!/usr/bin/env python3
"""Estimate the node count and list-price impact of a requests/replicas change.

Reads a live cluster snapshot (kubectl get nodes/pods -o json), applies the
changes from a JSON file, and bin-packs every workload pod (DaemonSets excluded)
into the node group it runs on today. A node group is the set of nodes sharing
compute class, spot/on-demand, architecture and taints: a pod never leaves its
group in the simulation, which is how nodeSelector, tolerations and arch are
honored. Each group is packed into its most common machine type.

Usage:
  python3 node_impact.py --nodes nodes.json --pods pods.json \
      --changes changes.json [--prices prices.json] [--fill 0.75]

changes.json, keyed by "<namespace>/<workload>" (Deployment, StatefulSet...):
  {"ns/app": {"replicas": 36, "cpu": "250m", "memory": "8Gi",
              "cpu_limit": "2", "memory_limit": "8Gi", "spread": "soft"}}
Every key is optional. "spread": "soft" drops a required hostname anti-affinity.

prices.json: {"<instance-type>": <USD per node-hour>}, from fetch_prices.sh.
"""
import argparse
import json
import re
from collections import Counter, defaultdict

HOURS_PER_MONTH = 730


def cpu(v):
    if v in (None, ""):
        return 0.0
    v = str(v)
    return float(v[:-1]) / 1000 if v.endswith("m") else float(v)


def mem(v):
    """Bytes string to GiB."""
    if v in (None, ""):
        return 0.0
    v = str(v)
    for unit, factor in (("Ki", 2**10), ("Mi", 2**20), ("Gi", 2**30), ("Ti", 2**40),
                         ("k", 1e3), ("M", 1e6), ("G", 1e9), ("T", 1e12)):
        if v.endswith(unit):
            return float(v[: -len(unit)]) * factor / 2**30
    return float(v) / 2**30


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


def pack(items, cap_c, cap_m):
    """First-fit decreasing on memory then CPU, one hostname-spread set per bin."""
    bins = []
    for key, c, m, hard in sorted(items, key=lambda x: (-x[2], -x[1])):
        for b in bins:
            if b["c"] + c <= cap_c and b["m"] + m <= cap_m and not (hard and key in b["hard"]):
                break
        else:
            b = {"c": 0.0, "m": 0.0, "hard": set()}
            bins.append(b)
        b["c"] += c
        b["m"] += m
        if hard:
            b["hard"].add(key)
    return len(bins)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", required=True)
    ap.add_argument("--pods", required=True)
    ap.add_argument("--changes", required=True)
    ap.add_argument("--prices")
    ap.add_argument("--fill", type=float, default=0.75,
                    help="real packing efficiency vs ideal FFD; calibrate on a cluster already in the target state")
    a = ap.parse_args()

    nodes = {n["metadata"]["name"]: n for n in json.load(open(a.nodes))["items"]}
    pods = [p for p in json.load(open(a.pods))["items"] if p["status"].get("phase") == "Running"]
    changes = json.load(open(a.changes))
    prices = json.load(open(a.prices)) if a.prices else {}

    groups = defaultdict(lambda: {"nodes": [], "ds": defaultdict(lambda: [0.0, 0.0]), "pods": []})
    for name, n in nodes.items():
        groups[group_of(n)]["nodes"].append(name)
    node_group = {name: group_of(n) for name, n in nodes.items()}

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
        g["pods"].append((key, c, m, hard_hostname_spread(p["spec"])))
        row = before_rows.setdefault(key, {"replicas": 0, "cpu": c, "memory": m,
                                           "cpu_limit": first(p["spec"], "limits", "cpu"),
                                           "memory_limit": first(p["spec"], "limits", "memory"),
                                           "spread": "hard" if hard_hostname_spread(p["spec"]) else "soft",
                                           "groups": set()})
        row["replicas"] += 1
        row["groups"].add(node_group[n])

    missing = [k for k in changes if k not in before_rows]
    if missing:
        raise SystemExit(f"workloads not found running: {missing}")

    def node_price(n):
        lab = nodes[n]["metadata"]["labels"]
        spot = lab.get("cloud.google.com/gke-spot") == "true" or lab.get("karpenter.sh/capacity-type") == "spot"
        return prices.get(lab.get("node.kubernetes.io/instance-type", "?") + (":spot" if spot else ""))

    shapes = {}
    for gk, g in groups.items():
        if not g["pods"]:
            continue
        mtype = Counter(nodes[n]["metadata"]["labels"].get("node.kubernetes.io/instance-type", "?")
                        for n in g["nodes"]).most_common(1)[0][0]
        ref = next(n for n in g["nodes"] if nodes[n]["metadata"]["labels"].get("node.kubernetes.io/instance-type") == mtype)
        alloc = nodes[ref]["status"]["allocatable"]
        shapes[gk] = (mtype, node_price(ref), cpu(alloc["cpu"]) - g["ds"][ref][0], mem(alloc["memory"]) - g["ds"][ref][1])

    def simulate(gk, chs):
        g, (_, _, cap_c, cap_m) = groups[gk], shapes[gk]
        after = []
        for key, c, m, hard in g["pods"]:
            ch = chs.get(key, {})
            after.append((key, cpu(ch["cpu"]) if "cpu" in ch else c, mem(ch["memory"]) if "memory" in ch else m,
                          False if ch.get("spread") == "soft" else hard))
        here = Counter(k for k, *_ in g["pods"])
        for key, ch in chs.items():
            if key in here and "replicas" in ch:
                proto = next(x for x in after if x[0] == key)
                target = round(ch["replicas"] * here[key] / before_rows[key]["replicas"])
                after = [x for x in after if x[0] != key] + [proto] * target
        return pack(after, cap_c, cap_m)

    ideal_all = {gk: simulate(gk, changes) for gk in shapes}

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
        print(f'| {key} | {fmt(b["replicas"], ch.get("replicas", b["replicas"]))} '
              f'| {fmt(f"{b["cpu"]:.2f}", f"{c_after:.2f}")} | {fmt(b["cpu_limit"], ch.get("cpu_limit", b["cpu_limit"]))} '
              f'| {fmt(f"{b["memory"]:.2f}Gi", f"{m_after:.2f}Gi")} | {fmt(b["memory_limit"], ch.get("memory_limit", b["memory_limit"]))} '
              f'| {fmt(b["spread"], ch.get("spread", b["spread"]))} | {marginal} |')
        if len(b["groups"]) > 1:
            print(f"\nWARNING {key} runs in {len(b['groups'])} node groups: replica changes are applied per group pro rata.")

    print("\n## Nodes per group\n")
    print("| Group (class, capacity, arch) | Packed into | Today | Model today | After, ideal | After, at fill | $/month today | $/month after (fill to ideal) |")
    print("|---|---|---|---|---|---|---|---|")
    tot = [0.0, 0.0, 0.0]
    for gk in sorted(shapes, key=lambda k: -len(groups[k]["nodes"])):
        mtype, price, _, _ = shapes[gk]
        today, model_today, ideal = len(groups[gk]["nodes"]), simulate(gk, {}), ideal_all[gk]
        real = min(today, -(-ideal // a.fill)) if a.fill < 1 else ideal
        node_prices = [node_price(n) for n in groups[gk]["nodes"]]
        if price is None or None in node_prices:
            cost = "n/a (no price)", "n/a"
        else:
            # Removed nodes priced at the packing shape; kept nodes keep their real price.
            now = sum(node_prices) * HOURS_PER_MONTH
            hi = now - max(0, today - real) * price * HOURS_PER_MONTH
            lo = now - max(0, today - ideal) * price * HOURS_PER_MONTH
            tot[0] += now
            tot[1] += hi
            tot[2] += lo
            cost = f"{now:,.0f}", f"{hi:,.0f} to {lo:,.0f}"
        print(f"| {gk[0]}, {gk[1]}, {gk[2]} | {mtype} | {today} | {model_today} | {ideal} | {int(real)} | {cost[0]} | {cost[1]} |")
        if model_today != today:
            print(f"\nCALIBRATION {gk[0]}: model gives {model_today} nodes for today's state, cluster has {today}. "
                  "Explain the gap (mixed machine types, pending pods, scale-down lag) before trusting the after.\n")
    print(f"\nList price, USD/month: today {tot[0]:,.0f}, after {tot[1]:,.0f} to {tot[2]:,.0f} "
          f"(saving {tot[0] - tot[1]:,.0f} to {tot[0] - tot[2]:,.0f}; fill {a.fill} to ideal packing).")


if __name__ == "__main__":
    main()
