---
tags: [javascript, performance, memory, chrome-devtools-memory-profiling]
module: "13 - Performance and Memory"
priority: deep-dive
status: not-started
---

# Chrome DevTools Memory Profiling

## Maturity Target

- Priority: #deep-dive
- Study time: 90-130 minutes
- Interview signal: you can describe a repeatable heap investigation workflow and explain retained size, shallow size, dominators, and retaining paths.
- Production signal: you diagnose leaks with evidence instead of guesses.
- Dependencies: [[13 - Performance and Memory/01 - Memory Management|Memory Management]], [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]], [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]

## Source Anchors

- [Chrome DevTools Memory Problems](https://developer.chrome.com/docs/devtools/memory-problems)
- [Chrome DevTools Performance Panel](https://developer.chrome.com/docs/devtools/performance)
- [MDN Memory management](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Memory_management)
- [MDN Performance API](https://developer.mozilla.org/en-US/docs/Web/API/Performance_API)

## 1. Concept

Memory profiling uses browser tools to answer two questions:

1. What objects are retained?
2. What retaining path keeps them alive?

The point is not to stare at heap size once. The point is to compare memory after repeated interactions and identify what should have gone away but did not.

## 2. Why It Matters

Memory leaks are easy to misdiagnose:

- heap naturally rises and falls as the app works;
- garbage collection is non-deterministic;
- dev mode can allocate extra objects;
- caches may grow intentionally;
- the object you notice may be retained by something unexpected.

Profiling gives you evidence.

## 3. Accurate Mechanism

Chrome DevTools Memory panel can capture heap snapshots and allocation timelines. Heap snapshots show objects, shallow size, retained size, and retaining paths.

Important terms:

| Term | Meaning |
| --- | --- |
| Shallow size | memory used by the object itself |
| Retained size | memory that could be freed if this object became unreachable |
| Retainer | object/path keeping another object alive |
| Dominator | object that controls reachability of a subgraph |
| Detached DOM node | node removed from DOM but still referenced |

## 4. Mental Model

A memory investigation is a controlled experiment:

1. Start clean.
2. Capture baseline.
3. Repeat one user flow.
4. Let cleanup and GC happen.
5. Capture another snapshot.
6. Compare.
7. Inspect retaining paths.
8. Fix the owner.
9. Repeat the same test.

## 5. Real Frontend Investigation: Modal Leak

Scenario: memory grows every time a modal opens and closes.

Workflow:

1. Open the page in a production-like build.
2. Open DevTools Memory panel.
3. Capture a heap snapshot.
4. Open and close the modal 20 times.
5. Trigger garbage collection from DevTools if available.
6. Capture another snapshot.
7. Compare snapshots.
8. Search for modal component names, detached DOM nodes, or listener callbacks.
9. Inspect retainers.

Possible result:

```txt
Window
  EventListener: keydown
    handleKeyDown
      Closure
        Modal props
          large product data
```

Fix: remove the keydown listener during modal cleanup or use an abort signal tied to the modal lifecycle.

## 6. Allocation Timeline Use

Heap snapshots answer "what is retained now?"

Allocation instrumentation answers "when was this allocated?"

Use allocation timeline when:

- a specific interaction causes a memory spike;
- you need to know which code path allocates many objects;
- snapshots show growth but not the moment it happens.

Use heap snapshots when:

- you need retaining paths;
- you suspect detached DOM nodes;
- repeated flows leave objects behind.

## 7. Production Performance Profiling

Memory is one side. Runtime performance is another.

Use Chrome Performance panel for:

- long tasks;
- scripting time;
- rendering and painting;
- layout thrashing;
- interaction delay;
- forced reflow warnings;
- event handler cost.

Use React Profiler for:

- which components rendered;
- render durations;
- whether memoization reduced render cost.

Use field metrics for:

- whether real users are affected;
- which routes/devices/interactions are slow.

## 8. Common False Positives

- DevTools itself adds overhead.
- Development builds allocate more and render extra checks.
- Caches may intentionally retain memory up to a bound.
- Heap may not drop immediately until GC runs.
- One retained object may be small but dominate a large graph.
- Browser extensions can add noise.

Use comparison and repetition, not one-off numbers.

> [!tip] Diagnose leaks by comparison, not absolute numbers
> A single heap number means little — dev builds, caches, and pending GC all inflate it. Take snapshots before and after repeating an action (open/close a modal N times); a leak shows as retained objects that grow with each cycle and never drop.

## 9. Debugging Checklist

- [ ] Reproduce in a production-like build.
- [ ] Disable unrelated extensions if possible.
- [ ] Record exact interaction steps.
- [ ] Compare before/after snapshots.
- [ ] Look for detached DOM nodes.
- [ ] Sort by retained size.
- [ ] Inspect retaining paths.
- [ ] Identify the owner that should release the object.
- [ ] Patch cleanup/eviction.
- [ ] Repeat the same profile to verify.

## 10. Interview Answer

**Short version:** I debug memory leaks by repeating a user flow, comparing heap snapshots, and inspecting retaining paths to find what keeps old objects alive.

**Strong version:** Heap size alone is not proof. I set up a controlled interaction, capture a baseline, repeat the lifecycle many times, allow cleanup/GC, then compare snapshots. I look at retained size, detached DOM nodes, dominators, and retaining paths. If a modal is retained by a `window` listener closure, the fix is not "optimize memory" in general; it is removing that listener or tying it to an abort signal. After the fix, I repeat the same profiling steps to prove the retaining path is gone.

## 11. Common Mistakes

- Guessing from code without inspecting retaining paths.
- Treating one heap increase as a leak.
- Profiling only in development mode.
- Sorting only by shallow size.
- Forgetting detached DOM nodes.
- Fixing the retained object rather than the retainer.
- Not repeating the same scenario after the fix.

## 12. Practice

1. Design a heap snapshot experiment for a modal open/close leak.
2. Explain shallow size vs retained size.
3. Explain what a retaining path tells you.
4. Decide when to use heap snapshot vs allocation instrumentation.
5. Describe how you would prove an event listener leak was fixed.

## Related Notes

- [[13 - Performance and Memory/01 - Memory Management|Memory Management]]
- [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]
- [[01 - Roadmap|Roadmap]]
