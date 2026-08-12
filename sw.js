// Service Worker - Gestion Popups Reflex v3
const CACHE_NAME = "popups-reflex-v3";
const ASSETS = [
  "./", "./index.html", "./manifest.json", "./icons/icon.svg",
  "./css/style.css", "./js/app.js", "./js/auth.js", "./js/config.js",
  "./js/demandes.js", "./js/firebase.js", "./js/ui.js", "./js/users.js",
  "./js/captures.js"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.hostname.includes("firebase") || url.hostname.includes("googleapis") || url.hostname.includes("gstatic")) return;

  if (event.request.method === "GET" &&
      (event.request.url.endsWith(".html") || event.request.url.endsWith(".js") ||
       event.request.url.endsWith(".css") || event.request.url.endsWith(".svg"))) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        fetch(event.request).then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
        }).catch(() => {});
        return cached || fetch(event.request);
      })
    );
    return;
  }

  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
