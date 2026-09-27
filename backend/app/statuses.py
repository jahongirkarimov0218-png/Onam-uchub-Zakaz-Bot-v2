"""Order status machine constants.

Extracted from `app.services.orders` (which still re-exports `NEXT`, `FINAL`,
`LABELS_UZ`, `allowed` for backward compatibility) so that `app.notify` can use
the same constants in `format_order`/`order_keyboard` without a circular import
(`services.orders` imports `notify.Notifier`).
"""
from __future__ import annotations

NEXT = {"new": "accepted", "accepted": "ordered", "ordered": "arrived", "arrived": "delivered"}
FINAL = {"delivered", "cancelled"}
LABELS_UZ = {
    "new": "Yangi",
    "accepted": "Qabul qilindi",
    "ordered": "Faberlic'ga buyurtma berildi",
    "arrived": "Yetib keldi",
    "delivered": "Topshirildi",
    "cancelled": "Bekor qilindi",
}


def allowed(from_status: str, to_status: str) -> bool:
    return NEXT.get(from_status) == to_status or (to_status == "cancelled" and from_status not in FINAL)
