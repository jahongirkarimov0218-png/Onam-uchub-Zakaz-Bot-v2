"""Customer-facing order endpoints."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth import TgUser, customer_user
from ..db import get_session
from ..models import Order, OrderItem
from ..schemas.orders import OrderCreate, OrderItemOut, OrderOut
from ..services import orders as orders_service
from ..services.orders import LABELS_UZ, OrderError
from ..uploads import public_url

router = APIRouter(dependencies=[Depends(customer_user)])


def order_item_to_out(item: OrderItem) -> OrderItemOut:
    return OrderItemOut(
        kind=item.kind,
        product_id=item.product_id,
        name=item.name,
        sku=item.sku,
        image_url=public_url(item.image_path) if item.image_path else None,
        unit_price=item.unit_price,
        quantity=item.quantity,
        note=item.note,
    )


def order_to_out(order: Order) -> OrderOut:
    created_at = order.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=dt.timezone.utc)
    return OrderOut(
        id=order.id,
        status=order.status,
        status_label=LABELS_UZ[order.status],
        customer_name=order.customer_name,
        phone=order.phone,
        delivery_type=order.delivery_type,
        address=order.address,
        comment=order.comment,
        total=order.total,
        created_at=created_at,
        items=[order_item_to_out(i) for i in order.items],
    )


@router.post("/api/orders", status_code=201)
async def create_order(
    request: Request,
    body: OrderCreate,
    user: TgUser = Depends(customer_user),
    session=Depends(get_session),
) -> OrderOut:
    limiter = request.app.state.order_limiter
    if not limiter.hit(user.id):
        raise HTTPException(status_code=429, detail="rate_limited")
    try:
        order = await orders_service.create_order(session, user, body, notifier=request.app.state.notifier)
    except OrderError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc
    return order_to_out(order)


@router.get("/api/orders/my")
async def my_orders(user: TgUser = Depends(customer_user), session=Depends(get_session)) -> list[OrderOut]:
    orders = await orders_service.list_orders(session, tg_user_id=user.id)
    return [order_to_out(o) for o in orders]
