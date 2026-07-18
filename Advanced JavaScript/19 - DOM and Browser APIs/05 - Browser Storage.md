---
tags: [javascript, dom, storage, security]
module: "19 - DOM and Browser APIs"
priority: must-know
status: not-started
aliases: [localStorage, IndexedDB]
---

# Browser Storage

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can compare cookies, localStorage, sessionStorage, and IndexedDB on size, synchronicity, scope, and security — and say when each is the *wrong* choice.
- Production signal: you never put tokens in localStorage without being able to defend it, and you know why a 5MB JSON blob in localStorage janks the main thread.
- Dependencies: [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]], [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]

## Source Anchors

- [MDN - Web Storage API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API)
- [MDN - IndexedDB API](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
- [MDN - Using HTTP cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies)
- [HTML Living Standard - Web storage](https://html.spec.whatwg.org/multipage/webstorage.html)
- [web.dev - Storage for the web](https://web.dev/articles/storage-for-the-web)

## 1. The Four Options at a Glance

| | Cookies | localStorage | sessionStorage | IndexedDB |
| --- | --- | --- | --- | --- |
| Size | ~4KB per cookie | ~5-10MB per origin | ~5MB | Large (% of disk, often GBs) |
| API | String header / `document.cookie` / CookieStore | Sync, strings only | Sync, strings only | Async, structured data |
| Sent to server | **Yes, on every request** | No | No | No |
| Lifetime | Expiry/max-age or session | Until cleared | Tab lifetime | Until cleared |
| Scope | Domain + path (subdomains possible) | Origin | Origin + **tab** | Origin |
| Workers can access | No (JS side) | No | No | Yes |
| JS-hidden option | `HttpOnly` ✅ | Never | Never | Never |

Scope subtlety worth stating precisely: `sessionStorage` is per-origin *per-tab* (duplicating a tab copies it; a new tab gets a fresh one). Cookies are domain-scoped and can cross subdomains; Web Storage is strictly origin-scoped (`https://app.example.com` ≠ `https://example.com`).

## 2. Why It Matters

- Storage choice is a *security* decision first (where can a token be stolen from?), a *performance* decision second (sync vs async), and a convenience decision last.
- "Where would you store the JWT?" is a near-universal senior interview question; the follow-ups test whether you understand XSS and CSRF, not storage APIs.

## 3. Mechanisms That Actually Matter

**Web Storage is synchronous.** `localStorage.getItem/setItem` block the main thread — reads/writes hit a per-origin store that may involve disk I/O. Small keys are microseconds; serializing and storing a multi-MB JSON string can take tens to hundreds of milliseconds, inside your click handler.

**Strings only.** `localStorage.setItem("user", userObj)` silently stores `"[object Object]"`. You must `JSON.stringify`/`JSON.parse`, which loses `Date`, `Map`, `undefined`, and cycles — see [[12 - Advanced Language Concepts/10 - BigInt Date RegExp JSON|JSON]].

**The `storage` event** fires on *other* same-origin tabs (not the one that wrote), enabling cheap cross-tab sync — logout propagation is the classic use. (`BroadcastChannel` is the modern general-purpose alternative.)

**IndexedDB is async and transactional.** It stores structured-clone-able values (Blobs, Files, typed arrays, Maps...), works in workers and service workers (offline apps need it), and doesn't block the main thread for I/O. Its raw API is callback/event-based and verbose; in production nearly everyone wraps it (`idb`) or uses it indirectly (TanStack Query persisters, Workbox).

**Cookies travel.** Every byte in a cookie rides on *every* request to that domain — 4KB of cookies on a site making 100 requests/page is real overhead. Their superpower is `HttpOnly` + `Secure` + `SameSite`: the only storage JavaScript *cannot read*, hence the default home for session credentials.

> [!warning] Any of these can simply fail
> Safari private mode historically threw on `setItem`; quota can be exceeded; enterprise policies disable storage; `JSON.parse` on a corrupted value throws. Every storage read/write in production belongs behind a try/catch wrapper with an in-memory fallback.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — persisting an entire Redux-ish store on every action:

```js
store.subscribe(() => {
  // Runs on EVERY dispatch
  localStorage.setItem("app-state", JSON.stringify(store.getState()));
});
```

Trace the failure:

1. User types in a search box; each keystroke dispatches.
2. Each dispatch synchronously stringifies the whole state (say 3MB: cached product lists, etc.) — ~30-80ms.
3. That blocks the main thread between keystrokes → visible input lag, INP degradation.
4. Eventually state grows past the ~5MB quota → `QuotaExceededError` thrown inside `subscribe` → depending on the framework, the dispatch pipeline breaks. Symptom: "the app stops updating after using it a while."

Production-safe fix — persist a slice, debounced, defensively:

```js
const persist = debounce(() => {
  try {
    const { preferences, draftOrder } = store.getState(); // small, chosen slices
    localStorage.setItem("app-state-v2", JSON.stringify({ preferences, draftOrder }));
  } catch (err) {
    // Quota/private mode: degrade to in-memory only, report once.
    reportOnce("persist_failed", err);
  }
}, 500);

store.subscribe(persist);
```

Tradeoffs: debouncing means a hard refresh can lose the last ≤500ms of changes (acceptable for preferences; not for a payment step). Versioning the key (`-v2`) prevents old-schema parse crashes but orphans old data — write a small migration/cleanup. If the persisted data is genuinely large (offline catalog, editor documents), the correct move is IndexedDB, accepting async complexity.

## 5. Security Rules of Thumb

- Anything readable by JavaScript (localStorage, sessionStorage, IndexedDB, non-HttpOnly cookies) is readable by *any* XSS payload and any compromised npm dependency running on your page. That's why long-lived auth tokens in localStorage are widely considered risky — full argument in [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]].
- `HttpOnly` cookies are immune to theft-via-JS but are attached automatically to requests → CSRF becomes your problem ([[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]).
- Never store PII or secrets client-side "temporarily". Storage outlives your intentions.

## Real-World Use Cases

### Dark mode without the flash of wrong theme

Theme preference lives in localStorage, but React reads it after hydration — so users see a white flash before dark mode applies. The fix is an inline `<head>` script that runs before first paint:

```html
<script>
  // Inline in <head>, before any stylesheet-dependent paint
  try {
    if (localStorage.getItem("theme") === "dark") {
      document.documentElement.dataset.theme = "dark";
    }
  } catch (_) { /* private mode / disabled storage: default theme */ }
</script>
```

This is the rare case where localStorage being *synchronous* is the feature: the read completes before the parser continues, so the first paint is already themed. (In Next.js this goes in the root layout via `dangerouslySetInnerHTML` — a known hydration-warning exception.)

### A/B test bucket in a cookie so the server can render it

An experiment changes the hero layout. Bucket in localStorage → the server can't see it → SSR renders variant A, client swaps to B → flicker and polluted metrics. Only cookies travel with the request.

```ts
// Next.js middleware: assign once, then every RSC/SSR render can read it
export function middleware(req: NextRequest) {
  if (!req.cookies.get("exp-hero")) {
    const res = NextResponse.next();
    res.cookies.set("exp-hero", Math.random() < 0.5 ? "a" : "b", {
      maxAge: 60 * 60 * 24 * 30, sameSite: "lax",
    });
    return res;
  }
}
```

Works because cookies are the only storage attached to the HTTP request — the deciding axis here is "does it travel", not size or API ([[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]).

### Per-tab checkout wizard in sessionStorage

A multi-step booking flow keeps step state in sessionStorage. A user comparing two flights in two tabs gets two *independent* drafts — with localStorage the tabs would silently overwrite each other's in-progress booking.

```js
function saveStep(step, data) {
  try {
    sessionStorage.setItem(`booking-step-${step}`, JSON.stringify(data));
  } catch (_) { /* fall back to in-memory draft */ }
}
```

Works because sessionStorage is scoped per-origin *per-tab* — the isolation that makes it wrong for OAuth redirects (see Practice 3) is exactly right for parallel drafts.

> [!warning]
> Duplicating a tab *copies* sessionStorage — two tabs can now submit the "same" draft. Include a client-generated draft id and let the server deduplicate.

### Offline mutation queue in IndexedDB

A field-service app must let technicians submit inspection reports (photos included) with no connectivity, syncing later. This needs everything Web Storage lacks: Blob storage, GB-scale quota, async access, and availability inside a service worker.

```js
import { openDB } from "idb";

const db = await openDB("outbox", 1, {
  upgrade: (db) => db.createObjectStore("reports", { keyPath: "id" }),
});
await db.put("reports", { id: crypto.randomUUID(), form, photos }); // photos: Blob[]
// A 'sync' handler in the service worker later reads the store and POSTs each report.
```

Works because IndexedDB stores structured-clone-able values (Blobs survive as-is) and is the only option accessible from workers — the replay logic lives in the service worker, not the page ([[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]]).

## 6. Interview Answer

Short answer:

> Cookies are small, domain-scoped, sent with every request, and the only option that can be hidden from JavaScript via HttpOnly — so they're for auth. localStorage/sessionStorage are synchronous string stores for small origin-scoped data — preferences, drafts. IndexedDB is the async, large-capacity, structured store — offline data, and it's the only one available in workers.

Deeper answer:

> The decision axes are: who can read it (HttpOnly vs JS-readable → XSS exposure), does it travel (cookies add bytes to every request), sync vs async (Web Storage blocks the main thread; IndexedDB doesn't), and capacity. So: session credential → HttpOnly SameSite cookie; UI preference → localStorage behind a try/catch; per-tab wizard state → sessionStorage; offline product catalog or files → IndexedDB, usually via a wrapper library.

## 7. Practice

1. <details><summary>User reports: "app works in normal Chrome, blank page in private browsing." Storage-related hypothesis and fix?</summary>Storage access is throwing (older Safari private mode threw on any `setItem`; quotas are near-zero in some private modes) and the exception during app bootstrap is unhandled → blank page. Fix: wrap all storage access in a safe wrapper that catches and falls back to an in-memory Map, so persistence degrades gracefully instead of crashing.</details>

2. <details><summary>How do you log a user out of all open tabs when they log out in one?</summary>On logout, write a marker: `localStorage.setItem("logout", Date.now())`. Other tabs receive the `storage` event (it fires only in tabs that didn't perform the write) and redirect to login. `BroadcastChannel("auth").postMessage(...)` is the modern equivalent; the localStorage trick still wins on very old browser support.</details>

3. <details><summary>Why is sessionStorage "per tab" a footgun for OAuth flows?</summary>Some providers redirect back in a new tab/window or through intermediate navigations; state saved in sessionStorage before redirecting may not exist in the context that receives the callback (new tab = fresh sessionStorage). Duplicating a tab *copies* sessionStorage, which can also double-submit one-time state. For redirect flows, prefer short-lived cookies or server-side state keyed by an id in the URL.</details>

4. <details><summary>You need to cache 50MB of product images for offline use. Walk through the storage decision.</summary>Cookies: absurd (4KB, sent to server). Web Storage: strings only, ~5MB quota, synchronous — serializing images to base64 would blow quota and block the thread. IndexedDB: stores Blobs natively, async, quota in GBs, accessible from the service worker that serves offline requests — correct choice. In practice, the Cache Storage API (`caches`) is even more natural for request/response pairs, with IndexedDB for the metadata.</details>

## Related Notes

- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
- [[20 - Network and Security/05 - XSS|XSS]]
- [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]]
- [[12 - Advanced Language Concepts/10 - BigInt Date RegExp JSON|BigInt Date RegExp JSON]]
- [[01 - Roadmap|Roadmap]]
