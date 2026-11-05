---
name: k8s-rightsizing
description: >-
  Use when sizing CPU/memory requests, limits or replicas of a Kubernetes workload from its real usage, and before any edit of a `resources:` block in Helm values: "on peut réduire cette RAM ?", "combien consomme <workload>", "il a déjà été OOMKilled ?", "combien de nodes on gagne ?", "ça coûte combien ?", a FinOps cut, a cluster with many idle nodes. Not for CI runners or a live OOM incident.
---

# K8s rightsizing

A recommendation is the peak of real usage over a representative window plus headroom: never the average, never a number read off someone else's dashboard. A requests cut is only worth an MR if it removes nodes: the bill is nodes, not requests.

## 1. Find the series

Federated or global stores usually drop the raw `container_*` and `kube_pod_container_*` series and keep **recording rules** instead (pod-level CPU rate, memory usage, OOM counters). If the project CLAUDE.md names them, use those first. Otherwise list what exists for the target cluster before any real query: an empty result means wrong series or datasource, not zero usage.

```bash
gcx metrics query -d <uid> 'count by (__name__) ({__name__=~".*(cpu_usage|memory_usage|working_set|oom).*", <cluster_label>="<cluster>"})' -o json --jq '[.data.result[].metric.__name__]'
```

| Need | Source |
|---|---|
| Pod-level usage, single-container pods (most cases) | the recording rules on the global store |
| Per-container split (sidecars), requests, raw OOM reason | the raw or per-cluster datasource |

Check the oldest point before claiming a 30-day window: retention differs per store.

**The window starts when the workload took its real traffic.** After a migration, a cutover or a ramp-up, find that date first (traffic series of the app, or the old platform going to zero) and measure from it: idle days before it dilute every quantile.

## 2. Measure

Always filter on cluster and namespace (and container on raw series): an unfiltered `[7d]` range over a multi-cluster store can OOM the queriers. Window `[7d]` by default, `[14d]` when the load is weekly-cyclic. Raw series shown; swap in the recording rule names where they exist.

| Signal | PromQL (instant query) |
|---|---|
| Memory peak | `max by (pod, container) (max_over_time(container_memory_working_set_bytes{C,N,X}[7d]))` |
| Memory p99 | `max by (container) (quantile_over_time(0.99, container_memory_working_set_bytes{C,N,X}[7d]))` |
| CPU p95 of the 5m rate | `max by (container) (quantile_over_time(0.95, rate(container_cpu_usage_seconds_total{C,N,X}[5m])[7d:5m]))` (on a rate recording rule, drop the inner `rate`) |
| CPU peak | same with `max_over_time` |
| Current requests / limits | `max by (container, resource) (kube_pod_container_resource_requests{C,N,X})`, same on `..._limits` |
| OOMKills | `max by (pod) (max_over_time(kube_pod_container_status_last_terminated_reason{C,N,X,reason="OOMKilled"}[7d]))` |
| Restarts | `max by (pod) (increase(kube_pod_container_status_restarts_total{C,N,X}[7d]))` |

Live spec for comparison: `kubectl klens reqlim --context <ctx> -n <ns> --by-owner`.

## 3. Recommend

| Value | Default rule (state the factors in the answer; a team standard overrides them) |
|---|---|
| Memory request | p99 working set x 1.15, rounded up to 64Mi |
| Memory limit | max(peak x 1.25, request); equal to the request for a fixed heap (JVM, `GOMEMLIMIT`); never below the window peak |
| Memory with a RAM-backed volume (`emptyDir.medium: Memory`, tmpfs cache) | request and limit >= its `sizeLimit` + process RSS peak, whatever the measured peak: a cache not yet full has not shown its size |
| CPU request | p95 of the 5m rate x 1.2, rounded to 50m |
| CPU limit | follow the repo (unset stays unset); if set, at least 2 x the request |
| Any OOMKill or memory restart in the window | no memory cut, report it first |
| Under 7 days of data, a recent rollout, or a known peak outside the window | say so, widen the window, or do not recommend |
| HPA on `Utilization` for that resource | the target is a % of the request: lowering the request scales the workload out, recompute the target |

Also check the replicas and the spread rules: a required `podAntiAffinity` on `kubernetes.io/hostname` makes the node count >= replicas, whatever the requests. It is often the biggest lever and no requests cut can beat it.

## 4. Node impact: the gate

Nodes come from requests, through the placement constraints. Before proposing an MR, simulate the node count with the constraints that decide where each pod may land:

| Constraint | Where to read it | Effect |
|---|---|---|
| Compute class, node pool, Karpenter NodePool | `nodeSelector` / node labels | pods only pack with their group |
| Spot vs on-demand | node label (`cloud.google.com/gke-spot`, `karpenter.sh/capacity-type`) | separate groups, separate prices |
| Architecture | `kubernetes.io/arch` node label, arm64 taint, image manifest | an amd64-only image never packs onto arm64 nodes |
| Taints / tolerations | `node.spec.taints` | dedicated pools stay dedicated |
| Required anti-affinity, `topologySpreadConstraints` | pod spec | floor of one node per replica (hostname) or per zone |
| DaemonSets, kube-reserved | node allocatable minus DaemonSet requests | the room left per node |
| Local SSD, GPU, max pods per node | machine type, `allocatable.pods` | some pods need a specific shape |
| Zonal PV (StatefulSet) | PV `nodeAffinity` | the pod is pinned to its zone |

Run the simulator on a live snapshot. It groups nodes by class, capacity type, arch and taints, packs each group into its most common machine type, and prices with the GCE catalog (list price, no CUD: a rough order of magnitude):

```bash
S=<scratchpad>
kubectl --context <ctx> get nodes -o json > "$S/nodes.json"
kubectl --context <ctx> get pods -A -o json > "$S/pods.json"
python3 scripts/fetch_prices.py "$S/nodes.json" > "$S/prices.json"   # GKE; elsewhere write {"<instance-type>": usd_per_hour}
python3 scripts/node_impact.py --nodes "$S/nodes.json" --pods "$S/pods.json" \
  --changes "$S/changes.json" --prices "$S/prices.json" --fill 0.75
```

`changes.json` is keyed `<namespace>/<owner>` (Deployment name, StatefulSet name): `{"ns/app": {"cpu": "250m", "memory": "2Gi", "replicas": 10, "spread": "soft"}}`.

- **Calibration first.** "Model today" must equal "Today" per group. A gap means a constraint the model misses (mixed shapes, pending pods, scale-down lag): explain it before trusting the after.
- **Range, not a point.** The ideal packing is a floor; real schedulers and the cluster autoscaler pack worse (spread preferences, 50% scale-down threshold). `--fill` defaults to 0.75; calibrate it on a cluster already in the target state when one exists.
- **Structural changes first.** Simulate the spread and replicas changes alone, then add the requests cuts on top: under a hard one-node-per-replica floor every requests cut shows 0, which hides what it saves once the floor is gone.
- **A change with 0 in "Nodes saved by this change alone" gets no MR.** Report it in the table as no gain and stop there, unless the user asks for it anyway.
- **Scale-down is progressive.** Soft spread and lower requests do not move running pods: the autoscaler drains underused nodes over hours.

## 5. Output

The answer is, in this order:

1. One line: environment, window (start date and why), pod- or container-level.
2. The workload table from `node_impact.py`, with the measured p95/p99/peak added per row: replicas, CPU req/limit, memory req/limit, before → after, and the nodes each change saves alone.
3. The node table per group: today, after (fill to ideal), machine type, list price per month today and after.
4. The gain per change (one MR each), from the "Gain per change" table: nodes and USD/month each MR adds on top of the previous ones, structural changes first, so the rows sum to the total. A 1-node row is within bin-packing noise: say so.
5. The total saving in USD/month (list price), and the changes rejected for zero node gain.

## 6. Ship

Values change in the owning GitOps repo (`mr-open`), one MR per workload with a node gain; its description carries the node and cost lines. Then check the rollout. Offer a reminder at +7 days (`tickler`) to re-measure, count the nodes and look for OOMKills.
