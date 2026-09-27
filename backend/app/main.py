"""Composition root. Owns lifespan and static mounting; exposes `create_app`."""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from .api import admin_catalog, catalog
from .auth import TgUser, admin_user
from .config import Settings, get_settings
from .db import make_engine, make_session_factory
from .ratelimit import RateLimiter


def include_routers(app: FastAPI) -> None:
    """Extension point for later tickets: ticket 02 (catalog/uploads) registers here;
    ticket 03 (orders) reuses `app.state.order_limiter` and adds its own router."""
    app.include_router(catalog.router)
    app.include_router(admin_catalog.router)


def create_app(settings: Settings | None = None, notifier: object | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI()
    app.state.settings = settings
    app.state.notifier = notifier
    app.dependency_overrides[get_settings] = lambda: settings

    engine = make_engine(settings.database_url)
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)

    app.state.upload_limiter = RateLimiter(settings.rate_limit_uploads, settings.rate_limit_window_seconds)
    app.state.order_limiter = RateLimiter(settings.rate_limit_orders, settings.rate_limit_window_seconds)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "bots": settings.bots_active}

    @app.get("/api/admin/me")
    async def admin_me(user: TgUser = Depends(admin_user)) -> dict:
        return {"id": user.id, "first_name": user.first_name}

    include_routers(app)

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

    frontend_dist = Path(settings.frontend_dist)
    if frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return app
