
const CACHE_NAME = "popups-reflex-v7";
const ASSETS = [
  "./", "./index.html", "./manifest.json", "./icons/icon.svg", "./css/style.css",
  "./js/app.js", "./js/auth.js", "./js/config.js", "./js/demandes.js",
  "./js/firebase.js", "./js/ui.js", "./js/users.js", "./js/captures.js"
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
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
