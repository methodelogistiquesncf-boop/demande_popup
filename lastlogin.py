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

# ═══ 1. users.js : fonction touchLastLogin ═══
users = read("js/users.js")
modif = False

if "getDoc," not in users:
    users = users.replace("deleteDoc, getDocs, serverTimestamp", "deleteDoc, getDoc, getDocs, serverTimestamp")
    modif = True

if "touchLastLogin" not in users:
    users += '''
export async function touchLastLogin(user) {
  try {
    const ref = doc(db, "users", user.uid);
    const snap = await getDoc(ref);
    if (snap.exists()) {
      await updateDoc(ref, { lastLogin: serverTimestamp() });
    } else {
      await setDoc(ref, {
        email: user.email, nom: "", role: "demandeur",
        createdAt: serverTimestamp(), lastLogin: serverTimestamp(), active: true
      });
    }
  } catch (e) {
    console.warn("Erreur lastLogin:", e);
  }
}
'''
    modif = True

if modif:
    write("js/users.js", users)
else:
    print("[OK] js/users.js deja a jour")

# ═══ 2. app.js : import + appel + affichage + tri ═══
app = read("js/app.js")
modif = False

if "touchLastLogin }" not in app and "touchLastLogin," not in app:
    app = app.replace(
        "import { createUser, getAllUsers, updateUserRole, deleteUser } from \"./users.js",
        "import { createUser, getAllUsers, updateUserRole, deleteUser, touchLastLogin } from \"./users.js")
    modif = True

old_key = """    const key = "lastSeen_" + user.uid;
    if (!localStorage.getItem(key)) localStorage.setItem(key, String(Date.now()));"""
if "touchLastLogin(user)" not in app and old_key in app:
    app = app.replace(old_key, old_key + "\n    touchLastLogin(user);")
    modif = True

old_p = "<p>${escapeHtml(u.email)} · Créé le ${formatDate(u.createdAt)}</p>"
new_p = "<p>${escapeHtml(u.email)} · Créé le ${formatDate(u.createdAt)} · 🕐 Dernière connexion : ${formatDate(u.lastLogin)}</p>"
if old_p in app:
    app = app.replace(old_p, new_p)
    modif = True

old_render = """function renderUsers(users) {
  const container = document.getElementById("users-list");"""
new_render = """function renderUsers(users) {
  users.sort((a, b) => {
    const ta = a.lastLogin && a.lastLogin.toMillis ? a.lastLogin.toMillis() : 0;
    const tb = b.lastLogin && b.lastLogin.toMillis ? b.lastLogin.toMillis() : 0;
    return tb - ta;
  });
  const container = document.getElementById("users-list");"""
if "users.sort" not in app and old_render in app:
    app = app.replace(old_render, new_render)
    modif = True

if modif:
    write("js/app.js", app)
else:
    print("[OK] js/app.js deja a jour")

# ═══ 3. Synchronisation versions -> v9 ═══
for p in ["index.html", "js/app.js", "js/auth.js", "js/users.js", "js/ui.js",
          "js/config.js", "js/firebase.js", "js/demandes.js", "js/captures.js"]:
    c = read(p)
    c2 = c.replace("?v=8", "?v=9")
    if c2 != c:
        write(p, c2)

sw = read("sw.js")
sw2 = re.sub(r'popups-reflex-v\d+', 'popups-reflex-v9', sw)
if sw2 != sw:
    write("sw.js", sw2)

print("\n=== TERMINE ===")
input("Appuyez sur Entree...")