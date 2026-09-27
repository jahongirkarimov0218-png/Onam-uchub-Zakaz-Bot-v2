"""Request/response shapes for the orders API.

Owns phone normalization and the structural item-shape rules (at least one of
product_id/custom, custom needs at least one of name/sku/upload_id, delivery
requires address); everything that needs the DB (product exists/available,
upload ownership) is `app.services.orders`'s job.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator

_STRIP_CHARS = re.compile(r"[\s\-()]")
_PHONE_WITH_PLUS = re.compile(r"^\+\d{9,15}$")
_PHONE_DIGITS = re.compile(r"^\d{9,15}$")


def normalize_phone(raw: str) -> str:
    """Strip spaces/dashes/parentheses, then accept `+` followed by 9-15 digits
    (any country code, e.g. `+998...`, `+7...`) as-is; a bare 9-digit local
    number gets `+998` prefixed; a longer bare digit string (already carrying a
    country code) gets a leading `+`. Anything else raises `ValueError` (-> 422
    at the API edge)."""
    value = _STRIP_CHARS.sub("", raw.strip())
    if _PHONE_WITH_PLUS.fullmatch(value):
        return value
    if _PHONE_DIGITS.fullmatch(value):
        return f"+998{value}" if len(value) == 9 else f"+{value}"
    raise ValueError("invalid phone number")


class CustomItemIn(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    sku: str | None = Field(default=None, max_length=32)
    upload_id: int | None = None
    note: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def _at_least_one_field(self) -> "CustomItemIn":
        if not (self.name or self.sku or self.upload_id):
            raise ValueError("custom line needs a name, article or photo")
        return self


class OrderItemIn(BaseModel):
    product_id: int | None = None
    custom: CustomItemIn | None = None
    quantity: int = Field(ge=1, le=99)

    @model_validator(mode="after")
    def _exactly_one_kind(self) -> "OrderItemIn":
        if (self.product_id is None) == (self.custom is None):
            raise ValueError("item needs exactly one of product_id or custom")
        return self


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=20)
    delivery_type: Literal["delivery", "pickup"]
    address: str | None = Field(default=None, max_length=300)
    comment: str | None = Field(default=None, max_length=500)
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def _normalize_and_check(self) -> "OrderCreate":
        self.phone = normalize_phone(self.phone)
        if self.delivery_type == "delivery" and not (self.address and self.address.strip()):
            raise ValueError("address is required for delivery")
        return self


class OrderItemOut(BaseModel):
    kind: Literal["catalog", "custom"]
    product_id: int | None
    name: str | None
    sku: str | None
    image_url: str | None
    unit_price: int | None
    quantity: int
    note: str | None


class OrderOut(BaseModel):
    id: int
    status: str
    status_label: str
    customer_name: str
    phone: str
    delivery_type: str
    address: str | None
    comment: str | None
    total: int
    created_at: dt.datetime
    items: list[OrderItemOut]


class HistoryOut(BaseModel):
    from_status: str | None
    to_status: str
    actor_tg_id: int | None
    source: str
    created_at: dt.datetime


class OrderDetailOut(OrderOut):
    history: list[HistoryOut]


class StatusIn(BaseModel):
    status: Literal["new", "accepted", "ordered", "arrived", "delivered", "cancelled"]


class StatsOut(BaseModel):
    by_status: dict[str, int]
    today: int
    delivered_month_sum: int
