
import { initAuth, login, logout, getCurrentUser, getCurrentRole, resetPassword } from "./auth.js";
import { createUser, getAllUsers, updateUserRole, deleteUser } from "./users.js";
import { createDemande, listenDemandes, updateStatut, repondreDemande, deleteDemande } from "./demandes.js";
import { showToast, showConfirm, formatDate, escapeHtml, getRoleLabel, getStatutLabel, getTypeLabel } from "./ui.js";
import { ROLES } from "./config.js";

let currentFilter = "all";
let allDemandes = [];
let pendingNotifs = [];
let pendingCapture = null;
let unsubDemandes = null;

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch((e) => console.warn("[SW]", e));
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initAuth(onAuthChange);
  bindEvents();
});

function onAuthChange(user, role) {
  const loginScreen = document.getElementById("screen-login");
  const appScreen = document.getElementById("screen-app");

  if (unsubDemandes) { unsubDemandes(); unsubDemandes = null; }

  if (user) {
    loginScreen.classList.add("hidden");
    appScreen.classList.remove("hidden");

    document.getElementById("header-email").textContent = user.email;
    const roleBadge = document.getElementById("header-role");
    roleBadge.textContent = getRoleLabel(role);
    roleBadge.className = "role-badge " + role;

    document.getElementById("tab-users").classList.toggle("hidden", role !== ROLES.ADMIN);
    document.getElementById("section-form").classList.remove("hidden");

    const key = "lastSeen_" + user.uid;
    if (!localStorage.getItem(key)) localStorage.setItem(key, String(Date.now()));

    unsubDemandes = listenDemandes(user.email, role, (demandes) => {
      allDemandes = demandes;
      renderDemandes();
      updateBell();
    });

    if (role === ROLES.ADMIN) loadUsers();
  } else {
    loginScreen.classList.remove("hidden");
    appScreen.classList.add("hidden");
    allDemandes = [];
    pendingNotifs = [];
  }
}

function bindEvents() {
  document.getElementById("btn-login").addEventListener("click", handleLogin);
  document.getElementById("login-pass").addEventListener("keydown", (e) => { if (e.key === "Enter") handleLogin(); });
  document.getElementById("btn-logout").addEventListener("click", () => logout());

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === btn.dataset.tab));
      document.getElementById("panel-demandes").classList.toggle("hidden", btn.dataset.tab !== "demandes");
      document.getElementById("panel-users").classList.toggle("hidden", btn.dataset.tab !== "users");
    });
  });

  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      currentFilter = btn.dataset.filter;
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderDemandes();
    });
  });

  document.getElementById("btn-submit-demande").addEventListener("click", handleSubmitDemande);
  document.getElementById("btn-create-user").addEventListener("click", handleCreateUser);

  document.getElementById("toggle-pass").addEventListener("click", () => {
    const input = document.getElementById("login-pass");
    const btn = document.getElementById("toggle-pass");
    if (input.type === "password") { input.type = "text"; btn.textContent = "🙈"; btn.title = "Masquer"; }
    else { input.type = "password"; btn.textContent = "👁"; btn.title = "Afficher"; }
  });

  document.getElementById("link-forgot").addEventListener("click", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    if (!email) { showToast("Saisissez d'abord votre email ci-dessus", "error"); document.getElementById("login-email").focus(); return; }
    const result = await resetPassword(email);
    if (result.success) showToast("📧 Email de réinitialisation envoyé à " + email, "success");
    else showToast(result.message, "error");
  });

  document.getElementById("bell-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    const dd = document.getElementById("notif-dropdown");
    if (!dd.classList.contains("hidden")) { dd.classList.add("hidden"); return; }
    dd.innerHTML = pendingNotifs.length
      ? pendingNotifs.map(n => '<div class="notif-item">🔔 ' + escapeHtml(n.text) + '</div>').join("")
      : '<div class="notif-empty">Aucune notification</div>';
    dd.classList.remove("hidden");
    const user = getCurrentUser();
    localStorage.setItem("lastSeen_" + user.uid, String(Date.now()));
    document.getElementById("bell-badge").classList.add("hidden");
  });
  document.addEventListener("click", () => document.getElementById("notif-dropdown").classList.add("hidden"));

  document.getElementById("f-capture").addEventListener("change", (e) => {
    const file = e.target.files[0];
    const preview = document.getElementById("capture-preview");
    pendingCapture = null;
    preview.classList.add("hidden");
    if (!file) return;
    if (!file.type.startsWith("image/")) { showToast("Le fichier doit être une image", "error"); e.target.value = ""; return; }
    if (file.size > 5 * 1024 * 1024) { showToast("Image trop lourde (max 5 Mo)", "error"); e.target.value = ""; return; }
    pendingCapture = file;
    const reader = new FileReader();
    reader.onload = (ev) => {
      preview.innerHTML = '<img src="' + ev.target.result + '" alt="Aperçu"><div class="capture-hint">' + escapeHtml(file.name) + ' (' + Math.round(file.size / 1024) + ' Ko)</div>';
      preview.classList.remove("hidden");
    };
    reader.readAsDataURL(file);
  });
}

async function handleLogin() {
  const email = document.getElementById("login-email").value.trim();
  const pass = document.getElementById("login-pass").value;
  const errorEl = document.getElementById("login-error");
  const btn = document.getElementById("btn-login");
  if (!email || !pass) { errorEl.textContent = "Veuillez remplir tous les champs"; errorEl.classList.remove("hidden"); return; }
  btn.disabled = true; btn.textContent = "Connexion…"; errorEl.classList.add("hidden");
  const result = await login(email, pass);
  if (!result.success) { errorEl.textContent = result.message; errorEl.classList.remove("hidden"); }
  btn.disabled = false; btn.textContent = "Se connecter";
}

function updateBell() {
  const user = getCurrentUser();
  if (!user) return;
  const role = getCurrentRole();
  const lastSeen = Number(localStorage.getItem("lastSeen_" + user.uid) || 0);
  if (role === "admin" || role === "qualite") {
    pendingNotifs = allDemandes
      .filter(d => (d.dateCreation && d.dateCreation.toMillis ? d.dateCreation.toMillis() : 0) > lastSeen)
      .map(d => ({ text: "Nouvelle demande " + (d.numero || d.symbole) + " — " + d.demandeur }));
  } else {
    pendingNotifs = allDemandes
      .filter(d => d.reponse && (d.dateReponse && d.dateReponse.toMillis ? d.dateReponse.toMillis() : 0) > lastSeen)
      .map(d => ({ text: "Réponse reçue sur " + (d.numero || d.symbole) }));
  }
  const badge = document.getElementById("bell-badge");
  badge.textContent = pendingNotifs.length;
  badge.classList.toggle("hidden", pendingNotifs.length === 0);
}

function renderDemandes() {
  const container = document.getElementById("demandes-list");
  const role = getCurrentRole();
  const canManage = role === ROLES.ADMIN || role === ROLES.QUALITE;

  let filtered = allDemandes;
  if (currentFilter !== "all") filtered = allDemandes.filter(d => d.statut === currentFilter);

  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>Aucune demande ' + (currentFilter !== "all" ? "avec ce statut" : "pour le moment") + '.</p></div>';
    return;
  }

  container.innerHTML = filtered.map(d => `
    <div class="demande-card" data-id="${d.id}">
      <div class="demande-header">
        <span class="demande-ref">${escapeHtml(d.numero || d.symbole || "—")}</span>
        <div class="demande-meta">
          <span class="demande-type type-${d.type}">${getTypeLabel(d.type)}</span>
          <span class="demande-status status-${d.statut}">${getStatutLabel(d.statut)}</span>
        </div>
      </div>
      <div class="demande-body">
        ${d.symbole && d.numero ? '<p class="symbole-line">Symbole : <strong>' + escapeHtml(d.symbole) + '</strong></p>' : ""}
        <p>${escapeHtml(d.description)}</p>
        ${d.captureUrl ? '<a href="' + d.captureUrl + '" target="_blank" rel="noopener"><img class="capture-thumb" src="' + d.captureUrl + '" alt="Capture"></a>' : ""}
      </div>
      ${d.reponse ? `
        <div class="demande-response">
          <div class="resp-label">✓ Réponse Qualité</div>
          <p>${escapeHtml(d.reponse)}</p>
        </div>` : ""}
      <div class="demande-footer">
        <span>Par <strong>${escapeHtml(d.demandeur)}</strong></span>
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
        </div>` : ""}
    </div>
  `).join("");

  container.querySelectorAll("[data-action='statut']").forEach(select => {
    select.addEventListener("change", async (e) => {
      const result = await updateStatut(e.target.dataset.id, e.target.value);
      if (result.success) showToast("Statut mis à jour", "success");
      else showToast("Erreur : " + result.message, "error");
    });
  });

  container.querySelectorAll("[data-action='delete']").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const confirmed = await showConfirm("Supprimer", "Voulez-vous vraiment supprimer cette demande ?");
      if (!confirmed) return;
      const result = await deleteDemande(e.target.dataset.id);
      if (result.success) showToast("Demande supprimée", "success");
      else showToast("Erreur : " + result.message, "error");
    });
  });

  container.querySelectorAll("[data-action='save']").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const id = e.target.dataset.id;
      const reponse = container.querySelector('textarea[data-id="' + id + '"]').value.trim();
      const statut = container.querySelector('select[data-id="' + id + '"]').value;
      if (!reponse) { showToast("Veuillez saisir une réponse", "error"); return; }
      const result = await repondreDemande(id, reponse, statut);
      if (result.success) showToast("Réponse enregistrée", "success");
      else showToast("Erreur : " + result.message, "error");
    });
  });
}

async function handleSubmitDemande() {
  const symbole = document.getElementById("f-symbole").value.trim();
  const type = document.getElementById("f-type").value;
  const demandeur = document.getElementById("f-demandeur").value.trim();
  const description = document.getElementById("f-description").value.trim();
  const user = getCurrentUser();

  if (!symbole || !demandeur || !description) { showToast("Veuillez remplir tous les champs obligatoires", "error"); return; }

  const btn = document.getElementById("btn-submit-demande");
  btn.disabled = true;
  btn.textContent = pendingCapture ? "⬆️ Envoi de la capture…" : "Envoi…";

  const result = await createDemande({
    symbole: symbole, type: type, demandeur: demandeur,
    demandeurEmail: user.email, description: description, captureFile: pendingCapture
  });

  btn.disabled = false;
  btn.textContent = "🚀 Envoyer la demande";

  if (result.success) {
    showToast("Demande " + result.numero + " envoyée à l'équipe Qualité !", "success");
    document.getElementById("f-symbole").value = "";
    document.getElementById("f-description").value = "";
    document.getElementById("f-capture").value = "";
    document.getElementById("capture-preview").classList.add("hidden");
    pendingCapture = null;
  } else {
    showToast("Erreur : " + result.message, "error");
  }
}

async function loadUsers() {
  renderUsers(await getAllUsers());
}

function renderUsers(users) {
  const container = document.getElementById("users-list");
  const currentUser = getCurrentUser();
  if (users.length === 0) { container.innerHTML = '<div class="empty-state"><p>Aucun utilisateur.</p></div>'; return; }

  container.innerHTML = users.map(u => `
    <div class="user-card">
      <div class="user-card-left">
        <div class="user-avatar">${escapeHtml((u.nom || u.email)[0].toUpperCase())}</div>
        <div class="user-card-info">
          <h4>${escapeHtml(u.nom || u.email)}</h4>
          <p>${escapeHtml(u.email)} · Créé le ${formatDate(u.createdAt)}</p>
        </div>
      </div>
      <div class="user-card-right">
        <select data-action="role" data-id="${u.id}" ${u.id === currentUser.uid ? "disabled" : ""}>
          <option value="demandeur" ${u.role === "demandeur" || u.role === "lecteur" ? "selected" : ""}>👤 Demandeur</option>
          <option value="qualite" ${u.role === "qualite" ? "selected" : ""}>📧 Qualité</option>
          <option value="admin" ${u.role === "admin" ? "selected" : ""}>👑 Admin</option>
        </select>
        ${u.id !== currentUser.uid ? '<button class="btn-danger btn-sm" data-action="delete-user" data-id="' + u.id + '">🗑️</button>' : ""}
      </div>
    </div>
  `).join("");

  container.querySelectorAll("[data-action='role']").forEach(select => {
    select.addEventListener("change", async (e) => {
      const result = await updateUserRole(e.target.dataset.id, e.target.value);
      if (result.success) showToast("Rôle mis à jour", "success");
      else showToast("Erreur : " + result.message, "error");
    });
  });

  container.querySelectorAll("[data-action='delete-user']").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      const confirmed = await showConfirm("Supprimer l'utilisateur", "Voulez-vous vraiment supprimer cet utilisateur ?");
      if (!confirmed) return;
      const result = await deleteUser(e.target.dataset.id);
      if (result.success) { showToast("Utilisateur supprimé", "success"); loadUsers(); }
      else showToast("Erreur : " + result.message, "error");
    });
  });
}

async function handleCreateUser() {
  const email = document.getElementById("u-email").value.trim();
  const nom = document.getElementById("u-nom").value.trim();
  const pass = document.getElementById("u-pass").value;
  const role = document.getElementById("u-role").value;

  if (!email || !nom || !pass) { showToast("Veuillez remplir tous les champs", "error"); return; }
  if (pass.length < 6) { showToast("Le mot de passe doit faire au moins 6 caractères", "error"); return; }

  const btn = document.getElementById("btn-create-user");
  btn.disabled = true; btn.textContent = "Création…";
  const result = await createUser(email, pass, nom, role);
  btn.disabled = false; btn.textContent = "Créer le compte";

  if (result.success) {
    showToast("Utilisateur " + email + " créé (" + getRoleLabel(role) + ")", "success");
    document.getElementById("u-email").value = "";
    document.getElementById("u-nom").value = "";
    document.getElementById("u-pass").value = "";
    loadUsers();
  } else {
    showToast("Erreur : " + result.message, "error");
  }
}
