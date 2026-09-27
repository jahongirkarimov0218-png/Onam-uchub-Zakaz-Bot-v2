"""Outbound Telegram notifications port.

`Notifier` protocol and `NullNotifier` (bots disabled / `create_app` default).
`TelegramNotifier` (two aiogram `Bot`s) sends order/status messages to admins
and the customer, keeping `order_admin_messages` in sync so `status_changed`
knows which messages to edit. Every Telegram call is wrapped: failures are
logged and never propagated, so a notifier problem never breaks an order.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from sqlalchemy import select, update

from . import texts
from .models import Order, OrderAdminMessage
from .statuses import FINAL, LABELS_UZ, NEXT

logger = logging.getLogger(__name__)


class Notifier(Protocol):
    """Outbound notification port used by `app.services.orders`.

    Implementations must never raise: callers invoke these inside a try/except
    and only log failures, so a notifier that raises would simply be swallowed
    upstream — but it should not rely on that and should handle its own errors.
    """

    async def order_created(self, order: object) -> None: ...

    async def status_changed(self, order: object) -> None: ...

    async def reminder(self, orders: list) -> None: ...

    async def daily_report(self, orders: list) -> None: ...


class NullNotifier:
    """No-op notifier: logs instead of sending. Used when bots are disabled and
    as the `create_app` default."""

    async def order_created(self, order: object) -> None:
        logger.info("order_created (no-op): order %s", getattr(order, "id", None))

    async def status_changed(self, order: object) -> None:
        logger.info("status_changed (no-op): order %s", getattr(order, "id", None))

    async def reminder(self, orders: list) -> None:
        logger.info("reminder (no-op): %d order(s)", len(orders))

    async def daily_report(self, orders: list) -> None:
        logger.info("daily_report (no-op): %d order(s)", len(orders))


def format_order(order: object) -> str:
    """Render the admin/customer-facing order card: number, customer, phone,
    delivery type/address, items (custom lines marked, unpriced), total, status,
    comment. Every label lives in `app.texts`."""
    lines = [
        f"{texts.LABEL_ORDER_PREFIX}{order.id}",
        f"{texts.LABEL_CUSTOMER} {order.customer_name}",
        f"{texts.LABEL_PHONE} {order.phone}",
    ]
    if getattr(order, "tg_username", None):
        lines.append(f"{texts.LABEL_USERNAME} @{order.tg_username}")
    if order.delivery_type == "delivery":
        lines.append(f"{texts.LABEL_DELIVERY} {order.address or ''}")
    else:
        lines.append(texts.PICKUP_LINE)

    lines.append("")
    lines.append(texts.LABEL_ITEMS)
    for item in order.items:
        name = item.name or item.sku or "—"
        if item.kind == "custom":
            lines.append(f"- {name} {texts.CUSTOM_ITEM_MARKER} x{item.quantity} — {texts.PRICE_LATER}")
        else:
            price = texts.format_money((item.unit_price or 0) * item.quantity)
            lines.append(f"- {name} x{item.quantity} — {price}")

    lines.append("")
    lines.append(f"{texts.LABEL_TOTAL} {texts.format_money(order.total)}")
    lines.append(f"{texts.LABEL_STATUS} {LABELS_UZ[order.status]}")
    if order.comment:
        lines.append(f"{texts.LABEL_COMMENT} {order.comment}")
    return "\n".join(lines)


def order_keyboard(order: object):
    """Inline keyboard with only the next allowed status button + "Bekor
    qilish", while the order is not final. `None` once it is final (delivered
    or cancelled) — nothing left to press."""
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    if order.status in FINAL:
        return None

    buttons = []
    next_status = NEXT.get(order.status)
    if next_status:
        buttons.append(
            InlineKeyboardButton(text=LABELS_UZ[next_status], callback_data=f"st:{order.id}:{next_status}")
        )
    buttons.append(InlineKeyboardButton(text=texts.BTN_CANCEL, callback_data=f"st:{order.id}:cancelled"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


class TelegramNotifier:
    """`Notifier` backed by two aiogram `Bot`s: `admin_bot` for admin chats,
    `customer_bot` for the customer. `session_factory` is used for the
    `order_admin_messages` bookkeeping (which admin message ids belong to which
    order, so `status_changed` knows what to edit) and to flip `admin_notified`."""

    def __init__(self, customer_bot, admin_bot, settings, session_factory) -> None:
        self.customer_bot = customer_bot
        self.admin_bot = admin_bot
        self.settings = settings
        self.session_factory = session_factory

    async def _send_custom_photos(self, admin_id: int, order: object) -> None:
        from aiogram.types import FSInputFile

        upload_dir = Path(self.settings.upload_dir)
        for item in order.items:
            if item.kind != "custom" or not item.image_path:
                continue
            path = upload_dir / item.image_path
            if not path.is_file():
                continue
            try:
                await self.admin_bot.send_photo(admin_id, FSInputFile(path))
            except Exception:  # noqa: BLE001 - a photo failure must not break notifications
                logger.exception("order_created: failed to send photo for order %s to %s", order.id, admin_id)

    async def order_created(self, order: object) -> None:
        text = format_order(order)
        keyboard = order_keyboard(order)
        sent_any = False
        for admin_id in self.settings.admin_id_set:
            try:
                message = await self.admin_bot.send_message(admin_id, text, reply_markup=keyboard)
            except Exception:  # noqa: BLE001
                logger.exception("order_created: failed to notify admin %s for order %s", admin_id, order.id)
                continue
            sent_any = True
            async with self.session_factory() as session:
                session.add(OrderAdminMessage(order_id=order.id, chat_id=admin_id, message_id=message.message_id))
                await session.commit()
            await self._send_custom_photos(admin_id, order)

        if sent_any:
            async with self.session_factory() as session:
                await session.execute(update(Order).where(Order.id == order.id).values(admin_notified=True))
                await session.commit()

    async def status_changed(self, order: object) -> None:
        text = format_order(order)
        keyboard = order_keyboard(order)

        async with self.session_factory() as session:
            stmt = select(OrderAdminMessage).where(OrderAdminMessage.order_id == order.id)
            admin_messages = list((await session.execute(stmt)).scalars().all())

        for admin_message in admin_messages:
            try:
                await self.admin_bot.edit_message_text(
                    chat_id=admin_message.chat_id,
                    message_id=admin_message.message_id,
                    text=text,
                    reply_markup=keyboard,
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "status_changed: failed to edit admin message %s for order %s",
                    admin_message.message_id, order.id,
                )

        try:
            await self.customer_bot.send_message(order.tg_user_id, texts.status_changed_text(order))
        except Exception:  # noqa: BLE001 - customer may have blocked the bot / never started it
            logger.exception("status_changed: failed to notify customer for order %s", order.id)

    async def reminder(self, orders: list) -> None:
        if not orders:
            return
        text = texts.reminder_text(orders)
        for admin_id in self.settings.admin_id_set:
            try:
                await self.admin_bot.send_message(admin_id, text)
            except Exception:  # noqa: BLE001
                logger.exception("reminder: failed to notify admin %s", admin_id)

    async def daily_report(self, orders: list) -> None:
        text = texts.daily_report_text(orders)
        for admin_id in self.settings.admin_id_set:
            try:
                await self.admin_bot.send_message(admin_id, text)
            except Exception:  # noqa: BLE001
                logger.exception("daily_report: failed to notify admin %s", admin_id)
