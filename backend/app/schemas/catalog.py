"""Request/response shapes for the catalog and uploads API."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ConfigOut(BaseModel):
    shop_name: str
    shop_subtitle: str
    pickup_address: str


class CategoryOut(BaseModel):
    id: int
    name: str


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class ProductOut(BaseModel):
    id: int
    category_id: int
    name: str
    sku: str
    price: int
    description: str | None
    image_url: str | None
    is_available: bool


class ProductIn(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=100)
    sku: str = Field(min_length=1, max_length=32)
    price: int = Field(ge=0, le=100_000_000)
    description: str | None = Field(default=None, max_length=2000)
    upload_id: int | None = None
    is_available: bool = True


class ProductPatch(BaseModel):
    # category_id/name/sku/price/is_available are `X | None = None` only so that
    # exclude_unset can tell "omitted" from "provided" — they are still required
    # columns, so an explicit `null` for any of them must be rejected (422) here,
    # before it can reach the service layer. description/upload_id are genuinely
    # nullable (upload_id maps to image_path) and null is allowed to clear them.
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    sku: str | None = Field(default=None, min_length=1, max_length=32)
    price: int | None = Field(default=None, ge=0, le=100_000_000)
    description: str | None = Field(default=None, max_length=2000)
    upload_id: int | None = None
    is_available: bool | None = None

    @field_validator("category_id", "name", "sku", "price", "is_available", mode="before")
    @classmethod
    def _required_field_rejects_null(cls, value: object, info) -> object:
        if value is None:
            raise ValueError(f"{info.field_name} cannot be null")
        return value


class UploadOut(BaseModel):
    upload_id: int
    url: str
