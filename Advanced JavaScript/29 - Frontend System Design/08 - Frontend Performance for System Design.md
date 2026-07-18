---
tags: [system-design, interview, performance, core-web-vitals]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [Core Web Vitals design, INP LCP CLS, performance budget]
verified_on: 2026-07-17
version_scope: "Core Web Vitals as of 2026 (INP replaced FID March 2024)"
---

# Frontend Performance for System Design

## Maturity Target

- Priority: #must-know
- Study time: 50 minutes
- Interview signal: In the Optimizations phase, name the performance work ranked by user impact and mapped to a metric (LCP/INP/CLS), not a grab bag of tricks.
- Production signal: You optimize the measured bottleneck against a budget, not by reflex.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]

## Source Anchors

- [web.dev — Core Web Vitals](https://web.dev/articles/vitals)
- [web.dev — Optimize INP](https://web.dev/articles/optimize-inp)
- [web.dev — Optimize LCP](https://web.dev/articles/optimize-lcp)

## 1. Concept

Simple version: tie every optimization to a metric and a requirement, so "make it fast" becomes a ranked, defensible list. The three Core Web Vitals (2026, "good" at the 75th percentile of real users):

- **LCP — Largest Contentful Paint < 2.5s** (loading). Levers: rendering strategy ([[29 - Frontend System Design/05 - Rendering Strategies for Design|SSR/streaming/ISR]]), critical-request priority, image optimization, fewer render-blocking resources, CDN.
- **INP — Interaction to Next Paint < 200ms** (responsiveness). *Replaced FID in March 2024* and is stricter — it measures every interaction's latency, not just the first. Levers: break up long tasks, yield to the main thread, defer non-urgent work (`useTransition`), offload heavy compute to [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers]], reduce hydration/JS cost.
- **CLS — Cumulative Layout Shift < 0.1** (visual stability). Levers: reserve space for images/ads (`aspect-ratio`, width/height), avoid inserting content above existing content, size fonts to avoid FOUT jumps.

Cross-cutting design levers: **bundle discipline** (code-split by route, lazy-load below-the-fold and heavy widgets, tree-shake — [[27 - Frontend Tooling and Build Systems/05 - Production Build Concerns|Production Build Concerns]]), **virtualization** for large lists ([[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|large lists]]), **image strategy** (responsive `srcset`, modern formats, `loading="lazy"`, priority hints for the LCP image), and a **performance budget** (a number the design must stay under).

> [!tip] Rank by user impact, not cleverness. In practice that sounds like: "requirement is slow-network mobile, so the wins are LCP work — bundle size, image payload, render strategy — not micro-memoizing renders." State the ranking and the metric each item moves.

## 2. Why It Matters

The Optimizations phase carries a large share of a frontend design round, and the failure mode is an unranked pile of buzzwords ("I'd memoize, virtualize, debounce, lazy-load…"). Mapping each to LCP/INP/CLS and to the requirement turns it into a prioritized argument. Performance is also a real business metric (CWV affect SEO ranking and conversion), so it connects to product outcomes.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a dashboard feels sluggish. The team memoizes components everywhere; it barely helps. The real complaint is that clicking a filter freezes the UI for ~400ms.

Trace: wrong metric targeted. Memoization addresses render count, but the freeze is an **INP** problem — the click handler runs a synchronous heavy transform on the main thread, blocking paint. Long task → high INP, regardless of memoization.

```tsx
// Fix: keep the interaction responsive — mark the expensive update non-urgent
const [query, setQuery] = useState('');
const deferredQuery = useDeferredValue(query);        // urgent input, deferred filtering
// or push the heavy compute off the main thread entirely:
const results = useMemo(() => filterHeavy(rows, deferredQuery), [rows, deferredQuery]);
// for truly heavy work: run filterHeavy in a Web Worker and post results back
```

Tradeoff: deferring shows stale results for a frame or two (usually fine); a Web Worker removes the freeze entirely but adds serialization cost and complexity ([[31 - Low Level Design/05 - Concurrency Foundations|message passing]]). The point is you fixed the *measured* bottleneck (INP), not the one that was easy to reach for.

## 4. Interview Answer

Short answer:

> I rank performance work by user impact and tie each item to a Core Web Vital. LCP under 2.5s is loading — driven by rendering strategy, critical resources, and image payload. INP under 200ms is responsiveness — break up long tasks, defer non-urgent updates, offload heavy compute. CLS under 0.1 is stability — reserve space for media. Then cross-cutting: code-split, virtualize large lists, budget the bundle. I optimize the measured bottleneck, not by reflex.

Deeper answer:

> INP is the one people miss because it replaced FID and is stricter — it scores every interaction, so a single heavy handler tanks it. The fix is main-thread discipline: yield, use transitions to keep input urgent while deprioritizing the expensive update, and push genuinely heavy compute to a worker. I'd also insist on a budget — a concrete JS/image size the design must stay under — because "faster" without a number can't be graded, and I'd map the ranking to the requirement: slow-network mobile makes LCP and payload dominate, a data-heavy interactive tool makes INP dominate. Saying which one dominates, and why, is the whole answer.

## 5. Practice

1. <details><summary>Users report the page "jumps around while loading." Which metric, and the fix?</summary>CLS. Content without reserved space (images, ads, late-loading banners) pushes existing content down as it arrives. Fix: set explicit width/height or `aspect-ratio` on media, reserve space for dynamic slots, and avoid inserting content above what's already visible. Font swaps can also shift — size fallback fonts to match.</details>
2. <details><summary>Why can memoizing everything fail to fix a janky interaction?</summary>Memoization reduces re-renders, but jank on interaction is usually INP — a long synchronous task in the handler blocking the next paint. If the work itself is heavy, it runs regardless of how few components re-render. The fix is main-thread scheduling (yield, transitions) or offloading to a worker, not more memoization.</details>
3. <details><summary>How do you decide what to optimize first in a design round?</summary>From the requirement: identify the dominant constraint (slow network → LCP/payload; huge lists → rendering/virtualization; heavy interactivity → INP), map candidate optimizations to the metric each moves, and rank by user impact. Then state a budget so the choice is measurable. An unranked pile of optimizations is the weak answer.</details>

## 6. Real-World Use Cases

§3 shows the INP fix; here are the other two Vitals plus the bundle lever, so the "rank by metric" thesis is shown end to end.

### LCP — priority-hint the hero image

The largest above-the-fold image usually *is* the LCP element; let the browser fetch it early instead of discovering it late.

```tsx
import Image from "next/image";
<Image src={hero} alt="" priority sizes="100vw" /> // priority → fetchpriority=high, no lazy
```

Prioritizing the LCP resource is the single biggest lever on a hero page. See [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]].

### CLS — reserve space for late content

Images, ads, and embeds that arrive without reserved dimensions shove content down. Reserve the box up front.

```css
.media { aspect-ratio: 16 / 9; width: 100%; }   /* space held before the asset loads */
.ad-slot { min-height: 250px; }                 /* reserve even if the ad is slow/absent */
```

No reflow on load → no layout shift. See [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]].

### Bundle — route-level code splitting

A heavy, below-the-fold widget shouldn't sit in the initial bundle and delay interactivity. Split it out and load on demand.

```tsx
import dynamic from "next/dynamic";
const AnalyticsChart = dynamic(() => import("./AnalyticsChart"), {
  ssr: false, loading: () => <ChartSkeleton />,
});
// ships in its own chunk, fetched when rendered — smaller initial JS, faster TTI
```

Smaller initial JS helps both INP and load. See [[27 - Frontend Tooling and Build Systems/05 - Production Build Concerns|Production Build Concerns]].

## Related Notes

- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[29 - Frontend System Design/05 - Rendering Strategies for Design|Rendering Strategies for Design]]
- [[27 - Frontend Tooling and Build Systems/05 - Production Build Concerns|Production Build Concerns]]
- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]
