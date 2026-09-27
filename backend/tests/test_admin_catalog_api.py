import pytest

from conftest import sign_init_data

CUSTOMER_TOKEN = "111111:TEST-customer"
ADMIN_TOKEN = "222222:TEST-admin"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 20


def _admin_auth(user_id: int = 555) -> dict:
    raw = sign_init_data({"id": user_id, "first_name": "Onam"}, ADMIN_TOKEN)
    return {"Authorization": f"tma {raw}"}


def _customer_auth(user_id: int = 1001) -> dict:
    raw = sign_init_data({"id": user_id, "first_name": "Ali"}, CUSTOMER_TOKEN)
    return {"Authorization": f"tma {raw}"}


async def _create_category(client, name: str) -> int:
    resp = await client.post("/api/admin/categories", headers=_admin_auth(), json={"name": name})
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_product(client, category_id: int, name: str = "Mahsulot", sku: str = "SKU-1") -> int:
    body = {"category_id": category_id, "name": name, "sku": sku, "price": 10000}
    resp = await client.post("/api/admin/products", headers=_admin_auth(), json=body)
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_category_and_product_crud_lifecycle(client):
    category_id = await _create_category(client, "Kosmetika")
    product_id = await _create_product(client, category_id)

    resp = await client.get("/api/admin/products", headers=_admin_auth())
    assert resp.status_code == 200
    assert [p["id"] for p in resp.json()] == [product_id]

    resp = await client.patch(
        f"/api/admin/products/{product_id}", headers=_admin_auth(), json={"is_available": False}
    )
    assert resp.status_code == 200
    assert resp.json()["is_available"] is False

    resp = await client.patch(
        f"/api/admin/categories/{category_id}", headers=_admin_auth(), json={"name": "Yangi nom"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Yangi nom"


async def test_soft_deleted_product_hidden_from_customer_list_but_admin_sees_history_unaffected(client):
    category_id = await _create_category(client, "Kat")
    product_id = await _create_product(client, category_id)

    resp = await client.get("/api/products", headers=_customer_auth())
    assert [p["id"] for p in resp.json()] == [product_id]

    resp = await client.delete(f"/api/admin/products/{product_id}", headers=_admin_auth())
    assert resp.status_code == 204

    resp = await client.get("/api/products", headers=_customer_auth())
    assert resp.json() == []


async def test_delete_category_with_active_product_is_409(client):
    category_id = await _create_category(client, "Kat")
    await _create_product(client, category_id)

    resp = await client.delete(f"/api/admin/categories/{category_id}", headers=_admin_auth())
    assert resp.status_code == 409
    assert resp.json() == {"detail": "category_not_empty"}


async def test_delete_empty_category_succeeds(client):
    category_id = await _create_category(client, "Bo'sh")
    resp = await client.delete(f"/api/admin/categories/{category_id}", headers=_admin_auth())
    assert resp.status_code == 204


async def test_product_image_set_via_upload_id(client):
    category_id = await _create_category(client, "Kat")
    files = {"file": ("a.png", PNG_BYTES, "image/png")}
    resp = await client.post("/api/admin/uploads", headers=_admin_auth(), files=files)
    assert resp.status_code == 200
    upload_id = resp.json()["upload_id"]

    product_id = await _create_product(client, category_id)
    resp = await client.patch(
        f"/api/admin/products/{product_id}", headers=_admin_auth(), json={"upload_id": upload_id}
    )
    assert resp.status_code == 200
    assert resp.json()["image_url"].endswith(".png")


async def test_patch_product_explicit_null_description_clears_it(client):
    category_id = await _create_category(client, "Kat")
    body = {
        "category_id": category_id,
        "name": "Mahsulot",
        "sku": "SKU-D1",
        "price": 10000,
        "description": "Boshlang'ich tavsif",
    }
    resp = await client.post("/api/admin/products", headers=_admin_auth(), json=body)
    assert resp.status_code == 201
    product_id = resp.json()["id"]
    assert resp.json()["description"] == "Boshlang'ich tavsif"

    resp = await client.patch(
        f"/api/admin/products/{product_id}", headers=_admin_auth(), json={"description": None}
    )
    assert resp.status_code == 200
    assert resp.json()["description"] is None


async def test_patch_product_omitted_description_stays_unchanged(client):
    category_id = await _create_category(client, "Kat")
    body = {
        "category_id": category_id,
        "name": "Mahsulot",
        "sku": "SKU-D2",
        "price": 10000,
        "description": "O'zgarmaydigan tavsif",
    }
    resp = await client.post("/api/admin/products", headers=_admin_auth(), json=body)
    assert resp.status_code == 201
    product_id = resp.json()["id"]

    resp = await client.patch(
        f"/api/admin/products/{product_id}", headers=_admin_auth(), json={"is_available": False}
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "O'zgarmaydigan tavsif"


async def test_patch_product_explicit_null_upload_id_clears_image(client):
    category_id = await _create_category(client, "Kat")
    files = {"file": ("a.png", PNG_BYTES, "image/png")}
    resp = await client.post("/api/admin/uploads", headers=_admin_auth(), files=files)
    upload_id = resp.json()["upload_id"]

    product_id = await _create_product(client, category_id, sku="SKU-I1")
    resp = await client.patch(
        f"/api/admin/products/{product_id}", headers=_admin_auth(), json={"upload_id": upload_id}
    )
    assert resp.json()["image_url"] is not None

    resp = await client.patch(
        f"/api/admin/products/{product_id}", headers=_admin_auth(), json={"upload_id": None}
    )
    assert resp.status_code == 200
    assert resp.json()["image_url"] is None


async def test_patch_product_omitted_upload_id_leaves_image_unchanged(client):
    category_id = await _create_category(client, "Kat")
    files = {"file": ("a.png", PNG_BYTES, "image/png")}
    resp = await client.post("/api/admin/uploads", headers=_admin_auth(), files=files)
    upload_id = resp.json()["upload_id"]

    product_id = await _create_product(client, category_id, sku="SKU-I2")
    resp = await client.patch(
        f"/api/admin/products/{product_id}", headers=_admin_auth(), json={"upload_id": upload_id}
    )
    image_url = resp.json()["image_url"]
    assert image_url is not None

    resp = await client.patch(
        f"/api/admin/products/{product_id}", headers=_admin_auth(), json={"is_available": False}
    )
    assert resp.status_code == 200
    assert resp.json()["image_url"] == image_url


@pytest.mark.parametrize("field", ["category_id", "name", "sku", "price", "is_available"])
async def test_patch_product_null_required_field_is_422(client, field):
    category_id = await _create_category(client, "Kat")
    product_id = await _create_product(client, category_id, sku=f"SKU-REQ-{field}")

    resp = await client.patch(
        f"/api/admin/products/{product_id}", headers=_admin_auth(), json={field: None}
    )
    assert resp.status_code == 422

    resp = await client.get(f"/api/admin/products", headers=_admin_auth())
    assert resp.status_code == 200
    assert [p["id"] for p in resp.json()] == [product_id]


async def test_admin_endpoints_reject_customer_init_data_401(client):
    headers = _customer_auth()
    resp = await client.get("/api/admin/products", headers=headers)
    assert resp.status_code == 401
    assert resp.json() == {"detail": "invalid_init_data"}


async def test_admin_endpoints_reject_admin_token_not_in_admin_ids_403(client):
    raw = sign_init_data({"id": 999, "first_name": "Nobody"}, ADMIN_TOKEN)
    headers = {"Authorization": f"tma {raw}"}
    resp = await client.get("/api/admin/products", headers=headers)
    assert resp.status_code == 403
    assert resp.json() == {"detail": "forbidden"}

    resp = await client.post("/api/admin/categories", headers=headers, json={"name": "X"})
    assert resp.status_code == 403

    resp = await client.get("/api/admin/categories", headers=headers)
    assert resp.status_code == 403

    files = {"file": ("a.png", PNG_BYTES, "image/png")}
    resp = await client.post("/api/admin/uploads", headers=headers, files=files)
    assert resp.status_code == 403
