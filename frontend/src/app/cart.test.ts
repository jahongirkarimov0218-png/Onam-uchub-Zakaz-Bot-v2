import { describe, it, expect, beforeEach } from "vitest";
import {
  loadCart,
  saveCart,
  cartTotal,
  addCatalogLine,
  addCustomLine,
  setQuantity,
  removeLine,
  lineKey,
} from "./cart";

const product = { productId: 1, name: "Krem", sku: "SK-1", price: 50000, imageUrl: null };

beforeEach(() => {
  localStorage.clear();
});

describe("cart", () => {
  it("adds a catalog product with default quantity 1", () => {
    const lines = addCatalogLine([], product);
    expect(lines).toEqual([
      { kind: "catalog", productId: 1, name: "Krem", sku: "SK-1", price: 50000, imageUrl: null, quantity: 1 },
    ]);
  });

  it("merges the same catalog product by increasing quantity instead of duplicating", () => {
    let lines = addCatalogLine([], product);
    lines = addCatalogLine(lines, product);
    expect(lines).toHaveLength(1);
    expect(lines[0].quantity).toBe(2);
  });

  it("clamps quantity to the 1..99 range", () => {
    let lines = addCatalogLine([], product);
    lines = setQuantity(lines, lineKey(lines[0]), 500);
    expect(lines[0].quantity).toBe(99);
    lines = setQuantity(lines, lineKey(lines[0]), 0);
    expect(lines[0].quantity).toBe(1);
  });

  it("removes a line", () => {
    let lines = addCatalogLine([], product);
    lines = removeLine(lines, lineKey(lines[0]));
    expect(lines).toEqual([]);
  });

  it("computes total from catalog lines only, excluding custom lines", () => {
    let lines = addCatalogLine([], product); // 50000 x1
    lines = setQuantity(lines, lineKey(lines[0]), 3); // 150000
    lines = addCustomLine(lines, { name: "Noma'lum", sku: null, uploadId: null, imageUrl: null, note: null, quantity: 2 });
    expect(cartTotal(lines)).toBe(150000);
    expect(lines).toHaveLength(2);
  });

  it("persists across save/load (simulated remount)", () => {
    const lines = addCatalogLine([], product);
    saveCart(lines);
    expect(loadCart()).toEqual(lines);
  });

  it("returns an empty cart when localStorage content is corrupt JSON", () => {
    localStorage.setItem("onam-cart-v1", "{not valid json");
    expect(loadCart()).toEqual([]);
  });

  it("returns an empty cart when localStorage content is valid JSON but not an array", () => {
    localStorage.setItem("onam-cart-v1", JSON.stringify({ foo: "bar" }));
    expect(loadCart()).toEqual([]);
  });
});
