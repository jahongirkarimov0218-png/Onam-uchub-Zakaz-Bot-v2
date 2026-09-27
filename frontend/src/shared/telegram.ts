// Safe wrapper around window.Telegram?.WebApp. Every accessor tolerates the
// SDK being absent (dev outside Telegram, tests without a mock) by returning
// a neutral value instead of throwing.
export type TgUser = {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
};

type ContactResponse = {
  responseUnsafe?: { contact?: { phone_number?: string } };
  response?: { contact?: { phone_number?: string } };
};

type TelegramWebApp = {
  initData?: string;
  initDataUnsafe?: { user?: TgUser };
  ready?: () => void;
  expand?: () => void;
  requestContact?: (callback: (granted: boolean, response?: ContactResponse) => void) => void;
  BackButton?: {
    show?: () => void;
    hide?: () => void;
    onClick?: (fn: () => void) => void;
    offClick?: (fn: () => void) => void;
  };
  HapticFeedback?: {
    impactOccurred?: (style: string) => void;
    notificationOccurred?: (type: string) => void;
  };
};

// Module-level: the one BackButton handler currently registered with
// Telegram, so `show()`/`hide()` can always offClick the handler that is
// actually attached — not the (different) closure the caller happens to pass.
let currentBackHandler: (() => void) | null = null;

function webApp(): TelegramWebApp | undefined {
  return typeof window !== "undefined"
    ? (window as unknown as { Telegram?: { WebApp?: TelegramWebApp } }).Telegram?.WebApp
    : undefined;
}

export const tg = {
  get initData(): string {
    return webApp()?.initData ?? "";
  },
  get user(): TgUser | null {
    return webApp()?.initDataUnsafe?.user ?? null;
  },
  ready(): void {
    webApp()?.ready?.();
  },
  expand(): void {
    webApp()?.expand?.();
  },
  /** Resolves the phone number if the user grants contact access, else null. */
  requestContact(): Promise<string | null> {
    return new Promise((resolve) => {
      const app = webApp();
      if (!app?.requestContact) {
        resolve(null);
        return;
      }
      try {
        app.requestContact((granted: boolean, response?: ContactResponse) => {
          if (!granted) {
            resolve(null);
            return;
          }
          const phone =
            response?.responseUnsafe?.contact?.phone_number ??
            response?.response?.contact?.phone_number ??
            null;
          resolve(phone);
        });
      } catch {
        resolve(null);
      }
    });
  },
  backButton: {
    /** Replaces the previously registered handler (offClick'ing it first) so
     * that repeated `show()` calls with a fresh closure — e.g. once per route
     * change — never stack up listeners on Telegram's BackButton. */
    show(onClick: () => void): void {
      const bb = webApp()?.BackButton;
      if (currentBackHandler) bb?.offClick?.(currentBackHandler);
      currentBackHandler = onClick;
      bb?.onClick?.(onClick);
      bb?.show?.();
    },
    hide(): void {
      const bb = webApp()?.BackButton;
      if (currentBackHandler) bb?.offClick?.(currentBackHandler);
      currentBackHandler = null;
      bb?.hide?.();
    },
  },
  haptic: {
    impact(style: "light" | "medium" | "heavy" = "light"): void {
      webApp()?.HapticFeedback?.impactOccurred?.(style);
    },
    notification(type: "error" | "success" | "warning" = "success"): void {
      webApp()?.HapticFeedback?.notificationOccurred?.(type);
    },
  },
};
