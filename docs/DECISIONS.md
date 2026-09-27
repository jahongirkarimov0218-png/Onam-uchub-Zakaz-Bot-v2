# Qarorlar (DECISIONS)

Brief: "Sessiya davomida savol berma. Qarorlarni o'zing qabul qil va docs/DECISIONS.md fayliga yoz." Quyidagi qarorlar foydalanuvchidan so'ramasdan qabul qilindi. `ASSUMPTION` — men qabul qilgan qaror; `PLACEHOLDER` — foydalanuvchi to'ldirishi kerak bo'lgan ma'lumot.

## Sessiya boshida foydalanuvchi bergan javoblar

- prompt.md `/autopilot` ni taqiqlagan edi, foydalanuvchi esa `/autopilot` yozdi. Savol berildi → javob: «/autopilot ishlat». Ish autopilot jarayoni bilan boradi, ECC agentlari (reviewer, e2e, quality-gate) uning ichida ishlatiladi.
- Do'kon nomi: «Faberlik Sotuv Bot» ("Faberlic konsultanti do'koni" sifatida, rasmiy Faberlic emas).

## Jarayon qarorlari

- D-P1: Reja va arxitektura autopilot spetsifikatsiyasidan olindi (`docs/PLAN.md`, `docs/ARCHITECTURE.md`), alohida ecc:planner / ecc:architect chaqirilmadi — spetsifikatsiya mustaqil agent tomonidan briefga nisbatan tekshirildi (G2).
- D-P2: Bot rejimi — polling (webhook emas): ochiq webhook endpoint kerak emas.
- D-P3: Bitta Vite loyiha, ikki HTML kirish nuqtasi (/app va /admin) — bitta `npm run build`.
- D-P4: E2E da Telegram Bot API o'rniga lokal mock server (`TELEGRAM_API_BASE`) — haqiqiy Telegramga murojaat yo'q.
- D-P5: Dashboard serveri: Windows'da `sync.py` jarayonni aniqlay olmay har safar yangi server ochgan; ortiqchalari to'xtatildi, bitta server qoldirildi.

## Mahsulot qarorlari (self-briefing)


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
- D-P6: T05 React review (HIGH) — loyihada lint yo'q edi. ESLint (react-hooks, jsx-a11y, typescript-eslint) ruxsat etilgan paketlar ro'yxatiga qo'shildi, `npm run lint` frontend sifat tekshiruvining bir qismi.
- D-P7: Admin Mini App'da mahsulot/kategoriya formalari alohida `#/products/:id` sahifasi emas, shu tab ichida ochiladi (backendda bitta mahsulotni olish endpointi yo'q; funksional talablar to'liq bajarilgan). Spetsifikatsiyadagi marshrutdan ongli chetlanish.
