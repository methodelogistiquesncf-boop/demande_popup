# -*- coding: utf-8 -*-
import os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))

def patch(path, old, new):
    full = os.path.join(BASE, *path.split("/"))
    if not os.path.exists(full):
        print("[ERREUR] " + path + " introuvable")
        return
    with open(full, encoding="utf-8") as f:
        content = f.read()
    if old in content:
        shutil.copyfile(full, full + ".bak")  # sauvegarde auto
        with open(full, "w", encoding="utf-8") as f:
            f.write(content.replace(old, new))
        print("[OK] " + path + " modifie")
    elif new in content:
        print("[OK] " + path + " deja a jour")
    else:
        print("[!!] " + path + " : texte introuvable, verifiez manuellement")

# 1. config.js : lecteur -> demandeur
patch("js/config.js",
    'LECTEUR: "lecteur"',
    'DEMANDEUR: "demandeur"')

# 2. auth.js
patch("js/auth.js",
    'currentRole = "lecteur";',
    'currentRole = "demandeur";')

patch("js/auth.js",
    '      return userDoc.data().role || "lecteur";',
    '      const role = userDoc.data().role || "demandeur";\n      return role === "lecteur" ? "demandeur" : role;')

patch("js/auth.js",
    'return "lecteur";',
    'return "demandeur";')

# 3. ui.js
patch("js/ui.js",
    'const labels = { admin: "Admin", qualite: "Qualité", lecteur: "Lecteur" };',
    'const labels = { admin: "Admin", qualite: "Qualité", demandeur: "Demandeur", lecteur: "Demandeur" };')

# 4. style.css
patch("css/style.css",
    '.role-badge.lecteur {',
    '.role-badge.demandeur, .role-badge.lecteur {')

# 5. index.html
patch("index.html",
    '<option value="lecteur">👁 Lecteur (fait des demandes)</option>',
    '<option value="demandeur">👤 Demandeur (fait des demandes)</option>')

# 6. app.js : formulaire visible pour tous
patch("js/app.js",
    'document.getElementById("section-form").classList.toggle("hidden", role !== ROLES.LECTEUR);',
    'document.getElementById("section-form").classList.remove("hidden");')

# 7. app.js : liste des rôles dans la gestion utilisateurs
patch("js/app.js",
    '<option value="lecteur" ${u.role === "lecteur" ? "selected" : ""}>👁 Lecteur</option>',
    '<option value="demandeur" ${u.role === "demandeur" || u.role === "lecteur" ? "selected" : ""}>👤 Demandeur</option>')

# 8. demandes.js : le demandeur voit SES demandes (sans index Firestore)
old = '''      // Lecteur voit seulement ses demandes
      q = query(
        collection(db, COLLECTION),
        where("demandeurEmail", "==", userEmail),
        orderBy("dateCreation", "desc")
      );
    }
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));'''

new = '''      // Demandeur voit seulement SES demandes
      q = query(
        collection(db, COLLECTION),
        where("demandeurEmail", "==", userEmail)
      );
    }
    const snapshot = await getDocs(q);
    let demandes = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    demandes.sort((a, b) => {
      const ta = a.dateCreation && a.dateCreation.toMillis ? a.dateCreation.toMillis() : 0;
      const tb = b.dateCreation && b.dateCreation.toMillis ? b.dateCreation.toMillis() : 0;
      return tb - ta;
    });
    return demandes;'''

patch("js/demandes.js", old, new)

print("\n=== TERMINÉ ===")
print("Rechargez votre page avec Ctrl + F5")
input("Appuyez sur Entrée pour fermer...")