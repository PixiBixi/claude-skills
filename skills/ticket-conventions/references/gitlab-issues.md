## GitLab issues: the flags that hang

```bash
glab issue create --title "..." --description "$(cat <tempfile>)" --label a,b --yes --no-editor
```

- **`--yes`**: without it, `glab` waits for a submit confirmation keypress nobody can send. It reads as a hung tool call, not as a stuck prompt.
- **`--no-editor`**: without it, `glab` opens `$EDITOR` for the description, same outcome.
- There is no `--description-file`. Write the body to a temp file first, then read it into `--description`, so newlines and backticks survive the shell.
