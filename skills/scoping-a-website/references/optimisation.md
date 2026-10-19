# Optimising a site whose design is kept

Rounds 1 to 3 of the interview are already answered: skip them.

## Round 0, measured

Payload sizes (compressed), DOM node count, eager rendering (offscreen sections, autoplaying loops), external dependencies (fonts, CDNs, trackers), cache headers (hashed assets `immutable`, HTML short-lived). Run `scripts/sitemap-inventory.py` on the live site so the plan covers every template, not just the home page.

## One question call

With the multiple-choice question tool, in the user's language:
- Target: rendering and smoothness, network weight, mobile, accessibility and SEO.
- Performance budget: LCP and TBT figures, recommended default first.
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
