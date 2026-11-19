// Peritão — service worker
// Guarda a casca do app para abrir sem rede. Dados nunca são cacheados:
// as chamadas ao Supabase passam direto e, se falharem, o app põe na fila local.

const CACHE = 'peritao-v8';
const CASCA = ['index.html', 'manifest.json', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(CASCA.map(f => new Request(f, { cache: 'reload' }))))
      .catch(() => {})
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // Tudo que for API, auth ou storage do Supabase vai direto para a rede.
  if (url.pathname.includes('/rest/v1/') ||
      url.pathname.includes('/auth/v1/') ||
      url.pathname.includes('/realtime/')) return;

  // Casca: rede primeiro, cache como rede de segurança.
  e.respondWith(
    fetch(req)
      .then(resp => {
        if (resp && resp.ok && url.origin === location.origin) {
          const copia = resp.clone();
          caches.open(CACHE).then(c => c.put(req, copia)).catch(() => {});
        }
        return resp;
      })
      .catch(() => caches.match(req).then(r => r || caches.match('index.html')))
  );
});
