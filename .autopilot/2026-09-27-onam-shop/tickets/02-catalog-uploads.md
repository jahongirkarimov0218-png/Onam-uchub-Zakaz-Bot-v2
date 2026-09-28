# 02 — Katalog API, admin mahsulot/kategoriya CRUD, rasm yuklash, rate limit, seed

**Требования:** R20, R21, R22, R42, R43, R44, R45, R47, R52, R53, R09, R51
**Blocked by:** 01
**Зона:** `backend/app/services/catalog.py`, `backend/app/uploads.py`, `backend/app/ratelimit.py`, `backend/app/api/catalog.py`, `backend/app/api/admin_catalog.py`, `backend/app/seed.py`, `backend/app/schemas/catalog.py`, their tests; router registration line in `app/main.py`
**Волна:** 2
**Status:** ready

## Что должно заработать

Customer endpoints `/api/config`, `/api/categories`, `/api/products` (category_id, q — case-insensitive substring on name or sku; excludes deleted products and products of deleted categories; unavailable included with flag), `/api/products/{id}`, `/api/uploads` (kind custom, rate limited). Admin endpoints for categories (create/rename/soft delete; 409 `category_not_empty` if it has active products), products (list incl. unavailable, create, partial update incl. `is_available` and `upload_id` -> image, soft delete), `/api/admin/uploads` (kind product). `app.uploads.save_upload`: reads at most MAX_UPLOAD_MB MB + 1 byte, 413 `file_too_large`, magic-byte detection JPEG/PNG/WEBP -> else 415 `unsupported_file_type`, filename `uuid4().hex + .jpg/.png/.webp` from content, row in `uploads` with uploader id; `public_url` -> `/uploads/<name>`. `app.ratelimit.RateLimiter` sliding window; app-level instances for orders and uploads from settings (stored on app.state so tests can reset); 429 `rate_limited`. Seed `python -m app.seed`: 3 categories, 10 fictional products (Uzbek names, sample prices in so'm, skus), generates local SVG placeholders into `UPLOAD_DIR/seed/`, idempotent. Tests first.

## Из брифа, дословно

> «Katalog: kategoriyalar, nom yoki artikul bo'yicha qidiruv, mahsulot kartasi (rasm, nom, artikul, narx so'mda, tavsif)»
> «Mahsulotlar: qo'shish, tahrirlash, o'chirish (soft delete), rasm yuklash (serverda saqlanadi), kategoriyalar, "mavjud emas" belgisi.»
> «faqat jpeg/png/webp, maksimal 5 MB. Fayl turi kontent bo'yicha tekshiriladi, faqat kengaytma bo'yicha emas. Fayl nomi server tomonda yangidan yaratiladi.»
> «Zakaz yaratish va rasm yuklashga rate limit.»
> «Seed: 3 ta kategoriya, 10 ta namunaviy mahsulot (to'qima nomlar, lokal placeholder rasmlar).»

## Разделы спецификации

Stories 5–9, 39–42, 46, 51, 53; API tables (catalog, admin catalog, uploads); Границы: app.uploads, app.ratelimit, app.services.catalog (`spec.md`), rules in `interfaces.md`.

## Критерии приёмки

- [ ] search by name and by sku, category filter, deleted excluded (tests)
- [ ] PNG bytes named .jpg stored as .png; text file named .png -> 415; 5 MB + 1 byte -> 413; stored name is uuid hex, client name ignored (tests)
- [ ] upload over the limit in window -> 429 (test with small limits)
- [ ] admin soft delete hides product from customer list; category with active product -> 409
- [ ] all admin catalog endpoints reject non-admin (403) and customer-token initData (401)
- [ ] seed run twice -> still 3 categories / 10 products; SVG files exist locally
