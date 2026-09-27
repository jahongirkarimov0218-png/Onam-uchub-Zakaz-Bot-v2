import { useEffect, useState } from "react";
import { api, ApiError } from "../../shared/api";
import { t } from "../../shared/i18n/uz";

type Category = { id: number; name: string };

/** Categories tab: list, create, rename inline, delete with an inline
 * confirm step (409 `category_not_empty` shows the uz message from the
 * shared error dictionary). */
export function Categories() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newName, setNewName] = useState("");
  const [renamingId, setRenamingId] = useState<number | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  const [savingRenameId, setSavingRenameId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  function reload() {
    setError(null);
    api<Category[]>("/api/admin/categories")
      .then((data) => {
        setCategories(data);
        setLoaded(true);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : t("errors.generic"));
        setLoaded(true);
      });
  }

  useEffect(reload, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (adding || !newName.trim()) return;
    setAdding(true);
    try {
      await api<Category>("/api/admin/categories", { method: "POST", body: { name: newName.trim() } });
      setNewName("");
      reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      setAdding(false);
    }
  }

  function startRename(c: Category) {
    setRenamingId(c.id);
    setRenameValue(c.name);
    setError(null);
  }

  async function saveRename(id: number) {
    if (savingRenameId === id) return;
    setSavingRenameId(id);
    try {
      await api<Category>(`/api/admin/categories/${id}`, { method: "PATCH", body: { name: renameValue.trim() } });
      setRenamingId(null);
      reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      setSavingRenameId(null);
    }
  }

  async function confirmDelete(id: number) {
    if (deletingId === id) return;
    setDeletingId(id);
    try {
      await api(`/api/admin/categories/${id}`, { method: "DELETE" });
      setConfirmingDeleteId(null);
      reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("errors.generic"));
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <h1>{t("admin.categories.title")}</h1>
      {error && <p role="alert">{error}</p>}
      {loaded && categories.length === 0 && <p>{t("admin.categories.empty")}</p>}
      <ul>
        {categories.map((c) => (
          <li key={c.id}>
            {renamingId === c.id ? (
              <span>
                <input
                  aria-label={t("admin.categories.renameAction")}
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                />
                <button disabled={savingRenameId === c.id} onClick={() => saveRename(c.id)}>
                  {t("admin.categories.rename")}
                </button>
              </span>
            ) : (
              <>
                <span>{c.name}</span>
                <button onClick={() => startRename(c)}>{t("admin.categories.renameAction")}</button>
              </>
            )}
            {confirmingDeleteId === c.id ? (
              <span>
                <span>{t("admin.categories.deleteConfirm")}</span>
                <button disabled={deletingId === c.id} onClick={() => confirmDelete(c.id)}>
                  {t("admin.categories.confirmYes")}
                </button>
                <button disabled={deletingId === c.id} onClick={() => setConfirmingDeleteId(null)}>
                  {t("admin.categories.confirmNo")}
                </button>
              </span>
            ) : (
              <button onClick={() => setConfirmingDeleteId(c.id)}>{t("admin.categories.delete")}</button>
            )}
          </li>
        ))}
      </ul>

      <form onSubmit={handleAdd}>
        <label>
          {t("admin.categories.namePlaceholder")}
          <input value={newName} onChange={(e) => setNewName(e.target.value)} />
        </label>
        <button type="submit" disabled={adding}>
          {t("admin.categories.add")}
        </button>
      </form>
    </div>
  );
}
