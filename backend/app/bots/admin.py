"""Admin bot: commands, status-change callbacks, and the "Ruxsat yo'q" gate.

Exposes `admin_router(settings, session_factory, notifier) -> Router`. Command
matching uses `F.text` magic filters (not aiogram's `Command`/`CommandStart`,
which require a real `aiogram.types.Message` instance) so handlers can be
exercised in tests with lightweight stand-in message/callback objects. All
commands accept an optional `@BotName` suffix and trailing text/args, like
Telegram group chats send them.

Handler order matters: admin-specific handlers first, then an admin catch-all
(help text, never "Ruxsat yo'q" for a recognised admin), then the final
catch-all ("Ruxsat yo'q") for anyone not in `ADMIN_IDS`.
"""
from __future__ import annotations

import datetime as dt
import re
import zoneinfo

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from .. import texts
from ..config import Settings
from ..models import OrderAdminMessage
from ..notify import Notifier, format_order, order_keyboard
from ..services import orders as orders_service
from ..services.orders import InvalidTransition, OrderError
from ..statuses import FINAL

_START_RE = re.compile(r"^/start(?:@\w+)?(?:\s+.*)?$")
_ORDERS_RE = re.compile(r"^/orders(?:@\w+)?$")
_STATS_RE = re.compile(r"^/stats(?:@\w+)?$")
_ORDER_DETAIL_RE = re.compile(r"^/order_(\d+)(?:@\w+)?$")
_FIND_RE = re.compile(r"^/find(?:@\w+)?(?:\s+(.*))?$")


def admin_router(settings: Settings, session_factory, notifier: Notifier) -> Router:
    router = Router(name="admin")
    is_admin = F.from_user.id.in_(settings.admin_id_set)

    @router.message(F.text.regexp(_START_RE), is_admin)
    async def start(message: Message) -> None:
        if settings.webapp_url:
            url = f"{settings.webapp_url.rstrip('/')}/admin/"
            markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=texts.BTN_OPEN_ADMIN, web_app=WebAppInfo(url=url))]]
            )
            await message.answer(texts.ADMIN_GREETING, reply_markup=markup)
        else:
            await message.answer(texts.ADMIN_GREETING_NO_WEBAPP)

    @router.message(F.text.regexp(_ORDERS_RE), is_admin)
    async def list_open(message: Message) -> None:
        async with session_factory() as session:
            open_orders = await orders_service.open_orders(session)
        await message.answer(texts.open_orders_list(open_orders))

    @router.message(F.text.regexp(_ORDER_DETAIL_RE), is_admin)
    async def order_detail(message: Message) -> None:
        match = _ORDER_DETAIL_RE.match(message.text or "")
        order_id = int(match.group(1))
        async with session_factory() as session:
            order = await orders_service.load_order(session, order_id)
            if order is None:
                await message.answer(texts.NOT_FOUND)
                return
            sent = await message.answer(format_order(order), reply_markup=order_keyboard(order))
            if order.status not in FINAL:
                # Track this message too, so a later status-change edits it in
                # place (not just the original broadcast to admins) — R33.
                session.add(
                    OrderAdminMessage(order_id=order.id, chat_id=message.chat.id, message_id=sent.message_id)
                )
                await session.commit()

    @router.message(F.text.regexp(_FIND_RE), is_admin)
    async def find(message: Message) -> None:
        match = _FIND_RE.match(message.text or "")
        query = (match.group(1) or "").strip()
        if not query:
            await message.answer(texts.FIND_USAGE)
            return
        async with session_factory() as session:
            results = await orders_service.search_orders(session, query)
        await message.answer(texts.search_results_list(results))

    @router.message(F.text.regexp(_STATS_RE), is_admin)
    async def stats_cmd(message: Message) -> None:
        tz = zoneinfo.ZoneInfo(settings.timezone)
        now = dt.datetime.now(dt.timezone.utc)
        async with session_factory() as session:
            data = await orders_service.stats(session, now, tz)
        await message.answer(texts.stats_text(data))

    @router.callback_query(F.data.startswith("st:"), is_admin)
    async def on_status_callback(callback: CallbackQuery) -> None:
        _, order_id_s, to_status = (callback.data or "").split(":")
        order_id = int(order_id_s)
        async with session_factory() as session:
            try:
                await orders_service.change_status(
                    session, order_id, to_status, actor_id=callback.from_user.id, source="bot",
                    notifier=notifier,
                )
            except InvalidTransition:
                current = await orders_service.load_order(session, order_id)
                await callback.answer(texts.STALE_STATUS)
                if current is not None and callback.message is not None:
                    await callback.message.edit_text(format_order(current), reply_markup=order_keyboard(current))
                return
            except OrderError:
                await callback.answer(texts.NOT_FOUND)
                return
        await callback.answer()

    @router.message(is_admin)
    async def admin_fallback(message: Message) -> None:
        # A recognised admin sending anything unrecognised (text, photo,
        # unknown command) gets help, never "Ruxsat yo'q".
        await message.answer(texts.ADMIN_HELP)

    @router.callback_query(is_admin)
    async def admin_fallback_callback(callback: CallbackQuery) -> None:
        await callback.answer()

    @router.message()
    async def not_admin_message(message: Message) -> None:
        await message.answer(texts.NOT_ADMIN)

    @router.callback_query()
    async def not_admin_callback(callback: CallbackQuery) -> None:
        await callback.answer(texts.NOT_ADMIN, show_alert=True)

    return router
