# -*- coding: utf-8 -*-
import os

BASE = os.path.dirname(os.path.abspath(__file__))

def write(p, c):
    full = os.path.join(BASE, *p.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(c)
    print("[OK] " + p)

write("js/config.js", r'''
export const firebaseConfig = {
  apiKey: "AIzaSyAgyjanFGdNCe23ptWtrLgI1wUSZij5y9I",
  authDomain: "popup-67e28.firebaseapp.com",
  projectId: "popup-67e28",
  storageBucket: "popup-67e28.firebasestorage.app",
  messagingSenderId: "1089603775753",
  appId: "1:1089603775753:web:0eda8de1f0b5d6e34af7d8"
};

export const ROLES = { ADMIN: "admin", QUALITE: "qualite", DEMANDEUR: "demandeur" };
''')

write("js/firebase.js", r'''
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { getStorage } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-storage.js";
import { firebaseConfig } from "./config.js";

const app = initializeApp(firebaseConfig);
const secondaryApp = initializeApp(firebaseConfig, "secondary");

export const auth = getAuth(app);
export const secondaryAuth = getAuth(secondaryApp);
export const db = getFirestore(app);
export const storage = getStorage(app);
''')

write("js/captures.js", r'''
import { ref, uploadBytes, getDownloadURL } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-storage.js";
import { storage } from "./firebase.js";

export async function uploadCapture(file) {
  const clean = file.name.replace(/[^\w.\-]/g, "_");
  const r = ref(storage, "captures/" + Date.now() + "_" + clean);
  await uploadBytes(r, file);
  return getDownloadURL(r);
}
''')

write("js/ui.js", r'''
export function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = "toast toast-" + type;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

export function showConfirm(title, message) {
  return new Promise((resolve) => {
    const overlay = document.getElementById("modal-overlay");
    document.getElementById("modal-title").textContent = title;
    document.getElementById("modal-message").textContent = message;
    overlay.classList.remove("hidden");
    const cleanup = () => {
      overlay.classList.add("hidden");
      document.getElementById("modal-confirm").onclick = null;
      document.getElementById("modal-cancel").onclick = null;
    };
    document.getElementById("modal-confirm").onclick = () => { cleanup(); resolve(true); };
    document.getElementById("modal-cancel").onclick = () => { cleanup(); resolve(false); };
  });
}

export function formatDate(ts) {
  if (!ts) return "—";
  const d = ts.toDate ? ts.toDate() : new Date(ts);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function getRoleLabel(role) {
  const labels = { admin: "Admin", qualite: "Qualité", demandeur: "Demandeur", lecteur: "Demandeur" };
  return labels[role] || role;
}

export function getStatutLabel(s) {
  const labels = { nouveau: "Nouveau", en_cours: "En cours", resolu: "Résolu" };
  return labels[s] || s;
}

export function getTypeLabel(t) {
  const labels = { creation: "Création", modification: "Modification", suppression: "Suppression" };
  return labels[t] || t;
}
''')

write("js/auth.js", r'''
import { signInWithEmailAndPassword, signOut, onAuthStateChanged, sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { doc, getDoc } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { auth, db } from "./firebase.js";

let currentUser = null;
let currentRole = "demandeur";

export function initAuth(callback) {
  onAuthStateChanged(auth, async (user) => {
    if (user) {
      currentUser = user;
      currentRole = await getUserRole(user.uid);
      callback(user, currentRole);
    } else {
      currentUser = null;
      currentRole = "demandeur";
      callback(null, null);
    }
  });
}

export async function login(email, password) {
  try {
    await signInWithEmailAndPassword(auth, email, password);
    return { success: true };
  } catch (error) {
    let message = "Erreur de connexion";
    if (error.code === "auth/user-not-found") message = "Aucun compte trouvé avec cet email";
    else if (error.code === "auth/wrong-password" || error.code === "auth/invalid-credential") message = "Mot de passe incorrect";
    else if (error.code === "auth/too-many-requests") message = "Trop de tentatives. Réessayez dans quelques minutes.";
    else if (error.code === "auth/invalid-email") message = "Format d'email invalide";
    return { success: false, message };
  }
}

export async function logout() { await signOut(auth); }

export async function resetPassword(email) {
  try {
    await sendPasswordResetEmail(auth, email);
    return { success: true };
  } catch (error) {
    let message = "Erreur lors de l'envoi";
    if (error.code === "auth/user-not-found" || error.code === "auth/invalid-email") message = "Aucun compte trouvé avec cet email";
    else if (error.code === "auth/too-many-requests") message = "Trop de tentatives, réessayez plus tard";
    return { success: false, message };
  }
}

async function getUserRole(uid) {
  try {
    const userDoc = await getDoc(doc(db, "users", uid));
    if (userDoc.exists()) {
      const role = userDoc.data().role || "demandeur";
      return role === "lecteur" ? "demandeur" : role;
    }
    return "demandeur";
  } catch (e) {
    console.error("Erreur chargement rôle:", e);
    return "demandeur";
  }
}

export function getCurrentUser() { return currentUser; }
export function getCurrentRole() { return currentRole; }
''')

write("js/users.js", r'''
import { createUserWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { collection, doc, setDoc, updateDoc, deleteDoc, getDocs, serverTimestamp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { db, secondaryAuth } from "./firebase.js";

export async function createUser(email, password, nom, role) {
  try {
    const cred = await createUserWithEmailAndPassword(secondaryAuth, email, password);
    await setDoc(doc(db, "users", cred.user.uid), {
      email: email, nom: nom, role: role, createdAt: serverTimestamp(), active: true
    });
    await signOut(secondaryAuth);
    return { success: true, uid: cred.user.uid };
  } catch (error) {
    let message = "Erreur lors de la création";
    if (error.code === "auth/email-already-in-use") message = "Cet email est déjà utilisé";
    else if (error.code === "auth/weak-password") message = "Mot de passe trop faible (min 6 caractères)";
    else if (error.code === "auth/invalid-email") message = "Email invalide";
    return { success: false, message };
  }
}

export async function getAllUsers() {
  try {
    const snap = await getDocs(collection(db, "users"));
    return snap.docs.map(d => ({ id: d.id, ...d.data() }));
  } catch (e) {
    console.error("Erreur chargement users:", e);
    return [];
  }
}

export async function updateUserRole(uid, newRole) {
  try {
    await updateDoc(doc(db, "users", uid), { role: newRole });
    return { success: true };
  } catch (e) { return { success: false, message: e.message }; }
}

export async function deleteUser(uid) {
  try {
    await deleteDoc(doc(db, "users", uid));
    return { success: true };
  } catch (e) { return { success: false, message: e.message }; }
}
''')

write("js/demandes.js", r'''
import { collection, doc, addDoc, updateDoc, deleteDoc, query, where, serverTimestamp, runTransaction, onSnapshot } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { db } from "./firebase.js";
import { uploadCapture } from "./captures.js";

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
    if (data.captureFile) captureUrl = await uploadCapture(data.captureFile);
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

print("[OK] Partie 1/2 terminee (7 fichiers JS)")
print("Dites 'ok' pour recevoir rebuild2.py (index.html + css + sw.js)")
input("Appuyez sur Entree...")