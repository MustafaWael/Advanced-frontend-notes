---
tags: [javascript, moc, performance, memory]
module: "13 - Performance and Memory"
priority: deep-dive
status: not-started
---

# Performance and Memory MOC

This module teaches how JavaScript memory actually works — allocation, reachability, garbage collection, retaining paths — and how that model explains leaks from listeners, timers, closures, and caches. It then moves up to CPU cost: memoization, React render bottlenecks, and profiling with Chrome DevTools. It unlocks the bugs that only appear after minutes of real usage (growing memory on route changes, sluggish tabs, leaking modals) and the interview questions that separate "I use `useMemo`" from "I can find and break the retaining path."

## Prerequisites

- [[03 - Scope and Variables/05 - Closures|Closures]] — closures are the main way memory is silently retained.
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]] — the bug patterns this module extends into memory terms.
- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]] — references and identity underpin reachability.
- [[09 - Event Loop Advanced/04 - Timers|Timers]] — timer lifetime is a recurring leak source here.
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]] — long tasks and main-thread blocking context.

## Reading Order

1. [[13 - Performance and Memory/01 - Memory Management|Memory Management]] — allocation, use, and release: the base vocabulary.
2. [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]] — why "unreachable" matters more than "not needed."
3. [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]] — the leak taxonomy: listeners, timers, caches, subscriptions, detached DOM.
4. [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]] — how a small callback can keep a large object alive.
5. [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]] — pairing every setup API with its correct cleanup.
6. [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]] — caching as keys, invalidation, and lifetime, not magic.
7. [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]] — `memo`, `useMemo`, `useCallback`, and real render bottlenecks.
8. [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]] — heap snapshots and retaining paths in practice.
9. [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]] — active self-test with scenarios and drills.
10. [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]] — LCP, INP, CLS, long tasks, `PerformanceObserver`, and field vs lab data.

## You're Done When

- [ ] I can explain allocation, use, and release, and why reachability — not "not needed" — decides collection.
- [ ] I can identify roots and retaining paths, and explain why a removed DOM node can still be retained.
- [ ] I can classify listener, timer, closure, cache, subscription, and object URL leaks, and pair each setup API with its cleanup.
- [ ] I can explain how closures retain lexical environments and how that shows up in heap snapshots.
- [ ] I can explain memoization as a cache with keys, invalidation, and lifetime, and measure before memoizing.
- [ ] I can say when `memo`, `useMemo`, and `useCallback` actually help in React, and when they are noise.
- [ ] I can distinguish render bottlenecks from DOM, network, memory, and main-thread bottlenecks.
- [ ] I can profile a leak with heap snapshots and verify a fix with repeated-interaction profiling in a production-like build.

## Related Notes

- [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]]
- [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]
- [[01 - Roadmap|Roadmap]]
