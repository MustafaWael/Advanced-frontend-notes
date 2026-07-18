---
tags: [system-design, interview, rendering, ssr, performance]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [CSR SSR SSG ISR, rendering strategy decision, streaming SSR]
verified_on: 2026-07-17
version_scope: "Next.js App Router / RSC / ISR / Partial Prerendering as of 2026 (Next 16-era); recheck feature names against current docs"
---

# Rendering Strategies for Design

## Maturity Target

- Priority: #must-know
- Study time: 45 minutes
- Interview signal: In the Architecture phase of any app-level design, pick a rendering strategy per route from the requirements (SEO, TTFB, data freshness, interactivity) and defend it against the alternatives.
- Production signal: You choose CSR/SSR/SSG/ISR/streaming per route, not one mode for the whole app.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]

## Source Anchors

- [web.dev — Rendering on the Web](https://web.dev/articles/rendering-on-the-web)
- [Next.js — Rendering fundamentals](https://nextjs.org/docs/app/building-your-application/rendering)
- [Next.js — Partial Prerendering](https://nextjs.org/docs/app/getting-started/partial-prerendering)
- [React — Server Components](https://react.dev/reference/rsc/server-components)

## 1. Concept

Simple version: "where and when does the HTML get built?" The mechanics live in [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]; this note is the *design-round decision* — which strategy each route needs and why.

The options as a decision axis (build-time → request-time → client-time):

| Strategy                           | HTML built                                                                                      | Best when                                                                  | Cost                                           |
| ---------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------- |
| **SSG** (static)                   | build time                                                                                      | content stable, same for everyone (docs, marketing, blog)                  | rebuild to update; not per-user                |
| **ISR** (incremental static regen) | build + revalidate                                                                              | mostly-static at scale, tolerable staleness (product pages)                | staleness window; cache infra                  |
| **SSR** (server render)            | each request                                                                                    | per-request/personalized + SEO + fast first paint (feed, dashboard w/ SEO) | server cost per request; TTFB tied to data     |
| **CSR** (client render)            | in the browser                                                                                  | private, highly interactive, SEO-irrelevant (app behind login)             | blank first paint, JS-dependent, weak SEO      |
| **Streaming SSR**                  | request, in chunks                                                                              | SSR but data is slow — shell first, stream the rest                        | complexity; needs Suspense boundaries          |
| **RSC** (server components)        | server → serialized payload (server components ship *no* client JS; client components still do) | reduce client bundle; data-fetching components                             | newer model; server/client boundary discipline |

The decision inputs, straight from RADIO's Requirements phase: **SEO need**, **personalization** (same for all vs per-user), **data freshness** (static / stale-ok / must-be-fresh), **interactivity**, and **TTFB/perceived-load targets**. Streaming and RSC aren't a separate axis so much as a way to get SSR's SEO/first-paint benefits without paying full SSR latency or full client bundle.

> [!tip] Per-route, not per-app. A real app mixes them: marketing pages SSG, product pages ISR, the logged-in dashboard SSR (or CSR if no SEO), the checkout CSR-heavy. "I'd render each route by its requirements" is the answer that lands; "I'd use SSR for everything" is the reflexive one that ignores the tradeoffs.

## 2. Why It Matters

App-level design questions (e-commerce, news feed, dashboard) are half won or lost in the rendering decision — it drives SEO, first-paint, server cost, and the caching design downstream. Interviewers probe it because it forces you to connect a product requirement (SEO, freshness) to an architecture choice with a cost.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an e-commerce team ships the whole storefront as a CSR SPA. Product pages don't rank, and the largest-contentful paint is slow on mobile because the browser downloads, parses, and runs a big JS bundle before any product is visible.

Trace: CSR sends an empty shell + JS; crawlers and users both wait for the bundle and the client fetch before content exists — wrong strategy for public, SEO-critical, content-heavy pages ([[13 - Performance and Memory/10 - Core Web Vitals and Measuring|LCP]] suffers).

Fix by route: product listing/detail → **ISR** (static-fast, SEO-friendly, revalidated for price/stock changes); cart/checkout → **CSR/SSR** (private, interactive, SEO-irrelevant); marketing → **SSG**. Optionally **stream** the SSR pages so the product shell paints before slow recommendation modules.

Tradeoff: ISR introduces a staleness window (a price change may lag until revalidation — mitigate with on-demand revalidation or a client refetch for stock), and mixing strategies raises architectural complexity. You're trading a uniform-but-wrong model for a per-route-correct-but-varied one.

## 4. Interview Answer

Short answer:

> I choose a rendering strategy per route from the requirements — SEO need, personalization, data freshness, interactivity, and first-paint targets. Static (SSG) for stable shared content, ISR for mostly-static at scale with tolerable staleness, SSR for personalized-plus-SEO, CSR for private interactive app screens. Streaming SSR and Server Components are how I keep SSR's SEO and first-paint wins without full latency or a heavy client bundle.

Deeper answer:

> The load-bearing inputs are SEO and freshness, because they eliminate options fast: SEO-critical rules out pure CSR; must-be-fresh-per-user rules out plain SSG. Streaming matters when SSR's TTFB is hostage to a slow data source — I put the shell outside a Suspense boundary and stream the slow module in, so LCP isn't blocked by the slowest query. And I'd be explicit that this decision cascades: it sets where caching lives, whether I need a data layer on the client at all, and how much JS ships — so I make it early in the architecture phase and trace everything else to it.

## 5. Practice

1. <details><summary>A dashboard is behind login (no SEO) but shows per-user data that must be current. CSR or SSR — and what decides it?</summary>Either can work; the deciding factors are first-paint target and data location. If a fast first paint matters and data is server-close, SSR (or streaming SSR) renders meaningful content immediately. If the app is highly interactive and a brief skeleton is acceptable, CSR keeps the server stateless and simpler. SEO isn't a factor here, so it doesn't force SSR.</details>
2. <details><summary>Why is ISR a better fit than SSR for a large product catalog?</summary>Product pages are mostly static and shared across users, so re-rendering them on every request (SSR) wastes server work and ties TTFB to data. ISR serves a cached static page instantly and regenerates on an interval or on-demand when price/stock changes — near-static performance with bounded staleness, which is the right trade for catalog scale.</details>
3. <details><summary>What does streaming SSR buy you that plain SSR doesn't?</summary>Plain SSR waits for all data before sending any HTML, so TTFB is the slowest query. Streaming sends the shell (and fast content) immediately and streams slow sections inside Suspense boundaries as their data resolves — LCP and first paint stop being blocked by the slowest module, at the cost of boundary design.</details>

## 6. Real-World Use Cases

The decision table earns its keep only when you can wire each choice up. Three routes from one real app, each a different strategy.

### Marketing/blog pages — SSG at build time

Content is the same for everyone and changes rarely, so build it once. In the App Router, `generateStaticParams` enumerates the pages to prerender.

```tsx
// app/blog/[slug]/page.tsx
export async function generateStaticParams() {
  const posts = await getAllPosts();
  return posts.map(p => ({ slug: p.slug }));   // prerendered at build → served as static HTML
}
export default async function Post({ params }: { params: { slug: string } }) {
  const post = await getPost(params.slug);
  return <article dangerouslySetInnerHTML={{ __html: post.html }} />;
}
```

Static + SEO + instant first paint; the cost is a rebuild (or ISR) to publish changes. See [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]].

### Product page — ISR with on-demand revalidation

Mostly static at scale but must reflect a price/stock change quickly — serve cached HTML, revalidate on a timer, and bust it precisely when the data changes.

```tsx
// app/product/[id]/page.tsx
export const revalidate = 3600;              // background re-render at most hourly…

// …and immediately when a webhook says the product changed:
// app/api/revalidate/route.ts
import { revalidatePath } from "next/cache";
export async function POST(req: Request) {
  const { id } = await req.json();
  revalidatePath(`/product/${id}`);          // next request rebuilds this page
  return Response.json({ revalidated: true });
}
```

Staleness is bounded and controllable — the tradeoff is cache infrastructure and a small window. See [[29 - Frontend System Design/20 - Designing an E-commerce Product Page|Designing an E-commerce Product Page]].

### Dashboard — streaming SSR with Suspense

The shell and fast widgets should paint immediately while a slow analytics query streams in, instead of the whole page waiting on the slowest data.

```tsx
export default function Dashboard() {
  return (
    <>
      <Header />                               {/* flushed instantly */}
      <Suspense fallback={<ChartSkeleton />}>
        <RevenueChart />                       {/* streamed when its data resolves */}
      </Suspense>
    </>
  );
}
```

Streaming buys SSR's SEO/first-paint without blocking on the slowest boundary. See [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]].

## Related Notes

- [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]
- [[26 - How the Web Works/01 - From URL to Pixels|From URL to Pixels]]
- [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]]
- [[29 - Frontend System Design/20 - Designing an E-commerce Product Page|Designing an E-commerce Product Page]]
