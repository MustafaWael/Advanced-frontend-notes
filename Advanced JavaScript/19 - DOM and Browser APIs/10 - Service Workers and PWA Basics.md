---
tags: [javascript, dom, workers, pwa, caching]
module: "19 - DOM and Browser APIs"
priority: deep-dive
status: not-started
aliases: [Service Worker, PWA]
---

# Service Workers and PWA Basics

## Maturity Target

- Priority: #deep-dive
- Study time: 60-90 minutes
- Interview signal: you can explain the service worker lifecycle (install → waiting → activate), why users see stale versions, and pick a caching strategy per resource type.
- Production signal: you can debug "users are stuck on an old deploy" and choose Workbox defaults deliberately instead of cargo-culting.
- Dependencies: [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers]], [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]], [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]

## Source Anchors

- [MDN - Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [web.dev - Service worker lifecycle](https://web.dev/articles/service-worker-lifecycle)
- [web.dev - Caching strategies (Offline cookbook)](https://web.dev/articles/offline-cookbook)
- [Service Workers specification](https://w3c.github.io/ServiceWorker/)

## 1. Concept

A service worker is a special worker that acts as a **programmable network proxy** for an origin scope: after registration, HTTP requests from controlled pages pass through its `fetch` event, where it can serve from cache, hit the network, or synthesize responses. It runs without any page open (woken for push, sync, fetch events), is killed aggressively when idle, and therefore keeps **no reliable in-memory state** — persistent state lives in Cache Storage or IndexedDB ([[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]]).

```js
// register from the page
navigator.serviceWorker.register("/sw.js");

// sw.js
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open("static-v3").then((c) => c.addAll(["/", "/app.css"])));
});

self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then((hit) => hit ?? fetch(e.request))
  );
});
```

It requires HTTPS, and its powers make it security-sensitive: whoever controls `/sw.js` controls every response your origin serves.

## 2. Why It Matters

- It's the engine behind offline support, installable PWAs, reliable "app shell" startup, push notifications, and precise cache control beyond HTTP headers.
- The lifecycle produces the two classic production incidents — "users stuck on the old version for days" and "the app broke and even a deploy can't fix it (cached forever)". Interviewers ask about service workers to see if you understand *deployment*, not just code.

## 3. The Lifecycle — Where the Bugs Live

1. **Install**: new/byte-different `sw.js` detected → new worker runs `install` (precache new assets here, into a *new versioned cache*).
2. **Waiting**: the new worker waits until **all tabs controlled by the old worker close**. Refresh is not enough — a refreshing tab keeps the old controller.
3. **Activate**: old worker released → new one activates (delete old caches here) and controls pages from their next load.

Escape hatches: `self.skipWaiting()` (activate immediately) + `clients.claim()` (take over open pages). Tempting defaults — but a worker that takes over mid-session can serve v2 chunks to a v1 page and crash lazy-loaded routes.

> [!warning] The stale-deploy incident, explained
> "We deployed Friday; Monday users still see the old app." Cause: the old service worker keeps serving the precached app shell while the new worker sits in `waiting`, and users never fully close the tab. Standard production pattern: detect `registration.waiting`, show an "Update available" toast, and on click post `{type: "SKIP_WAITING"}` to the worker, then reload once `controllerchange` fires. Also ensure `sw.js` itself is served with `Cache-Control: no-cache` — an HTTP-cached service worker file delays even *detecting* updates.

## 4. Caching Strategies — Choose Per Resource

| Strategy | Serve | Best for |
| --- | --- | --- |
| Cache First | cache, fallback network | Hashed immutable assets (`app.3f2a1.js`), fonts, logos |
| Network First | network, fallback cache | HTML documents, API data where freshness wins |
| Stale-While-Revalidate | cache immediately, refresh cache in background | Avatars, non-critical JSON — fast but ≤1 version stale |
| Network Only | network | Auth, payments, anything with side effects |
| Cache Only | cache | Precached app shell in full-offline apps |

The mistake is picking one strategy for everything. Hashed assets can be Cache First *forever* (the hash changes when content does); HTML must never be — cache-first HTML referencing deleted chunk files is the "white screen after deploy" bug. This table is the same reasoning as [[20 - Network and Security/02 - HTTP Caching|HTTP caching]] and, later, the [[22 - Next.js Deep Dive/02 - The Caching Layers|Next.js cache layers]]: per-resource freshness/speed tradeoffs.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — the tutorial-grade catch-all:

```js
self.addEventListener("fetch", (e) => {
  e.respondWith(
    caches.match(e.request).then((hit) => {
      return hit ?? fetch(e.request).then((res) => {
        caches.open("v1").then((c) => c.put(e.request, res.clone()));
        return res;
      });
    })
  );
});
```

Traced failures:

1. Caches **every** request cache-first — including `/api/cart`. User adds an item; the GET for the cart returns the cached old cart. "The app shows stale data randomly" forever.
2. Caches POST-adjacent GETs, error responses (`res.ok` never checked) — a transient 500 can be cached and replayed.
3. One unversioned cache `"v1"` that's never cleaned: deploys accumulate; old HTML can reference chunks that no longer exist on the server but *do* half-exist in cache.

Production-safe fix — route-scoped strategies + versioned cleanup:

```js
const STATIC = "static-v42";

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== STATIC).map((k) => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.pathname.startsWith("/api/")) return; // network only: don't respondWith at all
  if (url.pathname.startsWith("/assets/")) {
    e.respondWith(cacheFirst(e.request, STATIC));      // hashed, immutable
  } else if (e.request.mode === "navigate") {
    e.respondWith(networkFirst(e.request, STATIC));    // HTML: fresh, offline fallback
  }
});
```

Tradeoff: this is exactly what **Workbox** generates declaratively (`registerRoute`, precache manifests, expiration plugins) — in production, write Workbox config, not raw fetch handlers; the failure modes above are why. Raw handlers remain worth understanding because Workbox misconfiguration produces the *same* incidents one layer up.

## 6. PWA Basics Beyond Caching

- **Installability**: manifest (`name`, `icons`, `display: standalone`, `start_url`) + HTTPS + a service worker → install prompt / add to home screen.
- **Push notifications**: `push` events wake the worker (needs user permission + a push service).
- **Background/periodic sync**: retry writes when connectivity returns — spotty support outside Chromium; treat as progressive enhancement.
- Next.js note: service workers are *not* built in; PWA support comes via community plugins or a hand-rolled `public/sw.js` — and it must be reconciled with Next's own caching ([[22 - Next.js Deep Dive/02 - The Caching Layers|Caching Layers]]) or the two fight over freshness.

## 7. Interview Answer

Short answer:

> A service worker is a programmable network proxy for an origin: it intercepts fetches from controlled pages and answers from Cache Storage, the network, or both. It has an install → waiting → activate lifecycle; a new version waits until all old tabs close, which is why deploys can appear "stuck" without an update-toast + skipWaiting flow.

Deeper answer:

> Caching strategy is per resource: cache-first for hashed immutable assets, network-first for HTML and fresh data, stale-while-revalidate for tolerable-staleness assets, network-only for anything with side effects — and never cache non-GET or error responses. Versioned caches cleaned on activate prevent deploy corruption, and sw.js itself must bypass HTTP caching so updates are detected. In practice you express all this in Workbox.

## 8. Practice

1. <details><summary>Support ticket: "Even after you deployed the fix, my app is still broken. Hard refresh doesn't help." Diagnose.</summary>An old service worker still controls the page and serves the broken app shell cache-first; hard refresh doesn't bypass a controlling SW, and the fixed worker is stuck in `waiting` while any controlled tab stays open (or worse, sw.js was HTTP-cached so the update wasn't even detected). Fix path: unregister/`skipWaiting` flow, ensure sw.js is `no-cache`, version caches and clean on activate. Users can self-rescue via devtools → Application → Unregister, or closing all tabs.</details>

2. <details><summary>Why must you `clone()` a response before `cache.put(request, response)` and also return it?</summary>Response bodies are one-shot streams ([[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]): the page consuming it and the cache writing it are two consumers. `res.clone()` tees the stream so both can read; without it you get "body already used" errors or an empty cache entry.</details>

3. <details><summary>Which strategy for: (a) `main.8f3c9.js`, (b) `/index.html`, (c) `GET /api/notifications`, (d) `POST /api/orders`?</summary>(a) Cache First with long expiry — the content hash makes it immutable. (b) Network First with cache fallback — must pick up deploys, cache enables offline. (c) Network First or SWR depending on how stale notifications may be; never Cache First. (d) Network Only — side effects must never be served or replayed from cache (POST isn't cacheable in Cache Storage anyway; don't intercept it).</details>

4. <details><summary>What's the risk of calling `skipWaiting()` unconditionally in every deploy?</summary>The new worker activates while old pages are mid-session; with `clients.claim()` it starts serving v2 assets to v1 pages. A v1 page lazily importing a route chunk gets a v2 (or missing) chunk → runtime error/white screen. Safe pattern: skipWaiting only on explicit user consent (update toast), followed by a controlled reload on `controllerchange`.</details>

## Related Notes

- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]
- [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]
- [[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]]
- [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]
- [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]
- [[01 - Roadmap|Roadmap]]
