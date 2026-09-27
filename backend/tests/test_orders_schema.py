import pytest
from pydantic import ValidationError

from app.schemas.orders import OrderCreate, normalize_phone


def _base(**overrides) -> dict:
    body = {
        "customer_name": "Ali",
        "phone": "+998901234567",
        "delivery_type": "pickup",
        "items": [{"product_id": 1, "quantity": 2}],
    }
    body.update(overrides)
    return body


def test_normalize_phone_keeps_full_uz_format():
    assert normalize_phone("+998901234567") == "+998901234567"


def test_normalize_phone_prefixes_local_nine_digits_with_998():
    assert normalize_phone("901234567") == "+998901234567"


def test_normalize_phone_adds_plus_to_longer_international_digits():
    assert normalize_phone("15551234567") == "+15551234567"


def test_normalize_phone_strips_spaces_dashes_and_parens_before_validating():
    assert normalize_phone("+998 90 123 45 67") == "+998901234567"
    assert normalize_phone("+998 (90) 123-45-67") == "+998901234567"


def test_normalize_phone_accepts_other_country_codes_with_leading_plus():
    assert normalize_phone("+79161234567") == "+79161234567"


def test_normalize_phone_rejects_junk():
    with pytest.raises(ValueError):
        normalize_phone("abc")
    with pytest.raises(ValueError):
        normalize_phone("12345")  # too short


def test_order_create_normalizes_phone_field():
    order = OrderCreate(**_base(phone="901234567"))
    assert order.phone == "+998901234567"


def test_order_create_invalid_phone_is_rejected():
    with pytest.raises(ValidationError):
        OrderCreate(**_base(phone="12345"))


def test_order_create_delivery_requires_address():
    with pytest.raises(ValidationError):
        OrderCreate(**_base(delivery_type="delivery", address=None))


def test_order_create_delivery_with_address_ok():
    order = OrderCreate(**_base(delivery_type="delivery", address="Tashkent, 1-uy"))
    assert order.address == "Tashkent, 1-uy"


def test_order_create_custom_item_needs_at_least_one_field():
    with pytest.raises(ValidationError):
        OrderCreate(**_base(items=[{"custom": {}, "quantity": 1}]))


def test_order_create_custom_item_with_name_ok():
    order = OrderCreate(**_base(items=[{"custom": {"name": "Sovun"}, "quantity": 1}]))
    assert order.items[0].custom.name == "Sovun"


def test_order_create_item_needs_exactly_one_of_product_id_or_custom():
    with pytest.raises(ValidationError):
        OrderCreate(**_base(items=[{"quantity": 1}]))
    with pytest.raises(ValidationError):
        OrderCreate(
            **_base(items=[{"product_id": 1, "custom": {"name": "X"}, "quantity": 1}])
        )
