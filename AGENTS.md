# AGENTS.md

Guidance for coding agents writing or editing skills in this repository. Usage and install are in `README.md`; commit bodies carry the history behind each rule (`git log --format='%h %s%n%b' -- skills/<name>`).

## Layout

```text
skills/<name>/
├── SKILL.md            # frontmatter + workflow, the only file always read
├── references/*.md     # recipes and traps, loaded on demand from SKILL.md
├── scripts/            # bundled tooling, called via ${CLAUDE_SKILL_DIR}
└── evals/              # evals.json, optional trigger-eval.json
```

Every directory under `skills/` is deployed, no registration needed. Add a row to the README skills table when adding a skill.

A skill distilled from a wiki.jdelgado.fr article goes under `plugins/wiki/skills/<name>/` instead, so readers install it without the personal skills. The article links to it through its `skill:` front matter key. Cite wiki sections as full URLs with their anchor, or as a letter declared `- T = <url>` then `T #anchor`: `make check-anchors` only verifies those forms.

## Upstream mirrors

A SKILL.md with a `source:` frontmatter field mirrors an upstream file (`confluence`, `jira-cli`). `make update-skills` overwrites its body and re-injects `source:`, one commit per skill. Never add local rules to a mirror: they would be wiped on the next sync. Put them in a separate layer skill instead, as `ticket-conventions` does on top of `jira-cli`. Mirrors are exempt from the writing rules below.

## Frontmatter and description

- Authored skills carry only `name` and `description`.
- The description is the only thing that decides whether the skill loads. Shape: `Use when <situation>`, then the phrases actually typed (`Triggers - "fais la MR", "ouvre la MR"`), an optional `Covers ...` scope sentence, then `Not for <near miss> (<sibling skill>)`.
- Keep trigger phrases in the language they are typed in, French or mixed, even though the body is English. Translating them breaks discovery.
- No workflow steps in the description: a description that summarises the process gets followed instead of the body.
- Never write a colon followed by a space in an unquoted YAML description, it breaks the parse. Use `Triggers -`, a comma, parentheses, or a folded `description: >`.
- A skill that failed to trigger gets its description fixed here and committed, never patched with a memory. Add the phrasing that was actually used: real prompts beat imagined ones.

## Scope and size

- One skill per task domain. A description spanning two domains matches badly for both: split into two narrow skills with a pointer each way.
- Keep together sections that serve the same task, even when the file grows.
- SKILL.md holds the workflow, typically 40 to 120 lines. When it grows, move recipes, query catalogues and trap lists into `references/` and link them from the step that needs them.
- Test for what belongs in this public repo: "is this true outside our setup". Org-only facts (hosts, projects, team rules) go in the org CLAUDE.md or a private skill.

## Body

- English, except `pixibixi-wiki-article` whose body is the wiki's own French style rules.
- Give each rigid rule its reason, and prefer a required output shape over a list of prohibitions. A bare rule gets read as a word list instead of a criterion.
- Mechanical checks go in a script, the prose keeps only the judgment calls.
- A skill must not contain the faults it bans, and must not state a gotcha nobody verified. Fix skills from real use: when work contradicts a skill, update the skill in the same session.
- Cross-reference other skills by name in backticks, with the load order (`load grafana-dashboards first`) and a link back from the other side.

## Scripts

- Resolve bundled files with `${CLAUDE_SKILL_DIR}`, never `~/.claude/skills/...` and never a relative path: the skill runs from a clone or a plugin cache, and the shell cwd is never the skill directory.
- Define output paths explicitly in the run block. `CLAUDE_SCRATCHPAD` is not set by Claude Code.
- Python is stdlib only. A skill that needs a dependency builds its own venv under `${CLAUDE_SKILL_DIR}/.venv` (see `charting-grafana-metrics`).
- Shell scripts pass `shellcheck -o all`.
- No default host, email or ticket key: this repo is public. Read config from env vars with no default and exit with a clear message when one is missing.
- Shared helpers are copied across skills, since each skill must install alone, and imported within a skill.
- A script whose output gates a destructive decision never reports a verdict on incomplete data: exit 2 for "no verdict", not 0.
- Treat remote input as untrusted: restrict to the expected host and scheme, cap the size.
- Temp and cache files carry the pid (and thread) in their name: parallel scans share the directory.

## Evals

- `evals/evals.json`: `{skill_name, evals: [{id, prompt, expected_output, files}]}`.
- `evals/trigger-eval.json`: `[{query, should_trigger}]`, with near misses that must not trigger.
- Add a trigger eval when a description is rewritten for a triggering problem. An eval case must discriminate between versions of the skill: a case every version passes proves nothing.

## Writing rules

Enforced by pre-commit and the `.claude/wordlist-guard.json` hook config:

- No em dash, en dash or bullet character.
- No hard-wrapped prose.
- Inclusive terms (allowlist/blocklist, primary/replica, placeholder).

## Commits and checks

- Conventional Commits scoped to the skill: `fix(mr-open):`, `feat(k8s-rightsizing):`, one skill per commit. Older history uses `chore(claude):`, do not copy it.
- Signed commits, author `PixiBixi@users.noreply.github.com`.
- `pre-commit run --all-files` and `make validate` before pushing.
- Cross-references use bare names, which resolve with the symlink install. Under the plugin install, skills are namespaced (`pixibixi:mr-open`).
