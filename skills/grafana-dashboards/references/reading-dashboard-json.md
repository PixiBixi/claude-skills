# Reading dashboard JSON: what the linter cannot decide

Two things it cannot decide for you:

**An empty `[]` from a JSONPath is not proof of absence.** It also means "you asked for the wrong shape". `$.panels[*].targets[*].datasource.uid` returns `[]` both when no target carries a datasource *and* when every target carries one as a plain string, the two are indistinguishable. Query the parent (`.datasource`) and look at what comes back before concluding anything is missing.

**A `$.panels[*].targets[*].expr` sweep is blind to every GCM panel.** A fully migrated Cloud Monitoring dashboard comes back with no queries at all under that path, which reads as "these panels were abandoned" when they are in fact working: the query lives in `promQLQuery.expr` (PromQL mode) or `timeSeriesQuery.query` (MQL mode) instead. Any audit that answers "which dashboards still use metric X" has to read all three paths; `scripts/grafana_metric_usage.py` already does (see `references/audits-and-renames.md`). Cross-check the target count with `$.panels[*].targets[*].queryType` before reading an empty result as an empty dashboard.

**`gcx dashboards get -o json` returns a `dashboard.grafana.app/v2` manifest, where every v1 path is empty.** Check `.apiVersion` first, then read and patch these instead:

| What | v2 path |
|---|---|
| Panels, keyed `panel-<id>` | `.spec.elements[<name>].spec` (`id`, `title`, `description`, `vizConfig`) |
| Queries | `.spec.elements[<name>].spec.data.spec.queries[].spec.query.spec.expr` / `.legendFormat` |
| Rows and positions | `.spec.layout.spec.rows[].spec` (`title`) then `.layout.spec.items[].spec` (`x`, `y`, `width`, `height`, `element.name`) |
| Variables | `.spec.variables[].spec` (`name`, `options`, `current`), type in `.kind` |

A new panel needs both an `elements` entry and a `GridLayoutItem` referencing it; an element no row references is not drawn. Drop `.status` before pushing.
