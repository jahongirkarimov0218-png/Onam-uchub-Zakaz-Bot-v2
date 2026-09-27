"""All bot-facing texts (Uzbek Latin), in one module.

Pure string builders: no aiogram, no DB. `app.notify` / `app.bots.*` import
from here and do the sending.
"""
from __future__ import annotations

from .statuses import LABELS_UZ

BTN_OPEN_SHOP = "Do'konni ochish"
BTN_OPEN_ADMIN = "Admin panelni ochish"
BTN_CANCEL = "Bekor qilish"

CUSTOMER_GREETING = "Assalomu alaykum! Faberlik Sotuv Bot'ga xush kelibsiz."
CUSTOMER_GREETING_NO_WEBAPP = (
    "Assalomu alaykum! Do'kon hozircha sozlanmoqda, birozdan so'ng qayta urinib ko'ring."
)

ADMIN_GREETING = "Assalomu alaykum! Bu — admin bot."
ADMIN_GREETING_NO_WEBAPP = "Assalomu alaykum! Admin panel hozircha sozlanmagan (WEBAPP_URL yo'q)."
ADMIN_HELP = (
    "Buyruqlar:\n"
    "/orders — ochiq zakazlar\n"
    "/order_<raqam> — zakaz tafsilotlari\n"
    "/find <raqam yoki telefon> — qidirish\n"
    "/stats — statistika"
)

NOT_ADMIN = "Ruxsat yo'q"
STALE_STATUS = "Holat allaqachon o'zgargan"
NOT_FOUND = "Topilmadi"
NO_OPEN_ORDERS = "Ochiq zakazlar yo'q"
FIND_USAGE = "Foydalanish: /find <raqam yoki telefon>"

# format_order labels (app.notify composes these into the order card)
LABEL_ORDER_PREFIX = "Zakaz #"
LABEL_CUSTOMER = "Mijoz:"
LABEL_PHONE = "Telefon:"
LABEL_USERNAME = "Username:"
LABEL_DELIVERY = "Yetkazib berish:"
PICKUP_LINE = "Olib ketish"
LABEL_ITEMS = "Mahsulotlar:"
LABEL_TOTAL = "Summa:"
LABEL_STATUS = "Holat:"
LABEL_COMMENT = "Izoh:"
CUSTOM_ITEM_MARKER = "(katalogda yo'q)"
PRICE_LATER = "Narx keyin aniqlanadi"


def format_money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " so'm"


def status_changed_text(order: object) -> str:
    label = LABELS_UZ[order.status]
    return f"Sizning #{order.id} raqamli zakazingiz holati o'zgardi: {label}"


def reminder_text(orders: list) -> str:
    lines = ["Eslatma: quyidagi zakazlar hali qabul qilinmagan:"]
    for order in orders:
        lines.append(f"#{order.id} — {order.customer_name}")
    return "\n".join(lines)


def daily_report_text(orders: list) -> str:
    if not orders:
        return NO_OPEN_ORDERS
    groups: dict[str, list] = {}
    for order in orders:
        groups.setdefault(order.status, []).append(order)
    lines = ["Kunlik hisobot — ochiq zakazlar:"]
    for status, label in LABELS_UZ.items():
        if status not in groups:
            continue
        lines.append(f"\n{label}:")
        for order in groups[status]:
            lines.append(f"#{order.id} — {order.customer_name}")
    return "\n".join(lines)


def stats_text(data: dict) -> str:
    lines = ["Statistika:"]
    for status, label in LABELS_UZ.items():
        lines.append(f"{label}: {data['by_status'].get(status, 0)}")
    lines.append(f"Bugun: {data['today']}")
    lines.append(f"Bu oy topshirilgan summa: {format_money(data['delivered_month_sum'])}")
    return "\n".join(lines)


def open_orders_list(orders: list) -> str:
    """/orders reply: up to 30 open orders, newest first, each with its
    `/order_<id>` deep-link command; `NO_OPEN_ORDERS` if none."""
    if not orders:
        return NO_OPEN_ORDERS
    lines = [f"#{o.id} — {LABELS_UZ[o.status]} — /order_{o.id}" for o in orders[:30]]
    return "\n".join(lines)


def search_results_list(orders: list) -> str:
    """/find reply: matching orders; `NOT_FOUND` if none."""
    if not orders:
        return NOT_FOUND
    lines = [f"#{o.id} — {o.customer_name} — {LABELS_UZ[o.status]}" for o in orders]
    return "\n".join(lines)
