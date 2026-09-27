import time

import pytest

from app.auth import InitDataError, TgUser, validate_init_data
from conftest import sign_init_data

BOT_TOKEN = "111111:TEST-customer"
OTHER_BOT_TOKEN = "222222:TEST-admin"
USER = {"id": 42, "first_name": "Ona", "last_name": "Shop", "username": "onashop"}


def test_valid_init_data_parses_user():
    raw = sign_init_data(USER, BOT_TOKEN)
    user = validate_init_data(raw, BOT_TOKEN, max_age=86400)
    assert isinstance(user, TgUser)
    assert user.id == 42
    assert user.first_name == "Ona"
    assert user.username == "onashop"


def test_tampered_hash_is_rejected():
    raw = sign_init_data(USER, BOT_TOKEN)
    tampered = raw[:-1] + ("0" if raw[-1] != "0" else "1")
    with pytest.raises(InitDataError) as exc_info:
        validate_init_data(tampered, BOT_TOKEN, max_age=86400)
    assert exc_info.value.code == "invalid_init_data"


def test_missing_hash_is_rejected():
    raw = sign_init_data(USER, BOT_TOKEN)
    without_hash = "&".join(p for p in raw.split("&") if not p.startswith("hash="))
    with pytest.raises(InitDataError) as exc_info:
        validate_init_data(without_hash, BOT_TOKEN, max_age=86400)
    assert exc_info.value.code == "invalid_init_data"


def test_wrong_token_is_rejected():
    raw = sign_init_data(USER, BOT_TOKEN)
    with pytest.raises(InitDataError) as exc_info:
        validate_init_data(raw, OTHER_BOT_TOKEN, max_age=86400)
    assert exc_info.value.code == "invalid_init_data"


def test_expired_auth_date_is_rejected():
    old_auth_date = int(time.time()) - 100_000
    raw = sign_init_data(USER, BOT_TOKEN, auth_date=old_auth_date)
    with pytest.raises(InitDataError) as exc_info:
        validate_init_data(raw, BOT_TOKEN, max_age=86400)
    assert exc_info.value.code == "init_data_expired"


def test_future_auth_date_is_rejected():
    future_auth_date = int(time.time()) + 3600
    raw = sign_init_data(USER, BOT_TOKEN, auth_date=future_auth_date)
    with pytest.raises(InitDataError) as exc_info:
        validate_init_data(raw, BOT_TOKEN, max_age=86400)
    assert exc_info.value.code == "init_data_expired"
