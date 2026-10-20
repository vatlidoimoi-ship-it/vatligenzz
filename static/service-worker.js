const CACHE_NAME = "phyedu-pwa-v11";
const APP_SHELL = [
  "/static/manifest.webmanifest",
  "/static/css/style.css",
  "/static/js/main.js",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/apple-touch-icon.png",
  "/static/icons/logo-phyedu-88-v1.webp",
  "/static/offline.html"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  // Teacher drafts and signed video redirects must never survive in offline cache.
  if (url.pathname === "/teacher/videos" || url.pathname.startsWith("/teacher/videos/") || url.pathname === "/video-lessons" || url.pathname.startsWith("/video-lessons/")) {
    event.respondWith(fetch(request, { cache: "no-store" }));
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        // Pages may contain private chat, grades, and another account's session.
        // Keep only the public offline page rather than caching authenticated HTML.
        .catch(() => caches.match("/static/offline.html"))
    );
    return;
  }

  if (url.pathname.startsWith("/uploads/")) {
    event.respondWith(fetch(request));
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      fetch(request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        }
        return response;
      }).catch(() => caches.match(request))
    );
    return;
  }

  // API and account-specific responses must always come from the server.
  event.respondWith(fetch(request));
});
