# -*- coding: utf-8 -*-
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def read(p):
    with open(os.path.join(BASE, *p.split("/")), encoding="utf-8") as f:
        return f.read()

def write(p, c):
    full = os.path.join(BASE, *p.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] " + p)

def patch(p, old, new):
    c = read(p)
    if old not in c:
        print("[!!] " + p + " : texte introuvable" if new not in c else "[OK] " + p + " deja a jour")
        return
    write(p, c.replace(old, new))

# ═══ index.html : cloche + champ capture ═══
patch("index.html",
    '''      <div class="header-right">
        <div class="user-info">''',
    '''      <div class="header-right">
        <div class="notif-wrapper">
          <button class="bell-btn" id="bell-btn" title="Notifications">🔔<span class="bell-badge hidden" id="bell-badge">0</span></button>
          <div class="notif-dropdown hidden" id="notif-dropdown"></div>
        </div>
        <div class="user-info">''')

patch("index.html",
    '''          <div class="field field-full">
            <label for="f-description">Description *</label>
            <textarea id="f-description" rows="4" placeholder="Décrivez la modification souhaitée…" maxlength="1000"></textarea>
          </div>''',
    '''          <div class="field field-full">
            <label for="f-description">Description *</label>
            <textarea id="f-description" rows="4" placeholder="Décrivez la modification souhaitée…" maxlength="1000"></textarea>
          </div>
          <div class="field field-full">
            <label for="f-capture"> Capture d'écran (optionnel, 5 Mo max)</label>
            <input type="file" id="f-capture" accept="image/*">
            <div id="capture-preview" class="capture-preview hidden"></div>
          </div>''')

# ═══ CSS : styles cloche + captures ═══
css = read("css/style.css")
if ".bell-btn" not in css:
    css += '''
/* ═══ CLOCHE NOTIFICATIONS ═══ */
.notif-wrapper { position: relative; }
.bell-btn { position: relative; background: rgba(255,255,255,0.1); border: none; border-radius: 50%; width: 38px; height: 38px; font-size: 17px; cursor: pointer; }
.bell-btn:hover { background: rgba(255,255,255,0.25); }
.bell-badge { position: absolute; top: -5px; right: -5px; background: var(--red); color: white; font-size: 10px; font-weight: 700; min-width: 18px; height: 18px; border-radius: 9px; display: flex; align-items: center; justify-content: center; padding: 0 4px; }
.notif-dropdown { position: absolute; right: 0; top: 46px; width: 320px; background: white; border-radius: 10px; box-shadow: var(--shadow-lg); border: 1px solid var(--border); z-index: 300; max-height: 380px; overflow-y: auto; }
.notif-item { padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 13px; }
.notif-item:last-child { border-bottom: none; }
.notif-empty { padding: 20px; text-align: center; color: var(--text-light); font-size: 13px; }
/* ═══ CAPTURES ═══ */
.capture-thumb { max-width: 200px; max-height: 130px; border-radius: 8px; border: 1px solid var(--border); margin-top: 10px; display: block; cursor: zoom-in; }
.capture-thumb:hover { opacity: 0.85; }
.capture-preview img { max-width: 220px; max-height: 140px; border-radius: 8px; border: 1px solid var(--border); margin-top: 8px; display: block; }
.capture-hint { font-size: 11px; color: var(--text-light); margin-top: 4px; }
'''
    write("css/style.css", css)

# ═══ js/firebase.js : + Storage ═══
write("js/firebase.js", r'''import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { getStorage } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-storage.js";
import { firebaseConfig } from "./config.js?v=4";

const app = initializeApp(firebaseConfig);
const secondaryApp = initializeApp(firebaseConfig, "secondary");

export const auth = getAuth(app);
export const secondaryAuth = getAuth(secondaryApp);
export const db = getFirestore(app);
export const storage = getStorage(app);
''')

# ═══ js/captures.js : upload ═══
write("js/captures.js", r'''import { ref, uploadBytes, getDownloadURL } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-storage.js";
import { storage } from "./firebase.js?v=4";

export async function uploadCapture(file) {
  const clean = file.name.replace(/[^\w.\-]/g, "_");
  const r = ref(storage, "captures/" + Date.now() + "_" + clean);
  await uploadBytes(r, file);
  return await getDownloadURL(r);
}
''')

# ═══ js/demandes.js : numérotation + temps réel + capture ═══
write("js/demandes.js", r'''import {
  collection, doc, addDoc, updateDoc, deleteDoc, query, where,
  serverTimestamp, runTransaction, onSnapshot
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { db } from "./firebase.js?v=4";
import { uploadCapture } from "./captures.js?v=4";

const COLLECTION = "demandes";

// Numéro automatique DEM-AAAA-0000 (transaction = aucun doublon)
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
    if (data.captureFile) captureUrl = await uploadCapture(data.captureFile);
    const numero = await nextNumero();
    const docRef = await addDoc(collection(db, COLLECTION), {
      numero,
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
  } catch (e) {
    return { success: false, message: e.message };
  }
}

// Écoute temps réel (cloche + liste toujours à jour)
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
      reponse: reponse,
      statut: statut,
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

print("[OK] js/demandes.js (partie 1/2)")
print("Suite dans le meme fichier... voir app.js ci-dessous")