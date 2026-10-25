# Native MQL mode: deprecated, existing panels only
**Google has deprecated MQL: write every new panel in PromQL**, and when you touch an existing MQL panel, migrate it to PromQL rather than extending it. A usage/limit/ratio table costs 3 PromQL targets plus a `merge` where MQL did it in one, which is the price of staying on the supported language. What follows is here to read and migrate the MQL panels that still exist.

Label placement is not guessable, read it off the descriptors: metric labels are `metric.<key>` (from `metricDescriptors`), resource labels are `resource.<key>` (from `monitoredResourceDescriptors/<type>`). For `consumer_quota` that is `metric.quota_metric` against `resource.project_id` / `resource.service` / `resource.location`.

```text
{
  fetch consumer_quota::serviceruntime.googleapis.com/quota/allocation/usage
  | within 6h
  | group_by [resource.project_id, resource.service, resource.location, metric.quota_metric], max(val())
  ;
  fetch consumer_quota::serviceruntime.googleapis.com/quota/limit
  | within 6h
  | group_by [resource.project_id, resource.service, resource.location, metric.quota_metric], min(val())
}
| join
| value [usage: val(0), limit: val(1), ratio: val(0)/val(1)]
| filter resource.service =~ '$service'
| filter ratio > 0.8
```
`{A ; B} | join` pairs the two streams on their common labels, `| value [...]` names the output columns, and `| filter` / `| top 10, ratio` chain after it on those names. Chained `| filter` steps are fine. The `| within 6h` belongs on each `fetch`, not at the end.

The target shape, and note there is **no stub to ship** here: `timeSeriesQuery` *is* in `migrateQuery()`'s short-circuit list, unlike `promQLQuery`.
```json
{
  "queryType": "timeSeriesQuery",
  "timeSeriesQuery": {
    "projectName": "$project_id", "graphPeriod": "disabled", "query": "<MQL>"
  }
}
```
Two things to expect on the panel side:
- **Column names.** Whether Grafana exposes a label as `resource.project_id` or `project_id` is not worth a guess: put **both spellings** in the `organize` transformation's `renameByName`. An unmatched rename is a no-op, so the worst case is a raw column name, never a broken panel. The natural column order MQL returns is already the label order of your `group_by` followed by the `value` columns, so drop `indexByName` rather than fighting it.
- **MQL has no `absent()`**, so none of the healthy-state recipes above port. A `| filter ratio > 0.8` table reads "No data" when everything is fine. Use `fieldConfig.defaults.noValue` on the panel (`"No quota above 80%"`) as the equivalent.

Prove a filter actually filters before trusting an empty panel: run it at a threshold you know is crossed (`> 0.3`) and check rows come back.
