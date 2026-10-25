# claude-skills

[![pre-commit](https://github.com/PixiBixi/claude-skills/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/PixiBixi/claude-skills/actions/workflows/pre-commit.yml)
[![wiki-anchors](https://github.com/PixiBixi/claude-skills/actions/workflows/wiki-anchors.yml/badge.svg)](https://github.com/PixiBixi/claude-skills/actions/workflows/wiki-anchors.yml)
[![License](https://img.shields.io/github/license/PixiBixi/claude-skills)](LICENSE)
[![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-D97757)](https://code.claude.com)

**SRE and platform engineering skills for [Claude Code](https://code.claude.com), shaped by daily production use.**

Incidents, MRs, Grafana dashboards, Kubernetes sizing, Terraform releases, tickets: each skill packs a workflow that Claude loads only when the task matches, so you type `fais la MR` or paste a failed job URL and it follows the same steps every time.

## Quick start

```bash
claude plugin marketplace add PixiBixi/claude-skills
# every skill, namespaced as /pixibixi:<skill>
claude plugin install pixibixi@pixibixi
# or only the skills linked from wiki.jdelgado.fr
claude plugin install wiki@pixibixi
```

From inside a session: `/plugin install wiki --marketplace PixiBixi/claude-skills`.

| Plugin | Holds |
|--------|-------|
| `pixibixi` | Every skill under `skills/` |
| `wiki` | `plugins/wiki/`: skills distilled from [wiki.jdelgado.fr](https://wiki.jdelgado.fr/) articles, linked from those articles |

## Skills

### Git, MRs and CI

| Skill | Use | Triggered by |
|-------|-----|--------------|
| `mr-open` | Signed per-scope commits, then open or update an MR / PR | "fais la MR", "commit & push" |
| `addressing-gitlab-review-comments` | Address, reply to and resolve GitLab MR review threads | "réponds à la review" |
| `gitlab-job-triage` | Triage a failed GitLab job or pipeline, read a Terraform plan | a pasted job URL, "pourquoi ça a fail ?" |
| `tf-module-release` | Tag a Terraform module and bump its callers | "tag une nouvelle version" |

### Observability and incidents

| Skill | Use | Triggered by |
|-------|-----|--------------|
| `incident-response` | Run a production incident, postmortem, runbook | "c'est down en prod", "postmortem" |
| `grafana-dashboards` | Grafana dashboard house rules, PromQL, lint and usage audits | a `/d/<uid>` URL, "dash", "panel" |
| `grafana-cloud-monitoring` | Google Cloud Monitoring panels in Grafana | a GCM panel reading No data |
| `charting-grafana-metrics` | Plot Grafana / Prometheus series to a PNG | a before/after graph for a ticket or MR |
| `reviewing-thanos-deployments` (`wiki`) | Review a Thanos deployment against the wiki's production rules | Thanos Helm values, a Receive OOM |

### Kubernetes and FinOps

| Skill | Use | Triggered by |
|-------|-----|--------------|
| `k8s-rightsizing` | Size Kubernetes requests and limits from real usage | "on peut réduire cette RAM ?" |
| `claude-usage-audit` | Analyse Claude Code token usage from local transcripts | "analyse mon usage token" |

### Tickets and docs

| Skill | Use | Triggered by |
|-------|-----|--------------|
| `ticket-conventions` | Conventions for Jira / GitLab tickets and MR descriptions | "fais un ticket", "commente le ticket" |
| `jira-cli` | jira-cli reference (upstream mirror) | any Jira task |
| `confluence` | confluence-cli reference (upstream mirror) | any Confluence page |

### Writing and web

| Skill | Use | Triggered by |
|-------|-----|--------------|
| `pixibixi-wiki-article` | Write an article for wiki.jdelgado.fr | "écris un article wiki" |
| `wiki-fact-check` | Fact-check a wiki article before commit | "fact-check", "relis avant commit" |
| `scoping-a-website` | Scope a website before design or code | "refais mon site" |
| `rss-digest` | Catch up on a FreshRSS backlog as a digest | "fais-moi le digest RSS" |

## Install from a clone

To get the short skill names (`/mr-open` instead of `/pixibixi:mr-open`), symlink each skill into `~/.claude/skills`, as the [dotfiles](https://github.com/PixiBixi/dotfiles) `init_mac.sh` does:

```bash
REPO=~/Documents/perso/git/claude-skills
git clone https://github.com/PixiBixi/claude-skills.git "$REPO"
for skill_dir in "$REPO"/skills/*/ "$REPO"/plugins/*/skills/*/; do
    ln -sfn "$skill_dir" ~/.claude/skills/"$(basename "$skill_dir")"
done
```

> [!WARNING]
> Use the plugin or the symlinks, not both: each skill would load twice.

## Development

| Command | Does |
|---------|------|
| `pre-commit install --hook-type pre-commit --hook-type commit-msg` | Enable the hooks after cloning |
| `make validate` | `claude plugin validate` on the manifests |
| `make check-anchors` | Check that the wiki URLs and anchors cited by the `wiki` plugin skills exist on the live site (also run weekly by CI). `--site <dir>` checks a local MkDocs build instead, which the wiki CI runs before each deploy |
| `make check` | Dry-run diff of upstream-mirrored skills |
| `make update-skills` | Sync upstream-mirrored skills, one commit per skill |

A skill whose `SKILL.md` carries a `source:` frontmatter field mirrors an upstream file and is overwritten by `make update-skills`. Skills without it are authored here. Writing rules for new skills are in [AGENTS.md](AGENTS.md).

## License

[Apache 2.0](LICENSE)
