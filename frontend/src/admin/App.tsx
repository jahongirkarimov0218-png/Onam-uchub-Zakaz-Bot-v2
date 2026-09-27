import { useCallback, useEffect, useState } from "react";
import { tg } from "../shared/telegram";
import { api, ApiError } from "../shared/api";
import { t } from "../shared/i18n/uz";
import { Logo } from "../shared/Logo";
import { navigate, useHashRoute } from "../shared/router";
import { Orders } from "./screens/Orders";
import { OrderDetail } from "./screens/OrderDetail";
import { Products } from "./screens/Products";
import { Categories } from "./screens/Categories";

type Gate = "loading" | "forbidden" | "error" | "ready";

/** Opened outside Telegram: no fetch at all (same contract as the customer app). */
function NoInitData() {
  return (
    <div style={{ padding: 24, textAlign: "center" }}>
      <Logo />
      <p>{t("openInTelegram.title")}</p>
    </div>
  );
}

/** `/api/admin/me` gate: 401 (bad/expired initData) or 403 (not in
 * ADMIN_IDS) both render only the "Ruxsat yo'q" screen — nothing else. */
function Forbidden() {
  return (
    <div style={{ padding: 24, textAlign: "center" }}>
      <Logo />
      <p>{t("errors.forbidden")}</p>
    </div>
  );
}

/** Network/5xx (anything that isn't 401/403) is not the same as "not an
 * admin" — show a generic retryable error instead of "Ruxsat yo'q". */
function MeError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div style={{ padding: 24, textAlign: "center" }}>
      <Logo />
      <p role="alert">{message}</p>
      <button onClick={onRetry}>{t("admin.retry")}</button>
    </div>
  );
}

export function App() {
  const hasInitData = !!tg.initData;
  const route = useHashRoute();
  const [gate, setGate] = useState<Gate>("loading");
  const [meError, setMeError] = useState<string | null>(null);

  const checkMe = useCallback(() => {
    setGate("loading");
    api("/api/admin/me")
      .then(() => {
        tg.ready();
        setGate("ready");
      })
      .catch((err) => {
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          setGate("forbidden");
        } else {
          setMeError(err instanceof ApiError ? err.message : t("errors.generic"));
          setGate("error");
        }
      });
  }, []);

  useEffect(() => {
    if (hasInitData) checkMe();
  }, [hasInitData, checkMe]);

  const parts = route.split("/").filter(Boolean);
  const inOrderDetail = parts[0] === "orders" && !!parts[1];

  useEffect(() => {
    if (!hasInitData || gate !== "ready") return;
    if (inOrderDetail) {
      tg.backButton.show(() => window.history.back());
    } else {
      tg.backButton.hide();
    }
    return () => tg.backButton.hide();
  }, [hasInitData, gate, inOrderDetail]);

  if (!hasInitData) return <NoInitData />;
  if (gate === "loading") return null;
  if (gate === "forbidden") return <Forbidden />;
  if (gate === "error") return <MeError message={meError ?? t("errors.generic")} onRetry={checkMe} />;

  let body: React.ReactNode;
  if (inOrderDetail) {
    body = <OrderDetail orderId={Number(parts[1])} onBack={() => navigate("/orders")} />;
  } else if (parts[0] === "products") {
    body = <Products />;
  } else if (parts[0] === "categories") {
    body = <Categories />;
  } else {
    body = <Orders onSelectOrder={(id) => navigate(`/orders/${id}`)} />;
  }

  return (
    <div>
      <header>
        <Logo />
        <span>{t("app.title")}</span>
        <nav>
          <button onClick={() => navigate("/orders")}>{t("admin.tabs.orders")}</button>
          <button onClick={() => navigate("/products")}>{t("admin.tabs.products")}</button>
          <button onClick={() => navigate("/categories")}>{t("admin.tabs.categories")}</button>
        </nav>
      </header>
      <main>{body}</main>
    </div>
  );
}
