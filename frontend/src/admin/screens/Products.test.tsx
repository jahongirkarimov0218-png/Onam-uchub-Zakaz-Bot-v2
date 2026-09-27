import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Products } from "./Products";

beforeEach(() => {
  vi.restoreAllMocks();
});

const categories = [{ id: 1, name: "Parfyumeriya" }];
const products = [
  { id: 10, category_id: 1, name: "Krem", sku: "SK-1", price: 50000, description: "", image_url: null, is_available: true },
  { id: 11, category_id: 1, name: "Sovun", sku: "SK-2", price: 15000, description: "", image_url: null, is_available: false },
];

function mockFetch(overrides: Record<string, () => Promise<unknown>> = {}) {
  return vi.fn((url: string, opts?: RequestInit) => {
    const method = opts?.method ?? "GET";
    const key = `${method} ${url}`;
    for (const [pattern, handler] of Object.entries(overrides)) {
      if (key === pattern || url === pattern) {
        return handler().then((json) => ({ ok: true, status: 200, json: async () => json }));
      }
    }
    if (url === "/api/admin/categories") return Promise.resolve({ ok: true, status: 200, json: async () => categories });
    if (url.startsWith("/api/admin/products")) return Promise.resolve({ ok: true, status: 200, json: async () => products });
    return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
  });
}

describe("Products", () => {
  it("shows the unavailable badge and lists all products including unavailable ones", async () => {
    globalThis.fetch = mockFetch() as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Krem")).toBeInTheDocument());
    expect(screen.getByText("Sovun")).toBeInTheDocument();
    expect(screen.getAllByText("Mavjud emas")[0]).toBeInTheDocument();
  });

  it("creates a product via POST /api/admin/products with the form fields", async () => {
    const fetchMock = mockFetch({
      "POST /api/admin/products": () => Promise.resolve({ ...products[0], id: 20 }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Krem")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Yangi mahsulot" }));
    await userEvent.selectOptions(screen.getByLabelText("Kategoriya"), "1");
    await userEvent.type(screen.getByLabelText("Nomi"), "Yangi krem");
    await userEvent.type(screen.getByLabelText("Artikul"), "SK-9");
    await userEvent.type(screen.getByLabelText("Narxi"), "10000");
    fireEvent.click(screen.getByRole("button", { name: "Saqlash" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/admin/products",
        expect.objectContaining({ method: "POST" })
      )
    );
    const call = fetchMock.mock.calls.find((c) => c[0] === "/api/admin/products" && c[1]?.method === "POST");
    expect(JSON.parse(call![1]!.body as string)).toMatchObject({
      category_id: 1,
      name: "Yangi krem",
      sku: "SK-9",
      price: 10000,
    });
  });

  it("edits a product via PATCH, pre-filling the form from the list", async () => {
    const fetchMock = mockFetch({
      "PATCH /api/admin/products/10": () => Promise.resolve({ ...products[0], name: "Krem 2" }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Krem")).toBeInTheDocument());

    fireEvent.click(screen.getAllByRole("button", { name: "Tahrirlash" })[0]);
    expect(screen.getByLabelText("Nomi")).toHaveValue("Krem");
    await userEvent.clear(screen.getByLabelText("Nomi"));
    await userEvent.type(screen.getByLabelText("Nomi"), "Krem 2");
    fireEvent.click(screen.getByRole("button", { name: "Saqlash" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/admin/products/10",
        expect.objectContaining({ method: "PATCH" })
      )
    );
  });

  it("uploads and previews an image before saving", async () => {
    const fetchMock = mockFetch({
      "POST /api/admin/uploads": () => Promise.resolve({ upload_id: 77, url: "/uploads/x.png" }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Krem")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Yangi mahsulot" }));

    const file = new File(["x"], "photo.png", { type: "image/png" });
    const input = screen.getByLabelText("Rasm") as HTMLInputElement;
    await userEvent.upload(input, file);

    const preview = await screen.findByAltText("Yuklangan rasm");
    expect(preview).toHaveAttribute("src", "/uploads/x.png");
  });

  it("toggles availability via PATCH", async () => {
    const fetchMock = mockFetch({
      "PATCH /api/admin/products/10": () => Promise.resolve({ ...products[0], is_available: false }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Krem")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Mavjud emas qilish" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/admin/products/10",
        expect.objectContaining({ method: "PATCH" })
      )
    );
    const call = fetchMock.mock.calls.find((c) => c[0] === "/api/admin/products/10" && c[1]?.method === "PATCH");
    expect(JSON.parse(call![1]!.body as string)).toEqual({ is_available: false });
  });

  it("deletes a product only after the inline confirm step (no window.confirm)", async () => {
    const fetchMock = mockFetch({
      "DELETE /api/admin/products/11": () => Promise.resolve(undefined),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Sovun")).toBeInTheDocument());

    const deleteButtons = screen.getAllByRole("button", { name: "O'chirish" });
    fireEvent.click(deleteButtons[1]);
    expect(screen.getByText("Mahsulotni o'chirishni tasdiqlaysizmi?")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some((c) => c[1]?.method === "DELETE")).toBe(false);

    fireEvent.click(screen.getByRole("button", { name: "Ha, o'chirish" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/admin/products/11",
        expect.objectContaining({ method: "DELETE" })
      )
    );
  });

  it("sends exactly one PATCH request when the availability toggle is double-clicked rapidly", async () => {
    let resolvePatch: (v: unknown) => void = () => {};
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (url === "/api/admin/products/10" && opts?.method === "PATCH") {
        return new Promise((resolve) => {
          resolvePatch = resolve;
        });
      }
      if (url === "/api/admin/categories") return Promise.resolve({ ok: true, status: 200, json: async () => categories });
      return Promise.resolve({ ok: true, status: 200, json: async () => products });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Krem")).toBeInTheDocument());

    const toggleButton = screen.getByRole("button", { name: "Mavjud emas qilish" });
    fireEvent.click(toggleButton);
    fireEvent.click(toggleButton);
    resolvePatch({ ok: true, status: 200, json: async () => ({ ...products[0], is_available: false }) });

    await waitFor(() =>
      expect(fetchMock.mock.calls.filter((c) => c[0] === "/api/admin/products/10" && c[1]?.method === "PATCH")).toHaveLength(1)
    );
  });

  it("sends exactly one DELETE request when the confirm-delete button is double-clicked rapidly", async () => {
    let resolveDelete: (v: unknown) => void = () => {};
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (url === "/api/admin/products/11" && opts?.method === "DELETE") {
        return new Promise((resolve) => {
          resolveDelete = resolve;
        });
      }
      if (url === "/api/admin/categories") return Promise.resolve({ ok: true, status: 200, json: async () => categories });
      return Promise.resolve({ ok: true, status: 200, json: async () => products });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Sovun")).toBeInTheDocument());

    fireEvent.click(screen.getAllByRole("button", { name: "O'chirish" })[1]);
    const confirmButton = screen.getByRole("button", { name: "Ha, o'chirish" });
    fireEvent.click(confirmButton);
    fireEvent.click(confirmButton);
    resolveDelete({ ok: true, status: 204, json: async () => undefined });

    await waitFor(() =>
      expect(fetchMock.mock.calls.filter((c) => c[0] === "/api/admin/products/11" && c[1]?.method === "DELETE")).toHaveLength(1)
    );
  });

  it("sends description: null when the description field is cleared in the edit form", async () => {
    const withDescription = { ...products[0], description: "Eski tavsif" };
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (url === "/api/admin/products/10" && opts?.method === "PATCH") {
        return Promise.resolve({ ok: true, status: 200, json: async () => ({ ...withDescription, description: null }) });
      }
      if (url === "/api/admin/categories") return Promise.resolve({ ok: true, status: 200, json: async () => categories });
      return Promise.resolve({ ok: true, status: 200, json: async () => [withDescription, products[1]] });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Krem")).toBeInTheDocument());

    fireEvent.click(screen.getAllByRole("button", { name: "Tahrirlash" })[0]);
    expect(screen.getByLabelText("Tavsif")).toHaveValue("Eski tavsif");
    await userEvent.clear(screen.getByLabelText("Tavsif"));
    fireEvent.click(screen.getByRole("button", { name: "Saqlash" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/api/admin/products/10", expect.objectContaining({ method: "PATCH" }))
    );
    const call = fetchMock.mock.calls.find((c) => c[0] === "/api/admin/products/10" && c[1]?.method === "PATCH");
    expect(JSON.parse(call![1]!.body as string)).toMatchObject({ description: null });
  });

  it("shows an inline validation message and sends no request when no category is selected", async () => {
    const fetchMock = mockFetch();
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Krem")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Yangi mahsulot" }));
    await userEvent.type(screen.getByLabelText("Nomi"), "Yangi krem");
    await userEvent.type(screen.getByLabelText("Artikul"), "SK-9");
    await userEvent.type(screen.getByLabelText("Narxi"), "10000");
    fireEvent.click(screen.getByRole("button", { name: "Saqlash" }));

    expect(await screen.findByText("Kategoriyani tanlang")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some((c) => c[1]?.method === "POST")).toBe(false);
  });

  it("shows an inline validation message and sends no request when price is empty", async () => {
    const fetchMock = mockFetch();
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Products />);
    await waitFor(() => expect(screen.getByText("Krem")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Yangi mahsulot" }));
    await userEvent.selectOptions(screen.getByLabelText("Kategoriya"), "1");
    await userEvent.type(screen.getByLabelText("Nomi"), "Yangi krem");
    await userEvent.type(screen.getByLabelText("Artikul"), "SK-9");
    fireEvent.click(screen.getByRole("button", { name: "Saqlash" }));

    expect(await screen.findByText("Narxni kiriting")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some((c) => c[1]?.method === "POST")).toBe(false);
  });
});
