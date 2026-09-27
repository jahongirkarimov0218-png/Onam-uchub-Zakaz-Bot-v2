from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.bots.admin import admin_router
from app.config import Settings
from app.notify import TelegramNotifier


def _admin_settings(**overrides):
    fields = dict(admin_ids="10,20", webapp_url="", bots_enabled=True)
    fields.update(overrides)
    return Settings(**fields)


def _message(user_id, text=None, message_id=777):
    msg = AsyncMock()
    msg.from_user = SimpleNamespace(id=user_id)
    msg.chat = SimpleNamespace(id=user_id)
    msg.text = text
    msg.answer.return_value = SimpleNamespace(message_id=message_id)
    return msg


def _callback(user_id, data):
    cb = AsyncMock()
    cb.from_user = SimpleNamespace(id=user_id)
    cb.data = data
    cb.message = AsyncMock()
    return cb


async def _dispatch_message(router, message):
    bot = AsyncMock()
    for handler in router.message.handlers:
        ok = True
        for f in handler.filters:
            result = await f.call(message, bot=bot)
            if not result:
                ok = False
                break
        if ok:
            await handler.callback(message)
            return handler
    raise AssertionError("no message handler matched")


async def _dispatch_callback(router, callback):
    bot = AsyncMock()
    for handler in router.callback_query.handlers:
        ok = True
        for f in handler.filters:
            result = await f.call(callback, bot=bot)
            if not result:
                ok = False
                break
        if ok:
            await handler.callback(callback)
            return handler
    raise AssertionError("no callback handler matched")


@pytest.fixture
def notifier():
    n = AsyncMock()
    return n


async def test_non_admin_message_gets_only_ruxsat_yoq(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(999, text="/start")

    await _dispatch_message(router, message)

    message.answer.assert_awaited_once_with("Ruxsat yo'q")


async def test_non_admin_callback_gets_only_ruxsat_yoq(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    callback = _callback(999, "st:1:accepted")

    await _dispatch_callback(router, callback)

    callback.answer.assert_awaited_once()
    assert callback.answer.await_args.args[0] == "Ruxsat yo'q"


async def test_admin_start_without_webapp_url_greets_without_button(session_factory, notifier):
    settings = _admin_settings(webapp_url="")
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/start")

    await _dispatch_message(router, message)

    args, kwargs = message.answer.await_args
    assert kwargs.get("reply_markup") is None


async def test_admin_start_with_webapp_url_has_admin_button(session_factory, notifier):
    settings = _admin_settings(webapp_url="https://shop.example.com")
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/start")

    await _dispatch_message(router, message)

    args, kwargs = message.answer.await_args
    button = kwargs["reply_markup"].inline_keyboard[0][0]
    assert button.web_app.url == "https://shop.example.com/admin/"


async def test_orders_command_lists_open_orders(session_factory, notifier, make_order):
    await make_order(customer_name="Ali")
    await make_order(customer_name="Vali", status="accepted")
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/orders")

    await _dispatch_message(router, message)

    text = message.answer.await_args.args[0]
    assert "/order_1" in text
    assert "/order_2" in text


async def test_orders_command_empty_says_no_open_orders(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/orders")

    await _dispatch_message(router, message)

    message.answer.assert_awaited_once_with("Ochiq zakazlar yo'q")


async def test_order_detail_command_shows_full_message_and_keyboard(session_factory, notifier, make_order):
    order = await make_order()
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text=f"/order_{order.id}")

    await _dispatch_message(router, message)

    args, kwargs = message.answer.await_args
    assert f"#{order.id}" in args[0]
    assert kwargs["reply_markup"] is not None


async def test_order_detail_command_not_found(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/order_9999")

    await _dispatch_message(router, message)

    message.answer.assert_awaited_once_with("Topilmadi")


async def test_find_without_arg_shows_usage_hint(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/find")

    await _dispatch_message(router, message)

    text = message.answer.await_args.args[0]
    assert "/find" in text


async def test_find_by_id_finds_order(session_factory, notifier, make_order):
    order = await make_order()
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text=f"/find {order.id}")

    await _dispatch_message(router, message)

    text = message.answer.await_args.args[0]
    assert f"#{order.id}" in text


async def test_find_by_phone_finds_order(session_factory, notifier, make_order):
    order = await make_order(phone="+998901234567")
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/find 901234567")

    await _dispatch_message(router, message)

    text = message.answer.await_args.args[0]
    assert f"#{order.id}" in text


async def test_find_not_found(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/find 000000000")

    await _dispatch_message(router, message)

    message.answer.assert_awaited_once_with("Topilmadi")


async def test_stats_command_reports_numbers(session_factory, notifier, make_order):
    await make_order()
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/stats")

    await _dispatch_message(router, message)

    text = message.answer.await_args.args[0]
    assert "Statistika" in text


async def test_status_callback_changes_status_and_acks(session_factory, notifier, make_order):
    order = await make_order(status="new")
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    callback = _callback(10, f"st:{order.id}:accepted")

    await _dispatch_callback(router, callback)

    notifier.status_changed.assert_awaited_once()
    callback.answer.assert_awaited_once_with()

    async with session_factory() as session:
        from app.models import Order as OrderModel

        refreshed = await session.get(OrderModel, order.id)
    assert refreshed.status == "accepted"


async def test_pressing_button_on_order_detail_message_edits_that_exact_message(session_factory, make_order):
    """R33: a status change must re-render the pressed message even when it was
    opened via /order_<id> (not the original broadcast in `order_admin_messages`)."""
    order = await make_order(status="new")
    settings = _admin_settings()
    admin_bot = AsyncMock()
    customer_bot = AsyncMock()
    real_notifier = TelegramNotifier(customer_bot, admin_bot, settings, session_factory)
    router = admin_router(settings, session_factory, real_notifier)

    detail_message = _message(10, text=f"/order_{order.id}", message_id=4242)
    await _dispatch_message(router, detail_message)  # sends the /order_<id> card

    callback = _callback(10, f"st:{order.id}:accepted")
    callback.message = None  # the press came through the /order_<id> message, tracked in DB, not callback.message
    await _dispatch_callback(router, callback)

    admin_bot.edit_message_text.assert_awaited_once()
    kwargs = admin_bot.edit_message_text.await_args.kwargs
    assert kwargs["chat_id"] == 10
    assert kwargs["message_id"] == 4242
    assert "Qabul qilindi" in kwargs["text"]


async def test_admin_start_accepts_botname_suffix_and_deep_link_payload(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)

    for text in ["/start@MyBot", "/start somepayload"]:
        message = _message(10, text=text)
        await _dispatch_message(router, message)
        message.answer.assert_awaited_once()


async def test_orders_and_stats_accept_botname_suffix(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)

    orders_message = _message(10, text="/orders@MyBot")
    await _dispatch_message(router, orders_message)
    orders_message.answer.assert_awaited_once_with("Ochiq zakazlar yo'q")

    stats_message = _message(10, text="/stats@MyBot")
    await _dispatch_message(router, stats_message)
    stats_message.answer.assert_awaited_once()


async def test_admin_unknown_text_gets_help_not_ruxsat_yoq(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="salom")

    await _dispatch_message(router, message)

    text = message.answer.await_args.args[0]
    assert text != "Ruxsat yo'q"
    assert "/orders" in text


async def test_admin_photo_message_gets_help_not_ruxsat_yoq(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text=None)  # a photo message has no .text

    await _dispatch_message(router, message)

    text = message.answer.await_args.args[0]
    assert text != "Ruxsat yo'q"


async def test_admin_unknown_command_gets_help_not_ruxsat_yoq(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(10, text="/unknown")

    await _dispatch_message(router, message)

    message.answer.assert_awaited_once_with(
        "Buyruqlar:\n/orders — ochiq zakazlar\n/order_<raqam> — zakaz tafsilotlari\n"
        "/find <raqam yoki telefon> — qidirish\n/stats — statistika"
    )


async def test_non_admin_still_gets_only_ruxsat_yoq_for_unknown_text(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    message = _message(999, text="salom")

    await _dispatch_message(router, message)

    message.answer.assert_awaited_once_with("Ruxsat yo'q")


async def test_admin_unknown_callback_is_acknowledged_silently_not_ruxsat_yoq(session_factory, notifier):
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    callback = _callback(10, "unknown:data")

    await _dispatch_callback(router, callback)

    callback.answer.assert_awaited_once_with()


async def test_stale_status_callback_answers_and_does_not_change(session_factory, notifier, make_order):
    order = await make_order(status="accepted")
    settings = _admin_settings()
    router = admin_router(settings, session_factory, notifier)
    # "accepted" -> "accepted" is not a valid transition (stale button, already moved)
    callback = _callback(10, f"st:{order.id}:accepted")

    await _dispatch_callback(router, callback)

    callback.answer.assert_awaited_once()
    assert callback.answer.await_args.args[0] == "Holat allaqachon o'zgargan"
    callback.message.edit_text.assert_awaited_once()

    async with session_factory() as session:
        from app.models import Order as OrderModel

        refreshed = await session.get(OrderModel, order.id)
    assert refreshed.status == "accepted"
