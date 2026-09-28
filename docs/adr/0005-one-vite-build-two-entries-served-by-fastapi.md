## Context
There are two frontends, `/app` for customers and `/admin` for admins (R13). The brief requires one `npm run build` to build both (R64), and the deploy target is a single app container behind Caddy (R15).

## Decision
There is one Vite project in multi-page mode with two HTML entries (`app/index.html`, `admin/index.html`), shared `src/shared` code and one shared `dist/assets`. FastAPI mounts `frontend/dist` as static files at `/`, after the API routes, so it serves `/app/`, `/admin/`, `/api/*` and `/uploads/*` from a single origin.

## Why
- **Two separate Vite projects** were rejected. They would need two `package.json` files, two builds and two copies of the Telegram wrapper, API client and i18n. That is duplication the brief's "one i18n file" rule (R29) argues against.
- **One SPA that routes by role** was rejected. It would ship the admin UI bundle to every customer. It would also blur which bot token a page should sign with, because each entry is opened by a different bot.
- **Caddy serving `dist` directly** was rejected. Local runs (`uvicorn` only, no Caddy) and E2E would then need a second server. The frontend would also sit on a different origin than the API, which brings CORS into scope.

## Consequences
- The URLs `WEBAPP_URL/app/` and `WEBAPP_URL/admin/` are registered in BotFather and hard-coded in the bots. Moving them means reconfiguring both bots.
- Python serves static files, which is slower than Caddy would be. That is acceptable at this traffic level.
- The Docker image needs a multi-stage Node → Python build. A backend-only change still rebuilds the frontend stage unless layer caching hits.
- Code in `src/shared` changes both apps at once. A careless change there can break the admin panel while fixing the shop.
- A missing `dist` doesn't fail startup. The API runs and the Mini App URLs return 404, which can hide a broken build.
