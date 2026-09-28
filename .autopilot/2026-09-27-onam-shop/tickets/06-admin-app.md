# 06 — Admin Mini App (/admin)

**Требования:** R12, R13, R29, R42, R43, R44, R45, R46, R50
**Blocked by:** 05
**Зона:** `frontend/src/admin/`; additive keys in `frontend/src/shared/i18n/uz.ts`; new `frontend/src/shared/status.ts`
**Волна:** 3
**Status:** ready

## Что должно заработать

Admin entry using `src/shared` (do not fork shared code; additive changes to shared i18n are allowed — add keys only). On load calls `/api/admin/me`; 401/403 -> "Ruxsat yo'q" screen, nothing else rendered. Tabs: Zakazlar / Mahsulotlar / Kategoriyalar. Orders: status filter chips (incl. all/open), search box (number/phone/name), list newest first; detail with items (custom lines with photo), customer, phone (tel link), delivery/address, comment, total, status history (who/when/source), buttons for allowed transitions only (next + "Bekor qilish" with an inline confirm step), refresh after change. Products: list incl. unavailable (badge), search, create/edit form (category select, name, sku, price, description, image upload with preview, "Mavjud emas" toggle), soft delete with inline confirm step (no window.confirm). Categories: list, create, rename inline, delete (409 -> "Kategoriyada mahsulotlar bor"). Status machine constants mirrored in `src/shared/status.ts` (labels from i18n). Tests first (vitest + Testing Library, mocked fetch/Telegram).

## Из брифа, дословно

> «Mahsulotlar: qo'shish, tahrirlash, o'chirish (soft delete), rasm yuklash (serverda saqlanadi), kategoriyalar, "mavjud emas" belgisi.»
> «Zakazlar: status bo'yicha filtr, qidiruv, statusni o'zgartirish.»
> «/admin API faqat ADMIN_IDS uchun ochiq.»

## Разделы спецификации

Stories 39–45; API admin table; Status machine (`spec.md`), rules in `interfaces.md`.

## Критерии приёмки

- [ ] 403 from /api/admin/me -> 'Ruxsat yo'q' screen only (test)
- [ ] order detail shows only allowed transition buttons; cancel needs confirm; change calls POST status and refreshes (tests)
- [ ] status filter and search send correct query params (test)
- [ ] product create/edit/delete(confirm)/availability toggle call the right endpoints; image upload preview (tests)
- [ ] category delete 409 shows message (test)
- [ ] `npm run build` still green; customer app tests still green
