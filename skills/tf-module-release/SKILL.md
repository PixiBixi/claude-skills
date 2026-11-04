---
name: tf-module-release
description: >-
  Use right after a Terraform module MR is merged, to tag the new version and bump its callers: "fais le tag & bump module.hcl", "<n> est merge, tag". Not for Helm chart releases.
---

# Terraform module release

A module version is a signed annotated tag on the default-branch merge commit; callers pin it with `?ref=<version>` in their `.hcl` or `.tf` source. No CI job tags for you.

## 1. Tag

In the module's local clone (fetch, never check out the user's branch):

```bash
M=~/path/to/module-clone
git -C "$M" fetch origin --tags
B=$(git -C "$M" symbolic-ref --short refs/remotes/origin/HEAD)   # origin/main, origin/master...
git -C "$M" tag --sort=-v:refname | head -3      # the existing scheme: bare X.Y.Z or vX.Y.Z
git -C "$M" log --oneline -5 "$B"
```

| Change since the last tag | Bump |
|---|---|
| Removed or renamed input, new required input, resource replaced for existing callers | major |
| New optional input or output, new feature, behavior unchanged when unset | minor |
| Fix, docs, CI only | patch |

Follow the existing tag scheme exactly. Message: subject = the change in one line with the ticket key; body = what callers see, and whether bumping plans no change.

**Gate, before any command below**: confirm `$B` is the merge commit of the MR, show the tag name and message, and wait for a yes. A pushed tag is consumed immediately and is never re-pointed. Signed through `tag.gpgsign`:

```bash
VERSION=16.3.0                                   # the version chosen above, in the existing scheme
git -C "$M" tag -a "$VERSION" "$B" -F "$MSG"
git -C "$M" tag -v "$VERSION"
git -C "$M" push origin "$VERSION"
```

## 2. Find every caller

On the fetched default branch of each live repo, not the working tree (a stale checkout shows old refs):

```bash
L=~/path/to/live-repo
git -C "$L" fetch origin
git -C "$L" grep -n '<module-name>.git' "$(git -C "$L" symbolic-ref --short refs/remotes/origin/HEAD)" -- '*.hcl' '*.tf'
```

List callers in a table: repo, file, current ref. A caller more than one major behind gets its own decision, never a silent multi-major jump.

## 3. Bump MR per caller repo

- Commit `chore(<scope>): bump <module> to <version>` with the ticket key, body saying whether the plan is expected to be empty. Bump alone: an input change is its own `feat()` commit. One MR per repo (`mr-open`).
- The MR plan (`gitlab-job-triage` to read it) must match the tag message: "no change" means zero add/change/destroy on every caller unit.
- In repos that apply on merge, merging is the user's call.
