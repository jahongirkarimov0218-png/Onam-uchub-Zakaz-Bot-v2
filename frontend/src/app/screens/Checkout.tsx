import { useState } from "react";
import { api, ApiError } from "../../shared/api";
import { t } from "../../shared/i18n/uz";
import { tg } from "../../shared/telegram";
import type { CartLine } from "../cart";

const PHONE_RE = /^(\+998\d{9}|\+?\d{9,15})$/;

/** Strips spaces, dashes and parentheses before validation/submission. */
function normalizePhone(raw: string): string {
  return raw.trim().replace(/[\s\-()]/g, "");
}

function defaultName(): string {
  const user = tg.user;
  if (!user) return "";
  return [user.first_name, user.last_name].filter(Boolean).join(" ");
}

function buildItems(cart: CartLine[]) {
  return cart.map((line) =>
    line.kind === "catalog"
      ? { product_id: line.productId, quantity: line.quantity }
      : {
          custom: {
            name: line.name ?? undefined,
            sku: line.sku ?? undefined,
            upload_id: line.uploadId ?? undefined,
            note: line.note ?? undefined,
          },
          quantity: line.quantity,
        }
  );
}

type DeliveryType = "delivery" | "pickup";

export function Checkout({
  cart,
  pickupAddress,
  onSuccess,
}: {
  cart: CartLine[];
  pickupAddress: string;
  onSuccess: (orderId: number) => void;
}) {
  const [name, setName] = useState(defaultName());
  const [phone, setPhone] = useState("");
  const [deliveryType, setDeliveryType] = useState<DeliveryType>("delivery");
  const [address, setAddress] = useState("");
  const [comment, setComment] = useState("");
  const [sending, setSending] = useState(false);
  const [fieldError, setFieldError] = useState<{ field: string; text: string } | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleContact() {
    const phoneNumber = await tg.requestContact();
    if (phoneNumber) setPhone(phoneNumber);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (sending) return;
    if (!name.trim()) {
      setFieldError({ field: "name", text: t("checkout.nameRequired") });
      return;
    }
    const normalizedPhone = normalizePhone(phone);
    if (!PHONE_RE.test(normalizedPhone)) {
      setFieldError({ field: "phone", text: t("checkout.phoneInvalid") });
      return;
    }
    if (deliveryType === "delivery" && !address.trim()) {
      setFieldError({ field: "address", text: t("checkout.addressRequired") });
      return;
    }
    if (comment.length > 500) {
      setFieldError({ field: "comment", text: t("checkout.commentTooLong") });
      return;
    }
    setFieldError(null);
    setSubmitError(null);
    setSending(true);
    try {
      const order = await api<{ id: number }>("/api/orders", {
        method: "POST",
        body: {
          customer_name: name.trim(),
          phone: normalizedPhone,
          delivery_type: deliveryType,
          address: deliveryType === "delivery" ? address.trim() : undefined,
          comment: comment.trim() || undefined,
          items: buildItems(cart),
        },
      });
      onSuccess(order.id);
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>{t("checkout.title")}</h1>
      <label>
        {t("checkout.name")}
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      {fieldError?.field === "name" && <p role="alert">{fieldError.text}</p>}

      <button type="button" onClick={handleContact}>
        {t("checkout.sendContact")}
      </button>
      <label>
        {t("checkout.phone")}
        <input
          value={phone}
          placeholder={t("checkout.phoneManualLabel")}
          onChange={(e) => setPhone(e.target.value)}
        />
      </label>
      {fieldError?.field === "phone" && <p role="alert">{fieldError.text}</p>}

      <fieldset>
        <label>
          <input
            type="radio"
            name="deliveryType"
            checked={deliveryType === "delivery"}
            onChange={() => setDeliveryType("delivery")}
          />
          {t("checkout.delivery")}
        </label>
        <label>
          <input
            type="radio"
            name="deliveryType"
            checked={deliveryType === "pickup"}
            onChange={() => setDeliveryType("pickup")}
          />
          {t("checkout.pickup")}
        </label>
      </fieldset>

      {deliveryType === "delivery" ? (
        <>
          <label>
            {t("checkout.address")}
            <input value={address} onChange={(e) => setAddress(e.target.value)} />
          </label>
          {fieldError?.field === "address" && <p role="alert">{fieldError.text}</p>}
        </>
      ) : (
        <div>
          <p>{t("checkout.pickupAddressLabel")}</p>
          <p>{pickupAddress}</p>
        </div>
      )}

      <label>
        {t("checkout.comment")}
        <textarea value={comment} onChange={(e) => setComment(e.target.value)} />
      </label>
      {fieldError?.field === "comment" && <p role="alert">{fieldError.text}</p>}

      {submitError && <p role="alert">{submitError}</p>}

      <button type="submit" disabled={sending}>
        {sending ? t("checkout.sending") : t("checkout.submit")}
      </button>
    </form>
  );
}
