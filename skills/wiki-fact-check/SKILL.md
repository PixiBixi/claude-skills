---
name: wiki-fact-check
description: >-
  Use before committing a new or rewritten PixiBixi wiki article, or when asked to verify an existing one: "vérifie l'article", "fact-check", "est-ce que c'est juste", "relis avant commit". Covers claim extraction, checking against upstream source code, a freshness pass since the article's date, running snippets, batch checks and re-checks from the factcheck ledger. Not for writing or rewording (pixibixi-wiki-article).
---

# Fact-checking a wiki article

The build and markdownlint prove an article renders, nothing proves it is true. Across 9 AI-written articles, 49 claims were false, a third of them default values or borrowed numbers: syntax and flag names were almost always right, what breaks is whatever can be guessed plausibly.

The `yaml` and `json` fences are already checked by the wiki's `check-code-blocks` pre-commit hook: do not re-verify them by hand.

## Mode

- One article, never checked: the workflow below.
- Article with a `factcheck/` ledger entry: read `references/ledger.md` first, it narrows the pass to what moved.
- More than 3 articles: read `references/batch.md`.

## Workflow

Copy this checklist and tick it as you go:

```text
- [ ] 1. Date the article
- [ ] 2. Extract every claim
- [ ] 3. Verify each claim against the source
- [ ] 4. Freshness pass since the date
- [ ] 5. Run the snippets
- [ ] 6. Write the report
```

1. **Date.** Front matter, else `git log --diff-filter=A --format=%ad -- <file>`.
2. **Extract** before verifying: checking while reading misses whatever does not catch the eye. One line per claim, in 6 families:
   1. Default values of a flag, API field, config option
   2. Numbers: thresholds, ratios, gains, percentages, sizes
   3. Names of flags, metrics, YAML fields, commands, and which component owns them
   4. Behaviours: what a mechanism does, in what order, with what side effect
   5. Versions: since when, until when, GA or beta, deprecated or removed
   6. Return codes and quoted error messages
3. **Verify** each line by trying to break it: hunt the counter-example, the missing condition, the version where it stopped being true. An agent asked to "verify" otherwise confirms. For families 1, 3 and 4, read the source code, not the doc page: `references/source-checks.md` says where each answer lives and which extra checks to run (version, own config, PR titles, privileged recipes, present-tense bugs).
4. **Freshness.** Fact-checking against the source misses what shipped after the article was written (5 of about 25 corrections on one CI article). For each tool, platform and API cited, read what changed since the date: releases (`gh api repos/<o>/<r>/releases --jq '.[] | select(.published_at > "<date>") | .tag_name'` or `git tag --sort=-creatordate` in the local clone), CHANGELOG, and for GitHub its changelog and deprecation notices. Skim titles, open only what touches a claim. Hunt the time-bound words: "en preview", "bientôt", "prévu", "annoncé", "aujourd'hui", "par défaut", a quoted error message, a future date. CI and platform articles age fastest: run this step on every re-read of those.
5. **Run the snippets.** A command, config or script that can run in a throwaway container (`docker run --rm`, OrbStack) is run, not only read: one re-read found 4 bugs this way that source reading had missed.
6. **Report**, in the format below.

## Report

A report, never an edit to the article: the fix comes once the author agrees. One row per finding, all 4 fields required:

| Field | Content |
|---|---|
| `Severity` | ERROR, OUTDATED or IMPRECISE |
| `Line` | `docs/<section>/<article>.md:<n>` |
| `Article` | short quote of what the article says |
| `Actual` | the correct fact, then a verbatim quote of the source with its URL, or `path:lines @ ref` in the upstream repo |

A paraphrase inside quotation marks is a fabricated citation: copy the exact words or drop the quotes. Close with a tally: claims checked, ERROR, OUTDATED, IMPRECISE.

Severity is judged on what the reader does, not on how far the sentence is from the truth. This is where a check degrades into a rubber stamp:

- **ERROR**: a reader who acts on the sentence does the wrong thing, or takes away a guarantee that does not exist. A claim true only under an unstated condition is an ERROR ("`maxSkew: 1` guarantees one pod per node" fails once replicas outnumber nodes).
- **OUTDATED**: true in an earlier version, false in the current one. Give the date it changed, so the author sees it is not a writing mistake.
- **IMPRECISE**: the reader still does the right thing, only the wording is loose. A claim that could not be sourced lands here too, marked "source missing": it is not validated.

## Cost

About 90k to 120k tokens per article. Use Sonnet: checking that a flag exists and reading its default is pattern work. Reserve Opus for articles whose argument is a numeric chain, where the point is to notice that a calculation does not hold.
