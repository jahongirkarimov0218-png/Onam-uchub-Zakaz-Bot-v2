# Манифест требований

Источник: `2026-09-27-brief.md`. Строку из этого списка может снять **только пользователь**.

Режим: full (бриф: «Sessiya davomida savol berma») · глубина: normal.

| ID | Из брифа (дословно) | Статус | Основание | Где |
|----|---------------------|--------|-----------|-----|
| R01 | «mijozlar zakazni Telegram Mini App orqali beradi» | done | — | T03 |
| R02 | «Har bir zakaz alohida admin bot'ga keladi va status bilan kuzatiladi» | done | — | T03,T04 |
| R03 | «Hech bir zakaz yo'qolmaydi yoki unutilmaydi» | done | — | T03,T04 |
| R04 | «Do'kon nomi: [DO'KON NOMI]» → доп.: «Faberlik Sotuv Bot» | done | — | T05 |
| R05 | «Faberlic'ning rasmiy logotipi, brendi yoki domenini ishlatma. Ilova "Faberlic konsultanti do'koni" sifatida ko'rinsin» | done | — | T05,T07 |
| R06 | «Qarorlarni o'zing qabul qil va docs/DECISIONS.md fayliga yoz» | done | процесс — ведёт оркестратор | spec «Процесс» |
| R07 | «Fayllarni faqat "D:\ecc tool\onam-shop" ichida yarat» (+ весь блок <safety>) | done | процесс — ведёт оркестратор | spec «Процесс» |
| R08 | «Haqiqiy Telegram API'ga murojaat qilish [taqiqlangan]. Testlarda bot va Telegram mock qilinadi» | done | — | T01,T04,T07 |
| R09 | «Placeholder rasmlarni lokal yarat (masalan, SVG)» | done | — | T02 |
| R10 | «Backend: Python 3.11, FastAPI, aiogram 3 (2 ta bot bitta jarayonda), SQLAlchemy 2 async, SQLite (aiosqlite), Alembic, pydantic-settings, APScheduler» | done | — | T01,T04 |
| R11 | «Frontend: React 18 + Vite + TypeScript. Telegram WebApp SDK (telegram-web-app.js)» | done | — | T05 |
| R12 | «Telegram themeParams bilan light/dark mavzu» | done | — | T05,T06 |
| R13 | «2 ta frontend entry: /app (mijoz Mini App) va /admin (admin Mini App)» | done | — | T05,T06 |
| R14 | «Test: pytest + pytest-asyncio + httpx; frontend uchun vitest; E2E uchun Playwright (Telegram mock bilan)» | done | — | T07 |
| R15 | «Deploy fayllari: Dockerfile, docker-compose.yml, Caddyfile (avtomatik HTTPS)… faqat yoziladi, ishga tushirilmaydi» | done | — | T07 |
| R16 | «Barcha sirlar faqat .env faylida… Faqat .env.example yarat… .env faylini .gitignore'ga qo'sh» | done | — | T01 |
| R17 | «BOTS_ENABLED sozlamasi bo'lsin. Token yo'q yoki BOTS_ENABLED=false bo'lsa, API botlarsiz ishga tushadi» | done | — | T01,T04 |
| R18 | «/start: salomlashish va "Do'konni ochish" tugmasi (WebApp tugmasi)» | done | — | T04 |
| R19 | «Zakaz statusi o'zgarsa, mijozga xabar yuboradi» | done | — | T04 |
| R20 | «Katalog: kategoriyalar» | done | — | T02,T05 |
| R21 | «nom yoki artikul bo'yicha qidiruv» | done | — | T02,T05 |
| R22 | «mahsulot kartasi (rasm, nom, artikul, narx so'mda, tavsif)» | done | — | T02,T05 |
| R23 | «Savat: miqdorni o'zgartirish, jami summa» | done | — | T05 |
| R24 | «Savat localStorage'da saqlanadi» | done | — | T05 |
| R25 | «"Katalogda yo'q mahsulot" formasi: mijoz nom, artikul yoki rasm yuborib zakaz beradi. Bu asosiy xususiyat» | done | — | T03,T05 |
| R26 | «Checkout: ism, telefon (Telegram requestContact orqali yoki qo'lda)» | done | — | T03,T05 |
| R27 | «yetkazish yoki olib ketish, izoh» | placeholder | S05: olib ketish manzili — PICKUP_ADDRESS bo'sh bo'lsa ko'rinadigan zaglushka | T03,T05 |
| R28 | «"Mening zakazlarim": ro'yxat va har birining statusi» | done | — | T03,T05 |
| R29 | «UI tili: o'zbek (lotin). Barcha matnlar bitta i18n faylda» | done | — | T05,T06 |
| R30 | «ADMIN BOT… faqat ADMIN_IDS ro'yxatidagilar uchun» | done | — | T04 |
| R31 | «Yangi zakaz kelsa, darhol xabar keladi: raqam, mijoz, telefon, mahsulotlar, summa, izoh» | done | — | T04 |
| R32 | «inline tugmalar: Qabul qilindi → Faberlic'ga buyurtma berildi → Yetib keldi → Topshirildi \| Bekor qilish» | done | — | T04 |
| R33 | «Tugma bosilganda xabar tahrirlanadi va mijozga bildirishnoma ketadi» | done | — | T04 |
| R34 | «"Yangi" statusidagi zakaz 2 soat ichida qabul qilinmasa, eslatma keladi. Keyin har 4 soatda takrorlanadi» | done | — | T04 |
| R35 | «Vaqtlar .env orqali sozlanadi» | done | — | T04 |
| R36 | «Kunlik hisobot: har kuni 09:00 da (Asia/Tashkent) ochiq zakazlar ro'yxati» | done | — | T04 |
| R37 | «/orders (ochiq zakazlar)» | done | — | T04 |
| R38 | «/find <raqam yoki telefon>» | done | — | T04 |
| R39 | «/stats» | done | — | T03,T04 |
| R40 | «"Admin panelni ochish" tugmasi /admin Mini App'ni ochadi» | done | — | T04 |
| R41 | «Ruxsatsiz foydalanuvchiga javob: "Ruxsat yo'q". Boshqa ma'lumot bermaydi» | done | — | T04 |
| R42 | «Mahsulotlar: qo'shish, tahrirlash, o'chirish (soft delete)» | done | — | T02,T06 |
| R43 | «rasm yuklash (serverda saqlanadi)» | done | — | T02,T06 |
| R44 | «kategoriyalar» (admin boshqaradi) | done | — | T02,T06 |
| R45 | «"mavjud emas" belgisi» | done | — | T02,T05,T06 |
| R46 | «Zakazlar: status bo'yicha filtr, qidiruv, statusni o'zgartirish» | done | — | T03,T06 |
| R47 | «Seed: 3 ta kategoriya, 10 ta namunaviy mahsulot (to'qima nomlar, lokal placeholder rasmlar)» | done | — | T02 |
| R48 | «Har bir API so'rovida Telegram initData HMAC-SHA256 bilan tekshiriladi va auth_date muddati ham tekshiriladi» | done | — | T01,T05 |
| R49 | «Mijoz va admin uchun alohida bot tokeni bilan» | done | — | T01 |
| R50 | «/admin API faqat ADMIN_IDS uchun ochiq» | done | — | T01,T06 |
| R51 | «Input validatsiya: pydantic» | done | — | T01,T02,T03 |
| R52 | «faqat jpeg/png/webp, maksimal 5 MB. Fayl turi kontent bo'yicha tekshiriladi… Fayl nomi server tomonda yangidan yaratiladi» | done | — | T02,T03 |
| R53 | «Zakaz yaratish va rasm yuklashga rate limit» | done | — | T02,T03,T05 |
| R54 | «Har bosqich oxirida chiqar: "✅ [bosqich]…" Xuddi shu ma'lumotni docs/PROGRESS.md fayliga yoz» | done | процесс — ведёт оркестратор | spec «Процесс» |
| R55 | «Reja… → docs/PLAN.md… → docs/ARCHITECTURE.md (DB sxemasi, API endpointlari, bot oqimlari)» | done | процесс — ведёт оркестратор | spec «Процесс» |
| R56 | «Har bosqich oxirida lokal commit qil» | done | процесс — ведёт оркестратор | spec «Процесс» |
| R57 | «test birinchi yoziladi» (TDD) | done | процесс — ведёт оркестратор | spec «Процесс» |
| R58 | «Review… Barcha CRITICAL va HIGH topilmalarni tuzat» | done | процесс — ведёт оркестратор | spec «Процесс» |
| R59 | «E2E… katalog → savat → zakaz → admin bot'ga xabar (mock) → status o'zgarishi → mijozga xabar (mock)» | done | — | T07 |
| R60 | «To'lov tizimi, ro'yxatdan o'tish yoki ortiqcha abstraksiyalar qo'shma» | done | процесс — ведёт оркестратор | spec «Процесс» |
| R61 | «Tuzalmasa, docs/KNOWN_ISSUES.md fayliga yoz» / testni skip qilma | done | процесс — ведёт оркестратор | spec «Процесс» |
| R62 | «Sessiya oxirida hech qanday fon jarayoni qolmasin» | done | процесс — ведёт оркестратор | spec «Процесс» |
| R63 | «pytest va vitest yashil, backend coverage ≥ 80%» | done | — | T07 |
| R64 | «npm run build (ikkala frontend) xatosiz… uvicorn bilan BOTS_ENABLED=false rejimida… /health 200» | done | — | T07 |
| R65 | «README.md o'zbek tilida, texnik bo'lmagan odam uchun» + 5 bo'lim (BotFather, .env/ADMIN_IDS, lokal, VPS deploy, onam uchun qo'llanma); Docker fayllari ishga tushirilmagani aytilgan | done | — | T07 |
| R66 | «Yakuniy javob: bajarilgan ishlar ro'yxati, test natijalari, KNOWN_ISSUES, foydalanuvchi qo'lda bajarishi kerak bo'lgan qadamlar» | done | процесс — ведёт оркестратор | spec «Процесс» |
| R67 | «Playwright brauzerlarini loyiha ichiga o'rnat: PLAYWRIGHT_BROWSERS_PATH… Faqat chromium… .gitignore'ga qo'sh» | done | — | T07 |
| R68 | «uv venv --python 3.11 .venv. Paketlarni faqat shu .venv ichiga o'rnat» / npm lokal | done | — | T01 |
| R69i | *(подразумевается)* zakaz statusi tarixi — «status bilan kuzatiladi», «unutilmaydi» | done | — | T03 |
| R70i | *(подразумевается)* mijoz botni hech qachon ochmagan bo'lsa bildirishnoma yetmaydi — xato zakazni buzmasligi kerak | done | — | T03,T04 |
| R71i | *(подразумевается)* zakaz summasi server tomonda hisoblanadi (mijoz narxni soxtalashtira olmaydi) | done | — | T03 |

## Самобрифинг (full mode)

Каждая строка выше либо однозначна из брифа, либо закрыта одним из решений ниже.
`ASSUMPTION` — принято за пользователя, идёт в итоговый отчёт. `PLACEHOLDER` — факт о пользователе, остаётся видимой заглушкой.

| # | Строки | Решение |
|---|--------|---------|
| S01 | R02, R32, R69i | ASSUMPTION — статусы: `new` (Yangi) → `accepted` (Qabul qilindi) → `ordered` (Faberlic'ga buyurtma berildi) → `arrived` (Yetib keldi) → `delivered` (Topshirildi); `cancelled` (Bekor qilindi) из любого незавершённого. Переход только на один шаг вперёд или в отмену. Каждое изменение пишется в `order_status_history` (кто, когда, с какого на какой). |
| S02 | R25 | ASSUMPTION — «katalogda yo'q» = отдельная строка корзины (`custom`: nom и/или artikul и/или rasm, miqdor, izoh); оформляется тем же checkout, можно вместе с каталожными товарами. Цена такой строки неизвестна — в заказе «narx keyin aniqlanadi», в сумму не входит. |
| S03 | R26 | ASSUMPTION — телефон нормализуется к `+998XXXXXXXXX`, принимаются также другие международные номера 9–15 цифр. |
| S04 | R27 | ASSUMPTION — при «yetkazish» адрес обязателен; при «olib ketish» показывается адрес самовывоза. |
| S05 | R27 | PLACEHOLDER — адрес самовывоза: `PICKUP_ADDRESS` в `.env`, по умолчанию видимая заглушка «[Olib ketish manzili — .env faylida PICKUP_ADDRESS]». |
| S06 | R34, R35, R03 | ASSUMPTION — напоминания: APScheduler каждые `REMINDER_CHECK_MINUTES` (5) проверяет `new`-заказы старше `REMINDER_FIRST_HOURS` (2), повтор каждые `REMINDER_REPEAT_HOURS` (4); `last_reminded_at` хранится в БД, поэтому перезапуск ничего не теряет. |
| S07 | R36 | ASSUMPTION — время отчёта `DAILY_REPORT_TIME=09:00`, `TIMEZONE=Asia/Tashkent` в `.env`. |
| S08 | R03, R31 | ASSUMPTION — если уведомление админу не ушло (боты выключены / ошибка Telegram), у заказа остаётся `admin_notified=false`; тот же планировщик повторяет отправку. Заказ создаётся в любом случае. |
| S09 | R33 | ASSUMPTION — сообщения о заказе у каждого админа хранятся (`order_admin_messages`); смена статуса из бота или из admin Mini App редактирует все. |
| S10 | R70i | ASSUMPTION — ошибка отправки клиенту (не открыл бота / заблокировал) логируется, заказ и смена статуса не падают. |
| S11 | R71i | ASSUMPTION — сумма и цены строк считаются на сервере из БД, цена фиксируется в строке заказа; недоступный или удалённый товар заказать нельзя (400). |
| S12 | R53 | ASSUMPTION — rate limit в памяти по Telegram user id: заказы 5 за 10 мин, загрузки 10 за 10 мин (`.env`), ответ 429. |
| S13 | R48 | ASSUMPTION — `INIT_DATA_MAX_AGE_SECONDS=86400` (24 ч). |
| S14 | R49, R50 | ASSUMPTION — `/api/*` (клиент) проверяет initData токеном `CUSTOMER_BOT_TOKEN`; `/api/admin/*` — токеном `ADMIN_BOT_TOKEN` + `user.id ∈ ADMIN_IDS`. Никакого «dev-обхода» проверки нет; E2E подписывает initData тестовым токеном. |
| S15 | R13, R64 | ASSUMPTION — один Vite-проект, две HTML-точки входа (multi-page) → одна команда `npm run build` собирает обе; FastAPI раздаёт `dist` на `/app` и `/admin`. |
| S16 | R39 | ASSUMPTION — `/stats`: число заказов по статусам, заказов сегодня, сумма `delivered` за текущий месяц. |
| S17 | R38, R46 | ASSUMPTION — поиск заказа: по номеру, телефону (по цифрам), имени. |
| S18 | R44 | ASSUMPTION — категории: создать, переименовать, удалить (soft) — только если в ней нет активных товаров. |
| S19 | R45 | ASSUMPTION — «mavjud emas» товар виден в каталоге серым, в корзину не добавляется. |
| S20 | R04, R05 | ASSUMPTION — название `SHOP_NAME` (по умолчанию «Faberlik Sotuv Bot»), подзаголовок «Faberlic konsultanti do'koni»; логотип — собственная нейтральная SVG-иконка, без фирменного знака Faberlic. |
| S21 | R43, R52 | ASSUMPTION — файлы в `backend/uploads/` под именем `uuid4.<ext по содержимому>`, раздаются по `/uploads/…`; имя не угадывается. |
| S22 | R28 | ASSUMPTION — клиент видит только свои заказы (по Telegram user id); отменить сам не может (в брифе нет). |
| S23 | R22, R47 | ASSUMPTION — цены в seed — явно выдуманные образцы для демо, помечены в README как «namunaviy»; реальные цены вводит админ. |
