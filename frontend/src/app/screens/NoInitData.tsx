import { t } from "../../shared/i18n/uz";
import { Logo } from "../../shared/Logo";

/** Shown when the app is opened outside Telegram (no initData) — no API calls happen. */
export function NoInitData() {
  return (
    <div style={{ padding: 24, textAlign: "center" }}>
      <Logo />
      <p>{t("openInTelegram.title")}</p>
    </div>
  );
}
