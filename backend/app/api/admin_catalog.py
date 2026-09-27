"""Admin catalog endpoints: categories and products CRUD, product image uploads."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile

from ..auth import TgUser, admin_user
from ..config import Settings, get_settings
from ..db import get_session
from ..schemas.catalog import CategoryIn, CategoryOut, ProductIn, ProductPatch, UploadOut
from ..services import catalog
from ..services.catalog import CatalogError
from ..uploads import UploadError, public_url, save_upload
from .catalog import product_to_out

router = APIRouter(prefix="/api/admin", dependencies=[Depends(admin_user)])


@router.get("/categories")
async def list_categories(session=Depends(get_session)) -> list[CategoryOut]:
    categories = await catalog.list_categories(session)
    return [CategoryOut(id=c.id, name=c.name) for c in categories]


@router.post("/categories", status_code=201)
async def create_category(body: CategoryIn, session=Depends(get_session)) -> CategoryOut:
    category = await catalog.create_category(session, body.name)
    return CategoryOut(id=category.id, name=category.name)


@router.patch("/categories/{category_id}")
async def rename_category(category_id: int, body: CategoryIn, session=Depends(get_session)) -> CategoryOut:
    try:
        category = await catalog.rename_category(session, category_id, body.name)
    except CatalogError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc
    return CategoryOut(id=category.id, name=category.name)


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(category_id: int, session=Depends(get_session)) -> Response:
    try:
        await catalog.delete_category(session, category_id)
    except CatalogError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc
    return Response(status_code=204)


@router.get("/products")
async def list_products(
    category_id: int | None = None, q: str | None = None, session=Depends(get_session)
) -> list:
    products = await catalog.list_products(session, category_id=category_id, q=q)
    return [product_to_out(p) for p in products]


@router.post("/products", status_code=201)
async def create_product(body: ProductIn, session=Depends(get_session)):
    try:
        product = await catalog.create_product(session, **body.model_dump())
    except CatalogError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc
    return product_to_out(product)


@router.patch("/products/{product_id}")
async def update_product(product_id: int, body: ProductPatch, session=Depends(get_session)):
    fields = body.model_dump(exclude_unset=True)
    try:
        product = await catalog.update_product(session, product_id, **fields)
    except CatalogError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc
    return product_to_out(product)


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(product_id: int, session=Depends(get_session)) -> Response:
    try:
        await catalog.delete_product(session, product_id)
    except CatalogError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc
    return Response(status_code=204)


@router.post("/uploads")
async def upload_product_file(
    request: Request,
    file: UploadFile,
    user: TgUser = Depends(admin_user),
    session=Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> UploadOut:
    limiter = request.app.state.upload_limiter
    if not limiter.hit(user.id):
        raise HTTPException(status_code=429, detail="rate_limited")
    try:
        upload = await save_upload(file, "product", user.id, session, settings)
    except UploadError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.code) from exc
    return UploadOut(upload_id=upload.id, url=public_url(upload.filename))
