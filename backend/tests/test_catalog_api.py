from conftest import sign_init_data

from app.models import Category, Product
from app.ratelimit import RateLimiter

CUSTOMER_TOKEN = "111111:TEST-customer"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 20


def _auth(token: str, user_id: int = 1001) -> dict:
    raw = sign_init_data({"id": user_id, "first_name": "Ali"}, token)
    return {"Authorization": f"tma {raw}"}


async def _seed(app, *, categories: list[Category], products: list[Product]) -> None:
    async with app.state.session_factory() as session:
        session.add_all(categories)
        await session.flush()
        for product in products:
            product.category_id = product.category_id or categories[0].id
        session.add_all(products)
        await session.commit()


async def test_config_falls_back_to_placeholder_when_pickup_address_empty(app, client, settings):
    settings.pickup_address = ""
    resp = await client.get("/api/config", headers=_auth(CUSTOMER_TOKEN))
    body = resp.json()
    assert resp.status_code == 200
    assert body["shop_name"] == settings.shop_name
    assert "PICKUP_ADDRESS" in body["pickup_address"]


async def test_categories_excludes_deleted(app, client):
    await _seed(
        app,
        categories=[
            Category(name="Parfyumeriya", is_deleted=False),
            Category(name="O'chirilgan", is_deleted=True),
        ],
        products=[],
    )
    resp = await client.get("/api/categories", headers=_auth(CUSTOMER_TOKEN))
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert names == ["Parfyumeriya"]


async def test_products_search_by_name_and_sku_case_insensitive(app, client):
    cat = Category(name="Parfyumeriya")
    await _seed(
        app,
        categories=[cat],
        products=[
            Product(category_id=None, name="Atir Lavanda", sku="ABC-1", price=10000),
            Product(category_id=None, name="Sovun", sku="LAV-2", price=5000),
            Product(category_id=None, name="Shampun", sku="XYZ-3", price=7000),
        ],
    )
    resp = await client.get("/api/products", params={"q": "lav"}, headers=_auth(CUSTOMER_TOKEN))
    assert resp.status_code == 200
    names = sorted(p["name"] for p in resp.json())
    assert names == ["Atir Lavanda", "Sovun"]


async def test_products_filters_by_category_and_excludes_deleted(app, client):
    cat1 = Category(name="Kat1")
    cat2 = Category(name="Kat2")
    await _seed(
        app,
        categories=[cat1, cat2],
        products=[
            Product(category_id=None, name="A", sku="A1", price=1000),
            Product(category_id=None, name="B", sku="B1", price=1000, is_deleted=True),
        ],
    )
    async with app.state.session_factory() as session:
        p_in_cat2 = Product(category_id=cat2.id, name="C", sku="C1", price=2000)
        session.add(p_in_cat2)
        await session.commit()

    resp = await client.get("/api/products", params={"category_id": cat1.id}, headers=_auth(CUSTOMER_TOKEN))
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert names == ["A"]


async def test_products_excludes_products_of_deleted_category(app, client):
    cat = Category(name="Ghost", is_deleted=True)
    await _seed(app, categories=[cat], products=[Product(category_id=None, name="Gone", sku="G1", price=1)])
    resp = await client.get("/api/products", headers=_auth(CUSTOMER_TOKEN))
    assert resp.status_code == 200
    assert resp.json() == []


async def test_products_includes_unavailable_with_flag(app, client):
    cat = Category(name="Kat")
    await _seed(
        app,
        categories=[cat],
        products=[Product(category_id=None, name="Off", sku="O1", price=1000, is_available=False)],
    )
    resp = await client.get("/api/products", headers=_auth(CUSTOMER_TOKEN))
    body = resp.json()
    assert len(body) == 1
    assert body[0]["is_available"] is False


async def test_product_detail_404_when_missing(client):
    resp = await client.get("/api/products/999", headers=_auth(CUSTOMER_TOKEN))
    assert resp.status_code == 404
    assert resp.json() == {"detail": "not_found"}


async def test_product_detail_200(app, client):
    cat = Category(name="Kat")
    await _seed(app, categories=[cat], products=[Product(category_id=None, name="X", sku="X1", price=500)])
    async with app.state.session_factory() as session:
        from sqlalchemy import select

        product = (await session.execute(select(Product))).scalars().first()
        product_id = product.id
    resp = await client.get(f"/api/products/{product_id}", headers=_auth(CUSTOMER_TOKEN))
    assert resp.status_code == 200
    assert resp.json()["name"] == "X"


async def test_upload_rejects_unsupported_type(client):
    files = {"file": ("a.txt", b"hello world", "text/plain")}
    resp = await client.post("/api/uploads", headers=_auth(CUSTOMER_TOKEN), files=files)
    assert resp.status_code == 415
    assert resp.json() == {"detail": "unsupported_file_type"}


async def test_upload_success_returns_url(client):
    files = {"file": ("a.png", PNG_BYTES, "image/png")}
    resp = await client.post("/api/uploads", headers=_auth(CUSTOMER_TOKEN), files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["url"].startswith("/uploads/")
    assert body["url"].endswith(".png")


async def test_upload_over_limit_in_window_is_429(app, client):
    app.state.upload_limiter = RateLimiter(limit=1, window=600)
    files = {"file": ("a.png", PNG_BYTES, "image/png")}
    headers = _auth(CUSTOMER_TOKEN, user_id=2002)
    r1 = await client.post("/api/uploads", headers=headers, files=files)
    assert r1.status_code == 200
    r2 = await client.post("/api/uploads", headers=headers, files=files)
    assert r2.status_code == 429
    assert r2.json() == {"detail": "rate_limited"}


async def test_config_without_auth_header_is_401(client):
    resp = await client.get("/api/config")
    assert resp.status_code == 401
    assert resp.json() == {"detail": "invalid_init_data"}


async def test_categories_without_auth_header_is_401(client):
    resp = await client.get("/api/categories")
    assert resp.status_code == 401
    assert resp.json() == {"detail": "invalid_init_data"}


async def test_products_without_auth_header_is_401(client):
    resp = await client.get("/api/products")
    assert resp.status_code == 401
    assert resp.json() == {"detail": "invalid_init_data"}


async def test_product_detail_without_auth_header_is_401(client):
    resp = await client.get("/api/products/1")
    assert resp.status_code == 401
    assert resp.json() == {"detail": "invalid_init_data"}
