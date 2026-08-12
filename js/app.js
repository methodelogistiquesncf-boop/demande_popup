// ═══════════════════════════════════════
// POINT D'ENTRÉE DE L'APPLICATION
// ═══════════════════════════════════════

import { initAuth, login, logout, getCurrentUser, getCurrentRole } from "./auth.js";
import { createUser, getAllUsers, updateUserRole, deleteUser } from "./users.js";
import { createDemande, getDemandes, updateStatut, repondreDemande, deleteDemande } from "./demandes.js";
import { showToast, showConfirm, formatDate, escapeHtml, getRoleLabel, getStatutLabel, getTypeLabel } from "./ui.js";
import { ROLES } from "./config.js";

// ─── État global ───
let currentTab = "demandes";
let currentFilter = "all";
let allDemandes = [];

// ─── Initialisation ───
document.addEventListener("DOMContentLoaded", () => {
  initAuth(onAuthChange);
  bindEvents();
});

// ─── Changement d'état auth ───
function onAuthChange(user, role) {
  const loginScreen = document.getElementById("screen-login");
  const appScreen = document.getElementById("screen-app");

  if (user) {
    loginScreen.classList.add("hidden");
    appScreen.classList.remove("hidden");

    // Header
    document.getElementById("header-email").textContent = user.email;
    const roleBadge = document.getElementById("header-role");
    roleBadge.textContent = getRoleLabel(role);
    roleBadge.className = `role-badge ${role}`;

    // Afficher/cacher selon rôle
    document.getElementById("tab-users").classList.toggle("hidden", role !== ROLES.ADMIN);
    document.getElementById("section-form").classList.toggle("hidden", role !== ROLES.LECTEUR);

    // Charger les données
    loadDemandes();
    if (role === ROLES.ADMIN) loadUsers();
  } else {
    loginScreen.classList.remove("hidden");
    appScreen.classList.add("hidden");
  }
}

// ─── Bind events ───
function bindEvents() {
  // Login
  document.getElementById("btn-login").addEventListener("click", handleLogin);
  document.getElementById("login-pass").addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleLogin();
  });

  // Logout
  document.getElementById("btn-logout").addEventListener("click", () => logout());

  // Tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  // Filtres
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      currentFilter = btn.dataset.filter;
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderDemandes();
    });
  });

  // Soumettre demande
  document.getElementById("btn-submit-demande").addEventListener("click", handleSubmitDemande);

  // Créer utilisateur
  document.getElementById("btn-create-user").addEventListener("click", handleCreateUser);
}

// ─── Login ───
async function handleLogin() {
  const email = document.getElementById("login-email").value.trim();
  const pass = document.getElementById("login-pass").value;
  const errorEl = document.getElementById("login-error");
  const btn = document.getElementById("btn-login");

  if (!email || !pass) {
    errorEl.textContent = "Veuillez remplir tous les champs";
    errorEl.classList.remove("hidden");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Connexion…";
  errorEl.classList.add("hidden");

  const result = await login(email, pass);

  if (!result.success) {
    errorEl.textContent = result.message;
    errorEl.classList.remove("hidden");
  }

  btn.disabled = false;
  btn.textContent = "Se connecter";
}

// ─── Tabs ───
function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll(".tab-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.tab === tab);
  });
  document.getElementById("panel-demandes").classList.toggle("hidden", tab !== "demandes");
  document.getElementById("panel-users").classList.toggle("hidden", tab !== "users");
}

// ─── Charger les demandes ───
async function loadDemandes() {
  const user = getCurrentUser();
  const role = getCurrentRole();
  allDemandes = await getDemandes(user.email, role);
  renderDemandes();
}

// ─── Afficher les demandes ───
function renderDemandes() {
  const container = document.getElementById("demandes-list");
  const role = getCurrentRole();
  const canManage = role === ROLES.ADMIN || role === ROLES.QUALITE;

  let filtered = allDemandes;
  if (currentFilter !== "all") {
    filtered = allDemandes.filter(d => d.statut === currentFilter);
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="icon">📭</div>
        <p>Aucune demande ${currentFilter !== "all" ? "avec ce statut" : "pour le moment"}.</p>
      </div>`;
    return;
  }

  container.innerHTML = filtered.map(d => `
    <div class="demande-card" data-id="${d.id}">
      <div class="demande-header">
        <span class="demande-ref">${escapeHtml(d.symbole)}</span>
        <div class="demande-meta">
          <span class="demande-type type-${d.type}">${getTypeLabel(d.type)}</span>
          <span class="demande-status status-${d.statut}">${getStatutLabel(d.statut)}</span>
        </div>
      </div>
      <div class="demande-body">
        <p>${escapeHtml(d.description)}</p>
      </div>
      ${d.reponse ? `
        <div class="demande-response">
          <div class="resp-label">✓ Réponse Qualité</div>
          <p>${escapeHtml(d.reponse)}</p>
        </div>
      ` : ""}
      <div class="demande-footer">
        <span>Par <strong>${escapeHtml(d.demandeur)}</strong> (${escapeHtml(d.demandeurEmail)})</span>
        <span>${formatDate(d.dateCreation)}</span>
      </div>
      ${canManage ? `
        <div class="demande-actions">
          <div class="actions-row">
            <select data-action="statut" data-id="${d.id}">
              <option value="nouveau" ${d.statut === "nouveau" ? "selected" : ""}>🆕 Nouveau</option>
              <option value="en_cours" ${d.statut === "en_cours" ? "selected" : ""}>⚡ En cours</option>
              <option value="resolu" ${d.statut === "resolu" ? "selected" : ""}>✅ Résolu</option>
            </select>
            <button class="btn-danger btn-sm" data-action="delete" data-id="${d.id}">🗑️ Supprimer</button>
          </div>
          <textarea placeholder="Réponse au demandeur…" data-id="${d.id}">${escapeHtml(d.reponse || "")}</textarea>
          <div class="actions-btns">
            <button class="btn-success btn-sm" data-action="save" data-id="${d.id}">💾 Enregistrer</button>
          </div>
        </div>
      ` : ""}
    </div>
  `).join("");

  // Bind actions
  container.querySelectorAll("[data-action='statut']").forEach(select => {
    select.addEventListener("change", async (e) => {
      const id = e.target.dataset.id;
      const statut = e.target.value;
      const result = await updateStatut(id, statut);
      if (result.success) {
        showToast("Statut mis à jour", "success");
        loadDemandes();
      }
    });
  });

  container.querySelectorAll("[data-action='delete']").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const id = e.target.dataset.id;
      const confirmed = await showConfirm("Supprimer", "Voulez-vous vraiment supprimer cette demande ?");
      if (confirmed) {
        const result = await deleteDemande(id);
        if (result.success) {
          showToast("Demande supprimée", "success");
          loadDemandes();
        } else {
          showToast("Erreur: " + result.message, "error");
        }
      }
    });
  });

  container.querySelectorAll("[data-action='save']").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const id = e.target.dataset.id;
      const textarea = container.querySelector(`textarea[data-id="${id}"]`);
      const select = container.querySelector(`select[data-id="${id}"]`);
      const reponse = textarea.value.trim();
      const statut = select.value;

      if (!reponse) {
        showToast("Veuillez saisir une réponse", "error");
        return;
      }

      const result = await repondreDemande(id, reponse, statut);
      if (result.success) {
        showToast("Réponse enregistrée", "success");
        loadDemandes();
      } else {
        showToast("Erreur: " + result.message, "error");
      }
    });
  });
}

// ─── Soumettre une demande ───
async function handleSubmitDemande() {
  const symbole = document.getElementById("f-symbole").value.trim();
  const type = document.getElementById("f-type").value;
  const demandeur = document.getElementById("f-demandeur").value.trim();
  const description = document.getElementById("f-description").value.trim();
  const user = getCurrentUser();

  if (!symbole || !demandeur || !description) {
    showToast("Veuillez remplir tous les champs obligatoires", "error");
    return;
  }

  const btn = document.getElementById("btn-submit-demande");
  btn.disabled = true;
  btn.textContent = "Envoi…";

  const result = await createDemande({
    symbole,
    type,
    demandeur,
    demandeurEmail: user.email,
    description
  });

  btn.disabled = false;
  btn.textContent = "🚀 Envoyer la demande";

  if (result.success) {
    showToast("Demande envoyée à l'équipe Qualité !", "success");
    document.getElementById("f-symbole").value = "";
    document.getElementById("f-description").value = "";
    loadDemandes();
  } else {
    showToast("Erreur: " + result.message, "error");
  }
}

// ─── Charger les utilisateurs (Admin) ───
async function loadUsers() {
  const users = await getAllUsers();
  renderUsers(users);
}

// ─── Afficher les utilisateurs ───
function renderUsers(users) {
  const container = document.getElementById("users-list");
  const currentUser = getCurrentUser();

  if (users.length === 0) {
    container.innerHTML = `<div class="empty-state"><p>Aucun utilisateur.</p></div>`;
    return;
  }

  container.innerHTML = users.map(u => `
    <div class="user-card" data-id="${u.id}">
      <div class="user-card-left">
        <div class="user-avatar">${(u.nom || u.email)[0].toUpperCase()}</div>
        <div class="user-card-info">
          <h4>${escapeHtml(u.nom || u.email)}</h4>
          <p>${escapeHtml(u.email)} · Créé le ${formatDate(u.createdAt)}</p>
        </div>
      </div>
      <div class="user-card-right">
        <select data-action="role" data-id="${u.id}" ${u.id === currentUser.uid ? "disabled" : ""}>
          <option value="lecteur" ${u.role === "lecteur" ? "selected" : ""}>👁 Lecteur</option>
          <option value="qualite" ${u.role === "qualite" ? "selected" : ""}>📧 Qualité</option>
          <option value="admin" ${u.role === "admin" ? "selected" : ""}>👑 Admin</option>
        </select>
        ${u.id !== currentUser.uid ? `
          <button class="btn-danger btn-sm" data-action="delete-user" data-id="${u.id}">🗑️</button>
        ` : ""}
      </div>
    </div>
  `).join("");

  // Bind role change
  container.querySelectorAll("[data-action='role']").forEach(select => {
    select.addEventListener("change", async (e) => {
      const uid = e.target.dataset.id;
      const newRole = e.target.value;
      const result = await updateUserRole(uid, newRole);
      if (result.success) {
        showToast("Rôle mis à jour", "success");
      } else {
        showToast("Erreur: " + result.message, "error");
      }
    });
  });

  // Bind delete user
  container.querySelectorAll("[data-action='delete-user']").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const uid = e.target.dataset.id;
      const confirmed = await showConfirm(
        "Supprimer l'utilisateur",
        "Voulez-vous vraiment supprimer cet utilisateur ? Cette action est irréversible."
      );
      if (confirmed) {
        const result = await deleteUser(uid);
        if (result.success) {
          showToast("Utilisateur supprimé", "success");
          loadUsers();
        } else {
          showToast("Erreur: " + result.message, "error");
        }
      }
    });
  });
}

// ─── Créer un utilisateur ───
async function handleCreateUser() {
  const email = document.getElementById("u-email").value.trim();
  const nom = document.getElementById("u-nom").value.trim();
  const pass = document.getElementById("u-pass").value;
  const role = document.getElementById("u-role").value;

  if (!email || !nom || !pass) {
    showToast("Veuillez remplir tous les champs", "error");
    return;
  }

  if (pass.length < 6) {
    showToast("Le mot de passe doit faire au moins 6 caractères", "error");
    return;
  }

  const btn = document.getElementById("btn-create-user");
  btn.disabled = true;
  btn.textContent = "Création…";

  const result = await createUser(email, pass, nom, role);

  btn.disabled = false;
  btn.textContent = "Créer le compte";

  if (result.success) {
    showToast(`Utilisateur ${email} créé avec le rôle ${getRoleLabel(role)}`, "success");
    document.getElementById("u-email").value = "";
    document.getElementById("u-nom").value = "";
    document.getElementById("u-pass").value = "";
    loadUsers();
  } else {
    showToast("Erreur: " + result.message, "error");
  }
}
