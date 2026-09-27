"""Order lifecycle: creation, status machine, search/listing, stats.

Owns price snapshotting and history writing; exposes `create_order`,
`change_status`, `list_orders`, `search_orders`, `open_orders`, `stats`,
`load_order`, the status machine (`allowed`, `NEXT`, `FINAL`, `LABELS_UZ`) and
`OrderError` / `InvalidTransition`.
"""
from __future__ import annotations

import datetime as dt
import logging
import re
from collections import defaultdict

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import TgUser
from ..models import Order, OrderItem, OrderStatusHistory, Product, Upload
from ..notify import Notifier

logger = logging.getLogger(__name__)

NEXT = {"new": "accepted", "accepted": "ordered", "ordered": "arrived", "arrived": "delivered"}
FINAL = {"delivered", "cancelled"}
LABELS_UZ = {
    "new": "Yangi",
    "accepted": "Qabul qilindi",
    "ordered": "Faberlic'ga buyurtma berildi",
    "arrived": "Yetib keldi",
    "delivered": "Topshirildi",
    "cancelled": "Bekor qilindi",
}


class OrderError(Exception):
    """Raised for order rule violations. `code` is the machine error code."""

    def __init__(self, code: str, http_status: int) -> None:
        self.code = code
        self.http_status = http_status
        super().__init__(code)


class InvalidTransition(OrderError):
    """Raised by `change_status` for a forbidden status transition (409)."""

    def __init__(self) -> None:
        super().__init__("invalid_transition", 409)


def allowed(from_status: str, to_status: str) -> bool:
    return NEXT.get(from_status) == to_status or (to_status == "cancelled" and from_status not in FINAL)


async def _notify_safely(notifier: Notifier | None, method: str, arg: object) -> None:
    if notifier is None:
        return
    try:
        await getattr(notifier, method)(arg)
    except Exception:  # noqa: BLE001 - notifier failures must never break orders
        logger.exception("notifier.%s failed", method)


async def _build_catalog_item(session: AsyncSession, product_id: int, quantity: int) -> OrderItem:
    product = await session.get(Product, product_id)
    if product is None or product.is_deleted or not product.is_available:
        raise OrderError("product_unavailable", 400)
    return OrderItem(
        kind="catalog",
        product_id=product.id,
        name=product.name,
        sku=product.sku,
        image_path=product.image_path,
        unit_price=product.price,
        quantity=quantity,
        note=None,
    )


async def _build_custom_item(session: AsyncSession, user: TgUser, custom, quantity: int) -> OrderItem:
    image_path = None
    if custom.upload_id is not None:
        upload = await session.get(Upload, custom.upload_id)
        if upload is None or upload.kind != "custom" or upload.uploaded_by != user.id:
            raise OrderError("invalid_upload", 400)
        image_path = upload.filename
    return OrderItem(
        kind="custom",
        product_id=None,
        name=custom.name,
        sku=custom.sku,
        image_path=image_path,
        unit_price=None,
        quantity=quantity,
        note=custom.note,
    )


async def create_order(
    session: AsyncSession, user: TgUser, data, notifier: Notifier | None = None
) -> Order:
    """Validate items against the catalog/uploads, snapshot prices from the DB
    (client-supplied prices are never trusted — `OrderCreate` has no such field),
    total = sum of catalog lines only, write the initial history row, and notify.

    Notifier failures are caught and logged; they never break order creation.
    """
    items: list[OrderItem] = []
    total = 0
    for line in data.items:
        if line.product_id is not None:
            item = await _build_catalog_item(session, line.product_id, line.quantity)
            total += item.unit_price * item.quantity
        else:
            item = await _build_custom_item(session, user, line.custom, line.quantity)
        items.append(item)

    order = Order(
        tg_user_id=user.id,
        tg_username=user.username,
        customer_name=data.customer_name,
        phone=data.phone,
        delivery_type=data.delivery_type,
        address=data.address,
        comment=data.comment,
        status="new",
        total=total,
        admin_notified=False,
    )
    session.add(order)
    await session.flush()

    for item in items:
        item.order_id = order.id
        session.add(item)

    history = OrderStatusHistory(
        order_id=order.id, from_status=None, to_status="new", actor_tg_id=user.id, source="customer"
    )
    session.add(history)
    await session.commit()
    await session.refresh(order)

    order.items = items
    order.history = [history]

    await _notify_safely(notifier, "order_created", order)
    return order


async def change_status(
    session: AsyncSession,
    order_id: int,
    to: str,
    actor_id: int | None,
    source: str,
    notifier: Notifier | None = None,
) -> Order:
    """Enforce the status machine, write a history row, and notify. Raises
    `InvalidTransition` (409) for a forbidden move, `OrderError("not_found", 404)`
    if the order does not exist.

    The write is a conditional `UPDATE ... WHERE id=:id AND status=:from_status`:
    if another request already moved the order off the status we just read, this
    affects 0 rows and we raise `InvalidTransition` instead of silently applying a
    transition (or writing a duplicate history row) on top of a stale read.
    """
    order = await session.get(Order, order_id)
    if order is None:
        raise OrderError("not_found", 404)
    from_status = order.status
    if not allowed(from_status, to):
        raise InvalidTransition()

    result = await session.execute(
        update(Order).where(Order.id == order_id, Order.status == from_status).values(status=to)
    )
    if result.rowcount == 0:
        raise InvalidTransition()

    session.add(
        OrderStatusHistory(order_id=order.id, from_status=from_status, to_status=to, actor_tg_id=actor_id, source=source)
    )
    await session.commit()
    await session.refresh(order)
    await _attach_items(session, [order])

    await _notify_safely(notifier, "status_changed", order)
    return order


async def load_order(session: AsyncSession, order_id: int) -> Order | None:
    """Fetch a single order with `.items` and `.history` attached as plain lists
    (oldest-first for history) — used for API detail responses and notifiers."""
    order = await session.get(Order, order_id)
    if order is None:
        return None
    await _attach_items(session, [order])
    history_stmt = (
        select(OrderStatusHistory).where(OrderStatusHistory.order_id == order_id).order_by(OrderStatusHistory.id)
    )
    order.history = list((await session.execute(history_stmt)).scalars().all())
    return order


async def _attach_items(session: AsyncSession, orders: list[Order]) -> list[Order]:
    if not orders:
        return orders
    order_ids = [o.id for o in orders]
    stmt = select(OrderItem).where(OrderItem.order_id.in_(order_ids)).order_by(OrderItem.id)
    items = (await session.execute(stmt)).scalars().all()
    by_order: dict[int, list[OrderItem]] = defaultdict(list)
    for item in items:
        by_order[item.order_id].append(item)
    for order in orders:
        order.items = by_order.get(order.id, [])
    return orders


def _matches_query(order: Order, query: str) -> bool:
    q = query.strip()
    if not q:
        return True
    ql = q.lower()
    if q.isdigit() and str(order.id) == q:
        return True
    digits = re.sub(r"\D", "", q)
    if len(digits) >= 9:
        order_digits = re.sub(r"\D", "", order.phone)
        if order_digits[-9:] == digits[-9:]:
            return True
    if ql in order.customer_name.lower():
        return True
    return False


async def search_orders(session: AsyncSession, query: str) -> list[Order]:
    """Orders matching by id, phone (last 9 digits), or customer name substring,
    newest first."""
    stmt = select(Order).order_by(Order.id.desc())
    orders = list((await session.execute(stmt)).scalars().all())
    matched = [o for o in orders if _matches_query(o, query)]
    return await _attach_items(session, matched)


async def list_orders(
    session: AsyncSession,
    *,
    tg_user_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 200,
) -> list[Order]:
    """General listing, newest first. `tg_user_id` narrows to one customer
    (`/api/orders/my`); `status`/`q` are the admin filter/search."""
    stmt = select(Order)
    if tg_user_id is not None:
        stmt = stmt.where(Order.tg_user_id == tg_user_id)
    if status is not None:
        stmt = stmt.where(Order.status == status)
    stmt = stmt.order_by(Order.id.desc())
    orders = list((await session.execute(stmt)).scalars().all())
    if q:
        orders = [o for o in orders if _matches_query(o, q)]
    orders = orders[:limit]
    return await _attach_items(session, orders)


async def open_orders(session: AsyncSession) -> list[Order]:
    """Orders not in a final status (delivered/cancelled), newest first."""
    stmt = select(Order).where(Order.status.notin_(FINAL)).order_by(Order.id.desc())
    orders = list((await session.execute(stmt)).scalars().all())
    return await _attach_items(session, orders)


async def stats(session: AsyncSession, now: dt.datetime, tz: dt.tzinfo) -> dict:
    """Counts per status, orders created today (local `tz` calendar day), and
    the sum of `delivered` orders' totals in the current local month.

    `now` and DB datetimes: DB columns are naive UTC (SQLite drops tzinfo); the
    local-day/month boundaries are converted back to naive UTC before comparing.
    """
    local_now = now.astimezone(tz)
    day_start_utc = local_now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(dt.timezone.utc).replace(tzinfo=None)
    month_start_utc = local_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(dt.timezone.utc).replace(tzinfo=None)

    by_status_stmt = select(Order.status, func.count()).group_by(Order.status)
    rows = (await session.execute(by_status_stmt)).all()
    by_status = {status_key: 0 for status_key in LABELS_UZ}
    for status_value, count in rows:
        by_status[status_value] = count

    today_stmt = select(func.count()).select_from(Order).where(Order.created_at >= day_start_utc)
    today = (await session.execute(today_stmt)).scalar_one()

    delivered_stmt = (
        select(func.coalesce(func.sum(Order.total), 0))
        .select_from(Order)
        .join(OrderStatusHistory, OrderStatusHistory.order_id == Order.id)
        .where(
            Order.status == "delivered",
            OrderStatusHistory.to_status == "delivered",
            OrderStatusHistory.created_at >= month_start_utc,
        )
    )
    delivered_month_sum = (await session.execute(delivered_stmt)).scalar_one()

    return {"by_status": by_status, "today": today, "delivered_month_sum": delivered_month_sum}
