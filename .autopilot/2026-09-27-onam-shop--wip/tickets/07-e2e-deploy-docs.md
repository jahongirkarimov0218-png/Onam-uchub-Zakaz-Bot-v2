# 07 — E2E (Playwright + mock Telegram), Docker/Caddy fayllari, README (uz)

**Требования:** R05, R08, R14, R15, R59, R63, R64, R65, R67
**Blocked by:** 04, 06
**Зона:** `frontend/e2e/`, `frontend/playwright.config.ts`, e2e script in `frontend/package.json`, `Dockerfile`, `docker-compose.yml`, `Caddyfile`, `.dockerignore`, `README.md`
**Волна:** 5
**Status:** ready

## Что должно заработать

Playwright (chromium only, browsers in `.playwright-browsers` via PLAYWRIGHT_BROWSERS_PATH; `npm run e2e`). E2E harness: a Node mock Telegram Bot API server (`e2e/mock-telegram.ts`, http on a local port) answering `getMe`, `getUpdates` (empty, short wait), `deleteWebhook`, `sendMessage`, `sendPhoto`, `editMessageText`, `editMessageReplyMarkup`, `answerCallbackQuery`, `setMyCommands`, recording every call with a `/__calls` inspection route. Global setup: build frontend, start uvicorn from `backend/` with a temp DB, migrated + seeded, env: fake tokens, `ADMIN_IDS` = test admin id, `BOTS_ENABLED=true`, `TELEGRAM_API_BASE` = mock server, `FRONTEND_DIST` = built dist; teardown stops both. A helper signs initData in Node (same algorithm as backend) and injects `window.Telegram.WebApp` via `page.addInitScript` (customer token for /app, admin token for /admin). Main flow test: open /app -> catalog -> add product -> cart -> checkout (manual phone, pickup) -> success number -> mock recorded admin `sendMessage` containing the number -> open /admin as admin -> order -> "Qabul qilindi" -> mock recorded customer `sendMessage` with "Qabul qilindi" and admin `editMessageText`. Deploy files (written, NOT run): multi-stage `Dockerfile` (node build frontend -> python:3.11-slim, install backend, `alembic upgrade head` then uvicorn), `docker-compose.yml` (app + caddy:2, volumes for data, uploads, caddy data; env_file .env), `Caddyfile` (`{$DOMAIN}` -> reverse_proxy app:8000). `README.md` in Uzbek for a non-technical reader with sections: (1) BotFather — 2 bots, Mini App URL, (2) `.env` filling and finding ADMIN_IDS, (3) local run (uv + npm, seed, uvicorn, BOTS_ENABLED=false), (4) VPS deploy with docker compose + Caddy, (5) short guide for mom: accept an order, change status, add a product; explicit note that Docker/Caddy files were written but not run; note that seed prices are samples; Faberlic-not-official disclaimer.

## Из брифа, дословно

> «E2E: ecc:e2e-runner. Asosiy oqim: katalog → savat → zakaz → admin bot'ga xabar (mock) → status o'zgarishi → mijozga xabar (mock).»
> «Deploy fayllari: Dockerfile, docker-compose.yml, Caddyfile (avtomatik HTTPS). Bu fayllar faqat yoziladi, ishga tushirilmaydi.»
> «README.md o'zbek tilida, texnik bo'lmagan odam uchun yozilgan. Unda: (1) BotFather'da 2 ta bot yaratish va Mini App URL'ni ulash; (2) .env to'ldirish, ADMIN_IDS'ni topish; (3) lokal ishga tushirish (uv + npm); (4) VPS'ga docker compose + Caddy bilan deploy; (5) onam uchun qisqa qo'llanma: zakazni qabul qilish, status o'zgartirish, mahsulot qo'shish.»
> «Playwright brauzerlarini loyiha ichiga o'rnat… Faqat chromium o'rnatiladi.»

## Разделы спецификации

Stories 58, 59; Test seams (E2E); Процесс -> Done when (`spec.md`), rules in `interfaces.md`.

## Критерии приёмки

- [ ] `npm run e2e` green: main flow passes end to end with mock Telegram, no real network
- [ ] mock server records admin sendMessage with the order number and customer sendMessage with the new status
- [ ] no process left running after the E2E run
- [ ] Dockerfile, docker-compose.yml, Caddyfile present and plausible; not executed
- [ ] README.md has all 5 sections in Uzbek plus the 'not run' note
- [ ] `.playwright-browsers/` stays git-ignored
