# -*- coding: utf-8 -*-
import os, re

BASE = os.path.dirname(os.path.abspath(__file__))

def read(p):
    with open(os.path.join(BASE, *p.split("/")), encoding="utf-8") as f:
        return f.read()

def write(p, c):
    with open(os.path.join(BASE, *p.split("/")), "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] " + p)

# ═══ 1. auth.js : ajouter resetPassword si absent ═══
auth = read("js/auth.js")
if "resetPassword" not in auth:
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
else:
    print("[OK] js/auth.js deja complet")

# ═══ 2. index.html : oeil + oubli + cloche + capture ═══
html = read("index.html")
modif = False

if 'id="toggle-pass"' not in html:
    html = html.replace(
        '<input type="password" id="login-pass" placeholder="••••••••" autocomplete="current-password">',
        '''<div class="password-wrapper">
        <input type="password" id="login-pass" placeholder="••••••••" autocomplete="current-password">
        <button type="button" class="toggle-pass" id="toggle-pass" title="Afficher">👁</button>
      </div>
      <p class="forgot-password">
        <a href="#" id="link-forgot">Mot de passe oublié ?</a>
      </p>''')
    modif = True

if 'id="bell-btn"' not in html:
    html = html.replace(
        '''      <div class="header-right">
        <div class="user-info">''',
        '''      <div class="header-right">
        <div class="notif-wrapper">
          <button class="bell-btn" id="bell-btn" title="Notifications">🔔<span class="bell-badge hidden" id="bell-badge">0</span></button>
          <div class="notif-dropdown hidden" id="notif-dropdown"></div>
        </div>
        <div class="user-info">''')
    modif = True

if 'id="f-capture"' not in html:
    html = html.replace(
        '''          <div class="field field-full">
            <label for="f-description">Description *</label>
            <textarea id="f-description" rows="4" placeholder="Décrivez la modification souhaitée…" maxlength="1000"></textarea>
          </div>''',
        '''          <div class="field field-full">
            <label for="f-description">Description *</label>
            <textarea id="f-description" rows="4" placeholder="Décrivez la modification souhaitée…" maxlength="1000"></textarea>
          </div>
          <div class="field field-full">
            <label for="f-capture">📸 Capture d'écran (optionnel, 5 Mo max)</label>
            <input type="file" id="f-capture" accept="image/*">
            <div id="capture-preview" class="capture-preview hidden"></div>
          </div>''')
    modif = True

if modif:
    write("index.html", html)
else:
    print("[OK] index.html deja complet")

# ═══ 3. CSS : blocs manquants ═══
css = read("css/style.css")
add = ""
if ".password-wrapper" not in css:
    add += '''
.password-wrapper { position: relative; display: flex; align-items: center; }
.password-wrapper input { padding-right: 42px; }
.toggle-pass { position: absolute; right: 8px; background: transparent; border: none; padding: 6px 8px; font-size: 16px; cursor: pointer; color: var(--text-light); border-radius: 4px; }
.forgot-password { text-align: right; margin: -6px 0 16px; }
.forgot-password a { color: var(--orange); font-size: 13px; text-decoration: none; font-weight: 500; }
'''
if ".bell-btn" not in css:
    add += '''
.notif-wrapper { position: relative; }
.bell-btn { position: relative; background: rgba(255,255,255,0.1); border: none; border-radius: 50%; width: 38px; height: 38px; font-size: 17px; cursor: pointer; }
.bell-badge { position: absolute; top: -5px; right: -5px; background: var(--red); color: white; font-size: 10px; font-weight: 700; min-width: 18px; height: 18px; border-radius: 9px; display: flex; align-items: center; justify-content: center; padding: 0 4px; }
.notif-dropdown { position: absolute; right: 0; top: 46px; width: 320px; background: white; border-radius: 10px; box-shadow: var(--shadow-lg); border: 1px solid var(--border); z-index: 300; max-height: 380px; overflow-y: auto; }
.notif-item { padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 13px; }
.notif-empty { padding: 20px; text-align: center; color: var(--text-light); font-size: 13px; }
'''
if ".capture-thumb" not in css:
    add += '''
.capture-thumb { max-width: 200px; max-height: 130px; border-radius: 8px; border: 1px solid var(--border); margin-top: 10px; display: block; cursor: zoom-in; }
.capture-preview img { max-width: 220px; max-height: 140px; border-radius: 8px; border: 1px solid var(--border); margin-top: 8px; display: block; }
.capture-hint { font-size: 11px; color: var(--text-light); margin-top: 4px; }
'''
if add:
    write("css/style.css", css + add)
else:
    print("[OK] css deja complet")

# ═══ 4. Synchronisation des versions -> v6 ═══
for p in ["index.html", "sw.js", "js/app.js", "js/auth.js", "js/users.js",
          "js/ui.js", "js/config.js", "js/firebase.js", "js/demandes.js", "js/captures.js"]:
    if not os.path.exists(os.path.join(BASE, p)):
        continue
    c = read(p)
    c2 = re.sub(r'\?v=\d+', '?v=6', c)
    c2 = re.sub(r'popups-reflex-v\d+', 'popups-reflex-v6', c2)
    c2 = re.sub(r'src="js/app\.js"', 'src="js/app.js?v=6"', c2)
    if c2 != c:
        write(p, c2)

print("\n=== REPARATION TERMINEE ===")
input("Appuyez sur Entree...")