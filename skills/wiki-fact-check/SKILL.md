---
name: wiki-fact-check
description: >-
  Use before committing a new or rewritten PixiBixi wiki article, or when asked to verify an existing one: "vérifie l'article", "fact-check", "est-ce que c'est juste", "relis avant commit". Not for writing or rewording (pixibixi-wiki-article).
---

# Fact-checking a wiki article

## Overview

The build and markdownlint prove an article **renders**. Nothing proves it is **true**. This skill covers that gap.

Measured across 9 AI-written articles: 49 false claims, 17 of them default values or numbers borrowed from upstream. Syntax and flag names were almost always right. What breaks is whatever can be guessed plausibly.

**REQUIRED BACKGROUND:** this skill checks prose. The `yaml` and `json` fences are already covered by the repo's `check-code-blocks` pre-commit hook, so do not re-verify them by hand.

## What a verification pass produces

A report, never an edit to the article. The fix comes afterwards, once the author agrees.

Every finding carries **4 required fields**:

| Field | Content |
|---|---|
| `Severity` | ERROR, OUTDATED or IMPRECISE (see the rubric) |
| `Line` | `docs/<section>/<article>.md:<n>` |
| `Article` | short quote of what the article says |
| `Actual` | the correct fact, followed by its source |

The `Actual` field carries a **verbatim quote** of the source plus its URL, or a `file:line` in the upstream repository. A paraphrase presented inside quotation marks is a fabricated citation: copy the exact words, or drop the quotation marks.

Close with a tally: claims checked, ERROR, OUTDATED, IMPRECISE.

## The severity rubric

This is where a verification degrades into a rubber stamp. The test is **what the reader does**, not how far the sentence is from the truth:

- **ERROR**: a reader who acts on the sentence does the wrong thing, or takes away a guarantee that does not exist.
- **OUTDATED**: true in an earlier version, false in the current one.
- **IMPRECISE**: the reader still does the right thing, only the wording is loose.

A claim that holds only under an unstated condition is an **ERROR**, not an imprecision. "`maxSkew: 1` guarantees one pod per node" is false as soon as replicas outnumber nodes: the reader takes away a drain guarantee they do not have.

## Extract before verifying

Verifying while reading misses whatever does not catch the eye. List first, check second.

Sweep the article and pull out **every** claim in these 6 families, each becoming one line to check:

1. **Default values** of a flag, an API field, a config option
2. **Numbers**: thresholds, ratios, performance gains, percentages, sizes
3. **Names** of flags, metrics, YAML fields, commands, and which component owns them
4. **Behaviours**: what a mechanism does, in what order, with what side effect
5. **Versions**: since when, until when, GA or beta, deprecated or removed
6. **Return codes** and quoted error messages

Families 1 and 2 pay best: together they accounted for a third of the observed errors.

## Source beats documentation

Upstream docs lag or lie more often than expected, and precisely on the subtle points.

Two cases hit on the same day:

- Thanos `query-frontend.md` still claims only range queries go through the frontend. `roundtrip.go` has defined a `newInstantQueryTripperware` since 0.35.
- An agent reported `thanos_bucket_store_series_gate_duration_seconds`. The real name is `..._gate_queries_duration_seconds`, readable only in `pkg/gate/gate.go`.

So for any claim in families 1, 3 and 4: **go read the source**, not just the doc page. A default value lives in the flag declaration, a metric name in its definition, a behaviour in the function implementing it.

When docs and code disagree, code wins and the report flags the contradiction.

More checks the source makes cheap:

- **Version.** A behaviour can be true for the version deployed and false for the reader's. Find when it changed (`git log -S` on the function, then `git tag --contains`) and flag a claim that does not date itself. Thanos receive RF=2 needed both replicas to ack until v0.37 (PR #7669), then a quorum of 1.
- **Our own config.** A passage describing the author's setup (layers, flags, ApplicationSet shape) is checked against the current repo, not memory: the Thanos ApplicationSet had been rewritten since the article was drafted. Check the version actually running too (`kubectl get pods -o jsonpath` on the image), since a chart default can pin an older release than the repo suggests.
- **A fix named in a PR title.** "Fixed in vX" is verified by reading what the fix computes, not what it is called. Thanos `ObjectStorageConfigHash` (PR #6880) hashes the caching-bucket config plus its file path, not the object-store config, so 2 stacks sharing one backend still collide in v0.42.
- **A Kubernetes recipe that runs privileged.** Ask which namespace it changes and whether a native path exists. A `sysctl -w` initContainer in a `hostNetwork` pod rewrites the node for every host-network process, since the kubelet rejects `net.*` sysctls there (`pkg/kubelet/sysctl/allowlist.go`). In a pod with its own netns, `securityContext.sysctls` does it unprivileged, safe or unsafe per `safe_sysctls.go`, and Pod Security `baseline` admits only the safe ones.
- **A third-party bug described in the present tense.** Search upstream for a later fix (`git log --grep`, `git tag --contains`) and compare with the deployed version: Dragonfly emits its zero-valued eviction counters since v2.0.0 (PR #8052), while prod ran v1.37.

## Freshness pass

A claim true on the day the article was written can be false today. On the GitHub hardening article, 5 of about 25 corrections were changes that shipped in the 6 weeks after writing: a runner image going GA, a preview feature, a reworded validator message, an endpoint sunset, a renamed API host. Fact-checking against the source alone does not catch them unless the check starts from the article's date.

1. Take the article's date: the front matter, else `git log --diff-filter=A --format=%ad -- <file>`.
2. List every tool, platform and API the article cites.
3. For each one, read what changed since that date: the releases (`gh api repos/<o>/<r>/releases --jq '.[] | select(.published_at > "<date>") | .tag_name'`, or `git tag --sort=-creatordate` in the local clone), the CHANGELOG, and for GitHub itself the [changelog](https://github.blog/changelog/) and deprecation notices. Skim titles, open only what touches a claim.
4. Hunt the time-bound words: "en preview", "bientôt", "prévu", "annoncé", "aujourd'hui", "par défaut", a quoted error message, a date in the future.

A changed fact goes in the report like any other, tagged OUTDATED with the date it changed, so the author sees it is not a writing mistake. CI and platform articles age fastest: run the pass on every re-read of those, not only on a new article.

## Try to break it, not to confirm it

An agent asked to "verify this article" confirms the article. The posture that finds anything is the opposite: for each claim, actively hunt the counter-example, the missing condition, the version where it stopped being true.

A claim that could not be sourced is not validated. It goes out as IMPRECISE, noting the source is missing, and the author decides.

## Quick reference

| Question | Where the answer lives |
|---|---|
| Default value of a flag | The flag declaration under `cmd/`, or generated help. Never a blog post |
| Exact name of a metric | Its definition (`promauto.New...`), including any prefix added by a `WrapRegistererWithPrefix` |
| A Kubernetes API field and its default | `kubernetes/api`, `core/v1/types.go`, the field comment |
| GA or beta | `pkg/features/kube_features.go` for Kubernetes, the CHANGELOG otherwise |
| A borrowed performance number | The originating PR or benchmark. An unsourced round number is almost always wrong |
| A CLI behaviour | The subcommand's code first, the docs second |

## Common mistakes

- **Verifying while reading** instead of extracting first: whatever does not catch the eye never gets checked.
- **Filing something as a nuance when it changes what the reader does.** The rubric decides, not the impression.
- **Quoting from memory.** A paraphrase inside quotation marks passes an invention off as a source.
- **Stopping at the docs** for a default value or a metric name.
- **Deriving a tool's output from its source when running it is cheap.** An agent rebuilt the `renovate-config-validator` message from `validation.ts` and quoted a warning, while the run prints an error first, and that error text is the one that stayed stable across versions. Run the tool, paste what it prints.
- **Re-checking YAML and JSON fences**, already covered by the repo hook.
- **Fixing on the spot.** The report goes to the author first: when a number comes from their own measurement, only they know which one is right.

## Cost

A pass runs about 90k to 120k tokens per article.

Use **Sonnet**: checking that a flag exists and reading its default is pattern work. Reserve **Opus** for articles whose argument is a numeric chain, where the point is to notice that a calculation does not hold.
