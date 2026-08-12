// ═══════════════════════════════════════
// GESTION DES UTILISATEURS (Admin)
// ═══════════════════════════════════════

import {
  createUserWithEmailAndPassword,
  signOut
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import {
  collection,
  doc,
  setDoc,
  updateDoc,
  deleteDoc,
  getDocs,
  serverTimestamp
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { db, secondaryAuth } from "./firebase.js";

// Créer un nouvel utilisateur (par l'admin)
export async function createUser(email, password, nom, role) {
  try {
    // Utiliser l'app secondaire pour ne pas déconnecter l'admin
    const userCredential = await createUserWithEmailAndPassword(secondaryAuth, email, password);
    const uid = userCredential.user.uid;

    // Sauvegarder dans Firestore
    await setDoc(doc(db, "users", uid), {
      email,
      nom,
      role,
      createdAt: serverTimestamp(),
      active: true
    });

    // Déconnecter l'app secondaire
    await signOut(secondaryAuth);

    return { success: true, uid };
  } catch (error) {
    let message = "Erreur lors de la création";
    switch (error.code) {
      case "auth/email-already-in-use":
        message = "Cet email est déjà utilisé";
        break;
      case "auth/weak-password":
        message = "Mot de passe trop faible (min 6 caractères)";
        break;
      case "auth/invalid-email":
        message = "Email invalide";
        break;
    }
    return { success: false, message };
  }
}

// Lister tous les utilisateurs
export async function getAllUsers() {
  try {
    const snapshot = await getDocs(collection(db, "users"));
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }));
  } catch (e) {
    console.error("Erreur chargement users:", e);
    return [];
  }
}

// Changer le rôle d'un utilisateur
export async function updateUserRole(uid, newRole) {
  try {
    await updateDoc(doc(db, "users", uid), { role: newRole });
    return { success: true };
  } catch (e) {
    return { success: false, message: e.message };
  }
}

// Supprimer un utilisateur (de Firestore uniquement)
// Note: la suppression du compte Firebase Auth nécessite le SDK Admin (serveur)
export async function deleteUser(uid) {
  try {
    await deleteDoc(doc(db, "users", uid));
    return { success: true };
  } catch (e) {
    return { success: false, message: e.message };
  }
}
