import { describe, it, expect } from "vitest";
import { allowed, nextStatus, FINAL, statusLabel } from "./status";

describe("status machine (mirrors backend NEXT/FINAL/LABELS_UZ)", () => {
  it("allows only the documented forward transition for each non-final status", () => {
    expect(allowed("new", "accepted")).toBe(true);
    expect(allowed("accepted", "ordered")).toBe(true);
    expect(allowed("ordered", "arrived")).toBe(true);
    expect(allowed("arrived", "delivered")).toBe(true);
    expect(allowed("new", "ordered")).toBe(false);
  });

  it("allows cancelling from any non-final status but not from a final one", () => {
    expect(allowed("new", "cancelled")).toBe(true);
    expect(allowed("arrived", "cancelled")).toBe(true);
    expect(allowed("delivered", "cancelled")).toBe(false);
    expect(allowed("cancelled", "cancelled")).toBe(false);
  });

  it("exposes delivered and cancelled as the final set", () => {
    expect(FINAL.has("delivered")).toBe(true);
    expect(FINAL.has("cancelled")).toBe(true);
    expect(FINAL.has("arrived")).toBe(false);
  });

  it("nextStatus returns the single forward step or null for a final status", () => {
    expect(nextStatus("new")).toBe("accepted");
    expect(nextStatus("arrived")).toBe("delivered");
    expect(nextStatus("delivered")).toBeNull();
    expect(nextStatus("cancelled")).toBeNull();
  });

  it("statusLabel maps codes to the uz text from LABELS_UZ", () => {
    expect(statusLabel("new")).toBe("Yangi");
    expect(statusLabel("ordered")).toBe("Faberlic'ga buyurtma berildi");
    expect(statusLabel("cancelled")).toBe("Bekor qilindi");
  });
});
