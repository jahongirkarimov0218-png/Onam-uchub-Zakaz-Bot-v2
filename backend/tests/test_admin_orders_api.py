from conftest import sign_init_data

from app.models import Category, Product

CUSTOMER_TOKEN = "111111:TEST-customer"
ADMIN_TOKEN = "222222:TEST-admin"


def _customer_auth(user_id: int = 1001) -> dict:
    raw = sign_init_data({"id": user_id, "first_name": "Ali"}, CUSTOMER_TOKEN)
    return {"Authorization": f"tma {raw}"}


def _admin_auth(user_id: int = 555) -> dict:
    raw = sign_init_data({"id": user_id, "first_name": "Onam"}, ADMIN_TOKEN)
    return {"Authorization": f"tma {raw}"}


async def _seed_product(app, *, price: int = 10000) -> int:
    async with app.state.session_factory() as session:
        cat = Category(name="Kat")
        session.add(cat)
        await session.flush()
        product = Product(category_id=cat.id, name="Sovun", sku="S-1", price=price)
        session.add(product)
        await session.commit()
        return product.id


async def _create_order(client, app, *, customer_name: str = "Ali", phone: str = "901234567") -> int:
    product_id = await _seed_product(app)
    body = {
        "customer_name": customer_name, "phone": phone, "delivery_type": "pickup",
        "items": [{"product_id": product_id, "quantity": 1}],
    }
    resp = await client.post("/api/orders", headers=_customer_auth(), json=body)
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_list_orders_requires_admin(client):
    resp = await client.get("/api/admin/orders")
    assert resp.status_code == 401


async def test_customer_init_data_rejected_by_admin_api(app, client):
    resp = await client.get("/api/admin/orders", headers=_customer_auth())
    assert resp.status_code == 401


async def test_non_admin_user_forbidden(client):
    raw = sign_init_data({"id": 999999, "first_name": "Stranger"}, ADMIN_TOKEN)
    resp = await client.get("/api/admin/orders", headers={"Authorization": f"tma {raw}"})
    assert resp.status_code == 403


async def test_list_orders_limit_zero_is_422(client):
    resp = await client.get("/api/admin/orders", params={"limit": 0}, headers=_admin_auth())
    assert resp.status_code == 422


async def test_list_orders_limit_over_200_is_422(client):
    resp = await client.get("/api/admin/orders", params={"limit": 201}, headers=_admin_auth())
    assert resp.status_code == 422


async def test_list_orders_limit_200_is_accepted(client):
    resp = await client.get("/api/admin/orders", params={"limit": 200}, headers=_admin_auth())
    assert resp.status_code == 200


async def test_list_orders_filters_by_status_and_search(app, client):
    order_id = await _create_order(client, app, customer_name="Vali", phone="901112233")
    await _create_order(client, app, customer_name="Salima", phone="907778899")

    resp = await client.get("/api/admin/orders", params={"status": "new"}, headers=_admin_auth())
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    resp = await client.get("/api/admin/orders", params={"q": "vali"}, headers=_admin_auth())
    assert resp.status_code == 200
    assert [o["id"] for o in resp.json()] == [order_id]


async def test_order_detail_includes_history(app, client):
    order_id = await _create_order(client, app)
    resp = await client.get(f"/api/admin/orders/{order_id}", headers=_admin_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["history"]) == 1
    assert body["history"][0]["to_status"] == "new"


async def test_order_detail_404_when_missing(client):
    resp = await client.get("/api/admin/orders/999", headers=_admin_auth())
    assert resp.status_code == 404


async def test_set_status_valid_transition_notifies_and_writes_history(app, client, fake_notifier):
    order_id = await _create_order(client, app)
    resp = await client.post(
        f"/api/admin/orders/{order_id}/status", headers=_admin_auth(), json={"status": "accepted"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"
    assert "status_changed" in [e[0] for e in fake_notifier.events]


async def test_set_status_invalid_transition_is_409(app, client):
    order_id = await _create_order(client, app)
    resp = await client.post(
        f"/api/admin/orders/{order_id}/status", headers=_admin_auth(), json={"status": "delivered"}
    )
    assert resp.status_code == 409
    assert resp.json() == {"detail": "invalid_transition"}


async def test_stats_returns_counts(app, client):
    await _create_order(client, app)
    resp = await client.get("/api/admin/stats", headers=_admin_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert body["by_status"]["new"] == 1
    assert body["today"] == 1
    assert "delivered_month_sum" in body
