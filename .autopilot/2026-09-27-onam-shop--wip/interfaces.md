# Interfaces

Project root: `D:\ecc tool\onam-shop` (path has a SPACE — quote absolute paths; prefer relative paths from the root).

## Правила проекта

- Stack/versions: Python 3.11.9 in `.venv` (uv 0.11), Node 26 / npm 11. Allowed Python packages: fastapi, uvicorn[standard], aiogram>=3, sqlalchemy[asyncio]>=2, aiosqlite, alembic, pydantic-settings, apscheduler>=3,<4, python-multipart, tzdata; dev: pytest, pytest-asyncio, pytest-cov, httpx. Allowed npm packages: react@18, react-dom@18, vite, typescript, @vitejs/plugin-react, vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom, @types/react, @types/react-dom, @playwright/test, tsx (for e2e helpers), eslint, @eslint/js, typescript-eslint, eslint-plugin-react-hooks, eslint-plugin-jsx-a11y, globals (lint — added after T05 review). Anything else -> return `BLOCKED` with the reason instead of installing.
- Install: `uv pip install --python .venv/Scripts/python.exe -e "backend[dev]"` (from root). npm: `cd frontend && npm install` (local only, never -g).
- Backend tests: `cd backend && ../.venv/Scripts/python.exe -m pytest` (coverage: `--cov=app --cov-report=term-missing`). Frontend tests: `cd frontend && npx vitest run`. Build: `cd frontend && npm run build`. E2E (ticket 07): `cd frontend && npm run e2e` with `PLAYWRIGHT_BROWSERS_PATH` = `<root>/.playwright-browsers`.
- Never create `.env`, never write a real token. Tests use fake tokens like `123456:TEST-customer` generated in fixtures. No real network calls to Telegram — aiogram Bot is always mocked or pointed at a local mock server.
- Do not touch: `.autopilot/`, `CLAUDE.md`, `.git/`, `.venv/` internals, anything outside the project root. No `git push`, no remotes, no global installs, no Docker install/run.
- Deleting: only relative paths from root, no `*`, no `..`.
- Long-running processes (uvicorn, vite) only in background, stopped before returning.
- ECC GateGuard hook may demand facts before a Write/Bash: state them briefly and retry. Never disable hooks.
- UI text: Uzbek Latin, all in `frontend/src/shared/i18n/uz.ts`. Backend user-facing texts (bot messages) in `backend/app/texts.py` (one module).
- Commit is done by the orchestrator, not by you. Leave the tree with tests green.

## Границы, решённые в спецификации

| Модуль | Владеет | Выставляет | Прячет |
|---|---|---|---|
| `app.config` | settings | `Settings`, `get_settings()`; `settings.bots_active` (enabled and both tokens set), `settings.admin_id_set: set[int]` | env parsing |
| `app.db` / `app.models` | schema, sessions | `Base`, models above, `make_engine(url)`, `make_session_factory(engine)`, `get_session` dependency | engine details |
| `app.auth` | initData trust | `validate_init_data(raw, bot_token, max_age, now=None) -> TgUser` (raises `InitDataError(code)`), deps `customer_user`, `admin_user` | HMAC details |
| `app.uploads` | files on disk | `save_upload(file, kind, user_id, session, settings) -> Upload` (raises `UploadError(code, http_status)`), `public_url(path)` | magic bytes, naming |
| `app.ratelimit` | counters | `RateLimiter(limit, window).hit(key) -> bool` ; app-level instances | sliding window |
| `app.services.catalog` | categories/products rules | CRUD functions used by both APIs | soft delete, filtering |
| `app.services.orders` | order lifecycle | `create_order(session, user, data) -> Order`, `change_status(session, order_id, to, actor_id, source) -> Order` (raises `InvalidTransition`), `list_orders(...)`, `search_orders(session, query)`, `open_orders(session)`, `stats(session, now, tz)`, `allowed(from,to)`, `NEXT`, `FINAL`, `LABELS_UZ` | price snapshot, history |
| `app.notify` | outbound Telegram | `Notifier` protocol: `order_created(order)`, `status_changed(order)`, `reminder(orders)`, `daily_report(orders)`; `TelegramNotifier(customer_bot, admin_bot, settings, session_factory)`, `NullNotifier`; `format_order(order) -> str`, `order_keyboard(order)` | aiogram calls, message-id bookkeeping, error swallowing |
| `app.bots.customer` / `app.bots.admin` | bot handlers | `customer_router(settings)`, `admin_router(settings, session_factory, notifier)` | filters, texts |
| `app.scheduler` | timed jobs | `remind_and_retry(session_factory, notifier, settings, now)`, `daily_report(...)`, `build_scheduler(...)` | APScheduler wiring |
| `app.main` | composition | `create_app(settings=None, notifier=None) -> FastAPI` | lifespan, static mounting |
| frontend `src/shared` | Telegram + HTTP + text | `tg` (WebApp wrapper: `initData`, `user`, `requestContact()`, `ready()`), `api(path, opts)` (adds `tma` header, maps error codes), `t(key, params?)`, `formatSum(n)` | SDK absence handling |

**Test seams:** backend — HTTP via `create_app(settings, notifier=FakeNotifier())` + httpx `ASGITransport`; bots — router handlers called with mocked aiogram objects; scheduler — job functions called with a fixed `now`. Frontend — components rendered with a mocked `window.Telegram.WebApp` and mocked `fetch`. E2E — real uvicorn + built frontend + a Node mock Telegram Bot API server (records `sendMessage`/`editMessageText`), browser with injected `window.Telegram.WebApp` whose `initData` is signed with the test tokens.

## Status machine

```python
NEXT = {"new": "accepted", "accepted": "ordered", "ordered": "arrived", "arrived": "delivered"}
FINAL = {"delivered", "cancelled"}
LABELS_UZ = {"new": "Yangi", "accepted": "Qabul qilindi", "ordered": "Faberlic'ga buyurtma berildi",
             "arrived": "Yetib keldi", "delivered": "Topshirildi", "cancelled": "Bekor qilindi"}
```

API contracts, data model and settings: `spec.md` -> «Решения по реализации» (authoritative).

## Что построили таски

(appended by the orchestrator as tickets land)

### Из таска 01 — backend asosi

- `app.config`: `Settings(customer_bot_token, admin_bot_token, admin_ids, bots_enabled, webapp_url, telegram_api_base, shop_name, pickup_address, database_url, upload_dir, frontend_dist, init_data_max_age_seconds, reminder_first_hours, reminder_repeat_hours, reminder_check_minutes, daily_report_time, timezone, rate_limit_orders, rate_limit_uploads, rate_limit_window_seconds, max_upload_mb, domain)`; `.admin_id_set -> set[int]`; `.bots_active -> bool`; `get_settings()` (lru_cache).
- `app.db`: `make_engine(url) -> AsyncEngine`; `make_session_factory(engine) -> async_sessionmaker[AsyncSession]`; `get_session(request)` dependency (uses `request.app.state.session_factory`).
- `app.models`: `Base, Category, Product, Upload, Order, OrderItem, OrderStatusHistory, OrderAdminMessage` (spec Data model). New columns/tables → new Alembic revision (`alembic revision --autogenerate`); `alembic/env.py` strips `+aiosqlite` for sync DDL.
- `app.auth`: `validate_init_data(raw, bot_token, max_age, now=None) -> TgUser`; `InitDataError(code)` codes `invalid_init_data | init_data_expired`; `TgUser(id, first_name, last_name, username, language_code)`; deps `customer_user` (401) / `admin_user` (401, 403 `forbidden`).
- `app.main`: `create_app(settings=None, notifier=None) -> FastAPI`; `app.state.{settings, notifier, engine, session_factory}`; `app.dependency_overrides[get_settings]` set; `GET /health`, `GET /api/admin/me`; **routers are added inside `include_routers(app)`** (called before static mounts); `/uploads` static (dir created), `FRONTEND_DIST` at `/` (html=True) only if exists.
- Tests: `backend/tests/conftest.py` fixtures `settings`, `fake_notifier` (`FakeNotifier.events`, async `order_created/status_changed/reminder/daily_report`), `app` (create_all), `client` (httpx AsyncClient + ASGITransport); helper `from conftest import sign_init_data` → `sign_init_data(user: dict, bot_token: str, auth_date: int|None=None) -> str`.
- Test command: `cd backend && ../.venv/Scripts/python.exe -m pytest` (25 passed after T01, coverage 92%).
- Review notes for later tickets: DB datetime columns are naive (SQLite drops tzinfo) — values are UTC; re-attach `timezone.utc` when reading (orders, scheduler, stats). `PICKUP_ADDRESS` may be empty in `.env` — code that exposes it (`/api/config`) must fall back to the placeholder text «[Olib ketish manzili — .env faylida PICKUP_ADDRESS]» when empty.

### Из таска 05 — frontend shared (provisional, ticket in progress)

- `src/shared/telegram.ts` `tg`: `initData: string`, `user: TgUser|null`, `ready()`, `expand()`, `requestContact(): Promise<string|null>`, `backButton.show(onClick)/.hide()`, `haptic.impact(style?)/.notification(type?)`.
- `src/shared/api.ts` `api<T>(path, {method?, body?, headers?}): Promise<T>` — adds `Authorization: tma <initData>`, JSON unless FormData; throws `ApiError extends Error {status, code, message}` (code = server `detail`, or `network` / `generic` / `rate_limited`).
- `src/shared/i18n/uz.ts` `uz` dict with dot-path keys (`errors.not_found`), `t(key, params?)` with `{param}` interpolation.
- `src/shared/format.ts` `formatSum(n)` → `125 000 so'm`, `formatDate(iso)`. `src/shared/router.ts` `useHashRoute(): string`, `navigate(path)`. `src/shared/theme.css` (linked in both HTML entries). `src/shared/Logo.tsx`.
- Vite: `build.rollupOptions.input = {app: app/index.html, admin: admin/index.html}`; vitest jsdom with `test/setup.ts` (MemoryStorage localStorage polyfill — jsdom localStorage broken under Node 26 + vitest 2.1.9).
- Frontend tests: `cd frontend && npx vitest run`.

### Из таска 02 — katalog, yuklash, rate limit, seed

- `app.ratelimit.RateLimiter(limit, window).hit(key, now=None) -> bool`, `.reset()`; instances `app.state.upload_limiter`, `app.state.order_limiter` built in `create_app` from settings. **Ticket 03: reuse `order_limiter.hit(user.id)` in `POST /api/orders` (→ 429 `rate_limited`).**
- `app.uploads.save_upload(file, kind, user_id, session, settings) -> Upload` raises `UploadError(code, http_status)`; `public_url(filename) -> str` (`/uploads/<name>`).
- `app.services.catalog`: `list_categories`, `create_category`, `rename_category`, `delete_category`, `list_products(session, category_id=None, q=None)`, `get_product`, `get_visible_product(session, id)`, `create_product(session, **fields)`, `update_product(session, id, **fields)`, `delete_product(session, id)`; `CatalogError(code, http_status)`.
- `app.schemas.catalog`: `ConfigOut, CategoryOut, CategoryIn, ProductOut, ProductIn, ProductPatch, UploadOut`. `app.api.catalog.product_to_out(product) -> ProductOut` (reuse for image urls).
- Routers: `app.api.catalog.router` (customer), `app.api.admin_catalog.router` (prefix `/api/admin`, `dependencies=[Depends(admin_user)]`) — registered in `include_routers`.
- `app.seed.seed(session_factory, upload_dir: Path)`; CLI `python -m app.seed` (idempotent; SVGs in `UPLOAD_DIR/seed/`).
- `/api/config` `shop_subtitle` is a fixed constant in `app/api/catalog.py` («Faberlic konsultanti do'koni»).
- Backend: 53 tests, coverage 83% after T02.
- (T05 final) `src/app/App.tsx` `App()` — hash routes `/`, `/product/:id`, `/cart`, `/custom`, `/checkout`, `/orders`, `/done/:id`; `NoInitData` (no fetch) when `tg.initData` empty. Screens in `src/app/screens/`: `Catalog`, `ProductDetail`, `CartScreen`, `CustomForm` (`CustomFormResult`), `Checkout({cart, pickupAddress, onSuccess})` posting `OrderCreate` (phone regex `/^(\+998\d{9}|\d{9,15})$/`), `Orders`, `Done`, `NoInitData`. App clears cart in `onSuccess`. Test files use `globalThis.fetch` (no @types/node). Frontend: 18 tests; `npm run build` → `dist/app/index.html`, `dist/admin/index.html`.

### Из таска 03 — zakazlar

- `app.notify`: `Notifier(Protocol)` {`order_created(order)`, `status_changed(order)`, `reminder(orders)`, `daily_report(orders)`}; `NullNotifier` (log only). **T04 adds `TelegramNotifier` here.**
- `app.services.orders`: `NEXT`, `FINAL`, `LABELS_UZ`; `allowed(from, to)`; `OrderError(code, http_status)`; `InvalidTransition` (409 `invalid_transition`); `create_order(session, user, data, notifier=None) -> Order`; `change_status(session, order_id, to, actor_id, source, notifier=None) -> Order`; `load_order(session, order_id) -> Order|None` (attaches `.items`, `.history` lists); `list_orders(session, *, tg_user_id=None, status=None, q=None, limit=200)`; `search_orders(session, query)`; `open_orders(session)`; `stats(session, now, tz) -> {by_status, today, delivered_month_sum}` (delivered month uses `updated_at`). Callers pass `request.app.state.notifier`; notifier errors are swallowed inside the service.
- `app.schemas.orders`: `normalize_phone(raw)`, `OrderCreate`, `OrderItemIn`, `CustomItemIn`, `OrderOut`, `OrderItemOut`, `OrderDetailOut`, `HistoryOut`, `StatusIn`, `StatsOut`.
- `app.api.orders`: `order_to_out(order)`, `order_item_to_out(item)`; `POST /api/orders` (201, `order_limiter`), `GET /api/orders/my`. `app.api.admin_orders` (prefix `/api/admin`): `GET /orders`, `GET /orders/{id}`, `POST /orders/{id}/status`, `GET /stats`.
- `create_app(settings=None, notifier=None)` default notifier `NullNotifier()`. Backend: 119 tests, coverage 88%.
- (T05 repair) `Logo({size?, label?})`; ESLint flat config `frontend/eslint.config.js`, `npm run lint` (0 errors required). BackButton wired in App per route. Frontend: 28 tests.
- (T03 repair) `normalize_phone` accepts spaces/dashes/parens and any `+` 9–15 digits; `change_status` uses conditional UPDATE (race-safe); `delivered_month_sum` by `→delivered` history time. **T04: don't rely on `updated_at` for business time.** Backend: 127 tests.

### Из таска 06 — admin Mini App

- `src/shared/status.ts`: `NEXT`, `FINAL` (Set), `STATUSES`, `OrderStatus`, `allowed(from,to)`, `nextStatus(from)`, `statusLabel(code)` (i18n `status.*`).
- `src/admin/App.tsx` `App()`: gate on `GET /api/admin/me` (401/403 → only "Ruxsat yo'q"); tabs Zakazlar / Mahsulotlar / Kategoriyalar; routes `#/orders`, `#/orders/:id`, `#/products`, `#/categories` (product/category forms inline, no `#/products/:id`). OrderDetail: `POST /api/admin/orders/:id/status {status}`, cancel with inline confirm. Frontend: 54 tests.
- (T06 repair) `tg.backButton.show/hide` keep one registered handler internally (no leak). Admin gate: 401/403 → forbidden, other errors → retry screen. Frontend: 67 tests.

### Из таска 04 — botlar, eslatmalar, lifespan

- `app.statuses`: `NEXT`, `FINAL`, `LABELS_UZ`, `allowed` (re-exported by `app.services.orders`). `app.texts`: all bot texts.
- `app.notify.TelegramNotifier(customer_bot, admin_bot, settings, session_factory)`; `format_order(order) -> str`; `order_keyboard(order) -> InlineKeyboardMarkup|None`; callback data `st:<order_id>:<status>`.
- `app.bots.customer.customer_router(settings)`, `app.bots.admin.admin_router(settings, session_factory, notifier)` (commands via `F.text` filters).
- `app.scheduler`: `remind_and_retry(...)`, `daily_report(...)`, `build_scheduler(session_factory, notifier, settings)`.
- `app.main.build_bot(token, settings)` — `TELEGRAM_API_BASE` set → `AiohttpSession(api=TelegramAPIServer.from_base(...))`. Lifespan: `bots_active` → 2 bots polling (`handle_signals=False`) + TelegramNotifier + scheduler; else NullNotifier + scheduler. **E2E: set `BOTS_ENABLED=true`, fake tokens, `TELEGRAM_API_BASE=http://127.0.0.1:<mock port>`; mock must answer getMe, deleteWebhook, getUpdates, sendMessage, sendPhoto, editMessageText, answerCallbackQuery.**
- Backend: 171 tests, coverage 89%.
- (T04 repair) commands accept `@BotName`; admins get `texts.ADMIN_HELP` on unknown input; `/order_<id>` messages stored in `order_admin_messages`; lifespan closes bot sessions and sets admin menu button when WEBAPP_URL set; scheduler jobs reject naive `now`. Backend: 189 tests, 90%.
