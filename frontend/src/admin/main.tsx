import React from "react";
import { createRoot } from "react-dom/client";
import { t } from "../shared/i18n/uz";

// Stub entry for the admin Mini App. Ticket 06 replaces this with the real app.
function AdminPlaceholder() {
  return (
    <div style={{ padding: 24, fontFamily: "sans-serif" }}>
      <p>{t("admin.comingSoon")}</p>
    </div>
  );
}

const root = document.getElementById("root");
if (root) {
  createRoot(root).render(<AdminPlaceholder />);
}
