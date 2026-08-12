import os, re

BASE = os.path.dirname(os.path.abspath(__file__))

def patch(path, old, new):
    full = os.path.join(BASE, *path.split("/"))
    with open(full, encoding="utf-8") as f:
        content = f.read()
    if old not in content and new in content:
        print(f"[OK] {path} deja a jour")
        return
    if old not in content:
        print(f"[!!] {path} : texte introuvable")
        return
    with open(full, "w", encoding="utf-8") as f:
        f.write(content.replace(old, new))
    print(f"[OK] {path} modifie")

# 1. index.html : ajouter œil + mot de passe oublié
patch("index.html",
    '''<div class="field">
      <label for="login-pass">Mot de passe</label>
      <input type="password" id="login-pass" placeholder="••••••••" autocomplete="current-password">
    </div>''',
    '''<div class="field">
      <label for="login-pass">Mot de passe</label>
      <div class="password-wrapper">
        <input type="password" id="login-pass" placeholder="••••••••" autocomplete="current-password">
        <button type="button" class="toggle-pass" id="toggle-pass" title="Afficher">👁</button>
      </div>
    </div>
    <p class="forgot-password">
      <a href="#" id="link-forgot">Mot de passe oublié ?</a>
    </p>''')

# 2. css/style.css : ajouter le style
css_add = '''
/* ═══ TOGGLE MOT DE PASSE + OUBLIÉ ═══ */
.password-wrapper { position: relative; display: flex; align-items: center; }
.password-wrapper input { padding-right: 42px; }
.toggle-pass {
  position: absolute; right: 8px; background: transparent; border: none;
  padding: 6px 8px; font-size: 16px; cursor: pointer; color: var(--text-light);
  line-height: 1; border-radius: 4px;
}
.toggle-pass:hover { background: rgba(0,0,0,0.05); }
.forgot-password { text-align: right; margin-top: -8px; margin-bottom: 16px; }
.forgot-password a {
  color: var(--orange); font-size: 13px; text-decoration: none; font-weight: 500;
}
.forgot-password a:hover { text-decoration: underline; }
'''
css_path = os.path.join(BASE, "css/style.css")
with open(css_path, encoding="utf-8") as f:
    css = f.read()
if ".password-wrapper" in css:
    print("[OK] css/style.css deja a jour")
else:
    css = css.replace("/* ═══ RESPONSIVE", css_add + "\n/* ═══ RESPONSIVE")
    with open(css_path, "w", encoding="utf-8") as f:
        f.write(css)
    print("[OK] css/style.css modifie")

# 3. auth.js : ajouter resetPassword
auth_add = '''
// Envoyer un email de réinitialisation
export async function resetPassword(email) {
  try {
    const { sendPasswordResetEmail } = await import(
      "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js"
    );
    await sendPasswordResetEmail(auth, email);
    return { success: true };
  } catch (error) {
    let message = "Erreur lors de l'envoi";
    switch (error.code) {
      case "auth/user-not-found":
      case "auth/invalid-email":
        message = "Aucun compte trouvé avec cet email"; break;
      case "auth/too-many-requests":
        message = "Trop de tentatives, réessayez plus tard"; break;
    }
    return { success: false, message };
  }
}

'''
auth_path = os.path.join(BASE, "js/auth.js")
with open(auth_path, encoding="utf-8") as f:
    auth = f.read()
if "resetPassword" in auth:
    print("[OK] js/auth.js deja a jour")
else:
    auth = auth_add + auth
    with open(auth_path, "w", encoding="utf-8") as f:
        f.write(auth)
    print("[OK] js/auth.js modifie")

# 4. app.js : importer resetPassword
patch("js/app.js",
    'import { initAuth, login, logout, getCurrentUser, getCurrentRole } from "./auth.js',
    'import { initAuth, login, logout, getCurrentUser, getCurrentRole, resetPassword } from "./auth.js')

# 5. app.js : ajouter les events
events_add = '''
  // Toggle afficher/masquer mot de passe
  document.getElementById("toggle-pass").addEventListener("click", () => {
    const input = document.getElementById("login-pass");
    const btn = document.getElementById("toggle-pass");
    if (input.type === "password") {
      input.type = "text"; btn.textContent = "🙈"; btn.title = "Masquer";
    } else {
      input.type = "password"; btn.textContent = "👁"; btn.title = "Afficher";
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
  });
'''

app_path = os.path.join(BASE, "js/app.js")
with open(app_path, encoding="utf-8") as f:
    app = f.read()
if 'toggle-pass' in app:
    print("[OK] js/app.js deja a jour")
else:
    app = app.replace("  // Créer utilisateur", events_add + "\n  // Créer utilisateur")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app)
    print("[OK] js/app.js modifie")

print("\n=== TERMINE ===")
input("Appuyez sur Entree...")