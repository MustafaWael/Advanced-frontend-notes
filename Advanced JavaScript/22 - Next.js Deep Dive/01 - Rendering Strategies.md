---
tags: [nextjs, rendering, ssr, ssg]
module: "22 - Next.js Deep Dive"
priority: must-know
status: not-started
aliases: [SSR, SSG, ISR, PPR]
verified_on: 2026-07-12
version_scope: "Next.js 14–16"
---

# Rendering Strategies

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can define SSR, SSG, ISR, streaming, and PPR and pick one from requirements — freshness, personalization, scale, SEO.
- Production signal: you choose per route deliberately and know what "dynamic" actually costs versus static.
- Dependencies: [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]], [[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense and Concurrent Features]]

## Source Anchors

- [Next.js - Server Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [Next.js - Caching (Cache Components)](https://nextjs.org/docs/app/getting-started/caching)
- [Next.js - Partial Prerendering](https://nextjs.org/docs/app/getting-started/partial-prerendering)
- [web.dev - Rendering on the Web](https://web.dev/articles/rendering-on-the-web)

> Version note: this reflects Next.js 15/16. In Next.js 16, **Cache Components** are an opt-in (`cacheComponents: true`) and introduce the `use cache` directive. That opt-in enables the current Partial Prerendering model; PPR is not silently enabled for every app. The strategy *concepts* below are stable, but the APIs and defaults changed — verify against nextjs.org for your version.

## 1. The Strategies

| Strategy | When HTML is built | Freshness | Best for |
| --- | --- | --- | --- |
| **SSG** (static) | Build time, once | Stale until rebuild | Marketing, docs, blog — content that rarely changes |
| **SSR** (dynamic) | Every request | Always fresh | Personalized dashboards, per-user/auth pages |
| **ISR** (incremental) | Build + revalidate on a timer/on-demand | Fresh within revalidate window | Product pages, feeds — mostly-static, periodically updated |
| **Streaming SSR** | Per request, sent in chunks | Fresh | Pages with a fast shell + slow parts |
| **PPR** (partial prerender) | Static shell at build + dynamic holes at request | Mixed per region | The general case: one page with static + personalized parts |

The core tension: **static is fast and cheap and scales infinitely (a CDN serves a file) but can be stale and can't be personalized; dynamic is fresh and personalized but costs a server render per request.** Every strategy is a point on that spectrum, and PPR is the attempt to stop choosing per *page* and instead choose per *region*.

## 2. Why It Matters

- Rendering strategy is the highest-leverage architecture decision in a Next.js app — it determines TTFB, cost, cache behavior, and SEO.
- Interviewers probe it to see whether you reason from requirements ("this page is per-user, so it can't be statically cached") rather than defaulting to "SSR everything."

## 3. Server Components Are the Substrate

In the App Router, components are **Server Components by default** — they run on the server (build or request time), never ship to the client, can directly `await` data, and emit an **RSC payload** rather than raw HTML for client navigation ([[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client]]). `"use client"` marks the boundary where interactivity (state, effects, event handlers) begins and JS ships to the browser.

What decides static vs dynamic for a route is **whether it reads request-time data**: cookies, headers, `searchParams`, or uncached fetches. Touch any of those and that part becomes dynamic (rendered per request). Avoid them and it can be prerendered.

## 4. Streaming and PPR — The Current Model

**Streaming** (via `<Suspense>`) sends the ready shell immediately and streams slow parts as their data resolves ([[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense mechanism]]). The user sees the header and layout instantly instead of waiting for the slowest query.

**Partial Prerendering (PPR)** — available when a Next 16 app opts into Cache Components — combines both on one page: a static shell (nav, cached content) is prerendered and served instantly from the edge, while dynamic holes (a personalized greeting, a live cart) are wrapped in `<Suspense>` and stream in at request time.

```tsx
export default function BlogPage() {
  return (
    <>
      <Header />                              {/* static: in the prerendered shell */}
      <BlogPosts />                           {/* 'use cache' → cached, in the shell */}
      <Suspense fallback={<p>Loading…</p>}>
        <UserPreferences />                   {/* reads cookies → streams at request time */}
      </Suspense>
    </>
  );
}
```

> [!tip] The mental shift PPR forces
> Old model: pick one strategy per page. PPR model: a page is a static shell with dynamic holes, and you annotate *which parts* are cached (`use cache`) versus per-request (`<Suspense>` around runtime-API reads). Under Cache Components, reading a runtime API (cookies/headers) *outside* a Suspense boundary and without `use cache` is a build error — the framework forces you to declare each region's nature.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a product page must be fast and SEO-friendly, show a mostly-static product, but also a per-user "recently viewed" strip.

Buggy version — one blanket choice:

```tsx
// Reads cookies at the top → the WHOLE route becomes dynamic (SSR per request)
export default async function ProductPage({ params }) {
  const user = await getUserFromCookies();        // forces dynamic rendering of everything
  const product = await getProduct(params.id);    // now re-fetched per request too
  const recent = await getRecentlyViewed(user.id);
  return <><Product data={product} /><RecentStrip items={recent} /></>;
}
```

Trace the cost: because the whole component reads cookies, Next can't prerender any of it — every visit does a full server render including the expensive, *identical-for-everyone* product fetch. You lost the CDN-static win for the 95% of the page that never changes per user, hurting TTFB and server cost at scale.

Production-safe fix — isolate the dynamic hole:

```tsx
export default async function ProductPage({ params }) {
  return (
    <>
      <Product id={params.id} />               {/* cached / static shell */}
      <Suspense fallback={<RecentSkeleton />}>
        <RecentlyViewed />                      {/* reads cookies HERE → only this streams */}
      </Suspense>
    </>
  );
}

async function Product({ id }) {
  'use cache';                                  // Next 16: cached, part of the static shell
  const product = await getProduct(id);
  return <ProductView data={product} />;
}
```

Now the product renders once and serves statically from the edge; only the per-user strip renders per request and streams in. SEO gets the product in the initial HTML; the user gets instant paint.

Tradeoffs: PPR/Cache Components pushes complexity into *deciding and annotating* each region (`use cache` vs Suspense), and getting caching wrong flips to the stale-data bugs of [[22 - Next.js Deep Dive/02 - The Caching Layers|the caching layers]]. Pre-16 apps express the same intent with route segment config and `fetch` cache options — same concepts, older API. And genuinely per-user pages (a bank dashboard) legitimately are fully dynamic; don't contort them into static.

## Real-World Use Cases

### CMS-backed blog: SSG + `generateStaticParams` + webhook revalidation

A marketing blog pulls posts from a headless CMS. Content changes a few times a week, traffic spikes when a post goes viral — the exact profile where paying a server render per request is pure waste.

```tsx
// app/blog/[slug]/page.tsx
export async function generateStaticParams() {
  const posts = await cms.getAllPosts();
  return posts.map((p) => ({ slug: p.slug }));   // every post prerendered at build
}

export default async function PostPage({ params }) {
  const post = await cms.getPost(params.slug);   // no request-time APIs → stays static
  return <Article post={post} />;
}
```

This stays SSG because nothing in the tree reads cookies/headers/searchParams — the route is fully known at build. When an editor hits Publish, a CMS webhook triggers on-demand invalidation so you don't rebuild the site ([[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]]).

> [!tip]
> Viral traffic hits a CDN file, not your server. This is the "scales infinitely" end of the spectrum — reach for it whenever content is identical for everyone.

### Flight search results: `searchParams` makes it dynamic — stream around it

A travel site's `/search?from=CAI&to=LHR&date=...` page can't be prerendered: the whole point is request-specific input. But the filters sidebar and page chrome are the same for everyone — don't let the slow results query gate them.

```tsx
export default function SearchPage({ searchParams }) {
  return (
    <>
      <SearchFilters />                                  {/* static chrome, paints instantly */}
      <Suspense fallback={<ResultsSkeleton />} key={searchParams.date}>
        <FlightResults query={searchParams} />           {/* dynamic: slow aggregator call streams in */}
      </Suspense>
    </>
  );
}
```

Reading `searchParams` is request-time data, so `FlightResults` is dynamic per request — but streaming means TTFB is the shell, not the 2s aggregator query ([[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense]]).

### 100k-product catalog: prerender the head, ISR the tail

An e-commerce site has 100k product pages. Building all of them makes deploys take an hour; rendering all dynamically wastes servers on pages that rarely change. Split by traffic:

```tsx
export async function generateStaticParams() {
  const top = await db.product.findMany({ orderBy: { views: "desc" }, take: 1000 });
  return top.map((p) => ({ id: p.id }));   // top sellers built at deploy
}
export const dynamicParams = true;          // long tail: rendered on first request, then cached
export const revalidate = 3600;             // ISR keeps both fresh within an hour
```

The mechanism: `generateStaticParams` seeds the Full Route Cache at build; `dynamicParams: true` lets unlisted ids render on first hit and join the cache — ISR semantics per page ([[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]).

> [!warning]
> `dynamicParams: false` would 404 the tail instead — the right call only when the param set is truly closed (e.g., locales), not an open catalog.

## 6. Interview Answer

Short answer:

> SSG builds HTML once at build time (fast, cheap, cacheable, but stale and impersonal); SSR renders per request (fresh, personalized, but a server render each time); ISR is static with timed/on-demand revalidation; streaming sends a fast shell then slow parts; PPR combines a static shell with dynamic holes on one page. You choose per route by freshness, personalization, and scale — and increasingly per *region* with PPR.

Deeper answer:

> In the App Router, Server Components render on the server by default and a route becomes dynamic only when it reads request-time data — cookies, headers, searchParams, or uncached fetches. In a Next 16 app that opts into Cache Components, PPR makes you annotate each region: `use cache` for cached/static parts in the prerendered shell, `<Suspense>` around runtime-API reads that stream at request time. The anti-pattern is a single request-time read at the top forcing the whole route dynamic and discarding the CDN-static win for content that's identical for everyone.

## 7. Practice

1. <details><summary>A docs site and a personalized dashboard — which strategy each, and why?</summary>Docs: SSG (or cached/PPR shell) — content is the same for everyone and changes rarely, so build once and serve from the CDN for near-zero TTFB and infinite scale; revalidate on content updates. Dashboard: SSR/dynamic — it's per-user and auth-gated, so it can't be statically cached; render per request (stream the slow widgets). The deciding factor is per-user personalization, not "which is newer tech."</details>

2. <details><summary>Why does calling `cookies()` at the top of a page component make the entire route dynamic, and how does PPR avoid it?</summary>`cookies()` is request-time data; anything that depends on it can't be known at build, so Next must render that component per request — and if it's the top component, the whole tree is dynamic. PPR avoids it by pushing the cookie read down into a child wrapped in `<Suspense>`, so only that subtree is dynamic/streamed while the rest is prerendered into the static shell. Isolate the dynamic dependency to isolate the dynamic cost.</details>

3. <details><summary>ISR vs SSR for a product catalog updated a few times a day. Argue the tradeoff.</summary>ISR: serve a cached static page, revalidate every N minutes or on-demand when the catalog changes — near-static performance and cost with bounded staleness (minutes), ideal since products change rarely. SSR: fresh on every request but a server render each time, wasteful for content that's identical between updates and slower TTFB. Choose ISR unless the data must be real-time-accurate per request (e.g., live inventory shown as a number), which you can still stream as a dynamic hole while the rest stays ISR.</details>

4. <details><summary>What does streaming buy over plain SSR, mechanically?</summary>Plain SSR waits for *all* data before sending any HTML — TTFB is gated by the slowest query. Streaming sends the shell (and Suspense fallbacks) immediately, then streams each boundary's real HTML as its data resolves, with selective hydration. The user sees meaningful content sooner and a slow widget can't hold the whole page hostage. Cost: slightly more complex response handling and the need to place Suspense boundaries thoughtfully.</details>

## Related Notes

- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]
- [[22 - Next.js Deep Dive/06 - Data Fetching Patterns|Data Fetching Patterns]]
- [[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense and Concurrent Features]]
- [[21 - React Internals and Patterns/10 - React 19|React 19 — Activity and Partial Pre-rendering]]
- [[01 - Roadmap|Roadmap]]
