import { useEffect, useState } from "react";
import { api, ApiError } from "../../shared/api";
import { t } from "../../shared/i18n/uz";
import { formatSum, formatDate } from "../../shared/format";
import { FINAL, STATUSES } from "../../shared/status";

export type OrderSummary = {
  id: number;
  status: string;
  status_label: string;
  customer_name: string;
  phone: string;
  total: number;
  created_at: string;
};

type Filter = "all" | "open" | (typeof STATUSES)[number];

const FILTERS: Filter[] = ["all", "open", ...STATUSES];

function filterLabel(f: Filter): string {
  if (f === "all") return t("admin.orders.filterAll");
  if (f === "open") return t("admin.orders.filterOpen");
  return t(`status.${f}`);
}

/** Status filter chips + search box; fetches `/api/admin/orders`. "all"/"open"
 * send no `status` query param (the backend only supports one exact status);
 * "open" filters out final statuses client-side after the fetch. */
export function Orders({ onSelectOrder }: { onSelectOrder: (id: number) => void }) {
  const [filter, setFilter] = useState<Filter>("all");
  const [search, setSearch] = useState("");
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams();
    if (filter !== "all" && filter !== "open") params.set("status", filter);
    if (search.trim()) params.set("q", search.trim());
    const qs = params.toString();
    let cancelled = false;
    setError(null);
    api<OrderSummary[]>(`/api/admin/orders${qs ? `?${qs}` : ""}`)
      .then((data) => {
        if (cancelled) return;
        setOrders(filter === "open" ? data.filter((o) => !FINAL.has(o.status)) : data);
        setLoaded(true);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : t("errors.generic"));
        setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [filter, search]);

  return (
    <div>
      <h1>{t("admin.orders.title")}</h1>
      <input
        aria-label={t("admin.orders.searchPlaceholder")}
        placeholder={t("admin.orders.searchPlaceholder")}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <div>
        {FILTERS.map((f) => (
          <button key={f} aria-pressed={filter === f} onClick={() => setFilter(f)}>
            {filterLabel(f)}
          </button>
        ))}
      </div>

      {error && <p role="alert">{error}</p>}
      {loaded && orders.length === 0 && !error && <p>{t("admin.orders.empty")}</p>}

      <ul>
        {orders.map((o) => (
          <li key={o.id}>
            <button onClick={() => onSelectOrder(o.id)}>#{o.id}</button>
            <span>{o.status_label}</span>
            <span>{o.customer_name}</span>
            <span>{o.phone}</span>
            <span>{formatSum(o.total)}</span>
            <span>{formatDate(o.created_at)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
