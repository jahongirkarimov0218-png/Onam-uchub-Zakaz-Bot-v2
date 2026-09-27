import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CustomForm } from "./CustomForm";

beforeEach(() => {
  vi.restoreAllMocks();
});

describe("CustomForm", () => {
  it("shows a validation message and does not add to cart when name, sku and photo are all empty", async () => {
    const onAdd = vi.fn();
    render(<CustomForm onAdd={onAdd} />);
    await userEvent.click(screen.getByRole("button", { name: "Savatga qo'shish" }));
    expect(
      await screen.findByText("Nomi, artikul yoki rasmdan kamida bittasini kiriting")
    ).toBeInTheDocument();
    expect(onAdd).not.toHaveBeenCalled();
  });

  it("shows the uz error text when the immediate photo upload is rejected as too large", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 413,
      json: async () => ({ detail: "file_too_large" }),
    }) as unknown as typeof fetch;
    render(<CustomForm onAdd={vi.fn()} />);
    const file = new File(["x"], "photo.png", { type: "image/png" });
    const input = screen.getByLabelText("Rasm") as HTMLInputElement;
    await userEvent.upload(input, file);
    expect(
      await screen.findByText("Fayl hajmi juda katta (5 MB dan oshmasligi kerak)")
    ).toBeInTheDocument();
  });

  it("shows the uz error text when the immediate photo upload is rejected as an unsupported type", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 415,
      json: async () => ({ detail: "unsupported_file_type" }),
    }) as unknown as typeof fetch;
    render(<CustomForm onAdd={vi.fn()} />);
    const file = new File(["x"], "photo.bmp", { type: "image/bmp" });
    const input = screen.getByLabelText("Rasm") as HTMLInputElement;
    await userEvent.upload(input, file);
    expect(
      await screen.findByText("Fayl turi qo'llab-quvvatlanmaydi")
    ).toBeInTheDocument();
  });
});
