## Context
Two aiogram bots (customer, admin) must run in one process with FastAPI (R10). The only public HTTPS surface planned is the Mini App behind Caddy.

## Decision
Both bots receive updates by long polling, started from the FastAPI lifespan. No webhook endpoint exists.

## Why
- **Webhooks** were rejected. They need a public `/webhook/...` route per bot, a secret-token check on each, and `setWebhook` calls tied to the final domain. That is extra attack surface and deploy steps the non-technical owner would have to get right. For two low-traffic bots it buys nothing.
- **A separate bot worker process** was rejected. The brief asks for one process. Separating them would also need a second container and a way for the API to reach the bots, since order creation and status changes in the API send Telegram messages.

## Consequences
- Only one instance of the app can run at a time. A second copy (a scaled container, or a dev machine left running with the prod tokens) makes Telegram's `getUpdates` conflict, and updates get split or lost. Together with the in-memory rate limiter (S12), this rules out horizontal scaling.
- If the API goes down, both bots go down with it. A crash in bot code shares a process with order intake.
- Switching to webhooks later means adding routes, secrets and a `setWebhook` step at deploy. The handlers themselves stay the same.
- E2E depends on `TELEGRAM_API_BASE` pointing the polling client at a mock Bot API server (D-P4).
