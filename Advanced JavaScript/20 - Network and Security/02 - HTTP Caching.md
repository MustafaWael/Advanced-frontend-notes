---
tags: [javascript, network, http, caching, nextjs]
module: "20 - Network and Security"
priority: must-know
status: not-started
aliases: [Cache-Control, ETag]
---

# HTTP Caching

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can explain freshness vs revalidation, write correct `Cache-Control` for hashed assets vs HTML vs APIs, and trace a 304 round trip.
- Production signal: you can debug "users see the old version" layer by layer — browser cache, CDN, service worker, framework cache — instead of telling people to hard-refresh.
- Dependencies: [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]], [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers]]

## Source Anchors

- [MDN - HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching)
- [RFC 9111 - HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111)
- [web.dev - Love your cache](https://web.dev/articles/love-your-cache)
- [MDN - Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)
- [Next.js - Caching](https://nextjs.org/docs/app/guides/caching)

## 1. Concept

HTTP caching answers one question per response: **how long may this be reused without asking the server, and what happens after that?** Two mechanisms compose:

1. **Freshness** (`Cache-Control: max-age=N`, CDN-facing `s-maxage`): while fresh, the cache answers *without any network* — status "200 (from disk cache)".
2. **Revalidation** (`ETag` / `Last-Modified`): once stale, the cache asks cheaply: "I have version X — still good?" via `If-None-Match: "X"`. Server replies **304 Not Modified** (empty body — headers only, bytes saved) or `200` with the new version.

```text
First request:   GET /api/products      → 200, ETag: "abc123", Cache-Control: no-cache
Later request:   GET /api/products
                 If-None-Match: "abc123" → 304 (no body) — cache reuses stored response
```

## 2. Why It Matters

- Caching is the highest-leverage web performance tool that requires zero JavaScript.
- Misconfigured caching produces the two worst incident classes: *stale forever* (users stuck on broken deploys) and *never cached* (origin melts under load).
- Next.js's entire caching story ([[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]) is these concepts re-implemented at the framework level — `revalidate` is max-age, tag invalidation is purging, `no-store` is literally the same directive name.

## 3. The Directives That Matter

| Directive                   | Meaning                                                                  |
| --------------------------- | ------------------------------------------------------------------------ |
| `max-age=31536000`          | Fresh for a year (browser + shared caches)                               |
| `s-maxage=60`               | Freshness for *shared* caches (CDN) only; browser follows max-age        |
| `immutable`                 | Won't change during freshness — skip even refresh-triggered revalidation |
| `no-cache`                  | **Cache it, but revalidate every use** (misnamed!)                       |
| `no-store`                  | Never write to cache at all — the actual "don't cache"                   |
| `private`                   | Browser cache only, never CDN (per-user responses)                       |
| `public`                    | Cacheable by shared caches even with e.g. Authorization present          |
| `stale-while-revalidate=30` | Serve stale immediately, refresh in background for ≤30s                  |
| `must-revalidate`           | Once stale, must not be served without a successful revalidation         |

> [!warning] no-cache does not mean "don't cache"
> `no-cache` means "store, but check with the server (ETag) before every reuse" — great for HTML. `no-store` means "never store" — for sensitive data. Mixing these up either leaks private data into caches or throws away free 304 performance. This is a deliberately tricky interview question.

## 4. The Canonical Recipe (Say This in Interviews)

- **Hashed static assets** (`app.3f2a1c.js`): `Cache-Control: public, max-age=31536000, immutable`. The filename hash *is* the cache key — deploys change the URL, so old caches are irrelevant. This pattern is why bundlers hash filenames at all.
- **HTML documents**: `Cache-Control: no-cache` (or `max-age=0, must-revalidate`). HTML is the *entry point* that references hashed assets — it must always be current, but ETag revalidation keeps it cheap. Cache-first HTML + hashed assets = white-screen-after-deploy.
- **APIs**: usually `no-store` (user-specific, mutable) or `private, no-cache` with ETags for expensive stable reads; `public, s-maxage=60, stale-while-revalidate=300` for anonymous shared data on a CDN.
- **User-specific anything**: `private` at minimum, or a shared cache will serve one user's data to another — a real and famous incident class (`Vary` handling and CDN keying mistakes).

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: SPA deploys break for a subset of users; console shows `ChunkLoadError` / white screen.

Buggy setup — server sends for *everything* (a common default):

```text
Cache-Control: max-age=3600
```

Trace the failure:

1. Monday 10:00 — user's browser caches `index.html` (fresh 1h) referencing `main.OLD.js` (also cached).
2. 10:20 — you deploy: server now has `index.html` → `main.NEW.js`; `main.OLD.js` is deleted.
3. 10:30 — returning user: `index.html` still *fresh* → served from cache with zero network → references `main.OLD.js`.
4. If OLD chunk fell out of their cache (or a lazy route chunk was never cached): request hits the server → **404** → white screen. Support hears "works in incognito" — the incognito profile has no cache. Nothing you deploy fixes users until their hour expires.

Production-safe fix:

```text
/index.html:      Cache-Control: no-cache            (+ ETag)
/assets/*.hash.js: Cache-Control: public, max-age=31536000, immutable
```

And in the app, treat `ChunkLoadError` as a deploy signal: catch it at the router/error boundary and prompt or trigger a reload.

Tradeoff: `no-cache` HTML costs one conditional request per navigation (usually a 304, tens of bytes, but a real RTT on bad networks). Big sites buy that back with `s-maxage` at the CDN + instant purge-on-deploy: users hit the CDN's fresh copy, and the origin only sees purge-time traffic. That adds an infra dependency — purge must be *part of the deploy pipeline*, or you've rebuilt the same bug at the CDN layer. Keeping N previous asset versions on the server during rollout closes the remaining gap for long-lived tabs.

## 6. ETag Mechanics and Gotchas

- Strong (`"abc"`) vs weak (`W/"abc"`): weak = semantically equivalent, not byte-identical; fine for HTML, unusable for range requests.
- ETags are compared by the *server* — implementation is typically a content hash. Beware multi-server setups where default ETags derive from file inode/mtime (classic Apache/nginx issue): each server computes different ETags → revalidation never matches → cache useless. Fix: content-hash ETags or consistent generation.
- `Vary: Accept-Encoding, Accept-Language` splits cache entries per header value — forgetting `Vary` on content negotiation serves gzip to clients that can't decode it or English to everyone; over-Varying (e.g. `Vary: Cookie`) makes the cache nearly useless.
- Conditional *writes* reuse the same machinery: `If-Match: "abc"` on PUT → `412 Precondition Failed` if someone else changed the resource = optimistic locking over HTTP.

## 7. The Layer Stack (Debugging Order)

Request → **memory cache** → **service worker** ([[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|its own Cache Storage, its own rules]]) → **browser HTTP cache** → **CDN** → origin (which may have framework caches — [[22 - Next.js Deep Dive/02 - The Caching Layers|Next.js]]). "Users see old data" debugging = walk this list with DevTools (disable cache, check `x-cache`/`age` response headers, unregister SW) instead of guessing.

## Real-World Use Cases

### Back button shows the account page after logout

User logs out on a shared computer; the next person presses Back — and sees the previous user's dashboard, served from cache with zero network.

```text
# Any HTML rendering per-user data:
Cache-Control: no-store
```

The freshness mechanism working exactly as configured: a fresh cached page needs *no request*, so the server never gets a chance to say "session's gone". `no-store` (not `no-cache` — that still stores) is the only directive that keeps it out of the cache entirely.

> [!warning]
> The back/forward cache (bfcache) is a separate in-memory snapshot with its own rules. `no-store` blocks bfcache in Chrome today; for defense in depth, send `Clear-Site-Data: "cache"` on the logout response.

### New avatar uploaded, old avatar everywhere

Profile photos live at `/avatars/u42.jpg` with `max-age=86400` for CDN performance. Users upload a new photo and it "doesn't update" — same URL, still fresh, so browser and CDN keep answering with the old bytes for up to a day.

```tsx
// Version the URL — content change ⇒ URL change, the same trick as hashed bundles:
<img src={`/avatars/${user.id}.jpg?v=${user.avatarUpdatedAt}`} alt="" />
```

Same rule as the section-4 recipe: mutable content behind a stable URL is the unfixable configuration. Make the URL change on every content change, and year-long freshness becomes safe instead of a support ticket.

### Feature-flags endpoint that survives traffic spikes

An anonymous `/api/flags` config is fetched by every visitor on load. Without cache headers the origin eats one request per pageview; with them, the CDN absorbs nearly all of it.

```ts
// Next.js route handler
export async function GET() {
  const flags = await loadFlags();
  return Response.json(flags, {
    headers: { "Cache-Control": "public, s-maxage=60, stale-while-revalidate=300" },
  });
}
```

`s-maxage` gives the *CDN* a fresh copy while browsers still revalidate, and `stale-while-revalidate` hides refresh latency — visitors get an instant slightly-stale answer while the CDN refetches in the background. Only legal because the response is identical for everyone; anything per-user needs `private`/`no-store` (see practice 3).

## 8. Interview Answer

Short answer:

> Two mechanisms: freshness — `max-age` lets caches answer with no network at all — and revalidation — once stale, the client sends the ETag in `If-None-Match` and the server answers 304 with no body if unchanged. The canonical setup: hashed assets get `max-age=1y, immutable`; HTML gets `no-cache` so it's always revalidated; per-user APIs get `private` or `no-store`.

Deeper answer:

> `no-cache` still caches (it forces revalidation); `no-store` doesn't cache at all. `s-maxage` splits CDN freshness from browser freshness, `stale-while-revalidate` hides refresh latency, and `Vary` keys entries by request headers. The classic outage is fresh-cached HTML referencing deleted hashed chunks after a deploy — HTML must revalidate, assets can live forever because the URL changes. Next.js re-implements this same model as its Data Cache and Full Route Cache with tag-based purging.

## 9. Practice

1. <details><summary>Response has `Cache-Control: no-cache` and an ETag. The user revisits. Describe the request/response exchange and payload sizes.</summary>The browser has the response stored but must revalidate: it sends GET with `If-None-Match: "<etag>"`. If unchanged, server returns 304 with headers only (no body — tens/hundreds of bytes) and the browser uses its stored copy. If changed, a full 200 with new body and new ETag. Cost per reuse: one RTT, near-zero bandwidth.</details>

2. <details><summary>Why is `Cache-Control: max-age=31536000` catastrophic on `/index.html` but ideal on `/assets/app.3f2a1c.js`?</summary>The asset URL embeds a content hash — content changes produce a *new URL*, so year-long caching can never serve wrong content (add `immutable` to skip refresh revalidation). HTML keeps the *same URL* across deploys; a year of freshness means users may not see a new deploy for a year, and cached HTML will reference chunk files that no longer exist → white screens. Mutable-URL resources must revalidate; immutable-URL resources may cache forever.</details>

3. <details><summary>A CDN cached a logged-in user's `/api/me` response and served it to other users. Which header mistakes make this possible, and the fix?</summary>The response lacked `private` (or had `public`) so the shared cache stored it, and the CDN's cache key ignored the session (no appropriate `Vary`/cookie handling — many CDNs strip or ignore `Vary: Cookie` by design). Fix: `Cache-Control: private, no-store` on per-user endpoints; configure the CDN to bypass cache when session cookies/Authorization are present. Never rely on `Vary: Cookie` as the only guard.</details>

4. <details><summary>Product page shows `stale-while-revalidate` behavior: user sees an old price for a moment, then it's correct on next view. Product team asks "can we have fast AND always-correct?" Answer like a senior.</summary>Not from a cache alone — it's a genuine tradeoff triangle: serve-from-cache speed, freshness, origin load. Options with costs: shorten `s-maxage` (more origin load), event-driven purge on price change (infra complexity, purge lag; this is what `revalidateTag` does in Next), or client-side revalidation on mount showing a skeleton (fast-ish, correct, but a layout shift). For prices specifically, purge-on-change is the standard answer: prices change rarely but correctness is contractual.</details>

## Related Notes

- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]]
- [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]]
- [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]
- [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]]
- [[30 - Backend System Design/05 - Caching|Caching]] — the server-side cache these headers mirror
- [[01 - Roadmap|Roadmap]]
