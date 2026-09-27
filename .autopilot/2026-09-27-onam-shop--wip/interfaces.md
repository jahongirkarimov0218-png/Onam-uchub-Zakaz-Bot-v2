# Interfaces

Project root: `D:\ecc tool\onam-shop` (path has a SPACE — quote absolute paths; prefer relative paths from the root).

## Правила проекта

- Stack/versions: Python 3.11.9 in `.venv` (uv 0.11), Node 26 / npm 11. Allowed Python packages: fastapi, uvicorn[standard], aiogram>=3, sqlalchemy[asyncio]>=2, aiosqlite, alembic, pydantic-settings, apscheduler>=3,<4, python-multipart, tzdata; dev: pytest, pytest-asyncio, pytest-cov, httpx. Allowed npm packages: react@18, react-dom@18, vite, typescript, @vitejs/plugin-react, vitest, @testing-library/react, @testing-library/jest-dom, @testing-library/user-event, jsdom, @types/react, @types/react-dom, @playwright/test, tsx (for e2e helpers). Anything else -> return `BLOCKED` with the reason instead of installing.
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
