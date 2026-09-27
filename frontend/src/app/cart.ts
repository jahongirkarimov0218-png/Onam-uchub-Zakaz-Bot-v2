// Customer cart: pure state helpers + localStorage persistence.
// Not in src/shared — the admin app has no cart.
const STORAGE_KEY = "onam-cart-v1";
const MIN_QTY = 1;
const MAX_QTY = 99;

export type CatalogCartLine = {
  kind: "catalog";
  productId: number;
  name: string;
  sku: string;
  price: number;
  imageUrl: string | null;
  quantity: number;
};

export type CustomCartLine = {
  kind: "custom";
  id: string;
  name: string | null;
  sku: string | null;
  uploadId: number | null;
  imageUrl: string | null;
  note: string | null;
  quantity: number;
};

export type CartLine = CatalogCartLine | CustomCartLine;

export function lineKey(line: CartLine): string {
  return line.kind === "catalog" ? `catalog:${line.productId}` : `custom:${line.id}`;
}

function clampQty(qty: number): number {
  return Math.min(MAX_QTY, Math.max(MIN_QTY, Math.round(qty)));
}

export function loadCart(): CartLine[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as CartLine[]) : [];
  } catch {
    return [];
  }
}

export function saveCart(lines: CartLine[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(lines));
  } catch {
    // private-mode / quota errors: cart just won't persist this write
  }
}

export function cartTotal(lines: CartLine[]): number {
  return lines
    .filter((l): l is CatalogCartLine => l.kind === "catalog")
    .reduce((sum, l) => sum + l.price * l.quantity, 0);
}

export function addCatalogLine(
  lines: CartLine[],
  product: { productId: number; name: string; sku: string; price: number; imageUrl: string | null },
  quantity = 1
): CartLine[] {
  const existing = lines.find((l) => l.kind === "catalog" && l.productId === product.productId) as
    | CatalogCartLine
    | undefined;
  if (existing) {
    return setQuantity(lines, lineKey(existing), existing.quantity + quantity);
  }
  const line: CatalogCartLine = { kind: "catalog", ...product, quantity: clampQty(quantity) };
  return [...lines, line];
}

export function addCustomLine(
  lines: CartLine[],
  data: { name: string | null; sku: string | null; uploadId: number | null; imageUrl: string | null; note: string | null; quantity: number }
): CartLine[] {
  const line: CustomCartLine = {
    kind: "custom",
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    ...data,
    quantity: clampQty(data.quantity),
  };
  return [...lines, line];
}

export function setQuantity(lines: CartLine[], key: string, quantity: number): CartLine[] {
  const clamped = clampQty(quantity);
  return lines.map((l) => (lineKey(l) === key ? { ...l, quantity: clamped } : l));
}

export function removeLine(lines: CartLine[], key: string): CartLine[] {
  return lines.filter((l) => lineKey(l) !== key);
}
