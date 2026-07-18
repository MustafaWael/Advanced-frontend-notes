---
tags: [javascript, dom, performance, observers]
module: "19 - DOM and Browser APIs"
priority: must-know
status: not-started
aliases: [IntersectionObserver, ResizeObserver, MutationObserver]
---

# Observers

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can explain *why* IntersectionObserver replaced scroll-handler math, when each observer's callbacks run relative to rendering, and the ResizeObserver loop error.
- Production signal: lazy loading, infinite scroll, and "element visible" analytics in your apps use observers with correct cleanup, not scroll listeners.
- Dependencies: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## Source Anchors

- [MDN - Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)
- [MDN - ResizeObserver](https://developer.mozilla.org/en-US/docs/Web/API/ResizeObserver)
- [MDN - MutationObserver](https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver)
- [Intersection Observer spec](https://www.w3.org/TR/intersection-observer/)
- [web.dev - Lazy loading images](https://web.dev/articles/lazy-loading-images)

## 1. Concept

Observers invert the old pattern of "poll or listen to high-frequency events, then measure". You declare *what* you want to know; the browser tells you *when it changes*, batching notifications at rendering-friendly times:

- **IntersectionObserver** — "is this element visible relative to a root (viewport or scrollable ancestor)?" Async, off the hot scroll path.
- **ResizeObserver** — "did this element's box change size?" Fires after layout, before paint.
- **MutationObserver** — "did the DOM under this node change (children, attributes, text)?" Fires as a microtask with batched records.

## 2. Why It Matters

The pre-observer version of lazy loading was a `scroll` listener calling `getBoundingClientRect()` per element per scroll event — high-frequency forced layout reads on the most latency-sensitive interaction ([[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|layout thrashing]]). IntersectionObserver moved that computation into the browser's own rendering pipeline where the geometry is already known. This is the canonical example of "use the platform" in performance interviews.

## 3. IntersectionObserver, Precisely

```js
const io = new IntersectionObserver(
  (entries, observer) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const img = entry.target;
      img.src = img.dataset.src;          // start the real load
      observer.unobserve(img);            // one-shot: stop watching
    }
  },
  {
    root: null,            // null = viewport
    rootMargin: "200px 0px", // grow the detection box: preload before visible
    threshold: 0            // fire as soon as 1 pixel intersects
  }
);

document.querySelectorAll("img[data-src]").forEach((img) => io.observe(img));
```

Mechanics worth knowing cold:

- Callbacks are **asynchronous** — delivered around rendering steps, not synchronously during scroll. You trade immediacy for cheapness.
- On `observe()`, an initial entry is always delivered reporting the current state — even if not intersecting. Guard with `isIntersecting` instead of assuming "callback = visible".
- `threshold: [0, 0.5, 1]` fires at multiple visibility ratios; `entry.intersectionRatio` tells you which crossing happened.
- `rootMargin` requires the shorthand-like CSS margin string and works only on ancestors that are actual scroll containers when `root` is set.
- One observer instance can watch thousands of elements — create one per *behavior*, not one per element.

Uses: lazy images/components, infinite scroll sentinels, "seen" analytics, pausing videos offscreen, sticky-header state.

## 4. ResizeObserver and MutationObserver

**ResizeObserver** solves "element queries": react to the *element's* size, not the window's. It reports `contentBoxSize`/`borderBoxSize` and fires after layout but before paint, so you can adjust without visible flicker.

> [!warning] "ResizeObserver loop completed with undelivered notifications"
> If your callback changes an observed element's size, the browser breaks the potential infinite loop by deferring re-notification to the next frame and firing this error event. It's usually benign noise (and famously spams error trackers), but recurring floods mean your handler resizes what it observes — restructure so the observed element and the mutated element differ, or write via `requestAnimationFrame`. In new code, prefer CSS container queries when the reaction is pure styling.

**MutationObserver** watches DOM tree changes — the replacement for long-removed mutation events. Callback runs as a **microtask** after the mutating task finishes, with all records batched (mutating 100 nodes in one loop = one callback with 100 records). Uses: integrating third-party scripts you don't control, watching for a widget to mount, editors tracking contenteditable. It observes *DOM* changes only — not style-driven size changes (that's ResizeObserver) and not visibility (IntersectionObserver).

## 5. Real Frontend Example: Bug → Fix → Tradeoff (Infinite Scroll)

Buggy version — scroll math:

```js
window.addEventListener("scroll", () => {
  const nearBottom =
    window.innerHeight + window.scrollY >= document.body.offsetHeight - 300;
  if (nearBottom) loadNextPage();
});
```

Traced failure modes:

1. `offsetHeight` read on every scroll event → forced layout on the hottest path.
2. No in-flight guard: crossing the threshold fires dozens of scroll events → `loadNextPage()` called repeatedly → duplicate pages, race conditions ([[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]).
3. Doesn't work when the list scrolls inside a container instead of the window.
4. Listener never removed on route change → leak ([[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]).

Production-safe fix — sentinel + observer + in-flight guard:

```js
function setupInfiniteScroll(listEl, loadNextPage) {
  const sentinel = document.createElement("div");
  listEl.append(sentinel);

  let loading = false;
  const io = new IntersectionObserver(
    async ([entry]) => {
      if (!entry.isIntersecting || loading) return;
      loading = true;
      try {
        const hasMore = await loadNextPage();
        if (!hasMore) io.disconnect();
        else listEl.append(sentinel); // keep sentinel last
      } finally {
        loading = false;
      }
    },
    { root: null, rootMargin: "400px 0px" }
  );

  io.observe(sentinel);
  return () => io.disconnect(); // cleanup for the route/component
}
```

Trace: sentinel enters the (400px-extended) viewport → browser delivers an entry at the next rendering opportunity → guard blocks re-entry while a page is in flight → new items push sentinel down → repeat. Cleanup is one `disconnect()`.

Tradeoff: observer delivery is async — with `rootMargin: 0` and fast flick-scrolling, users can briefly hit the bottom before content loads; tune `rootMargin` (prefetch distance) against wasted requests. The sentinel is an extra DOM node contract that virtualized lists (react-window etc.) handle differently — don't mix both mechanisms blindly.

## 6. React Integration Sketch

Observers are imperative and live outside React's render cycle — the standard shape is an effect with cleanup:

```jsx
function useOnScreen(ref, rootMargin = "0px") {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => setVisible(entry.isIntersecting),
      { rootMargin }
    );
    io.observe(el);
    return () => io.disconnect();   // cleanup or leak
  }, [ref, rootMargin]);
  return visible;
}
```

Note the classic trap this dodges: reading `ref.current` inside the effect (not during render), and disconnecting in cleanup so Strict Mode's double-invoke doesn't stack observers.

## Real-World Use Cases

### Scrollspy: highlighting the active section in docs nav

A documentation site highlights the sidebar link for the section currently being read. The pre-observer version read `getBoundingClientRect()` for every heading on every scroll event; one observer with a narrowed detection band replaces all of it.

```js
const spy = new IntersectionObserver(
  (entries) => {
    for (const entry of entries) {
      const link = navFor(entry.target.id);
      link.classList.toggle("active", entry.isIntersecting);
    }
  },
  // Shrink the root box to a band near the top: "active" = heading in reading position
  { rootMargin: "-10% 0px -80% 0px" }
);
document.querySelectorAll("article h2[id]").forEach((h) => spy.observe(h));
```

Works because *negative* `rootMargin` shrinks the intersection root — the observer fires only when a heading crosses the reading band, with zero JavaScript on the scroll path ([[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]).

### Responsive canvas chart sized by its container

A dashboard chart must resize when the sidebar collapses or its grid cell changes — cases a `window.resize` listener never sees. ResizeObserver reacts to the *element's* box, whatever caused it.

```js
const ro = new ResizeObserver(([entry]) => {
  const { inlineSize: w, blockSize: h } = entry.contentBoxSize[0];
  requestAnimationFrame(() => {           // write next frame: dodge the loop error
    canvas.width = w * devicePixelRatio;  // canvas is inside the observed container,
    canvas.height = h * devicePixelRatio; // not the observed element itself
    redrawChart(canvas);
  });
});
ro.observe(chartContainer);
```

Works because ResizeObserver fires after layout with the new box already computed — no measuring. Observing the container while mutating only the inner canvas is the structural fix for the "loop completed with undelivered notifications" error from section 4.

### Auto-scrolling chat pinned to the newest message

A support chat must scroll to the bottom when new messages arrive — but the rendering is done by a third-party SDK, so there is no callback to hook. MutationObserver watches the message list instead.

```js
let pinned = true;
list.addEventListener("scroll", () => {
  pinned = list.scrollTop + list.clientHeight >= list.scrollHeight - 40;
}, { passive: true });

const mo = new MutationObserver(() => {
  if (pinned) list.scrollTop = list.scrollHeight; // don't yank users reading history
});
mo.observe(list, { childList: true });
```

Works because MutationObserver delivers batched records as a microtask right after the SDK's inserting task — a burst of 20 appended messages triggers *one* callback and one scroll write, not 20 ([[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]).

> [!warning]
> All three observers retain their targets until `disconnect()`. In an SPA, an observer created per route/component without cleanup is a memory leak with a scroll listener's lifespan — see [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]].

## 7. Interview Answer

Short answer:

> Observers replace polling and high-frequency event math: IntersectionObserver for visibility (lazy loading, infinite scroll), ResizeObserver for element size, MutationObserver for DOM changes. The browser batches notifications at rendering-friendly times, so you avoid forced layouts in scroll handlers.

Deeper answer:

> IntersectionObserver callbacks are async and include an initial entry on observe, so you guard with `isIntersecting`; one instance watches many targets. ResizeObserver fires between layout and paint, and resizing an observed element from its own callback triggers the loop-limit error. MutationObserver delivers batched records as a microtask. All three need explicit `disconnect` in SPA lifecycles or they retain their targets.

## 8. Practice

1. <details><summary>Your "impression" analytics fires for products that were never on screen. The callback does `trackImpression(entry.target)` unconditionally. Why?</summary>IntersectionObserver delivers an initial entry for every observed element describing its *current* state — including "not intersecting". The callback fires on observe, not only on becoming visible. Fix: `if (!entry.isIntersecting) return;` and typically `unobserve` after the first genuine impression (plus a dwell-time threshold via `setTimeout` if "seen" means >1s).</details>

2. <details><summary>Why is IntersectionObserver cheaper than a scroll listener + getBoundingClientRect, mechanically?</summary>The scroll listener runs JavaScript on every scroll event and `getBoundingClientRect` can force synchronous layout while layout is dirty. The observer computes intersections inside the browser's rendering pipeline, where up-to-date geometry already exists, and delivers batched results asynchronously — zero JS on the scroll fast path, no forced layouts.</details>

3. <details><summary>A chart library resizes its canvas inside a ResizeObserver callback watching the same container, and Sentry fills with "loop completed with undelivered notifications". Benign or bug? Fix?</summary>It signals the callback's writes re-trigger the observation within one frame; the browser defers to the next frame and emits the error. Often visually benign (one-frame lag) but it can loop forever burning frames. Fix: observe the *container*, resize only the inner canvas (not observed); or debounce writes into `requestAnimationFrame`; or use CSS (aspect-ratio/container queries) so no JS resize is needed.</details>

4. <details><summary>You must run code when a third-party script finally injects `#chat-widget` into the page. Compare polling vs MutationObserver.</summary>Polling (`setInterval` + `querySelector`) wastes work, adds latency up to the interval, and needs manual teardown. MutationObserver on `document.body` with `{ childList: true, subtree: true }` fires as a microtask right after the insertion task, with zero cost while nothing changes; check each record's added nodes for the widget, then `disconnect()`. Caveat: subtree observation on body during heavy DOM churn processes many records — scope the observed root as narrowly as possible.</details>

## Related Notes

- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]
- [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
- [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[01 - Roadmap|Roadmap]]
