
import { createUserWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
import { collection, doc, setDoc, updateDoc, deleteDoc, getDoc, getDocs, serverTimestamp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import { db, secondaryAuth } from "./firebase.js?v=8";

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
