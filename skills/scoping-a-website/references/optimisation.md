# Optimising a site whose design is kept

Rounds 1 to 3 of the interview are already answered: skip them.

## Round 0, measured

Payload sizes (compressed), DOM node count, eager rendering (offscreen sections, autoplaying loops), external dependencies (fonts, CDNs, trackers), cache headers (hashed assets `immutable`, HTML short-lived). Read minification and fingerprinting from the built HTML and files, not from the config: an MkDocs site had `minify_css: true` and shipped every own stylesheet unminified, because `css_files` was empty. Run `scripts/sitemap-inventory.py` on the live site so the plan covers every template, not just the home page.

Field data first: real-user p75 from CrUX tells whether visitors suffer before any lab run says why. The keyless quota is shared and answers 429, so pass `key=` (a Google Cloud API key) or read pagespeed.web.dev; a low-traffic site has no CrUX record, say so and rely on the lab.

```bash
curl -sS "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=$URL&strategy=mobile&category=performance&key=$PSI_KEY" > psi.json
jq -r '.loadingExperience | .overall_category, (.metrics | to_entries[] | "\(.key) p75=\(.value.percentile)")' psi.json
```

## One question call

With the multiple-choice question tool, in the user's language:
- Target: rendering and smoothness, network weight, mobile, accessibility and SEO.
- Performance budget, recommended default first: the Core Web Vitals "good" thresholds at p75 on mobile (LCP 2.5 s, INP 200 ms, CLS 0.1), with TBT 200 ms in the lab as the INP proxy.
- Build-step tolerance: none, a minifier, a full SSG.

## The brief

States the measured costs, the plan in order, the commit scopes, and a before/after measurement as the first and last steps. Get an explicit OK, then apply `prototype-checklist.md` to the changed parts.

## Measuring

- Lighthouse 13.x or later: 12.2 returns errors on the LCP-element and layout-shift audits with current Chrome, which hides what the LCP actually is.
- A local server (`python3 -m http.server`, `serve`) sends Lighthouse uncompressed files, so the local LCP is inflated. Validate the budget on the deployed site.
- Run 3 times and keep the median. Before reading a report, check `runtimeError` and that `finalDisplayedUrl` is the page asked for: a redirect, a dropped query string or a WAF/bot challenge means the wrong page was measured.
- Read where the time goes, not the score: a 94 hid a 1.8 s LCP render delay on a zero-JS Starlight site. The insight subparts come from the observed (unthrottled) trace while the LCP metric is simulated, so compare their ratios, never their sum with the LCP figure. Pull the breakdowns from the JSON report:
  ```bash
  jq -r '.audits["lcp-breakdown-insight"].details.items[]?.items[]? | "\(.subpart) \(.duration)"' lh.json
  jq -r '.audits["mainthread-work-breakdown"].details.items[] | "\(.groupLabel) \(.duration|floor)ms"' lh.json
  ```
- Render delay dominating the LCP while Script Evaluation stays small means CSS and layout, not JS: merge or inline critical render-blocking stylesheets, and put `content-visibility: auto` on offscreen sections of long pages (high Style & Layout, high Speed Index).
- On an ad-funded site, measure twice: as is, then with the ad and consent stack blocked (`--blocked-url-patterns='*doubleclick*' ...`, domains from `third-parties-insight`). The gap is what the owner cannot fix in code. Lighthouse sees the pre-consent page, so a visitor who accepts loads more.
- Any large fetch started at boot, even in `requestIdleCallback`, counts in Lighthouse's simulated mobile LCP. Start non-critical payloads on first interaction.
- A bimodal simulated LCP (2.6 s on some runs, 4.9 s on others), or one far above `observedLargestContentfulPaint` in the `metrics` audit, is the simulation, not the page: one wiki observed 0.17 to 0.42 s on every run. Rerun 3 times with `--throttling-method=devtools` (real throttling) before hunting a cause in the code. Validate CLS there too: a late font swap gave 0.107 under devtools and 0.018 simulated.

## Fonts

- A late swap shifting text: preload the latin subset first, then measure with devtools throttling. If it still shifts, `font-display: optional` or a metric-adjusted fallback (`size-adjust`), and say what each costs.
- A lighter font that drops an axis or a weight is a design change: validate it with the screenshots before recommending it. Dropping `opsz` from Source Serif 4 cut 122 KB to 51 KB, but widened every heading and reflowed the mobile h1 from 3 to 4 lines.
- Google Fonts serves the full variable file whenever the request names `opsz`, whatever range or fixed value is asked: no lighter optical-size variant comes from there, only a self-hosted instance (fontTools `instancer`).
