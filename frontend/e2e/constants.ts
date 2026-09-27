// Shared fixed values for the E2E harness: ports, fake tokens, test users.
// Fixed (not dynamically allocated) because the E2E run owns its own short-lived
// processes end to end — nothing else is expected to be listening here.
export const BACKEND_PORT = 38781;
export const MOCK_TELEGRAM_PORT = 38782;

export const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
export const MOCK_TELEGRAM_URL = `http://127.0.0.1:${MOCK_TELEGRAM_PORT}`;

// Fake tokens — never real, never sent to the real Telegram API (TELEGRAM_API_BASE
// points bots at the local mock server for the whole E2E run).
export const CUSTOMER_BOT_TOKEN = "100001:E2E-customer-fake-token";
export const ADMIN_BOT_TOKEN = "100002:E2E-admin-fake-token";

export const ADMIN_TG_ID = 900001;
export const CUSTOMER_TG_ID = 900002;
