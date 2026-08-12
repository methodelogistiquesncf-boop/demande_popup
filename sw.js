// Service Worker - Gestion Popups Reflex v1
const CACHE_NAME = "popups-reflex-v1";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icons/icon.svg",
  "./css/style.css",
  "./js/app.js",
  "./js/auth.js",
  "./js/config.js",
  "./js/demandes.js",
  "./js/firebase.js",
  "./js/ui.js",
  "./js/users.js"
];

// Installation : mise en cache des assets
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// Activation : nettoyage des anciens caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(
        names.filter((n) => n !== CACHE_NAME).map((n) => caches.delete(n))
      )
    )
  );
  self.clients.claim();
});

// Stratégie network-first (priorité réseau pour Firebase, cache en secours)
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Ne jamais mettre en cache les requêtes Firebase (toujours à jour)
  if (url.hostname.includes("firebase") ||
      url.hostname.includes("googleapis") ||
      url.hostname.includes("gstatic")) {
    return;
  }

  // Assets statiques : cache-first (rapide)
  if (event.request.method === "GET" &&
      (event.request.url.endsWith(".html") ||
       event.request.url.endsWith(".js") ||
       event.request.url.endsWith(".css") ||
       event.request.url.endsWith(".svg"))) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        const fetchPromise = fetch(event.request).then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        }).catch(() => cached);
        return cached || fetchPromise;
      })
    );
    return;
  }

  // Par défaut : network-first
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
