# Bepul deploy: Render (backend) + Vercel (Mini App) + GitHub Actions (keep-alive)

Docker kerak emas. Backend (FastAPI + 2 bot) Render Free'da, ikkala Mini App (`/app/`, `/admin/`) Vercel'da ishlaydi.
Vercel `/api/*` va `/uploads/*` so'rovlarini Render'ga uzatadi, shuning uchun frontend kodini o'zgartirish shart emas.

## 1. GitHub: public repo

1. GitHub'da yangi **public** repo yarating (README qo'shmang).
2. Deploy fayllarini commit qiling:

```bash
git add render.yaml frontend/vercel.json .github/workflows/keep-alive.yml DEPLOY.md
```

```bash
git commit -m "chore(deploy): Render + Vercel + keep-alive config"
```

3. Loyiha papkasida repo manzilini ulang:

```bash
git remote add origin <url>
```

```bash
git push -u origin master
```

## 2. Render: backend

1. render.com → **New** → **Blueprint** → GitHub repo'ni tanlang. `render.yaml` avtomatik o'qiladi.
2. `sync: false` bo'lgan qiymatlarni kiriting: `CUSTOMER_BOT_TOKEN`, `ADMIN_BOT_TOKEN`, `ADMIN_IDS`, `SHOP_NAME`, `PICKUP_ADDRESS`. `WEBAPP_URL` ni hozircha bo'sh qoldiring (4-qadamda to'ldiriladi).
3. Deploy tugagach, servis URL'ini ko'ring. Agar u `https://onam-backend.onrender.com` bo'lmasa, `frontend/vercel.json` dagi ikkala URL'ni haqiqiy URL bilan almashtiring, keyin commit va push qiling.

## 3. Vercel: Mini App

1. vercel.com → **Add New** → **Project** → **Import** → shu repo.
2. **Root Directory**: `frontend`. Qolgan sozlamalar `vercel.json` dan olinadi.
3. **Deploy** bosing. Tayyor URL (masalan `https://onam-shop.vercel.app`) ni yozib oling.

## 4. Vercel URL'ni Render'ga ulash

1. Render → servis → **Environment** → `WEBAPP_URL` = Vercel URL (oxirida `/` yo'q).
2. **Manual Deploy** → **Deploy latest commit**. Botlar Mini App tugmalarini shu manzil bilan yaratadi.

## 5. GitHub Actions: keep-alive

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
2. Nomi `RENDER_BACKEND_URL`, qiymati Render URL (oxirida `/` yo'q).
3. **Actions** → **keep-alive** → **Run workflow**. Yashil bo'lsa, u har 10 daqiqada backend'ni uyg'otib turadi.

## 6. Tekshirish

1. `curl <render-url>/health` → `{"status":"ok","bots":true}`.
2. Mijoz botida `/start` → "Do'konni ochish" → Mini App ochiladi.
3. Admin bot menyusi → "Admin panelni ochish" → admin panel ochiladi.
4. Test buyurtma bering va admin botda statusini o'zgartiring: mijozga xabar kelishi kerak.
5. ~5 MB rasm yuklab ko'ring. Vercel proxy orqali body hajmi limiti TEKSHIRILMAGAN. Xato chiqsa, Render'da `MAX_UPLOAD_MB=4` qo'ying.

## Ogohlantirishlar

- Render Free diski vaqtinchalik: SQLite bazasi, buyurtmalar va rasmlar har deploy yoki restartda o'chadi. Keyingi qadam — tashqi DB.
- Deploy paytida bir necha soniya ikki instance polling qiladi, logda `TelegramConflictError` chiqishi mumkin. Bu normal.
- GitHub cron kechiksa, Render uxlaydi va birinchi so'rov ~50 soniya kutadi. Telegram xabarlari yo'qolmaydi, bot uyg'onganda qayta ishlanadi.
- 60 kun commit bo'lmasa, GitHub scheduled workflow'ni o'chiradi. Actions sahifasida uni qayta yoqing.
- VPS/Docker deploy (README) ham ishlashda davom etadi.
