import { tg } from "./telegram";
import { t, uz } from "./i18n/uz";

export type ApiOptions = {
  method?: string;
  body?: unknown | FormData;
  headers?: Record<string, string>;
};

const KNOWN_CODES = uz.errors as Record<string, string>;

/** Typed API error: `code` is the machine code from `{"detail": code}` (or
 * "network" / "generic"), `message` is the uz text mapped from i18n. */
export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string) {
    super(KNOWN_CODES[code] ?? t("errors.generic"));
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

/** Fetch wrapper: adds `Authorization: tma <initData>`, JSON-encodes plain
 * bodies (FormData passes through untouched), maps error responses to
 * ApiError with an i18n-mapped message. */
export async function api<T>(path: string, opts: ApiOptions = {}): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && opts.body instanceof FormData;
  const headers: Record<string, string> = { ...opts.headers };
  if (tg.initData) headers["Authorization"] = `tma ${tg.initData}`;
  if (!isFormData && opts.body !== undefined) headers["Content-Type"] = "application/json";

  let response: Response;
  try {
    response = await fetch(path, {
      method: opts.method ?? (opts.body !== undefined ? "POST" : "GET"),
      headers,
      body: isFormData ? (opts.body as FormData) : opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
    });
  } catch {
    throw new ApiError(0, "network");
  }

  if (!response.ok) {
    let code = "generic";
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") code = data.detail;
    } catch {
      // no JSON body — keep generic
    }
    if (response.status === 429 && code === "generic") code = "rate_limited";
    throw new ApiError(response.status, code);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
