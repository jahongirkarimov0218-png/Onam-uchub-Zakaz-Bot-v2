import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Categories } from "./Categories";

beforeEach(() => {
  vi.restoreAllMocks();
});

const categories = [{ id: 1, name: "Parfyumeriya" }];

describe("Categories", () => {
  it("creates a category via POST", async () => {
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (opts?.method === "POST") return Promise.resolve({ ok: true, status: 201, json: async () => ({ id: 2, name: "Kosmetika" }) });
      return Promise.resolve({ ok: true, status: 200, json: async () => categories });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Categories />);
    await waitFor(() => expect(screen.getByText("Parfyumeriya")).toBeInTheDocument());

    await userEvent.type(screen.getByLabelText("Kategoriya nomi"), "Kosmetika");
    fireEvent.click(screen.getByRole("button", { name: "Qo'shish" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/api/admin/categories", expect.objectContaining({ method: "POST" }))
    );
  });

  it("renames a category inline via PATCH", async () => {
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (opts?.method === "PATCH") return Promise.resolve({ ok: true, status: 200, json: async () => ({ id: 1, name: "Yangi nom" }) });
      return Promise.resolve({ ok: true, status: 200, json: async () => categories });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Categories />);
    await waitFor(() => expect(screen.getByText("Parfyumeriya")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Nomlash" }));
    const input = screen.getByLabelText("Nomlash");
    await userEvent.clear(input);
    await userEvent.type(input, "Yangi nom");
    fireEvent.click(screen.getByRole("button", { name: "Saqlash" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/api/admin/categories/1", expect.objectContaining({ method: "PATCH" }))
    );
  });

  it("shows the uz message when deleting a non-empty category (409 category_not_empty)", async () => {
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (opts?.method === "DELETE") {
        return Promise.resolve({ ok: false, status: 409, json: async () => ({ detail: "category_not_empty" }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => categories });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Categories />);
    await waitFor(() => expect(screen.getByText("Parfyumeriya")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "O'chirish" }));
    fireEvent.click(screen.getByRole("button", { name: "Ha, o'chirish" }));

    expect(await screen.findByText("Kategoriyada mahsulotlar bor")).toBeInTheDocument();
  });

  it("does not send DELETE before the inline confirm step is accepted", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => categories });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Categories />);
    await waitFor(() => expect(screen.getByText("Parfyumeriya")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "O'chirish" }));
    expect(screen.getByText("Kategoriyani o'chirishni tasdiqlaysizmi?")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some((c) => c[1]?.method === "DELETE")).toBe(false);
  });

  it("sends exactly one POST when the add button is double-clicked rapidly", async () => {
    let resolvePost: (v: unknown) => void = () => {};
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (opts?.method === "POST") {
        return new Promise((resolve) => {
          resolvePost = resolve;
        });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => categories });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Categories />);
    await waitFor(() => expect(screen.getByText("Parfyumeriya")).toBeInTheDocument());

    await userEvent.type(screen.getByLabelText("Kategoriya nomi"), "Kosmetika");
    const addButton = screen.getByRole("button", { name: "Qo'shish" });
    fireEvent.click(addButton);
    fireEvent.click(addButton);
    resolvePost({ ok: true, status: 201, json: async () => ({ id: 2, name: "Kosmetika" }) });

    await waitFor(() =>
      expect(fetchMock.mock.calls.filter((c) => c[0] === "/api/admin/categories" && c[1]?.method === "POST")).toHaveLength(1)
    );
  });

  it("sends exactly one PATCH when the inline rename save is double-clicked rapidly", async () => {
    let resolvePatch: (v: unknown) => void = () => {};
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (opts?.method === "PATCH") {
        return new Promise((resolve) => {
          resolvePatch = resolve;
        });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => categories });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Categories />);
    await waitFor(() => expect(screen.getByText("Parfyumeriya")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Nomlash" }));
    await userEvent.type(screen.getByLabelText("Nomlash"), " 2");
    const saveButton = screen.getByRole("button", { name: "Saqlash" });
    fireEvent.click(saveButton);
    fireEvent.click(saveButton);
    resolvePatch({ ok: true, status: 200, json: async () => ({ id: 1, name: "Parfyumeriya 2" }) });

    await waitFor(() =>
      expect(fetchMock.mock.calls.filter((c) => c[0] === "/api/admin/categories/1" && c[1]?.method === "PATCH")).toHaveLength(1)
    );
  });

  it("sends exactly one DELETE when the confirm-delete button is double-clicked rapidly", async () => {
    let resolveDelete: (v: unknown) => void = () => {};
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (opts?.method === "DELETE") {
        return new Promise((resolve) => {
          resolveDelete = resolve;
        });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => categories });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Categories />);
    await waitFor(() => expect(screen.getByText("Parfyumeriya")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "O'chirish" }));
    const confirmButton = screen.getByRole("button", { name: "Ha, o'chirish" });
    fireEvent.click(confirmButton);
    fireEvent.click(confirmButton);
    resolveDelete({ ok: true, status: 204, json: async () => undefined });

    await waitFor(() =>
      expect(fetchMock.mock.calls.filter((c) => c[0] === "/api/admin/categories/1" && c[1]?.method === "DELETE")).toHaveLength(1)
    );
  });
});
