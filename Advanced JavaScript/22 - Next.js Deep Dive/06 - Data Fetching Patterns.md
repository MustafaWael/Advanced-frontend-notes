---
tags: [nextjs, data-fetching, rsc, performance]
module: "22 - Next.js Deep Dive"
priority: must-know
status: not-started
aliases: [Waterfalls, Parallel Fetching]
---

# Data Fetching Patterns

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can spot a request waterfall, fix it with parallel fetching, and explain request memoization + React `cache`.
- Production signal: your Server Components fetch in parallel where possible and stream independent slow parts instead of blocking.
- Dependencies: [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]], [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]

## Source Anchors

- [Next.js - Fetching Data (Server Components)](https://nextjs.org/docs/app/getting-started/fetching-data)
- [Next.js - Caching: Request Memoization / Preloading](https://nextjs.org/docs/app/guides/caching-without-cache-components)
- [React - cache](https://react.dev/reference/react/cache)
- [MDN - Promise.all](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all)

## 1. Concept

In the App Router, Server Components fetch data by `await`ing directly — no `useEffect`, no client fetch. But *how* you await determines performance. The enemy is the **waterfall**: sequential awaits where each request waits for the previous one to finish, even when they're independent.

```tsx
// ❌ Waterfall: user → posts → comments, serially. Total = sum of all three.
const user = await getUser(id);
const posts = await getPosts(id);
const comments = await getComments(id);
```

```tsx
// ✅ Parallel: start all three, await together. Total = the slowest one.
const [user, posts, comments] = await Promise.all([
  getUser(id), getPosts(id), getComments(id),
]);
```

If the three take 100/200/300ms: the waterfall is ~600ms; parallel is ~300ms. Same data, half the latency ([[08 - Async JavaScript/03 - Promise Methods|Promise.all]]).

## 2. Why It Matters

- Under HTTP/2+, request *count* barely matters ([[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP versions]]) — request *dependencies* (waterfalls) dominate frontend latency. This is *the* modern data-fetching performance lesson.
- Server Components make waterfalls easy to create accidentally (sequential `await` reads naturally) and easy to fix (Promise.all, or component-level parallelism). Interviewers test whether you see them.

## 3. Legitimate vs Accidental Waterfalls

A waterfall is only justified when a request genuinely *depends* on a previous result:

```tsx
const user = await getUser(id);              // must run first...
const team = await getTeam(user.teamId);     // ...because we need user.teamId — real dependency
```

Accidental waterfalls are independent requests written sequentially out of habit — the common, fixable case. Diagnosis: "does request B need any value from request A's result? If no → they should be parallel."

**Component-level parallelism**: sibling Server Components each fetching their own data render (and fetch) in parallel automatically — you don't always need explicit `Promise.all`; splitting into components achieves it. Combined with `<Suspense>`, each streams in as its data resolves ([[22 - Next.js Deep Dive/01 - Rendering Strategies|streaming]]).

## 4. Request Memoization and the Preload Pattern

**Request Memoization** ([[22 - Next.js Deep Dive/02 - The Caching Layers|caching layers]]): within one render, identical `fetch` calls are deduped automatically, so a layout and a page both fetching the current user hit the network once. For non-`fetch` data (DB/ORM), wrap in React's `cache()` to get the same dedup:

```tsx
import { cache } from "react";
export const getUser = cache(async (id: string) => db.user.findUnique({ where: { id } }));
// Called in layout + page + a component → one DB query per render.
```

**Preload pattern**: to avoid a waterfall between "check something" and "fetch the thing," kick off the fetch early without awaiting it, so it's in flight while other work runs:

```tsx
export default async function Page({ params }) {
  preload(params.id);                 // starts getItem(id) — not awaited (memoized/cache-backed)
  const ok = await checkAccess();     // runs concurrently with the item fetch
  return ok ? <Item id={params.id} /> : null;   // getItem already resolved/in-flight
}
```

> [!tip] The senior fix order for a slow page
> 1. Are independent requests serialized? → parallelize (Promise.all / sibling components). 2. Is a genuinely slow, independent part blocking fast content? → wrap it in `<Suspense>` and stream it. 3. Are the same reads happening repeatedly in one render? → memoize with `cache()`. Only then reach for more caching (Data Cache). Structure beats config.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a dashboard page is slow; profiling shows a 1.2s server render for data that should take ~400ms.

Buggy version — accidental waterfall + repeated reads:

```tsx
export default async function Dashboard() {
  const user = await getUser();              // 200ms
  const stats = await getStats();            // 400ms — doesn't need user
  const activity = await getActivity();      // 300ms — doesn't need user or stats
  const notifications = await getUser();     // 200ms — SAME user, re-fetched
  return <Layout user={user} stats={stats} activity={activity} n={notifications} />;
}
```

Trace: four sequential awaits = 200+400+300+200 ≈ 1.1s, and the second `getUser()` refetches identical data. Independent requests are needlessly serialized.

Production-safe fix:

```tsx
const getUser = cache(async () => db.user.current());   // dedupe repeated reads

export default async function Dashboard() {
  const [user, stats, activity] = await Promise.all([
    getUser(), getStats(), getActivity(),               // parallel: ~400ms (the slowest)
  ]);
  // getUser() elsewhere in this render reuses the memoized result — no second query
  return <Layout user={user} stats={stats} activity={activity} />;
}
```

Even better if `getStats` is the slow, independent part and the rest can paint first: leave the fast data awaited in the page and stream stats via a Suspense-wrapped child, so the user sees the dashboard shell at ~300ms and stats fill in.

Tradeoffs: `Promise.all` fails fast — one rejected request rejects the whole batch ([[08 - Async JavaScript/03 - Promise Methods|Promise.all vs allSettled]]); if partial data is acceptable, use `Promise.allSettled` and render what succeeded. Parallelizing also means all requests hit your backend simultaneously — usually fine, but a burst of heavy queries can spike DB load; component-level streaming spreads them slightly. And over-splitting into many Suspense boundaries creates a "popcorn" of skeletons — group related data. The structural fixes (parallelize, stream, memoize) are almost always better first moves than adding cache layers.

## Real-World Use Cases

### N+1 waterfall in a list: awaiting inside a loop

An orders page enriches each order with live shipping status from a carrier API. Written the natural way, 20 orders = 20 *serial* round trips:

```tsx
// ❌ each iteration awaits before the next starts — 20 × 150ms ≈ 3s
const withStatus = [];
for (const order of orders) {
  withStatus.push({ ...order, status: await getShippingStatus(order.trackingId) });
}

// ✅ start all 20 at once — ≈ 150ms total
const withStatus = await Promise.all(
  orders.map(async (order) => ({
    ...order,
    status: await getShippingStatus(order.trackingId),
  }))
);
```

Same diagnosis rule as section 3: no iteration depends on another's result, so serializing them is accidental. `map` starts every promise before `Promise.all` awaits any — the loop version never gets that concurrency.

> [!warning]
> 20 parallel calls can trip a carrier API's rate limit. If it does, batch (`getShippingStatuses(ids)`) or chunk with a small concurrency cap — don't retreat to the full serial waterfall.

### Passing a promise to a client component with `use()`

A product page needs reviews, but reviews are slow and interactive (sort/filter → client component). Awaiting them on the server blocks the whole page; fetching in `useEffect` starts a second, later waterfall. Instead: start on the server, resolve in the client.

```tsx
// Server Component — kick off, do NOT await
export default function ProductPage({ params }) {
  const reviewsPromise = getReviews(params.id);
  return (
    <>
      <ProductDetails id={params.id} />
      <Suspense fallback={<ReviewsSkeleton />}>
        <Reviews reviewsPromise={reviewsPromise} />
      </Suspense>
    </>
  );
}

// Client Component
"use client";
import { use } from "react";
export function Reviews({ reviewsPromise }) {
  const reviews = use(reviewsPromise);   // suspends until the server-started fetch resolves
  return <SortableReviewList reviews={reviews} />;
}
```

The fetch is in flight *during* the rest of the server render and streams into an interactive component — the preload idea from section 4 extended across the server/client boundary ([[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense]]).

### `generateMetadata` and the page fetching the same data

SEO requires `generateMetadata` to fetch the product for `<title>`/OG tags — and the page body fetches the same product. Unmemoized, that's two identical DB queries per request:

```tsx
const getProduct = cache(async (id: string) =>
  db.product.findUnique({ where: { id } })
);

export async function generateMetadata({ params }) {
  const product = await getProduct(params.id);      // query #1
  return { title: product.name, description: product.summary };
}

export default async function ProductPage({ params }) {
  const product = await getProduct(params.id);      // memoized — no second query
  return <ProductView product={product} />;
}
```

Request Memoization (or React `cache()` for non-`fetch` reads, as here) spans `generateMetadata`, layout, and page within one render pass — this duplication is invisible in the UI and shows up only as doubled DB load ([[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]).

## 6. Interview Answer

Short answer:

> In Server Components you `await` data directly, so the risk is waterfalls — independent requests written sequentially, where total time is the sum instead of the max. Fix with `Promise.all` (or sibling components that fetch in parallel automatically), reserving sequential awaits for genuine data dependencies. Request Memoization dedupes identical fetches within a render; React `cache()` does the same for DB/ORM reads.

Deeper answer:

> Under HTTP/2+, request dependencies dominate latency more than request count, so the highest-leverage fix is removing accidental waterfalls, then streaming genuinely slow independent parts with `<Suspense>`, then deduping repeated reads with `cache()` — structure before configuration. The preload pattern starts a fetch early without awaiting so it overlaps other work. Tradeoffs: `Promise.all` is fail-fast (use `allSettled` for partial rendering), parallel fetches burst backend load, and over-splitting Suspense boundaries creates staggered skeleton popcorn.

## 7. Practice

1. <details><summary>Three fetches take 100/150/250ms. What's the total for sequential awaits vs Promise.all, and when is sequential correct?</summary>Sequential: ~500ms (sum). Promise.all: ~250ms (the slowest, since they run concurrently). Sequential is correct only when a request depends on a previous result (e.g., you need `user.teamId` before fetching the team). If requests are independent, serializing them is an accidental waterfall — parallelize.</details>

2. <details><summary>A layout and three child components each call `fetch('/api/session')`. How many requests, and how would you dedupe a DB-based equivalent?</summary>For `fetch`, one request — Next's Request Memoization dedupes identical fetch calls within a single render. For a DB/ORM equivalent (no fetch), wrap the function in React's `cache()`: `const getSession = cache(() => db.session.current())`, so all callers in one render share a single query. Both are per-render dedup, not cross-request caching.</details>

3. <details><summary>Dashboard has fast user info and a slow analytics widget (2s). How do you avoid the widget blocking the whole page?</summary>Don't await the analytics data at the page top. Render the fast content immediately and wrap the analytics widget in `<Suspense fallback={<Skeleton />}>`, letting it fetch its own data and stream in when ready. The user sees the dashboard shell + user info right away; the widget appears at ~2s without holding the rest hostage. This is streaming + component-level data fetching.</details>

4. <details><summary>You parallelize with `Promise.all` and now one flaky endpoint failing blanks the whole page. Fix?</summary>`Promise.all` rejects if any promise rejects, discarding the successful results. If partial rendering is acceptable, use `Promise.allSettled` and render each section based on its own fulfilled/rejected status (show data or a per-section error). Alternatively, isolate the flaky fetch in its own Suspense + Error Boundary child so its failure degrades only that widget, not the page. Choose based on whether the data is essential to the whole page.</details>

## Related Notes

- [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]
- [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]]
- [[01 - Roadmap|Roadmap]]
