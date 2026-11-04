---
name: auditing-mobile-layout
description: Play a web app or browser game through on emulated iPhone and Android, portrait and landscape, and measure the layout.
disable-model-invocation: true
---

# Auditing a mobile layout

## Overview

Plays the app on six emulated phones and records geometry, never pixels: overflow, tap targets, text size, dialogs that do not fit, controls covered by others, and how far apart two things the player must see together are. An audit records every breach and keeps going; a regression spec fails on the first. Measure first, then pick which breaches deserve a spec.

## Profiles

iPhone SE (320x568), iPhone 15, iPhone 15 landscape on WebKit; Galaxy S9+ (320 wide), Pixel 7, Pixel 7 landscape on Chromium. The 320px and landscape profiles are where layouts break: a 390px-only check misses them. For a multiplayer game, use the largest table size, so every rail has its real height.

## Run

The specs need the app's own `@playwright/test`, so they run from a directory inside the repo, never committed.

```bash
REPO=/path/to/the/app
AUDIT=${REPO}/.mobile-audit                 # specs, excluded from git
OUT=/path/to/scratchpad/mobile-audit        # rows, progress, screenshots
mkdir -p "${AUDIT}" "${OUT}"
cp "${CLAUDE_SKILL_DIR}"/scripts/*.ts "${AUDIT}/"
cd "${REPO}"
echo '.mobile-audit/' >> "$(git rev-parse --git-path info/exclude)"   # also right in a worktree
npx playwright install webkit chromium-headless-shell
```

1. Build the app and start its production server in the background on a port of its own, keeping its PID, then `until nc -z 127.0.0.1 <port>; do sleep 0.5; done`. A stale build is an old app under a new test. Stop it with `kill <pid>`: a `pkill -f` on the server's path also kills the server of any other session working on a sibling app.
2. Write `${AUDIT}/game.spec.ts` from `references/game-bot.md`, the only game-specific file. Skip it for an app with no flow beyond its URLs.
3. In the background, first one profile, then all six:

```bash
cd "${REPO}"
AUDIT_DIR="${OUT}" AUDIT_BASE_URL=http://127.0.0.1:<port> AUDIT_PATHS=/ \
  npx playwright test -c .mobile-audit/playwright.config.ts --project 'iPhone SE'
```

4. "Is it stuck?": `tail -1 "${OUT}/progress.log"`, one line per move. A loop that stops writing for 30s throws with the move number.
5. `bash "${CLAUDE_SKILL_DIR}/scripts/summary.sh" "${OUT}"`, then stop the server.
6. Move `${AUDIT}` to the scratchpad (`mv "${AUDIT}" "${OUT}/specs"`) before any lint or commit: a linter run over `.` (`eslint .`) parses it and fails. Copy it back to rerun.

## What counts

| Measure | Breach |
| --- | --- |
| `overflowX` | any element past the viewport edge |
| `covered` | a tap on a control lands on another element |
| `dialog` | a button of the dialog is off screen |
| `turns` | the move and its target never on one screen (`together` = 0) |
| text inputs | under 16px: iOS Safari zooms on focus |
| `smallTargets`, `tinyText` | under 40px, under 12px: report, rarely blocking |

Emulation does not cover the Safari URL bar, the virtual keyboard, safe areas, real touch latency or sound (headless). Say so in the report.

## Report

A table, one row per breach and one column per profile, ranked by impact on play: covered controls and unreachable actions first, sizes last. Then the screens the bot never reached (`unseen`). Numbers from the rows, never read off a screenshot.

## Turning a finding into a spec

A regression spec asserts one number on one viewport (`page.setViewportSize`) in the app's own e2e suite. Adding a WebKit or phone project to the app's CI config changes its pipeline: ask first.
