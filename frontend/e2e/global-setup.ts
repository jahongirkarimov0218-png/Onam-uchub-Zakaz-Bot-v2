// Playwright globalSetup: builds nothing itself (that's `npm run build`, run
// before `playwright test` by the `e2e` npm script) but brings up everything
// the browser talks to — the mock Telegram Bot API and a real uvicorn backend
// on a fresh, migrated + seeded temp DB — and returns the teardown function
// that stops both and verifies nothing is left running.
import { spawn, spawnSync, type ChildProcess } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { startMockTelegram, type MockTelegramServer } from "./mock-telegram";
import { ADMIN_BOT_TOKEN, ADMIN_TG_ID, BACKEND_PORT, BACKEND_URL, CUSTOMER_BOT_TOKEN, MOCK_TELEGRAM_PORT, MOCK_TELEGRAM_URL } from "./constants";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..", "..");
const BACKEND_DIR = path.join(ROOT_DIR, "backend");
const PYTHON = path.join(ROOT_DIR, ".venv", "Scripts", "python.exe");
const TMP_RELATIVE = ".tmp-e2e";
const TMP_DIR_ABS = path.join(BACKEND_DIR, TMP_RELATIVE);

const BACKEND_ENV: NodeJS.ProcessEnv = {
  ...process.env,
  PYTHONUNBUFFERED: "1",
  CUSTOMER_BOT_TOKEN,
  ADMIN_BOT_TOKEN,
  ADMIN_IDS: String(ADMIN_TG_ID),
  BOTS_ENABLED: "true",
  WEBAPP_URL: "",
  TELEGRAM_API_BASE: MOCK_TELEGRAM_URL,
  SHOP_NAME: "Faberlik Sotuv Bot (E2E)",
  PICKUP_ADDRESS: "Toshkent, Chilonzor tumani, 1-uy (E2E test manzili)",
  // Relative to `cwd: BACKEND_DIR` below — sidesteps sqlite URL / space-in-path
  // issues from the project root containing a space ("onam-shop" under "ecc tool").
  DATABASE_URL: `sqlite+aiosqlite:///./${TMP_RELATIVE}/e2e.db`,
  UPLOAD_DIR: `${TMP_RELATIVE}/uploads`,
  FRONTEND_DIST: "../frontend/dist",
  INIT_DATA_MAX_AGE_SECONDS: "86400",
  REMINDER_FIRST_HOURS: "2",
  REMINDER_REPEAT_HOURS: "4",
  REMINDER_CHECK_MINUTES: "5",
  DAILY_REPORT_TIME: "09:00",
  TIMEZONE: "Asia/Tashkent",
  RATE_LIMIT_ORDERS: "5",
  RATE_LIMIT_UPLOADS: "10",
  RATE_LIMIT_WINDOW_SECONDS: "600",
  MAX_UPLOAD_MB: "5",
  DOMAIN: "",
};

function runStep(cmd: string, args: string[]): void {
  const result = spawnSync(cmd, args, { cwd: BACKEND_DIR, env: BACKEND_ENV, encoding: "utf8" });
  if (result.status !== 0) {
    throw new Error(
      `E2E setup step failed: ${cmd} ${args.join(" ")}\n--- stdout ---\n${result.stdout}\n--- stderr ---\n${result.stderr}`
    );
  }
}

async function waitForHealth(timeoutMs: number, proc: ChildProcess, log: () => string): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (proc.exitCode !== null) {
      throw new Error(`uvicorn exited early (code ${proc.exitCode}) before /health responded.\n${log()}`);
    }
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (res.ok) {
        const body = (await res.json()) as { status: string; bots: boolean };
        if (body.status === "ok") return;
      }
    } catch {
      // backend not accepting connections yet — retry
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error(`Timed out waiting for ${BACKEND_URL}/health.\n${log()}`);
}

/** Windows `child.kill()` terminates forcefully but can leave the port bound
 * for a moment; poll until the health endpoint actually stops answering so
 * teardown only returns once nothing is left running. */
async function waitForDown(url: string, timeoutMs: number): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      await fetch(url, { signal: AbortSignal.timeout(500) });
    } catch {
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  return false;
}

function forceKillByPid(pid: number): void {
  if (process.platform === "win32") {
    spawnSync("taskkill", ["/PID", String(pid), "/T", "/F"]);
  } else {
    try {
      process.kill(-pid, "SIGKILL");
    } catch {
      try {
        process.kill(pid, "SIGKILL");
      } catch {
        // already gone
      }
    }
  }
}

export default async function globalSetup(): Promise<() => Promise<void>> {
  fs.rmSync(TMP_DIR_ABS, { recursive: true, force: true });
  fs.mkdirSync(TMP_DIR_ABS, { recursive: true });

  const mock: MockTelegramServer = await startMockTelegram(MOCK_TELEGRAM_PORT);

  runStep(PYTHON, ["-m", "alembic", "upgrade", "head"]);
  runStep(PYTHON, ["-m", "app.seed"]);

  let backendLog = "";
  // `app.main` only exposes the `create_app()` factory (no module-level
  // `app` instance), so uvicorn needs `--factory`; `create_app()` with no
  // args reads `Settings()` from the environment, which is what BACKEND_ENV sets.
  const backend = spawn(
    PYTHON,
    ["-m", "uvicorn", "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", String(BACKEND_PORT)],
    {
      cwd: BACKEND_DIR,
      env: BACKEND_ENV,
      stdio: ["ignore", "pipe", "pipe"],
    }
  );
  backend.stdout?.on("data", (chunk: Buffer) => {
    backendLog += chunk.toString();
  });
  backend.stderr?.on("data", (chunk: Buffer) => {
    backendLog += chunk.toString();
  });

  try {
    await waitForHealth(20_000, backend, () => backendLog);
  } catch (err) {
    forceKillByPid(backend.pid!);
    await mock.close();
    throw err;
  }

  return async function globalTeardown(): Promise<void> {
    if (backend.pid && backend.exitCode === null) {
      backend.kill();
      const down = await waitForDown(`${BACKEND_URL}/health`, 5_000);
      if (!down && backend.exitCode === null) {
        forceKillByPid(backend.pid);
        await waitForDown(`${BACKEND_URL}/health`, 5_000);
      }
    }
    await mock.close();
    fs.rmSync(TMP_DIR_ABS, { recursive: true, force: true });
  };
}
