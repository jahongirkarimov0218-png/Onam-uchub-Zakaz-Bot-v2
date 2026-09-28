"""Composition root. Owns lifespan and static mounting; exposes `create_app`."""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.types import MenuButtonWebApp, WebAppInfo
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles

from . import texts
from .api import admin_catalog, admin_orders, catalog, orders
from .auth import TgUser, admin_user
from .bodylimit import BodySizeLimitMiddleware
from .bots.admin import admin_router
from .bots.customer import customer_router
from .config import Settings, get_settings
from .db import make_engine, make_session_factory
from .notify import Notifier, NullNotifier, TelegramNotifier
from .ratelimit import RateLimiter
from .scheduler import build_scheduler

logger = logging.getLogger(__name__)


def include_routers(app: FastAPI) -> None:
    """Extension point for later tickets. Reuses `app.state.order_limiter` /
    `app.state.notifier`, set up in `create_app` before this runs."""
    app.include_router(catalog.router)
    app.include_router(admin_catalog.router)
    app.include_router(orders.router)
    app.include_router(admin_orders.router)


def build_bot(token: str, settings: Settings) -> Bot:
    """Build an aiogram `Bot` for `token`. Points at `settings.telegram_api_base`
    (a local mock Telegram Bot API server, used by the E2E ticket) when set;
    otherwise talks to the official API."""
    if settings.telegram_api_base:
        session = AiohttpSession(api=TelegramAPIServer.from_base(settings.telegram_api_base))
        return Bot(token=token, session=session)
    return Bot(token=token)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    app.state.bot_tasks = []
    app.state.scheduler = None

    if settings.bots_active:
        customer_bot = build_bot(settings.customer_bot_token, settings)
        admin_bot = build_bot(settings.admin_bot_token, settings)
        notifier: Notifier = TelegramNotifier(customer_bot, admin_bot, settings, app.state.session_factory)
        app.state.notifier = notifier
        app.state.customer_bot = customer_bot
        app.state.admin_bot = admin_bot

        if settings.webapp_url:
            try:
                await admin_bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(
                        text=texts.BTN_OPEN_ADMIN,
                        web_app=WebAppInfo(url=f"{settings.webapp_url.rstrip('/')}/admin/"),
                    )
                )
            except Exception:  # noqa: BLE001 - a menu-button failure must not stop startup
                logger.exception("failed to set the admin chat menu button")

        customer_dp = Dispatcher()
        customer_dp.include_router(customer_router(settings))
        admin_dp = Dispatcher()
        admin_dp.include_router(admin_router(settings, app.state.session_factory, notifier))
        app.state.customer_dp = customer_dp
        app.state.admin_dp = admin_dp

        app.state.bot_tasks = [
            asyncio.create_task(
                customer_dp.start_polling(customer_bot, handle_signals=False, close_bot_session=False)
            ),
            asyncio.create_task(
                admin_dp.start_polling(admin_bot, handle_signals=False, close_bot_session=False)
            ),
        ]

    # Scheduler runs regardless of bots_active: with NullNotifier (or a caller-
    # supplied notifier) its jobs are harmless no-ops, logged instead of sent.
    scheduler = build_scheduler(app.state.session_factory, app.state.notifier, settings)
    scheduler.start()
    app.state.scheduler = scheduler

    yield

    if app.state.scheduler is not None:
        app.state.scheduler.shutdown(wait=False)
    if app.state.bot_tasks:
        await app.state.customer_dp.stop_polling()
        await app.state.admin_dp.stop_polling()
        await asyncio.gather(*app.state.bot_tasks, return_exceptions=True)
        await app.state.customer_bot.session.close()
        await app.state.admin_bot.session.close()


def create_app(settings: Settings | None = None, notifier: Notifier | None = None) -> FastAPI:
    settings = settings or get_settings()

    app = FastAPI(lifespan=_lifespan)
    app.state.settings = settings
    app.state.notifier = notifier or NullNotifier()
    app.dependency_overrides[get_settings] = lambda: settings

    # Defense in depth for POST /api/uploads and POST /api/admin/uploads:
    # rejects an oversized body (413 file_too_large) before it is spooled by
    # python-multipart / save_upload's own check. See app.bodylimit.
    app.add_middleware(BodySizeLimitMiddleware, settings=settings)

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
