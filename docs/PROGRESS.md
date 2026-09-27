# PROGRESS

Kontekst siqilsa — ishni shu fayldan va `.autopilot/state.js` dan davom ettir.

- ✅ [0. Tayyorgarlik]: `onam-shop` papkasi, `git init` (lokal identifikatsiya), `.gitignore`, `.venv` (Python 3.11), autopilot dashboard. Testlar: hali yo'q.
- ✅ [1. Reja]: brief 71 ta talabga bo'lindi (`manifest.md`), spetsifikatsiya yozildi va mustaqil tekshirildi (14 ta jarayon qoidasi qo'shildi), 7 ta task / 5 to'lqin (`docs/PLAN.md`), arxitektura (`docs/ARCHITECTURE.md`), qarorlar (`docs/DECISIONS.md`). Testlar: hali yo'q.
- ✅ [2. Qurish — backend]: T01 asos (sozlamalar, DB, Alembic, initData HMAC), T02 katalog/yuklash/rate limit/seed, T03 zakazlar (status mashinasi, tarix, statistika), T04 ikki bot, eslatmalar, kunlik hisobot. Har biri review (manifest+spec, craft) → tuzatish → commit. Testlar: pytest 189 passed, coverage 90%.
- ✅ [2. Qurish — frontend]: T05 mijoz Mini App, T06 admin Mini App. React review HIGH lar tuzatildi (ESLint qo'shildi, double-submit, BackButton). Testlar: vitest 67 passed, lint 0 xato, `npm run build` yashil.
