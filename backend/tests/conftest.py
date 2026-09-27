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
from app.db import make_engine, make_session_factory
from app.main import create_app
from app.models import Base, Order, OrderItem, OrderStatusHistory


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


@pytest.fixture
async def session_factory(tmp_path):
    """Standalone DB (independent of the `app` fixture) for notify/bots/scheduler
    tests that only need a session factory, not the ASGI app."""
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'seam.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield make_session_factory(engine)
    await engine.dispose()


@pytest.fixture
def make_order(session_factory):
    """Insert an order (with one catalog item and its `new` history row) into
    `session_factory`'s DB and return it loaded with `.items`/`.history`."""

    async def _make(**overrides):
        fields = dict(
            tg_user_id=overrides.get("tg_user_id", 555),
            tg_username=overrides.get("tg_username", "ali"),
            customer_name=overrides.get("customer_name", "Ali Valiyev"),
            phone=overrides.get("phone", "+998901234567"),
            delivery_type=overrides.get("delivery_type", "pickup"),
            address=overrides.get("address"),
            comment=overrides.get("comment"),
            status=overrides.get("status", "new"),
            total=overrides.get("total", 150000),
            admin_notified=overrides.get("admin_notified", False),
            last_reminded_at=overrides.get("last_reminded_at"),
        )
        if "created_at" in overrides:  # explicit override only; else model default (utcnow)
            fields["created_at"] = overrides["created_at"]
        async with session_factory() as session:
            order = Order(**fields)
            session.add(order)
            await session.flush()
            session.add(
                OrderItem(
                    order_id=order.id, kind="catalog", name="Sovun", sku="SKU1",
                    unit_price=order.total, quantity=1,
                )
            )
            session.add(
                OrderStatusHistory(
                    order_id=order.id, from_status=None, to_status=order.status,
                    actor_tg_id=order.tg_user_id, source="customer",
                )
            )
            await session.commit()
            order_id = order.id

        from app.services.orders import load_order

        async with session_factory() as session:
            return await load_order(session, order_id)

    return _make
