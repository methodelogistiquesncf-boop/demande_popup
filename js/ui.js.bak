// ═══════════════════════════════════════
// FONCTIONS UI (Toast, Modal, Helpers)
// ═══════════════════════════════════════

// Toast notification
export function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// Modal de confirmation
export function showConfirm(title, message) {
  return new Promise((resolve) => {
    const overlay = document.getElementById("modal-overlay");
    const titleEl = document.getElementById("modal-title");
    const msgEl = document.getElementById("modal-message");
    const confirmBtn = document.getElementById("modal-confirm");
    const cancelBtn = document.getElementById("modal-cancel");

    titleEl.textContent = title;
    msgEl.textContent = message;
    overlay.classList.remove("hidden");

    const cleanup = () => {
      overlay.classList.add("hidden");
      confirmBtn.onclick = null;
      cancelBtn.onclick = null;
    };

    confirmBtn.onclick = () => { cleanup(); resolve(true); };
    cancelBtn.onclick = () => { cleanup(); resolve(false); };
  });
}

// Formater une date
export function formatDate(timestamp) {
  if (!timestamp) return "—";
  const date = timestamp.toDate ? timestamp.toDate() : new Date(timestamp);
  return date.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

// Échapper le HTML
export function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Obtenir le label d'un rôle
export function getRoleLabel(role) {
  const labels = { admin: "Admin", qualite: "Qualité", lecteur: "Lecteur" };
  return labels[role] || role;
}

// Obtenir le label d'un statut
export function getStatutLabel(statut) {
  const labels = { nouveau: "Nouveau", en_cours: "En cours", resolu: "Résolu" };
  return labels[statut] || statut;
}

// Obtenir le label d'un type
export function getTypeLabel(type) {
  const labels = { creation: "Création", modification: "Modification", suppression: "Suppression" };
  return labels[type] || type;
}
