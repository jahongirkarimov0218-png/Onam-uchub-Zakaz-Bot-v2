"""Telegram WebApp initData trust boundary.

Owns HMAC validation; exposes `validate_init_data`, `TgUser`, `InitDataError`,
and the FastAPI dependencies `customer_user` / `admin_user`.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException

from .config import Settings, get_settings

FUTURE_TOLERANCE_SECONDS = 60


class InitDataError(Exception):
    """Raised when initData fails validation. `code` is the machine error code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class TgUser:
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None


def validate_init_data(
    raw: str, bot_token: str, max_age: int, now: float | None = None
) -> TgUser:
    """Validate a raw Telegram WebApp initData string per the Telegram spec.

    Raises InitDataError("invalid_init_data") for missing/tampered hash or wrong token,
    InitDataError("init_data_expired") for auth_date too old or too far in the future.
    """
    if not raw:
        raise InitDataError("invalid_init_data")

    pairs = parse_qsl(raw, keep_blank_values=True)
    data = dict(pairs)
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise InitDataError("invalid_init_data")

    check_string = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise InitDataError("invalid_init_data")

    auth_date_raw = data.get("auth_date")
    if auth_date_raw is None:
        raise InitDataError("invalid_init_data")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise InitDataError("invalid_init_data") from exc

    current = now if now is not None else time.time()
    if current - auth_date > max_age:
        raise InitDataError("init_data_expired")
    if auth_date - current > FUTURE_TOLERANCE_SECONDS:
        raise InitDataError("init_data_expired")

    user_raw = data.get("user")
    if not user_raw:
        raise InitDataError("invalid_init_data")
    try:
        user_json = json.loads(user_raw)
    except ValueError as exc:
        raise InitDataError("invalid_init_data") from exc

    try:
        return TgUser(
            id=int(user_json["id"]),
            first_name=user_json.get("first_name", ""),
            last_name=user_json.get("last_name"),
            username=user_json.get("username"),
            language_code=user_json.get("language_code"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise InitDataError("invalid_init_data") from exc


def _extract_raw_init_data(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("tma "):
        raise InitDataError("invalid_init_data")
    return authorization[len("tma ") :]


async def customer_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> TgUser:
    try:
        raw = _extract_raw_init_data(authorization)
        return validate_init_data(raw, settings.customer_bot_token, settings.init_data_max_age_seconds)
    except InitDataError as exc:
        raise HTTPException(status_code=401, detail=exc.code) from exc


async def admin_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> TgUser:
    try:
        raw = _extract_raw_init_data(authorization)
        user = validate_init_data(raw, settings.admin_bot_token, settings.init_data_max_age_seconds)
    except InitDataError as exc:
        raise HTTPException(status_code=401, detail=exc.code) from exc
    if user.id not in settings.admin_id_set:
        raise HTTPException(status_code=403, detail="forbidden")
    return user
