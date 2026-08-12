// ═══════════════════════════════════════
// GESTION DES DEMANDES
// ═══════════════════════════════════════

import {
  collection,
  doc,
  addDoc,
  updateDoc,
  deleteDoc,
  getDocs,
  query,
  orderBy,
  where,
  serverTimestamp
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { db } from "./firebase.js";

const COLLECTION = "demandes";

// Créer une demande
export async function createDemande(data) {
  try {
    const docRef = await addDoc(collection(db, COLLECTION), {
      symbole: data.symbole,
      type: data.type,
      demandeur: data.demandeur,
      demandeurEmail: data.demandeurEmail,
      description: data.description,
      statut: "nouveau",
      reponse: null,
      dateCreation: serverTimestamp(),
      dateResolution: null
    });
    return { success: true, id: docRef.id };
  } catch (e) {
    return { success: false, message: e.message };
  }
}

// Lister les demandes
export async function getDemandes(userEmail, role) {
  try {
    let q;
    if (role === "admin" || role === "qualite") {
      // Admin et Qualité voient tout
      q = query(collection(db, COLLECTION), orderBy("dateCreation", "desc"));
    } else {
      // Lecteur voit seulement ses demandes
      q = query(
        collection(db, COLLECTION),
        where("demandeurEmail", "==", userEmail),
        orderBy("dateCreation", "desc")
      );
    }
    const snapshot = await getDocs(q);
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
  } catch (e) {
    console.error("Erreur chargement demandes:", e);
    return [];
  }
}

// Mettre à jour le statut
export async function updateStatut(id, statut) {
  try {
    const data = { statut };
    if (statut === "resolu") {
      data.dateResolution = serverTimestamp();
    }
    await updateDoc(doc(db, COLLECTION, id), data);
    return { success: true };
  } catch (e) {
    return { success: false, message: e.message };
  }
}

// Répondre à une demande
export async function repondreDemande(id, reponse, statut) {
  try {
    await updateDoc(doc(db, COLLECTION, id), {
      reponse,
      statut,
      dateResolution: statut === "resolu" ? serverTimestamp() : null
    });
    return { success: true };
  } catch (e) {
    return { success: false, message: e.message };
  }
}

// Supprimer une demande
export async function deleteDemande(id) {
  try {
    await deleteDoc(doc(db, COLLECTION, id));
    return { success: true };
  } catch (e) {
    return { success: false, message: e.message };
  }
}
