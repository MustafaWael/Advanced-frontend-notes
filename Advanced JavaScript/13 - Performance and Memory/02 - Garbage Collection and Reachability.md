---
tags: [javascript, performance, memory, garbage-collection-and-reachability]
module: "13 - Performance and Memory"
priority: deep-dive
status: not-started
aliases: [GC, Garbage Collection]
---

# Garbage Collection and Reachability

## Maturity Target

- Priority: #deep-dive
- Study time: 100-140 minutes
- Interview signal: you can explain roots, retaining paths, mark-and-sweep, cycles, weak collections, and why GC timing is not part of app logic.
- Production signal: you debug memory problems by asking what keeps an object reachable.
- Dependencies: [[13 - Performance and Memory/01 - Memory Management|Memory Management]], [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]], [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]

## Source Anchors

- [MDN Memory management](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Memory_management)
- [MDN WeakMap](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakMap)
- [Chrome DevTools Memory Problems](https://developer.chrome.com/docs/devtools/memory-problems)

## 1. Concept

Garbage collection reclaims memory for objects that are no longer reachable.

Reachable means there is a path from a root to the object. Roots include the global object, active stack frames, closures, host registrations, and other engine/host references.

```js
let user = { name: "Ada" };
let current = user;

user = null;
// The object is still reachable through current.

current = null;
// Now it may become collectible.
```

## 2. Why It Matters

> [!warning] The retaining path is the bug
> The bug is rarely "the object is big." The bug is "something still points to it."

In browser apps, common retaining paths include:

- event listeners on `window` or `document`;
- timers and animation callbacks;
- closures registered in global stores;
- detached DOM nodes referenced from JavaScript;
- maps and arrays that never delete entries;
- pending promises and subscriptions;
- React state or refs that outlive a view.

## 3. Official Mechanism

Modern JavaScript engines use reachability-based garbage collection. MDN describes mark-and-sweep as the core mental model:

1. Start from roots.
2. Mark every reachable object.
3. Continue through references from marked objects.
4. Collect objects that were not reached.

Cycles are not automatically leaks if the cycle itself is unreachable.

```js
function makeCycle() {
  const a = {};
  const b = {};
  a.b = b;
  b.a = a;
}

makeCycle();
```

After `makeCycle` returns, the cycle is unreachable from roots, so a reachability-based collector can reclaim it.

## 4. Mental Model

Reachable means alive, even if useless.

When debugging memory, ask:

- What object is growing?
- What path keeps it reachable?
- Which owner should release that path?
- Is the retaining path a JavaScript reference, a DOM reference, or a host registration?

## 5. Real Frontend Bug: Detached DOM Node

Problem:

```ts
const removedPanels: HTMLElement[] = [];

function closePanel(panel: HTMLElement) {
  panel.remove();
  removedPanels.push(panel);
}
```

Bug:

- `panel.remove()` detaches the node from the document;
- `removedPanels` still strongly references it;
- the panel and its child tree remain reachable;
- any event handlers and data attached to that subtree also stay alive.

Fix:

```ts
function closePanel(panel: HTMLElement) {
  panel.remove();
  // Do not store detached nodes unless there is a bounded, intentional owner.
}
```

If metadata is needed while the element exists:

```ts
const panelMeta = new WeakMap<HTMLElement, { openedAt: number }>();

function openPanel(panel: HTMLElement) {
  panelMeta.set(panel, { openedAt: Date.now() });
}
```

> [!tip] WeakMap avoids extending lifetime
> The WeakMap does not keep the element alive after nothing else references it.

## 6. Host References Matter

The browser can hold references too.

```ts
function mount() {
  const panel = document.querySelector("#panel");

  function onResize() {
    console.log(panel?.clientWidth);
  }

  window.addEventListener("resize", onResize);
}
```

> [!warning] Host references keep closures alive
> Even if the panel is removed from the DOM, the `resize` listener can keep `onResize` alive, and `onResize` can keep `panel` alive through its closure.

Fix:

```ts
function mount() {
  const panel = document.querySelector("#panel");

  function onResize() {
    console.log(panel?.clientWidth);
  }

  window.addEventListener("resize", onResize);

  return () => {
    window.removeEventListener("resize", onResize);
  };
}
```

## 7. Weak References and Weak Collections

WeakMap and WeakSet are useful when metadata should not extend an object's lifetime.

```ts
const measurements = new WeakMap<Element, DOMRect>();

function rememberMeasurement(element: Element) {
  measurements.set(element, element.getBoundingClientRect());
}
```

Constraints:

- WeakMap keys must be objects or allowed symbols in modern engines;
- WeakMap is not iterable;
- there is no `.size`;
- you cannot build app logic around when GC happens.

> [!tip] Weak collections are not GC hooks
> Use weak collections to avoid accidental retention, not to observe garbage collection.

## 8. Production Tradeoffs

| Concept | Practical consequence |
| --- | --- |
| Root | Anything reachable from it is alive |
| Retaining path | The chain you must break |
| Closure | Can keep its lexical environment alive |
| Host registration | Browser holds callback reference |
| WeakMap | Metadata without strong key retention |
| GC timing | Non-deterministic, not app logic |

## 9. Interview Answer

**Short version:** Garbage collection reclaims objects that are unreachable from roots. A leak means something still keeps an object reachable even though the app no longer needs it.

**Strong version:** Modern engines use reachability-based collection. The collector starts from roots such as globals, stack frames, closures, DOM/host references, timers, and listeners, then marks reachable objects. Cycles are fine if the whole cycle is unreachable. In production, I debug memory by finding the retaining path. A detached DOM node is not collectible if a listener closure, array, map, or global store still references it. I break that path with cleanup, deletion, bounded caches, or WeakMap when metadata should not extend lifetime.

## 10. Common Mistakes

- Thinking circular references always leak.
- Thinking removed DOM nodes are automatically collectible.
- Forgetting that host objects can retain callbacks.
- Using a normal `Map` for DOM metadata that should be weak.
- Trying to rely on when GC will run.
- Looking at heap size once instead of comparing after repeated interactions.

## 11. Practice

1. Explain why an unreachable cycle can be collected.
2. Identify the retaining path in a detached DOM node leak.
3. Replace a `Map<Element, Data>` with `WeakMap<Element, Data>` and explain the tradeoff.
4. Explain why you cannot iterate a WeakMap.
5. Describe the difference between "not needed" and "unreachable."

## Related Notes

- [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]]
- [[13 - Performance and Memory/01 - Memory Management|Memory Management]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
- [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]
- [[01 - Roadmap|Roadmap]]
