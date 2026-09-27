<!-- autopilot:start -->
# Faberlik Sotuv Bot (onam-shop)

Telegram Mini App shop for one Faberlic consultant: customer Mini App + admin Mini App + 2 aiogram bots (customer, admin) on one FastAPI backend with SQLite. Not an official Faberlic project.

## Commands

Repo root is `D:\ecc tool\onam-shop` (space in path — quote it). Backend commands run from `backend/` (relative DB/upload/dist paths resolve against CWD).

```bash
# install backend (venv already created by: uv venv --python 3.11 .venv)
uv pip install --python .venv/Scripts/python.exe -e "backend[dev]"      # from repo root
# migrate + seed (idempotent: 3 categories, 10 fictional products, SVG placeholders in UPLOAD_DIR/seed/)
cd backend && ../.venv/Scripts/python.exe -m alembic upgrade head
cd backend && ../.venv/Scripts/python.exe -m app.seed
# run API locally without bots (serves /app/ and /admin/ if frontend/dist exists)
cd backend && BOTS_ENABLED=false ../.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
# backend tests (pytest-cov on; add --cov-report=term-missing for gaps)
cd backend && ../.venv/Scripts/python.exe -m pytest
cd backend && ../.venv/Scripts/python.exe -m pytest tests/test_auth.py -q --no-cov
# frontend
cd frontend && npm install
cd frontend && npx vitest run                      # or one file: npx vitest run src/app/cart.test.ts
cd frontend && npm run lint                        # must be 0 errors
cd frontend && npm run build                       # tsc + vite -> dist/app/index.html, dist/admin/index.html
cd frontend && npm run e2e                         # build + Playwright (chromium from .playwright-browsers)
cd frontend && npm run dev                         # vite dev server (/app/index.html, /admin/index.html), proxies /api and /uploads to 127.0.0.1:8000
```

Deploy: `Dockerfile` + `docker-compose.yml` + `Caddyfile` (container runs `alembic upgrade head` then uvicorn). Never run here (no Docker on this machine).

## Structure

```
backend/app/            FastAPI app: config, db, models, auth, uploads, ratelimit, notify, scheduler, texts, statuses, seed
backend/app/api/        HTTP routers: catalog.py, orders.py (customer), admin_catalog.py, admin_orders.py (/api/admin)
backend/app/services/   business rules: catalog.py (CRUD, soft delete), orders.py (lifecycle, search, stats)
backend/app/schemas/    Pydantic in/out models (catalog.py, orders.py)
backend/app/bots/       aiogram routers: customer.py (/start -> open shop), admin.py (commands, status callbacks)
backend/alembic/        migrations (versions/c7f20d1d99a6_initial_schema.py)
backend/tests/          pytest suite + conftest fixtures
backend/data/           default SQLite location (onam.db, gitignored)
frontend/app/, admin/   the two HTML entries (Vite multi-page)
frontend/src/app/       customer Mini App: App.tsx (hash router), cart.ts, screens/
frontend/src/admin/     admin Mini App: App.tsx (admin gate + tabs), screens/
frontend/src/shared/    telegram.ts, api.ts, i18n/uz.ts, format.ts, router.ts, status.ts, theme.css, Logo.tsx
frontend/e2e/           Playwright spec + global-setup (uvicorn + mock Telegram Bot API)
frontend/test/setup.ts  vitest setup (jest-dom, localStorage polyfill)
```

## Key files

- `backend/app/main.py` — `create_app(settings=None, notifier=None)` (composition root), `include_routers(app)`, `build_bot`, lifespan.
- `backend/app/config.py` — `Settings` (one field per env var), `get_settings()` (lru_cache), `.bots_active`, `.admin_id_set`.
- `backend/app/auth.py` — `validate_init_data(raw, bot_token, max_age, now=None) -> TgUser`; deps `customer_user` (401), `admin_user` (401 / 403 `forbidden`).
- `backend/app/services/orders.py` — `create_order`, `change_status` (raises `InvalidTransition` 409), `load_order`, `list_orders`, `search_orders`, `open_orders`, `stats`.
- `backend/app/statuses.py` — status machine `NEXT`, `FINAL`, `LABELS_UZ`, `allowed(from, to)`; mirrored in `frontend/src/shared/status.ts`.
- `backend/app/notify.py` — `Notifier` protocol, `NullNotifier`, `TelegramNotifier`, `format_order`, `order_keyboard`.
- `backend/app/scheduler.py` — `remind_and_retry`, `daily_report`, `build_scheduler` (APScheduler 3, AsyncIOScheduler).
- `backend/app/texts.py` — every bot-facing string. `frontend/src/shared/i18n/uz.ts` — every UI string, `t(key, params?)`.
- `frontend/src/shared/api.ts` — `api<T>(path, opts)`, `ApiError {status, code}`.
- `frontend/src/shared/telegram.ts` — `tg` wrapper over `window.Telegram.WebApp` (tolerates its absence).

## Architecture

- Customer: Mini App (`/app/`) -> `api()` sends `Authorization: tma <initData>` -> `customer_user` validates HMAC with `CUSTOMER_BOT_TOKEN` -> router -> `services.*` -> DB.
- Admin: Mini App (`/admin/`) -> same header -> `admin_user` validates with `ADMIN_BOT_TOKEN` and requires id in `ADMIN_IDS`; UI first calls `GET /api/admin/me` (401/403 -> "Ruxsat yo'q", other errors -> retry screen).
- Order flow: `POST /api/orders` (rate-limited by `app.state.order_limiter`) -> `create_order` snapshots name/sku/price into `order_items` -> `notifier.order_created`. Status changes (admin API or bot callback `st:<order_id>:<status>`) -> `change_status` (conditional UPDATE, writes `order_status_history`) -> `notifier.status_changed`.
- `TelegramNotifier` messages admins + customer, records admin message ids in `order_admin_messages` to edit them on status change; `orders.admin_notified=False` orders are resent by the scheduler.
- Scheduler (always started, even without bots): every `REMINDER_CHECK_MINUTES` -> `remind_and_retry` (resend un-notified, remind about `new` orders); cron at `DAILY_REPORT_TIME` in `TIMEZONE` -> `daily_report` of open orders.
- Lifespan: if `settings.bots_active` -> two `Bot`s polling (`handle_signals=False`) + `TelegramNotifier`, admin menu button set to `<WEBAPP_URL>/admin/`; else `NullNotifier` (logs only). Customer bot `/start` offers `<WEBAPP_URL>/app/`.
- Static: `/uploads` -> `UPLOAD_DIR`; `FRONTEND_DIST` mounted at `/` with `html=True` (only if the dir exists), so `dist/app/index.html` is `/app/` and `dist/admin/index.html` is `/admin/`. Routers are included before the static mounts.
- Status machine: `new -> accepted -> ordered -> arrived -> delivered`; `cancelled` from any non-final status; `delivered`/`cancelled` are final.
- Catalog: soft delete (`is_deleted`) for categories/products; `is_available=False` products are shown flagged, not hidden; deleting a non-empty category -> 409 `category_not_empty`.
- Order items: `kind` `catalog` (priced snapshot) or `custom` (free-form, unpriced, optional image upload); `delivery_type` `delivery` (address required) or `pickup`.
- Frontend: React 18, hash routing (`useHashRoute`, `navigate`); customer routes `/`, `/product/:id`, `/cart`, `/custom`, `/checkout`, `/orders`, `/done/:id`; admin `#/orders`, `#/orders/:id`, `#/products`, `#/categories`. Cart persisted in localStorage key `onam-cart-v1`.

## Code conventions

- API errors: `HTTPException(status, detail=<machine_code>)` -> body `{"detail": "code"}`; services raise `CatalogError` / `OrderError` / `UploadError` (`code`, `http_status`) and routers translate. Frontend maps `code` to text via `uz.ts` (`errors.<code>`).
- All UI text in Uzbek Latin in `frontend/src/shared/i18n/uz.ts`; all bot text in `backend/app/texts.py`. No inline user-facing strings elsewhere.
- DB datetimes are naive UTC (SQLite drops tzinfo); re-attach `timezone.utc` when reading. Scheduler jobs take an aware `now` and raise `ValueError` on naive.
- Business time comes from `order_status_history`, not `updated_at` (e.g. delivered-this-month sum uses the `->delivered` history time).
- Prices are integer so'm; `formatSum(n)` -> `125 000 so'm`.
- Schema change = model edit + new Alembic revision (`test_migrations.py` checks upgrade head creates all 7 tables).
- New setting = field on `Settings` + line in `.env.example` (enforced by `tests/test_env_example.py`).
- Admin bot commands use `F.text.regexp` filters (not `Command`) so tests can pass stand-in message objects; commands accept an `@BotName` suffix; handler order matters (admin handlers, admin catch-all help, final "Ruxsat yo'q").
- Notifier calls are wrapped: Telegram failures are logged, never break an order.

## Environment

Names from `.env.example` (never commit values; `.env` is gitignored):
- `CUSTOMER_BOT_TOKEN`, `ADMIN_BOT_TOKEN` — BotFather tokens; also the HMAC keys for customer/admin initData.
- `ADMIN_IDS` — comma-separated Telegram ids allowed into the admin bot and `/api/admin/*`.
- `BOTS_ENABLED` — `false` (or either token empty) runs the API without bots.
- `WEBAPP_URL` — public base URL; bots link to `<url>/app/` and `<url>/admin/`.
- `TELEGRAM_API_BASE` — empty = official Telegram; set to a local mock server for E2E.
- `SHOP_NAME`, `PICKUP_ADDRESS` — shown in bots/Mini App; empty pickup falls back to a placeholder text.
- `DATABASE_URL` (sqlite+aiosqlite, relative to `backend/`), `UPLOAD_DIR`, `FRONTEND_DIST` — storage and static paths.
- `INIT_DATA_MAX_AGE_SECONDS` — initData lifetime.
- `REMINDER_FIRST_HOURS`, `REMINDER_REPEAT_HOURS`, `REMINDER_CHECK_MINUTES` — reminders for unaccepted `new` orders.
- `DAILY_REPORT_TIME` (HH:MM), `TIMEZONE` — daily open-orders report.
- `RATE_LIMIT_ORDERS`, `RATE_LIMIT_UPLOADS`, `RATE_LIMIT_WINDOW_SECONDS` — per-user in-memory limits (429 `rate_limited`).
- `MAX_UPLOAD_MB` — upload size cap (type checked by magic bytes).
- `DOMAIN` — used only by Caddy in docker compose.

## Tests

- Backend: `backend/tests/`, pytest with `asyncio_mode=auto`. Fixtures in `conftest.py`: `settings` (tmp SQLite, fake tokens), `fake_notifier` (`.events`), `app` (`create_app(settings, notifier=FakeNotifier())`), `client` (httpx `ASGITransport`), `session_factory`, `make_order`; helper `from conftest import sign_init_data`.
- Bots are tested by calling router handlers with mocked aiogram objects; scheduler jobs with a fixed aware `now`. No real Telegram calls; fake tokens are generated in fixtures.
- Frontend: `*.test.ts(x)` next to sources, vitest + jsdom + Testing Library; mock `window.Telegram.WebApp` and `globalThis.fetch`.
- E2E: `frontend/e2e/main-flow.spec.ts` (catalog -> cart -> order -> admin -> status). `global-setup.ts` migrates + seeds a temp DB in `backend/.tmp-e2e/` (removed on teardown), starts a Node mock Telegram Bot API on 127.0.0.1:38782 and uvicorn on 127.0.0.1:38781 with `BOTS_ENABLED=true` and fake tokens.

## Gotchas

- Path has a space: quote absolute paths; the E2E setup uses a DB path relative to `backend/` to avoid sqlite URL issues.
- `.env` is read from the repo root (path resolved in `config.py`), whatever the CWD; explicit env vars override it. Never create `.env` — `test_no_real_env_file_was_created` fails if it exists.
- Relative `DATABASE_URL`/`UPLOAD_DIR`/`FRONTEND_DIST` resolve against CWD — run backend commands from `backend/`.
- `app.main` has no module-level `app`: uvicorn needs `app.main:create_app --factory`.
- `alembic/env.py` uses `DATABASE_URL` env var or settings and strips `+aiosqlite` (sync DDL).
- `app/statuses.py` exists to avoid a circular import (`services.orders` imports `notify`); `services.orders` re-exports its names.
- Customer and admin initData are signed by different bots — a customer token never authenticates `/api/admin/*`.
- `frontend/test/setup.ts` installs an in-memory `localStorage` (jsdom's is broken under Node 26 + vitest 2); keep it.
- `playwright.config.ts` sets `PLAYWRIGHT_BROWSERS_PATH` to `<root>/.playwright-browsers` if unset, so plain `npm run e2e` works.
- Frontend tests use `globalThis.fetch` (no `@types/node` in the app tsconfig).
- Both HTML entries load `https://telegram.org/js/telegram-web-app.js`; outside Telegram `tg.initData` is empty and the customer app shows `NoInitData` without fetching.
- E2E mock Telegram must answer getMe, deleteWebhook, getUpdates, sendMessage, sendPhoto, editMessageText, answerCallbackQuery.

## Как здесь работает Autopilot

Сборка ведётся навыком `/autopilot`. Требования, спецификация и таски — в `.autopilot/`.
Прогресс — `.autopilot/dashboard.html`. Правило: требование из `manifest.md`
может снять только пользователь.

Если работа продолжается — скажи «продолжи автопилот»: состояние поднимется
из `.autopilot/state.js`, переспрашивать ничего не нужно.
<!-- autopilot:end -->
