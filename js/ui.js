
export function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast toast-" + type;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

export function showConfirm(title, message) {
  return new Promise((resolve) => {
    const overlay = document.getElementById("modal-overlay");
    document.getElementById("modal-title").textContent = title;
    document.getElementById("modal-message").textContent = message;
    overlay.classList.remove("hidden");
    const cleanup = () => {
      overlay.classList.add("hidden");
      document.getElementById("modal-confirm").onclick = null;
      document.getElementById("modal-cancel").onclick = null;
    };
    document.getElementById("modal-confirm").onclick = () => { cleanup(); resolve(true); };
    document.getElementById("modal-cancel").onclick = () => { cleanup(); resolve(false); };
  });
}

export function formatDate(ts) {
  if (!ts) return "—";
  const d = ts.toDate ? ts.toDate() : new Date(ts);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function getRoleLabel(role) {
  const labels = { admin: "Admin", qualite: "Qualité", demandeur: "Demandeur", lecteur: "Demandeur" };
  return labels[role] || role;
}

export function getStatutLabel(s) {
  const labels = { nouveau: "Nouveau", en_cours: "En cours", resolu: "Résolu" };
  return labels[s] || s;
}

export function getTypeLabel(t) {
  const labels = { creation: "Création", modification: "Modification", suppression: "Suppression" };
  return labels[t] || t;
}
