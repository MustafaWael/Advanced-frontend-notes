---
tags: [javascript, performance, memory, performance-checklist]
module: "13 - Performance and Memory"
priority: must-know
status: not-started
---

# Performance Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, diagnose, and fix the behavior without looking.

## Maturity Target

- Priority: #must-know
- Study time: 90-130 minutes for review.
- Interview signal: you can connect memory, render performance, cleanup, memoization, DevTools, and user-facing responsiveness.
- Production signal: you measure, identify the bottleneck, fix ownership, and verify the same scenario again.

## Fast Track Order

1. [[13 - Performance and Memory/01 - Memory Management|Memory Management]]
2. [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]
3. [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
4. [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
5. [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
6. [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
7. [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
8. [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]

Reason: understand ownership and reachability before reaching for performance tools.

## Core Understanding

- [ ] I can explain allocation, use, and release in JavaScript.
- [ ] I can explain why unreachable matters more than "not needed."
- [ ] I can identify common roots and retaining paths.
- [ ] I can explain why a removed DOM node can still be retained.
- [ ] I can classify listener, timer, closure, cache, subscription, and object URL leaks.
- [ ] I can pair every setup API with the correct cleanup API.
- [ ] I can explain how closures retain lexical environments.
- [ ] I can explain memoization as a cache with keys, values, invalidation, and lifetime.
- [ ] I can explain when `memo`, `useMemo`, and `useCallback` help in React.
- [ ] I can distinguish render bottlenecks from DOM, network, memory, and main-thread bottlenecks.
- [ ] I can use heap snapshots to inspect retaining paths.
- [ ] I can connect long tasks and main-thread blocking to poor interaction responsiveness.

## Production Readiness Checklist

- [ ] Caches are bounded, scoped, or explicitly cleared.
- [ ] Listeners are removed with the same function reference or an abort signal.
- [ ] Timers and animation frames are cleared.
- [ ] Observers, workers, object URLs, and subscriptions are released.
- [ ] React effects mirror setup and cleanup.
- [ ] Debug buffers do not grow forever.
- [ ] Large closures are avoided or unregistered.
- [ ] Expensive calculations are measured before memoization.
- [ ] Large lists are virtualized or paginated when DOM size is the bottleneck.
- [ ] React context is split by update frequency when broad rerenders hurt.
- [ ] Performance fixes are verified in production-like builds.
- [ ] Memory fixes are verified with repeated interaction profiling.

## Source-Backed Terms

| Term | Plain meaning | Technical meaning | Production use |
| --- | --- | --- | --- |
| Reachable | Still connected. | Object can be reached from roots. | Explains why GC cannot collect it. |
| Retaining path | Why it is alive. | Chain of references from root to object. | The path to break when fixing leaks. |
| Retained size | Memory controlled by an object. | Memory freed if the object became unreachable. | Better leak signal than shallow size. |
| Long task | Main-thread work that runs too long. | Blocks input/render opportunities. | Hurts responsiveness and INP. |
| Memoization | Reuse calculated value. | Cache by dependencies or keys. | Saves CPU when invalidation is correct. |
| Cleanup | End ownership. | Remove host references or release resources. | Prevents leaks and duplicate work. |

## Real-World Scenario Review

### Scenario 1: modal opens and closes repeatedly

Check:

- keydown listener cleanup;
- body scroll lock cleanup;
- timers and animations;
- detached DOM nodes;
- old props retained by closures.

Fix pattern:

```tsx
useEffect(() => {
  function onKeyDown(event: KeyboardEvent) {
    if (event.key === "Escape") onClose();
  }

  window.addEventListener("keydown", onKeyDown);
  return () => window.removeEventListener("keydown", onKeyDown);
}, [onClose]);
```

### Scenario 2: table search feels slow

Decision path:

1. Measure filter/sort cost.
2. Profile render cost.
3. Check DOM size.
4. If calculation is slow, use memoization/indexing/debounce/worker.
5. If rendering is slow, use pagination or virtualization.

### Scenario 3: route changes grow memory

Check:

- query/page caches;
- event bus subscriptions;
- global stores holding route data;
- object URLs;
- detached DOM nodes;
- pending promises retaining old payloads.

### Scenario 4: memoized child rerenders

Check:

- new object/array/function props;
- context updates;
- changing keys;
- parent state colocated too high;
- child is not actually expensive.

## Code Drills

### Drill 1: listener cleanup

```tsx
useEffect(() => {
  function onResize() {
    console.log(window.innerWidth);
  }

  window.addEventListener("resize", onResize);
  return () => window.removeEventListener("resize", onResize);
}, []);
```

Explain: same function reference, setup mirrors cleanup.

### Drill 2: bounded cache

```ts
const cache = new Map<string, Result>();

function setCached(key: string, value: Result, maxSize = 50) {
  cache.set(key, value);

  if (cache.size > maxSize) {
    const oldest = cache.keys().next().value;
    cache.delete(oldest);
  }
}
```

Explain: memory is bounded by entry count, with a refetch/recompute tradeoff.

### Drill 3: measure calculation

```ts
const start = performance.now();
const result = expensiveTransform(items);
console.log(performance.now() - start);
```

Explain: local measurement identifies CPU cost, but React render cost needs React/browser profiling.

### Drill 4: memoized child prop

```tsx
<Chart options={{ showLegend: true }} />
```

Explain: a new object is created every render; `memo` sees changed props. Use module constant or `useMemo` if the chart is actually expensive.

## Interview Prompts

1. What does JavaScript garbage collection reclaim?
2. What is a retaining path?
3. Why can a detached DOM node leak?
4. Why does removing a listener require the same function reference?
5. How can closures retain large objects?
6. What is the cost of memoization?
7. When does `useCallback` help?
8. How do you profile a memory leak in Chrome DevTools?
9. How do you profile a React render bottleneck?
10. What is the difference between lab profiling and field performance data?

## Self-Review Rubric

| Level | What your answer sounds like |
| --- | --- |
| Weak | "Use memoization and cleanup." |
| Junior-plus | "Remove listeners and use `useMemo` for expensive work." |
| Mid-level | "Find the bottleneck, understand ownership, and fix the retaining path or render cause." |
| Strong mid-level | "I can design a measured investigation, distinguish memory from CPU/render/network issues, fix the exact owner, and verify with the same scenario." |

## Related Notes

- [[13 - Performance and Memory/01 - Memory Management|Memory Management]]
- [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]
- [[01 - Roadmap|Roadmap]]
