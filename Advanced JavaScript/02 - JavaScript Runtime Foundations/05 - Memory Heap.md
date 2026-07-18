---
tags: [javascript, runtime, memory-heap]
module: "02 - JavaScript Runtime Foundations"
priority: must-know
status: not-started
---

# Memory Heap

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Outcome: explain object allocation, references, reachability, and the practical causes of frontend memory leaks.

## Source Anchors

- [MDN Memory management](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Memory_management)
- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)

## 1. Simple Explanation

The heap is where JavaScript engines allocate objects and other dynamic values such as arrays, functions, maps, sets, closures, and many engine-managed structures.

You do not manually free heap memory in JavaScript. The engine reclaims objects when they are no longer reachable.

## 2. Why It Matters

Frontend memory problems rarely come from "forgetting to free memory" directly. They come from keeping references alive longer than intended:

- Event listeners that are never removed.
- Timers that continue after unmount.
- Closures stored in long-lived registries.
- Caches that grow forever.
- Detached DOM nodes retained by JavaScript references.
- React state snapshots or query caches kept beyond their useful lifetime.

## 3. Accurate Mechanism

The exact memory layout is engine-specific, but the useful model is:

| Concept | Practical meaning |
| --- | --- |
| Primitive value | Immutable language value such as number, string, boolean, null, undefined, symbol, or bigint. |
| Object value | A reference to a heap-allocated object, array, function, map, set, date, etc. |
| Reachability | If a live root can reach an object through references, the object must stay alive. |
| Garbage collection | Engine process that reclaims unreachable objects. |
| Retaining path | The chain of references keeping an object alive. |

The stack vs heap explanation is useful, but do not oversimplify it. Variables are spec bindings in environments. Engines choose concrete storage strategies internally. The production rule is about references and reachability.

### Generational Collection (Overview)

Most objects die young — a render allocates hundreds of temporary objects that are garbage before the next frame. V8 exploits this by splitting the heap into generations:

- **Young generation**: new allocations land here. A minor GC (the **Scavenger**) runs cheaply and frequently, copying the few survivors and discarding the rest wholesale.
- **Old generation**: objects that survive a couple of minor GCs are promoted here. A major GC (**Mark-Compact**) reclaims it, running concurrently and incrementally (V8's Orinoco project) to keep main-thread pauses short.

Practical consequence: short-lived allocations are cheap; what hurts is churning *long-lived* references (promoted objects that then die) and, above all, unintentionally keeping objects reachable. Deep dive lives in [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]].

## 4. Reference Model

```js
const user = { name: 'Mina' };
const sameUser = user;

sameUser.name = 'Updated';

console.log(user.name); // Updated
```

Both variables hold references to the same object. Reassigning one variable would not reassign the other, but mutating the shared object is visible through both references.

## 5. Pass-By-Sharing Edge Case

JavaScript does not pass variables "by reference" in the C++ sense. Function arguments receive values. For objects, that value is a reference to an object, so mutation is visible but reassignment is not.

```js
function update(obj) {
  obj.x = 1;      // Mutates the shared object.
  obj = { x: 2 }; // Reassigns only the local parameter binding.
}

const item = { x: 0 };
update(item);

console.log(item.x); // 1
```

Production lesson: a helper can mutate state even if it cannot reassign the caller's variable. That is why mutation discipline matters around React state, query caches, and shared API data.

## 6. Real Frontend Example

```tsx
function ViewportSize() {
  const [size, setSize] = React.useState({
    width: window.innerWidth,
    height: window.innerHeight
  });

  React.useEffect(() => {
    function handleResize() {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    }

    // The browser keeps a reference to this callback.
    // The callback keeps references to everything it closes over.
    window.addEventListener('resize', handleResize);

    // Cleanup removes the host reference, allowing closed-over data to be collected
    // when nothing else references it.
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return <span>{size.width}x{size.height}</span>;
}
```

## 7. Common Production Bug

```ts
const searchCache = new Map<string, SearchResult[]>();

export async function search(query: string) {
  if (searchCache.has(query)) return searchCache.get(query)!;

  const results = await fetch(`/api/search?q=${query}`).then(r => r.json());
  searchCache.set(query, results);
  return results;
}
```

This cache can grow forever in a long session. It is not a leak from the engine's perspective because the map is reachable and intentionally holds values. It is a leak from the application's perspective because old entries no longer have business value.

Safer patterns:

- Bound cache size.
- Add time-based eviction.
- Clear user-scoped caches on logout.
- Prefer a query library with stale time and garbage collection policy.
- Use `WeakMap` only when object-key lifetime is the correct ownership model.

## 8. WeakRef and FinalizationRegistry (ES2021)

While `WeakMap` and `WeakSet` hold keys weakly, ES2021 introduced `WeakRef` and `FinalizationRegistry` for direct reference tracking.

A `WeakRef` lets you hold a reference to an object without preventing it from being garbage collected. You access the target object with `.deref()`, which returns the object if it is still alive, or `undefined` if it has been collected.

```js
let heavyObject = { data: new ArrayBuffer(1_000_000) };
const ref = new WeakRef(heavyObject);

// Accessing the object
const obj = ref.deref();
if (obj) {
  console.log("Alive:", obj.data);
} else {
  console.log("Collected");
}
```

A `FinalizationRegistry` registers a cleanup callback that runs after an object is garbage-collected.

```js
const registry = new FinalizationRegistry((heldValue) => {
  console.log(`Cleanup for: ${heldValue}`);
});

let user = { name: "Mustafa" };
registry.register(user, "user-meta-data-key");
user = null; // Object is now candidate for GC
```

> [!warning]
> Garbage collection is non-deterministic. Never rely on the timing of GC or finalizer callbacks for program correctness. Use them only for performance optimizations like caches.

## 9. V8 Array Element Kinds (Packed vs. Holey)

This section is engine implementation detail, not spec behavior — useful for understanding measured hot paths, not a daily coding rule.

Under the hood, engines like V8 optimize arrays based on their shape and content types, tracked via **Element Kinds**.

| Element Kind | Example | Performance |
| --- | --- | --- |
| `PACKED_SMI_ELEMENTS` | `[1, 2, 3]` | High (all small integers, contiguous memory) |
| `PACKED_DOUBLE_ELEMENTS` | `[1.1, 2.2, 3.3]` | Medium (numbers/floats) |
| `PACKED_ELEMENTS` | `[1, "two", {}]` | Lower (mixed objects/types) |
| `HOLEY_ELEMENTS` | `[1, , 3]` | Slowest (contains index gaps/holes) |

### The One-Way Transition
V8 transitions arrays from specific to general kinds, but never back. Once an array becomes holey (e.g. `arr[10] = 99` on a 3-element array) or holds objects, it is permanently de-optimized.

```js
const arr = [1, 2, 3]; // PACKED_SMI
arr.push(4.5);         // Transition to PACKED_DOUBLE
arr[10] = "eleven";    // Transition to HOLEY_ELEMENTS
```

### The Cost of Holes
When accessing an index that is a hole, the engine cannot just return `undefined`. By spec, it must check the prototype chain (`Array.prototype` -> `Object.prototype`) for an indexed property, because a prototype could define one. That check forces the engine off its fast element-access path, and holey arrays can additionally fall back to dictionary-mode (slow) elements. The cost is losing the optimized fast path, not a linear walk over the array's elements.

Production rule: Avoid leaving `new Array(size)` holey. `new Array(n).fill(0)` immediately produces a PACKED array, so preallocation is fine when you fill it right away. `Array.from({ length: size }, fn)` and sequential `push` also keep arrays packed.

## 10. Shallow Copy Bug

```tsx
function updateTheme(user: User) {
  const nextUser = { ...user };

  // Bug: preferences is still the same nested object.
  nextUser.preferences.theme = "dark";

  return nextUser;
}
```

The outer object is new, but `preferences` is shared. In React state, copy every changed level:

```tsx
function updateTheme(user: User) {
  return {
    ...user,
    preferences: {
      ...user.preferences,
      theme: "dark",
    },
  };
}
```

Tradeoff: deep copying everything is wasteful and can break identity optimizations. Copy the path you change, normalize complex data, or use a well-understood immutable-update helper when nested updates dominate the code.

## Real-World Use Cases

### Classic interview trap: the detached DOM node

The standard "find the leak" question. A tooltip manager keeps a module-level registry of elements; the elements leave the page but never leave memory.

```ts
const tooltipTargets = new Map<string, HTMLElement>();

export function registerTooltip(id: string, el: HTMLElement) {
  tooltipTargets.set(id, el);
}

// Later: a route change unmounts the whole section...
container.replaceChildren(); // nodes removed from the document
// ...but tooltipTargets still references every one of them.
```

Trace the retaining path: `module environment -> tooltipTargets Map -> HTMLElement`. Removal from the document only severs the *document's* reference; the node stays reachable from a root (the module), so the GC must keep it — along with its entire subtree and any listeners attached to it. DevTools' heap snapshot labels these "Detached HTMLDivElement". Fix: delete entries on unmount, or key the map weakly — `new WeakMap<HTMLElement, TooltipMeta>()` inverts the ownership so the DOM node's lifetime drives the metadata's lifetime.

See [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]] and [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]].

### Live dashboard: unbounded WebSocket message history

An ops dashboard stays open for days. Every incoming event is appended to state; the tab dies at 2GB around hour 30.

```tsx
useEffect(() => {
  const socket = new WebSocket(WS_URL);
  socket.onmessage = event => {
    const alert = JSON.parse(event.data);
    setAlerts(prev => [...prev, alert].slice(-500)); // bounded: keep the newest 500
  };
  return () => socket.close();
}, []);
```

Without `.slice(-500)`, every alert ever received stays reachable through React's state. The GC is working perfectly — the application simply declared it wants everything alive. Reachability, not collection, is the knob you control.

See [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets SSE and Polling]].

### A tiny closure pinning a 10MB API response

A report page fetches a large payload, derives one number, and hands a callback to a long-lived toolbar. The whole payload rides along.

```tsx
const report = await fetchAnnualReport(); // ~10MB parsed object

// Bug: the handler only needs the total, but it closes over `report`.
toolbar.onExport(() => download(buildCsv(report.rows)));

// Fix: extract what you need; let the big object go.
const rows = report.rows.map(pickExportColumns); // small projection
toolbar.onExport(() => download(buildCsv(rows)));
```

The closure keeps its creation-time environment reachable, and the environment holds `report` — so a 40-byte function retains a 10MB graph for as long as the toolbar keeps the callback. Retained size (what a heap snapshot shows) is about what a reference *transitively* keeps alive, not the size of the function itself.

> [!tip]
> When a heap snapshot shows a huge "retained size" on a small closure, look at what the closure's scope captures — then narrow the capture by pulling out the small derived value before creating the function.

See [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]].

## 11. Interview Answer

**Short version:** The heap stores dynamically allocated objects. JavaScript garbage collection frees objects that are no longer reachable, but it cannot free objects your code still references.

**Deeper version:** JavaScript developers do not manually allocate and free memory, but they still control object lifetime by controlling references. Objects remain alive while reachable from roots such as globals, active stack frames, closures, host callbacks, DOM references, or framework caches. Most frontend leaks come from long-lived references: event listeners, timers, subscriptions, unbounded caches, detached DOM nodes, or closures retaining large data.

## 12. Common Mistakes

- Thinking garbage collection prevents all leaks.
- Treating `{ ...obj }` as a deep clone.
- Forgetting that a small closure can retain a large object graph.
- Keeping global caches forever because they are convenient.
- Assuming removing DOM from the page removes every JavaScript reference to it.
- Thinking `WeakMap` is a general cache eviction strategy. It only helps when object-key lifetime matches the cached metadata lifetime.

## 13. Practice

1. Explain reachability without saying "the engine knows what I need."
2. Show how two variables can reference the same object.
3. Find the retaining path in a listener or timer leak.
4. Explain why a module-level cache can be an application memory leak.
5. Connect this note to React effect cleanup.
6. Why is `new Array(5)` slower to access later than `[1, 2, 3, 4, 5]`?
7. When would you use a `WeakRef` over a `WeakMap`?

<details>
<summary>Show answer</summary>

1. Reachability means an object can be reached from roots such as globals, active stack frames, closures, host callbacks, DOM references, or framework caches. If a reachable path exists, the object must stay alive.

2. `const a = {}; const b = a;` makes `a` and `b` hold references to the same object. `b.name = "x"` is visible through `a.name`.

3. In a listener leak, the retaining path might be `window -> resize listener list -> handleResize function -> closed-over component data`. Removing the listener breaks the host reference so the closed-over data can be collected when nothing else reaches it.

4. A module-level cache is reachable for as long as the module instance is reachable. If it grows with every search query or user id and never evicts, old data stays alive even when it has no business value.

5. React effect cleanup removes host/runtime references: event listeners, timers, subscriptions, sockets, and in-flight request callbacks. Cleanup is what aligns component lifetime with external resource lifetime.

6. `new Array(5)` creates an array of size 5 filled with holes (`HOLEY_SMI_ELEMENTS`). Accessing a holey array is slower because the engine must check the prototype chain (`Array.prototype`, `Object.prototype`) for an indexed property before returning `undefined`, which disables the packed fast path. `[1, 2, 3, 4, 5]` is `PACKED_SMI_ELEMENTS` with direct fast-path index access. Note `new Array(5).fill(0)` is packed, so preallocate-and-fill is fine.

7. Use a `WeakMap` when you want to associate metadata with a key object, and have that metadata automatically cleared when the key object is collected. Use a `WeakRef` when you want to hold a reference to an object itself without keeping it alive (e.g., in a cache values mapping, or canvas buffers) and retrieve it if it still exists.

</details>

## Related Notes

- [[13 - Performance and Memory/01 - Memory Management|Memory Management]]
- [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
- [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]
