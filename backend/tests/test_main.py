from conftest import sign_init_data

CUSTOMER_TOKEN = "111111:TEST-customer"
ADMIN_TOKEN = "222222:TEST-admin"


async def test_health_reports_bots_false_when_disabled(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "bots": False}


async def test_admin_me_without_authorization_header_is_401(client):
    resp = await client.get("/api/admin/me")
    assert resp.status_code == 401
    assert resp.json() == {"detail": "invalid_init_data"}


async def test_admin_me_with_customer_token_init_data_is_401(client):
    raw = sign_init_data({"id": 555, "first_name": "Admin"}, CUSTOMER_TOKEN)
    resp = await client.get("/api/admin/me", headers={"Authorization": f"tma {raw}"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "invalid_init_data"}


async def test_admin_me_with_admin_token_but_id_not_in_admin_ids_is_403(client):
    raw = sign_init_data({"id": 999, "first_name": "Nobody"}, ADMIN_TOKEN)
    resp = await client.get("/api/admin/me", headers={"Authorization": f"tma {raw}"})
    assert resp.status_code == 403
    assert resp.json() == {"detail": "forbidden"}


async def test_admin_me_with_admin_in_list_is_200(client):
    raw = sign_init_data({"id": 555, "first_name": "Onam"}, ADMIN_TOKEN)
    resp = await client.get("/api/admin/me", headers={"Authorization": f"tma {raw}"})
    assert resp.status_code == 200
    assert resp.json() == {"id": 555, "first_name": "Onam"}


async def test_app_serves_asgi_smoke(app):
    # create_app must succeed and produce a usable ASGI app with BOTS_ENABLED=false.
    assert app.state.settings.bots_active is False
