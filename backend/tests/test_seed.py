from sqlalchemy import select

from app.db import make_engine, make_session_factory
from app.models import Base, Category, Product
from app.seed import seed


async def _fresh(tmp_path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = make_session_factory(engine)
    return engine, session_factory


async def test_seed_creates_3_categories_and_10_products_with_svg_files(tmp_path):
    engine, session_factory = await _fresh(tmp_path)
    upload_dir = tmp_path / "uploads"

    await seed(session_factory, upload_dir)

    async with session_factory() as session:
        categories = (await session.execute(select(Category))).scalars().all()
        products = (await session.execute(select(Product))).scalars().all()
    assert len(categories) == 3
    assert len(products) == 10
    for product in products:
        assert product.image_path is not None
        image_file = upload_dir / product.image_path
        assert image_file.exists()
        assert image_file.suffix == ".svg"

    await engine.dispose()


async def test_seed_run_twice_still_3_categories_10_products(tmp_path):
    engine, session_factory = await _fresh(tmp_path)
    upload_dir = tmp_path / "uploads"

    await seed(session_factory, upload_dir)
    await seed(session_factory, upload_dir)

    async with session_factory() as session:
        categories = (await session.execute(select(Category))).scalars().all()
        products = (await session.execute(select(Product))).scalars().all()
    assert len(categories) == 3
    assert len(products) == 10

    await engine.dispose()
