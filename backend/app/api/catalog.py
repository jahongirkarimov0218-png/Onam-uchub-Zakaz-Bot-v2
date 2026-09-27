"""Customer-facing catalog and uploads endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile

from ..auth import TgUser, customer_user
from ..config import Settings, get_settings
from ..db import get_session
from ..models import Product
from ..schemas.catalog import CategoryOut, ConfigOut, ProductOut, UploadOut
from ..services import catalog
from ..uploads import UploadError, public_url, save_upload

router = APIRouter(dependencies=[Depends(customer_user)])

_PICKUP_ADDRESS_PLACEHOLDER = Settings.model_fields["pickup_address"].default
_SHOP_SUBTITLE = "Faberlic konsultanti do'koni"


def product_to_out(product: Product) -> ProductOut:
    return ProductOut(
        id=product.id,
        category_id=product.category_id,
        name=product.name,
        sku=product.sku,
        price=product.price,
        description=product.description,
        image_url=public_url(product.image_path) if product.image_path else None,
        is_available=product.is_available,
    )


@router.get("/api/config")
async def get_config(settings: Settings = Depends(get_settings)) -> ConfigOut:
    return ConfigOut(
        shop_name=settings.shop_name,
        shop_subtitle=_SHOP_SUBTITLE,
        pickup_address=settings.pickup_address or _PICKUP_ADDRESS_PLACEHOLDER,
    )


@router.get("/api/categories")
async def get_categories(session=Depends(get_session)) -> list[CategoryOut]:
    categories = await catalog.list_categories(session)
    return [CategoryOut(id=c.id, name=c.name) for c in categories]


@router.get("/api/products")
async def get_products(
    category_id: int | None = None, q: str | None = None, session=Depends(get_session)
) -> list[ProductOut]:
    products = await catalog.list_products(session, category_id=category_id, q=q)
    return [product_to_out(p) for p in products]


@router.get("/api/products/{product_id}")
async def get_product_detail(product_id: int, session=Depends(get_session)) -> ProductOut:
    product = await catalog.get_visible_product(session, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="not_found")
    return product_to_out(product)


@router.post("/api/uploads")
async def upload_custom_file(
    request: Request,
    file: UploadFile,
    user: TgUser = Depends(customer_user),
    session=Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> UploadOut:
    limiter = request.app.state.upload_limiter
    if not limiter.hit(user.id):
        raise HTTPException(status_code=429, detail="rate_limited")
    try:
        upload = await save_upload(file, "custom", user.id, session, settings)
    except UploadError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc
    return UploadOut(upload_id=upload.id, url=public_url(upload.filename))
