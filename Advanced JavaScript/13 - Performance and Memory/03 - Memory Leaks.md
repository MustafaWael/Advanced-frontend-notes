---
tags: [javascript, performance, memory, memory-leaks]
module: "13 - Performance and Memory"
priority: deep-dive
status: not-started
---

# Memory Leaks

## Maturity Target

- Priority: #deep-dive
- Study time: 110-150 minutes
- Interview signal: you can classify leak sources, explain retaining paths, and describe a repeatable debugging workflow.
- Production signal: repeated UI flows do not retain old listeners, timers, DOM nodes, subscriptions, caches, or closures.
- Dependencies: [[13 - Performance and Memory/01 - Memory Management|Memory Management]], [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]], [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]

## Source Anchors

- [MDN Memory management](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Memory_management)
- [Chrome DevTools Memory Problems](https://developer.chrome.com/docs/devtools/memory-problems)
- [React useEffect](https://react.dev/reference/react/useEffect)
- [MDN addEventListener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener)

## 1. Concept

A memory leak is memory that remains reachable after the application no longer needs it.

In JavaScript, leaks are usually not manual allocation mistakes. They are ownership mistakes:

- something was registered and never unregistered;
- something was cached and never evicted;
- something was stored globally and never cleared;
- something was closed over and never released.

## 2. Why It Matters

Leaks hurt long-lived pages more than short demos:

- single-page apps keep the tab alive for hours;
- dashboards and admin tools repeat route transitions;
- modals, tooltips, and editors mount/unmount often;
- large data views can retain thousands of objects;
- memory pressure can increase GC work and interaction latency.

## 3. Accurate Mechanism

The leaked object is only the visible symptom. The cause is the retaining path.

Common leak categories:

| Category | Retaining source |
| --- | --- |
| Listener leak | `window`, `document`, element, media query, socket, store |
| Timer leak | `setInterval`, `setTimeout`, `requestAnimationFrame` |
| Cache leak | array, object, Map, query cache, module singleton |
| Closure leak | callback retains large lexical environment |
| DOM leak | detached nodes referenced from JS |
| Subscription leak | event bus, observable, websocket, external store |
| Resource leak | object URLs, workers, streams, observers |

## 4. Mental Model

Leaks are proven by repetition.

One mount is not a leak. A leak shows up when repeating the same lifecycle leaves extra memory behind each time.

Investigation loop:

1. Establish baseline.
2. Repeat one interaction many times.
3. Let cleanup happen.
4. Compare heap/snapshots.
5. Inspect retaining paths.
6. Fix the owner that forgot cleanup.

## 5. Real Frontend Bug: Modal Listener Leak

Problem:

```tsx
function Modal({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    window.addEventListener("keydown", (event) => {
      if (event.key === "Escape") onClose();
    });
  }, [onClose]);

  return <div role="dialog">...</div>;
}
```

Bug:

- every mount creates a new anonymous listener;
- there is no cleanup;
- the listener retains `onClose` and anything it closes over;
- Escape may call old handlers after the modal closes.

Fix:

```tsx
function Modal({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return <div role="dialog">...</div>;
}
```

Why it works: cleanup removes the exact function reference registered with the host.

## 6. Real Frontend Bug: Route Cache Growth

Problem:

```ts
const pageCache = new Map<string, PageData>();

export async function loadPage(route: string) {
  if (pageCache.has(route)) return pageCache.get(route)!;

  const data = await fetchPage(route);
  pageCache.set(route, data);
  return data;
}
```

Bug:

- every route is cached forever;
- large page data remains reachable for the whole tab;
- memory grows as users navigate.

Fix with a bounded cache:

```ts
const MAX_PAGES = 20;
const pageCache = new Map<string, PageData>();

export async function loadPage(route: string) {
  const cached = pageCache.get(route);
  if (cached) return cached;

  const data = await fetchPage(route);
  pageCache.set(route, data);

  if (pageCache.size > MAX_PAGES) {
    const oldestKey = pageCache.keys().next().value;
    pageCache.delete(oldestKey);
  }

  return data;
}
```

> [!tip] Tradeoff
> evicted routes may refetch. That is a deliberate memory/network tradeoff.

## 7. Other Leak Patterns

```ts
// Timer leak
const id = setInterval(refresh, 1000);
clearInterval(id);

// Animation frame leak
const frame = requestAnimationFrame(tick);
cancelAnimationFrame(frame);

// Observer leak
const observer = new IntersectionObserver(callback);
observer.observe(element);
observer.disconnect();

// Object URL leak
const url = URL.createObjectURL(file);
URL.revokeObjectURL(url);

// Worker leak
const worker = new Worker("/worker.js");
worker.terminate();
```

The specific API changes, but the ownership rule is the same: create, use, release.

## 8. React Strict Mode Note

In development, React Strict Mode may run an extra setup-cleanup cycle for effects. Treat that as a gift: if your cleanup is wrong, duplicate subscriptions or timer bugs become visible earlier.

Production code should tolerate setup and cleanup happening in a clear mirrored way:

```tsx
useEffect(() => {
  subscribe();
  return () => unsubscribe();
}, []);
```

## 9. Production Checklist

- [ ] Every effect that subscribes returns cleanup.
- [ ] Event listeners are removed with the same function reference and capture option.
- [ ] Timers, animation frames, observers, workers, and object URLs are released.
- [ ] Caches are bounded or intentionally scoped.
- [ ] Large data is not kept in debug globals.
- [ ] Detached DOM nodes are not stored in arrays/maps.
- [ ] Repeated mount/unmount does not increase retained heap.
- [ ] Retaining paths are inspected before guessing.

## 10. Interview Answer

**Short version:** A JavaScript memory leak is memory that stays reachable after the app no longer needs it. The fix is to break the retaining path.

**Strong version:** Leaks usually come from listeners, timers, closures, detached DOM nodes, subscriptions, unbounded caches, workers, observers, or object URLs. Garbage collection only collects unreachable objects, so a removed component can still be retained by a host listener or a global cache. I debug leaks by repeating one interaction, comparing heap snapshots, and inspecting retaining paths. I fix ownership with cleanup, deletion, eviction, cancellation, or weak collections where appropriate.

## 11. Common Mistakes

- Looking at a single heap snapshot and calling it a leak.
- Forgetting cleanup for event bus or store subscriptions.
- Removing a listener with a different function reference.
- Letting debug caches ship to production unbounded.
- Treating object URLs as normal strings with no lifetime.
- Ignoring detached DOM nodes in snapshots.
- Optimizing CPU while the real issue is retained memory.

## 12. Practice

1. Fix a modal that adds a keydown listener on every open.
2. Add an eviction policy to an unbounded `Map`.
3. List five browser APIs that require explicit cleanup.
4. Explain why a detached DOM node can remain alive.
5. Describe a DevTools workflow to prove a leak is fixed.

## Related Notes

- [[13 - Performance and Memory/01 - Memory Management|Memory Management]]
- [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]
- [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]
- [[01 - Roadmap|Roadmap]]
