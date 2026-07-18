---
tags: [nextjs, caching, performance]
module: "22 - Next.js Deep Dive"
priority: must-know
status: not-started
aliases: [Data Cache, Full Route Cache, Router Cache]
verified_on: 2026-07-12
version_scope: "Next.js 14–16"
---

# The Caching Layers

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can name the four caching layers, say what each caches and where, and diagnose "why is my data stale" by layer.
- Production signal: you can explain why a mutation didn't show up, and which cache to invalidate, without random `revalidate` guesses.
- Dependencies: [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]], [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]

## Source Anchors

- [Next.js - Caching (Cache Components)](https://nextjs.org/docs/app/getting-started/caching)
- [Next.js - Caching and Revalidating (Previous Model)](https://nextjs.org/docs/app/guides/caching-without-cache-components)
- [Next.js - use cache directive](https://nextjs.org/docs/app/api-reference/directives/use-cache)
- [React - cache](https://react.dev/reference/react/cache)

> Version note: caching defaults changed significantly across Next.js 14 → 15 → 16. The **four-layer mental model** below is the durable way to reason; the **defaults** are called out per version because they are the #1 source of confusion. Verify against your version.

## 1. The Four Layers

Next.js caches at four distinct points, each with a different scope and lifetime:

| Layer | Caches | Where | Scope / Lifetime |
| --- | --- | --- | --- |
| **Request Memoization** | Return value of `fetch` (and React `cache`) during one render | Server | A single render pass — dedupes the same call across components |
| **Data Cache** | Results of data fetches across requests and deploys | Server (persistent) | Until revalidated (time or tag) |
| **Full Route Cache** | Rendered HTML + RSC payload of static routes | Server (build/persistent) | Until the route's data revalidates or redeploy |
| **Router Cache** (Client Cache) | RSC payloads of visited/prefetched routes | Client (in-memory) | Session; short auto-expiry for back/forward instantaneity |

Reading top-to-bottom is the request lifecycle: memoization dedupes within a render; the Data Cache avoids refetching across requests; the Full Route Cache avoids re-rendering static routes; the Router Cache avoids refetching on client navigation.

## 2. Why It Matters

This stack is the single biggest source of "it works locally / why is my data stale / my mutation doesn't show up" confusion in Next.js. Because the layers cache at *different scopes* (one render, across requests, across navigations), a stale value can be trapped in any of them — and the fix differs per layer. Being able to name the layer is the difference between a targeted fix and sprinkling `revalidate` until it "works."

## 3. Each Layer, Precisely

**Request Memoization** — within one render, calling `fetch(sameUrl)` in three components hits the network once; React reuses the result. For non-`fetch` data (ORM/DB), wrap in React's `cache()` to get the same dedup ([[22 - Next.js Deep Dive/06 - Data Fetching Patterns|Data Fetching]]). This is per-render only — it does not persist.

**Data Cache** — persists fetch results across requests and even deploys. Controlled by `fetch` options (`{ next: { revalidate, tags } }`, `cache: 'force-cache'`) or, in Next 16 Cache Components, the `use cache` directive with `cacheLife`/`cacheTag`. Invalidated by time (`revalidate`) or on-demand (`revalidateTag`/`revalidatePath` — [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]]).

**Full Route Cache** — for statically rendered routes, Next caches the rendered output so requests serve HTML/RSC with no re-render. A route opts out (becomes dynamic) by reading request-time data. Revalidating its data invalidates this cache too.

**Router Cache** — client-side, in memory: as you navigate, Next stores RSC payloads so Back/Forward and re-visits are instant without refetching. Its staleness is the classic "I mutated data, navigated back, and see the old version" bug — the client served its cached payload.

> [!warning] Defaults flipped in Next.js 15 — this trips up everyone
> In Next **14**, `fetch` was cached by default and GET Route Handlers were cached by default — people were surprised by *stale* data. In Next **15**, `fetch` is **no longer cached by default**, GET Route Handlers are **not cached by default**, and the client Router Cache `staleTime` defaults to **0** — now people are surprised by *no* caching / extra requests. If you read a tutorial and behavior differs, check the version first. Next **16** Cache Components makes caching explicit via `use cache` rather than implicit defaults.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a dashboard lists projects; a "New Project" action creates one, but the list doesn't update until a hard refresh.

Buggy version:

```tsx
// Server Component
async function ProjectList() {
  const projects = await fetch("https://api/projects", { cache: "force-cache" }).then(r => r.json());
  return <ul>{projects.map(p => <li key={p.id}>{p.name}</li>)}</ul>;
}

// Server Action
async function createProject(formData) {
  "use server";
  await db.project.create({ data: { name: formData.get("name") } });
  // ❌ nothing tells any cache the data changed
}
```

Trace the staleness through the layers: `force-cache` put the list in the **Data Cache**; the route may also be in the **Full Route Cache**; and after the action, the client's **Router Cache** still holds the old RSC payload. The DB has the new project, but every cache layer is serving the old view. A hard refresh bypasses the Router Cache, and if the Data Cache also expired, *then* it appears — hence "only shows after refresh."

Production-safe fix — invalidate the right layers after mutation:

```tsx
async function ProjectList() {
  const projects = await fetch("https://api/projects", {
    next: { tags: ["projects"] },        // tag the Data Cache entry
  }).then(r => r.json());
  return <ul>{projects.map(p => <li key={p.id}>{p.name}</li>)}</ul>;
}

async function createProject(formData) {
  "use server";
  await db.project.create({ data: { name: formData.get("name") } });
  updateTag("projects");                 // ✅ Next 16 Server Action: expire and refresh this
                                         //    tag for immediate read-your-writes
}
```

Trace of the fix: `updateTag("projects")` expires every cached entry tagged `projects` and gives this Server Action read-your-writes behavior, so the affected current view receives fresh RSC without a manual refresh. In Next 16, `revalidateTag("projects", "max")` has a different contract: it marks data stale and uses stale-while-revalidate, which is suitable when a brief stale response is acceptable.

Tradeoffs: tag discipline is real work — you must tag reads and revalidate on writes consistently, or you get stale reads (forgot to revalidate) or over-invalidation (too-broad tag purges caches needlessly, losing performance). Caching everything maximizes speed but maximizes staleness risk; caching nothing is always fresh but slow and costly. The senior skill is caching *deliberately per data's tolerance for staleness* — the same freshness-vs-speed tradeoff as [[20 - Network and Security/02 - HTTP Caching|HTTP caching]], one layer up.

## Real-World Use Cases

### Per-user data leaked through the shared Data Cache

A team caches "the current user's cart" for speed. But the Data Cache is keyed by URL + options and **shared across all visitors** — user A's cart gets served to user B:

```tsx
async function Cart() {
  const cart = await fetch("https://api.shop.com/cart", {
    headers: { cookie: cookies().toString() },
    cache: "force-cache",              // ❌ same URL for everyone → first user's cart cached for all
  }).then((r) => r.json());
  return <CartView items={cart.items} />;
}
```

Fails because the Data Cache persists across *requests*, not per user — the cookie header isn't part of the implicit cache key the way you'd hope. Per-user reads must stay uncached (`cache: "no-store"` or just the Next 15+ default) and live in a dynamic region ([[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]).

> [!warning]
> This is a data-leak class of bug, not a staleness bug. Rule: anything derived from cookies/session never goes in the shared Data Cache. Cache the catalog, never the cart.

### Third-party API quota: the Data Cache as a rate-limit shield

The app shows currency conversion via an external FX API limited to 1,000 calls/day. Every server render calling it directly burns quota (and in Next 15+, uncached is the default — one call *per request*).

```tsx
const rates = await fetch("https://api.fx.dev/latest?base=USD", {
  next: { revalidate: 3600, tags: ["fx-rates"] },   // at most ~24 origin calls/day
}).then((r) => r.json());
```

The Data Cache persists across requests and deploys, so thousands of page views collapse into one origin call per hour — the cache is doing cost control, not just latency work. Same freshness-window reasoning as [[20 - Network and Security/02 - HTTP Caching|HTTP caching]], applied server-side.

### Back-button shows a stale balance: the Router Cache at work

A fintech dashboard: user views their balance, navigates to "Transfer", sends money, taps Back — and sees the **old balance**. Server data is fine; the client Router Cache replayed the stored RSC payload for the previous route without asking the server.

```tsx
// In the transfer Server Action — invalidate so navigation gets fresh RSC:
async function transfer(formData: FormData) {
  "use server";
  await executeTransfer(formData);
  updateTag("balance");                // Next 16; revalidatePath("/dashboard") in 14/15
}
```

The mechanism is the Router Cache's whole purpose — instant back/forward from in-memory payloads — turned into a bug when data mutates between visits. Server-side invalidation from the action also purges the client's stale entry for affected routes; for money-grade freshness you can additionally drop `staleTimes` to 0 or call `router.refresh()` on focus.

> [!tip]
> Diagnose by scope: "wrong after back-navigation, correct after hard refresh" fingerprints the Router Cache specifically — the hard refresh bypasses only the client layer.

## 5. Interview Answer

Short answer:

> Four layers: Request Memoization dedupes identical fetches within one render; the Data Cache persists fetch results across requests/deploys; the Full Route Cache stores rendered output of static routes; the client Router Cache holds RSC payloads of visited routes for instant navigation. "Stale data" bugs mean a value is trapped in one of these — you diagnose by asking which scope (one render, across requests, across navigations) is serving the old value.

Deeper answer:

> After a mutation you invalidate the right layer — a bare DB write updates none of them. In a Next 16 Server Action, use `updateTag` when the actor must immediately read their own write; use `revalidateTag(tag, "max")` when stale-while-revalidate is acceptable; use `revalidatePath` when the unit of staleness is a route. Defaults matter: Next 14 cached fetch and GET handlers by default (stale surprises); Next 15 flipped both to uncached and set Router Cache staleTime to 0 (extra-request surprises); Next 16 Cache Components makes caching explicit with `use cache`, `cacheLife`, and `cacheTag`. The discipline is tag-on-read, invalidate-on-write, and caching per the data's staleness tolerance.

## 6. Practice

1. <details><summary>A user updates their profile via a Server Action; the DB is correct but the profile page shows old data until refresh. Walk the layers.</summary>The read was cached in the Data Cache (and possibly the route in the Full Route Cache); after the write, the client Router Cache still holds the old RSC payload for the profile route. The DB changed but no cache was told. In Next 16, use `updateTag('profile')` for immediate read-your-writes, or `revalidatePath('/profile')` when invalidating the route is the right unit. Use `revalidateTag('profile', 'max')` only when stale-while-revalidate is acceptable. Hard refresh "fixes" it only by bypassing the Router Cache and hoping the Data Cache also expired.</details>

2. <details><summary>Same `fetch('/api/user')` is called in a layout and three components. How many network requests in one render, and which layer is responsible?</summary>One. Request Memoization dedupes identical fetches within a single render pass, so the layout and components share the result. It's per-render only — a subsequent request re-fetches unless the Data Cache also stored it. For non-fetch data (DB/ORM), wrap in React `cache()` to get the same per-render dedup.</details>

3. <details><summary>You upgraded Next 14 → 15 and suddenly every page hits your API on each request, spiking cost. What changed and what's the fix?</summary>Next 15 stopped caching `fetch` by default (and GET Route Handlers), so previously-cached reads now go to the origin every request. Fix: explicitly opt the appropriate fetches into caching — `fetch(url, { cache: 'force-cache' })` or `{ next: { revalidate: N, tags: [...] } }` — for data that tolerates staleness. This is intended: Next made caching opt-in to stop the reverse surprise (unexpected staleness) from Next 14. Audit which reads actually need freshness.</details>

4. <details><summary>Why can over-broad tagging hurt even though it "fixes" staleness?</summary>A too-coarse tag (e.g., tagging everything `data`) means any mutation revalidates *all* cached reads, discarding cache entries that didn't change — you pay to re-render/refetch unrelated data, losing the performance the cache existed for. Correct granularity: tag by entity/collection (`projects`, `user:42`) so a write invalidates exactly the affected reads. Staleness and over-invalidation are the two failure modes; precise tags avoid both.</details>

## Related Notes

- [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]
- [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]]
- [[22 - Next.js Deep Dive/06 - Data Fetching Patterns|Data Fetching Patterns]]
- [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]
- [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]]
- [[01 - Roadmap|Roadmap]]
- [[90 - Labs/04 - Next Cached Dashboard Mutation Lab|Next Cached Dashboard Mutation Lab]] — prove the invalidation story by building it
