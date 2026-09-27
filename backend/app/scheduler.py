"""Timed jobs: retry unnotified orders, remind about stale `new` orders, and
the daily open-orders report.

Job bodies are plain async functions taking `(session_factory, notifier,
settings, now)` so tests call them directly with a fixed `now`;
`build_scheduler` wires them into APScheduler.
"""
from __future__ import annotations

import datetime as dt
import zoneinfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from .config import Settings
from .models import Order
from .notify import Notifier
from .services import orders as orders_service


def _require_aware(now: dt.datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")


async def remind_and_retry(session_factory, notifier: Notifier, settings: Settings, now: dt.datetime) -> None:
    """Resend the admin notification for orders that never got it
    (`admin_notified=False`), and remind about `new` orders sitting unaccepted
    past `REMINDER_FIRST_HOURS`, repeating every `REMINDER_REPEAT_HOURS` while
    they stay `new`. DB datetimes are naive UTC; `now` is converted the same way
    before comparing. Raises `ValueError` for a naive `now` (would otherwise be
    silently treated as local time)."""
    _require_aware(now)
    now_naive = now.astimezone(dt.timezone.utc).replace(tzinfo=None)

    async with session_factory() as session:
        stmt = select(Order.id).where(Order.admin_notified.is_(False))
        not_notified_ids = list((await session.execute(stmt)).scalars().all())
    for order_id in not_notified_ids:
        async with session_factory() as session:
            order = await orders_service.load_order(session, order_id)
        if order is not None:
            await notifier.order_created(order)

    first_threshold = now_naive - dt.timedelta(hours=settings.reminder_first_hours)
    repeat_threshold = now_naive - dt.timedelta(hours=settings.reminder_repeat_hours)

    due_ids: list[int] = []
    async with session_factory() as session:
        stmt = select(Order).where(Order.status == "new", Order.created_at <= first_threshold)
        candidates = list((await session.execute(stmt)).scalars().all())
        due = [o for o in candidates if o.last_reminded_at is None or o.last_reminded_at <= repeat_threshold]
        for order in due:
            order.last_reminded_at = now_naive
            due_ids.append(order.id)
        if due:
            await session.commit()

    if due_ids:
        due_orders = []
        async with session_factory() as session:
            for order_id in due_ids:
                order = await orders_service.load_order(session, order_id)
                if order is not None:
                    due_orders.append(order)
        await notifier.reminder(due_orders)


async def daily_report(session_factory, notifier: Notifier, settings: Settings, now: dt.datetime) -> None:
    """Forward the currently open orders (not delivered/cancelled) to the
    notifier; it decides how to group/format them ("Ochiq zakazlar yo'q" if
    empty). Raises `ValueError` for a naive `now`."""
    _require_aware(now)
    async with session_factory() as session:
        orders = await orders_service.open_orders(session)
    await notifier.daily_report(orders)


def build_scheduler(session_factory, notifier: Notifier, settings: Settings) -> AsyncIOScheduler:
    tz = zoneinfo.ZoneInfo(settings.timezone)
    scheduler = AsyncIOScheduler(timezone=tz)

    async def _remind_job() -> None:
        await remind_and_retry(session_factory, notifier, settings, dt.datetime.now(dt.timezone.utc))

    async def _report_job() -> None:
        await daily_report(session_factory, notifier, settings, dt.datetime.now(dt.timezone.utc))

    scheduler.add_job(_remind_job, IntervalTrigger(minutes=settings.reminder_check_minutes))
    hour_s, minute_s = settings.daily_report_time.split(":")
    scheduler.add_job(_report_job, CronTrigger(hour=int(hour_s), minute=int(minute_s), timezone=tz))
    return scheduler
