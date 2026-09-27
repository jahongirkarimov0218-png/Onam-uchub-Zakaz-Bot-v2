import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.models import OrderAdminMessage
from app.notify import NullNotifier, Notifier, TelegramNotifier, format_order, order_keyboard


async def test_null_notifier_satisfies_protocol_and_is_a_noop(caplog):
    notifier: Notifier = NullNotifier()
    caplog.set_level("INFO")

    await notifier.order_created(object())
    await notifier.status_changed(object())
    await notifier.reminder([object(), object()])
    await notifier.daily_report([object()])

    # no-op: nothing raised, and it logged instead of doing anything else
    assert caplog.records


def _order(**overrides):
    base = dict(
        id=42,
        tg_user_id=555,
        tg_username="ali",
        customer_name="Ali Valiyev",
        phone="+998901234567",
        delivery_type="pickup",
        address=None,
        comment="Tezroq kerak",
        status="new",
        total=150000,
        items=[
            SimpleNamespace(
                kind="catalog", name="Sovun", sku="SKU1", image_path=None,
                unit_price=150000, quantity=1, note=None,
            ),
            SimpleNamespace(
                kind="custom", name="Krem", sku=None, image_path=None,
                unit_price=None, quantity=2, note="Qizil rangda",
            ),
        ],
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_format_order_includes_key_fields():
    order = _order()
    text = format_order(order)
    assert "#42" in text
    assert "Ali Valiyev" in text
    assert "+998901234567" in text
    assert "Sovun" in text
    assert "Krem" in text
    assert "Narx keyin aniqlanadi" in text  # custom line has no price
    assert "150 000" in text  # total
    assert "Tezroq kerak" in text


def test_order_keyboard_offers_only_next_status_and_cancel():
    order = _order(status="new")
    keyboard = order_keyboard(order)
    callbacks = [btn.callback_data for row in keyboard.inline_keyboard for btn in row]
    assert callbacks == ["st:42:accepted", "st:42:cancelled"]


def test_order_keyboard_is_empty_for_final_status():
    order = _order(status="delivered")
    keyboard = order_keyboard(order)
    assert keyboard is None


@pytest.fixture
def notifier_settings():
    return Settings(
        customer_bot_token="111:CUST",
        admin_bot_token="222:ADMIN",
        admin_ids="10,20",
        bots_enabled=True,
    )


@pytest.fixture
def notifier(notifier_settings, session_factory):
    customer_bot = AsyncMock()
    admin_bot = AsyncMock()
    admin_bot.send_message.return_value = SimpleNamespace(message_id=999)
    tn = TelegramNotifier(customer_bot, admin_bot, notifier_settings, session_factory)
    tn.customer_bot = customer_bot
    tn.admin_bot = admin_bot
    return tn


async def test_order_created_sends_to_every_admin_and_stores_message_ids(notifier, session_factory):
    order = _order()
    await notifier.order_created(order)

    assert notifier.admin_bot.send_message.await_count == 2
    called_ids = {c.args[0] for c in notifier.admin_bot.send_message.await_args_list}
    assert called_ids == {10, 20}

    async with session_factory() as session:
        from sqlalchemy import select

        rows = (await session.execute(select(OrderAdminMessage))).scalars().all()
    assert len(rows) == 2
    assert {r.chat_id for r in rows} == {10, 20}
    assert all(r.message_id == 999 for r in rows)


async def test_order_created_marks_admin_notified_true_on_success(notifier, session_factory, make_order):
    order = await make_order()
    await notifier.order_created(order)

    async with session_factory() as session:
        refreshed = await session.get(type(order), order.id)
    assert refreshed.admin_notified is True


async def test_order_created_swallows_telegram_errors_and_logs(notifier, caplog):
    caplog.set_level("ERROR")
    notifier.admin_bot.send_message.side_effect = RuntimeError("boom")
    order = _order()

    await notifier.order_created(order)  # must not raise

    assert any("order_created" in r.message or "boom" in str(r) for r in caplog.records)


async def test_status_changed_edits_every_stored_admin_message_and_notifies_customer(
    notifier, session_factory, make_order
):
    order = await make_order()
    async with session_factory() as session:
        session.add(OrderAdminMessage(order_id=order.id, chat_id=10, message_id=100))
        session.add(OrderAdminMessage(order_id=order.id, chat_id=20, message_id=200))
        await session.commit()

    await notifier.status_changed(order)

    assert notifier.admin_bot.edit_message_text.await_count == 2
    notifier.customer_bot.send_message.assert_awaited_once()
    assert notifier.customer_bot.send_message.await_args.args[0] == order.tg_user_id


async def test_status_changed_customer_send_failure_does_not_raise(notifier, session_factory, make_order):
    order = await make_order()
    notifier.customer_bot.send_message.side_effect = RuntimeError("forbidden")

    await notifier.status_changed(order)  # must not raise


async def test_change_status_commits_even_when_customer_bot_forbidden(notifier, session_factory, make_order):
    """A customer who never started the bot or blocked it (TelegramForbiddenError)
    must not stop the status change from being committed (R70i)."""
    from aiogram.exceptions import TelegramForbiddenError

    from app.models import Order as OrderModel
    from app.services.orders import change_status

    order = await make_order(status="new")
    notifier.customer_bot.send_message.side_effect = TelegramForbiddenError(
        method=None, message="bot was blocked by the user"
    )

    async with session_factory() as session:
        await change_status(session, order.id, "accepted", actor_id=555, source="bot", notifier=notifier)

    async with session_factory() as session:
        refreshed = await session.get(OrderModel, order.id)
    assert refreshed.status == "accepted"
