# Faberlik Sotuv Bot — Faberlic konsultanti do'koni

Bu — Telegram orqali ishlaydigan kichik do'kon: mijozlar Telegram botidagi
"Mini App" (kichik ilova) orqali katalogni ko'rib, buyurtma beradi; siz esa
alohida — admin — bot orqali buyurtmalarni qabul qilasiz va holatini
o'zgartirasiz.

**Muhim izoh:** bu — Faberlic kompaniyasining rasmiy do'koni emas, balki
Faberlic konsultantining shaxsiy sotuv vositasi. Katalogdagi mahsulotlar va
narxlar — namuna sifatida qo'yilgan (`backend/app/seed.py`); haqiqiy
mahsulotlar va narxlarni admin panel orqali o'zingiz kiritasiz yoki
mavjudlarini tahrirlaysiz.

Quyida 5 ta bo'lim bor: (1) Telegram botlarini yaratish, (2) sozlamalar
fayli, (3) kompyuteringizda sinab ko'rish, (4) internetga (VPS serverga)
joylashtirish, (5) kundalik ishlatish bo'yicha qisqa qo'llanma.

---

## 1. BotFather'da 2 ta bot yaratish

Do'kon uchun **ikkita** alohida bot kerak: biri mijozlar uchun, ikkinchisi —
faqat siz (admin) uchun.

1. Telegram'da **@BotFather** botini toping va oching.
2. `/newbot` buyrug'ini yuboring, botga nom bering (masalan, "Faberlik Sotuv
   Bot"), keyin username so'raydi — u `bot` bilan tugashi kerak (masalan,
   `faberlik_sotuv_bot`). BotFather sizga bir qator harf-raqamlardan iborat
   **token** beradi (masalan, `123456789:AAExampleTokenHere`) — buni
   ko'chirib, xavfsiz joyga saqlab qo'ying. Bu — mijozlar boti.
3. Xuddi shu tartibda yana bitta bot yarating (masalan,
   `faberlik_sotuv_admin_bot`) — bu admin bot bo'ladi, faqat siz
   foydalanasiz. Uning tokenini ham saqlang.
4. **Mini App URL'ni ulash** — bu qadamni do'kon internetga joylashtirilgach
   (4-bo'lim) bajarasiz, chunki avval saytning manzili (domeni) kerak bo'ladi:
   - Mijozlar boti uchun: BotFather'da botni tanlang → **Bot Settings** →
     **Menu Button** → **Configure menu button** → tugma matnini kiriting
     (masalan, "Do'konni ochish") → URL sifatida `https://SIZNING-DOMEN/app/`
     kiriting.
   - Admin bot uchun alohida sozlash shart emas — dastur o'zi ishga
     tushganda (agar `.env` faylida `WEBAPP_URL` to'ldirilgan bo'lsa) admin
     botning menyu tugmasini avtomatik ravishda `https://SIZNING-DOMEN/admin/`
     ga sozlab qo'yadi.
   - Ikkala bot ham `/start` buyrug'iga javoban do'konni ochadigan tugma
     bilan xabar yuboradi — shuning uchun Menu Button sozlanmagan bo'lsa ham,
     `/start` orqali ochsa bo'ladi.

---

## 2. `.env` faylini to'ldirish

Loyiha papkasida `.env.example` — namuna fayl bor. Uni **nusxalab**, nomini
`.env` deb o'zgartiring (bu faylni hech qachon boshqalarga yubormang va
git'ga qo'shmang — u avtomatik e'tiborsiz qoldiriladi, `.gitignore` orqali).

Muhim maydonlar:

- `CUSTOMER_BOT_TOKEN` — 1-bo'limda olingan mijozlar boti tokeni.
- `ADMIN_BOT_TOKEN` — admin boti tokeni.
- `ADMIN_IDS` — sizning (va kerak bo'lsa, boshqa adminlarning) Telegram
  raqamli ID'si (username emas!). Buni topish uchun Telegram'da
  **@userinfobot** ni oching va unga istalgan xabar yuboring — u sizga
  `Id: 123456789` ko'rinishida raqam qaytaradi. Shu raqamni `ADMIN_IDS`
  ga yozing. Bir nechta admin bo'lsa, vergul bilan ajrating:
  `ADMIN_IDS=123456789,987654321`.
- `BOTS_ENABLED=true` — botlarni yoqadi (kompyuterda sinab ko'rishda
  `false` qilib qo'yish mumkin, 3-bo'limga qarang).
- `WEBAPP_URL` — do'kon internetga chiqqanda uning manzili, masalan
  `https://onamshop.uz` (oxirida `/` shart emas). Kompyuterda sinashda
  bo'sh qoldirilsa ham bo'ladi.
- `SHOP_NAME`, `PICKUP_ADDRESS` — do'kon nomi va "olib ketish" manzili,
  mijozlarga ko'rsatiladi.
- `DOMAIN` — faqat 4-bo'limdagi (VPS) joylashtirish uchun kerak, masalan
  `onamshop.uz`.

Qolgan maydonlar (eslatma vaqtlari, limitlar va h.k.) uchun
`.env.example`dagi tayyor qiymatlar odatda yetarli — xohlasangiz keyinroq
o'zgartirasiz.

---

## 3. Kompyuteringizda sinab ko'rish (lokal ishga tushirish)

Bu bo'lim texnik odam (yoki sizga yordam beruvchi) uchun — do'konni haqiqiy
serverga qo'yishdan oldin kompyuterda tekshirib ko'rish.

Kerakli vositalar: Python 3.11 uchun **uv**, va **Node.js** + npm.

### Backend (server qismi)

```
uv venv --python 3.11 .venv
uv pip install --python .venv/Scripts/python.exe -e "backend[dev]"
cd backend
../.venv/Scripts/python.exe -m alembic upgrade head
../.venv/Scripts/python.exe -m app.seed
```

`alembic upgrade head` — ma'lumotlar bazasini (jadvallarni) tayyorlaydi.
`app.seed` — namuna kategoriyalar va mahsulotlarni qo'shadi (narxlar —
namuna, keyinroq admin panelda o'zgartirasiz).

Botlarsiz, faqat saytni tekshirish uchun (haqiqiy Telegram tokenlari va
internet shart emas):

```
BOTS_ENABLED=false ../.venv/Scripts/python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

(`--factory` kerak, chunki `app.main` moduli tayyor ilova o'rniga uni
yasovchi funksiyani — `create_app()` — beradi.)

Boshqa terminalda tekshiring:

```
curl http://127.0.0.1:8000/health
```

Javobda `{"status":"ok","bots":false}` chiqsa — server ishlayapti.

### Frontend (Mini App qismi)

```
cd frontend
npm install
npm run build
```

`npm run build` — ikkala Mini App'ni (`/app` — mijozlar, `/admin` — admin)
yig'adi; natija `frontend/dist` papkasida bo'ladi, uni backend
`FRONTEND_DIST` sozlamasi orqali ko'rsatadi.

### Testlarni ishga tushirish

```
# Backend testlari
cd backend && ../.venv/Scripts/python.exe -m pytest

# Frontend testlari
cd frontend && npx vitest run

# E2E (brauzerda to'liq oqimni tekshiradi: katalog -> savat -> buyurtma -> admin -> status)
cd frontend
PLAYWRIGHT_BROWSERS_PATH="$(cd .. && pwd)/.playwright-browsers" npx playwright install chromium   # faqat bir marta
npm run e2e
```

E2E testlar haqiqiy Telegram'ga ulanmaydi — soxta (test) tokenlar va
kompyuterda ishga tushadigan "soxta Telegram server" ishlatiladi, shuning
uchun internet yoki haqiqiy bot kerak emas.

---

## 4. VPS serverga joylashtirish (docker compose + Caddy)

**Muhim: bu loyihada `Dockerfile`, `docker-compose.yml` va `Caddyfile`
fayllari yozilgan, lekin ushbu ishlab chiqish jarayonida (bu sessiyada)
Docker o'rnatilmagani sababli bir marta ham ishga tushirilmagan va
sinalmagan.** VPS'ga joylashtirishdan oldin ularni albatta birinchi marta
sinovdan o'tkazing (masalan, test serverida).

Kerakli narsalar: Docker va Docker Compose o'rnatilgan VPS (masalan, Ubuntu),
va sizga tegishli domen nomi (masalan, `onamshop.uz`).

1. **DNS**: domen provayderingizning boshqaruv panelida domen uchun **A
   yozuvi** (A record) yarating — u VPS serveringizning IP-manziliga
   ko'rsatishi kerak. Bu odatda bir necha daqiqadan bir necha soatgacha
   vaqt oladi (tarqalishi uchun).
2. Loyiha fayllarini VPS'ga ko'chiring (masalan, `git clone` yoki `scp`
   orqali).
3. `.env.example`dan `.env` yarating (2-bo'limga qarang), qo'shimcha:
   - `DOMAIN=onamshop.uz` (o'z domeningiz, `https://` yozmasdan).
   - `WEBAPP_URL=https://onamshop.uz` (endi `https://` bilan, oxirida `/`
     siz).
   - `BOTS_ENABLED=true`, ikkala haqiqiy bot tokeni, `ADMIN_IDS`.
4. Serverda ishga tushiring:
   ```
   docker compose build
   docker compose up -d
   ```
   Bu `app` konteynerini (backend + tayyor frontend) va `caddy`
   konteynerini (avtomatik HTTPS bilan) ishga tushiradi. Caddy domeningiz
   uchun Let's Encrypt orqali o'zi bepul SSL sertifikat oladi — buning
   uchun DNS to'g'ri sozlangan va 80/443 portlari ochiq bo'lishi kifoya.
5. Bir necha daqiqadan so'ng `https://onamshop.uz/health` manzilini
   brauzerda oching — `{"status":"ok","bots":true}` ko'rinishi kerak.
6. 1-bo'limdagi kabi, mijozlar botining Menu Button'ini
   `https://onamshop.uz/app/` ga sozlang (admin bot buni o'zi avtomatik
   qiladi).

---

## 5. Onam uchun qisqa qo'llanma — kundalik ishlatish

### Yangi buyurtma kelganda

Mijoz buyurtma bergach, **admin botga** darhol xabar keladi — unda mijoz
ismi, telefoni, olib ketish yoki yetkazib berish, mahsulotlar ro'yxati va
umumiy summa yozilgan. Xabar ostida tugma(lar) bo'ladi:

- Keyingi holat tugmasi (masalan, **"Qabul qilindi"**) — bosilganda
  buyurtma holati o'zgaradi va mijozga avtomatik xabar boradi.
- **"Bekor qilish"** — buyurtmani bekor qiladi.

Buyurtma holatlari ketma-ket o'zgaradi: **Yangi → Qabul qilindi →
Faberlic'ga buyurtma berildi → Yetib keldi → Topshirildi**. Har safar tugmani
bosganingizda, keyingi holat tugmasi paydo bo'ladi — shu tugmalarni ketma-ket
bosib boring.

Bu ishni admin **botda** ham, admin **ilovada** (Mini App; sahifa yuqorisida,
sarlavha ostida turgan **"Zakazlar"** bo'limi) ham qilish mumkin — ikkalasi
ham bir xil ishlaydi.

### Eslatmalar va kunlik hisobot

Agar "Yangi" holatdagi buyurtma 2 soat davomida qabul qilinmasa, bot sizga
eslatma yuboradi (keyin har 4 soatda takrorlanadi — bu vaqtlarni
`.env`dagi `REMINDER_FIRST_HOURS` / `REMINDER_REPEAT_HOURS` orqali
o'zgartirish mumkin). Har kuni ertalab soat **09:00**da (`DAILY_REPORT_TIME`)
admin botga hali yopilmagan barcha buyurtmalar ro'yxati — kunlik hisobot —
avtomatik yuboriladi.

### Admin botning foydali buyruqlari

Admin botga quyidagi buyruqlarni yozishingiz mumkin:

- `/orders` — hali yopilmagan (ochiq) barcha buyurtmalar ro'yxati.
- `/order_<raqam>` — muayyan buyurtma tafsilotlari (masalan, `/order_12`).
- `/find <raqam yoki telefon>` — buyurtmani raqami yoki mijoz telefoni
  bo'yicha qidirish.
- `/stats` — statistika: qaysi holatda nechta buyurtma bor, bugungi va shu
  oy topshirilgan buyurtmalar summasi.

### Yangi mahsulot qo'shish (rasm bilan)

1. Admin ilovani oching (admin botdagi tugma orqali yoki `/start`).
2. Sahifa yuqorisidagi, sarlavha ostidagi bo'limlardan **"Mahsulotlar"**ni
   tanlang.
3. **"Yangi mahsulot"** tugmasini bosing.
4. Formani to'ldiring: **Kategoriya**, **Nomi**, **Artikul**, **Narxi**,
   **Tavsif** (ixtiyoriy) va **Rasm** — rasmni tanlab yuklang (yuklanayotganda
   "Yuklanmoqda..." deb ko'rsatadi, tugagach rasm ko'rinadi).
5. **"Saqlash"** tugmasini bosing — mahsulot katalogga qo'shiladi va mijozlar
   uni darhol ko'ra oladi.

### Mahsulotni vaqtincha yashirish ("Mavjud emas" qilish)

Agar mahsulot omborda tugab qolsa, uni o'chirmasdan turib "mavjud emas" deb
belgilashingiz mumkin — u katalogda xiralashgan holda ko'rinadi va mijozlar
uni savatga qo'sha olmaydi. Buning uchun: **Mahsulotlar** ro'yxatida kerakli
mahsulot qatorida turgan **"Mavjud emas qilish"** tugmasini bosing — forma
ochish shart emas. Mahsulot qayta kelganda, xuddi shu qatordagi
**"Mavjud qilish"** tugmasini bosib, qaytarasiz. (Mahsulot qo'shish/tahrirlash
formasida ham xuddi shu narsani belgilaydigan **"Mavjud emas"** nomli katakcha
bor.)
