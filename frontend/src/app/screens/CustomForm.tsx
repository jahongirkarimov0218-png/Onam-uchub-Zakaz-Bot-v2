import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../../shared/api";
import { t } from "../../shared/i18n/uz";

export type CustomFormResult = {
  name: string | null;
  sku: string | null;
  uploadId: number | null;
  imageUrl: string | null;
  note: string | null;
  quantity: number;
};

/** "Katalogda yo'q mahsulot" form: at least one of name/sku/photo is required.
 * The photo uploads immediately on selection (not on submit). */
export function CustomForm({ onAdd }: { onAdd: (data: CustomFormResult) => void }) {
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [note, setNote] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [uploadId, setUploadId] = useState<number | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const result = await api<{ upload_id: number; url: string }>("/api/uploads", {
        method: "POST",
        body: form,
      });
      if (!mountedRef.current) return;
      setUploadId(result.upload_id);
      setImageUrl(result.url);
    } catch (err) {
      if (!mountedRef.current) return;
      setUploadError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      if (mountedRef.current) setUploading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() && !sku.trim() && !uploadId) {
      setValidationError(t("customForm.validationRequired"));
      return;
    }
    setValidationError(null);
    onAdd({
      name: name.trim() || null,
      sku: sku.trim() || null,
      uploadId,
      imageUrl,
      note: note.trim() || null,
      quantity,
    });
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>{t("customForm.title")}</h1>
      <label>
        {t("customForm.name")}
        <input value={name} onChange={(e) => setName(e.target.value)} />
      </label>
      <label>
        {t("customForm.sku")}
        <input value={sku} onChange={(e) => setSku(e.target.value)} />
      </label>
      <label>
        {t("customForm.photo")}
        <input type="file" accept="image/*" onChange={handleFile} disabled={uploading} />
      </label>
      {uploading && <p>{t("customForm.uploading")}</p>}
      {uploadError && <p role="alert">{uploadError}</p>}
      {imageUrl && <img src={imageUrl} alt={t("customForm.photoPreviewAlt")} width={60} height={60} />}
      <label>
        {t("customForm.quantity")}
        <input
          type="number"
          min={1}
          max={99}
          value={quantity}
          onChange={(e) => setQuantity(Math.min(99, Math.max(1, Number(e.target.value) || 1)))}
        />
      </label>
      <label>
        {t("customForm.note")}
        <textarea value={note} onChange={(e) => setNote(e.target.value)} />
      </label>
      {validationError && <p role="alert">{validationError}</p>}
      <button type="submit" disabled={uploading}>
        {t("customForm.submit")}
      </button>
    </form>
  );
}
