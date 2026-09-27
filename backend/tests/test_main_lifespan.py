from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings
from app.main import build_bot, create_app
from app.notify import NullNotifier, TelegramNotifier


async def test_lifespan_bots_disabled_creates_no_bot_but_scheduler_still_runs(settings):
    app = create_app(settings=settings)

    with patch("app.main.Bot") as bot_cls:
        async with app.router.lifespan_context(app):
            assert bot_cls.call_count == 0
            assert isinstance(app.state.notifier, NullNotifier)
            assert app.state.scheduler is not None
        # scheduler stopped cleanly on exit, no dangling bot tasks
        assert app.state.bot_tasks == []

    await app.state.engine.dispose()


def _bots_enabled_settings(tmp_path, **overrides):
    fields = dict(
        customer_bot_token="111111:TEST-customer",
        admin_bot_token="222222:TEST-admin",
        admin_ids="555",
        bots_enabled=True,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'lifespan.db'}",
        upload_dir=str(tmp_path / "uploads"),
        frontend_dist=str(tmp_path / "no-such-dist"),
    )
    fields.update(overrides)
    return Settings(**fields)


async def test_lifespan_bots_enabled_builds_telegram_notifier_and_starts_dispatchers(tmp_path):
    settings = _bots_enabled_settings(tmp_path)
    app = create_app(settings=settings)

    fake_customer_bot = AsyncMock()
    fake_admin_bot = AsyncMock()

    fake_dp = MagicMock()
    fake_dp.start_polling = AsyncMock()
    fake_dp.stop_polling = AsyncMock()
    fake_dp.include_router = MagicMock()

    with (
        patch("app.main.Bot", side_effect=[fake_customer_bot, fake_admin_bot]),
        patch("app.main.Dispatcher", return_value=fake_dp),
    ):
        async with app.router.lifespan_context(app):
            assert isinstance(app.state.notifier, TelegramNotifier)
            assert app.state.scheduler is not None
            assert len(app.state.bot_tasks) == 2

    assert fake_dp.stop_polling.await_count == 2
    fake_customer_bot.session.close.assert_awaited_once()
    fake_admin_bot.session.close.assert_awaited_once()
    await app.state.engine.dispose()


async def test_lifespan_sets_admin_chat_menu_button_when_webapp_url_set(tmp_path):
    settings = _bots_enabled_settings(tmp_path, webapp_url="https://shop.example.com")
    app = create_app(settings=settings)

    fake_customer_bot = AsyncMock()
    fake_admin_bot = AsyncMock()
    fake_dp = MagicMock()
    fake_dp.start_polling = AsyncMock()
    fake_dp.stop_polling = AsyncMock()
    fake_dp.include_router = MagicMock()

    with (
        patch("app.main.Bot", side_effect=[fake_customer_bot, fake_admin_bot]),
        patch("app.main.Dispatcher", return_value=fake_dp),
    ):
        async with app.router.lifespan_context(app):
            pass

    fake_admin_bot.set_chat_menu_button.assert_awaited_once()
    kwargs = fake_admin_bot.set_chat_menu_button.await_args.kwargs
    assert kwargs["menu_button"].web_app.url == "https://shop.example.com/admin/"
    await app.state.engine.dispose()


async def test_lifespan_menu_button_failure_is_logged_not_raised(tmp_path, caplog):
    settings = _bots_enabled_settings(tmp_path, webapp_url="https://shop.example.com")
    app = create_app(settings=settings)

    fake_customer_bot = AsyncMock()
    fake_admin_bot = AsyncMock()
    fake_admin_bot.set_chat_menu_button.side_effect = RuntimeError("boom")
    fake_dp = MagicMock()
    fake_dp.start_polling = AsyncMock()
    fake_dp.stop_polling = AsyncMock()
    fake_dp.include_router = MagicMock()

    caplog.set_level("ERROR")
    with (
        patch("app.main.Bot", side_effect=[fake_customer_bot, fake_admin_bot]),
        patch("app.main.Dispatcher", return_value=fake_dp),
    ):
        async with app.router.lifespan_context(app):  # must not raise
            pass

    assert any("menu button" in r.message for r in caplog.records)
    await app.state.engine.dispose()


def test_build_bot_uses_official_api_when_no_telegram_api_base():
    settings = Settings(telegram_api_base="")
    bot = build_bot("111:AAA", settings)
    try:
        assert "api.telegram.org" in bot.session.api.base
    finally:
        import asyncio

        asyncio.run(bot.session.close())


def test_build_bot_points_at_telegram_api_base_when_set():
    settings = Settings(telegram_api_base="http://localhost:8081")
    bot = build_bot("111:AAA", settings)
    try:
        assert bot.session.api.base.startswith("http://localhost:8081/")
    finally:
        import asyncio

        asyncio.run(bot.session.close())
