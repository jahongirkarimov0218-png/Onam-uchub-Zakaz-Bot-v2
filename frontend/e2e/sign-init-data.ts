// Signs a Telegram WebApp initData string in Node, using the exact same
// algorithm as `backend/app/auth.py` (`validate_init_data`) and
// `backend/tests/conftest.py` (`sign_init_data`):
//   secret_key = HMAC_SHA256("WebAppData", bot_token)
//   hash = HMAC_SHA256(secret_key, "\n".join(sorted "key=value" pairs))
import { createHmac } from "node:crypto";

export type SignInitDataUser = {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
};

export function signInitData(user: SignInitDataUser, botToken: string, authDate?: number): string {
  const data: Record<string, string> = {
    query_id: "AAHe2etestquery",
    user: JSON.stringify(user),
    auth_date: String(authDate ?? Math.floor(Date.now() / 1000)),
  };

  const checkString = Object.keys(data)
    .sort()
    .map((key) => `${key}=${data[key]}`)
    .join("\n");

  const secretKey = createHmac("sha256", "WebAppData").update(botToken).digest();
  const hash = createHmac("sha256", secretKey).update(checkString).digest("hex");

  const params = new URLSearchParams({ ...data, hash });
  return params.toString();
}
