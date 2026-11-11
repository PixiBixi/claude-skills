# Re-check and the ledger

Every checked article has a ledger entry in the wiki repo, so a re-check only reads what moved since the last pass.

## Entry format

Path: `factcheck/<path under docs>.md`.

| Front matter key | Content |
|---|---|
| `article` | the article path |
| `checked` | date of the last pass |
| `commit` | the fix commit of that pass |
| `sources` | list of `repo`, `path`, `lines`, `ref`, `commit` (clone in `~/Documents/work/src`) |
| `unpinned` | claims whose source could not be pinned to a file and commit |

The body is the last report. Write sources as `path:lines @ ref` in the report so the pins can be extracted. Lint the entry like any `.md`.

## Before re-checking

Run from the wiki repo:

```bash
uv run scripts/factcheck_stale.py docs/...   # --fetch refreshes the source clones first
```

It lists the articles whose text changed since `commit`, and the pinned sources that gained upstream commits after `checked`. Re-check only those, and inside them only the changed lines, the claims citing a moved source, and the `unpinned` claims. An article without an entry gets a full pass.

## After the fix commit

Rewrite the entry: new `checked` and `commit`, each source pinned to the full commit read, the new report as body.
