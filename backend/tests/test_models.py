from sqlalchemy import inspect

from app.db import make_engine, make_session_factory
from app.models import Base


async def test_create_all_creates_all_seven_tables(tmp_path):
    db_path = tmp_path / "models.db"
    engine = make_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    def get_table_names(sync_conn):
        return set(inspect(sync_conn).get_table_names())

    async with engine.connect() as conn:
        tables = await conn.run_sync(get_table_names)

    await engine.dispose()

    assert tables == {
        "categories",
        "products",
        "uploads",
        "orders",
        "order_items",
        "order_status_history",
        "order_admin_messages",
    }


async def test_make_session_factory_returns_working_session(tmp_path):
    db_path = tmp_path / "models2.db"
    engine = make_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = make_session_factory(engine)
    async with session_factory() as session:
        from app.models import Category

        session.add(Category(name="Parfyumeriya"))
        await session.commit()
        result = await session.execute(Category.__table__.select())
        rows = result.fetchall()
        assert len(rows) == 1
    await engine.dispose()
