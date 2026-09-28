# Onam Shop — multi-stage image (frontend build -> Python runtime).
#
# NOT RUN in this session (Docker isn't installed here) — written for the VPS
# deploy described in README.md. Build with `docker compose build` there.

# ---- Stage 1: build the two Vite entries (/app, /admin) ----
FROM node:22-slim AS frontend-build
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python runtime (FastAPI + aiogram) ----
FROM python:3.11-slim AS runtime

# Backend lives at /app/backend so its relative-path settings work unchanged:
#   DATABASE_URL=sqlite+aiosqlite:///./data/onam.db, UPLOAD_DIR=uploads,
#   FRONTEND_DIST=../frontend/dist (all relative to this WORKDIR).
WORKDIR /app/backend

COPY backend/pyproject.toml ./
COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./

RUN pip install --no-cache-dir .

COPY --from=frontend-build /src/frontend/dist /app/frontend/dist

# Non-root runtime user (security review ticket 08): the app only ever needs
# to write under data/ (sqlite db) and uploads/ (saved files), so those are
# the only paths it owns.
RUN mkdir -p data uploads \
    && groupadd -r app && useradd -r -g app -d /app/backend app \
    && chown -R app:app /app/backend

ENV DATABASE_URL=sqlite+aiosqlite:///./data/onam.db \
    UPLOAD_DIR=uploads \
    FRONTEND_DIST=../frontend/dist \
    PYTHONUNBUFFERED=1

EXPOSE 8000

USER app

# `app.main` only exposes the `create_app()` factory (no module-level `app`
# instance), hence `--factory` — see docs/DECISIONS.md / ticket 07 notes.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000"]
