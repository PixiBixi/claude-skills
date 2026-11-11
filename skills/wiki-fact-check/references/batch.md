# Batch mode

For more than 3 articles. Approving article by article does not scale, so decisions are taken once on a single table.

1. Keep a reference copy of each article before any rewrite.
2. Run the passes in parallel lots of 6, one Sonnet subagent per article, to stay under the concurrent subagent limit. Each subagent gets the full `SKILL.md` workflow and returns the report format, nothing else.
3. Collect every report into one table: article, line, severity, article quote, actual with source.
4. Get the author's decisions on that table in one round.
5. Apply the accepted fixes and commit per article, then update each ledger entry (`ledger.md`).
