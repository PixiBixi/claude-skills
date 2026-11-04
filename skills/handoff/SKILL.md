---
name: handoff
description: Write a handoff of the current session so a fresh one can pick it up after a break, while the prompt cache is still warm.
argument-hint: "What the next session will do (optional)"
disable-model-invocation: true
---

# Handoff

Run before a break of an hour or more in a long session: written now, the summary costs cache reads; after the break, the same context is re-written at the full cache-write price.

1. **Write** `~/.claude/handoffs/<YYYY-MM-DD-HHMM>-<slug>.md` (create the folder if missing), in English, at most 60 lines:
   - **Goal**: what the user is trying to get done, in their words when they gave them.
   - **State**: what is done, with links (MR and ticket URLs, commit hashes, absolute file paths). Reference artifacts, never copy their content.
   - **Open**: what is left, the next concrete action first, and every pending question to the user.
   - **Decisions**: choices already made and why, so the next session does not reopen them.
   - **Background work**: anything still running (CI, deploy, reminder) and how to check it.
   - **Skills to load**: the skills the next session needs first.
   If the user passed an argument, tailor the doc to that next task and drop what it does not need.
2. **Redact**: no token, password, secret value or customer data. Name where a secret lives, never its value.
3. **Repoint reminders**: `tickler list --due all --json`, keep `status == "open"` and `sessionId == $CLAUDE_CODE_SESSION_ID`. For each, `tickler edit <id> --fresh --prompt 'Read <absolute path> and continue from "Open"'`, and append the path to its existing notes (`tickler show <id> --json` first, then `--notes -`: notes are replaced, not appended). Their Resume then starts a new session instead of reopening this one. List them in one line.
4. **Hand over**: copy `Read <absolute path of the handoff> and continue from "Open".` to the clipboard with `pbcopy`, then tell the user in one line to run `/clear` and paste it. Done when the file exists and the clipboard holds that line.
