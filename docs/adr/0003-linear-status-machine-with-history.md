## Context
Orders have to be tracked by status (R02) with nothing forgotten (R69i). Several admins can press buttons on the same order at once, from the admin bot or from the admin Mini App.

## Decision
An order's status follows a fixed linear machine: `new → accepted → ordered → arrived → delivered`, plus `cancelled` from any non-final state. A transition may only move one step forward or go to cancellation. Every change writes a row to `order_status_history` (from, to, actor, source, time). The change is applied with an UPDATE conditioned on the current status. If a concurrent change already moved the order, the request gets `invalid_transition` / "Holat allaqachon o'zgargan", and the admin messages are refreshed.

## Why
- **A free-form status field that admins could set to any value** was rejected. The bot's inline keyboard can show only the next valid button. Skipping or reverting states would make reminders (which key on `new`) and `/stats` unreliable.
- **Tracking only the current status plus `updated_at`** was rejected. It can't answer "who accepted this and when", and R69i asks for exactly that trail. It also can't show history in the admin detail view.
- **Read-then-write without a condition** was rejected. Two admins pressing different buttons at the same moment would both succeed, leave history inconsistent, and send the customer two contradictory messages.
- **Undo / step-back transitions** were left out. The brief lists a forward chain and cancel only. Adding undo would mean deciding what to tell the customer when a status goes backwards.

## Consequences
- An admin's mis-click can't be undone. The only fixes are cancelling or moving forward, and the customer has already been notified.
- Adding, renaming or reordering a status changes `NEXT`, `LABELS_UZ`, the bot keyboards, reminders, the daily report, stats, and every existing history row. Stored status strings are part of the data, so renaming one requires a data migration.
- `cancelled` is terminal. A cancelled order that the customer still wants has to be placed again as a new order.
- The history table grows by one row per transition and is never pruned.
