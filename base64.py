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

# ═══ 1. js/captures.js : compression + base64 (plus de Storage) ═══
write("js/captures.js", r'''
// Convertit une image en base64 optimise (max 1280px, JPEG 72%)
export function processCapture(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (ev) => {
      const img = new Image();
      img.onload = () => {
        const MAX = 1280;
        let w = img.width, h = img.height;
        if (w > MAX) { h = Math.round(h * MAX / w); w = MAX; }
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        canvas.getContext("2d").drawImage(img, 0, 0, w, h);
        const dataUrl = canvas.toDataURL("image/jpeg", 0.72);
        if (dataUrl.length > 900000) {
          reject(new Error("Image trop lourde même compressée"));
        } else {
          resolve(dataUrl);
        }
      };
      img.onerror = () => reject(new Error("Image illisible"));
      img.src = ev.target.result;
    };
    reader.onerror = () => reject(new Error("Fichier illisible"));
    reader.readAsDataURL(file);
  });
}
''')

# ═══ 2. js/firebase.js : sans Storage ═══
write("js/firebase.js", r'''
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { firebaseConfig } from "./config.js";

const app = initializeApp(firebaseConfig);
const secondaryApp = initializeApp(firebaseConfig, "secondary");

export const auth = getAuth(app);
export const secondaryAuth = getAuth(secondaryApp);
export const db = getFirestore(app);
''')

# ═══ 3. js/demandes.js : capture en base64 dans le document ═══
write("js/demandes.js", r'''
import { collection, doc, addDoc, updateDoc, deleteDoc, query, where, serverTimestamp, runTransaction, onSnapshot } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { db } from "./firebase.js";
import { processCapture } from "./captures.js";

const COLLECTION = "demandes";

export async function nextNumero() {
  const counterRef = doc(db, "config", "counters");
  return runTransaction(db, async (tx) => {
    const snap = await tx.get(counterRef);
    const year = new Date().getFullYear();
    let cur = snap.exists() ? snap.data() : { year: year, next: 1 };
    if (cur.year !== year) cur = { year: year, next: 1 };
    tx.set(counterRef, { year: year, next: cur.next + 1 });
    return "DEM-" + year + "-" + String(cur.next).padStart(4, "0");
  });
}

export async function createDemande(data) {
  try {
    let captureUrl = null;
    if (data.captureFile) captureUrl = await processCapture(data.captureFile);
    const numero = await nextNumero();
    const docRef = await addDoc(collection(db, COLLECTION), {
      numero: numero,
      symbole: data.symbole,
      type: data.type,
      demandeur: data.demandeur,
      demandeurEmail: data.demandeurEmail,
      description: data.description,
      captureUrl: captureUrl,
      statut: "nouveau",
      reponse: null,
      dateCreation: serverTimestamp(),
      dateReponse: null,
      dateResolution: null
    });
    return { success: true, id: docRef.id, numero: numero };
  } catch (e) { return { success: false, message: e.message }; }
}

export function listenDemandes(userEmail, role, callback) {
  let q;
  if (role === "admin" || role === "qualite") {
    q = query(collection(db, COLLECTION));
  } else {
    q = query(collection(db, COLLECTION), where("demandeurEmail", "==", userEmail));
  }
  return onSnapshot(q, (snapshot) => {
    let demandes = snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
    demandes.sort((a, b) => {
      const ta = a.dateCreation && a.dateCreation.toMillis ? a.dateCreation.toMillis() : 0;
      const tb = b.dateCreation && b.dateCreation.toMillis ? b.dateCreation.toMillis() : 0;
      return tb - ta;
    });
    callback(demandes);
  });
}

export async function updateStatut(id, statut) {
  try {
    const data = { statut: statut };
    if (statut === "resolu") data.dateResolution = serverTimestamp();
    await updateDoc(doc(db, COLLECTION, id), data);
    return { success: true };
  } catch (e) { return { success: false, message: e.message }; }
}

export async function repondreDemande(id, reponse, statut) {
  try {
    await updateDoc(doc(db, COLLECTION, id), {
      reponse: reponse, statut: statut,
      dateReponse: serverTimestamp(),
      dateResolution: statut === "resolu" ? serverTimestamp() : null
    });
    return { success: true };
  } catch (e) { return { success: false, message: e.message }; }
}

export async function deleteDemande(id) {
  try {
    await deleteDoc(doc(db, COLLECTION, id));
    return { success: true };
  } catch (e) { return { success: false, message: e.message }; }
}
''')

# ═══ 4. js/app.js : visionneuse au clic (lightbox) ═══
app = read("js/app.js")
modif = False

old_img = """${d.captureUrl ? '<a href="' + d.captureUrl + '" target="_blank" rel="noopener"><img class="capture-thumb" src="' + d.captureUrl + '" alt="Capture"></a>' : ""}"""
new_img = """${d.captureUrl ? '<img class="capture-thumb" src="' + d.captureUrl + '" alt="Capture">' : ""}"""
if old_img in app:
    app = app.replace(old_img, new_img)
    modif = True

old_save = """      const result = await repondreDemande(id, reponse, statut);
      if (result.success) showToast("Réponse enregistrée", "success");
      else showToast("Erreur : " + result.message, "error");
    });
  });
}"""
new_save = """      const result = await repondreDemande(id, reponse, statut);
      if (result.success) showToast("Réponse enregistrée", "success");
      else showToast("Erreur : " + result.message, "error");
    });
  });

  // Visionneuse capture : clic = plein ecran
  container.querySelectorAll(".capture-thumb").forEach(img => {
    img.addEventListener("click", () => {
      const overlay = document.createElement("div");
      overlay.className = "lightbox";
      const big = document.createElement("img");
      big.src = img.src;
      big.alt = "Capture";
      overlay.appendChild(big);
      overlay.addEventListener("click", () => overlay.remove());
      document.body.appendChild(overlay);
    });
  });
}"""
if "lightbox" not in app and old_save in app:
    app = app.replace(old_save, new_save)
    modif = True

if modif:
    write("js/app.js", app)
else:
    print("[OK] js/app.js deja a jour")

# ═══ 5. CSS : lightbox ═══
css = read("css/style.css")
if ".lightbox" not in css:
    css += '''
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.85); display: flex; align-items: center; justify-content: center; z-index: 10000; cursor: zoom-out; padding: 20px; }
.lightbox img { max-width: 95vw; max-height: 95vh; border-radius: 8px; box-shadow: 0 10px 40px rgba(0,0,0,0.5); }
'''
    write("css/style.css", css)

# ═══ 6. Synchronisation versions -> v8 ═══
for p in ["index.html", "js/app.js", "js/auth.js", "js/users.js", "js/ui.js",
          "js/config.js", "js/firebase.js", "js/demandes.js", "js/captures.js"]:
    c = read(p)
    c2 = re.sub(r'from "(\./[a-z]+\.js)"', r'from "\1?v=8"', c)
    if c2 != c:
        write(p, c2)

html = read("index.html")
html2 = re.sub(r'src="js/app\.js(\?v=\d+)"?', 'src="js/app.js?v=8"', html)
if html2 != html:
    write("index.html", html2)

sw = read("sw.js")
sw2 = re.sub(r'popups-reflex-v\d+', 'popups-reflex-v8', sw)
if sw2 != sw:
    write("sw.js", sw2)

print("\n=== BASE64 PRET ===")
print("Plus besoin de Firebase Storage !")
input("Appuyez sur Entree...")