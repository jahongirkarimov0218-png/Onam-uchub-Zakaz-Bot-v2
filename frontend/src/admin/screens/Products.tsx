import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "../../shared/api";
import { t } from "../../shared/i18n/uz";
import { formatSum } from "../../shared/format";

type Category = { id: number; name: string };
type Product = {
  id: number;
  category_id: number;
  name: string;
  sku: string;
  price: number;
  description: string | null;
  image_url: string | null;
  is_available: boolean;
};

type Mode = { kind: "list" } | { kind: "create" } | { kind: "edit"; product: Product };

function emptyForm() {
  return { categoryId: "", name: "", sku: "", price: "", description: "", uploadId: null as number | null, imageUrl: null as string | null, isAvailable: true };
}

function formFromProduct(p: Product) {
  return {
    categoryId: String(p.category_id),
    name: p.name,
    sku: p.sku,
    price: String(p.price),
    description: p.description ?? "",
    uploadId: null as number | null,
    imageUrl: p.image_url,
    isAvailable: p.is_available,
  };
}

/** Products tab: list (incl. unavailable, badge), search, create/edit form
 * (inline, no separate hash route — the edit form is pre-filled from the
 * already-fetched list since there is no single-product GET endpoint), soft
 * delete with an inline confirm step, availability toggle. */
export function Products() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>({ kind: "list" });
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyForm());
  const [uploading, setUploading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    api<Category[]>("/api/admin/categories").then(setCategories).catch(() => {});
  }, []);

  const reload = useCallback(() => {
    const params = new URLSearchParams();
    if (search.trim()) params.set("q", search.trim());
    const qs = params.toString();
    setListError(null);
    api<Product[]>(`/api/admin/products${qs ? `?${qs}` : ""}`)
      .then((data) => {
        setProducts(data);
        setLoaded(true);
      })
      .catch((err) => {
        setListError(err instanceof ApiError ? err.message : t("errors.generic"));
        setLoaded(true);
      });
  }, [search]);

  useEffect(() => {
    reload();
  }, [reload]);

  function startCreate() {
    setForm(emptyForm());
    setFormError(null);
    setMode({ kind: "create" });
  }

  function startEdit(p: Product) {
    setForm(formFromProduct(p));
    setFormError(null);
    setMode({ kind: "edit", product: p });
  }

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setFormError(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const result = await api<{ upload_id: number; url: string }>("/api/admin/uploads", { method: "POST", body });
      setForm((f) => ({ ...f, uploadId: result.upload_id, imageUrl: result.url }));
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      setUploading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (saving) return;
    if (!form.categoryId) {
      setFormError(t("admin.products.categoryRequired"));
      return;
    }
    if (!form.price.trim()) {
      setFormError(t("admin.products.priceRequired"));
      return;
    }
    setSaving(true);
    setFormError(null);
    const payload: Record<string, unknown> = {
      category_id: Number(form.categoryId),
      name: form.name.trim(),
      sku: form.sku.trim(),
      price: Number(form.price),
      // Explicit null (not omitted) so the server clears a cleared description
      // instead of leaving the old value untouched (PATCH uses exclude_unset).
      description: form.description.trim() || null,
      is_available: form.isAvailable,
    };
    if (form.uploadId != null) payload.upload_id = form.uploadId;
    try {
      if (mode.kind === "create") {
        await api<Product>("/api/admin/products", { method: "POST", body: payload });
      } else if (mode.kind === "edit") {
        await api<Product>(`/api/admin/products/${mode.product.id}`, { method: "PATCH", body: payload });
      }
      setMode({ kind: "list" });
      reload();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      setSaving(false);
    }
  }

  async function toggleAvailability(p: Product) {
    if (togglingId === p.id) return;
    setTogglingId(p.id);
    try {
      await api<Product>(`/api/admin/products/${p.id}`, {
        method: "PATCH",
        body: { is_available: !p.is_available },
      });
      reload();
    } catch (err) {
      setListError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      setTogglingId(null);
    }
  }

  async function confirmDelete(id: number) {
    if (deletingId === id) return;
    setDeletingId(id);
    try {
      await api(`/api/admin/products/${id}`, { method: "DELETE" });
      setConfirmingDeleteId(null);
      reload();
    } catch (err) {
      setListError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      setDeletingId(null);
    }
  }

  if (mode.kind === "create" || mode.kind === "edit") {
    return (
      <form onSubmit={handleSubmit}>
        <h1>{mode.kind === "create" ? t("admin.products.createTitle") : t("admin.products.editTitle")}</h1>
        <label>
          {t("admin.products.category")}
          <select value={form.categoryId} onChange={(e) => setForm((f) => ({ ...f, categoryId: e.target.value }))}>
            <option value="" disabled>
              —
            </option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("admin.products.name")}
          <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
        </label>
        <label>
          {t("admin.products.sku")}
          <input value={form.sku} onChange={(e) => setForm((f) => ({ ...f, sku: e.target.value }))} />
        </label>
        <label>
          {t("admin.products.price")}
          <input
            type="number"
            value={form.price}
            onChange={(e) => setForm((f) => ({ ...f, price: e.target.value }))}
          />
        </label>
        <label>
          {t("admin.products.description")}
          <textarea value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
        </label>
        <label>
          {t("admin.products.photo")}
          <input type="file" accept="image/*" onChange={handleFile} disabled={uploading} />
        </label>
        {uploading && <p>{t("admin.products.uploading")}</p>}
        {form.imageUrl && <img src={form.imageUrl} alt={t("admin.products.photoPreviewAlt")} width={60} height={60} />}
        <label>
          <input
            type="checkbox"
            checked={!form.isAvailable}
            onChange={(e) => setForm((f) => ({ ...f, isAvailable: !e.target.checked }))}
          />
          {t("admin.products.unavailableToggle")}
        </label>
        {formError && <p role="alert">{formError}</p>}
        <button type="submit" disabled={saving || uploading}>
          {saving ? t("admin.products.saving") : t("admin.products.save")}
        </button>
        <button type="button" onClick={() => setMode({ kind: "list" })}>
          {t("admin.products.cancelForm")}
        </button>
      </form>
    );
  }

  return (
    <div>
      <h1>{t("admin.products.title")}</h1>
      <input
        aria-label={t("admin.products.searchPlaceholder")}
        placeholder={t("admin.products.searchPlaceholder")}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <button onClick={startCreate}>{t("admin.products.addNew")}</button>
      {listError && <p role="alert">{listError}</p>}
      {loaded && products.length === 0 && !listError && <p>{t("admin.products.empty")}</p>}
      <ul>
        {products.map((p) => (
          <li key={p.id}>
            {p.image_url && <img src={p.image_url} alt={p.name} width={40} height={40} />}
            <span>{p.name}</span>
            <span>{p.sku}</span>
            <span>{formatSum(p.price)}</span>
            {!p.is_available && <span>{t("admin.products.unavailableBadge")}</span>}
            <button disabled={togglingId === p.id} onClick={() => toggleAvailability(p)}>
              {p.is_available ? t("admin.products.markUnavailable") : t("admin.products.markAvailable")}
            </button>
            <button onClick={() => startEdit(p)}>{t("admin.products.edit")}</button>
            {confirmingDeleteId === p.id ? (
              <span>
                <span>{t("admin.products.deleteConfirm")}</span>
                <button disabled={deletingId === p.id} onClick={() => confirmDelete(p.id)}>
                  {t("admin.products.confirmYes")}
                </button>
                <button disabled={deletingId === p.id} onClick={() => setConfirmingDeleteId(null)}>
                  {t("admin.products.confirmNo")}
                </button>
              </span>
            ) : (
              <button onClick={() => setConfirmingDeleteId(p.id)}>{t("admin.products.delete")}</button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
