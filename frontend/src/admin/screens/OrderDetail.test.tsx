import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { OrderDetail } from "./OrderDetail";

beforeEach(() => {
  vi.restoreAllMocks();
});

function detailOf(status: string) {
  return {
    id: 5,
    status,
    status_label: status,
    customer_name: "Aziz",
    phone: "+998901112233",
    delivery_type: "pickup",
    address: null,
    comment: null,
    total: 50000,
    created_at: "2026-01-01T00:00:00Z",
    items: [{ kind: "catalog", product_id: 1, name: "Krem", sku: "SK-1", image_url: null, unit_price: 50000, quantity: 1, note: null }],
    history: [
      { from_status: null as string | null, to_status: status, actor_tg_id: 1, source: "customer", created_at: "2026-01-01T00:00:00Z" },
    ],
  };
}

describe("OrderDetail", () => {
  it("shows only the single forward-transition button and the cancel button for a non-final status", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => detailOf("new") }) as unknown as typeof fetch;
    render(<OrderDetail orderId={5} onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("#5")).toBeInTheDocument());

    expect(screen.getByRole("button", { name: "Qabul qilindi" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Bekor qilish" })).toBeInTheDocument();
    // no other status buttons rendered
    expect(screen.queryByRole("button", { name: "Yetib keldi" })).not.toBeInTheDocument();
  });

  it("shows no transition buttons for a final status", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => detailOf("delivered") }) as unknown as typeof fetch;
    render(<OrderDetail orderId={5} onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("#5")).toBeInTheDocument());

    expect(screen.queryByRole("button", { name: "Bekor qilish" })).not.toBeInTheDocument();
  });

  it("requires an inline confirm before cancelling, then posts the status change and refreshes", async () => {
    const fetchMock = vi.fn((url: string, opts?: RequestInit) => {
      if (typeof url === "string" && url.endsWith("/status")) {
        expect(JSON.parse(opts!.body as string)).toEqual({ status: "cancelled" });
        return Promise.resolve({ ok: true, status: 200, json: async () => detailOf("cancelled") });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => detailOf("new") });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    render(<OrderDetail orderId={5} onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("#5")).toBeInTheDocument());

    fireEvent.click(screen.getByRole("button", { name: "Bekor qilish" }));
    expect(screen.getByText("Buyurtmani bekor qilishni tasdiqlaysizmi?")).toBeInTheDocument();
    // no status POST fired yet
    expect(fetchMock.mock.calls.some((c) => typeof c[0] === "string" && c[0].endsWith("/status"))).toBe(false);

    fireEvent.click(screen.getByRole("button", { name: "Ha, bekor qilish" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/admin/orders/5/status",
        expect.objectContaining({ method: "POST" })
      )
    );
    // refetch after the change
    await waitFor(() => expect(fetchMock.mock.calls.filter((c) => c[0] === "/api/admin/orders/5").length).toBe(2));
  });

  it("shows the uz label for the history source, not the raw code", async () => {
    const data = detailOf("accepted");
    data.history = [
      { from_status: null, to_status: "new", actor_tg_id: 1, source: "customer", created_at: "2026-01-01T00:00:00Z" },
      { from_status: "new", to_status: "accepted", actor_tg_id: 7, source: "admin_app", created_at: "2026-01-02T00:00:00Z" },
    ];
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => data }) as unknown as typeof fetch;
    render(<OrderDetail orderId={5} onBack={vi.fn()} />);
    await waitFor(() => expect(screen.getByText("#5")).toBeInTheDocument());

    expect(screen.getByText(/Mijoz/)).toBeInTheDocument();
    expect(screen.getByText(/Admin panel/)).toBeInTheDocument();
    expect(screen.queryByText(/admin_app/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\bcustomer\b/)).not.toBeInTheDocument();
  });
});
