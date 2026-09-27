# 01 — Backend asosi: sozlamalar, DB, migratsiya, initData auth, /health

**Требования:** R10, R16, R17, R48, R49, R50, R51, R68, R08
**Blocked by:** —
**Зона:** `backend/` (package skeleton: pyproject, app/config, app/db, app/models, app/auth, app/main, alembic, tests/conftest), `.env.example`
**Волна:** 1
**Status:** ready

## Что должно заработать

Backend project exists and runs: `backend/pyproject.toml` (package `app`, deps + dev extras from interfaces.md; pytest config with asyncio_mode=auto), `.venv` populated. `app.config.Settings` reads every setting from spec «Settings» (defaults as listed; `ADMIN_IDS` comma list -> `admin_id_set`; `bots_active` = BOTS_ENABLED and both tokens non-empty). `app.db`/`app.models`: all 7 tables of the data model; Alembic set up (`backend/alembic.ini`, `backend/alembic/`) with one initial migration equal to the models. `app.auth.validate_init_data` implements Telegram WebApp initData validation (HMAC-SHA256, secret = HMAC_SHA256(key="WebAppData", msg=bot_token), constant-time compare, auth_date max age and not >60s in the future) and FastAPI deps `customer_user` (CUSTOMER_BOT_TOKEN) / `admin_user` (ADMIN_BOT_TOKEN + ADMIN_IDS -> 403 `forbidden`). `app.main.create_app(settings=None, notifier=None)` with `/health` -> `{"status":"ok","bots":bool}`, error format `{"detail": code}`, `/uploads` static from UPLOAD_DIR (created if missing), and `FRONTEND_DIST` mounted statically at `/` (html=True) only if the dir exists, registered after API routers so API wins. `/api/admin/me` endpoint. Test infrastructure: `backend/tests/conftest.py` with tmp sqlite DB (`create_all`), a `sign_init_data(user, bot_token, auth_date=None)` helper, a `FakeNotifier` fixture hook, httpx AsyncClient over ASGITransport. `.env.example` at repo root with every setting, empty tokens, comments in Uzbek. Tests written first.

## Из брифа, дословно

> «Backend: Python 3.11, FastAPI, aiogram 3 (2 ta bot bitta jarayonda), SQLAlchemy 2 async, SQLite (aiosqlite), Alembic, pydantic-settings, APScheduler»
> «Har bir API so'rovida Telegram initData HMAC-SHA256 bilan tekshiriladi va auth_date muddati ham tekshiriladi. Mijoz va admin uchun alohida bot tokeni bilan.»
> «/admin API faqat ADMIN_IDS uchun ochiq.»
> «BOTS_ENABLED sozlamasi bo'lsin. Token yo'q yoki BOTS_ENABLED=false bo'lsa, API botlarsiz ishga tushadi.»
> «Faqat .env.example yarat. Haqiqiy .env faylini yaratma»

## Разделы спецификации

Stories 47–50, 55, 56, 60; Решения: Stack, Repo layout, SQLite, Auth header, Data model, Settings; Границы: app.config, app.db/models, app.auth, app.main (`spec.md`), rules in `interfaces.md`.

## Критерии приёмки

- [ ] `alembic upgrade head` on a fresh sqlite file creates all 7 tables (test)
- [ ] valid initData -> user parsed; tampered hash, missing hash, wrong token, expired auth_date, future auth_date -> `InitDataError` with code (tests)
- [ ] customer initData on `/api/admin/me` -> 401; admin-token initData with id not in ADMIN_IDS -> 403; admin in list -> 200
- [ ] `/health` -> 200 `{status: ok, bots: false}` when BOTS_ENABLED=false or tokens empty
- [ ] `.env.example` lists every setting from spec, no values for secrets; no `.env` created
- [ ] app imports and serves with BOTS_ENABLED=false (ASGI smoke test)
