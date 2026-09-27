import { t } from "../../shared/i18n/uz";
import { formatSum } from "../../shared/format";
import { cartTotal, lineKey, type CartLine } from "../cart";

export function CartScreen({
  cart,
  onSetQuantity,
  onRemove,
  onCheckout,
  onAddCustom,
}: {
  cart: CartLine[];
  onSetQuantity: (key: string, quantity: number) => void;
  onRemove: (key: string) => void;
  onCheckout: () => void;
  onAddCustom: () => void;
}) {
  if (cart.length === 0) {
    return (
      <div>
        <h1>{t("cart.title")}</h1>
        <p>{t("cart.empty")}</p>
        <button onClick={onAddCustom}>{t("cart.addCustom")}</button>
      </div>
    );
  }

  return (
    <div>
      <h1>{t("cart.title")}</h1>
      <ul>
        {cart.map((line) => {
          const key = lineKey(line);
          return (
            <li key={key}>
              <span>{line.kind === "catalog" ? line.name : line.name ?? line.sku ?? t("cart.customItemLabel")}</span>
              <span>{line.kind === "catalog" ? formatSum(line.price * line.quantity) : t("cart.customPriceLater")}</span>
              <button aria-label={t("cart.decrease")} onClick={() => onSetQuantity(key, line.quantity - 1)}>
                −
              </button>
              <input
                aria-label={t("cart.quantityLabel")}
                type="number"
                min={1}
                max={99}
                value={line.quantity}
                onChange={(e) => onSetQuantity(key, Number(e.target.value) || 1)}
              />
              <button aria-label={t("cart.increase")} onClick={() => onSetQuantity(key, line.quantity + 1)}>
                +
              </button>
              <button onClick={() => onRemove(key)}>{t("cart.remove")}</button>
            </li>
          );
        })}
      </ul>
      <p>
        {t("cart.total")}: {formatSum(cartTotal(cart))}
      </p>
      <button onClick={onAddCustom}>{t("cart.addCustom")}</button>
      <button onClick={onCheckout}>{t("cart.checkout")}</button>
    </div>
  );
}
