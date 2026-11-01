import type { Browser, BrowserContextOptions, Page, TestInfo } from '@playwright/test'
import { appendFileSync, mkdirSync } from 'node:fs'
import { join } from 'node:path'

/** Every row, progress line and screenshot goes here. Required: keep it outside the repo. */
const dir = process.env['AUDIT_DIR']
if (dir === undefined || dir === '') throw new Error('AUDIT_DIR is not set')
export const AUDIT_DIR: string = dir
mkdirSync(join(AUDIT_DIR, 'shots'), { recursive: true })
const ROWS = join(AUDIT_DIR, 'audit.jsonl')

export function log(row: object): void {
  appendFileSync(ROWS, JSON.stringify(row) + '\n')
}

/**
 * Nothing is measured while it moves. Infinite animations are skipped: their `finished`
 * promise never resolves and would time the test out instead of measuring.
 */
export async function settle(page: Page): Promise<void> {
  await page.evaluate(async () => {
    const finite = document
      .getAnimations()
      .filter((a) => a.effect?.getComputedTiming().iterations !== Infinity)
    await Promise.allSettled(finite.map((a) => a.finished))
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  })
}

/**
 * One phone per player, with the project's device profile. Hand-made contexts ignore the
 * config's actionTimeout, and without one a blocked click waits until the test timeout.
 */
export async function openPhone(browser: Browser, info: TestInfo): Promise<Page> {
  const u = info.project.use
  const opts: BrowserContextOptions = {
    viewport: u.viewport,
    userAgent: u.userAgent,
    deviceScaleFactor: u.deviceScaleFactor,
    isMobile: u.isMobile,
    hasTouch: u.hasTouch,
    baseURL: u.baseURL,
  }
  const ctx = await browser.newContext(opts)
  ctx.setDefaultTimeout(5_000)
  return ctx.newPage()
}

export type Rect = { top: number; bottom: number; left: number; right: number; w: number; h: number }

/** Document-space rect, so two elements compare whatever the scroll position. */
export async function docRect(page: Page, selector: string): Promise<Rect | null> {
  return page.evaluate((q) => {
    const el = document.querySelector(q)
    if (!el) return null
    const r = el.getBoundingClientRect()
    return {
      top: Math.round(r.top + scrollY),
      bottom: Math.round(r.bottom + scrollY),
      left: Math.round(r.left),
      right: Math.round(r.right),
      w: Math.round(r.width),
      h: Math.round(r.height),
    }
  }, selector)
}

/** Generic per-screen audit: overflow, small targets, tiny text, input font sizes. */
export async function measure(page: Page, screen: string, info: TestInfo): Promise<void> {
  await settle(page)
  const data = await page.evaluate(() => {
    const vw = innerWidth
    const label = (el: Element): string => {
      const cls = typeof el.className === 'string' ? el.className.split(' ').slice(0, 2).join('.') : ''
      const txt = (el.textContent ?? el.getAttribute('aria-label') ?? '').trim().slice(0, 25)
      return `${el.tagName.toLowerCase()}${cls ? '.' + cls : ''} "${txt}"`
    }
    const visible = (el: Element): boolean => {
      const s = getComputedStyle(el)
      const r = el.getBoundingClientRect()
      return s.visibility !== 'hidden' && s.display !== 'none' && r.width > 0 && r.height > 0
    }
    const all = [...document.body.querySelectorAll('*')].filter(visible)
    const overflowX = all
      .filter((el) => {
        const r = el.getBoundingClientRect()
        return r.right > vw + 1 || r.left < -1
      })
      .filter((el, _i, arr) => !arr.some((o) => o !== el && o.contains(el)))
      .map(label)
    const smallTargets = all
      .filter((el) =>
        el.matches('button, a[href], input, select, textarea, [role=button], [role=checkbox], [tabindex="0"]'),
      )
      .map((el) => ({ el, r: el.getBoundingClientRect() }))
      .filter(({ r }) => Math.min(r.width, r.height) < 40)
      .map(({ el, r }) => `${label(el)} ${Math.round(r.width)}x${Math.round(r.height)}`)
    const tinyText = [
      ...new Set(
        all
          .filter((el) => [...el.childNodes].some((n) => n.nodeType === 3 && (n.textContent ?? '').trim() !== ''))
          .filter((el) => parseFloat(getComputedStyle(el).fontSize) < 12)
          .map((el) => `${label(el)} ${getComputedStyle(el).fontSize}`),
      ),
    ]
    const textInputs = [
      ...document.querySelectorAll('input:not([type=checkbox]):not([type=radio]):not([type=range]), textarea'),
    ]
      .filter(visible)
      .map((el) => `${label(el)} ${getComputedStyle(el).fontSize}`)
    return {
      vw,
      vh: innerHeight,
      scrollH: document.documentElement.scrollHeight,
      overflowX,
      smallTargets,
      tinyText,
      textInputs,
    }
  })
  const project = info.project.name
  log({ project, screen, ...data })
  await page.screenshot({ path: join(AUDIT_DIR, 'shots', `${project.replace(/ /g, '_')}-${screen}.png`), fullPage: true })
}

/** Does a dialog fit the viewport, and can every button in it be tapped without scrolling? */
export async function dialogFit(page: Page, selector: string) {
  return page.evaluate((q) => {
    const el = document.querySelector(q)
    if (!el) return null
    const r = el.getBoundingClientRect()
    return {
      vh: innerHeight,
      fits: r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth,
      buttons: [...el.querySelectorAll('button')].map((b) => {
        const br = b.getBoundingClientRect()
        return {
          text: (b.textContent ?? b.getAttribute('aria-label') ?? '').trim().slice(0, 20),
          onScreen: br.top >= 0 && br.bottom <= innerHeight && br.left >= 0 && br.right <= innerWidth,
        }
      }),
    }
  }, selector)
}

/** What actually receives a tap at the centre of a control. Call it when a click is intercepted. */
export async function coveredBy(page: Page, selector: string): Promise<string | null> {
  return page.evaluate((q) => {
    const el = document.querySelector(q)
    if (!el) return null
    const r = el.getBoundingClientRect()
    const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)
    if (top === null || el.contains(top)) return null
    return `${top.tagName.toLowerCase()}.${String(top.className).split(' ')[0] ?? ''}`
  }, selector)
}

/** Distance in document pixels between two elements the player must see together. */
export async function spread(page: Page, a: string, b: string): Promise<{ spread: number; vh: number } | null> {
  return page.evaluate(
    ([qa, qb]) => {
      const ea = document.querySelector(qa)
      const eb = document.querySelector(qb)
      if (!ea || !eb) return null
      const ra = ea.getBoundingClientRect()
      const rb = eb.getBoundingClientRect()
      return { spread: Math.round(Math.max(ra.bottom, rb.bottom) - Math.min(ra.top, rb.top)), vh: innerHeight }
    },
    [a, b] as const,
  )
}

/**
 * Heartbeat and stall detector for a bot loop. Call `tick(moves)` once per loop: it writes
 * a progress line on every new move and throws after `stallMs` without one.
 */
export function heartbeat(stallMs = 30_000) {
  let last = -1
  let since = Date.now()
  return (moves: number, state = ''): void => {
    if (moves !== last) {
      last = moves
      since = Date.now()
      appendFileSync(join(AUDIT_DIR, 'progress.log'), `${new Date().toISOString()} move=${moves} ${state}\n`)
    } else if (Date.now() - since > stallMs) {
      throw new Error(`stalled ${stallMs / 1000}s at move ${moves}`)
    }
  }
}
