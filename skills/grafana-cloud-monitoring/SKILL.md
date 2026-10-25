---
name: grafana-cloud-monitoring
description: Use when a Grafana panel queries Google Cloud Monitoring (the cloud-monitoring datasource, plugin type stackdriver), in PromQL or native MQL mode, or when migrating panels off a stackdriver-exporter onto it. Covers a GCM panel in No data or 403, converting a Cloud Monitoring or GMP metric type to its PromQL name, quota metrics that read empty, and template variables on a GCM datasource. Triggers - "la datasource GCM a pas de data", "ils sont dans google cloud monitoring, va check", "check si des dashboards utilisent des métriques stackdriver", "migre le panel du stackdriver_exporter". Not for Prometheus or Thanos panels and general dashboard work (grafana-dashboards), or the alert rule itself (equativ-add-alert).
---

# Grafana on Google Cloud Monitoring (GCM)

For everything that is not GCM-specific, the `grafana-dashboards` skill owns it: panel schema baseline, table layout, healthy/empty states, aggregation traps and the audit tools. This file only covers what breaks **because** the datasource is Cloud Monitoring.

Grafana's `cloud-monitoring` datasource (plugin type `stackdriver`) has a PromQL editor that queries Cloud Monitoring's Prometheus-compatible endpoint, so a Prometheus panel can move onto GCP metrics almost verbatim, ratios and `absent()` fallbacks included. `sort_desc`, `label_replace`, `vector()`, `absent()` and `last_over_time` all work. What makes it fail is never the PromQL.

**Metric names.** Take the Cloud Monitoring metric type, turn the first `/` into `:` and every other special character into `_`: `cloudsql.googleapis.com/database/cpu/utilization` -> `cloudsql_googleapis_com:database_cpu_utilization`. Label names are the metric and resource labels, unchanged. Converting off a `stackdriver_exporter`: its name is `stackdriver_<resource_type>_<metric_type>`, so strip `stackdriver_` and the resource-type prefix, then put the `:` back at the first `/` boundary. Do not "fix" a name that looks wrong, `container.googleapis.com/quota/quota/nodes_per_cluster/usage` really does carry `quota` twice.

**The `:` rule does NOT apply to Google Managed Prometheus metrics, and this is the one that wastes an hour.** GMP scrapes are stored under `prometheus.googleapis.com/<name>/<kind>`, but the PromQL endpoint serves them under their **original, bare Prometheus name**. The tell is the exporter's resource type, `prometheus_target`:

| Exporter metric | The `:` rule gives | Actually works |
|---|---|---|
| `stackdriver_prometheus_target_prometheus_googleapis_com_apiserver_request_total_counter` | `prometheus_googleapis_com:apiserver_request_total_counter` -> absent | `apiserver_request_total` |
| `stackdriver_prometheus_target_prometheus_googleapis_com_scheduler_pod_scheduling_sli_duration_seconds_histogram_bucket` | `prometheus_googleapis_com:..._histogram_bucket` -> absent | `scheduler_pod_scheduling_sli_duration_seconds_bucket` |

So: `stackdriver_prometheus_target_*` -> drop the whole `prometheus_googleapis_com` segment and the trailing `_counter` / `_histogram`, keep the plain Prometheus name and its normal `_bucket` / `_count` suffixes. Everything else (`serviceruntime`, `cloudsql`, `compute`, `container`) follows the `:` rule above. Pre-flight both spellings rather than reasoning about it: the wrong one returns `-1`, not an error.

**A JSON-authored target is silently rewritten to the Builder query.** `migrateQuery()` (`grafana/grafana-cloudmonitoring-datasource`, `src/datasource.ts`) short-circuits only when the target already owns one of `metricQuery`, `sloQuery`, `timeSeriesQuery` or `timeSeriesList`. `promQLQuery` is **not** in that list, so a target carrying only `promQLQuery` becomes `queryType: timeSeriesList` with no metric type, and `filterQuery()` then drops it: the panel sends no query at all and reads "No data". It runs from `query()` as well as from the editor, so this bites at render time. Ship a `timeSeriesList` stub alongside, which is what the UI leaves behind anyway:
```json
{
  "queryType": "promQL",
  "promQLQuery": { "projectName": "$project", "expr": "...", "step": "1m" },
  "timeSeriesList": {
    "projectName": "$project", "crossSeriesReducer": "REDUCE_NONE",
    "alignmentPeriod": "cloud-monitoring-auto", "perSeriesAligner": "ALIGN_MEAN",
    "filters": [], "groupBys": []
  }
}
```
That asymmetry is why the mode works when clicked together in the UI and not when authored as JSON. `projectName` is interpolated like any string field, so a dashboard variable belongs there.

**PromQL reads one project, never a metrics scope.** The endpoint is `projects/<project>/location/global/prometheus`, and a scoping project returns an empty vector for metrics owned by the projects in its scope. `projectName` must name the project that **owns** the metric, so a dashboard spanning several (cluster quotas in one project, Cloud SQL in another) needs a different `projectName` per panel group, and a project that no variable can derive needs its own hidden `constant` variable. Widening the metrics scope does not help.

**`monitored_resource` is mandatory when a metric maps to several resource types.** Quota metrics are the usual case, and the API **rejects** the query rather than returning empty, which makes this the easy one to diagnose:
```text
must specify a label matcher on the 'monitored_resource' label because multiple
monitored resource types [consumer_quota producer_quota] are possible
```

**New-style resources carry the project as `resource_container`, not `project_id`.** `compute.googleapis.com/Location` and `container.googleapis.com/Cluster` are the ones met on quota metrics; a `project_id` matcher there matches nothing and the panel is empty with no error. Legacy resources (`consumer_quota`, `cloudsql_database`, `gce_instance`) do use `project_id`. Read the labels back before filtering rather than assuming either.

**The editor has no `legendFormat` and no instant/table query**, only Project, the expression and a min step. Two consequences:
- Legends come out as the raw label set. Reduce to a single label in the query (`max by (database_id) (...)`) and add a `renameByRegex` transformation (`.*database_id="([^"]+)".*` -> `$1`). Non-destructive: a display name that does not match is left alone.
- A table panel cannot use `format: table` + `instant`. Fold the range result with a `reduce` transformation in `seriesToRows` mode **with `labelsToFields: true`**: without it you get a single `Field` column (the label set as text) plus the reducer column, with it one column per label. Keep the query reduced to the labels you want as columns (`max by (...)`), and say in the panel description that the table is a reduced range query.

**Quota metrics publish sparsely.** An instant read of a GCP quota metric is routinely empty while `last_over_time(<metric>[6h])` returns the value. Keep the window, and do not read the empty instant panel as a broken query.

**A 403 arrives as a JSON parse error.** The plugin parses the API error body as a result, so a missing `roles/monitoring.viewer` on the target project surfaces as `ReadString: expects " or n, but found {` with the real `"code": 403` truncated at the end of the tooltip. Read the whole string before touching the query.

**Migrating a dashboard breaks its variables, not just its panels.** A GCM datasource cannot serve `label_values()`, so every `type: query` variable built on the old Prometheus metric dies with the exporter. The panels are the mechanical half. Rebuild the variables as:
- `custom` for a short, stable list (the projects that own the metric). It must be **single-select** wherever it feeds `projectName`, because PromQL and MQL both read one project.
- `textbox` defaulting to `.*` for a label filter. It survives a new label value appearing, where a `custom` list with `includeAll` silently hides it: `All` expands to the hardcoded options only, which is the "panel lies with no visible symptom" failure again.
A regex textbox works unchanged in both languages: `service=~"$service"` in PromQL, `| filter resource.service =~ '$service'` in MQL.

## Native MQL mode

Write new panels in PromQL only: Google has deprecated MQL. Before touching an existing MQL panel (migrating it to PromQL, reading its column names or label placement), read `references/mql.md`.

## Pre-flight
Check `gcx` before any Grafana call in this skill:
```bash
command -v gcx >/dev/null || { echo "install: brew install gcx"; exit 1; }
gcx config check || { echo "not ready: gcx login"; exit 1; }
```

`gcx datasources cloudmonitoring query` DOES reach a `stackdriver` datasource (structured project/metric/reducer/aligner query, not PromQL), and is the fastest way to check a metric returns data:
```bash
gcx datasources cloudmonitoring query -d <ds-uid> --project <project> \
  --metric <cloud-monitoring-metric-type> --since 1h
```
To prove a query with your own credentials rather than the datasource's service account, settle a metric name from the descriptors, or see the columns an MQL query returns, read `references/api-queries.md`.


## Common mistakes
| Symptom | Cause | Fix |
|---|---|---|
| GCM panel "No data", editor opens on Query type **Builder** | JSON target carried only `promQLQuery`, `migrateQuery` rewrote it | ship a `timeSeriesList` stub next to `promQLQuery` |
| GCM panel empty, the same expr returns series on another project | `projectName` is a scoping project, PromQL reads one project | point `projectName` at the project owning the metric |
| GCM quota query rejected outright, not empty | metric maps to several monitored resource types | add `monitored_resource="consumer_quota"` |
| GCM quota panel empty with no error at all | filtered on `project_id` for a new-style resource | filter on `resource_container` |
| GCM panel error `ReadString: expects " or n, but found {` | a 403 rendered as a parse failure | grant `roles/monitoring.viewer` to the datasource SA on that project |
| GCP quota stat empty although the quota exists | quota metrics publish sparsely, the instant read is empty | keep `last_over_time(...[6h])` |
| Converted GMP metric absent, other converted names all work | the `:` rule does not apply to `prometheus_target` metrics | use the bare Prometheus name (`apiserver_request_total`) |
| Migrated dashboard's table lost its Project / Service columns | PromQL mode cannot do `format: table`, `reduce` folds labels into one text column | set `labelsToFields: true` on the `reduce` transformation, never switch the panel to MQL |
| MQL table reads "No data" and nothing is actually wrong | MQL has no `absent()`, so no healthy-state fallback | set `fieldConfig.defaults.noValue` on the panel |
| MQL columns come out named `resource.project_id` (or `project_id`) | Grafana's label naming is not guessable | put both spellings in `renameByName`, unmatched renames no-op |
| Audit reports a GCM dashboard as having no queries | a `$.panels[*].targets[*].expr` sweep misses GCM's own query paths | also read `promQLQuery.expr` and `timeSeriesQuery.query` |
| Variables dead after moving panels to GCM | a GCM datasource cannot serve `label_values()` | rebuild as `custom` (single-select for `projectName`) or `textbox` regex |

Every one of these returns a plausible wrong answer or an empty panel rather than an error, which is why they cost hours. The PromQL itself is almost never the problem.
