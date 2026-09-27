import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Catalog } from "./Catalog";

const categories = [{ id: 1, name: "Kremlar" }];

function mockFetch(products: unknown[]) {
  return vi.fn((url: string) => {
    if (url.startsWith("/api/categories")) {
      return Promise.resolve({ ok: true, status: 200, json: async () => categories });
    }
    return Promise.resolve({ ok: true, status: 200, json: async () => products });
  });
}

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Catalog", () => {
  it("calls the API with category_id and then with q when filtering and searching", async () => {
    const fetchMock = mockFetch([]);
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Catalog onSelectProduct={vi.fn()} onAddToCart={vi.fn()} onOpenCustomForm={vi.fn()} />);

    fireEvent.click(await screen.findByText("Kremlar"));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("category_id=1"), expect.anything())
    );

    await userEvent.type(screen.getByLabelText("Nom yoki artikul bo'yicha qidirish"), "krem");
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("q=krem"), expect.anything())
    );
  });

  it("disables add-to-cart for an unavailable product", async () => {
    const product = {
      id: 1,
      category_id: 1,
      name: "Yog'",
      sku: "SK-2",
      price: 1000,
      description: "",
      image_url: null,
      is_available: false,
    };
    globalThis.fetch = mockFetch([product]) as unknown as typeof fetch;
    render(<Catalog onSelectProduct={vi.fn()} onAddToCart={vi.fn()} onOpenCustomForm={vi.fn()} />);
    const button = await screen.findByRole("button", { name: "Mavjud emas" });
    expect(button).toBeDisabled();
  });

  it("shows the empty state with a link to the custom form when there are no products", async () => {
    globalThis.fetch = mockFetch([]) as unknown as typeof fetch;
    const onOpenCustomForm = vi.fn();
    render(<Catalog onSelectProduct={vi.fn()} onAddToCart={vi.fn()} onOpenCustomForm={onOpenCustomForm} />);
    expect(await screen.findByText("Hech narsa topilmadi")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Katalogda yo'q mahsulot uchun forma"));
    expect(onOpenCustomForm).toHaveBeenCalled();
  });
});
