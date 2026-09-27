import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { loadCart } from "./cart";

describe("App — opened outside Telegram", () => {
  const originalTelegram = (window as unknown as { Telegram?: unknown }).Telegram;

  afterEach(() => {
    (window as unknown as { Telegram?: unknown }).Telegram = originalTelegram;
  });

  it("shows the open-in-Telegram screen and makes no API calls when initData is empty", () => {
    (window as unknown as { Telegram?: unknown }).Telegram = {
      WebApp: { initData: "", initDataUnsafe: {}, ready: vi.fn() },
    };
    const fetchMock = vi.fn();
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    render(<App />);

    expect(screen.getByText("Iltimos, do'konni Telegram orqali oching")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

function configFetch() {
  return vi.fn((url: string) => {
    if (typeof url === "string" && url.startsWith("/api/config")) {
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({ shop_name: "Do'kon", shop_subtitle: "", pickup_address: "Manzil, 1" }),
      });
    }
    return Promise.resolve({ ok: true, status: 200, json: async () => [] });
  });
}

describe("App — Telegram BackButton", () => {
  const originalTelegram = (window as unknown as { Telegram?: unknown }).Telegram;

  function mockWebApp() {
    const backButton = { show: vi.fn(), hide: vi.fn(), onClick: vi.fn(), offClick: vi.fn() };
    (window as unknown as { Telegram?: unknown }).Telegram = {
      WebApp: {
        initData: "abc",
        initDataUnsafe: {},
        ready: vi.fn(),
        BackButton: backButton,
      },
    };
    return backButton;
  }

  beforeEach(() => {
    localStorage.clear();
    globalThis.fetch = configFetch() as unknown as typeof fetch;
  });

  afterEach(() => {
    (window as unknown as { Telegram?: unknown }).Telegram = originalTelegram;
    window.location.hash = "";
  });

  it("hides the BackButton on the root route", async () => {
    const backButton = mockWebApp();
    window.location.hash = "#/";
    render(<App />);
    await waitFor(() => expect(backButton.hide).toHaveBeenCalled());
    expect(backButton.show).not.toHaveBeenCalled();
  });

  it("shows the BackButton on a non-root route and goes back in history when clicked", async () => {
    const backButton = mockWebApp();
    window.location.hash = "#/cart";
    const backSpy = vi.spyOn(window.history, "back").mockImplementation(() => {});
    render(<App />);
    await waitFor(() => expect(backButton.show).toHaveBeenCalled());
    const onClick = backButton.onClick.mock.calls[0][0];
    onClick();
    expect(backSpy).toHaveBeenCalled();
    backSpy.mockRestore();
  });
});

describe("App — order submission and the cart", () => {
  const originalTelegram = (window as unknown as { Telegram?: unknown }).Telegram;

  beforeEach(() => {
    localStorage.clear();
    (window as unknown as { Telegram?: unknown }).Telegram = {
      WebApp: {
        initData: "abc",
        initDataUnsafe: { user: { id: 1, first_name: "Aziz" } },
        ready: vi.fn(),
      },
    };
    localStorage.setItem(
      "onam-cart-v1",
      JSON.stringify([
        { kind: "catalog", productId: 1, name: "Krem", sku: "SK-1", price: 50000, imageUrl: null, quantity: 2 },
      ])
    );
    window.location.hash = "#/checkout";
  });

  afterEach(() => {
    (window as unknown as { Telegram?: unknown }).Telegram = originalTelegram;
    window.location.hash = "";
  });

  it("clears the cart and navigates to the done screen on a successful order", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (typeof url === "string" && url.startsWith("/api/config")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ shop_name: "Do'kon", shop_subtitle: "", pickup_address: "Manzil, 1" }),
        });
      }
      if (typeof url === "string" && url.startsWith("/api/orders")) {
        return Promise.resolve({ ok: true, status: 201, json: async () => ({ id: 5 }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => [] });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    render(<App />);
    await userEvent.type(screen.getByLabelText("Telefon"), "+998901234567");
    fireEvent.click(screen.getByLabelText("Olib ketish"));
    fireEvent.click(screen.getByRole("button", { name: "Buyurtma berish" }));

    await waitFor(() => expect(window.location.hash).toBe("#/done/5"));
    expect(loadCart()).toEqual([]);
  });

  it("keeps the cart when the order submission fails", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (typeof url === "string" && url.startsWith("/api/config")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ shop_name: "Do'kon", shop_subtitle: "", pickup_address: "Manzil, 1" }),
        });
      }
      if (typeof url === "string" && url.startsWith("/api/orders")) {
        return Promise.resolve({ ok: false, status: 500, json: async () => ({ detail: "generic" }) });
      }
      return Promise.resolve({ ok: true, status: 200, json: async () => [] });
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    render(<App />);
    await userEvent.type(screen.getByLabelText("Telefon"), "+998901234567");
    fireEvent.click(screen.getByLabelText("Olib ketish"));
    fireEvent.click(screen.getByRole("button", { name: "Buyurtma berish" }));

    expect(await screen.findByText("Xatolik yuz berdi, qaytadan urinib ko'ring")).toBeInTheDocument();
    expect(loadCart()).toHaveLength(1);
  });
});
