"""Shared test fixtures: tmp sqlite DB, initData signer, FakeNotifier, ASGI client."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app
from app.models import Base


def sign_init_data(user: dict, bot_token: str, auth_date: int | None = None) -> str:
    """Build a raw Telegram WebApp initData string, signed for `bot_token`."""
    if auth_date is None:
        auth_date = int(time.time())
    data = {
        "query_id": "AAHtestquery",
        "user": json.dumps(user, separators=(",", ":")),
        "auth_date": str(auth_date),
    }
    check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)


class FakeNotifier:
    """Test double for app.notify.Notifier: records calls instead of hitting Telegram."""

    def __init__(self) -> None:
        self.events: list[tuple[str, object]] = []

    async def order_created(self, order):
        self.events.append(("order_created", order))

    async def status_changed(self, order):
        self.events.append(("status_changed", order))

    async def reminder(self, orders):
        self.events.append(("reminder", orders))

    async def daily_report(self, orders):
        self.events.append(("daily_report", orders))


@pytest.fixture
def settings(tmp_path):
    db_path = tmp_path / "test.db"
    return Settings(
        customer_bot_token="111111:TEST-customer",
        admin_bot_token="222222:TEST-admin",
        admin_ids="555",
        bots_enabled=False,
        database_url=f"sqlite+aiosqlite:///{db_path}",
        upload_dir=str(tmp_path / "uploads"),
        frontend_dist=str(tmp_path / "no-such-dist"),
    )


@pytest.fixture
def fake_notifier():
    return FakeNotifier()


@pytest.fixture
async def app(settings, fake_notifier):
    application = create_app(settings=settings, notifier=fake_notifier)
    engine = application.state.engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield application
    await engine.dispose()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
