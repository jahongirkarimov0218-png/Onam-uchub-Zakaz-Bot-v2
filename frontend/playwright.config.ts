import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";
import { BACKEND_URL } from "./e2e/constants";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Chromium only, browsers installed locally into `.playwright-browsers`.
// Resolved here from this file's own location (not relying on a manually
// exported env var) so a plain `npm run e2e` finds them too — plain Node
// path code, so it's Windows+Git-Bash-safe either way.
process.env.PLAYWRIGHT_BROWSERS_PATH ??= path.resolve(__dirname, "..", ".playwright-browsers");

// No `webServer` here: globalSetup owns uvicorn + the mock Telegram server so
// it can migrate/seed a temp DB and point bots at the mock before anything
// starts, and stop both afterwards.
export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  globalSetup: "./e2e/global-setup.ts",
  use: {
    baseURL: BACKEND_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
