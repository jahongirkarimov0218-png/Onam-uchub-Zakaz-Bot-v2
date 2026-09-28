from conftest import sign_init_data

from app.main import create_app
from app.notify import NullNotifier

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


def test_create_app_defaults_notifier_to_null_notifier(settings):
    app = create_app(settings=settings)
    assert isinstance(app.state.notifier, NullNotifier)


async def test_oversized_content_length_on_upload_path_is_413_before_auth_runs(app, settings):
    # Raw ASGI call (bypasses httpx, which would recompute Content-Length):
    # proves the body-size middleware sits in front of the app, rejecting by
    # a lying Content-Length before even the auth dependency runs — no
    # Authorization header is supplied here.
    limit = settings.max_upload_mb * 1024 * 1024 + 64 * 1024
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/uploads",
        "headers": [(b"content-length", str(limit + 1).encode())],
        "query_string": b"",
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 80),
        "scheme": "http",
        "root_path": "",
        "http_version": "1.1",
    }
    sent = []

    async def receive():
        raise AssertionError("body must not be read")

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)

    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413
