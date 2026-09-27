import datetime as dt
import zoneinfo

import pytest
from sqlalchemy import select

from app.auth import TgUser
from app.models import Category, Order, OrderStatusHistory, Product, Upload
from app.schemas.orders import OrderCreate
from app.services import orders as svc

TZ = zoneinfo.ZoneInfo("Asia/Tashkent")


def _user(user_id: int = 1001, username: str | None = "ali") -> TgUser:
    return TgUser(id=user_id, first_name="Ali", username=username)


async def _seed_product(app, *, price: int = 10000, available: bool = True, deleted: bool = False) -> int:
    async with app.state.session_factory() as session:
        cat = Category(name="Kat")
        session.add(cat)
        await session.flush()
        product = Product(
            category_id=cat.id, name="Sovun", sku="S-1", price=price,
            is_available=available, is_deleted=deleted,
        )
        session.add(product)
        await session.commit()
        return product.id


async def _seed_upload(app, *, kind: str = "custom", uploaded_by: int = 1001) -> int:
    async with app.state.session_factory() as session:
        upload = Upload(filename="x.png", kind=kind, uploaded_by=uploaded_by, size=10)
        session.add(upload)
        await session.commit()
        return upload.id


# --- status machine ---------------------------------------------------------

def test_allowed_transitions_follow_next_map():
    assert svc.allowed("new", "accepted") is True
    assert svc.allowed("accepted", "ordered") is True
    assert svc.allowed("ordered", "arrived") is True
    assert svc.allowed("arrived", "delivered") is True


def test_allowed_rejects_skipping_a_step():
    assert svc.allowed("new", "ordered") is False


def test_allowed_permits_cancel_from_any_non_final_state():
    for status in ("new", "accepted", "ordered", "arrived"):
        assert svc.allowed(status, "cancelled") is True


def test_allowed_rejects_transition_out_of_final_states():
    assert svc.allowed("delivered", "cancelled") is False
    assert svc.allowed("cancelled", "new") is False


# --- create_order ------------------------------------------------------------

async def test_create_order_totals_catalog_lines_and_nulls_custom_price(app):
    product_id = await _seed_product(app, price=15000)
    async with app.state.session_factory() as session:
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[
                {"product_id": product_id, "quantity": 2},
                {"custom": {"name": "Noma'lum sovun"}, "quantity": 1},
            ],
        )
        order = await svc.create_order(session, _user(), data)
        assert order.total == 30000
        assert order.status == "new"
        catalog_line, custom_line = order.items
        assert catalog_line.kind == "catalog" and catalog_line.unit_price == 15000
        assert custom_line.kind == "custom" and custom_line.unit_price is None


async def test_create_order_ignores_client_supplied_price_uses_db_price(app):
    # OrderCreate has no client price field at all -- price always comes from DB.
    product_id = await _seed_product(app, price=5000)
    async with app.state.session_factory() as session:
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 3}],
        )
        order = await svc.create_order(session, _user(), data)
        assert order.total == 15000


async def test_create_order_rejects_unavailable_product(app):
    product_id = await _seed_product(app, available=False)
    async with app.state.session_factory() as session:
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        with pytest.raises(svc.OrderError) as exc_info:
            await svc.create_order(session, _user(), data)
        assert exc_info.value.code == "product_unavailable"
        assert exc_info.value.http_status == 400


async def test_create_order_rejects_deleted_product(app):
    product_id = await _seed_product(app, deleted=True)
    async with app.state.session_factory() as session:
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        with pytest.raises(svc.OrderError) as exc_info:
            await svc.create_order(session, _user(), data)
        assert exc_info.value.code == "product_unavailable"


async def test_create_order_rejects_foreign_users_upload(app):
    upload_id = await _seed_upload(app, kind="custom", uploaded_by=9999)
    async with app.state.session_factory() as session:
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"custom": {"upload_id": upload_id}, "quantity": 1}],
        )
        with pytest.raises(svc.OrderError) as exc_info:
            await svc.create_order(session, _user(user_id=1001), data)
        assert exc_info.value.code == "invalid_upload"
        assert exc_info.value.http_status == 400


async def test_create_order_rejects_product_kind_upload_in_custom_line(app):
    upload_id = await _seed_upload(app, kind="product", uploaded_by=1001)
    async with app.state.session_factory() as session:
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"custom": {"upload_id": upload_id}, "quantity": 1}],
        )
        with pytest.raises(svc.OrderError) as exc_info:
            await svc.create_order(session, _user(user_id=1001), data)
        assert exc_info.value.code == "invalid_upload"


async def test_create_order_writes_initial_history_row(app):
    product_id = await _seed_product(app)
    async with app.state.session_factory() as session:
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        order = await svc.create_order(session, _user(), data)
        loaded = await svc.load_order(session, order.id)
        assert len(loaded.history) == 1
        row = loaded.history[0]
        assert row.from_status is None
        assert row.to_status == "new"
        assert row.source == "customer"


async def test_create_order_notifier_failure_does_not_break_creation(app):
    product_id = await _seed_product(app)

    class BoomNotifier:
        async def order_created(self, order):
            raise RuntimeError("telegram is down")

        async def status_changed(self, order):
            raise RuntimeError("boom")

        async def reminder(self, orders):
            pass

        async def daily_report(self, orders):
            pass

    async with app.state.session_factory() as session:
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        order = await svc.create_order(session, _user(), data, notifier=BoomNotifier())
        assert order.id is not None


async def test_create_order_calls_notifier_order_created(app, fake_notifier):
    product_id = await _seed_product(app)
    async with app.state.session_factory() as session:
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        order = await svc.create_order(session, _user(), data, notifier=fake_notifier)
    assert [e[0] for e in fake_notifier.events] == ["order_created"]
    assert fake_notifier.events[0][1].id == order.id


# --- change_status ------------------------------------------------------------

async def _new_order(app, session) -> Order:
    product_id = await _seed_product(app)
    data = OrderCreate(
        customer_name="Ali", phone="901234567", delivery_type="pickup",
        items=[{"product_id": product_id, "quantity": 1}],
    )
    return await svc.create_order(session, _user(), data)


async def test_change_status_walks_full_happy_path(app):
    async with app.state.session_factory() as session:
        order = await _new_order(app, session)
        order_id = order.id
    for to in ("accepted", "ordered", "arrived", "delivered"):
        async with app.state.session_factory() as session:
            order = await svc.change_status(session, order_id, to, actor_id=555, source="admin_app")
            assert order.status == to


async def test_change_status_forbidden_transition_raises_409(app):
    async with app.state.session_factory() as session:
        order = await _new_order(app, session)
        order_id = order.id
    async with app.state.session_factory() as session:
        with pytest.raises(svc.InvalidTransition) as exc_info:
            await svc.change_status(session, order_id, "delivered", actor_id=555, source="admin_app")
        assert exc_info.value.http_status == 409
        assert exc_info.value.code == "invalid_transition"


async def test_change_status_detects_concurrent_update_via_conditional_write(app):
    # Two admins both read the order while it is still "new". Admin A's change lands
    # first (status -> accepted, committed). Admin B's session still has a stale
    # in-memory copy at "new" (expire_on_commit=False) and must not blindly overwrite
    # admin A's write or write a second, contradictory history row -- the conditional
    # UPDATE (WHERE id=... AND status=<status admin B read>) must affect 0 rows and
    # change_status must turn that into InvalidTransition rather than succeeding.
    async with app.state.session_factory() as session:
        order = await _new_order(app, session)
        order_id = order.id

    async with app.state.session_factory() as session_a, app.state.session_factory() as session_b:
        # Admin B reads the order first (stale cache from here on, expire_on_commit=False).
        order_b = await session_b.get(Order, order_id)
        assert order_b.status == "new"

        # Admin A reads and applies its transition through the real service, and commits.
        order_a = await svc.change_status(session_a, order_id, "accepted", actor_id=1, source="admin_app")
        assert order_a.status == "accepted"

        # Admin B, still holding the pre-A snapshot, tries the same transition.
        with pytest.raises(svc.InvalidTransition):
            await svc.change_status(session_b, order_id, "accepted", actor_id=2, source="admin_app")

    async with app.state.session_factory() as session:
        loaded = await svc.load_order(session, order_id)
        assert loaded.status == "accepted"
        # only admin A's transition was recorded -- no duplicate history row from B.
        assert [h.to_status for h in loaded.history] == ["new", "accepted"]


async def test_change_status_writes_history_with_actor_and_source(app):
    async with app.state.session_factory() as session:
        order = await _new_order(app, session)
        order_id = order.id
    async with app.state.session_factory() as session:
        await svc.change_status(session, order_id, "accepted", actor_id=777, source="bot")
        loaded = await svc.load_order(session, order_id)
        assert len(loaded.history) == 2
        last = loaded.history[-1]
        assert last.from_status == "new"
        assert last.to_status == "accepted"
        assert last.actor_tg_id == 777
        assert last.source == "bot"


async def test_change_status_notifier_failure_does_not_break_status_change(app):
    class BoomNotifier:
        async def order_created(self, order):
            pass

        async def status_changed(self, order):
            raise RuntimeError("boom")

        async def reminder(self, orders):
            pass

        async def daily_report(self, orders):
            pass

    async with app.state.session_factory() as session:
        order = await _new_order(app, session)
        order_id = order.id
    async with app.state.session_factory() as session:
        order = await svc.change_status(
            session, order_id, "accepted", actor_id=1, source="admin_app", notifier=BoomNotifier()
        )
        assert order.status == "accepted"


async def test_change_status_calls_notifier_status_changed(app, fake_notifier):
    async with app.state.session_factory() as session:
        order = await _new_order(app, session)
        order_id = order.id
    async with app.state.session_factory() as session:
        await svc.change_status(
            session, order_id, "accepted", actor_id=1, source="admin_app", notifier=fake_notifier
        )
    assert [e[0] for e in fake_notifier.events] == ["status_changed"]


# --- search / list / open / stats -------------------------------------------

async def test_search_orders_by_id_phone_and_name(app):
    async with app.state.session_factory() as session:
        product_id = await _seed_product(app)
        data1 = OrderCreate(
            customer_name="Vali", phone="901112233", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        data2 = OrderCreate(
            customer_name="Salima", phone="907778899", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        order1 = await svc.create_order(session, _user(user_id=1), data1)
        order2 = await svc.create_order(session, _user(user_id=2), data2)

        by_id = await svc.search_orders(session, str(order1.id))
        assert [o.id for o in by_id] == [order1.id]

        by_phone = await svc.search_orders(session, "907778899")
        assert [o.id for o in by_phone] == [order2.id]

        by_name = await svc.search_orders(session, "vali")
        assert [o.id for o in by_name] == [order1.id]


async def test_list_orders_filters_by_tg_user_id(app):
    async with app.state.session_factory() as session:
        product_id = await _seed_product(app)
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        mine = await svc.create_order(session, _user(user_id=1001), data)
        await svc.create_order(session, _user(user_id=2002), data)

        mine_orders = await svc.list_orders(session, tg_user_id=1001)
        assert [o.id for o in mine_orders] == [mine.id]


async def test_list_orders_filters_by_status_and_newest_first(app):
    async with app.state.session_factory() as session:
        product_id = await _seed_product(app)
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        first = await svc.create_order(session, _user(), data)
        second = await svc.create_order(session, _user(), data)
        await svc.change_status(session, first.id, "accepted", actor_id=1, source="admin_app")

        new_only = await svc.list_orders(session, status="new")
        assert [o.id for o in new_only] == [second.id]

        newest_first = await svc.list_orders(session)
        assert [o.id for o in newest_first] == [second.id, first.id]


async def test_open_orders_excludes_final_states(app):
    async with app.state.session_factory() as session:
        product_id = await _seed_product(app)
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        open_order = await svc.create_order(session, _user(), data)
        cancelled = await svc.create_order(session, _user(), data)
        await svc.change_status(session, cancelled.id, "cancelled", actor_id=1, source="admin_app")

        open_ids = [o.id for o in await svc.open_orders(session)]
        assert open_ids == [open_order.id]


async def test_stats_counts_by_status_today_and_delivered_month_sum(app):
    fixed_now = dt.datetime(2026, 9, 27, 10, 0, tzinfo=dt.timezone.utc)
    async with app.state.session_factory() as session:
        product_id = await _seed_product(app, price=20000)
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        new_order = await svc.create_order(session, _user(), data)
        delivered = await svc.create_order(session, _user(), data)
        for to in ("accepted", "ordered", "arrived", "delivered"):
            await svc.change_status(session, delivered.id, to, actor_id=1, source="admin_app")

        result = await svc.stats(session, fixed_now, TZ)
        assert result["by_status"]["new"] == 1
        assert result["by_status"]["delivered"] == 1
        assert result["today"] == 2
        assert result["delivered_month_sum"] == 20000


async def test_stats_delivered_month_sum_uses_delivered_history_time_not_updated_at(app):
    # The order's `updated_at` is "now" (real wall-clock, set by every status-change
    # commit) -- but the ->delivered history row is backdated into the previous
    # local month. delivered_month_sum must follow the history row, so a later,
    # unrelated write to an already-delivered order (which would only bump
    # updated_at) can never move it into a different month's total.
    fixed_now = dt.datetime(2026, 9, 27, 10, 0, tzinfo=dt.timezone.utc)
    async with app.state.session_factory() as session:
        product_id = await _seed_product(app, price=20000)
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        order = await svc.create_order(session, _user(), data)
        for to in ("accepted", "ordered", "arrived", "delivered"):
            await svc.change_status(session, order.id, to, actor_id=1, source="admin_app")

        history_stmt = select(OrderStatusHistory).where(
            OrderStatusHistory.order_id == order.id, OrderStatusHistory.to_status == "delivered"
        )
        delivered_row = (await session.execute(history_stmt)).scalar_one()
        delivered_row.created_at = dt.datetime(2026, 8, 15, 10, 0)  # previous local month, naive UTC
        await session.commit()

        result = await svc.stats(session, fixed_now, TZ)
        assert result["delivered_month_sum"] == 0


async def test_stats_today_counts_order_by_local_tashkent_day_not_utc_day(app):
    # 19:30 UTC on Sep 27 is 00:30 on Sep 28 in Asia/Tashkent (UTC+5): already "today"
    # relative to a `now` that is also Sep 28 in Tashkent, even though the UTC
    # calendar date differs from `now`'s UTC calendar date.
    fixed_now = dt.datetime(2026, 9, 28, 10, 0, tzinfo=dt.timezone.utc)  # 15:00 Tashkent, Sep 28
    async with app.state.session_factory() as session:
        product_id = await _seed_product(app)
        data = OrderCreate(
            customer_name="Ali", phone="901234567", delivery_type="pickup",
            items=[{"product_id": product_id, "quantity": 1}],
        )
        just_after_midnight = await svc.create_order(session, _user(), data)
        just_after_midnight.created_at = dt.datetime(2026, 9, 27, 19, 30)
        still_previous_day = await svc.create_order(session, _user(), data)
        still_previous_day.created_at = dt.datetime(2026, 9, 27, 18, 0)  # 23:00 Tashkent, Sep 27
        await session.commit()

        result = await svc.stats(session, fixed_now, TZ)
        assert result["today"] == 1
