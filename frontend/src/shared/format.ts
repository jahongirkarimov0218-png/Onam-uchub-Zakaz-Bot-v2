/** Formats an integer so'm amount as "125 000 so'm". */
export function formatSum(amount: number): string {
  const rounded = Math.round(amount);
  const sign = rounded < 0 ? "-" : "";
  const digits = Math.abs(rounded).toString();
  const grouped = digits.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  return `${sign}${grouped} so'm`;
}

/** Formats an ISO datetime string for display (uz-UZ, date + time). */
export function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const datePart = date.toLocaleDateString("uz-UZ");
  const timePart = date.toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit" });
  return `${datePart} ${timePart}`;
}
