## Jira: never invent a custom field id

`customfield_10001` in one instance is not the same field in another. A wrong id either errors or **writes to the wrong field silently**, which nobody finds out about until an audit.

If a field id is not already known, discover it read-only before writing:

- MCP: `getJiraProjectIssueTypesMetadata`, then `getJiraIssueTypeMetaWithFields` for the target issue type. Returns the ids, which are required, and the allowed values.
- REST on a known-good ticket: `GET /rest/api/3/issue/<TICKET-ID>?expand=names` shows the ids next to human names, plus the exact value shape already stored in that field.

Report what you found (name, id, value shape, allowed values) before using it. Value shapes differ per field: plain string, `{"value": ...}`, `{"id": ...}`, or an array. Take the shape from what discovery returned, never from a guess.

If discovery is blocked, say so and create the ticket without that field, or stop if it is required. Do not retry with a guessed id.

Sprint and other Agile board fields are usually not writable through the create API. When one cannot be set, create the ticket and say it needs a manual move on the board, rather than failing the whole write.

## Sizing

For a PE ticket, use the `sp-suggest` skill to see the Story Points of the most similar past tickets before proposing an estimate. It is a lookup, not a prediction: it anchors the number, the estimate stays yours.
