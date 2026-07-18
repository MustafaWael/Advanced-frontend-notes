---
tags: [nextjs, checklist]
module: "22 - Next.js Deep Dive"
priority: must-know
status: not-started
---

# Next.js Deep Dive Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, predict, debug, and refactor without looking.

## Source Anchors

- [Next.js - App Router docs](https://nextjs.org/docs/app)
- [Next.js - Caching](https://nextjs.org/docs/app/getting-started/caching)
- [React - Server Components](https://react.dev/reference/rsc/server-components)
- [web.dev - Core Web Vitals](https://web.dev/articles/vitals)

## Rendering Strategies

- [ ] I can define SSG, SSR, ISR, streaming, and PPR and pick one from requirements.
- [ ] I can explain why reading a runtime API makes a route dynamic.
- [ ] I can explain PPR: static shell + dynamic holes, and how to annotate each region.
- [ ] I can isolate a dynamic dependency so it doesn't force the whole route dynamic.

## Caching Layers

- [ ] I can name the four layers and what each caches and where.
- [ ] I can diagnose "stale data" by identifying which layer holds the old value.
- [ ] I can explain the Next 14 → 15 default flip for fetch and GET route handlers.
- [ ] I can explain Request Memoization and React `cache()`.

## Revalidation

- [ ] I can compare time-based vs on-demand revalidation and choose per data.
- [ ] I can choose `revalidateTag` vs `revalidatePath` and defend it.
- [ ] I can explain the Next 16 contract differences: `updateTag` (read-your-writes) vs `revalidateTag(tag, "max")` (SWR) vs `refresh()` (client router only, no cache invalidation) — and that single-argument `revalidateTag` is deprecated.
- [ ] I can design a tag taxonomy that avoids staleness and over-invalidation.

## Server Actions

- [ ] I can explain the serialization boundary (data crosses, behavior doesn't).
- [ ] I can explain that actions are public endpoints needing authN, authZ, and validation.
- [ ] I can explain progressive enhancement of form actions.
- [ ] I can identify the "admin-only UI" privilege-escalation vulnerability.

## Route Handlers and Proxy

- [ ] I can choose Route Handler vs Server Action vs Server Component per need.
- [ ] I can explain what proxy (`proxy.ts`, Next 16, Node runtime) is for, why it must stay thin, and that `middleware.ts` is the deprecated ≤15 convention (Edge runtime).
- [ ] I can explain Edge vs Node runtime constraints and common Edge crashes.
- [ ] I can explain why proxy/middleware auth needs defense-in-depth at the data layer.

## Data Fetching

- [ ] I can spot an accidental waterfall and fix it with Promise.all or sibling components.
- [ ] I can distinguish a legitimate dependency waterfall from an accidental one.
- [ ] I can use the preload pattern and React `cache()` to dedupe.
- [ ] I can choose Promise.all vs allSettled for partial rendering.

## Metadata and SEO

- [ ] I can use static `metadata` and dynamic `generateMetadata`.
- [ ] I can explain why client-side metadata fails for crawlers and social scrapers.
- [ ] I can explain how streaming keeps metadata complete.
- [ ] I can name SEO fundamentals beyond metadata (status codes, semantic HTML, CWV).

## Asset Optimization

- [ ] I can explain what `next/image` does: CLS prevention, responsive, formats, lazy, eager-load via `preload` (Next 16; `priority` in 14/15).
- [ ] I can explain what `next/font` does: self-hosting, preload, metric-matched fallback.
- [ ] I can map each optimization to the Core Web Vital it targets.
- [ ] I can say when a plain `<img>` is the right choice.

## Exit Test

- [ ] Design the rendering strategy for a product page with a per-user strip and defend each region.
- [ ] Debug "my mutation doesn't show up" through all four cache layers to a `revalidateTag` fix.
- [ ] Identify and fix a privilege-escalation hole in a Server Action.
- [ ] Turn a 1.2s waterfall dashboard into a ~400ms parallel + streamed one.
- [ ] Explain to a stakeholder why the SPA doesn't rank and how SSR metadata fixes it.

## Related Notes

- [[22 - Next.js Deep Dive/00 - Next.js Deep Dive MOC|Next.js Deep Dive MOC]]
- [[21 - React Internals and Patterns/13 - React Internals Checklist|React Internals Checklist]]
- [[14 - JavaScript in React and Next.js/11 - React and Next Checklist|React and Next Checklist]]
- [[01 - Roadmap|Roadmap]]
