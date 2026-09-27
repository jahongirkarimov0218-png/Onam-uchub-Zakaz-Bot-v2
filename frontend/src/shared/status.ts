// Order status machine — mirrors `app.services.orders` (NEXT/FINAL/LABELS_UZ)
// on the backend exactly. Labels come from i18n so the uz text lives in one
// place (`shared/i18n/uz.ts` -> `status.*`).
import { t } from "./i18n/uz";

export const NEXT: Record<string, string> = {
  new: "accepted",
  accepted: "ordered",
  ordered: "arrived",
  arrived: "delivered",
};

export const FINAL: Set<string> = new Set(["delivered", "cancelled"]);

export const STATUSES = ["new", "accepted", "ordered", "arrived", "delivered", "cancelled"] as const;
export type OrderStatus = (typeof STATUSES)[number];

/** Same rule as the backend: forward one step per NEXT, or cancel from any
 * non-final status. */
export function allowed(from: string, to: string): boolean {
  return NEXT[from] === to || (to === "cancelled" && !FINAL.has(from));
}

/** The single forward transition for `from`, or null when there isn't one
 * (final statuses, or an unknown status). */
export function nextStatus(from: string): string | null {
  return NEXT[from] ?? null;
}

/** uz label for a status code, via `status.<code>` in the i18n dict. */
export function statusLabel(status: string): string {
  return t(`status.${status}`);
}
