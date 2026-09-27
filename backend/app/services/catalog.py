"""Categories/products rules.

Owns soft-delete and filtering; exposes CRUD functions used by both the customer
and the admin catalog API.
"""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Category, Product, Upload


class CatalogError(Exception):
    """Raised for catalog rule violations. `code` is the machine error code."""

    def __init__(self, code: str, http_status: int) -> None:
        self.code = code
        self.http_status = http_status
        super().__init__(code)


async def list_categories(session: AsyncSession) -> list[Category]:
    """Non-deleted categories, in creation order."""
    stmt = select(Category).where(Category.is_deleted.is_(False)).order_by(Category.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_category(session: AsyncSession, name: str) -> Category:
    category = Category(name=name)
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def get_category(session: AsyncSession, category_id: int) -> Category | None:
    return await session.get(Category, category_id)


async def rename_category(session: AsyncSession, category_id: int, name: str) -> Category:
    category = await session.get(Category, category_id)
    if category is None or category.is_deleted:
        raise CatalogError("not_found", 404)
    category.name = name
    await session.commit()
    await session.refresh(category)
    return category


async def delete_category(session: AsyncSession, category_id: int) -> None:
    """Soft-delete a category. Refuses (409 category_not_empty) if it still has
    non-deleted products."""
    category = await session.get(Category, category_id)
    if category is None or category.is_deleted:
        raise CatalogError("not_found", 404)
    stmt = select(func.count()).select_from(Product).where(
        Product.category_id == category_id, Product.is_deleted.is_(False)
    )
    active_count = (await session.execute(stmt)).scalar_one()
    if active_count > 0:
        raise CatalogError("category_not_empty", 409)
    category.is_deleted = True
    await session.commit()


async def list_products(
    session: AsyncSession, category_id: int | None = None, q: str | None = None
) -> list[Product]:
    """Non-deleted products of non-deleted categories. Includes unavailable ones
    (flagged, not hidden). `q` matches name or sku, case-insensitive substring."""
    stmt = (
        select(Product)
        .join(Category, Product.category_id == Category.id)
        .where(Product.is_deleted.is_(False), Category.is_deleted.is_(False))
    )
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(func.lower(Product.name).like(pattern), func.lower(Product.sku).like(pattern))
        )
    stmt = stmt.order_by(Product.id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_product(session: AsyncSession, product_id: int) -> Product | None:
    """Raw fetch by id, ignoring soft-delete — for admin mutations."""
    return await session.get(Product, product_id)


async def get_visible_product(session: AsyncSession, product_id: int) -> Product | None:
    """Fetch for customer display: None if the product or its category is deleted."""
    product = await session.get(Product, product_id)
    if product is None or product.is_deleted:
        return None
    category = await session.get(Category, product.category_id)
    if category is None or category.is_deleted:
        return None
    return product


async def _resolve_upload_image(session: AsyncSession, upload_id: int) -> str:
    upload = await session.get(Upload, upload_id)
    if upload is None or upload.kind != "product":
        raise CatalogError("invalid_upload", 400)
    return upload.filename


async def create_product(
    session: AsyncSession,
    *,
    category_id: int,
    name: str,
    sku: str,
    price: int,
    description: str | None = None,
    upload_id: int | None = None,
    is_available: bool = True,
) -> Product:
    category = await session.get(Category, category_id)
    if category is None or category.is_deleted:
        raise CatalogError("not_found", 404)
    image_path = await _resolve_upload_image(session, upload_id) if upload_id is not None else None
    product = Product(
        category_id=category_id,
        name=name,
        sku=sku,
        price=price,
        description=description,
        image_path=image_path,
        is_available=is_available,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def update_product(session: AsyncSession, product_id: int, **fields: object) -> Product:
    """Partial update. Recognised keys: category_id, name, sku, price, description,
    is_available, upload_id (maps to image_path)."""
    product = await session.get(Product, product_id)
    if product is None or product.is_deleted:
        raise CatalogError("not_found", 404)

    if "upload_id" in fields:
        upload_id = fields.pop("upload_id")
        if upload_id is None:
            product.image_path = None
        else:
            product.image_path = await _resolve_upload_image(session, upload_id)

    for key, value in fields.items():
        setattr(product, key, value)

    await session.commit()
    await session.refresh(product)
    return product


async def delete_product(session: AsyncSession, product_id: int) -> None:
    product = await session.get(Product, product_id)
    if product is None or product.is_deleted:
        raise CatalogError("not_found", 404)
    product.is_deleted = True
    await session.commit()
