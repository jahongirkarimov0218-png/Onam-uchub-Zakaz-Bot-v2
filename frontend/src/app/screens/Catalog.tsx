import { useEffect, useState } from "react";
import { api } from "../../shared/api";
import { t } from "../../shared/i18n/uz";
import { formatSum } from "../../shared/format";

export type Category = { id: number; name: string };
export type Product = {
  id: number;
  category_id: number;
  name: string;
  sku: string;
  price: number;
  description: string;
  image_url: string | null;
  is_available: boolean;
};

/** Category chips + search box; fetches `/api/products` with `category_id`/`q`
 * params whenever the filter changes. */
export function Catalog({
  onSelectProduct,
  onAddToCart,
  onOpenCustomForm,
}: {
  onSelectProduct: (id: number) => void;
  onAddToCart: (product: Product) => void;
  onOpenCustomForm: () => void;
}) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [search, setSearch] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    api<Category[]>("/api/categories").then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (categoryId != null) params.set("category_id", String(categoryId));
    if (search.trim()) params.set("q", search.trim());
    const qs = params.toString();
    let cancelled = false;
    api<Product[]>(`/api/products${qs ? `?${qs}` : ""}`)
      .then((data) => {
        if (!cancelled) {
          setProducts(data);
          setLoaded(true);
        }
      })
      .catch(() => {
        if (!cancelled) setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [categoryId, search]);

  return (
    <div>
      <input
        aria-label={t("catalog.searchPlaceholder")}
        placeholder={t("catalog.searchPlaceholder")}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <div>
        <button aria-pressed={categoryId === null} onClick={() => setCategoryId(null)}>
          {t("catalog.allCategories")}
        </button>
        {categories.map((c) => (
          <button key={c.id} aria-pressed={categoryId === c.id} onClick={() => setCategoryId(c.id)}>
            {c.name}
          </button>
        ))}
      </div>

      {loaded && products.length === 0 && (
        <div>
          <p>{t("catalog.empty")}</p>
          <button onClick={onOpenCustomForm}>{t("catalog.emptyCustomLink")}</button>
        </div>
      )}

      <ul>
        {products.map((p) => (
          <li key={p.id} style={{ opacity: p.is_available ? 1 : 0.5 }}>
            {p.image_url && <img src={p.image_url} alt={p.name} width={60} height={60} />}
            <button onClick={() => onSelectProduct(p.id)}>{p.name}</button>
            <span>{p.sku}</span>
            <span>{formatSum(p.price)}</span>
            <span>{p.description}</span>
            <button disabled={!p.is_available} onClick={() => onAddToCart(p)}>
              {p.is_available ? t("catalog.addToCart") : t("catalog.unavailable")}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
