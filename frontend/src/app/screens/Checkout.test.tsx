import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Checkout } from "./Checkout";
import type { CartLine } from "../cart";

const cart: CartLine[] = [
  { kind: "catalog", productId: 1, name: "Krem", sku: "SK-1", price: 50000, imageUrl: null, quantity: 2 },
];

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("Checkout", () => {
  it("shows an inline error and keeps the entered values when the phone is invalid", async () => {
    render(<Checkout cart={cart} pickupAddress="Toshkent, 1-ko'cha" onSuccess={vi.fn()} />);
    await userEvent.type(screen.getByLabelText("Ismingiz"), "Aziz");
    await userEvent.type(screen.getByLabelText("Telefon"), "abc");
    await userEvent.type(screen.getByLabelText("Manzil"), "Chilonzor");
    fireEvent.click(screen.getByRole("button", { name: "Buyurtma berish" }));
    expect(await screen.findByText("Telefon raqami noto'g'ri")).toBeInTheDocument();
    expect(screen.getByLabelText("Ismingiz")).toHaveValue("Aziz");
  });

  it("requires the address only for delivery and shows the pickup address for pickup", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ id: 7 }) });
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    const onSuccess = vi.fn();
    render(<Checkout cart={cart} pickupAddress="Chilonzor, 1-uy" onSuccess={onSuccess} />);
    await userEvent.type(screen.getByLabelText("Ismingiz"), "Aziz");
    await userEvent.type(screen.getByLabelText("Telefon"), "+998901234567");
    fireEvent.click(screen.getByRole("button", { name: "Buyurtma berish" }));
    expect(await screen.findByText("Manzilni kiriting")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Olib ketish"));
    expect(screen.getByText("Chilonzor, 1-uy")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Buyurtma berish" }));
    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith(7));
  });

  it("sends exactly one request when the submit button is clicked twice in a row", async () => {
    let resolveFetch: (v: unknown) => void = () => {};
    const fetchMock = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        })
    );
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    const onSuccess = vi.fn();
    render(<Checkout cart={cart} pickupAddress="Chilonzor, 1-uy" onSuccess={onSuccess} />);
    await userEvent.type(screen.getByLabelText("Ismingiz"), "Aziz");
    await userEvent.type(screen.getByLabelText("Telefon"), "+998901234567");
    fireEvent.click(screen.getByLabelText("Olib ketish"));
    const submitButton = screen.getByRole("button", { name: "Buyurtma berish" });
    fireEvent.click(submitButton);
    fireEvent.click(submitButton);
    resolveFetch({ ok: true, status: 201, json: async () => ({ id: 9 }) });
    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith(9));
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it.each(["+998 90 123 45 67", "+7 912 345 67 89"])(
    "accepts a phone number with spaces after stripping formatting: %s",
    async (rawPhone) => {
      const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 201, json: async () => ({ id: 21 }) });
      globalThis.fetch = fetchMock as unknown as typeof fetch;
      const onSuccess = vi.fn();
      render(<Checkout cart={cart} pickupAddress="Chilonzor, 1-uy" onSuccess={onSuccess} />);
      await userEvent.type(screen.getByLabelText("Ismingiz"), "Aziz");
      await userEvent.type(screen.getByLabelText("Telefon"), rawPhone);
      fireEvent.click(screen.getByLabelText("Olib ketish"));
      fireEvent.click(screen.getByRole("button", { name: "Buyurtma berish" }));
      await waitFor(() => expect(onSuccess).toHaveBeenCalledWith(21));
    }
  );

  it("keeps the form values and shows a retryable error when the request fails", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue({ ok: false, status: 500, json: async () => ({ detail: "generic" }) }) as unknown as typeof fetch;
    const onSuccess = vi.fn();
    render(<Checkout cart={cart} pickupAddress="Chilonzor, 1-uy" onSuccess={onSuccess} />);
    await userEvent.type(screen.getByLabelText("Ismingiz"), "Aziz");
    await userEvent.type(screen.getByLabelText("Telefon"), "+998901234567");
    fireEvent.click(screen.getByLabelText("Olib ketish"));
    fireEvent.click(screen.getByRole("button", { name: "Buyurtma berish" }));
    expect(await screen.findByText("Xatolik yuz berdi, qaytadan urinib ko'ring")).toBeInTheDocument();
    expect(onSuccess).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Ismingiz")).toHaveValue("Aziz");
  });
});
