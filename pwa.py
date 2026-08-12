# -*- coding: utf-8 -*-
"""
Script PWA : icône + service worker + manifest
Usage : python pwa.py
"""
import os, json

BASE = os.path.dirname(os.path.abspath(__file__))

def write(path, content):
    full = os.path.join(BASE, *path.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] {path}")

# ═══════════════════════════════════════════════════════
# 1. ICÔNE SVG (vectorielle, toujours nette)
# ═══════════════════════════════════════════════════════
ICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="96" fill="#1A2F4E"/>
  <g transform="translate(256 240)">
    <!-- Bulle de dialogue -->
    <path d="M -140 -100 Q -140 -130 -110 -130 L 110 -130 Q 140 -130 140 -100 L 140 20 Q 140 50 110 50 L -40 50 L -80 90 L -80 50 L -110 50 Q -140 50 -140 20 Z"
          fill="#E05A00" stroke="#FFF" stroke-width="4"/>
    <!-- Engrenage/clé -->
    <g transform="translate(0 -40)" fill="#FFF">
      <path d="M 0 -50 L 10 -50 L 14 -38 Q 22 -34 28 -28 L 40 -32 L 48 -24 L 42 -14 Q 46 -6 46 0 L 58 4 L 54 14 L 42 14 Q 38 22 32 28 L 38 40 L 28 48 L 18 40 Q 10 44 0 44 Q -10 44 -18 40 L -28 48 L -38 40 L -32 28 Q -38 22 -42 14 L -54 14 L -58 4 L -46 0 Q -46 -6 -42 -14 L -48 -24 L -40 -32 L -28 -28 Q -22 -34 -14 -38 Z"/>
      <circle r="16" fill="#1A2F4E"/>
    </g>
  </g>
  <!-- Texte "POP" -->
  <text x="256" y="420" text-anchor="middle" font-family="Arial Black, sans-serif"
        font-size="64" font-weight="900" fill="#FFF" letter-spacing="2">POPUPS</text>
</svg>'''

write("icons/icon.svg", ICON_SVG)

# ═══════════════════════════════════════════════════════
# 2. MANIFEST PWA
# ═══════════════════════════════════════════════════════
manifest = {
    "name": "Gestion Popups Reflex",
    "short_name": "Popups Reflex",
    "description": "Gestion des demandes de modification de popups - Service Qualité",
    "start_url": "./",
    "display": "standalone",
    "background_color": "#1A2F4E",
    "theme_color": "#1A2F4E",
    "orientation": "portrait-primary",
    "lang": "fr",
    "icons": [
        {
            "src": "icons/icon.svg",
            "sizes": "any",
            "type": "image/svg+xml",
            "purpose": "any maskable"
        }
    ]
}
write("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))

# ═══════════════════════════════════════════════════════
# 3. SERVICE WORKER
# ═══════════════════════════════════════════════════════
SW = '''// Service Worker - Gestion Popups Reflex v1
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
'''
write("sw.js", SW)

# ═══════════════════════════════════════════════════════
# 4. MODIFIER index.html : ajouter manifest + icones
# ═══════════════════════════════════════════════════════
html_path = os.path.join(BASE, "index.html")
with open(html_path, encoding="utf-8") as f:
    html = f.read()

pwa_meta = '''  <link rel="manifest" href="manifest.json">
  <link rel="icon" type="image/svg+xml" href="icons/icon.svg">
  <link rel="apple-touch-icon" href="icons/icon.svg">
  <meta name="theme-color" content="#1A2F4E">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="Popups Reflex">'''

if '<link rel="manifest"' in html:
    print("[OK] index.html : manifest deja present")
else:
    html = html.replace('<meta name="viewport"', pwa_meta + '\n  <meta name="viewport"')
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print("[OK] index.html : meta PWA ajoutees")

# ═══════════════════════════════════════════════════════
# 5. MODIFIER js/app.js : enregistrer le SW
# ═══════════════════════════════════════════════════════
app_path = os.path.join(BASE, "js/app.js")
with open(app_path, encoding="utf-8") as f:
    app = f.read()

sw_register = '''
// ─── Enregistrement du Service Worker (PWA) ───
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js")
      .then(() => console.log("[SW] Enregistre"))
      .catch((e) => console.warn("[SW] Erreur:", e));
  });
}
'''

if "serviceWorker" in app:
    print("[OK] js/app.js : SW deja enregistre")
else:
    app = sw_register + app
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app)
    print("[OK] js/app.js : enregistrement SW ajoute")

print("\n=== PWA PRETE ===")
print("Testez en local : python -m http.server 8123")
print("Puis : git add . && git commit -m 'Ajout PWA (icone + SW)' && git push")
input("Appuyez sur Entree...")