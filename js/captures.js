
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
