import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Orders } from "./Orders";

beforeEach(() => {
  vi.restoreAllMocks();
});

function ordersResponse(data: unknown[]) {
  return Promise.resolve({ ok: true, status: 200, json: async () => data });
}

describe("Orders — filter chips and search", () => {
  it("sends no status param for 'Hammasi' and requests again with status= for a specific chip", async () => {
    const fetchMock = vi.fn(() => ordersResponse([]));
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Orders onSelectOrder={vi.fn()} />);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/admin/orders", expect.anything()));

    fireEvent.click(screen.getByRole("button", { name: "Yangi" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/api/admin/orders?status=new", expect.anything())
    );
  });

  it("filters out final statuses client-side for 'Ochiq' without sending a status param", async () => {
    const fetchMock = vi.fn(() =>
      ordersResponse([
        { id: 1, status: "new", status_label: "Yangi", customer_name: "Aziz", phone: "+998901112233", total: 1000, created_at: "2026-01-01T00:00:00Z" },
        { id: 2, status: "delivered", status_label: "Topshirildi", customer_name: "Vali", phone: "+998901112244", total: 2000, created_at: "2026-01-01T00:00:00Z" },
      ])
    );
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Orders onSelectOrder={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("#1")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Ochiq" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/admin/orders", expect.anything()));
    expect(screen.getByText("#1")).toBeInTheDocument();
    expect(screen.queryByText("#2")).not.toBeInTheDocument();
  });

  it("sends the search box text as a q param, combined with the active status chip", async () => {
    const fetchMock = vi.fn(() => ordersResponse([]));
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<Orders onSelectOrder={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Yangi" }));
    await userEvent.type(screen.getByLabelText("Raqam, telefon yoki ism bo'yicha qidirish"), "Aziz");

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/api/admin/orders?status=new&q=Aziz", expect.anything())
    );
  });

  it("calls onSelectOrder with the order id when a row is clicked", async () => {
    const fetchMock = vi.fn(() =>
      ordersResponse([
        { id: 42, status: "new", status_label: "Yangi", customer_name: "Aziz", phone: "+998901112233", total: 1000, created_at: "2026-01-01T00:00:00Z" },
      ])
    );
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    const onSelectOrder = vi.fn();
    render(<Orders onSelectOrder={onSelectOrder} />);
    await waitFor(() => expect(screen.getByText("#42")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "#42" }));
    expect(onSelectOrder).toHaveBeenCalledWith(42);
  });
});
