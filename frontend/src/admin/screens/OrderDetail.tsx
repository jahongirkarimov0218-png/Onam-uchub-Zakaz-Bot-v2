import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../../shared/api";
import { t } from "../../shared/i18n/uz";
import { formatSum, formatDate } from "../../shared/format";
import { FINAL, nextStatus, statusLabel } from "../../shared/status";

/** uz label for a history row's source; falls back to the raw code for an
 * unknown value rather than rendering nothing. */
function sourceLabel(source: string): string {
  const key = `admin.orders.historySource.${source}`;
  const label = t(key);
  return label === key ? source : label;
}

type OrderItem = {
  kind: "catalog" | "custom";
  product_id: number | null;
  name: string | null;
  sku: string | null;
  image_url: string | null;
  unit_price: number | null;
  quantity: number;
  note: string | null;
};

type HistoryRow = {
  from_status: string | null;
  to_status: string;
  actor_tg_id: number | null;
  source: string;
  created_at: string;
};

type OrderDetailData = {
  id: number;
  status: string;
  status_label: string;
  customer_name: string;
  phone: string;
  delivery_type: "delivery" | "pickup";
  address: string | null;
  comment: string | null;
  total: number;
  created_at: string;
  items: OrderItem[];
  history: HistoryRow[];
};

/** Order detail: items, customer, status history, and buttons for the
 * allowed transitions only (next step + cancel, cancel needs an inline
 * confirm — no window.confirm in Telegram). Refetches after a status change. */
export function OrderDetail({ orderId, onBack }: { orderId: number; onBack: () => void }) {
  const [order, setOrder] = useState<OrderDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirmingCancel, setConfirmingCancel] = useState(false);
  const [changing, setChanging] = useState(false);

  const load = useCallback(() => {
    api<OrderDetailData>(`/api/admin/orders/${orderId}`)
      .then((data) => {
        setOrder(data);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : t("admin.orders.loadError"));
      });
  }, [orderId]);

  useEffect(() => {
    load();
  }, [load]);

  async function changeStatus(to: string) {
    if (changing) return;
    setChanging(true);
    try {
      await api(`/api/admin/orders/${orderId}/status`, { method: "POST", body: { status: to } });
      setConfirmingCancel(false);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      setChanging(false);
    }
  }

  const forward = order ? nextStatus(order.status) : null;
  const canCancel = order ? !FINAL.has(order.status) : false;

  return (
    <div>
      <button onClick={onBack}>{t("admin.orders.back")}</button>
      {error && <p role="alert">{error}</p>}
      {order && (
        <div>
          <h1>#{order.id}</h1>
          <p>{order.status_label}</p>
          <p>{order.customer_name}</p>
          <p>
            <a href={`tel:${order.phone}`}>{order.phone}</a>
          </p>
          <p>{order.delivery_type === "delivery" ? t("admin.orders.delivery") : t("admin.orders.pickup")}</p>
          {order.address && <p>{order.address}</p>}
          {order.comment && <p>{order.comment}</p>}

          <ul>
            {order.items.map((it, idx) => (
              <li key={idx}>
                {it.image_url && <img src={it.image_url} alt={it.name ?? it.sku ?? ""} width={60} height={60} />}
                <span>
                  {it.name ?? it.sku} x{it.quantity}
                </span>
                {it.unit_price != null && <span>{formatSum(it.unit_price * it.quantity)}</span>}
                {it.note && <p>{it.note}</p>}
              </li>
            ))}
          </ul>
          <p>
            {t("admin.orders.total")}: {formatSum(order.total)}
          </p>

          <div>
            {forward && (
              <button disabled={changing} onClick={() => changeStatus(forward)}>
                {statusLabel(forward)}
              </button>
            )}
            {canCancel && !confirmingCancel && (
              <button disabled={changing} onClick={() => setConfirmingCancel(true)}>
                {t("admin.orders.cancel")}
              </button>
            )}
            {confirmingCancel && (
              <div>
                <p>{t("admin.orders.cancelConfirm")}</p>
                <button disabled={changing} onClick={() => changeStatus("cancelled")}>
                  {t("admin.orders.confirmYes")}
                </button>
                <button disabled={changing} onClick={() => setConfirmingCancel(false)}>
                  {t("admin.orders.confirmNo")}
                </button>
              </div>
            )}
          </div>

          <h2>{t("admin.orders.history")}</h2>
          {order.history.length === 0 ? (
            <p>{t("admin.orders.historyEmpty")}</p>
          ) : (
            <ul>
              {order.history.map((h, idx) => (
                <li key={idx}>
                  {h.from_status ? statusLabel(h.from_status) : "—"} → {statusLabel(h.to_status)} ({sourceLabel(h.source)}
                  {h.actor_tg_id != null ? `, ${h.actor_tg_id}` : ""}, {formatDate(h.created_at)})
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
