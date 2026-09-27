# 04 — Ikki bot (aiogram), TelegramNotifier, eslatmalar, kunlik hisobot, lifespan

**Требования:** R02, R03, R08, R10, R17, R18, R19, R30, R31, R32, R33, R34, R35, R36, R37, R38, R39, R40, R41, R70i
**Blocked by:** 03
**Зона:** `backend/app/bots/`, `backend/app/notify.py` (TelegramNotifier part), `backend/app/scheduler.py`, `backend/app/texts.py`, `backend/app/main.py` (lifespan), their tests
**Волна:** 4
**Status:** ready

## Что должно заработать

`TelegramNotifier(customer_bot, admin_bot, settings, session_factory)`: `order_created` sends `format_order` text + `order_keyboard` to every admin id (and a photo per custom line with an image, read from UPLOAD_DIR), stores `order_admin_messages`, sets `admin_notified=true` if at least one admin got it; `status_changed` edits every stored admin message (text + keyboard) and sends the customer a status message via the customer bot; every Telegram error is caught and logged. `order_keyboard`: only the next status button + "Bekor qilish" while not final; callback data `st:<order_id>:<status>`. Admin router: non-admin gets only "Ruxsat yo'q" for any message/callback; /start (greeting + "Admin panelni ochish" web_app button to `WEBAPP_URL/admin/` if WEBAPP_URL set), /orders (≤30 open, each with `/order_<id>`), `/order_<id>` (full message + keyboard), /find <id or phone> (usage hint without arg, "Topilmadi"), /stats; callback -> `change_status(source=bot)`; stale -> answer "Holat allaqachon o'zgargan" and refresh the message. Customer router: /start greeting + "Do'konni ochish" web_app button (`WEBAPP_URL/app/`); without WEBAPP_URL greeting only. Scheduler: `remind_and_retry(session_factory, notifier, settings, now)` — resend not-notified orders; remind for `new` orders older than REMINDER_FIRST_HOURS whose `last_reminded_at` is null or older than REMINDER_REPEAT_HOURS, persist `last_reminded_at`; `daily_report(...)` open orders grouped by status or "Ochiq zakazlar yo'q"; `build_scheduler` (AsyncIOScheduler, TIMEZONE, interval + cron DAILY_REPORT_TIME). `create_app` lifespan: if `settings.bots_active` -> two `Bot`s (session built with `TelegramAPIServer.from_base(TELEGRAM_API_BASE)` when set), TelegramNotifier, both dispatchers polling as background tasks, scheduler started; all stopped on shutdown. Otherwise NullNotifier; scheduler may still run. Bot texts in `app/texts.py` (Uzbek). Tests first, all Telegram calls mocked (no network).

## Из брифа, дословно

> «/start: salomlashish va "Do'konni ochish" tugmasi (WebApp tugmasi). Zakaz statusi o'zgarsa, mijozga xabar yuboradi.»
> «Yangi zakaz kelsa, darhol xabar keladi: raqam, mijoz, telefon, mahsulotlar, summa, izoh.»
> «Qabul qilindi → Faberlic'ga buyurtma berildi → Yetib keldi → Topshirildi | Bekor qilish. Tugma bosilganda xabar tahrirlanadi va mijozga bildirishnoma ketadi.»
> «"Yangi" statusidagi zakaz 2 soat ichida qabul qilinmasa, eslatma keladi. Keyin har 4 soatda takrorlanadi. Vaqtlar .env orqali sozlanadi.»
> «Kunlik hisobot: har kuni 09:00 da (Asia/Tashkent) ochiq zakazlar ro'yxati.»
> «Komandalar: /orders (ochiq zakazlar), /find <raqam yoki telefon>, /stats. "Admin panelni ochish" tugmasi /admin Mini App'ni ochadi.»
> «Ruxsatsiz foydalanuvchiga javob: "Ruxsat yo'q". Boshqa ma'lumot bermaydi.»

## Разделы спецификации

Stories 1–4, 27–38, 56–58; Решения: Bots via polling, Notifications, Scheduler; Границы: app.notify, app.bots.*, app.scheduler, app.main (`spec.md`), rules in `interfaces.md`.

## Критерии приёмки

- [ ] new order -> mocked admin bot `send_message` called for each admin with number, name, phone, items, total, comment; message ids stored
- [ ] callback `st:<id>:accepted` from admin -> status changed, all stored admin messages edited, customer bot `send_message` called; from non-admin -> 'Ruxsat yo'q', no change
- [ ] stale callback -> 'Holat allaqachon o'zgargan', no invalid transition
- [ ] customer bot raising TelegramForbiddenError -> status change still committed
- [ ] remind_and_retry: new order 1h59m -> no reminder; 2h01m -> reminder, last_reminded_at set; +3h -> none; +4h01m -> again; accepted order -> none; not-notified order is resent
- [ ] daily_report groups open orders; empty -> 'Ochiq zakazlar yo'q'; cron job at DAILY_REPORT_TIME in TIMEZONE
- [ ] /orders, /find (id, phone, no arg, not found), /stats, /start (with/without WEBAPP_URL) produce expected texts
- [ ] BOTS_ENABLED=false -> app starts, no Bot created, /health bots=false; TELEGRAM_API_BASE respected when building the Bot session (unit test)
- [ ] backend total coverage ≥ 80%
