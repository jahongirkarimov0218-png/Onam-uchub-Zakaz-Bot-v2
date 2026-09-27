"""Outbound Telegram notifications port.

This ticket owns only the port itself: the `Notifier` protocol and `NullNotifier`
(used when bots are disabled, or as the `create_app` default). `TelegramNotifier`
(two aiogram `Bot`s, message-id bookkeeping) lands in a later ticket behind the
same protocol — order creation/status change never depend on which one is wired.
"""
from __future__ import annotations

import logging
from typing import Protocol

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
