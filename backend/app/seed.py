"""Idempotent demo data: 3 categories, 10 fictional products, local SVG placeholders.

Entry point: `python -m app.seed`.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from .config import get_settings
from .db import make_engine, make_session_factory
from .models import Base, Category, Product

CATEGORY_NAMES = ["Parfyumeriya", "Yuz uchun", "Soch uchun"]

# (category index into CATEGORY_NAMES, name, sku, price so'm, description)
PRODUCTS = [
    (0, "Bahor Nafasi Atiri", "PRF-001", 145000, "Yengil gulli atir, kunduzgi foydalanish uchun."),
    (0, "Kechki Sehr Atiri", "PRF-002", 189000, "Quyuq sharqona atir, kechki tadbirlar uchun."),
    (0, "Yosh Bahor Kolon Suvi", "PRF-003", 98000, "Yengil sitrusli kolon suvi."),
    (1, "Namlantiruvchi Krem", "FCE-001", 76000, "Yuz terisini kun bo'yi namlab turadi."),
    (1, "Tozalovchi Gel", "FCE-002", 54000, "Yuzni yumshoq tozalaydigan gel."),
    (1, "Ko'z Atrofi Seruma", "FCE-003", 112000, "Ko'z atrofi terisiga g'amxo'rlik qiladi."),
    (2, "Tiklovchi Shampun", "HR-001", 65000, "Sochni yumshoq va yaltiroq qiladi."),
    (2, "Ozuqaviy Balzam", "HR-002", 70000, "Sochga qo'shimcha ozuqa beradi."),
    (2, "Soch Uchun Tiklovchi Yog'", "HR-003", 88000, "Quruq sochlar uchun tiklovchi yog'."),
    (2, "Hajm Beruvchi Sprey", "HR-004", 59000, "Sochga hajm va yengillik beradi."),
]


def _svg_placeholder(label: str) -> bytes:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">'
        '<rect width="300" height="300" fill="#e5e5e5"/>'
        f'<text x="150" y="160" font-size="22" text-anchor="middle" fill="#555555">{label}</text>'
        "</svg>"
    )
    return svg.encode("utf-8")


def _ensure_placeholder(upload_dir: Path, sku: str) -> str:
    """Write (if missing) a local SVG placeholder for `sku`; return its path relative
    to `upload_dir`, suitable for storage in `Product.image_path`."""
    seed_dir = upload_dir / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{sku}.svg"
    path = seed_dir / filename
    if not path.exists():
        path.write_bytes(_svg_placeholder(sku))
    return f"seed/{filename}"


async def seed(session_factory: async_sessionmaker, upload_dir: Path) -> None:
    """Insert the 3 categories and 10 products if missing, generate their SVG
    placeholders. Safe to call repeatedly — matches by name/sku."""
    async with session_factory() as session:
        existing_categories = (await session.execute(select(Category))).scalars().all()
        by_name = {c.name: c for c in existing_categories}
        categories = []
        for name in CATEGORY_NAMES:
            category = by_name.get(name)
            if category is None:
                category = Category(name=name)
                session.add(category)
                await session.flush()
            categories.append(category)

        existing_skus = {p.sku for p in (await session.execute(select(Product))).scalars().all()}
        for category_index, name, sku, price, description in PRODUCTS:
            if sku in existing_skus:
                continue
            image_path = _ensure_placeholder(upload_dir, sku)
            session.add(
                Product(
                    category_id=categories[category_index].id,
                    name=name,
                    sku=sku,
                    price=price,
                    description=description,
                    image_path=image_path,
                )
            )

        await session.commit()


async def main() -> None:
    settings = get_settings()
    engine = make_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = make_session_factory(engine)
    await seed(session_factory, Path(settings.upload_dir))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
