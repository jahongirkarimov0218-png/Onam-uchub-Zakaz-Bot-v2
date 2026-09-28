# Reja — Faberlik Sotuv Bot

Yarus T2: 7 ta task, 5 to'lqin (wave). Bir to'lqindagi tasklar parallel bajariladi. Har task — test birinchi (TDD), keyin kod, review, commit.

| # | Task | To'lqin | Oldin tugashi kerak |
|---|---|---|---|
| 01 | Backend asosi: sozlamalar, DB, migratsiya, initData auth, /health | 1 | — |
| 02 | Katalog API, admin mahsulot/kategoriya CRUD, rasm yuklash, rate limit, seed | 2 | 01 |
| 03 | Zakaz xizmati: yaratish, status mashinasi, tarix, mijoz va admin zakaz API, statistika, Notifier porti | 3 | 02 |
| 04 | Ikki bot (aiogram), TelegramNotifier, eslatmalar, kunlik hisobot, lifespan | 4 | 03 |
| 05 | Frontend asosi + mijoz Mini App (/app) | 2 | 01 |
| 06 | Admin Mini App (/admin) | 3 | 05 |
| 07 | E2E (Playwright + mock Telegram), Docker/Caddy fayllari, README (uz) | 5 | 04, 06 |

Tartib briefdagidek: DB modellari va migratsiyalar → initData auth → mahsulot API → zakaz API → admin bot, bildirishnomalar, eslatmalar → mijoz Mini App → admin Mini App. Frontend tasklari (05, 06) API kontraktlari spetsifikatsiyada qat'iy belgilangani uchun backend bilan parallel ketadi.

Keyin: review (python / typescript / react / security reviewer), E2E, quality-gate + verification-loop, README.

Task fayllari: `.autopilot/2026-09-27-onam-shop/tickets/`.
