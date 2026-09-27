from conftest import sign_init_data

from app.models import Category, Product
from app.ratelimit import RateLimiter

CUSTOMER_TOKEN = "111111:TEST-customer"


def _auth(user_id: int = 1001, username: str = "ali") -> dict:
    raw = sign_init_data({"id": user_id, "first_name": "Ali", "username": username}, CUSTOMER_TOKEN)
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


async def test_create_order_returns_201_with_order_out(app, client):
    product_id = await _seed_product(app)
    body = {
        "customer_name": "Ali",
        "phone": "901234567",
        "delivery_type": "pickup",
        "items": [{"product_id": product_id, "quantity": 2}],
    }
    resp = await client.post("/api/orders", headers=_auth(), json=body)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "new"
    assert data["status_label"] == "Yangi"
    assert data["phone"] == "+998901234567"
    assert data["total"] == 20000
    assert data["items"][0]["quantity"] == 2


async def test_create_order_unavailable_product_is_400(app, client):
    async with app.state.session_factory() as session:
        cat = Category(name="Kat")
        session.add(cat)
        await session.flush()
        product = Product(category_id=cat.id, name="X", sku="X1", price=1, is_available=False)
        session.add(product)
        await session.commit()
        product_id = product.id
    body = {
        "customer_name": "Ali", "phone": "901234567", "delivery_type": "pickup",
        "items": [{"product_id": product_id, "quantity": 1}],
    }
    resp = await client.post("/api/orders", headers=_auth(), json=body)
    assert resp.status_code == 400
    assert resp.json() == {"detail": "product_unavailable"}


async def test_create_order_invalid_phone_is_422(client):
    body = {
        "customer_name": "Ali", "phone": "123", "delivery_type": "pickup",
        "items": [{"custom": {"name": "X"}, "quantity": 1}],
    }
    resp = await client.post("/api/orders", headers=_auth(), json=body)
    assert resp.status_code == 422


async def test_create_order_delivery_without_address_is_422(client):
    body = {
        "customer_name": "Ali", "phone": "901234567", "delivery_type": "delivery",
        "items": [{"custom": {"name": "X"}, "quantity": 1}],
    }
    resp = await client.post("/api/orders", headers=_auth(), json=body)
    assert resp.status_code == 422


async def test_create_order_over_rate_limit_is_429(app, client):
    app.state.order_limiter = RateLimiter(limit=1, window=600)
    product_id = await _seed_product(app)
    body = {
        "customer_name": "Ali", "phone": "901234567", "delivery_type": "pickup",
        "items": [{"product_id": product_id, "quantity": 1}],
    }
    headers = _auth(user_id=3003)
    r1 = await client.post("/api/orders", headers=headers, json=body)
    assert r1.status_code == 201
    r2 = await client.post("/api/orders", headers=headers, json=body)
    assert r2.status_code == 429
    assert r2.json() == {"detail": "rate_limited"}


async def test_create_order_notifies_fake_notifier(app, client, fake_notifier):
    product_id = await _seed_product(app)
    body = {
        "customer_name": "Ali", "phone": "901234567", "delivery_type": "pickup",
        "items": [{"product_id": product_id, "quantity": 1}],
    }
    resp = await client.post("/api/orders", headers=_auth(), json=body)
    assert resp.status_code == 201
    assert [e[0] for e in fake_notifier.events] == ["order_created"]


async def test_my_orders_only_shows_own_orders(app, client):
    product_id = await _seed_product(app)
    body = {
        "customer_name": "Ali", "phone": "901234567", "delivery_type": "pickup",
        "items": [{"product_id": product_id, "quantity": 1}],
    }
    await client.post("/api/orders", headers=_auth(user_id=1001), json=body)
    await client.post("/api/orders", headers=_auth(user_id=2002), json=body)

    resp = await client.get("/api/orders/my", headers=_auth(user_id=1001))
    assert resp.status_code == 200
    orders = resp.json()
    assert len(orders) == 1


async def test_orders_without_auth_header_is_401(client):
    resp = await client.get("/api/orders/my")
    assert resp.status_code == 401
