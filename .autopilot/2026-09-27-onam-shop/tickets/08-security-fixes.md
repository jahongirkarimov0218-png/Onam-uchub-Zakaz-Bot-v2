# 08 — Xavfsizlik tuzatishlari (final security review)

**Требования:** R52, R53, R15
**Blocked by:** 01–07
**Зона:** `backend/app/main.py` (request-size middleware), new `backend/app/bodylimit.py` if needed, its tests, `Caddyfile`, `Dockerfile`
**Волна:** 6
**Status:** ready

## Что должно заработать

Final whole-project security review found one HIGH: an oversized multipart upload is fully received and spooled before the 5 MB check runs (no body-size cap anywhere), so an authenticated user can exhaust disk/memory. Fix it in depth: the app itself rejects requests to the upload endpoints (`POST /api/uploads`, `POST /api/admin/uploads`) whose body exceeds `MAX_UPLOAD_MB` + small multipart overhead with 413 `file_too_large` — by `Content-Length` up front and by counting streamed bytes when Content-Length is absent/lying (pure ASGI middleware, no new packages); and Caddy caps request bodies (`request_body { max_size … }`). Also MEDIUM: the runtime container runs as root — add a non-root user in the Dockerfile with writable data/uploads dirs.

## Из брифа, дословно

> «faqat jpeg/png/webp, maksimal 5 MB. Fayl turi kontent bo'yicha tekshiriladi»
> «Zakaz yaratish va rasm yuklashga rate limit.»
> «Deploy fayllari: Dockerfile, docker-compose.yml, Caddyfile (avtomatik HTTPS). Bu fayllar faqat yoziladi, ishga tushirilmaydi.»

## Разделы спецификации

Stories 51, 53, 59 (`spec.md`), rules in `interfaces.md`.

## Критерии приёмки

- [ ] Upload request with `Content-Length` above the limit → 413 `file_too_large` before the body is read (test)
- [ ] Chunked/streamed upload body exceeding the limit without Content-Length → 413, not spooled past the limit (test)
- [ ] Normal uploads (≤5 MB) and all other endpoints unaffected; full backend suite green, coverage ≥80%
- [ ] Caddyfile caps request body size (≈6 MB) — written, not run
- [ ] Dockerfile runtime stage runs as a non-root user; data/uploads writable — written, not run
