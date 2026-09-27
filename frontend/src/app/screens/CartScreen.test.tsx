import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CartScreen } from "./CartScreen";
import { setQuantity, type CartLine } from "../cart";

describe("CartScreen — quantity controls", () => {
  it("clamps quantity to 99 via the + button, which has an accessible label", () => {
    let cart: CartLine[] = [
      { kind: "catalog", productId: 1, name: "Krem", sku: "SK-1", price: 1000, imageUrl: null, quantity: 99 },
    ];
    const onSetQuantity = vi.fn((key: string, qty: number) => {
      cart = setQuantity(cart, key, qty);
    });
    render(
      <CartScreen cart={cart} onSetQuantity={onSetQuantity} onRemove={vi.fn()} onCheckout={vi.fn()} onAddCustom={vi.fn()} />
    );
    fireEvent.click(screen.getByLabelText("Ko'paytirish"));
    expect(cart[0].quantity).toBe(99);
  });

  it("clamps quantity to 1 via the - button, which has an accessible label", () => {
    let cart: CartLine[] = [
      { kind: "catalog", productId: 1, name: "Krem", sku: "SK-1", price: 1000, imageUrl: null, quantity: 1 },
    ];
    const onSetQuantity = vi.fn((key: string, qty: number) => {
      cart = setQuantity(cart, key, qty);
    });
    render(
      <CartScreen cart={cart} onSetQuantity={onSetQuantity} onRemove={vi.fn()} onCheckout={vi.fn()} onAddCustom={vi.fn()} />
    );
    fireEvent.click(screen.getByLabelText("Kamaytirish"));
    expect(cart[0].quantity).toBe(1);
  });

  it("shows an i18n custom-item label for a photo-only custom line instead of the cart title", () => {
    const cart: CartLine[] = [
      { kind: "custom", id: "1", name: null, sku: null, uploadId: 5, imageUrl: "/u/5", note: null, quantity: 1 },
    ];
    render(
      <CartScreen cart={cart} onSetQuantity={vi.fn()} onRemove={vi.fn()} onCheckout={vi.fn()} onAddCustom={vi.fn()} />
    );
    expect(screen.getByText("Katalogda yo'q mahsulot")).toBeInTheDocument();
  });
});
