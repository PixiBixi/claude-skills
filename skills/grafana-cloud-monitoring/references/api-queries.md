# Cloud Monitoring API pre-flight

For a PromQL-syntax pre-flight, or to prove the query as your own credentials rather than the datasource's service account (which proves the query and the metric name, never the permissions), hit the Cloud Monitoring API directly instead:
```bash
curl -s -G -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  --data-urlencode 'query=count(<metric>) or on() vector(-1)' \
  "https://monitoring.googleapis.com/v1/projects/<project>/location/global/prometheus/api/v1/query"
```
To settle a metric name, list what the project actually exports, which is faster and safer than any doc:
```bash
curl -s -G -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  --data-urlencode 'filter=metric.type = starts_with("container.googleapis.com/quota")' \
  'https://monitoring.googleapis.com/v3/projects/<project>/metricDescriptors'
```
Use the descriptors API rather than a regex on the name: `__name__=~"..."` is rejected with `=~ is an unsupported matchtype for the __name__ label`.

MQL is a different endpoint, a POST on v3, and it is worth running because the response tells you the column names the panel will get (`labelDescriptors` and `pointDescriptors`):
```bash
curl -s -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" -d '{"query": "<MQL>"}' \
  "https://monitoring.googleapis.com/v3/projects/<project>/timeSeries:query"
```
