# Writing the game bot

The bot is the only game-specific file. It opens one phone per player, sets the game up so every screen is reachable, then loops over the players until the end screen, measuring each screen the first time it appears.

## Shape

```ts
import { expect, test, type Page } from '@playwright/test'
import { coveredBy, dialogFit, heartbeat, log, measure, openPhone, spread } from './lib.js'

test('a full game on four phones', async ({ browser }, info) => {
  const project = info.project.name
  const players: Page[] = []
  for (let i = 0; i < 4; i++) players.push(await openPhone(browser, info))
  // 1. Create the room on players[0], join with the others, pick the shortest match,
  //    turn on every option that unlocks a dialog. measure() the lobby for host and guest.

  const seen = new Set<string>()
  const turns: { spread: number; vh: number }[] = []
  const tick = heartbeat()
  let moves = 0
  while (!(await players[0]!.locator(END_SCREEN).isVisible())) {
    tick(moves)
    for (const page of players) {
      // 2. Order: open dialog, then optional calls (UNO, "check"), then a legal move,
      //    then the fallback (draw, pass). One action per page per pass.
      if (await page.locator(DIALOG).isVisible()) {
        if (!seen.has('dialog')) {
          seen.add('dialog')
          log({ project, kind: 'dialog', name: 'colour', ...(await dialogFit(page, DIALOG)) })
          await measure(page, 'dialog', info)
        }
        await page.locator(DIALOG_CHOICE).first().click()
        continue
      }
      const move = page.locator(LEGAL_MOVE)
      if ((await move.count()) > 0) {
        const s = await spread(page, BOARD_TARGET, LEGAL_MOVE)
        if (s !== null) turns.push(s)
        try {
          await move.first().click({ timeout: 2_000 })
        } catch {
          // Intercepted: a finding, not a flake. Record who covers it, then move on another way.
          log({ project, kind: 'covered', control: LEGAL_MOVE, by: await coveredBy(page, LEGAL_MOVE) })
          await move.first().dispatchEvent('click')
        }
        moves++
      }
    }
  }
  // 3. The end screen, for every player, then the per-turn summary.
  for (const page of players) log({ project, kind: 'dialog', name: 'end', ...(await dialogFit(page, END_SCREEN)) })
  await measure(players[0]!, 'end', info)
  const sorted = turns.map((t) => t.spread).sort((a, b) => a - b)
  log({
    project,
    kind: 'turns',
    moves,
    turns: turns.length,
    together: turns.filter((t) => t.spread <= t.vh).length,
    medianSpread: sorted[Math.floor(sorted.length / 2)],
    vh: turns[0]?.vh,
    unseen: ['dialog'].filter((k) => !seen.has(k)),
  })
  expect(moves).toBeGreaterThan(0)
})
```

`summary.sh` reads the `kind` values `turns`, `covered` and `dialog` with these field names: keep them.

## Traps

- Shortest match: most games default to a multi-round goal. A bot on the default runs for many rounds and the test times out before the end screen.
- Options that unlock dialogs (a swap rule, a challenge rule) are off by default: turn them on, or the dialog is never measured.
- A control whose state comes back from the server: `click()` then `expect(...).toBeChecked()`. `check()` reads the state before the server answers and fails with "Clicking the checkbox did not change its state".
- Relabelled buttons: a pending penalty often renames the fallback action ("Draw card" becomes "Take 2"). Match both with a regex, or the bot waits forever.
- One action per page per pass, then `continue`: what the bot read before an action is stale after it, and a second click in the same pass lands on a card the server has just disabled (5s timeout).
- `:has-text()` and other Playwright selectors are invalid inside `page.evaluate`: use a locator's `boundingBox()` there.
- A bot that plays the first legal move does not reach every dialog on every run. Read `unseen` and rerun rather than forcing the game state.

## Example: UNO (uno-multiplayer)

| Placeholder | Value |
| --- | --- |
| Shortest match | `A set number of rounds`, then `Single game` |
| Option unlocking a dialog | Seven-Zero (swap-target picker) |
| `DIALOG` / `DIALOG_CHOICE` | `.picker-veil` / `.swatch` or `.swap-target` |
| Optional call | `.btn-uno` when enabled; keyboard shortcut `U` when covered |
| `LEGAL_MOVE` | `.hand-card button:not([disabled])` |
| `BOARD_TARGET` | `.pile-discard` |
| Fallback | `/^(Draw card\|Take \d+)$/`, then `End turn` after a draw |
| `END_SCREEN` | `.over-veil` |

On that game the audit found the UNO button covered by the hand-sort control on the 320px-wide profiles (iPhone SE, Galaxy S9+) and on none of the wider ones.
