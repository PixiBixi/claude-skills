---
name: ticket-conventions
description: >-
  Use BEFORE every write to a tracker or an MR/PR description, even if loaded earlier: "fais un ticket", "ouvre une issue", "ouvre la MR" (with mr-open), "description de la MR", "poste ça sur PE-xxxx". For an Equativ Jira ticket, load equativ-jira next for fields, sprint and ADF. Not for jira-cli syntax (jira-cli).
---

# Ticket conventions

Command syntax lives in `jira-cli`. This file is the layer above it: what a write must look like, and the five ways a tracker write goes wrong (approval gate, Jira markdown, length, custom field ids, glab flags that hang).

## The approval gate

**Never create or comment before an explicit yes in the current turn.** Show the target and the full body together in one message, then stop:

```text
Ticket:  PE-1234  (https://<instance>/browse/PE-1234)
Comment:
<the exact text, in full>
```

The user is confirming the wording **and the target**, not the intent, so the gate applies even when they asked for the ticket in the first place. Showing the id next to the body is what catches a comment aimed at the wrong ticket, which is visible to the whole team the moment it lands.

Show the full body, never a three-line excerpt: an excerpt hides exactly the mistakes the gate exists to catch. If the user edits the wording, show the revised draft and wait again. One approval covers one write.

A change the user asks for on text already approved (a bold title, a reworded line, a typo) is applied directly, then shown: the request is the approval. The gate covers new content and new targets, not re-confirming the user's own instruction.

When the user says go, create the ticket yourself. Never ask whether a small change deserves a ticket.

After posting, output the direct link so it can be verified: `<baseUrl>/browse/<TICKET-ID>?focusedCommentId=<commentId>`.

## Jira: markdown, never wiki markup

Pass `contentFormat: "markdown"` and write plain markdown. Jira wiki markup (`h2.`, `[text|url]`, `{code}`) does **not** render through the REST API or the MCP tools: it lands as literal text in the ticket and nothing errors.

- `###` (h3) is the largest heading allowed, in issues and in comments. Never h1 or h2.
- `- ` for bullets, `1. ` for numbered lists, `[text](url)` for links.
- Default to short and scannable: one or two sentences of context, then a bulleted list, then the must-know note. Skip headings entirely unless the comment genuinely has several sections.
- Never paste credentials, tokens, or internal hostnames into a ticket.

## Length: the description too, not just the comment

**60 lines is the hard ceiling for a ticket description, and it is a ceiling, not a target.** The real rule is proportionality: the description matches the size of the change, never the size of the investigation. Resizing a PVC is three lines - what, on which cluster, why now. It is not 60, and it is not 20. Only a ticket that genuinely carries a root-cause analysis, several linked changes and an open decision gets near the ceiling.

A description is read by someone deciding whether to pick the ticket up. Keep the problem in a sentence, the root cause with its one decisive number, what changed with its links, the open risk, the decision criterion.

Cut everything you needed to measure to get there. Per-metric tables, enumerations of what you scanned, the list of every artefact you touched, measurement traps you hit on the way, corrections of your own earlier numbers. That material belongs in the MR, where it serves the review, or in the dashboard you built. A section title taken from your investigation rather than from the problem is the tell that the section should go.

Same restraint on an edit: re-read the whole description after amending it and cut, rather than appending a section each time something new is learned.

## MR/PR descriptions

Same ceiling spirit, shorter still: what and why, test evidence, links. No narrated investigation ("trop verbose", "raconte pas ta vie"). English always, even in a French session. Never hard-wrap prose. After adding commits, update the description.

## Jira custom fields and sizing

Read `references/jira-fields.md` before setting any Jira custom field (ids differ per instance, a wrong id writes to the wrong field silently) and before proposing Story Points.

## GitLab issues

Read `references/gitlab-issues.md` before `glab issue create` (the flags that hang: `--yes`, `--no-editor`).
