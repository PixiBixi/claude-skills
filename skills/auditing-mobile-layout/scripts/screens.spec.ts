import { test } from '@playwright/test'
import { measure } from './lib.js'

// Static screens reachable by URL alone, one measurement each. AUDIT_PATHS="/,/rules,/about".
const paths = (process.env['AUDIT_PATHS'] ?? '/').split(',').filter((p) => p !== '')

for (const path of paths) {
  test(`screen ${path}`, async ({ page }, info) => {
    await page.goto(path)
    await page.waitForLoadState('networkidle')
    await measure(page, `url${path.replace(/\//g, '_')}`, info)
  })
}
