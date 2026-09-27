# 05 — Frontend asosi + mijoz Mini App (/app)

**Требования:** R04, R05, R11, R12, R13, R20, R21, R22, R23, R24, R25, R26, R27, R28, R29, R45, R48, R53
**Blocked by:** 01
**Зона:** `frontend/` except `frontend/src/admin/`, `frontend/e2e/`, `frontend/playwright.config.ts` (the `frontend/admin/index.html` entry and a stub `src/admin/main.tsx` are created here)
**Волна:** 2
**Status:** ready

## Что должно заработать

Vite + React 18 + TS project in `frontend/`, multi-page: `app/index.html` and `admin/index.html` (admin entry renders a stub from `src/admin/main.tsx` that ticket 06 replaces), both loading `https://telegram.org/js/telegram-web-app.js`. `npm run build` -> `dist/app/index.html`, `dist/admin/index.html`; `npm run dev` proxies `/api` and `/uploads` to `http://127.0.0.1:8000`; `npm test` = `vitest run` (jsdom). `src/shared`: `telegram.ts` (safe wrapper around `window.Telegram?.WebApp`: initData, user, ready/expand, requestContact -> Promise<phone|null>, BackButton, haptic), `api.ts` (fetch with `Authorization: tma <initData>`, JSON, maps `detail` codes to i18n keys, typed errors incl. 429/413/415), `i18n/uz.ts` + `t(key, params)` (ALL UI strings), `format.ts` (`formatSum` -> `125 000 so'm`, dates), `router.ts` (hash router hook), `theme.css` using `--tg-theme-*` vars with light/dark fallbacks, neutral SVG logo; shop name/subtitle from `/api/config`. Customer screens: Catalog (category chips incl. "Hammasi", search, cards with image/name/sku/price, unavailable greyed "Mavjud emas", empty states with a link to the custom form), Product detail, Cart (qty 1..99, remove, total excludes custom lines "Narx keyin aniqlanadi", localStorage `onam-cart-v1`, corrupt -> empty), Custom item form (name/sku/photo — at least one, qty, note; photo uploaded immediately with error texts), Checkout (name prefilled from TG user, phone via "Kontaktni yuborish" or manual with validation, delivery/pickup with address rules and pickup address display, comment ≤500, submit disabled while sending, on success clear cart and go to `#/done/:id`, on error keep everything), My orders (newest first, status badge, items, total, empty state), "open via Telegram" screen when initData is empty. Tests first with vitest + Testing Library (mock Telegram + fetch).

## Из брифа, дословно

> «Katalog: kategoriyalar, nom yoki artikul bo'yicha qidiruv, mahsulot kartasi (rasm, nom, artikul, narx so'mda, tavsif).»
> «Savat: miqdorni o'zgartirish, jami summa. Savat localStorage'da saqlanadi.»
> «"Katalogda yo'q mahsulot" formasi: mijoz nom, artikul yoki rasm yuborib zakaz beradi. Bu asosiy xususiyat.»
> «Checkout: ism, telefon (Telegram requestContact orqali yoki qo'lda), yetkazish yoki olib ketish, izoh.»
> «UI tili: o'zbek (lotin). Barcha matnlar bitta i18n faylda (keyinchalik rus tilini qo'shish oson bo'lsin).»
> «Telegram themeParams bilan light/dark mavzu.»

## Разделы спецификации

Stories 5–26; Решения: One Vite build, Frontend routing, Theme, Placeholders; API customer table; Границы: frontend src/shared (`spec.md`), rules in `interfaces.md`.

## Критерии приёмки

- [ ] `npm run build` succeeds and produces both entry HTMLs
- [ ] cart: add, ±, remove, total, persistence across remount, corrupt localStorage -> empty cart (tests)
- [ ] custom form requires at least one of name/sku/photo; upload error 415/413 shown in uz (tests)
- [ ] checkout: phone validation, address required for delivery only, double submit sends one request, failure keeps cart, success clears cart (tests)
- [ ] catalog: category filter + search call API with params; unavailable product cannot be added; empty state renders (tests)
- [ ] no hard-coded UI strings outside i18n
- [ ] no initData -> 'Telegram orqali oching' screen, no API call
