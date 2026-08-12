# -*- coding: utf-8 -*-
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def read(p):
    with open(os.path.join(BASE, *p.split("/")), encoding="utf-8") as f:
        return f.read()

def write(p, c):
    with open(os.path.join(BASE, *p.split("/")), "w", encoding="utf-8") as f:
        f.write(c)

# ═══ 1. index.html : œil + mot de passe oublié ═══
html = read("index.html")
if 'id="toggle-pass"' in html:
    print("[OK] index.html deja a jour")
else:
    old = '<input type="password" id="login-pass" placeholder="••••••••" autocomplete="current-password">'
    new = '''<div class="password-wrapper">
        <input type="password" id="login-pass" placeholder="••••••••" autocomplete="current-password">
        <button type="button" class="toggle-pass" id="toggle-pass" title="Afficher">👁</button>
      </div>
      <p class="forgot-password">
        <a href="#" id="link-forgot">Mot de passe oublié ?</a>
      </p>'''
    if old in html:
        write("index.html", html.replace(old, new))
        print("[OK] index.html modifie")
    else:
        print("[!!] index.html : champ login-pass introuvable")

# ═══ 2. CSS ═══
css = read("css/style.css")
if ".password-wrapper" in css:
    print("[OK] css deja a jour")
else:
    css += '''
/* ═══ TOGGLE PASS + OUBLI ═══ */
.password-wrapper { position: relative; display: flex; align-items: center; }
.password-wrapper input { padding-right: 42px; }
.toggle-pass { position: absolute; right: 8px; background: transparent; border: none; padding: 6px 8px; font-size: 16px; cursor: pointer; color: var(--text-light); border-radius: 4px; }
.toggle-pass:hover { background: rgba(0,0,0,0.05); }
.forgot-password { text-align: right; margin: -6px 0 16px; }
.forgot-password a { color: var(--orange); font-size: 13px; text-decoration: none; font-weight: 500; }
.forgot-password a:hover { text-decoration: underline; }
'''
    write("css/style.css", css)
    print("[OK] css modifie")

# ═══ 3. auth.js : fonction resetPassword ═══
auth = read("js/auth.js")
if "resetPassword" in auth:
    print("[OK] auth.js deja a jour")
else:
    auth += '''
// Envoyer un email de réinitialisation
export async function resetPassword(email) {
  try {
    const { sendPasswordResetEmail } = await import("https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js");
    await sendPasswordResetEmail(auth, email);
    return { success: true };
  } catch (error) {
    let message = "Erreur lors de l'envoi";
    if (error.code === "auth/user-not-found" || error.code === "auth/invalid-email") message = "Aucun compte trouvé avec cet email";
    if (error.code === "auth/too-many-requests") message = "Trop de tentatives, réessayez plus tard";
    return { success: false, message };
  }
}
'''
    write("js/auth.js", auth)
    print("[OK] auth.js modifie")

# ═══ 4. app.js : import + événements ═══
app = read("js/app.js")
modif = False
if "resetPassword" not in app:
    app = app.replace("getCurrentRole } from", "getCurrentRole, resetPassword } from")
    modif = True

if "toggle-pass" not in app:
    anchor = 'document.getElementById("btn-create-user").addEventListener("click", handleCreateUser);'
    events = anchor + '''

  // Toggle afficher/masquer mot de passe
  document.getElementById("toggle-pass").addEventListener("click", () => {
    const input = document.getElementById("login-pass");
    const btn = document.getElementById("toggle-pass");
    if (input.type === "password") {
      input.type = "text";
      btn.textContent = "🙈";
      btn.title = "Masquer";
    } else {
      input.type = "password";
      btn.textContent = "👁";
      btn.title = "Afficher";
    }
  });

  // Mot de passe oublié
  document.getElementById("link-forgot").addEventListener("click", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    if (!email) {
      showToast("Saisissez d'abord votre email ci-dessus", "error");
      document.getElementById("login-email").focus();
      return;
    }
    const result = await resetPassword(email);
    if (result.success) {
      showToast("📧 Email de réinitialisation envoyé à " + email, "success");
    } else {
      showToast(result.message, "error");
    }
  });'''
    app = app.replace(anchor, events)
    modif = True

if modif:
    write("js/app.js", app)
    print("[OK] app.js modifie")
else:
    print("[OK] app.js deja a jour")

# ═══ 5. Anti-cache : v2 -> v3 partout + nouveau nom de cache SW ═══
for p in ["index.html", "js/app.js", "js/auth.js", "js/users.js",
          "js/demandes.js", "js/ui.js", "js/firebase.js"]:
    c = read(p)
    if "?v=2" in c:
        write(p, c.replace("?v=2", "?v=3"))
        print("[OK] " + p + " -> v3")

sw = read("sw.js")
if "popups-reflex-v1" in sw:
    write("sw.js", sw.replace("popups-reflex-v1", "popups-reflex-v2"))
    print("[OK] sw.js : cache invalide (v2)")

print("\n=== TERMINE ===")
input("Appuyez sur Entree...")