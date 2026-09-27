// Shared Playwright helpers: inject a signed `window.Telegram.WebApp` (the
// only way /app and /admin render anything — both show "NoInitData"/"Ruxsat
// yo'q" screens without it) and poll the mock Telegram server's `/__calls`.
import type { BrowserContext, Page } from "@playwright/test";
import { BACKEND_URL, MOCK_TELEGRAM_URL } from "./constants";
import { signInitData, type SignInitDataUser } from "./sign-init-data";
import type { MockCall } from "./mock-telegram";

/** Opens `/app/` or `/admin/` in a fresh page of `context`, with initData
 * signed for `botToken` injected before any script runs, and the
 * `telegram-web-app.js` CDN request stubbed (no internet in the test env). */
export async function openMiniApp(
  context: BrowserContext,
  entryPath: "/app/" | "/admin/",
  user: SignInitDataUser,
  botToken: string
): Promise<Page> {
  const initData = signInitData(user, botToken);

  await context.route("https://telegram.org/js/telegram-web-app.js", (route) =>
    route.fulfill({ status: 200, contentType: "application/javascript", body: "" })
  );

  await context.addInitScript(
    ([initDataArg, userArg]) => {
      (window as unknown as { Telegram: unknown }).Telegram = {
        WebApp: {
          initData: initDataArg,
          initDataUnsafe: { user: userArg },
          ready() {},
          expand() {},
          requestContact(cb: (granted: boolean) => void) {
            cb(false);
          },
          BackButton: {
            show() {},
            hide() {},
            onClick() {},
            offClick() {},
          },
          HapticFeedback: {
            impactOccurred() {},
            notificationOccurred() {},
          },
        },
      };
    },
    [initData, user]
  );

  const page = await context.newPage();
  await page.goto(`${BACKEND_URL}${entryPath}`);
  return page;
}

/** Polls the mock Telegram server until a recorded call matches `predicate`,
 * or throws after `timeoutMs`. This is how the test observes what the two
 * bots actually sent, without any real Telegram network call. */
export async function waitForMockCall(
  predicate: (call: MockCall) => boolean,
  timeoutMs = 10_000
): Promise<MockCall> {
  const deadline = Date.now() + timeoutMs;
  let lastCalls: MockCall[] = [];
  while (Date.now() < deadline) {
    const res = await fetch(`${MOCK_TELEGRAM_URL}/__calls`);
    lastCalls = (await res.json()) as MockCall[];
    const found = lastCalls.find(predicate);
    if (found) return found;
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error(
    `Timed out waiting for a matching mock Telegram call. Recorded calls: ${JSON.stringify(lastCalls, null, 2)}`
  );
}
