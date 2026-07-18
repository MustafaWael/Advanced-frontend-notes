---
tags: [system-design, interview, offline, pwa, service-worker]
module: "29 - Frontend System Design"
priority: important
status: not-started
aliases: [PWA design, offline first, service worker caching, resilience]
verified_on: 2026-07-17
version_scope: "Service Worker / Background Sync / IndexedDB browser support as of 2026 (Background Sync remains Chromium-only)"
---

# Offline and Resilient UX

## Maturity Target

- Priority: #important
- Study time: 40 minutes
- Interview signal: Design for degraded and offline networks — caching layers, optimistic queueing, sync — and name the consistency cost.
- Production signal: Your app has designed states for offline/slow/failed, not just the happy path.
- Dependencies: [[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]], [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]]

## Source Anchors

- [web.dev — Offline cookbook](https://web.dev/articles/offline-cookbook)
- [MDN — Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [MDN — IndexedDB](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)

## 1. Concept

Simple version: networks fail, so "what happens offline / on a slow connection" is a design requirement, not an edge case. The mechanics are in [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]]; this is the design decision.

The layers of resilience:

- **Service Worker caching strategies** — cache-first (static assets, app shell), network-first (fresh data, fall back to cache), stale-while-revalidate (serve cache, refresh in background). Choose per resource type.
- **Local persistence** — IndexedDB for structured data/read cache, so the app opens and shows something offline. (localStorage is tiny and synchronous — not for app data.)
- **Optimistic queueing / outbox** — writes made offline are applied optimistically and queued in a durable store; a flush drains them when connectivity returns. This is [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|optimistic updates]] extended across a disconnect. The **Background Sync API** is the ideal trigger (the SW wakes and flushes even after the tab closed) but is **Chromium-only — no Safari or Firefox** — so treat it as progressive enhancement and always keep a portable fallback: flush on the `online` event and on next app launch (re-scan the outbox).
- **Conflict resolution** — when a queued write reaches a server that changed meanwhile: last-write-wins, version checks, or merge (CRDTs for collaborative apps). The hard part.
- **Connection-aware UX** — reflect online/offline status, disable or queue actions, show "pending sync" state honestly.

> [!warning] Offline writes make the consistency window long and multi-actor. A note edited offline for an hour, then synced, can conflict with another device's edits — you must pick a resolution policy (LWW loses data silently; merge is complex). "Offline-first" without a conflict story is a data-loss bug waiting to happen ([[30 - Backend System Design/07 - CAP and Consistency|consistency]]).

## 2. Why It Matters

Mobile and flaky networks are the real world; a design that only works on fast wifi is incomplete. Raising offline/slow/failed states unprompted is a product-sense signal, and the conflict-resolution question separates people who've said "offline-first" from people who've shipped it. Even without full offline, network-first-with-cache-fallback and honest failure states are table stakes.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a field-service app lets technicians log job notes. On a spotty site, saving a note either spins forever or throws, and switching screens loses the unsaved note.

Trace: no resilience layer — writes go straight to the network with no queue, and unsaved input lives only in component state, so a failed request or a navigation drops it. The happy path was the only path.

Fix: write the note to **IndexedDB** immediately (durable local), reflect it optimistically, and enqueue it in an outbox; flush the outbox when back online. Use the Service Worker **Background Sync API** where available (it flushes even if the tab was closed) but, because it's Chromium-only, always back it with a portable trigger — flush on the `window` `online` event and on app launch — so Safari/Firefox users still sync. Show the note as "saved locally, syncing." On conflict at flush, apply the chosen policy (e.g., server-wins with a "your offline edit couldn't merge" prompt rather than silent loss).

Tradeoff: this adds real complexity — a local store, an outbox, a sync flow, and a conflict policy — and introduces a staleness/conflict window. For a read-mostly app, network-first caching alone may suffice; full offline-write support is justified only when the requirement (field work, unreliable networks) demands it. Say which.

## 4. Interview Answer

Short answer:

> I treat offline and slow networks as requirements. Static assets and the app shell cache-first via a Service Worker; fresh data network-first with cache fallback or stale-while-revalidate. Structured data and a read cache live in IndexedDB so the app opens offline. Offline writes go to a durable outbox, apply optimistically, and flush on background sync — with an explicit conflict-resolution policy, because that's where offline-first actually gets hard.

Deeper answer:

> The caching strategy is per resource type, not global — app shell cache-first, data network-first or SWR. The genuinely hard part is offline writes: they extend the optimistic-update window across a disconnect, so a queued write can meet a server that changed, and I have to choose last-write-wins (simple, silently lossy), version checks (reject and prompt), or CRDT merge (complex, for collaboration). I'd name that tradeoff explicitly and scope it to the requirement — full offline-write with conflict handling only when the product needs it, otherwise cache-fallback and honest failure states are enough.

## 5. Practice

1. <details><summary>Which Service Worker caching strategy for the app shell vs live data, and why?</summary>App shell: cache-first — it changes rarely and must load instantly/offline, so serve from cache and update in the background. Live data: network-first (fall back to cache) or stale-while-revalidate — freshness matters, but a cached fallback beats a blank screen when offline. Strategy is chosen per resource type.</details>
2. <details><summary>What makes offline writes fundamentally harder than offline reads?</summary>Reads just need a cached copy; staleness is cosmetic. Writes create a divergence that must eventually merge with a server that may have changed — a long, multi-device consistency window needing a conflict-resolution policy (LWW, version check, or merge). Without one, syncing silently loses data.</details>
3. <details><summary>Why IndexedDB rather than localStorage for offline app data?</summary>localStorage is small (~5MB), synchronous (blocks the main thread), and string-only. IndexedDB is asynchronous, stores structured data, and holds far more — suitable for a read cache and an outbox of queued writes. Using localStorage for app data risks main-thread jank and quota errors.</details>

## 6. Real-World Use Cases

### Network-first with cache fallback (Service Worker)

Live data should be fresh when online but must not show a blank screen offline. In the SW `fetch` handler, try the network, fall back to the last cached response.

```js
// sw.js
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    fetch(e.request)
      .then((res) => { caches.open("data").then((c) => c.put(e.request, res.clone())); return res; })
      .catch(() => caches.match(e.request))   // offline → serve last good copy
  );
});
```

Strategy chosen per resource type — this is the "fresh, but degrade gracefully" one. See [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]].

### Outbox flush on reconnect (portable, no Background Sync)

Writes made offline sit in a durable outbox; drain it when connectivity returns. Because Background Sync is Chromium-only, trigger on the `online` event and on app launch too.

```ts
async function flushOutbox() {
  const pending = await idb.getAll("outbox");
  for (const item of pending) {
    try { await fetch(item.url, { method: "POST", body: JSON.stringify(item.body) });
          await idb.delete("outbox", item.id); }
    catch { break; }   // still offline — stop, keep the rest queued
  }
}
window.addEventListener("online", flushOutbox);
flushOutbox();          // also on launch, in case we missed the event
```

The outbox is optimistic updates extended across a disconnect. See [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]].

### Conflict at flush — last-write-wins vs version check

A queued edit can reach a server that changed meanwhile. LWW is one line and silently lossy; a version check refuses the stale write and lets you prompt instead.

```ts
// Version check: server rejects if the row moved since we read it
const res = await fetch(`/notes/${id}`, {
  method: "PUT",
  headers: { "If-Match": localNote.version },   // 412 Precondition Failed if stale
  body: JSON.stringify(localNote),
});
if (res.status === 412) showMergePrompt(await res.json());  // don't overwrite silently
```

"Offline-first" without a conflict policy is a data-loss bug. See [[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]].

## Related Notes

- [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]]
- [[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]]
- [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]]
- [[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]]
