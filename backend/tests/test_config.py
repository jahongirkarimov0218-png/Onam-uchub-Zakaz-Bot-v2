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
