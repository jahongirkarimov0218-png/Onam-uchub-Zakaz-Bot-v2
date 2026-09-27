// A local mock of the Telegram Bot API, used instead of the real network by
// the E2E run (both bots point at it via TELEGRAM_API_BASE). aiogram's
// AiohttpSession always POSTs `multipart/form-data` (even with no files), so
// this server parses multipart bodies by hand rather than JSON — no extra
// npm package is on the allowed list for this.
import http from "node:http";
import type { AddressInfo } from "node:net";

export type MockCall = {
  method: string;
  token: string;
  fields: Record<string, string>;
  at: number;
};

function parseMultipart(buffer: Buffer, contentType: string): Record<string, string> {
  const boundaryMatch = contentType.match(/boundary=(?:"([^"]+)"|([^;]+))/);
  if (!boundaryMatch) return {};
  const boundary = boundaryMatch[1] ?? boundaryMatch[2];
  const marker = Buffer.from(`--${boundary}`);
  const fields: Record<string, string> = {};

  let start = buffer.indexOf(marker);
  while (start !== -1) {
    const next = buffer.indexOf(marker, start + marker.length);
    if (next === -1) break;
    const part = buffer.subarray(start + marker.length, next);
    start = next;

    const headerEnd = part.indexOf("\r\n\r\n");
    if (headerEnd === -1) continue;
    const header = part.subarray(0, headerEnd).toString("utf8");
    const nameMatch = header.match(/name="([^"]*)"/);
    if (!nameMatch) continue;

    let content = part.subarray(headerEnd + 4);
    if (content.subarray(-2).toString("utf8") === "\r\n") {
      content = content.subarray(0, -2);
    }
    fields[nameMatch[1]] = content.toString("utf8");
  }
  return fields;
}

function jsonResponse(res: http.ServerResponse, status: number, body: unknown): void {
  const payload = JSON.stringify(body);
  res.writeHead(status, { "content-type": "application/json; charset=utf-8" });
  res.end(payload);
}

export type MockTelegramServer = {
  server: http.Server;
  port: number;
  close: () => Promise<void>;
};

export function startMockTelegram(port: number): Promise<MockTelegramServer> {
  const calls: MockCall[] = [];
  let messageId = 5000;

  const server = http.createServer((req, res) => {
    const url = req.url ?? "";

    if (url === "/__calls") {
      jsonResponse(res, 200, calls);
      return;
    }
    if (url === "/__reset" && req.method === "POST") {
      calls.length = 0;
      jsonResponse(res, 200, { ok: true });
      return;
    }

    const match = url.match(/^\/bot([^/]+)\/([A-Za-z]+)$/);
    if (!match) {
      jsonResponse(res, 404, { ok: false, description: "not found" });
      return;
    }
    const [, token, method] = match;

    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      const raw = Buffer.concat(chunks);
      const contentType = req.headers["content-type"] ?? "";
      // aiogram's AiohttpSession serializes a request with no file fields as
      // `application/x-www-form-urlencoded` (aiohttp's FormData only switches
      // to multipart once a file/filename/content_type is attached, e.g. sendPhoto).
      let fields: Record<string, string> = {};
      if (contentType.includes("multipart/form-data")) {
        fields = parseMultipart(raw, contentType);
      } else if (contentType.includes("application/x-www-form-urlencoded")) {
        fields = Object.fromEntries(new URLSearchParams(raw.toString("utf8")));
      } else if (raw.length > 0) {
        try {
          fields = JSON.parse(raw.toString("utf8"));
        } catch {
          fields = {};
        }
      }
      calls.push({ method, token, fields, at: Date.now() });

      switch (method) {
        case "getMe":
          jsonResponse(res, 200, {
            ok: true,
            result: { id: 1, is_bot: true, first_name: "Mock Bot", username: `mock_bot_${token.slice(0, 6)}` },
          });
          return;
        case "deleteWebhook":
        case "setMyCommands":
        case "answerCallbackQuery":
          jsonResponse(res, 200, { ok: true, result: true });
          return;
        case "getUpdates":
          // Short artificial wait so aiogram's polling loop doesn't hot-spin
          // against an always-empty result.
          setTimeout(() => jsonResponse(res, 200, { ok: true, result: [] }), 200);
          return;
        case "sendMessage": {
          messageId += 1;
          jsonResponse(res, 200, {
            ok: true,
            result: {
              message_id: messageId,
              date: Math.floor(Date.now() / 1000),
              chat: { id: Number(fields.chat_id), type: "private" },
              text: fields.text ?? "",
            },
          });
          return;
        }
        case "sendPhoto": {
          messageId += 1;
          jsonResponse(res, 200, {
            ok: true,
            result: {
              message_id: messageId,
              date: Math.floor(Date.now() / 1000),
              chat: { id: Number(fields.chat_id), type: "private" },
            },
          });
          return;
        }
        case "editMessageText":
        case "editMessageReplyMarkup": {
          jsonResponse(res, 200, {
            ok: true,
            result: {
              message_id: Number(fields.message_id) || messageId,
              date: Math.floor(Date.now() / 1000),
              chat: { id: Number(fields.chat_id), type: "private" },
              text: fields.text ?? "",
            },
          });
          return;
        }
        default:
          jsonResponse(res, 200, { ok: true, result: true });
      }
    });
  });

  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", () => {
      const address = server.address() as AddressInfo;
      resolve({
        server,
        port: address.port,
        close: () =>
          new Promise<void>((res) => {
            server.closeAllConnections?.();
            server.close(() => res());
          }),
      });
    });
  });
}
