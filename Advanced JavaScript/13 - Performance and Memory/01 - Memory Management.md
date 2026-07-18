---
tags: [javascript, performance, memory, memory-management]
module: "13 - Performance and Memory"
priority: deep-dive
status: not-started
---

# Memory Management

## Maturity Target

- Priority: #deep-dive
- Study time: 100-140 minutes
- Interview signal: you can explain allocation, reachability, garbage collection, retained memory, and why "automatic memory" does not mean "no memory responsibility."
- Production signal: you design bounded lifetimes for caches, listeners, timers, object URLs, closures, and large data.
- Dependencies: [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]], [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]], [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]

## Source Anchors

- [MDN Memory management](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Memory_management)
- [MDN Performance API](https://developer.mozilla.org/en-US/docs/Web/API/Performance_API)
- [web.dev Learn Performance](https://web.dev/learn/performance/)
- [web.dev Optimize long tasks](https://web.dev/articles/optimize-long-tasks)
- [Chrome DevTools Memory Problems](https://developer.chrome.com/docs/devtools/memory-problems)

## 1. Concept

JavaScript memory management has three practical phases:

1. Allocate memory when values, objects, functions, DOM nodes, closures, and data structures are created.
2. Use that memory while the app needs it.
3. Let the engine reclaim it after it is no longer reachable.

> [!warning] Automatic does not mean hands-off
> Developers do not manually call `free()`. Developers control references and ownership. If your app keeps a reference alive, the object is still alive from the garbage collector's perspective.

## 2. Why It Matters

Memory problems are often slow-burn production bugs:

- a dashboard gets slower after many route changes;
- a modal leaks listeners after repeated open/close cycles;
- a cache grows for an entire tab session;
- a closure keeps a large API response alive;
- object URLs or image previews are never revoked;
- GC work creates jank during interactions.

> [!warning] Retained memory hurts responsiveness
> Memory is connected to performance. More retained objects can mean more GC work, larger heap snapshots, slower interactions, and worse responsiveness.

## 3. Official Mechanism

At a high level, JavaScript engines allocate memory automatically and reclaim objects that are no longer reachable. Modern engines use reachability-based garbage collectors with implementation optimizations such as generational, incremental, concurrent, or parallel collection. Those optimizations are engine details, but the developer-facing rule is stable:

If an object is reachable from active roots, it cannot be collected.

Common roots and retaining sources include:

- global objects and module singletons;
- current call stack and local variables;
- closures kept by callbacks;
- event listeners registered with host objects;
- timers and animation callbacks;
- DOM nodes reachable from the document or from JavaScript variables;
- caches, maps, arrays, and stores;
- pending promises and subscriptions.

## 4. Mental Model

You do not free memory. You stop owning it.

For any value that can grow or outlive a render, ask:

- Who owns this?
- How large can it get?
- When does ownership end?
- What removes the reference?
- How would I prove it gets released?

## 5. Real Frontend Bug: Unbounded Telemetry Buffer

Problem:

```ts
const debugEvents: DebugEvent[] = [];

export function recordDebugEvent(event: DebugEvent) {
  debugEvents.push({
    ...event,
    capturedAt: Date.now()
  });
}
```

Bug:

- the module-level array lives for the full tab session;
- every event remains reachable;
- long sessions accumulate memory;
- the debugger feature becomes a production leak.

Fix:

```ts
const MAX_DEBUG_EVENTS = 200;
const debugEvents: DebugEvent[] = [];

export function recordDebugEvent(event: DebugEvent) {
  debugEvents.push({
    ...event,
    capturedAt: Date.now()
  });

  if (debugEvents.length > MAX_DEBUG_EVENTS) {
    // Remove oldest events so the buffer has a bounded lifetime.
    debugEvents.splice(0, debugEvents.length - MAX_DEBUG_EVENTS);
  }
}

export function clearDebugEvents() {
  debugEvents.length = 0;
}
```

> [!tip] Bounded beats unbounded
> Tradeoff: a bounded buffer loses old events. That is usually better than an unbounded production heap.

## 6. Real Frontend Bug: Object URL Lifetime

Problem:

```tsx
function ImagePreview({ file }: { file: File }) {
  const url = URL.createObjectURL(file);
  return <img src={url} alt="" />;
}
```

Bug:

- each render can create a new object URL;
- the browser keeps the underlying blob data;
- the URL is never revoked.

Fix:

```tsx
function ImagePreview({ file }: { file: File }) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    const nextUrl = URL.createObjectURL(file);
    setUrl(nextUrl);

    return () => {
      URL.revokeObjectURL(nextUrl);
    };
  }, [file]);

  return url ? <img src={url} alt="" /> : null;
}
```

> [!tip] Give object URLs an owner
> Why it works: the effect gives the object URL a clear owner and revokes it when the file changes or the component unmounts.

## 7. Measure Before Optimizing

Use the right signal for the problem:

| Symptom | First tool |
| --- | --- |
| Tab memory grows after repeated interactions | Chrome Memory panel heap snapshots |
| Clicks feel delayed | Performance panel, INP field data |
| CPU spikes during render | React Profiler or browser Performance panel |
| Filtering/search is slow | `performance.now()` around the calculation |
| Huge list slows page | DOM size and rendering profile |

Small measurement helper:

```ts
function measure<T>(label: string, fn: () => T): T {
  const start = performance.now();
  try {
    return fn();
  } finally {
    console.log(`${label}: ${performance.now() - start}ms`);
  }
}
```

Use this for local investigation, not as noisy production logging.

## 8. Production Tradeoffs

| Technique | Benefit | Cost |
| --- | --- | --- |
| Bounded cache | predictable memory | cache misses after eviction |
| WeakMap metadata | no strong object retention | no iteration or size |
| Memoization | less repeated CPU work | extra memory and invalidation complexity |
| Cleanup in effects | releases host references | more lifecycle code |
| Virtualization | less DOM and render work | more complex accessibility/layout |
| Web worker | moves CPU off main thread | serialization and coordination overhead |

## 9. Interview Answer

**Short version:** JavaScript allocates memory automatically and garbage collects unreachable objects. Developers still manage memory indirectly by controlling references and lifetimes.

**Strong version:** The engine can reclaim objects only when they are unreachable from roots such as globals, the stack, closures, DOM references, listeners, timers, and caches. A memory leak in JavaScript usually means the app still has a retaining path to data it no longer logically needs. In production I look for unbounded caches, listeners, timers, object URLs, subscriptions, detached DOM nodes, and closures over large data. I fix ownership first, then verify with repeated-interaction profiling and heap snapshots.

## 10. Common Mistakes

- Thinking garbage collection prevents all leaks.
- Treating memory issues as guesses instead of retaining-path investigations.
- Keeping unbounded arrays, maps, or caches at module scope.
- Forgetting object URL cleanup.
- Memoizing large values without an invalidation or eviction plan.
- Assuming clearing the UI removes all JavaScript references.
- Measuring development mode and assuming production behavior is identical.

## 11. Practice

1. Explain why a module-level array can leak memory in a single-page app.
2. Write a bounded LRU-like cache with a maximum size.
3. Fix an object URL preview so it calls `URL.revokeObjectURL`.
4. Describe how you would prove a repeated modal interaction does not leak.
5. Explain why "reachable" is more important than "still needed."

## Related Notes

- [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[01 - Roadmap|Roadmap]]
