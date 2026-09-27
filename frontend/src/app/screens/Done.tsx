import { t } from "../../shared/i18n/uz";

export function Done({ orderId, onBackToCatalog }: { orderId: number; onBackToCatalog: () => void }) {
  return (
    <div>
      <h1>{t("done.title")}</h1>
      <p>{t("done.orderNumber", { id: orderId })}</p>
      <button onClick={onBackToCatalog}>{t("done.backToCatalog")}</button>
    </div>
  );
}
