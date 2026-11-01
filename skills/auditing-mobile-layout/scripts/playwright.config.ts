import { defineConfig, devices } from '@playwright/test'

// Phone profiles for a layout audit. Copied next to the game's audit specs, run against a live server.
const baseURL = process.env['AUDIT_BASE_URL']
if (baseURL === undefined || baseURL === '') throw new Error('AUDIT_BASE_URL is not set')

export default defineConfig({
  testDir: '.',
  workers: 1,
  reporter: 'list',
  timeout: 600_000,
  use: { baseURL, actionTimeout: 5_000 },
  projects: [
    { name: 'iPhone SE', use: { ...devices['iPhone SE'] } },
    { name: 'iPhone 15', use: { ...devices['iPhone 15'] } },
    { name: 'iPhone 15 landscape', use: { ...devices['iPhone 15 landscape'] } },
    { name: 'Galaxy S9+', use: { ...devices['Galaxy S9+'] } },
    { name: 'Pixel 7', use: { ...devices['Pixel 7'] } },
    { name: 'Pixel 7 landscape', use: { ...devices['Pixel 7 landscape'] } },
  ],
})
