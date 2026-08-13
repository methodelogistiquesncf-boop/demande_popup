
import { collection, doc, addDoc, updateDoc, deleteDoc, query, where, serverTimestamp, runTransaction, onSnapshot } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { db } from "./firebase.js?v=8";
import { processCapture } from "./captures.js?v=8";

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
