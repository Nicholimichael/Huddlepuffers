/* Huddlepuffers dashboard — service worker.
 *
 * Two jobs:
 *   1. The home-screen app launches instantly from cache — even offline.
 *   2. The weekly refresh still lands: the one-page shell is served
 *      stale-while-revalidate, and when the background fetch brings a new build
 *      (window.__DATA_VERSION__ changed) every open page is told so it can offer
 *      a one-tap reload (the #hp-update toast in redesign_template.html).
 *
 * Bump VERSION to drop every cache (old caches are deleted on activate).
 * Published by .github/workflows/refresh.yml — staged into _site/ next to index.html.
 */
'use strict';

const VERSION = 'hp-2026-09-02';
const CACHE = 'huddlepuffers-' + VERSION;
const SCOPE = self.registration.scope;   // https://huddlepuffers.hossautomation.com/
const SHELL = SCOPE;                     // every navigation is the same one-page shell

// Fetched at install so the very first standalone launch works offline.
// Only the shell is a must-have; a flaky CDN must not block install.
const PRECACHE = [
  'manifest.json',
  'assets/mascot.webp',
  'assets/icon-192.png',
  'assets/apple-touch-icon.png',
  'https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js',
].map((u) => new URL(u, SCOPE).href);

// Third-party hosts whose URLs are version-pinned or content-hashed: cache-first.
const CACHEABLE_HOSTS = new Set(['cdn.jsdelivr.net', 'fonts.googleapis.com', 'fonts.gstatic.com']);

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.add(SHELL);
    await Promise.allSettled(PRECACHE.map((u) => cache.add(new Request(u, { mode: 'cors' }))));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter((n) => n.startsWith('huddlepuffers-') && n !== CACHE)
      .map((n) => caches.delete(n)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (req.mode === 'navigate') {
    event.respondWith(serveShell(event));
    return;
  }
  if (url.origin === self.location.origin) {
    if (url.pathname.endsWith('/sw.js')) return;   // never cache ourselves
    event.respondWith(staleWhileRevalidate(req));
    return;
  }
  if (CACHEABLE_HOSTS.has(url.hostname)) {
    event.respondWith(cacheFirst(req));
  }
});

// The page pings us when it comes back to the foreground after a long sleep
// (a home-screen app can sit open for a week) so a new build is noticed
// without a navigation.
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'HP_CHECK') {
    event.waitUntil(refreshShell(new Request(SHELL)));
  }
});

/* ---- strategies ---- */

async function serveShell(event) {
  const cache = await caches.open(CACHE);
  const cached = await cache.match(SHELL);
  const refresh = refreshShell(event.request);
  if (cached) {
    event.waitUntil(refresh);
    return cached;
  }
  return (await refresh) || offlinePage();
}

// Fetch the shell, store it, and tell open pages if the build changed.
async function refreshShell(request) {
  let res;
  try {
    res = await fetch(request);
  } catch (_) {
    return null;
  }
  if (!res.ok || !(res.headers.get('content-type') || '').includes('text/html')) return res;
  const cache = await caches.open(CACHE);
  const prev = await cache.match(SHELL);
  const before = prev ? await buildVersion(prev) : null;   // read before put() replaces the entry
  const fresh = res.clone();
  await cache.put(SHELL, res.clone());
  if (before) {
    const after = await buildVersion(fresh);
    if (after && before !== after) {
      const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
      clients.forEach((c) => c.postMessage({ type: 'HP_NEW_BUILD', version: after }));
    }
  }
  return res;
}

// window.__DATA_VERSION__ is stamped by scripts/build_redesign.py on every deploy.
async function buildVersion(response) {
  try {
    const text = await response.text();
    const m = /__DATA_VERSION__\s*=\s*"([^"]+)"/.exec(text);
    return m ? m[1] : response.headers.get('etag');
  } catch (_) {
    return null;
  }
}

async function staleWhileRevalidate(req) {
  const cache = await caches.open(CACHE);
  const cached = await cache.match(req);
  const network = fetch(req).then((res) => {
    if (res.ok) cache.put(req, res.clone());
    return res;
  }).catch(() => null);
  return cached || (await network) || Response.error();
}

async function cacheFirst(req) {
  const cache = await caches.open(CACHE);
  const cached = await cache.match(req, { ignoreVary: true });
  if (cached) return cached;
  // Re-request in CORS mode (these hosts all send ACAO: *) so the stored copy is
  // a real response, not an opaque one; fall back to a plain pass-through.
  try {
    const res = await fetch(new Request(req.url, { mode: 'cors', credentials: 'omit' }));
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (_) {
    return fetch(req);
  }
}

function offlinePage() {
  return new Response(
    '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>Huddlepuffers</title>' +
    '<body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;' +
    'background:#0E0B07;color:#F1E9D8;font:600 16px -apple-system,BlinkMacSystemFont,sans-serif;text-align:center;padding:24px">' +
    '<div><div style="font-size:22px;margin-bottom:8px">You’re offline</div>' +
    '<div style="color:#b3a994;font-weight:400">Open the Huddlepuffers dashboard once while online and it will work offline from then on.</div></div>',
    { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
}
