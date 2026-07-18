---
tags: [performance, web-vitals, measurement]
module: "13 - Performance and Memory"
priority: must-know
status: not-started
aliases: [Core Web Vitals, LCP, INP, CLS]
---

# Core Web Vitals and Measuring

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can define LCP, INP, and CLS, name what worsens each, and measure them with `PerformanceObserver` and field vs lab tools.
- Production signal: you diagnose a slow page with real metrics and connect the cause back to the event loop and render pipeline instead of guessing.
- Dependencies: [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]], [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]

## Source Anchors

- [web.dev - Web Vitals](https://web.dev/articles/vitals)
- [web.dev - Interaction to Next Paint (INP)](https://web.dev/articles/inp)
- [web.dev - Optimize Cumulative Layout Shift](https://web.dev/articles/optimize-cls)
- [MDN - PerformanceObserver](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceObserver)
- [web.dev - Largest Contentful Paint (LCP)](https://web.dev/articles/lcp)

## 1. The Three Core Web Vitals

Google's Core Web Vitals quantify user experience into three metrics, each with a "good" threshold (at the 75th percentile of real users):

| Metric | Measures | Good | Worsened by |
| --- | --- | --- | --- |
| **LCP** (Largest Contentful Paint) | Loading — when the biggest content element paints | ≤ 2.5s | Slow server/TTFB, render-blocking CSS/JS, unoptimized hero images, late-discovered resources |
| **INP** (Interaction to Next Paint) | Responsiveness — worst input→paint delay across the visit | ≤ 200ms | Long tasks blocking the main thread, heavy event handlers, expensive re-renders |
| **CLS** (Cumulative Layout Shift) | Visual stability — how much layout jumps unexpectedly | ≤ 0.1 | Images without dimensions, injected content, web-font swaps, ads/embeds |

INP replaced FID (First Input Delay) as a Core Web Vital in 2024 — a stricter metric measuring the *full* interaction latency (input to the next paint), not just the initial delay.

## 2. Why It Matters

- CWV are a Google ranking factor and a direct proxy for user-perceived quality — they're the shared vocabulary between engineering and the business.
- Each vital traces to a mechanism you already know: LCP to resource loading and the [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|render pipeline]], INP to [[09 - Event Loop Advanced/01 - Event Loop Overview|long tasks on the event loop]], CLS to [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|reflow]]. Being able to connect metric → mechanism → fix is the senior skill.

## 3. INP and the Event Loop

INP is where JavaScript performance shows up as UX. An interaction (click, tap, keypress) can't paint its result until the main thread is free to run the handler and the subsequent render. If a **long task** (>50ms of uninterrupted main-thread work — [[13 - Performance and Memory/06 - Memoization and Expensive Computations|expensive computation]], a giant re-render, a synchronous parse) is running or queued, the interaction waits behind it. High INP almost always means "the main thread was busy."

Fixes map directly: break long tasks into chunks that yield ([[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|chunking]]), move CPU work to a [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|worker]], reduce re-render cost with memoization or [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|transitions]], and defer non-urgent work with `requestIdleCallback`/`scheduler.yield`.

## 4. Measuring: Field vs Lab

- **Field data (RUM)**: real users, real devices/networks — the ground truth Google ranks on. Collected via the `web-vitals` library or `PerformanceObserver`, sent to your analytics. Chrome UX Report (CrUX) aggregates it.
- **Lab data**: a controlled synthetic run — Lighthouse, DevTools Performance panel. Reproducible and great for debugging, but one machine/network ≠ your user distribution (and Lighthouse can't measure INP, which needs real interactions).

Use both: lab to *debug* a specific problem, field to *know what real users experience* and catch regressions.

```js
// Measuring with PerformanceObserver directly (what web-vitals wraps)
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    // LCP: the largest-contentful-paint entry's startTime
    console.log(entry.name, entry.startTime, entry);
  }
}).observe({ type: "largest-contentful-paint", buffered: true });

new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (entry.duration > 50) reportLongTask(entry);   // long tasks → INP culprits
  }
}).observe({ type: "longtask", buffered: true });
```

> [!tip] In practice, use the web-vitals library
> Hand-rolling correct LCP/INP/CLS measurement (handling bfcache, multiple interactions, final values on page hide) is subtle. Google's `web-vitals` library gives you `onLCP`, `onINP`, `onCLS` callbacks that get the attribution right; send those to your analytics for field monitoring. Know `PerformanceObserver` for the mechanism; use the library in production.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a dashboard scores poorly — LCP 4.5s, INP 400ms, CLS 0.3.

Buggy version:

```jsx
function Dashboard() {
  const [data, setData] = useState(null);
  useEffect(() => { fetch("/api/all").then(r => r.json()).then(setData); }, []);
  if (!data) return null;                     // blank until everything loads → late LCP
  return (
    <>
      <img src="/hero-4mb.jpg" />             {/* no dimensions → CLS; huge → LCP */}
      <SearchBox onChange={q => setResults(expensiveFilter(data, q))} /> {/* long task → INP */}
      <BigTable rows={data.rows} />
    </>
  );
}
```

Trace each vital: the whole page waits on one `/api/all` fetch and renders nothing until then (LCP gated by the slowest data + a 4MB unsized hero); the hero has no dimensions, so when it loads it shoves content down (CLS); each keystroke runs `expensiveFilter` synchronously, a long task that delays the paint of the typed character (INP).

Production-safe fix:

```jsx
function Dashboard() {
  return (
    <>
      <Image src="/hero.jpg" width={1200} height={400} priority />  {/* sized + eager → LCP/CLS */}
      <Suspense fallback={<TableSkeleton />}>                        {/* stream, don't block LCP */}
        <DataTable />
      </Suspense>
      <Search />   {/* deferred value / worker for the filter → INP */}
    </>
  );
}
```

Fixes mapped: sized priority image and streaming shell improve LCP and eliminate the hero's CLS; deferring/off-threading the filter frees the main thread for INP. Each change targets a *measured* metric.

Tradeoffs: optimizing one vital can trade against another and against effort. Eager-loading everything for LCP hurts bandwidth and can starve other resources; over-splitting Suspense boundaries adds skeleton popcorn; a worker for filtering adds complexity you should only pay if INP is actually the bottleneck. The discipline is *measure first (field data), fix the worst metric, re-measure* — not blanket "performance tips." Premature optimization of a vital that's already green wastes effort.

## Real-World Use Cases

### Shipping RUM: vitals to your analytics with `sendBeacon`

Field data only exists if you collect it. Metrics finalize when the page is hidden or unloaded — exactly when normal `fetch` calls get dropped — so the report goes out via `navigator.sendBeacon`.

```ts
import { onLCP, onINP, onCLS, type Metric } from "web-vitals/attribution";

function report(metric: Metric) {
  navigator.sendBeacon(
    "/api/vitals",
    JSON.stringify({
      name: metric.name,
      value: metric.value,
      target: (metric as any).attribution?.interactionTarget, // which element was slow
      page: location.pathname,
    })
  );
}

onLCP(report);
onINP(report);
onCLS(report);
```

Works because `sendBeacon` is queued by the browser and survives page dismissal, and the attribution build names the DOM node behind a bad INP — turning "INP is 400ms" into "the Add to Cart handler is 400ms".

> [!tip]
> Segment vitals by route and device class in your analytics. A p75 INP that looks fine overall often hides one catastrophic page on low-end Android.

### Cookie-consent banner tanking CLS

Legal requires a consent banner; it mounts after hydration at the top of the page and shoves all content down — CLS jumps from 0.02 to 0.25 with zero JS performance change.

```css
/* Fix: overlay instead of participating in layout */
.consent-banner {
  position: fixed;
  inset-inline: 0;
  bottom: 0;
}
```

Works because CLS only counts movement of *existing* content — a `fixed`-position element (or a slot with reserved `min-height`) inserts without displacing anything. Same principle as unsized images and ad slots: reserve or overlay before the content arrives. See [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]].

### Lighthouse CI as a per-PR performance budget

A refactor quietly adds a render-blocking script; nobody notices until CrUX updates a month later. A lab budget in CI catches the regression at review time.

```json
// lighthouserc.json
{
  "ci": {
    "assert": {
      "assertions": {
        "largest-contentful-paint": ["error", { "maxNumericValue": 2500 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }],
        "total-blocking-time": ["error", { "maxNumericValue": 300 }]
      }
    }
  }
}
```

Works because lab runs are reproducible, so a threshold is meaningful PR-to-PR. Note the INP gap: Lighthouse cannot measure it (no real interactions), so the budget uses Total Blocking Time as the lab proxy while field RUM remains the INP backstop — the field-vs-lab split from section 4 made operational.

## 6. Interview Answer

Short answer:

> Core Web Vitals are LCP (loading — largest element paints, good ≤2.5s), INP (responsiveness — worst interaction-to-paint, good ≤200ms, replaced FID in 2024), and CLS (visual stability — unexpected layout shift, good ≤0.1). Each maps to a mechanism: LCP to resource loading and rendering, INP to long tasks on the main thread, CLS to reflow from unsized images/font swaps/injected content.

Deeper answer:

> Measure with field data (real users via the web-vitals library / PerformanceObserver, aggregated in CrUX — the ground truth Google ranks on) and lab data (Lighthouse/DevTools for reproducible debugging, though lab can't measure INP). INP is where JS perf surfaces: a long task blocks the interaction's paint, so fixes are chunking with yields, workers, cheaper re-renders, and transitions. The workflow is measure-worst-metric, fix, re-measure — optimizing a green vital is wasted effort, and vitals can trade off against each other.

## 7. Practice

1. <details><summary>A page feels laggy when users type, but loads fast. Which vital, and where do you look first?</summary>INP (responsiveness) — loading is fine but interactions are slow. Look at the main thread: long tasks (>50ms) during/after the keystroke, blocking the handler and its paint. Common culprits: synchronous filtering/sorting on each keystroke, expensive re-renders, heavy layout reads. Profile in DevTools Performance, find the long task, then chunk it, memoize it, defer it (transition/deferred value), or move it to a worker.</details>

2. <details><summary>Why did Google replace FID with INP, and what does that change about what you optimize?</summary>FID measured only the *initial* input delay (time until the handler starts) on the *first* interaction — it missed slow processing and slow rendering, and later interactions. INP measures the full interaction latency (input → next paint) across the whole visit and reports (near) the worst. So you can no longer pass by just making the first interaction cheap; every interaction's total cost — handler + re-render + paint — matters, which pushes you to fix long tasks and expensive renders throughout the session.</details>

3. <details><summary>Field data shows good CLS but lab (Lighthouse) shows poor CLS, or vice versa. Why can they disagree?</summary>Lab is one machine/network/viewport with no real user interaction, so it can miss shifts caused by real behavior (late-loading personalized content, interaction-triggered layout) or over-report shifts users never hit. Field data reflects the actual distribution of devices, networks, and interactions. They measure different things: lab for reproducible debugging, field for real experience. Trust field for ranking/reality; use lab to reproduce and fix a specific cause.</details>

4. <details><summary>List three distinct causes of CLS and the fix for each.</summary>(1) Images without dimensions → set width/height (or use `next/image`) so space is reserved before load. (2) Web-font swap with different metrics → preload and match fallback metrics (`next/font`, `size-adjust`) so text doesn't reflow on swap. (3) Content injected above existing content (ads, banners, async data) → reserve space with a min-height placeholder or insert below the fold. All three are the same principle: reserve the correct layout space before the content arrives so nothing shifts.</details>

## Related Notes

- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]
- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]
- [[22 - Next.js Deep Dive/08 - Asset Optimization|Asset Optimization]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[01 - Roadmap|Roadmap]]
