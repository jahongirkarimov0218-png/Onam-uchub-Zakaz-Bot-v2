# Спецификация: Faberlik Sotuv Bot (onam-shop)

## Задача

A Faberlic consultant (the user's mother) takes orders by phone. Customers call and say "order this product for me"; she sometimes forgets an order or cannot find it later. Orders get lost, customers wait, nobody knows what state an order is in.

## Решение

Customers open a Telegram Mini App from a customer bot, browse a catalog (or describe a product that is not in the catalog, with a photo), put things in a cart and place an order. Every order instantly arrives in a separate admin bot with buttons to move it through statuses; each status change is pushed to the customer. The admin bot nags about orders nobody accepted, sends a morning list of open orders, and opens an admin Mini App where the consultant manages products and orders. Nothing is lost: every order and every status change is stored; a new-order message to the admins that failed is retried by the scheduler (customer messages that fail are logged, the order is unaffected).

The shop is presented as "Faberlik Sotuv Bot — Faberlic konsultanti do'koni", never as official Faberlic: no Faberlic logo, brand assets or domain.

## Пользовательские истории

Marks: `R##` from the manifest, `R##.n` deepening, `A## → R##` addition. `S##` = self-briefing decision in manifest.

### Customer bot

| # | Mark | Story | Acceptance |
|---|------|-------|------------|
| 1 | R18 | As a customer, I send /start and get a greeting and a "Do'konni ochish" WebApp button | reply text from i18n + `web_app` button with `WEBAPP_URL/app/` |
| 2 | R18.1 | …if `WEBAPP_URL` is not configured, I still get a greeting, without a broken button | no button, greeting says shop is being set up |
| 3 | R19, S10 | As a customer, I get a message whenever my order status changes | text: order number, new status label (uz) |
| 4 | R70i | …if I never started the bot or blocked it, the status change still succeeds | send error logged, API returns 200, history written |

### Customer Mini App (/app)

| # | Mark | Story | Acceptance |
|---|------|-------|------------|
| 5 | R20 | As a customer, I see categories as tabs/chips and products of the selected one ("Hammasi" = all) | category filter works |
| 6 | R21 | I search by name or article (sku); search is case-insensitive, substring | `q` matches name or sku |
| 7 | R22 | A product card shows image, name, article, price formatted in so'm (`125 000 so'm`), description | all 5 fields visible; detail view shows full description |
| 8 | R20.1 | Empty catalog / no search results show a friendly text and a link to the "Katalogda yo'q" form | empty-state text from i18n |
| 9 | R45, S19 | Unavailable product is shown greyed with "Mavjud emas", add-to-cart disabled | button disabled |
| 10 | R23 | Cart: +/− quantity (1…99), remove line, total in so'm | total recalculated live |
| 11 | R24 | Cart survives closing the app (localStorage key `onam-cart-v1`) | reopen → same cart; corrupt JSON → empty cart, no crash |
| 12 | R25, S02 | "Katalogda yo'q mahsulot" form: name and/or article and/or photo (at least one required), quantity, note → added to cart as a custom line | validation message when all three empty |
| 13 | R25.1 | Photo is uploaded right away, with progress/error; wrong type or >5 MB shows a clear error in uz | 415/413 mapped to text |
| 14 | R25.2 | Custom lines show "Narx keyin aniqlanadi" and are not in the total | total excludes them; label shown |
| 15 | R26 | Checkout: name (prefilled from Telegram first/last name), phone — "Kontaktni yuborish" button (Telegram `requestContact`) or manual input | contact fills phone; manual works when contact refused/unsupported |
| 16 | R26.1, S03 | Phone validation: `+998XXXXXXXXX` or 9–15 digits; server normalizes | invalid phone → inline error, form keeps values |
| 17 | R27, S04, S05 | Delivery type: "Yetkazib berish" (address required) or "Olib ketish" (shows pickup address); comment optional (≤500 chars) | address required only for delivery |
| 18 | R01 | Submit → order created, cart cleared, success screen with order number `#<id>` | order exists in DB, cart empty |
| 19 | R01.1 | Double tap on submit does not create two orders (button disabled while sending) | one order |
| 20 | R01.2 | Network/server error keeps the form and the cart and shows a retry-able error | cart not cleared on failure |
| 21 | R53 | Too many orders/uploads → 429 → "Juda ko'p urinish, birozdan keyin qayta urinib ko'ring" | text shown |
| 22 | R28, S22 | "Mening zakazlarim": my orders newest first, number, date, status badge, items, total | only own orders |
| 23 | R28.1 | No orders yet → empty text + button back to catalog | empty state |
| 24 | R12 | Colors follow Telegram `themeParams` (CSS vars `--tg-theme-*`), light and dark; outside Telegram falls back to `prefers-color-scheme` | both themes readable |
| 25 | R29 | All UI strings live in one i18n module `uz` (Latin); adding `ru` = adding one dictionary | no hard-coded UI strings in components |
| 26 | R48.1 | Opened outside Telegram (no initData) → screen "Iltimos, do'konni Telegram orqali oching" | no API calls with empty auth |

### Admin bot

| # | Mark | Story | Acceptance |
|---|------|-------|------------|
| 27 | R31 | As the admin, a new order arrives instantly: number, customer name, phone, (username), delivery type/address, items (custom lines marked, photo sent as a separate photo if present), total, comment | message to every id in `ADMIN_IDS` |
| 28 | R32, S01 | The message has inline buttons for the next allowed status only + "Bekor qilish" (while not final) | buttons match the state machine |
| 29 | R33, S09 | Pressing a button changes the status, edits the message (new status line, new buttons) in every admin's chat, and notifies the customer | history row `source=bot`; customer message sent |
| 30 | R32.1 | Stale button (status already moved, e.g. by another admin) → callback answer "Holat allaqachon o'zgargan", message refreshed | no invalid transition |
| 31 | R34, R35, S06 | Order still `new` 2 h after creation → reminder to admins; repeated every 4 h while it stays `new`; hours from `.env` | `last_reminded_at` persisted |
| 32 | R03, S08 | If the new-order message failed (bots off / Telegram error), the scheduler retries it | `admin_notified` flag |
| 33 | R36, S07 | Every day 09:00 Asia/Tashkent: list of open orders (not delivered/cancelled) grouped by status; "Ochiq zakazlar yo'q" if none | job registered with tz |
| 34 | R37 | /orders → open orders (up to 30, newest first) with numbers and statuses; each opens as a message with buttons via `/order_<id>` link | list + detail |
| 35 | R38 | /find <number or phone> → matching orders (phone matched by digits, last 9 digits) | found / "Topilmadi" / usage hint |
| 36 | R39, S16 | /stats → counts per status, orders today, delivered sum this month | numbers |
| 37 | R40 | /start and a menu button "Admin panelni ochish" open `WEBAPP_URL/admin/` | web_app button |
| 38 | R41 | Any user not in `ADMIN_IDS` gets only "Ruxsat yo'q" for every message and callback | no data leaks |

### Admin Mini App (/admin)

| # | Mark | Story | Acceptance |
|---|------|-------|------------|
| 39 | R42 | Products list (incl. unavailable), create, edit, soft delete (with confirm step in UI) | deleted product disappears from catalog, old orders keep it |
| 40 | R43 | Upload a product image (jpeg/png/webp ≤5 MB), preview before save | stored on server |
| 41 | R44, S18 | Categories: create, rename, delete (soft; refused with a message if the category has active products) | 409 + text |
| 42 | R45 | Toggle "Mavjud emas" | catalog reflects it |
| 43 | R46 | Orders: filter by status, search by number/phone/name, open detail, change status (same state machine, customer notified, bot messages edited) | history row `source=admin_app` |
| 44 | R46.1 | Order detail shows status history (who/when) and custom-item photos | history list |
| 45 | R50 | Non-admin opening /admin → "Ruxsat yo'q" screen (API 403) | no data rendered |
| 46 | R47 | Seed: 3 categories, 10 fictional products with local SVG placeholder images; idempotent (`python -m app.seed`) | re-run does not duplicate |

### Security

| # | Mark | Story | Acceptance |
|---|------|-------|------------|
| 47 | R48 | Every `/api/*` request carries `Authorization: tma <initData>`; server checks HMAC-SHA256 per Telegram spec (secret = HMAC_SHA256("WebAppData", bot_token)), constant-time compare, and `auth_date` not older than `INIT_DATA_MAX_AGE_SECONDS` (and not in the future by >60 s) | 401 on missing/bad/expired |
| 48 | R49, S14 | Customer endpoints validate with `CUSTOMER_BOT_TOKEN`, admin endpoints with `ADMIN_BOT_TOKEN`; a customer initData is rejected by admin API | cross-token → 401 |
| 49 | R50 | Admin API additionally requires `user.id ∈ ADMIN_IDS` → else 403 | 403 |
| 50 | R51 | All bodies/queries are pydantic models with limits (names ≤100, comment ≤500, qty 1–99, ≤50 lines, price 0–100 000 000) | 422 |
| 51 | R52, S21 | Uploads: magic-bytes check (JPEG `FF D8 FF`, PNG `89 50 4E 47 0D 0A 1A 0A`, WEBP `RIFF....WEBP`), size ≤5 MB read in a bounded way, saved as `uuid4().hex + ext-from-content`; client filename ignored | 415 / 413 |
| 52 | R52.1 | A custom order line may reference only an upload made by the same user, kind `custom` | else 400 |
| 53 | R53, S12 | Rate limit per Telegram user id: orders `RATE_LIMIT_ORDERS` per `RATE_LIMIT_WINDOW_SECONDS` (5/600), uploads `RATE_LIMIT_UPLOADS` (10/600) | 429 |
| 54 | R71i, S11 | Prices and total computed server-side from DB; unavailable/deleted product → 400 | client price ignored |
| 55 | R16 | Secrets only via `.env`; only `.env.example` committed; tokens never logged | grep shows no tokens |

### Operations

| # | Mark | Story | Acceptance |
|---|------|-------|------------|
| 56 | R17 | `BOTS_ENABLED=false` or missing tokens → API starts without bots and scheduler notifications become no-ops (logged); `/health` → `{"status":"ok","bots":false}` | uvicorn starts, 200 |
| 57 | R10 | Two aiogram bots (customer, admin) polling in the same process as FastAPI (started in lifespan) | both dispatchers in one process |
| 58 | A01 → R59 | `TELEGRAM_API_BASE` setting (empty = official) so bots can point at a local mock Bot API server — used by E2E | aiogram `TelegramAPIServer.from_base` |
| 59 | R15 | Dockerfile (multi-stage: node build → python runtime), docker-compose.yml (app + caddy, volumes for db/uploads), Caddyfile (`{$DOMAIN}` reverse_proxy, auto HTTPS) — written, not run | files exist |
| 60 | R10 | Alembic migrations create the schema (`alembic upgrade head` on a fresh sqlite works); tests use `create_all` | migration test |

## Решения по реализации

- **Stack** — fixed by the brief (R10, R11, R14). Python 3.11 in `.venv` via uv; packages: fastapi, uvicorn[standard], aiogram 3, sqlalchemy[asyncio] 2, aiosqlite, alembic, pydantic-settings, apscheduler 3.x, python-multipart, tzdata; dev: pytest, pytest-asyncio, pytest-cov, httpx. Frontend: react 18, react-dom, vite, typescript, @vitejs/plugin-react, vitest, @testing-library/react, jsdom, @playwright/test.
- **Repo layout** — `backend/` (package `app`, `alembic/`, `tests/`, `uploads/`, `pyproject.toml`), `frontend/` (Vite multi-page: `app/index.html`, `admin/index.html`, `src/shared`, `src/app`, `src/admin`, `e2e/`), Dockerfile, docker-compose.yml, Caddyfile at repo root. `docs/` for PLAN/ARCHITECTURE/DECISIONS/PROGRESS/KNOWN_ISSUES.
- **One Vite build, two entries** (S15) — `npm run build` → `frontend/dist/app/index.html`, `frontend/dist/admin/index.html`, shared `dist/assets`. FastAPI mounts `frontend/dist` as static with html=True at `/` after API routes, so `/app/` and `/admin/` work; `FRONTEND_DIST` setting; missing dist → API still runs.
- **Bots via polling** — no public webhook endpoint to secure; works behind Caddy with only the Mini App needing HTTPS.
- **Notifications through one port** — `Notifier` protocol; `TelegramNotifier` (two aiogram `Bot`s) and `NullNotifier` (bots disabled). Order service calls the notifier; failures are caught and logged, never propagated. This is the test seam for everything Telegram.
- **Scheduler** — APScheduler `AsyncIOScheduler`, timezone `TIMEZONE`; jobs: `remind_and_retry` every `REMINDER_CHECK_MINUTES`, `daily_report` cron at `DAILY_REPORT_TIME`. Job bodies are plain async functions taking `(session_factory, notifier, settings, now)` so tests call them directly.
- **Order number** = DB integer id shown as `#<id>`.
- **SQLite** `DATABASE_URL=sqlite+aiosqlite:///./data/onam.db` (relative to backend); tests use a tmp file.
- **Auth header** `Authorization: tma <raw initData>` (Telegram's documented convention).
- **Frontend routing** — tiny in-house hash router (no react-router): customer `#/`, `#/product/:id`, `#/cart`, `#/custom`, `#/checkout`, `#/orders`, `#/done/:id`; admin `#/orders`, `#/orders/:id`, `#/products`, `#/products/:id|new`, `#/categories`. Telegram BackButton wired to history back.
- **Theme** — `telegram-web-app.js` loaded from `https://telegram.org/js/telegram-web-app.js` in both HTML entries; Telegram sets `--tg-theme-*` CSS vars; our CSS uses them with fallbacks.
- **Placeholders** — SVG generated by the seed script into `backend/uploads/seed/`; neutral logo SVG in the frontend.

### Data model

```text
categories(id PK, name str(100), is_deleted bool, created_at)
products(id PK, category_id FK, name str(100), sku str(32), price int (so'm, ≥0), description text(≤2000),
         image_path str|null, is_available bool, is_deleted bool, created_at, updated_at)
uploads(id PK, filename str unique, kind 'product'|'custom', uploaded_by bigint, size int, created_at)
orders(id PK, tg_user_id bigint idx, tg_username str|null, customer_name str(100), phone str(20),
       delivery_type 'delivery'|'pickup', address str(300)|null, comment str(500)|null,
       status str idx, total int, admin_notified bool, last_reminded_at dt|null, created_at, updated_at)
order_items(id PK, order_id FK, kind 'catalog'|'custom', product_id FK|null, name str(100)|null,
            sku str(32)|null, image_path str|null, unit_price int|null, quantity int, note str(300)|null)
order_status_history(id PK, order_id FK, from_status str|null, to_status str, actor_tg_id bigint|null,
                     source 'customer'|'bot'|'admin_app'|'system', created_at)
order_admin_messages(id PK, order_id FK, chat_id bigint, message_id bigint)
```

All datetimes stored UTC, timezone-aware at the edges.

### Status machine (S01)

```python
NEXT = {"new": "accepted", "accepted": "ordered", "ordered": "arrived", "arrived": "delivered"}
FINAL = {"delivered", "cancelled"}
# allowed(from, to) = NEXT.get(from) == to or (to == "cancelled" and from not in FINAL)
LABELS_UZ = {"new": "Yangi", "accepted": "Qabul qilindi", "ordered": "Faberlic'ga buyurtma berildi",
             "arrived": "Yetib keldi", "delivered": "Topshirildi", "cancelled": "Bekor qilindi"}
```

### API

Customer (initData by `CUSTOMER_BOT_TOKEN`):

| Method | Path | Body / query | Response |
|---|---|---|---|
| GET | `/health` | — (no auth) | `{"status":"ok","bots":bool}` |
| GET | `/api/config` | — | `{shop_name, shop_subtitle, pickup_address}` |
| GET | `/api/categories` | — | `[{id,name}]` |
| GET | `/api/products` | `category_id?`, `q?` | `[ProductOut]` (non-deleted, of non-deleted categories) |
| GET | `/api/products/{id}` | — | `ProductOut` / 404 |
| POST | `/api/uploads` | multipart `file` | `{upload_id, url}` (kind custom) — 413/415/429 |
| POST | `/api/orders` | `OrderCreate` | `OrderOut` 201 — 400/422/429 |
| GET | `/api/orders/my` | — | `[OrderOut]` |

Admin (initData by `ADMIN_BOT_TOKEN` + ADMIN_IDS):

| Method | Path | Body / query | Response |
|---|---|---|---|
| GET | `/api/admin/me` | — | `{id, first_name}` (UI uses it to show the 403 screen) |
| GET/POST | `/api/admin/categories` | `{name}` | list / created |
| PATCH/DELETE | `/api/admin/categories/{id}` | `{name}` | updated / 204 / 409 |
| GET | `/api/admin/products` | `q?`, `category_id?` | `[ProductOut]` incl. unavailable |
| POST | `/api/admin/products` | `ProductIn` | created |
| PATCH | `/api/admin/products/{id}` | partial `ProductIn` | updated |
| DELETE | `/api/admin/products/{id}` | — | 204 (soft) |
| POST | `/api/admin/uploads` | multipart `file` | `{upload_id, url}` (kind product) |
| GET | `/api/admin/orders` | `status?`, `q?`, `limit≤200` | `[OrderOut]` newest first |
| GET | `/api/admin/orders/{id}` | — | `OrderDetailOut` (+history) |
| POST | `/api/admin/orders/{id}/status` | `{status}` | `OrderOut` / 409 invalid transition |
| GET | `/api/admin/stats` | — | `{by_status:{}, today:int, delivered_month_sum:int}` |

```text
ProductOut  = {id, category_id, name, sku, price, description, image_url|null, is_available}
ProductIn   = {category_id, name, sku, price, description?, upload_id?, is_available?}
OrderCreate = {customer_name, phone, delivery_type, address?, comment?,
               items: [{product_id, quantity} | {custom: {name?, sku?, upload_id?, note?}, quantity}]}
OrderOut    = {id, status, status_label, customer_name, phone, delivery_type, address, comment,
               total, created_at, items: [{kind, product_id, name, sku, image_url, unit_price, quantity, note}]}
```

Errors: `{"detail": "<machine_code>"}` — codes `invalid_init_data`, `init_data_expired`, `forbidden`, `not_found`, `product_unavailable`, `invalid_transition`, `file_too_large`, `unsupported_file_type`, `rate_limited`, `invalid_upload`, `category_not_empty`. The frontend maps codes to uz text.

### Settings (.env.example)

`CUSTOMER_BOT_TOKEN`, `ADMIN_BOT_TOKEN`, `ADMIN_IDS` (comma list), `BOTS_ENABLED` (true), `WEBAPP_URL`, `TELEGRAM_API_BASE` (empty), `SHOP_NAME` (Faberlik Sotuv Bot), `PICKUP_ADDRESS`, `DATABASE_URL`, `UPLOAD_DIR`, `FRONTEND_DIST`, `INIT_DATA_MAX_AGE_SECONDS` (86400), `REMINDER_FIRST_HOURS` (2), `REMINDER_REPEAT_HOURS` (4), `REMINDER_CHECK_MINUTES` (5), `DAILY_REPORT_TIME` (09:00), `TIMEZONE` (Asia/Tashkent), `RATE_LIMIT_ORDERS` (5), `RATE_LIMIT_UPLOADS` (10), `RATE_LIMIT_WINDOW_SECONDS` (600), `MAX_UPLOAD_MB` (5), `DOMAIN` (Caddy).

## Границы и швы

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

## Процесс (из брифа) — binds every ticket

**Safety (R07)** — the brief's `<safety>` block, minus the `/autopilot` ban the user lifted (Дополнения):
- Create/modify/delete files only inside `D:\ecc tool\onam-shop`. `D:\ecc tool\prompt.md` and `D:\ecc tool\docs` are read-only. uv/npm caches outside are fine.
- Delete only with relative paths from the project root (`rm -rf frontend/dist`). Never absolute paths, `*`, or `..` in a delete. Never delete the project folder, `.git`, `.venv`. The path contains a SPACE — always quote absolute paths; run commands from inside the project with relative paths.
- Forbidden: deploy / server / domain / paid services; installing Docker; `git push` and adding remotes; global installs (`npm -g`, system `pip install`, PATH/registry/system settings); touching `~/.claude` or disabling ECC hooks (`ECC_GATEGUARD=off`, `ECC_DISABLED_HOOKS`…); reading secrets outside the project (`~/.ssh`, `~/.aws`, browser profiles, other `.env`); real Telegram API calls (tests mock bots/Telegram — R08); scraping Faberlic, downloading images (placeholders are local SVG — R09).
- Stop and ask only if a ban must be broken, or 3 stages in a row fail.
- ECC GateGuard hook asks for facts → state them briefly and retry the same action; never disable the hook.

**Environment (R67, R68, R16)** — Python 3.11.9 + uv (`uv venv --python 3.11 .venv`, packages only into `.venv`); Node 26 / npm 11, local packages; Playwright browsers `PLAYWRIGHT_BROWSERS_PATH=<project>/.playwright-browsers`, chromium only, folder in `.gitignore`. `git init` only inside onam-shop, local identity `user.name "Onam Shop Dev"`, `user.email "dev@onam-shop.local"`, never `--global`. Only `.env.example` is created; never create a real `.env` or write a token anywhere; `.env` is in `.gitignore`.

**Build order (R57)** — DB models + migrations → initData auth → product API → order API → admin bot, notifications, reminders → customer Mini App → admin Mini App. Test first (ecc:tdd-workflow / tdd-guide discipline).

**Workflow (R54–R58)**
- After every stage print "✅ [bosqich]: nima qilindi, testlar holati" and append the same to `docs/PROGRESS.md`; after a context compaction continue from `docs/PROGRESS.md` (and `.autopilot/state.js`). Local commit at the end of every stage.
- `docs/PLAN.md` (plan), `docs/ARCHITECTURE.md` (DB schema, API endpoints, bot flows), `docs/DECISIONS.md` (every decision made without asking — the S## list and later ones).
- Build errors → ecc:build-error-resolver / ecc:react-build-resolver.
- Review: ecc:python-reviewer, ecc:typescript-reviewer, ecc:react-reviewer, ecc:security-reviewer (focus: initData, admin permission, file upload). Fix every CRITICAL and HIGH. Review → fix cycle at most 2 times.
- E2E (ecc:e2e-runner / Playwright): catalog → cart → order → admin bot message (mock) → status change → customer message (mock).
- Final check: ecc:quality-gate and ecc:verification-loop, each at most 2 times.

**Limits (R60, R61, R62)** — build only listed features; no payment, registration, extra abstractions. At most 3 fix attempts per test/build error, then write it to `docs/KNOWN_ISSUES.md` and move on. Never delete, `skip`, or weaken a test to make it pass — such cases go to KNOWN_ISSUES. Long-running processes (uvicorn, vite) run in background and are stopped after checking; nothing left running at the end.

**Done when (R63–R66)**
- `pytest` and `vitest` green; backend coverage ≥ 80%.
- Playwright E2E main flow green.
- `npm run build` (both frontends) passes; backend starts in `.venv` with `uvicorn`, `BOTS_ENABLED=false`, `/health` → 200.
- Dockerfile, docker-compose.yml, Caddyfile written, not run — README says so.
- No open CRITICAL/HIGH from security review.
- `README.md` in Uzbek for a non-technical reader: (1) creating 2 bots in BotFather and linking the Mini App URL; (2) filling `.env`, finding your `ADMIN_IDS`; (3) running locally (uv + npm); (4) deploy to a VPS with docker compose + Caddy; (5) short guide for mom: accept an order, change status, add a product.
- Background processes stopped, last commit made.
- Final answer: work done, test results, KNOWN_ISSUES, manual steps for the user (tokens, domain, deploy).

## Вне рамок

| Требование | Почему не сейчас |
|---|---|
| R60 — to'lov tizimi, ro'yxatdan o'tish | brief forbids |
| R29 — rus tili | only the structure (one dictionary file) is required now |
| S22 — customer self-cancel | not in brief; admin cancels |
| webhooks | polling chosen; switch later if needed |
| real deploy, domain, real tokens | forbidden by brief; README explains the manual steps |

## Открытые места

| Placeholder | Where | What the user provides |
|---|---|---|
| S05 pickup address | `.env PICKUP_ADDRESS`, default text «[Olib ketish manzili — .env faylida PICKUP_ADDRESS]» | real address |
| tokens, ADMIN_IDS, WEBAPP_URL, DOMAIN | `.env` | BotFather tokens, own Telegram id, domain |
| S23 seed prices/products | seed script | real products entered via admin Mini App |

## Покрытие манифеста

| Требование | Раздел |
|---|---|
| R01 | 18–20 |
| R02 | 27–29, status machine |
| R03 | 31–32, S08, history table |
| R04, R05 | Решение, S20 |
| R06 | Процесс |
| R07, R08, R09 | Процесс, Test seams |
| R10 | Stack, 57, 60 |
| R11 | Stack, Theme |
| R12 | 24 |
| R13 | One Vite build, two entries |
| R14 | Test seams |
| R15 | 59 |
| R16 | 55, Settings |
| R17 | 56 |
| R18 | 1–2 |
| R19 | 3 |
| R20 | 5, 8 |
| R21 | 6 |
| R22 | 7 |
| R23 | 10 |
| R24 | 11 |
| R25 | 12–14 |
| R26 | 15–16 |
| R27 | 17 |
| R28 | 22–23 |
| R29 | 25 |
| R30 | 38, 49 |
| R31 | 27 |
| R32 | 28, 30 |
| R33 | 29 |
| R34, R35 | 31, Settings |
| R36 | 33 |
| R37 | 34 |
| R38 | 35 |
| R39 | 36 |
| R40 | 37 |
| R41 | 38 |
| R42 | 39 |
| R43 | 40 |
| R44 | 41 |
| R45 | 9, 42 |
| R46 | 43–44 |
| R47 | 46 |
| R48 | 47, 26 |
| R49 | 48 |
| R50 | 45, 49 |
| R51 | 50 |
| R52 | 51–52 |
| R53 | 21, 53 |
| R54–R68 | Процесс, 59 |
| R69i | history table, 44 |
| R70i | 4 |
| R71i | 54 |
