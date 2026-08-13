
import { signInWithEmailAndPassword, signOut, onAuthStateChanged, sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { doc, getDoc } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { auth, db } from "./firebase.js?v=8";

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
