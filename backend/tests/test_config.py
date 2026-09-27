from pathlib import Path

from app.config import Settings, get_settings


def test_bots_active_true_when_enabled_and_both_tokens_set():
    settings = Settings(
        customer_bot_token="123:TEST-customer",
        admin_bot_token="456:TEST-admin",
        bots_enabled=True,
    )
    assert settings.bots_active is True


def test_bots_active_false_when_disabled():
    settings = Settings(
        customer_bot_token="123:TEST-customer",
        admin_bot_token="456:TEST-admin",
        bots_enabled=False,
    )
    assert settings.bots_active is False


def test_bots_active_false_when_token_missing():
    settings = Settings(customer_bot_token="123:TEST-customer", admin_bot_token="", bots_enabled=True)
    assert settings.bots_active is False


def test_admin_id_set_parses_comma_list():
    settings = Settings(admin_ids="111, 222,333")
    assert settings.admin_id_set == {111, 222, 333}


def test_admin_id_set_empty_string_is_empty_set():
    settings = Settings(admin_ids="")
    assert settings.admin_id_set == set()


def test_get_settings_returns_settings_instance():
    assert isinstance(get_settings(), Settings)


def test_settings_env_file_is_project_root_absolute_path_independent_of_cwd(monkeypatch):
    # env_file must be an absolute path resolved once from config.py's own
    # location, not a bare ".env" (which pydantic-settings resolves against
    # os.getcwd() — wrong whenever the process isn't started with backend/
    # as its cwd).
    env_file = Path(Settings.model_config["env_file"])
    assert env_file.is_absolute()
    assert env_file.name == ".env"

    project_root = env_file.parent
    assert (project_root / "backend").is_dir()
    assert (project_root / "frontend").is_dir()

    # Baked in at class-definition time, so changing the process cwd (e.g. to
    # backend/, where the app is normally started from) can't change it.
    monkeypatch.chdir(project_root / "backend")
    assert Settings.model_config["env_file"] == str(env_file)
