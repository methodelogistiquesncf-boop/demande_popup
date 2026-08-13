# -*- coding: utf-8 -*-
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def write(p, c):
    full = os.path.join(BASE, *p.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] " + p)

# ═══════════════════════════════════════
# js/app.js
# ═══════════════════════════════════════
write("js/app.js", r'''
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
''')

# ═══════════════════════════════════════
# index.html
# ═══════════════════════════════════════
write("index.html", r'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gestion Popups Reflex</title>
  <link rel="manifest" href="manifest.json">
  <link rel="icon" type="image/svg+xml" href="icons/icon.svg">
  <link rel="apple-touch-icon" href="icons/icon.svg">
  <meta name="theme-color" content="#1A2F4E">
  <meta name="mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Popups Reflex">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>

  <div id="toast-container"></div>

  <div id="modal-overlay" class="hidden">
    <div class="modal-box">
      <h3 id="modal-title">Confirmer</h3>
      <p id="modal-message">Êtes-vous sûr ?</p>
      <div class="modal-actions">
        <button class="btn-secondary" id="modal-cancel">Annuler</button>
        <button class="btn-danger" id="modal-confirm">Confirmer</button>
      </div>
    </div>
  </div>

  <div id="screen-login">
    <div class="login-box">
      <div class="login-icon">🔧</div>
      <h1>Gestion Popups Reflex</h1>
      <p class="login-subtitle">Service Qualité</p>
      <div class="field">
        <label for="login-email">Adresse e-mail</label>
        <input type="email" id="login-email" placeholder="prenom.nom@sncf.fr" autocomplete="email">
      </div>
      <div class="field">
        <label for="login-pass">Mot de passe</label>
        <div class="password-wrapper">
          <input type="password" id="login-pass" placeholder="••••••••" autocomplete="current-password">
          <button type="button" class="toggle-pass" id="toggle-pass" title="Afficher">👁</button>
        </div>
      </div>
      <p class="forgot-password"><a href="#" id="link-forgot">Mot de passe oublié ?</a></p>
      <button class="btn-primary btn-full" id="btn-login">Se connecter</button>
      <p id="login-error" class="error-text hidden"></p>
    </div>
  </div>

  <div id="screen-app" class="hidden">
    <header>
      <div class="header-left">
        <span class="header-icon">🔧</span>
        <h1>Popups Reflex</h1>
      </div>
      <nav id="nav-tabs">
        <button class="tab-btn active" data-tab="demandes">📋 Demandes</button>
        <button class="tab-btn hidden" data-tab="users" id="tab-users">👥 Utilisateurs</button>
      </nav>
      <div class="header-right">
        <div class="notif-wrapper">
          <button class="bell-btn" id="bell-btn" title="Notifications">🔔<span class="bell-badge hidden" id="bell-badge">0</span></button>
          <div class="notif-dropdown hidden" id="notif-dropdown"></div>
        </div>
        <div class="user-info">
          <span id="header-email"></span>
          <span id="header-role" class="role-badge"></span>
        </div>
        <button class="btn-secondary btn-sm" id="btn-logout">Déconnexion</button>
      </div>
    </header>

    <main id="panel-demandes">
      <section id="section-form" class="hidden">
        <h2>📝 Nouvelle demande</h2>
        <div class="form-grid">
          <div class="field">
            <label for="f-symbole">Symbole / Réf *</label>
            <input type="text" id="f-symbole" placeholder="ex: POP-042" maxlength="50">
          </div>
          <div class="field">
            <label for="f-type">Type de demande *</label>
            <select id="f-type">
              <option value="creation">➕ Création</option>
              <option value="modification">✏️ Modification</option>
              <option value="suppression">🗑️ Suppression</option>
            </select>
          </div>
          <div class="field">
            <label for="f-demandeur">Votre nom *</label>
            <input type="text" id="f-demandeur" placeholder="Prénom Nom" maxlength="100">
          </div>
          <div class="field field-full">
            <label for="f-description">Description *</label>
            <textarea id="f-description" rows="4" placeholder="Décrivez la modification souhaitée…" maxlength="1000"></textarea>
          </div>
          <div class="field field-full">
            <label for="f-capture">📸 Capture d'écran (optionnel, 5 Mo max)</label>
            <input type="file" id="f-capture" accept="image/*">
            <div id="capture-preview" class="capture-preview hidden"></div>
          </div>
        </div>
        <button class="btn-primary" id="btn-submit-demande">🚀 Envoyer la demande</button>
      </section>

      <section id="section-list">
        <div class="list-header">
          <h2>📋 Demandes</h2>
          <div class="list-filters">
            <button class="filter-btn active" data-filter="all">Toutes</button>
            <button class="filter-btn" data-filter="nouveau">🆕 Nouvelles</button>
            <button class="filter-btn" data-filter="en_cours">⚡ En cours</button>
            <button class="filter-btn" data-filter="resolu">✅ Résolues</button>
          </div>
        </div>
        <div id="demandes-list"></div>
      </section>
    </main>

    <main id="panel-users" class="hidden">
      <section class="admin-section">
        <h2>➕ Créer un utilisateur</h2>
        <div class="form-grid">
          <div class="field">
            <label for="u-email">Email *</label>
            <input type="email" id="u-email" placeholder="prenom.nom@sncf.fr">
          </div>
          <div class="field">
            <label for="u-nom">Nom complet *</label>
            <input type="text" id="u-nom" placeholder="Prénom Nom">
          </div>
          <div class="field">
            <label for="u-pass">Mot de passe *</label>
            <input type="password" id="u-pass" placeholder="Min 6 caractères">
          </div>
          <div class="field">
            <label for="u-role">Rôle *</label>
            <select id="u-role">
              <option value="demandeur">👤 Demandeur (fait des demandes)</option>
              <option value="qualite">📧 Qualité (traite les demandes)</option>
              <option value="admin">👑 Admin (accès total)</option>
            </select>
          </div>
        </div>
        <button class="btn-primary" id="btn-create-user">Créer le compte</button>
      </section>

      <section class="admin-section">
        <h2>👥 Utilisateurs existants</h2>
        <div id="users-list"></div>
      </section>
    </main>
  </div>

  <script type="module" src="js/app.js"></script>
</body>
</html>
''')

# ═══════════════════════════════════════
# css/style.css
# ═══════════════════════════════════════
write("css/style.css", r'''
:root {
  --navy: #1A2F4E; --navy-light: #243d63; --orange: #E05A00; --orange-hover: #c44e00;
  --green: #2E7D52; --green-hover: #245f3e; --red: #e74c3c; --red-hover: #c0392b;
  --blue: #1565C0; --blue-light: #E3F2FD; --bg: #f0f2f5; --card: #fff;
  --text: #1a1a2e; --text-light: #6B7A8D; --border: #e0e4ea; --radius: 10px;
  --shadow: 0 2px 8px rgba(0,0,0,0.06); --shadow-lg: 0 8px 24px rgba(0,0,0,0.12);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
.hidden { display: none !important; }

button { font-family: inherit; cursor: pointer; border: none; padding: 10px 18px; border-radius: 6px; font-weight: 600; font-size: 14px; transition: all 0.2s; }
.btn-primary { background: var(--orange); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--orange-hover); }
.btn-secondary { background: #fff; color: var(--text); border: 1px solid var(--border); }
.btn-secondary:hover { background: #f5f5f5; }
.btn-danger { background: var(--red); color: #fff; }
.btn-danger:hover { background: var(--red-hover); }
.btn-success { background: var(--green); color: #fff; }
.btn-success:hover { background: var(--green-hover); }
.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-full { width: 100%; }
button:disabled { opacity: 0.5; cursor: not-allowed; }

.field { margin-bottom: 16px; }
.field label { display: block; font-size: 12px; font-weight: 600; color: var(--text-light); text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 6px; }
.field input, .field select, .field textarea { width: 100%; padding: 10px 14px; border: 1.5px solid var(--border); border-radius: 8px; font-family: inherit; font-size: 14px; color: var(--text); background: #fff; }
.field input:focus, .field select:focus, .field textarea:focus { outline: none; border-color: var(--orange); box-shadow: 0 0 0 3px rgba(224,90,0,0.1); }
.field textarea { resize: vertical; min-height: 80px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 16px; margin-bottom: 16px; }
.field-full { grid-column: 1 / -1; }
.error-text { color: var(--red); font-size: 13px; margin-top: 12px; text-align: center; }

#screen-login { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--navy) 0%, var(--navy-light) 100%); padding: 20px; }
.login-box { background: #fff; padding: 48px 40px; border-radius: 16px; box-shadow: var(--shadow-lg); width: 420px; max-width: 100%; }
.login-icon { text-align: center; font-size: 48px; margin-bottom: 12px; }
.login-box h1 { text-align: center; font-size: 22px; color: var(--navy); margin-bottom: 4px; }
.login-subtitle { text-align: center; color: var(--text-light); font-size: 14px; margin-bottom: 28px; }
.password-wrapper { position: relative; display: flex; align-items: center; }
.password-wrapper input { padding-right: 42px; }
.toggle-pass { position: absolute; right: 8px; background: transparent; border: none; padding: 6px 8px; font-size: 16px; cursor: pointer; color: var(--text-light); border-radius: 4px; }
.toggle-pass:hover { background: rgba(0,0,0,0.05); }
.forgot-password { text-align: right; margin: -6px 0 16px; }
.forgot-password a { color: var(--orange); font-size: 13px; text-decoration: none; font-weight: 500; }
.forgot-password a:hover { text-decoration: underline; }

header { background: var(--navy); color: #fff; padding: 0 24px; height: 56px; display: flex; align-items: center; justify-content: space-between; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
.header-left { display: flex; align-items: center; gap: 10px; }
.header-icon { font-size: 22px; }
.header-left h1 { font-size: 16px; font-weight: 700; }
#nav-tabs { display: flex; gap: 4px; }
.tab-btn { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.7); padding: 8px 16px; border-radius: 6px; font-size: 13px; }
.tab-btn:hover { background: rgba(255,255,255,0.2); color: #fff; }
.tab-btn.active { background: var(--orange); color: #fff; }
.header-right { display: flex; align-items: center; gap: 12px; }
.user-info { display: flex; align-items: center; gap: 8px; font-size: 13px; }
#header-email { color: rgba(255,255,255,0.9); }
.role-badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.role-badge.admin { background: #FFD54F; color: #333; }
.role-badge.qualite { background: #42A5F5; color: #fff; }
.role-badge.demandeur { background: rgba(255,255,255,0.2); color: #fff; }

.notif-wrapper { position: relative; }
.bell-btn { position: relative; background: rgba(255,255,255,0.1); border: none; border-radius: 50%; width: 38px; height: 38px; font-size: 17px; cursor: pointer; }
.bell-btn:hover { background: rgba(255,255,255,0.25); }
.bell-badge { position: absolute; top: -5px; right: -5px; background: var(--red); color: #fff; font-size: 10px; font-weight: 700; min-width: 18px; height: 18px; border-radius: 9px; display: flex; align-items: center; justify-content: center; padding: 0 4px; }
.notif-dropdown { position: absolute; right: 0; top: 46px; width: 320px; background: #fff; border-radius: 10px; box-shadow: var(--shadow-lg); border: 1px solid var(--border); z-index: 300; max-height: 380px; overflow-y: auto; }
.notif-item { padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text); }
.notif-item:last-child { border-bottom: none; }
.notif-empty { padding: 20px; text-align: center; color: var(--text-light); font-size: 13px; }

#panel-demandes, #panel-users { max-width: 1200px; margin: 0 auto; padding: 24px; }
#section-form { background: var(--card); border-radius: var(--radius); padding: 28px; margin-bottom: 24px; box-shadow: var(--shadow); border-left: 4px solid var(--orange); }
#section-form h2 { font-size: 16px; margin-bottom: 20px; color: var(--navy); }

.list-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.list-header h2 { font-size: 18px; color: var(--navy); }
.list-filters { display: flex; gap: 6px; flex-wrap: wrap; }
.filter-btn { background: #fff; border: 1.5px solid var(--border); color: var(--text-light); padding: 7px 14px; font-size: 12px; }
.filter-btn:hover { border-color: var(--orange); color: var(--orange); }
.filter-btn.active { background: var(--orange); color: #fff; border-color: var(--orange); }

.demande-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 14px; box-shadow: var(--shadow); }
.demande-card:hover { box-shadow: var(--shadow-lg); }
.demande-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; gap: 12px; flex-wrap: wrap; }
.demande-ref { background: var(--navy); color: #fff; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 700; font-family: 'Courier New', monospace; }
.demande-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.demande-type { font-size: 12px; padding: 3px 8px; border-radius: 4px; font-weight: 600; }
.type-creation { background: #E8F5E9; color: #2E7D32; }
.type-modification { background: #FFF3E0; color: #E65100; }
.type-suppression { background: #FFEBEE; color: #C62828; }
.demande-status { font-size: 11px; padding: 4px 10px; border-radius: 12px; font-weight: 700; }
.status-nouveau { background: #FFF3E0; color: #E65100; }
.status-en_cours { background: var(--blue-light); color: var(--blue); }
.status-resolu { background: #E8F5E9; color: var(--green); }
.demande-body p { font-size: 14px; line-height: 1.6; }
.symbole-line { font-size: 12px; color: var(--text-light); margin-bottom: 6px; }
.capture-thumb { max-width: 200px; max-height: 130px; border-radius: 8px; border: 1px solid var(--border); margin-top: 10px; display: block; cursor: zoom-in; }
.capture-thumb:hover { opacity: 0.85; }
.capture-preview img { max-width: 220px; max-height: 140px; border-radius: 8px; border: 1px solid var(--border); margin-top: 8px; display: block; }
.capture-hint { font-size: 11px; color: var(--text-light); margin-top: 4px; }
.demande-response { background: #f0faf5; border-left: 3px solid var(--green); padding: 12px 16px; border-radius: 0 6px 6px 0; margin-top: 12px; }
.demande-response .resp-label { font-size: 11px; font-weight: 700; color: var(--green); text-transform: uppercase; margin-bottom: 4px; }
.demande-response p { font-size: 13px; color: #1a3d2b; }
.demande-footer { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: var(--text-light); margin-top: 12px; flex-wrap: wrap; gap: 8px; }
.demande-actions { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border); }
.actions-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.demande-actions select { padding: 7px 10px; border: 1.5px solid var(--border); border-radius: 6px; font-size: 13px; font-family: inherit; }
.demande-actions textarea { width: 100%; padding: 8px 12px; border: 1.5px solid var(--border); border-radius: 6px; font-size: 13px; font-family: inherit; resize: vertical; min-height: 60px; margin-top: 10px; }
.actions-btns { display: flex; gap: 8px; margin-top: 10px; justify-content: flex-end; }
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-light); }
.empty-state .icon { font-size: 48px; margin-bottom: 12px; }

.admin-section { background: var(--card); border-radius: var(--radius); padding: 28px; margin-bottom: 24px; box-shadow: var(--shadow); }
.admin-section h2 { font-size: 16px; margin-bottom: 20px; color: var(--navy); }
.user-card { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 10px; background: var(--bg); }
.user-card:hover { background: #e8ecf0; }
.user-card-left { display: flex; align-items: center; gap: 14px; }
.user-avatar { width: 38px; height: 38px; border-radius: 50%; background: var(--navy); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; }
.user-card-info h4 { font-size: 14px; font-weight: 600; }
.user-card-info p { font-size: 12px; color: var(--text-light); }
.user-card-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.user-card-right select { padding: 6px 10px; border: 1.5px solid var(--border); border-radius: 6px; font-size: 12px; font-family: inherit; }

#toast-container { position: fixed; top: 16px; right: 16px; z-index: 9999; display: flex; flex-direction: column; gap: 8px; }
.toast { padding: 12px 20px; border-radius: 8px; color: #fff; font-size: 14px; font-weight: 500; box-shadow: var(--shadow-lg); animation: slideIn 0.3s ease; max-width: 350px; }
.toast-success { background: var(--green); }
.toast-error { background: var(--red); }
.toast-info { background: var(--blue); }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

#modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 9998; }
.modal-box { background: #fff; padding: 32px; border-radius: 12px; max-width: 400px; width: 90%; box-shadow: var(--shadow-lg); }
.modal-box h3 { margin-bottom: 12px; font-size: 17px; }
.modal-box p { color: var(--text-light); font-size: 14px; margin-bottom: 24px; line-height: 1.5; }
.modal-actions { display: flex; gap: 12px; justify-content: flex-end; }

@media (max-width: 768px) {
  .form-grid { grid-template-columns: 1fr; }
  .header-left h1 { display: none; }
  .demande-header { flex-direction: column; }
  .user-card { flex-direction: column; align-items: flex-start; gap: 12px; }
  .user-card-right { width: 100%; justify-content: flex-end; }
  header { padding: 0 12px; }
  #panel-demandes, #panel-users { padding: 16px; }
}
''')

# ═══════════════════════════════════════
# sw.js
# ═══════════════════════════════════════
write("sw.js", r'''
const CACHE_NAME = "popups-reflex-v7";
const ASSETS = [
  "./", "./index.html", "./manifest.json", "./icons/icon.svg", "./css/style.css",
  "./js/app.js", "./js/auth.js", "./js/config.js", "./js/demandes.js",
  "./js/firebase.js", "./js/ui.js", "./js/users.js", "./js/captures.js"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.hostname.includes("firebase") || url.hostname.includes("googleapis") || url.hostname.includes("gstatic")) return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
''')

print("\n=== RECONSTRUCTION TERMINEE ===")
print("1) Test local :  python -m http.server 8123")
print("2) Publication : git add . && git commit -m 'Reconstruction complete v7' && git push")
input("Appuyez sur Entree...")
