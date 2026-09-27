// Neutral, self-made mark — never the Faberlic logo (this is not an official
// Faberlic project).
import { t } from "./i18n/uz";

export function Logo({ size = 40, label }: { size?: number; label?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" role="img" aria-label={label ?? t("app.title")}>
      <circle cx="20" cy="20" r="19" fill="var(--tg-button, #2481cc)" />
      <path
        d="M12 24 L20 12 L28 24 Z"
        fill="var(--tg-button-text, #ffffff)"
      />
      <circle cx="20" cy="27" r="2.5" fill="var(--tg-button-text, #ffffff)" />
    </svg>
  );
}
