# 03 — Zakaz xizmati: yaratish, status mashinasi, tarix, mijoz va admin zakaz API, statistika, Notifier porti

**Требования:** R01, R02, R03, R25, R26, R27, R28, R39, R46, R51, R52, R53, R69i, R70i, R71i
**Blocked by:** 02
**Зона:** `backend/app/services/orders.py`, `backend/app/notify.py` (Protocol + NullNotifier only), `backend/app/api/orders.py`, `backend/app/api/admin_orders.py`, `backend/app/schemas/orders.py`, their tests; router registration in `app/main.py`
**Волна:** 3
**Status:** ready

## Что должно заработать

`app.services.orders`: `create_order` validates items (catalog: product exists, not deleted, available -> else 400 `product_unavailable`; price snapshot from DB, client price ignored; custom: at least one of name/sku/upload_id, upload must be kind custom and uploaded by the same user -> else 400 `invalid_upload`), normalizes phone (+998XXXXXXXXX, or 9–15 digits international), address required for delivery, computes total from catalog lines only, writes history row (None -> new, source customer), then calls `notifier.order_created(order)` inside try/except (failure logged, order kept, `admin_notified` false unless the notifier set it). `change_status` enforces the machine (409 `invalid_transition`), writes history (actor, source), calls `notifier.status_changed(order)` safely. `search_orders` by id, phone digits (last 9), name substring; `open_orders`; `stats(session, now, tz)`. `app.notify`: `Notifier` Protocol (`order_created`, `status_changed`, `reminder`, `daily_report`), `NullNotifier` (logs only). A `FakeNotifier` in tests records calls. Endpoints: `POST /api/orders` (rate limited per user, 201), `GET /api/orders/my`, admin `GET /api/admin/orders` (status, q, limit), `GET /api/admin/orders/{id}` (+history, item image urls), `POST /api/admin/orders/{id}/status` (source admin_app), `GET /api/admin/stats`. Tests first.

## Из брифа, дословно

> «Har bir zakaz alohida admin bot'ga keladi va status bilan kuzatiladi. Hech bir zakaz yo'qolmaydi yoki unutilmaydi.»
> «"Katalogda yo'q mahsulot" formasi: mijoz nom, artikul yoki rasm yuborib zakaz beradi. Bu asosiy xususiyat.»
> «Checkout: ism, telefon (Telegram requestContact orqali yoki qo'lda), yetkazish yoki olib ketish, izoh.»
> «"Mening zakazlarim": ro'yxat va har birining statusi.»
> «Zakazlar: status bo'yicha filtr, qidiruv, statusni o'zgartirish.»

## Разделы спецификации

Stories 4, 12–22, 29 (service part), 32 (flag), 36, 43–44, 50, 52–54; Status machine; API order tables; Границы: app.services.orders, app.notify (`spec.md`), rules in `interfaces.md`.

## Критерии приёмки

- [ ] order with catalog + custom lines: total = sum of catalog lines using DB prices; custom line has null price (test)
- [ ] unavailable/deleted product -> 400; foreign or product-kind upload in custom line -> 400; empty custom line -> 422
- [ ] invalid phone -> 422; delivery without address -> 422; phone normalized to +998…
- [ ] every allowed transition works, every forbidden one -> 409; history rows written with source/actor
- [ ] notifier raising an exception does not break order creation or status change
- [ ] customer sees only own orders; admin filter by status and search by id/phone/name; stats correct for a fixed `now`
- [ ] order over the rate limit -> 429
- [ ] coverage of this zone ≥ 80%
