"""Admin order endpoints: list/filter/search, detail with history, status changes, stats."""
from __future__ import annotations

import datetime as dt
import zoneinfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ..auth import TgUser, admin_user
from ..config import Settings, get_settings
from ..db import get_session
from ..models import OrderStatusHistory
from ..schemas.orders import HistoryOut, OrderDetailOut, OrderOut, StatsOut, StatusIn
from ..services import orders as orders_service
from ..services.orders import OrderError
from .orders import order_to_out

router = APIRouter(prefix="/api/admin", dependencies=[Depends(admin_user)])


def _history_to_out(row: OrderStatusHistory) -> HistoryOut:
    created_at = row.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=dt.timezone.utc)
    return HistoryOut(
        from_status=row.from_status,
        to_status=row.to_status,
        actor_tg_id=row.actor_tg_id,
        source=row.source,
        created_at=created_at,
    )


@router.get("/orders")
async def list_orders(
    status: str | None = None,
    q: str | None = None,
    limit: int = Query(default=200, ge=1, le=200),
    session=Depends(get_session),
) -> list[OrderOut]:
    orders = await orders_service.list_orders(session, status=status, q=q, limit=limit)
    return [order_to_out(o) for o in orders]


@router.get("/orders/{order_id}")
async def order_detail(order_id: int, session=Depends(get_session)) -> OrderDetailOut:
    order = await orders_service.load_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="not_found")
    out = order_to_out(order)
    return OrderDetailOut(**out.model_dump(), history=[_history_to_out(h) for h in order.history])


@router.post("/orders/{order_id}/status")
async def set_status(
    order_id: int,
    body: StatusIn,
    request: Request,
    user: TgUser = Depends(admin_user),
    session=Depends(get_session),
) -> OrderOut:
    try:
        order = await orders_service.change_status(
            session, order_id, body.status, actor_id=user.id, source="admin_app",
            notifier=request.app.state.notifier,
        )
    except OrderError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc
    return order_to_out(order)


@router.get("/stats")
async def get_stats(settings: Settings = Depends(get_settings), session=Depends(get_session)) -> StatsOut:
    tz = zoneinfo.ZoneInfo(settings.timezone)
    now = dt.datetime.now(dt.timezone.utc)
    data = await orders_service.stats(session, now, tz)
    return StatsOut(**data)
