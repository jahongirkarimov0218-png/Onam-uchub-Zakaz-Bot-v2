import { describe, it, expect, beforeEach, vi } from "vitest";
import { tg } from "./telegram";

type BackButtonMock = {
  onClick: ReturnType<typeof vi.fn>;
  offClick: ReturnType<typeof vi.fn>;
  show: ReturnType<typeof vi.fn>;
  hide: ReturnType<typeof vi.fn>;
  handlers: Set<() => void>;
};

function mockBackButton(): BackButtonMock {
  const handlers = new Set<() => void>();
  const onClick = vi.fn((fn: () => void) => handlers.add(fn));
  const offClick = vi.fn((fn: () => void) => handlers.delete(fn));
  const show = vi.fn();
  const hide = vi.fn();
  (window as unknown as { Telegram?: unknown }).Telegram = {
    WebApp: { BackButton: { onClick, offClick, show, hide } },
  };
  return { onClick, offClick, show, hide, handlers };
}

beforeEach(() => {
  // Clear any handler the wrapper still remembers from a previous test before
  // wiping window.Telegram, and start each test with no Telegram at all.
  tg.backButton.hide();
  (window as unknown as { Telegram?: unknown }).Telegram = undefined;
});

describe("tg.backButton — no listener leak across repeated show() calls (regression)", () => {
  it("keeps exactly one registered handler after several show() calls with a fresh closure each time", () => {
    const bb = mockBackButton();
    const first = vi.fn();
    const second = vi.fn();
    const third = vi.fn();

    tg.backButton.show(first);
    tg.backButton.show(second);
    tg.backButton.show(third);

    expect(bb.handlers.size).toBe(1);
    for (const handler of bb.handlers) handler();
    expect(first).not.toHaveBeenCalled();
    expect(second).not.toHaveBeenCalled();
    expect(third).toHaveBeenCalledTimes(1);
  });

  it("hide() unregisters the current handler so a later show() starts from zero listeners", () => {
    const bb = mockBackButton();
    const handler = vi.fn();
    tg.backButton.show(handler);
    tg.backButton.hide();
    expect(bb.handlers.size).toBe(0);
    expect(bb.offClick).toHaveBeenCalledWith(handler);
  });
});
