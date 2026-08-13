# -*- coding: utf-8 -*-
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def read(p):
    with open(os.path.join(BASE, *p.split("/")), encoding="utf-8") as f:
        return f.read()

def write(p, c):
    with open(os.path.join(BASE, *p.split("/")), "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] " + p)

# ═══ 1. index.html : champ de recherche ═══
html = read("index.html")
old = """        <div class="list-header">
          <h2>📋 Demandes</h2>
          <div class="list-filters">"""
new = """        <div class="list-header">
          <h2>📋 Demandes</h2>
          <div class="search-box">
            <input type="text" id="search-input" placeholder="🔍 Symbole, numéro, demandeur…">
          </div>
          <div class="list-filters">"""
if "search-input" not in html and old in html:
    write("index.html", html.replace(old, new))
else:
    print("[OK] index.html deja a jour")

# ═══ 2. CSS : style du champ ═══
css = read("css/style.css")
if ".search-box" not in css:
    css += '''
.search-box { flex: 1; min-width: 180px; max-width: 340px; }
.search-box input { width: 100%; padding: 8px 14px; border: 1.5px solid var(--border); border-radius: 8px; font-family: inherit; font-size: 13px; background: #fff; }
.search-box input:focus { outline: none; border-color: var(--orange); box-shadow: 0 0 0 3px rgba(224,90,0,0.1); }
'''
    write("css/style.css", css)
else:
    print("[OK] css deja a jour")

# ═══ 3. app.js : état + écouteur + filtre ═══
app = read("js/app.js")
modif = False

if "currentSearch" not in app:
    app = app.replace(
        'let currentFilter = "all";',
        'let currentFilter = "all";\nlet currentSearch = "";')
    modif = True

anchor = '  document.getElementById("btn-submit-demande").addEventListener("click", handleSubmitDemande);'
if "search-input" not in app and anchor in app:
    app = app.replace(anchor,
        '''  document.getElementById("search-input").addEventListener("input", (e) => {
    currentSearch = e.target.value.toLowerCase().trim();
    renderDemandes();
  });

''' + anchor)
    modif = True

old_filter = """  let filtered = allDemandes;
  if (currentFilter !== "all") filtered = allDemandes.filter(d => d.statut === currentFilter);"""
new_filter = """  let filtered = allDemandes;
  if (currentFilter !== "all") filtered = allDemandes.filter(d => d.statut === currentFilter);
  if (currentSearch) {
    filtered = filtered.filter(d =>
      (d.symbole || "").toLowerCase().includes(currentSearch) ||
      (d.numero || "").toLowerCase().includes(currentSearch) ||
      (d.demandeur || "").toLowerCase().includes(currentSearch));
  }"""
if "currentSearch)" not in app and old_filter in app:
    app = app.replace(old_filter, new_filter)
    modif = True

old_empty = "(currentFilter !== \"all\" ? \"avec ce statut\" : \"pour le moment\")"
new_empty = "(currentSearch ? \"pour cette recherche\" : (currentFilter !== \"all\" ? \"avec ce statut\" : \"pour le moment\"))"
if old_empty in app:
    app = app.replace(old_empty, new_empty)
    modif = True

if modif:
    write("js/app.js", app)
else:
    print("[OK] js/app.js deja a jour")

# ═══ 4. Versions -> v10 ═══
for p in ["index.html", "js/app.js", "js/auth.js", "js/users.js", "js/ui.js",
          "js/config.js", "js/firebase.js", "js/demandes.js", "js/captures.js"]:
    c = read(p)
    c2 = c.replace("?v=9", "?v=10")
    if c2 != c:
        write(p, c2)

sw = read("sw.js")
import re
sw2 = re.sub(r'popups-reflex-v\d+', 'popups-reflex-v10', sw)
if sw2 != sw:
    write("sw.js", sw2)

print("\n=== RECHERCHE PRETE ===")
input("Appuyez sur Entree...")