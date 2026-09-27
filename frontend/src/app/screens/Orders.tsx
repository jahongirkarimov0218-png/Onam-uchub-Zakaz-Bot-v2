import { useEffect, useState } from "react";
import { api, ApiError } from "../../shared/api";
import { t } from "../../shared/i18n/uz";
import { formatSum, formatDate } from "../../shared/format";

type OrderItem = {
  kind: "catalog" | "custom";
  name: string | null;
  sku: string | null;
  quantity: number;
};

type Order = {
  id: number;
  status: string;
  status_label: string;
  total: number;
  created_at: string;
  items: OrderItem[];
};

export function Orders({ onBackToCatalog }: { onBackToCatalog: () => void }) {
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<Order[]>("/api/orders/my")
      .then((data) => {
        if (!cancelled) setOrders(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : t("errors.generic"));
          setOrders([]);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <h1>{t("orders.title")}</h1>
      {error && <p role="alert">{error}</p>}
      {orders && orders.length === 0 && (
        <div>
          <p>{t("orders.empty")}</p>
          <button onClick={onBackToCatalog}>{t("orders.backToCatalog")}</button>
        </div>
      )}
      {orders && orders.length > 0 && (
        <ul>
          {orders.map((o) => (
            <li key={o.id}>
              <p>#{o.id}</p>
              <p>{formatDate(o.created_at)}</p>
              <p>{o.status_label}</p>
              <ul>
                {o.items.map((it, idx) => (
                  <li key={idx}>
                    {it.name ?? it.sku} x{it.quantity}
                  </li>
                ))}
              </ul>
              <p>
                {t("orders.total")}: {formatSum(o.total)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
