
const CACHE_NAME = 'mrd-pwa-v1';
const ASSETS = [
  '/webui/',
  '/webui/index.html',
  '/webui/assets/app.js',
  '/webui/assets/style.css',
  '/webui/manifest.webmanifest',
  '/webui/icons/icon-192.png',
  '/webui/icons/icon-512.png',
  '/webui/icons/apple-touch-icon.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))));
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Cache-first for static assets, network-first for API
  if (ASSETS.includes(url.pathname)) {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  } else if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      fetch(e.request).catch(()=>caches.match('/webui/index.html'))
    );
  }
});
