## Context
Every API call has to be authenticated with Telegram initData HMAC plus an `auth_date` check (R48), and customers and admins use separate bot tokens (R49). The admin API holds every customer's name, phone and address.

## Decision
Customer endpoints (`/api/*`) validate initData only against `CUSTOMER_BOT_TOKEN`. Admin endpoints (`/api/admin/*`) validate only against `ADMIN_BOT_TOKEN` and then also require `user.id ∈ ADMIN_IDS`. Validation has no development bypass, no header override and no "trust localhost" rule. Tests and E2E sign real initData with test tokens.

## Why
- **One token for both apps, with `ADMIN_IDS` as the only gate** was rejected. A single leaked or mis-set ID list would then be the only barrier. Keeping two tokens means initData captured from the customer app is worthless against the admin API (cross-token returns 401), and that holds even for an admin's own customer session.
- **Trying both tokens on every endpoint** was rejected. It removes the separation above and doubles the ways a bad request can be accepted.
- **A dev bypass (env flag or fake header)** was rejected. Local runs would get easier, but one mis-copied `.env` on the VPS would open the admin API to anyone. Signing test initData costs a small helper and is what the E2E needs anyway.
- **Our own login or sessions** were rejected. The brief forbids registration (R60), and Telegram already identifies the user.

## Consequences
- The owner has to create and maintain two BotFather bots, each with its own Mini App URL. The README has to walk a non-technical user through that.
- The Mini Apps can't be used in a normal browser. Outside Telegram they show "Iltimos, do'konni Telegram orqali oching", and manual testing needs a signed initData fixture.
- `ADMIN_IDS` is static config. Adding or removing an admin means editing `.env` and restarting.
- Sessions expire after `INIT_DATA_MAX_AGE_SECONDS` (24 h). An admin who keeps the Mini App open longer starts getting 401 and has to reopen it.
- Rotating either token instantly invalidates every open session of that app.
