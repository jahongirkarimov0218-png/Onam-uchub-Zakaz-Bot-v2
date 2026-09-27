"""Application settings loaded from environment / .env file.

Owns env parsing; exposes `Settings` and `get_settings()`.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the project-root `.env`, resolved from this file's own
# location rather than left as a bare ".env" (which pydantic-settings would
# resolve against the process's current working directory — wrong whenever
# the app isn't started with `backend/` as cwd, e.g. `uvicorn` run from the
# project root). Explicit environment variables still take precedence over
# the file either way (pydantic-settings' default source order).
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore", case_sensitive=False)

    customer_bot_token: str = ""
    admin_bot_token: str = ""
    admin_ids: str = ""
    bots_enabled: bool = True
    webapp_url: str = ""
    telegram_api_base: str = ""
    shop_name: str = "Faberlik Sotuv Bot"
    pickup_address: str = "[Olib ketish manzili — .env faylida PICKUP_ADDRESS]"
    database_url: str = "sqlite+aiosqlite:///./data/onam.db"
    upload_dir: str = "uploads"
    frontend_dist: str = "../frontend/dist"
    init_data_max_age_seconds: int = 86400
    reminder_first_hours: int = 2
    reminder_repeat_hours: int = 4
    reminder_check_minutes: int = 5
    daily_report_time: str = "09:00"
    timezone: str = "Asia/Tashkent"
    rate_limit_orders: int = 5
    rate_limit_uploads: int = 10
    rate_limit_window_seconds: int = 600
    max_upload_mb: int = 5
    domain: str = ""

    @property
    def admin_id_set(self) -> set[int]:
        return {int(part.strip()) for part in self.admin_ids.split(",") if part.strip()}

    @property
    def bots_active(self) -> bool:
        return bool(self.bots_enabled and self.customer_bot_token and self.admin_bot_token)


@lru_cache
def get_settings() -> Settings:
    return Settings()
