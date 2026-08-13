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

html = read("index.html")
modif = False

# 1. Retire la section de la page Aide (elle demenage sur le login)
old_help = """        <div class="aide-block">
          <h3>🔒 Initialiser votre mot de passe (1ʳᵉ connexion)</h3>
          <ul>
            <li>Votre administrateur crée votre compte avec un <strong>mot de passe provisoire</strong> et vous le communique directement (email, téléphone…).</li>
            <li>Connectez-vous une première fois avec ce mot de passe provisoire.</li>
            <li>Pour définir <strong>votre propre mot de passe</strong>, cliquez sur « <strong>Mot de passe oublié ?</strong> » sous le formulaire de connexion.</li>
            <li>Un email de réinitialisation vous est envoyé : ouvrez-le et cliquez sur le lien.</li>
            <li>Choisissez votre nouveau mot de passe (6 caractères minimum), puis reconnectez-vous avec.</li>
          </ul>
        </div>

"""
if old_help in html:
    html = html.replace(old_help, "")
    modif = True

# 2. Ajoute l'encart depliable sur la page login
anchor = '      <p id="login-error" class="error-text hidden"></p>'
new_login = """      <p id="login-error" class="error-text hidden"></p>
      <details class="login-help">
        <summary>🔒 Première connexion ? Initialiser votre mot de passe</summary>
        <ol>
          <li>Votre administrateur vous a communiqué un <strong>mot de passe provisoire</strong> : connectez-vous avec.</li>
          <li>Cliquez ensuite sur « <strong>Mot de passe oublié ?</strong> ».</li>
          <li>Ouvrez l'email reçu, cliquez sur le lien et choisissez <strong>votre propre mot de passe</strong> (6 caractères min).</li>
          <li>Reconnectez-vous avec votre nouveau mot de passe.</li>
        </ol>
      </details>"""
if "login-help" not in html and anchor in html:
    html = html.replace(anchor, new_login)
    modif = True

if modif:
    write("index.html", html)
else:
    print("[OK] index.html deja a jour")

# 3. CSS
css = read("css/style.css")
if ".login-help" not in css:
    css += '''
.login-help { margin-top: 18px; font-size: 13px; color: var(--text-light); }
.login-help summary { cursor: pointer; color: var(--orange); font-weight: 600; }
.login-help summary:hover { text-decoration: underline; }
.login-help ol { margin-top: 10px; padding-left: 20px; }
.login-help li { margin-bottom: 6px; line-height: 1.5; }
'''
    write("css/style.css", css)
else:
    print("[OK] css deja a jour")

# 4. Versions -> v13
for p in ["index.html", "js/app.js", "js/auth.js", "js/users.js", "js/ui.js",
          "js/config.js", "js/firebase.js", "js/demandes.js", "js/captures.js"]:
    c = read(p)
    c2 = c.replace("?v=12", "?v=13")
    if c2 != c:
        write(p, c2)

sw = read("sw.js")
sw2 = re.sub(r'popups-reflex-v\d+', 'popups-reflex-v13', sw)
if sw2 != sw:
    write("sw.js", sw2)

print("\n=== ENCART LOGIN PRET ===")
input("Appuyez sur Entree...")