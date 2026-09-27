import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { App } from "./App";

const originalTelegram = (window as unknown as { Telegram?: unknown }).Telegram;

function mockWebApp() {
  (window as unknown as { Telegram?: unknown }).Telegram = {
    WebApp: { initData: "admin-init-data", initDataUnsafe: {}, ready: vi.fn() },
  };
}

afterEach(() => {
  (window as unknown as { Telegram?: unknown }).Telegram = originalTelegram;
  window.location.hash = "";
  vi.restoreAllMocks();
});

describe("App — /api/admin/me gate", () => {
  it("shows only 'Ruxsat yo'q' and renders nothing else when /api/admin/me is 403", async () => {
    mockWebApp();
    const fetchMock = vi.fn((url: string) => {
      if (typeof url === "string" && url.startsWith("/api/admin/me")) {
        return Promise.resolve({ ok: false, status: 403, json: async () => ({ detail: "forbidden" }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => [] });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    render(<App />);

    expect(await screen.findByText("Ruxsat yo'q")).toBeInTheDocument();
    expect(screen.queryByText("Zakazlar")).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("shows 'Ruxsat yo'q' for a 401 (invalid/expired initData) too", async () => {
    mockWebApp();
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "invalid_init_data" }),
    }) as unknown as typeof fetch;

    render(<App />);

    expect(await screen.findByText("Ruxsat yo'q")).toBeInTheDocument();
  });

  it("renders the tabs and defaults to the orders tab when /api/admin/me succeeds", async () => {
    mockWebApp();
    const fetchMock = vi.fn((url: string) => {
      if (typeof url === "string" && url.startsWith("/api/admin/me")) {
        return Promise.resolve({ ok: true, status: 200, json: async () => ({ id: 1, first_name: "Admin" }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => [] });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    render(<App />);

    await waitFor(() => expect(screen.getByRole("button", { name: "Mahsulotlar" })).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Zakazlar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kategoriyalar" })).toBeInTheDocument();
  });

  it("shows a generic retryable error (not 'Ruxsat yo'q') for a 500 from /api/admin/me, and retry re-checks", async () => {
    mockWebApp();
    const fetchMock = vi.fn((url: string) => {
      if (typeof url === "string" && url.startsWith("/api/admin/me")) {
        return Promise.resolve({ ok: false, status: 500, json: async () => ({ detail: "generic" }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => [] });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    render(<App />);

    expect(await screen.findByText("Xatolik yuz berdi, qaytadan urinib ko'ring")).toBeInTheDocument();
    expect(screen.queryByText("Ruxsat yo'q")).not.toBeInTheDocument();
    const retryButton = screen.getByRole("button", { name: "Qayta urinish" });
    expect(fetchMock).toHaveBeenCalledTimes(1);

    fireEvent.click(retryButton);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });

  it("shows a generic retryable error for a network failure from /api/admin/me", async () => {
    mockWebApp();
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError("network down")) as unknown as typeof fetch;

    render(<App />);

    expect(await screen.findByText("Internet aloqasi yo'q, qaytadan urinib ko'ring")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Qayta urinish" })).toBeInTheDocument();
  });

  it("makes no API calls at all when opened outside Telegram", () => {
    (window as unknown as { Telegram?: unknown }).Telegram = { WebApp: { initData: "", initDataUnsafe: {}, ready: vi.fn() } };
    const fetchMock = vi.fn();
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    render(<App />);

    expect(fetchMock).not.toHaveBeenCalled();
  });
});
