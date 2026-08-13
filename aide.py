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

old_tab = """        <button class="tab-btn hidden" data-tab="users" id="tab-users">👥 Utilisateurs</button>
      </nav>"""
new_tab = """        <button class="tab-btn hidden" data-tab="users" id="tab-users">👥 Utilisateurs</button>
        <button class="tab-btn" data-tab="aide">❓ Aide</button>
      </nav>"""
if 'data-tab="aide"' not in html and old_tab in html:
    html = html.replace(old_tab, new_tab)
    modif = True

old_panel = """        <div id="users-list"></div>
      </section>
    </main>
  </div>"""
new_panel = """        <div id="users-list"></div>
      </section>
    </main>

    <main id="panel-aide" class="hidden">
      <section class="admin-section">
        <h2>❓ Aide — Fonctionnement du site</h2>

        <div class="aide-block">
          <h3>👤 Vous êtes Demandeur</h3>
          <ul>
            <li>Connectez-vous puis remplissez le formulaire <strong>📝 Nouvelle demande</strong>.</li>
            <li>Indiquez le <strong>symbole</strong> de la popup, le <strong>type</strong> (création, modification, suppression), votre nom et une <strong>description</strong> précise.</li>
            <li>Ajoutez si besoin une <strong>📸 capture d'écran</strong> (5 Mo max) — cliquez dessus pour l'agrandir.</li>
            <li>Un <strong>numéro automatique</strong> (ex : DEM-2026-0001) est attribué à chaque demande.</li>
            <li>Suivez le <strong>statut</strong> : 🆕 Nouveau →  En cours → ✅ Résolu.</li>
            <li>Quand la Qualité répond : <strong>cloche 🔔</strong> avec badge rouge + réponse affichée sous votre demande.</li>
          </ul>
        </div>

        <div class="aide-block">
          <h3>📧 Vous êtes Qualité</h3>
          <ul>
            <li>Vous voyez <strong>toutes les demandes</strong> de tous les utilisateurs.</li>
            <li>La <strong>cloche 🔔</strong> signale les nouvelles demandes en temps réel.</li>
            <li>Pour traiter : choisissez un <strong>statut</strong>, rédigez une <strong>réponse</strong>, cliquez <strong>💾 Enregistrer</strong>.</li>
            <li>Utilisez la <strong>recherche 🔍</strong> (symbole, numéro, demandeur) et les filtres de statut.</li>
            <li>Bouton 🗑️ pour supprimer une demande.</li>
          </ul>
        </div>

        <div class="aide-block">
          <h3>👑 Vous êtes Admin</h3>
          <ul>
            <li>Tout ce que fait la Qualité, plus l'onglet <strong>👥 Utilisateurs</strong>.</li>
            <li><strong>Créer un compte</strong> : email + nom + mot de passe (6 caractères min) + rôle.</li>
            <li><strong>Changer un rôle</strong> via le menu déroulant de chaque utilisateur.</li>
            <li><strong>Supprimer un compte</strong> avec le bouton 🗑️.</li>
            <li>La <strong>🕐 dernière connexion</strong> de chaque utilisateur est affichée.</li>
          </ul>
        </div>

        <div class="aide-block">
          <h3>🔑 Connexion & divers</h3>
          <ul>
            <li>👁 Le bouton œil permet de <strong>voir le mot de passe</strong> pendant la saisie.</li>
            <li>« <strong>Mot de passe oublié ?</strong> » envoie un email de réinitialisation.</li>
            <li>📱 Sur mobile : menu du navigateur → « Ajouter à l'écran d'accueil » pour installer l'application.</li>
            <li>En cas de problème, contactez l'administrateur du site.</li>
          </ul>
        </div>
      </section>
    </main>
  </div>"""
if 'id="panel-aide"' not in html and old_panel in html:
    html = html.replace(old_panel, new_panel)
    modif = True

if modif:
    write("index.html", html)
else:
    print("[OK] index.html deja a jour")

app = read("js/app.js")
old_tabs = """      document.getElementById("panel-demandes").classList.toggle("hidden", btn.dataset.tab !== "demandes");
      document.getElementById("panel-users").classList.toggle("hidden", btn.dataset.tab !== "users");"""
new_tabs = """      document.getElementById("panel-demandes").classList.toggle("hidden", btn.dataset.tab !== "demandes");
      document.getElementById("panel-users").classList.toggle("hidden", btn.dataset.tab !== "users");
      document.getElementById("panel-aide").classList.toggle("hidden", btn.dataset.tab !== "aide");"""
if "panel-aide" not in app and old_tabs in app:
    write("js/app.js", app.replace(old_tabs, new_tabs))
else:
    print("[OK] js/app.js deja a jour")

css = read("css/style.css")
if ".aide-block" not in css:
    css += '''
.aide-block { margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
.aide-block:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
.aide-block h3 { margin-bottom: 10px; font-size: 15px; color: var(--navy); }
.aide-block ul { padding-left: 22px; }
.aide-block li { margin-bottom: 7px; font-size: 14px; line-height: 1.6; }
'''
    write("css/style.css", css)
else:
    print("[OK] css deja a jour")

for p in ["index.html", "js/app.js", "js/auth.js", "js/users.js", "js/ui.js",
          "js/config.js", "js/firebase.js", "js/demandes.js", "js/captures.js"]:
    c = read(p)
    c2 = c.replace("?v=10", "?v=11")
    if c2 != c:
        write(p, c2)

sw = read("sw.js")
sw2 = re.sub(r'popups-reflex-v\d+', 'popups-reflex-v11', sw)
if sw2 != sw:
    write("sw.js", sw2)

print("\n=== PAGE AIDE PRETE ===")
input("Appuyez sur Entree...")