# KNOWN ISSUES

- **Vitest vaqt limiti (flaky):** mustaqil tekshiruvda `npx vitest run` bitta testda timeout bilan yiqildi — u `pytest` bilan bir vaqtda, kompyuter band paytida ishga tushirilgan edi. Alohida ishga tushirilganda 67/67 yashil. Agar takrorlansa: testlarni ketma-ket ishga tushiring.
- **Haqiqiy Telegram bilan tekshirilmagan:** brief bo'yicha haqiqiy Telegram API'ga murojaat taqiqlangan. Botlar pytest'da mock bilan, E2E'da lokal mock Bot API server bilan tekshirilgan. Haqiqiy tokenlar bilan birinchi ishga tushirishda /start, zakaz xabari va tugmalarni qo'lda sinab ko'ring.
- **Docker/Caddy ishga tushirilmagan:** Dockerfile, docker-compose.yml, Caddyfile yozilgan, lekin bu kompyuterda Docker yo'q — VPS'da birinchi marta ishga tushirilganda tekshirilishi kerak.
- **JPEG tekshiruvi faqat sarlavha bo'yicha:** rasm turi fayl boshidagi baytlar bo'yicha aniqlanadi; to'liq rasm strukturasi tekshirilmaydi (Pillow ruxsat etilgan paketlar ro'yxatida yo'q). Xavf past: fayllar rasm Content-Type bilan beriladi.
- **Rate limit xotirada:** server qayta ishga tushsa hisoblagich nollanadi; bir nechta worker bo'lsa har biri alohida hisoblaydi. Hozirgi bitta jarayonli deploy uchun yetarli.
