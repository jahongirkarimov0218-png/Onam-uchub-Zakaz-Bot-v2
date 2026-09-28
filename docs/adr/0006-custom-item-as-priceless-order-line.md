## Context
Ordering a product that isn't in the catalog, by name, article or photo, is the core feature (R25). Its price is unknown when the order is placed, and the consultant is the one who finds it out later.

## Decision
A "Katalogda yo'q" request is an ordinary cart and order line with `kind='custom'`, going through the same checkout as catalog items. Its fields are optional `name`/`sku`/`upload_id`, a quantity and a note, with `product_id` and `unit_price` set to NULL. It is shown as "Narx keyin aniqlanadi" and left out of `orders.total`.

## Why
- **A separate "product request" entity with its own flow** was rejected. It would need a second checkout, a second status pipeline and a second set of admin notifications. A customer who wants two catalog items and one unknown one would end up with two unrelated records, which is exactly how orders got lost before.
- **Creating a catalog product on the fly** for each request was rejected. The catalog would fill with unverified, priceless one-offs that other customers could see.
- **Making the customer enter a price** was rejected. They don't know it, and client-supplied prices go against R71i.
- **Letting the admin set the price later on the line** was left out. The brief doesn't ask for it, and it would need a price-edit flow, total recalculation and a notification to the customer.

## Consequences
- `orders.total` understates what the customer will actually pay whenever the order has custom lines. The final amount is agreed outside the system, by phone.
- `/stats` "delivered sum this month" undercounts for the same reason, so it isn't a revenue figure.
- `order_items` has nullable `product_id`, `unit_price` and `name`. Every consumer (formatters, stats, the frontend) has to handle both shapes.
- A custom line can only point to a `custom` upload made by the same user (R52.1). Its photo is the only record of what was asked for, so upload files can't be treated as disposable.
- Adding admin-set pricing later means a schema change for who set the price and when, plus a re-total rule. It can't be done as a UI-only change.
