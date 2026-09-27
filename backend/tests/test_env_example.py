from pathlib import Path

from app.config import Settings

ENV_EXAMPLE_PATH = Path(__file__).resolve().parents[2] / ".env.example"

SECRET_KEYS = {"CUSTOMER_BOT_TOKEN", "ADMIN_BOT_TOKEN", "ADMIN_IDS"}


def _parse_env_example() -> dict[str, str]:
    lines = ENV_EXAMPLE_PATH.read_text(encoding="utf-8").splitlines()
    values = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key] = value
    return values


def test_env_example_file_exists():
    assert ENV_EXAMPLE_PATH.is_file()


def test_env_example_lists_every_setting():
    values = _parse_env_example()
    expected_keys = {name.upper() for name in Settings.model_fields}
    assert expected_keys.issubset(values.keys())


def test_env_example_has_no_secret_values():
    values = _parse_env_example()
    for key in SECRET_KEYS:
        assert values.get(key, "") == "", f"{key} must be empty in .env.example"


def test_no_real_env_file_was_created():
    assert not (ENV_EXAMPLE_PATH.parent / ".env").exists()
