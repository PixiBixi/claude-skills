# claude-skills

Personal [Claude Code](https://code.claude.com) skills, mostly SRE and platform engineering workflows. The repo is a plugin marketplace with two plugins:

| Plugin | Holds |
|--------|-------|
| `pixibixi` | The repo root: every skill under `skills/` |
| `wiki` | `plugins/wiki/`: skills distilled from [wiki.jdelgado.fr](https://wiki.jdelgado.fr/) articles, linked from those articles |

## Install

As a plugin (skills are namespaced, e.g. `/pixibixi:mr-open`):

```bash
claude plugin marketplace add PixiBixi/claude-skills
claude plugin install pixibixi@pixibixi
# or only the wiki skills
claude plugin install wiki@pixibixi
```

In one step from a session: `/plugin install wiki --marketplace PixiBixi/claude-skills`.

As user-level skills with their short names, from a clone (what the [dotfiles](https://github.com/PixiBixi/dotfiles) `init_mac.sh` does):

```bash
git clone https://github.com/PixiBixi/claude-skills.git ~/Documents/perso/git/claude-skills
for skill_dir in ~/Documents/perso/git/claude-skills/skills/*/ ~/Documents/perso/git/claude-skills/plugins/*/skills/*/; do
    ln -sfn "$skill_dir" ~/.claude/skills/"$(basename "$skill_dir")"
done
```

Use one or the other, not both: each skill would load twice.

## Skills

| Skill | Use |
|-------|-----|
| `addressing-gitlab-review-comments` | Address, reply to and resolve GitLab MR review threads |
| `charting-grafana-metrics` | Plot Grafana / Prometheus series to a PNG |
| `claude-usage-audit` | Analyse Claude Code token usage from local transcripts |
| `confluence` | confluence-cli reference (upstream) |
| `gitlab-job-triage` | Triage a failed GitLab job or pipeline, read a Terraform plan |
| `grafana-cloud-monitoring` | Google Cloud Monitoring panels in Grafana |
| `grafana-dashboards` | Grafana dashboard house rules, PromQL, lint and usage audits |
| `incident-response` | Run a production incident, postmortem, runbook |
| `jira-cli` | jira-cli reference (upstream) |
| `k8s-rightsizing` | Size Kubernetes requests and limits from real usage |
| `mr-open` | Signed per-scope commits, then open or update an MR / PR |
| `pixibixi-wiki-article` | Write an article for wiki.jdelgado.fr |
| `reviewing-thanos-deployments` (`wiki`) | Review a Thanos deployment against the wiki's production rules |
| `rss-digest` | Catch up on a FreshRSS backlog as a digest |
| `scoping-a-website` | Scope a website before design or code |
| `tf-module-release` | Tag a Terraform module and bump its callers |
| `ticket-conventions` | Conventions for Jira / GitLab tickets and MR descriptions |
| `wiki-fact-check` | Fact-check a wiki article before commit |

## Development

| Command | Does |
|---------|------|
| `make validate` | `claude plugin validate` on the manifests |
| `make check-anchors` | Check that the wiki URLs and anchors cited by the `wiki` plugin skills exist on the live site (also run weekly by CI) |
| `make check` | Dry-run diff of upstream-mirrored skills |
| `make update-skills` | Sync upstream-mirrored skills, one commit per skill |
| `pre-commit install --hook-type pre-commit --hook-type commit-msg` | Enable the hooks after cloning |

A skill whose `SKILL.md` carries a `source:` frontmatter field mirrors an upstream file and is overwritten by `make update-skills`. Skills without it are authored here.

Reference bundled files through `${CLAUDE_SKILL_DIR}`, never a `~/.claude/skills/...` path: the skill may run from a clone or from a plugin cache.
