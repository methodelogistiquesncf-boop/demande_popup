import { ref, uploadBytes, getDownloadURL } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-storage.js";
import { storage } from "./firebase.js?v=4";

export async function uploadCapture(file) {
  const clean = file.name.replace(/[^\w.\-]/g, "_");
  const r = ref(storage, "captures/" + Date.now() + "_" + clean);
  await uploadBytes(r, file);
  return await getDownloadURL(r);
}
