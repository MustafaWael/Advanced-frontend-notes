---
tags: [nextjs, performance, images, fonts]
module: "22 - Next.js Deep Dive"
priority: important
status: not-started
aliases: [next/image, next/font]
verified_on: 2026-07-12
version_scope: "Next.js 14–16"
---

# Asset Optimization

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain what `next/image` and `next/font` actually do — layout stability, lazy loading, format negotiation, zero-CLS fonts.
- Production signal: your images don't cause CLS or ship oversized, and fonts don't flash or shift.
- Dependencies: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals]], [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals]]

## Source Anchors

- [Next.js - Image Optimization](https://nextjs.org/docs/app/getting-started/images)
- [Next.js - next/image](https://nextjs.org/docs/app/api-reference/components/image)
- [Next.js - Font Optimization](https://nextjs.org/docs/app/getting-started/fonts)
- [web.dev - Optimize Cumulative Layout Shift](https://web.dev/articles/optimize-cls)
- [Next.js 16 upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-16)

> Version note — `next/image` changed in Next 16:
> - `priority` is **deprecated** in favor of `preload` (same intent — eager-load + preload the LCP image — clearer name). Next 14/15 code uses `priority`.
> - `images.minimumCacheTTL` default rose from 60 s to **4 hours** (fewer re-optimizations; lower CPU/cost; longer-lived cached variants).
> - `16` was removed from the default `images.imageSizes`.
> - Local image URLs with query strings now require an `images.localPatterns.search` allowlist, and optimization of local-IP sources is blocked by default (`images.dangerouslyAllowLocalIP` to override) — both SSRF/enumeration hardening.
> Examples below are labeled per version.

## 1. What next/image Actually Does

`next/image` is not just an `<img>` wrapper; it automates a bundle of image best-practices that are tedious and error-prone by hand:

- **Prevents layout shift (CLS)**: by requiring `width`/`height` (or `fill`), it reserves the correct space *before* the image loads, so content doesn't jump when it arrives — the [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|reflow]] that damages [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|CLS]].
- **Responsive sizing**: generates `srcset`/`sizes` so devices download an appropriately-sized image, not a 4000px hero on a phone.
- **Modern formats**: serves WebP/AVIF to browsers that support them (via content negotiation), often a large byte saving over JPEG/PNG.
- **Lazy loading** by default (offscreen images load as they approach the viewport — [[19 - DOM and Browser APIs/06 - Observers|IntersectionObserver]] semantics), with `preload` (Next 16; `priority` in 14/15) to eager-load the LCP image.
- **On-demand optimization**: resizing/reformatting happens at request time (or build) and is cached, so you ship one source image.

```tsx
import Image from "next/image";
// Next 16
<Image src="/hero.jpg" width={1200} height={630} preload alt="…" />    // LCP image: eager + preloaded
<Image src={product.image} width={300} height={300} alt={product.name} /> // lazy by default
// Next 14/15: the same eager-load prop was called `priority`
```

## 2. What next/font Actually Does

`next/font` solves font loading's two problems — layout shift and privacy/latency:

- **Zero layout shift**: it computes fallback font metrics and applies `size-adjust`/`ascent-override` so the fallback occupies the same space as the web font — when the real font swaps in, text doesn't reflow (the FOUT/CLS jump).
- **Self-hosting**: fonts (including Google Fonts) are downloaded at build and served from your origin — no request to a third party at runtime (faster, and removes a privacy/GDPR concern and a third-party point of failure).
- **Preloading** the font files so text renders in the right face quickly.

```tsx
import { Inter } from "next/font/google";
const inter = Inter({ subsets: ["latin"], display: "swap" });
// <body className={inter.className}>
```

> [!tip] These target specific Core Web Vitals
> `next/image` reserving space and `next/font` matching fallback metrics both attack **CLS** (visual stability); `preload`/`priority` on the hero image and font preloading attack **LCP** (loading speed). Knowing *which vital each optimization serves* is the senior framing — you optimize a measured metric, not "make it faster" vaguely ([[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals]]).

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a product grid janks — content jumps as images load, the hero appears late, and text reflows when the font loads. Lighthouse flags CLS and LCP.

Buggy version — raw tags:

```tsx
<img src={product.image} alt={product.name} />          {/* no dimensions → CLS jump */}
<img src="/hero-4000px.jpg" alt="Hero" />               {/* huge, not prioritized → slow LCP */}
// global CSS: font-family: 'Custom', sans-serif; loaded via <link> to Google Fonts
```

Trace: the browser doesn't know each image's size until it loads, so it reserves zero space → every image load shoves content down (CLS). The hero is a 4000px JPEG, lazy by nature of being an `<img>` with no priority, and is the LCP element → slow LCP. The web font loads late and has different metrics than the fallback → text reflows on swap (more CLS).

Production-safe fix:

```tsx
import Image from "next/image";
import { Inter } from "next/font/google";
const inter = Inter({ subsets: ["latin"], display: "swap" });

<Image src={product.image} width={300} height={300} alt={product.name} />   // reserves space, WebP, lazy
<Image src="/hero.jpg" width={1200} height={630} preload alt="Hero" />      // eager, right-sized, LCP (Next 16; `priority` in 14/15)
// <body className={inter.className}>  → self-hosted, metric-matched fallback, no reflow
```

Result: space is reserved (CLS ≈ 0), the hero loads eagerly at an appropriate size (better LCP), and font swap doesn't shift text.

Tradeoffs: `next/image` requires knowing dimensions (or `fill` + a sized container) — awkward for arbitrary user-generated images where you must derive/store dimensions or accept `fill`; and its on-demand optimization needs an image optimization backend (built-in on Vercel; self-hosting requires configuring a loader/`sharp` or an external service, with cost/ops implications). Remote images need `remotePatterns` allowlisting (an SSRF-conscious default). For truly simple cases (a fixed decorative SVG, an already-optimized icon) a plain `<img>` is fine — don't reach for `next/image` reflexively when there's nothing to optimize. `next/font` similarly adds a small build step and only supports fonts it can fetch/self-host.

## 4. Interview Answer

Short answer:

> `next/image` prevents layout shift by reserving space from required dimensions, serves responsive `srcset` and modern formats (WebP/AVIF), lazy-loads by default with `preload` (Next 16; formerly `priority`) for the LCP image, and optimizes on demand — so you ship one source image. `next/font` self-hosts fonts, preloads them, and matches fallback metrics so text doesn't reflow when the web font swaps in. Both primarily target CLS and LCP.

Deeper answer:

> The mechanisms map to specific Core Web Vitals: dimension-based space reservation and metric-matched font fallbacks fix CLS; `priority` and font preloading fix LCP; format negotiation and responsive sizing cut bytes. Tradeoffs: `next/image` needs known dimensions (or `fill`), a remote-pattern allowlist, and an optimization backend that's turnkey on Vercel but requires a loader/`sharp` when self-hosting; user-generated images need stored dimensions. Plain `<img>`/CSS remain fine for already-optimized or trivial assets — the point is to optimize measured metrics, not apply the components reflexively.

## 5. Practice

1. <details><summary>How does `next/image` requiring width and height improve a Core Web Vital, and which one?</summary>CLS (Cumulative Layout Shift). With explicit dimensions (or `fill` in a sized container), the browser reserves the correct box before the image bytes arrive, so surrounding content doesn't jump when the image loads. A raw `<img>` without dimensions reserves no space, so each load shifts layout — the exact behavior CLS penalizes. It's the reflow/space-reservation idea from the render pipeline applied to images.</details>

2. <details><summary>Your hero image is the LCP element and loads slowly. Two next/image levers.</summary>(1) Add `preload` (Next 16; `priority` in 14/15) so it's eagerly loaded and preloaded instead of lazy — the LCP image should never be lazy-loaded. (2) Ensure it's appropriately sized/responsive (correct `width`/`height` and `sizes`) so devices download a right-sized, modern-format (WebP/AVIF) version rather than an oversized original. Together they cut the LCP element's load time.</details>

3. <details><summary>Why does self-hosting fonts via next/font help both performance and privacy?</summary>Performance: no runtime request to a third-party font host (extra DNS/connection/round trip removed), fonts served from your origin and preloaded, plus metric-matched fallbacks preventing reflow. Privacy: the user's browser never contacts Google's font servers at runtime, removing a third-party data exposure (a GDPR concern in the EU) and a third-party availability/failure dependency. The fonts are fetched once at build and bundled.</details>

4. <details><summary>When is a plain `<img>` the right choice over next/image?</summary>When there's nothing to optimize or the constraints don't fit: a small already-optimized SVG/icon, a decorative image where format/size is already ideal, or environments where you can't run the optimization backend and the overhead isn't justified. `next/image` shines for content photos (responsive sizing, format negotiation, CLS/LCP wins); forcing it onto trivial assets adds config (dimensions, remote patterns, loader) for no benefit. Optimize where there's measured cost.</details>

## Related Notes

- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]
- [[19 - DOM and Browser APIs/06 - Observers|Observers]]
- [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]
- [[01 - Roadmap|Roadmap]]
