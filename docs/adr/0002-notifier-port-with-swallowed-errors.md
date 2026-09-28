## Context
The whole point of the product is that no order gets lost (R03). But Telegram delivery can fail: bots might be disabled (R17), a customer may never have started the bot or may have blocked it (R70i), or the API may simply error.

## Decision
All outbound Telegram traffic goes through a single `Notifier` port (`order_created`, `status_changed`, `reminder`, `daily_report`). There are two implementations, `TelegramNotifier` and `NullNotifier`. The order service commits first and calls the notifier afterwards. The notifier catches and logs every error and never raises. `orders.admin_notified` stays `false` until the new-order message has reached the admins, and the scheduler's `remind_and_retry` job resends it until it does. A failed customer message is only logged.

## Why
- **Sending inside the request and failing the order on error** was rejected. A blocked customer or a Telegram outage would then make it impossible to place an order, which is the exact loss the brief forbids.
- **Fire-and-forget without a retry flag** was rejected. If the admin message fails, nobody learns the order exists. That is the original "mom forgot the order" problem, just moved somewhere else.
- **An outbox table or an external queue** was rejected as heavier than needed. There is exactly one message whose delivery must be guaranteed (new order to admins). A boolean on the order plus the scheduler that already runs every few minutes covers it without new infrastructure (R60: no extra abstractions).
- **Calling aiogram directly from services** was rejected. Every test would need Telegram mocks, and `BOTS_ENABLED=false` would need `if` checks spread across the codebase. The port is the single test seam (`FakeNotifier`).

## Consequences
- Delivery to admins is at-least-once. If the process dies after sending but before `admin_notified` is committed, admins receive a duplicate.
- A retry can arrive up to `REMINDER_CHECK_MINUTES` late. While bots are off, retries are no-ops and pile up until bots come back.
- Customer notifications are best-effort with no retry. A customer who blocked the bot never finds out about status changes except through "Mening zakazlarim".
- Swallowed errors show up only in logs. Nothing alerts anyone when every send is failing (for example, a revoked token).
- Anything new that talks to Telegram must go through this port, or it loses both the test seam and the bots-off behaviour.
