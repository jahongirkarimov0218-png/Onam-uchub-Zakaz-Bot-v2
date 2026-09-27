from app import texts


def test_daily_report_text_is_placeholder_when_no_open_orders():
    assert texts.daily_report_text([]) == "Ochiq zakazlar yo'q"


def test_daily_report_text_groups_open_orders_by_status():
    new_order = type("O", (), {"id": 3, "customer_name": "Ali", "status": "new"})()
    accepted_order = type("O", (), {"id": 1, "customer_name": "Vali", "status": "accepted"})()
    text = texts.daily_report_text([new_order, accepted_order])
    assert "Yangi" in text
    assert "Qabul qilindi" in text
    assert "#3" in text and "#1" in text
    assert text.index("Yangi") < text.index("#3")


def test_reminder_text_lists_order_numbers():
    order = type("O", (), {"id": 7, "customer_name": "Ali"})()
    text = texts.reminder_text([order])
    assert "#7" in text
    assert "Ali" in text


def test_status_changed_text_has_number_and_label():
    order = type("O", (), {"id": 5, "status": "accepted"})()
    text = texts.status_changed_text(order)
    assert "#5" in text
    assert "Qabul qilindi" in text


def test_find_usage_and_not_found_and_no_open_orders_are_plain_strings():
    assert "/find" in texts.FIND_USAGE
    assert texts.NOT_FOUND == "Topilmadi"
    assert texts.NOT_ADMIN == "Ruxsat yo'q"
    assert texts.STALE_STATUS == "Holat allaqachon o'zgargan"
    assert texts.NO_OPEN_ORDERS == "Ochiq zakazlar yo'q"


def test_format_money_groups_thousands():
    assert texts.format_money(450000) == "450 000 so'm"


def test_stats_text_uses_grouped_money_format():
    data = {"by_status": {}, "today": 2, "delivered_month_sum": 450000}
    text = texts.stats_text(data)
    assert "450 000 so'm" in text


def test_open_orders_list_formats_and_links_order_ids():
    order = type("O", (), {"id": 9, "status": "new"})()
    text = texts.open_orders_list([order])
    assert "/order_9" in text
    assert "Yangi" in text


def test_open_orders_list_empty_is_no_open_orders():
    assert texts.open_orders_list([]) == texts.NO_OPEN_ORDERS


def test_search_results_list_formats_matches():
    order = type("O", (), {"id": 4, "customer_name": "Ali", "status": "accepted"})()
    text = texts.search_results_list([order])
    assert "#4" in text and "Ali" in text


def test_search_results_list_empty_is_not_found():
    assert texts.search_results_list([]) == texts.NOT_FOUND
