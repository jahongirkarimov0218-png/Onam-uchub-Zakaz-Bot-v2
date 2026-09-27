import { useEffect, useState } from "react";
import { tg } from "../shared/telegram";
import { api } from "../shared/api";
import { t } from "../shared/i18n/uz";
import { Logo } from "../shared/Logo";
import { navigate, useHashRoute } from "../shared/router";
import { addCatalogLine, addCustomLine, loadCart, removeLine, saveCart, setQuantity, type CartLine } from "./cart";
import { Catalog, type Product } from "./screens/Catalog";
import { ProductDetail } from "./screens/ProductDetail";
import { CartScreen } from "./screens/CartScreen";
import { CustomForm } from "./screens/CustomForm";
import { Checkout } from "./screens/Checkout";
import { Orders } from "./screens/Orders";
import { Done } from "./screens/Done";
import { NoInitData } from "./screens/NoInitData";

type Config = { shop_name: string; shop_subtitle: string; pickup_address: string };

export function App() {
  const hasInitData = !!tg.initData;
  const route = useHashRoute();
  const [cart, setCart] = useState<CartLine[]>(() => loadCart());
  const [config, setConfig] = useState<Config | null>(null);

  useEffect(() => {
    if (hasInitData) tg.ready();
  }, [hasInitData]);

  useEffect(() => {
    saveCart(cart);
  }, [cart]);

  useEffect(() => {
    if (!hasInitData) return;
    api<Config>("/api/config")
      .then(setConfig)
      .catch(() => {});
  }, [hasInitData]);

  useEffect(() => {
    if (!hasInitData) return;
    if (route === "/") {
      tg.backButton.hide();
      return;
    }
    tg.backButton.show(() => window.history.back());
    return () => tg.backButton.hide();
  }, [hasInitData, route]);

  if (!hasInitData) {
    return <NoInitData />;
  }

  function addToCart(product: Product) {
    if (!product.is_available) return;
    setCart((lines) =>
      addCatalogLine(lines, {
        productId: product.id,
        name: product.name,
        sku: product.sku,
        price: product.price,
        imageUrl: product.image_url,
      })
    );
  }

  const parts = route.split("/").filter(Boolean);
  let body: React.ReactNode;
  if (parts.length === 0) {
    body = <Catalog onSelectProduct={(id) => navigate(`/product/${id}`)} onAddToCart={addToCart} onOpenCustomForm={() => navigate("/custom")} />;
  } else if (parts[0] === "product" && parts[1]) {
    body = (
      <ProductDetail
        productId={Number(parts[1])}
        onBack={() => navigate("/")}
        onAddToCart={(p) => {
          addToCart(p);
          navigate("/cart");
        }}
      />
    );
  } else if (parts[0] === "cart") {
    body = (
      <CartScreen
        cart={cart}
        onSetQuantity={(key, qty) => setCart((lines) => setQuantity(lines, key, qty))}
        onRemove={(key) => setCart((lines) => removeLine(lines, key))}
        onCheckout={() => navigate("/checkout")}
        onAddCustom={() => navigate("/custom")}
      />
    );
  } else if (parts[0] === "custom") {
    body = (
      <CustomForm
        onAdd={(data) => {
          setCart((lines) => addCustomLine(lines, data));
          navigate("/cart");
        }}
      />
    );
  } else if (parts[0] === "checkout") {
    body = (
      <Checkout
        cart={cart}
        pickupAddress={config?.pickup_address ?? ""}
        onSuccess={(orderId) => {
          setCart([]);
          navigate(`/done/${orderId}`);
        }}
      />
    );
  } else if (parts[0] === "orders") {
    body = <Orders onBackToCatalog={() => navigate("/")} />;
  } else if (parts[0] === "done" && parts[1]) {
    body = <Done orderId={Number(parts[1])} onBackToCatalog={() => navigate("/")} />;
  } else {
    body = <Catalog onSelectProduct={(id) => navigate(`/product/${id}`)} onAddToCart={addToCart} onOpenCustomForm={() => navigate("/custom")} />;
  }

  return (
    <div>
      <header>
        <Logo />
        <span>{config?.shop_name ?? t("app.title")}</span>
        <p>{config?.shop_subtitle ?? t("app.subtitle")}</p>
        <nav>
          <button onClick={() => navigate("/")}>{t("nav.catalog")}</button>
          <button onClick={() => navigate("/cart")}>{t("nav.cart")}</button>
          <button onClick={() => navigate("/orders")}>{t("nav.orders")}</button>
        </nav>
      </header>
      <main>{body}</main>
    </div>
  );
}
