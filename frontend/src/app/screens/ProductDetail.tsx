import { useEffect, useState } from "react";
import { api, ApiError } from "../../shared/api";
import { t } from "../../shared/i18n/uz";
import { formatSum } from "../../shared/format";
import type { Product } from "./Catalog";

export function ProductDetail({
  productId,
  onBack,
  onAddToCart,
}: {
  productId: number;
  onBack: () => void;
  onAddToCart: (product: Product) => void;
}) {
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<Product>(`/api/products/${productId}`)
      .then((p) => {
        if (!cancelled) setProduct(p);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : t("errors.generic"));
      });
    return () => {
      cancelled = true;
    };
  }, [productId]);

  return (
    <div>
      <button onClick={onBack}>{t("product.back")}</button>
      {error && <p role="alert">{error}</p>}
      {product && (
        <div>
          {product.image_url && <img src={product.image_url} alt={product.name} width={200} height={200} />}
          <h1>{product.name}</h1>
          <p>
            {t("product.sku")}: {product.sku}
          </p>
          <p>{formatSum(product.price)}</p>
          <p>{t("product.description")}</p>
          <p>{product.description}</p>
          <button disabled={!product.is_available} onClick={() => onAddToCart(product)}>
            {product.is_available ? t("catalog.addToCart") : t("catalog.unavailable")}
          </button>
        </div>
      )}
    </div>
  );
}
