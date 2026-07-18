---
tags: [nextjs, moc]
module: "22 - Next.js Deep Dive"
priority: must-know
status: not-started
---

# Next.js Deep Dive MOC

This module goes deep on the App Router: rendering strategies (SSR/SSG/ISR/streaming/PPR), the four caching layers and revalidation that cause most "why is my data stale" bugs, Server Actions and their security model, route handlers and proxy (Next 16's replacement for middleware), data-fetching patterns, metadata/SEO, and asset optimization. It extends the two Next.js notes in folder 14 — it links to them rather than repeating them. After this module, you can architect a Next.js app deliberately: choosing per-route rendering, invalidating exactly the right cache, and treating server code as the untrusted boundary it is.

## Prerequisites

- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]] — the server/client boundary this module builds on.
- [[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense and Concurrent Features]] — streaming and PPR depend on it.
- [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]] — the Next cache layers mirror these concepts.

## Reading Order

1. [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]] — SSR, SSG, ISR, streaming, PPR decision framework.
2. [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]] — the four caches and stale-data diagnosis.
3. [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]] — time-based vs on-demand, tag vs path.
4. [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]] — mechanics, serialization, security, progressive enhancement.
5. [[22 - Next.js Deep Dive/05 - Route Handlers and Middleware|Route Handlers and Middleware]] — endpoints, cross-cutting logic, Edge vs Node.
6. [[22 - Next.js Deep Dive/06 - Data Fetching Patterns|Data Fetching Patterns]] — waterfalls, parallelism, memoization.
7. [[22 - Next.js Deep Dive/07 - Metadata SEO and the head|Metadata, SEO and the head]] — server-rendered metadata and why it matters.
8. [[22 - Next.js Deep Dive/08 - Asset Optimization|Asset Optimization]] — next/image and next/font, mapped to Core Web Vitals.
9. [[22 - Next.js Deep Dive/09 - Next.js Deep Dive Checklist|Next.js Deep Dive Checklist]] — active self-test.

## You're Done When

- [ ] I can choose a rendering strategy per route (and per region with PPR) from requirements.
- [ ] I can name the four caching layers and diagnose stale data by layer.
- [ ] I can invalidate exactly the right cache after a mutation with tags or paths.
- [ ] I can explain the Server Action security model and secure one properly.
- [ ] I can choose Route Handler vs Server Action vs Server Component and place proxy/middleware logic correctly.
- [ ] I can eliminate request waterfalls and dedupe reads.
- [ ] I can generate correct server-side metadata and explain its SEO importance.
- [ ] I can explain what next/image and next/font do and which Core Web Vitals they target.

## Related Notes

- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]
- [[21 - React Internals and Patterns/00 - React Internals and Patterns MOC|React Internals and Patterns MOC]]
- [[20 - Network and Security/00 - Network and Security MOC|Network and Security MOC]]
- [[01 - Roadmap|Roadmap]]
