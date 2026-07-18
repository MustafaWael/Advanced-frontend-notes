---
tags: [nextjs, caching, revalidation]
module: "22 - Next.js Deep Dive"
priority: must-know
status: not-started
aliases: [revalidateTag, revalidatePath, ISR, updateTag]
verified_on: 2026-07-12
version_scope: "Next.js 14–16"
---

# Revalidation

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can compare time-based vs on-demand revalidation and choose `revalidateTag` vs `revalidatePath` correctly.
- Production signal: your mutations invalidate exactly the right cached data, and you use tags to model data dependencies.
- Dependencies: [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]], [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]

## Source Anchors

- [Next.js - Revalidating](https://nextjs.org/docs/app/getting-started/revalidating)
- [Next.js - revalidateTag](https://nextjs.org/docs/app/api-reference/functions/revalidateTag)
- [Next.js - revalidatePath](https://nextjs.org/docs/app/api-reference/functions/revalidatePath)
- [Next.js - cacheTag / cacheLife](https://nextjs.org/docs/app/api-reference/directives/use-cache)

> Version note: Next 16 Cache Components adds `cacheTag`/`cacheLife`/`updateTag` for the `use cache` model. In Next 16, `revalidateTag(tag, profile)` is stale-while-revalidate and the single-argument form is deprecated (it type-errors; migrate to `revalidateTag(tag, "max")` or `updateTag`); `updateTag(tag)` is Server-Action-only and gives immediate read-your-writes. Pre-16 (Next 14/15) examples commonly use `fetch` `next: { revalidate, tags }` plus single-argument `revalidateTag`/`revalidatePath`. Same concepts, version-specific APIs.

### The Next 16 invalidation menu, disambiguated

| Call | Where | Contract |
| --- | --- | --- |
| `updateTag(tag)` | Server Actions only | Expire **and refresh now** — the caller's response includes fresh data (read-your-writes) |
| `revalidateTag(tag, "max")` | Server Actions, Route Handlers | Mark stale; serve stale while revalidating in the background (SWR) |
| `revalidateTag(tag, "hours" \| "days" \| { expire: N })` | Same | SWR with a bounded tolerated staleness window |
| `revalidatePath(path)` | Same | Invalidate everything cached for one route |
| `refresh()` | Server Actions only | Refresh the **client router's** current view — does **not** invalidate any tagged/server cache |

> [!warning] `refresh()` is not an invalidation API
> `refresh()` (from `next/cache`) re-renders the current route on the client so the user sees a fresh render of *uncached* data — but tagged Data Cache entries stay cached and stale. If a mutation changed tagged data, `refresh()` alone will re-show the same cached value. Use `updateTag` (or `revalidateTag`) for cached data; use `refresh()` when the goal is only to re-pull dynamic, uncached reads (e.g., after a mutation that only affects per-request data).

## 1. Concept

Revalidation is how cached data ([[22 - Next.js Deep Dive/02 - The Caching Layers|Data Cache / Full Route Cache]]) becomes fresh again. Two triggers:

- **Time-based**: "this data may be stale for at most N seconds." Set `revalidate: N` on a fetch, route segment, or `cacheLife`. After N seconds, the next request serves the stale copy *and* triggers a background refresh (stale-while-revalidate) — so users rarely wait. This is ISR.
- **On-demand**: "invalidate this data because something changed." In Next 16, use `updateTag(tag)` inside a Server Action when the actor must immediately see their write; use `revalidateTag(tag, "max")` for stale-while-revalidate; use `revalidatePath(path)` when a route is the unit to refresh.

## 2. Why It Matters

- It's the answer to the two failure modes of caching: too stale (need shorter time or on-demand invalidation) and too fresh/costly (need longer time). Getting it right is what makes aggressive caching *safe*.
- On-demand revalidation with tags is the production pattern for correctness-critical data (prices, inventory, published content) that also needs cache performance.

## 3. Time-Based vs On-Demand — Choosing

**Time-based** fits data with a tolerable staleness window and no precise "changed" event you can hook: a news feed (`revalidate: 60`), weather, aggregate stats. Simple, no wiring — you accept up to N seconds stale.

**On-demand** fits data that changes via *your* mutations. In Next 16, a user editing a post should usually call `updateTag('post:42')` inside its Server Action when the UI must immediately reflect the change. An admin publishing documentation may use `revalidateTag('posts', 'max')` when serving stale content while it revalidates is acceptable. You must call the chosen invalidation path from every relevant mutation.

Combine them: cache with a long time-based fallback *and* invalidate on-demand when you know it changed — belt and suspenders. Prices might be `revalidate: 3600` (safety net) plus `updateTag('prices')` in the updating Server Action for immediate correctness.

## 4. revalidateTag vs revalidatePath

**Tag invalidation** targets every cached entry carrying that tag — you tag reads by *data dependency* and invalidate by the same tag on write. In Next 16, `updateTag(tag)` is the immediate Server-Action form; `revalidateTag(tag, "max")` is the stale-while-revalidate form. This models "what data changed," decoupled from which pages show it:

```tsx
// Read: tag the data
await fetch(`/api/posts/${id}`, { next: { tags: [`post:${id}`, "posts"] } });

// Write: invalidate by data identity — every page using post:42 refreshes
async function editPost(id, data) {
  "use server";
  await db.post.update({ where: { id }, data });
  updateTag(`post:${id}`);       // Next 16 Server Action: immediate read-your-writes
}
```

**`revalidatePath(path)`** invalidates everything cached for a route path — "this *page* is stale." Coarser; use when you think in pages rather than data, or to force a specific route fresh:

```tsx
revalidatePath("/dashboard");      // whole route
revalidatePath("/blog/[slug]", "page");  // dynamic route form
```

> [!tip] Prefer tags for data, paths for pages
> Tags scale better: one tag invalidation (`updateTag('post:42')` for an immediate Server-Action update, or `revalidateTag('post:42', 'max')` for SWR) covers the detail page, list, and sidebar widget wherever they read that tagged data. `revalidatePath` requires you to enumerate every affected route — brittle as the app grows. Reach for it when the unit of staleness genuinely is "this page," or as a blunt fix.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an e-commerce admin updates a product's price; the price is shown on the product page, the category list, and a homepage "deals" carousel.

Buggy version — revalidate one path:

```tsx
async function updatePrice(id, price) {
  "use server";
  await db.product.update({ where: { id }, data: { price } });
  revalidatePath(`/products/${id}`);   // ❌ only the detail page; list + carousel still stale
}
```

Trace: the detail page refreshes, but the category list (`/category/...`) and the homepage carousel (`/`) cached the old price independently — customers see inconsistent prices across the site, a real trust/correctness bug (and potentially a pricing dispute).

Production-safe fix — tag by data, revalidate the tag:

```tsx
// Everywhere the price is read:
await fetch(`/api/products/${id}`, { next: { tags: [`product:${id}`, "products"] } });

async function updatePrice(id, price) {
  "use server";
  await db.product.update({ where: { id }, data: { price } });
  updateTag(`product:${id}`);          // ✅ immediate Server-Action update for tagged reads
}
```

Tradeoffs: tag discipline must be consistent — a read that forgot the tag won't be invalidated (silent staleness), and tags too broad over-invalidate (revalidating `products` on one price change re-renders every product page). Time-based revalidation as a backstop (`revalidate: 3600`) caps the damage of a missed tag at one hour, at the cost of some background refreshes. There's genuine engineering in mapping your data model to a tag taxonomy — but it's the same rigor that makes any cache invalidation correct ("one of the two hard problems in CS").

## Real-World Use Cases

### Headless CMS publish webhook → on-demand revalidation

Editors publish in Contentful/Sanity; the site must update within seconds without a redeploy. The CMS calls a Route Handler on publish, and the handler invalidates by tag:

```tsx
// app/api/revalidate/route.ts
import { revalidateTag } from "next/cache";

export async function POST(req: Request) {
  if (req.headers.get("x-webhook-secret") !== process.env.CMS_WEBHOOK_SECRET)
    return new Response("Forbidden", { status: 403 });   // it's a public endpoint — gate it
  const { slug } = await req.json();
  revalidateTag(`post:${slug}`, "max");                   // Next 16 form; revalidateTag(tag) in 14/15
  return Response.json({ revalidated: true });
}
```

This is the canonical "static performance, CMS freshness" architecture: pages stay in the Full Route Cache indefinitely and the *change event itself* triggers invalidation — no polling, no `revalidate: 60` guesswork. Note `updateTag` isn't available here: it's Server-Action-only, and a webhook has no client waiting to read its own write — SWR is exactly right.

> [!warning]
> The webhook handler is internet-reachable. Verify a shared secret or signature before revalidating, or anyone can purge your caches at will (a cheap cache-stampede DoS).

### Live leaderboard: time-based, because there is no clean "changed" event

A game's leaderboard updates from thousands of score writes per minute. On-demand tagging would mean invalidating on every score submit — constant purging, zero cache hits. There's no single mutation to hook, so buy a staleness window instead:

```tsx
const leaderboard = await fetch("https://api.game.dev/leaderboard", {
  next: { revalidate: 30 },     // stale-while-revalidate: users never wait for the refresh
}).then((r) => r.json());
```

Mechanically this is ISR: after 30s the next visitor gets the cached copy instantly while a background refresh replaces it. High-write, tolerance-for-30s-stale data is the profile where time-based beats on-demand outright.

### Comment thread: `updateTag` for the author, SWR for everyone else

A user posts a comment and the thread must show it *to them* immediately — read-your-writes — while other viewers can tolerate seconds of staleness:

```tsx
async function postComment(articleId: string, formData: FormData) {
  "use server";
  await db.comment.create({ data: { articleId, body: formData.get("body") } });
  updateTag(`comments:${articleId}`);   // the author's response includes the fresh thread
}
```

One call covers both audiences: `updateTag` expires the tag *and* refreshes the author's current view in the action response, while other visitors simply get fresh data on their next request. Reaching for `refresh()` here is the classic mistake — it re-renders but re-reads the same cached entry (see the warning above). Pairs with [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]] and the optimistic-UI patterns in [[21 - React Internals and Patterns/10 - React 19|React 19]].

## 6. Interview Answer

Short answer:

> Time-based revalidation (`revalidate: N`) serves cached data for up to N seconds, then refreshes in the background — that's ISR, for data with a tolerable staleness window. In Next 16, on-demand invalidation uses `updateTag` for immediate Server-Action read-your-writes, `revalidateTag(tag, 'max')` for stale-while-revalidate, or `revalidatePath` for a route. Prefer tags: tag reads by data dependency and invalidate that tag on write, so every page using the data is covered in one call.

Deeper answer:

> `revalidateTag` models "what data changed" independent of which routes display it, so one call covers the detail page, list, and any widget reading the same tagged data — far more maintainable than `revalidatePath`, which invalidates a specific route and forces you to enumerate every affected page. The robust pattern combines both: on-demand tags for immediate correctness plus a time-based backstop to bound the impact of a missed tag. The hard part is a consistent tag taxonomy — tag every read, revalidate every write, granular enough to avoid over-invalidation.

## 7. Practice

1. <details><summary>News homepage vs a user's order status — time-based or on-demand for each?</summary>News homepage: time-based (`revalidate: 30–60`) — no discrete "changed" event, and 30–60s staleness is acceptable, so cache and auto-refresh. Order status: on-demand — it changes through known mutations (payment, shipping updates) and users expect prompt accuracy, so call `updateTag('order:123')` in the updating Server Action (optionally with a short time-based backstop). Match the trigger to whether you have a precise change event and how much staleness is tolerable.</details>

2. <details><summary>Why does tagging reads scale better than revalidatePath for invalidation?</summary>A tag names a piece of *data*; revalidating it refreshes every cached read carrying that tag, wherever those reads live — one call, all consumers. `revalidatePath` names a *route*, so you must know and list every route displaying the changed data and call it for each; adding a new page that shows the data silently misses invalidation until someone remembers to add its path. Tags decouple "data changed" from "which pages care."</details>

3. <details><summary>An admin edits a product but the change appears only after ~1 hour. Two hypotheses.</summary>(1) The mutation doesn't call any on-demand revalidation, so the data only refreshes when the time-based `revalidate: 3600` window elapses — add `revalidateTag`/`revalidatePath` in the action. (2) The revalidation call uses a tag/path the reads don't actually carry (typo or missing tag on the fetch), so nothing is invalidated and it again waits for the time-based backstop. Verify the read's tags match the write's revalidation exactly.</details>

4. <details><summary>A teammate calls `refresh()` in a Server Action after editing a cached, tagged product and reports "the page still shows the old price." Why, and what's the fix?</summary>`refresh()` only re-renders the current route on the client; it does not touch the Data Cache, so the re-render reads the *same cached, tagged entry* and re-displays the stale price. Fix: call `updateTag('product:42')` (immediate read-your-writes) or `revalidateTag('product:42', 'max')` (SWR) so the cached entry is actually invalidated. `refresh()` is only sufficient when the changed data is dynamic/uncached.</details>

5. <details><summary>What's the risk of invalidating `products` on every single product edit in a 100k-product catalog?</summary>Over-invalidation: one edit expires the cached reads for *all* products tagged `products`, forcing mass re-fetch/re-render and a cache-miss stampede on a large catalog. Use a granular tag (`product:${id}`) for the specific edit, and reserve the broad `products` tag for operations that genuinely affect the whole collection (e.g., a category restructure). Granularity is the lever between staleness and wasted work.</details>

## Related Notes

- [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]
- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]
- [[01 - Roadmap|Roadmap]]
