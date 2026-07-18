---
tags: [javascript, dom, workers, performance]
module: "19 - DOM and Browser APIs"
priority: important
status: not-started
aliases: [Web Workers, Transferables]
---

# Web Workers and Offloading Work

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: you can explain what workers can and cannot touch, structured clone vs transferables, and articulate when a worker is the right fix versus chunking on the main thread.
- Production signal: you've moved a real CPU-bound task (parsing, diffing, compression, search indexing) off the main thread and measured the win.
- Dependencies: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]], [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]

## Source Anchors

- [MDN - Using Web Workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Using_web_workers)
- [HTML Living Standard - Workers](https://html.spec.whatwg.org/multipage/workers.html)
- [MDN - Structured clone algorithm](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Structured_clone_algorithm)
- [MDN - Transferable objects](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Transferable_objects)
- [web.dev - Off the main thread](https://web.dev/articles/off-main-thread)

## 1. Concept

JavaScript's main thread runs your code, layout, paint, and input handling. A **Web Worker** is a separate thread with its own event loop, global scope (`self`), and memory — communicating with the page only via message passing.

```js
// main.js
const worker = new Worker(new URL("./search.worker.js", import.meta.url), { type: "module" });
worker.postMessage({ query: "phone", products });
worker.onmessage = (e) => renderResults(e.data);
worker.onerror = (e) => reportError(e);

// search.worker.js
self.onmessage = (e) => {
  const results = heavySearch(e.data.products, e.data.query);
  self.postMessage(results);
};
```

Hard boundaries: workers have **no DOM**, no `window`, no `document` — but they do have `fetch`, timers, IndexedDB, `caches`, WebSocket, and `OffscreenCanvas`. No shared objects: each `postMessage` payload is deep-copied via **structured clone** (unless transferred).

## 2. Why It Matters

A task longer than ~50ms on the main thread makes input handling wait — that's the definition of a "long task" and it directly damages INP ([[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals]]). There are exactly two remedies: break the work up (chunking/yielding) or move it off the thread (worker). Seniors are expected to know which one fits, and that "make it async with a promise" does *neither* — `await` doesn't move CPU work anywhere ([[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async]]).

## 3. Structured Clone vs Transferables

**Structured clone** (the same algorithm behind `structuredClone()`, IndexedDB, and `postMessage`) copies deeply: objects, arrays, Map, Set, Date, RegExp, Blob, File, ArrayBuffer, typed arrays. It does **not** clone functions, DOM nodes, class prototypes (instances arrive as plain objects), or property accessors — attempting functions/DOM throws `DataCloneError`.

Copying is O(size): posting a 200MB ArrayBuffer clones 200MB. **Transferables** fix this — ownership moves instead:

```js
const buffer = new ArrayBuffer(200 * 1024 * 1024);
worker.postMessage({ buffer }, [buffer]);   // transfer list
console.log(buffer.byteLength);              // 0 — neutered on this side
```

Transfer is O(1) — pointer handoff. Transferable types include `ArrayBuffer`, `MessagePort`, `ImageBitmap`, `OffscreenCanvas`, and streams. The sender's object becomes unusable ("detached"), which is the safety mechanism replacing locks.

> [!warning] postMessage cost is part of the math
> If serializing input + deserializing output costs more than the computation, the worker makes things *slower* — a common outcome when shipping big object graphs for small tasks. Send compact data (typed arrays, ids), transfer buffers, or keep long-lived state *inside* the worker and send small queries.

## 4. Decision Framework: Worker vs Chunking

| Situation | Right tool |
| --- | --- |
| Pure CPU work, seconds long (parse 50MB CSV, compress image, fuzzy-search 100k records) | Worker |
| Work needs the DOM (measure, mutate) | Can't leave the thread — chunk with `requestAnimationFrame`/`scheduler.yield()`-style slices |
| Work is I/O-bound (fetch, IndexedDB) | Neither — it's already async; the thread isn't the problem |
| Many small updates causing jank | Batch/debounce first; workers add latency per message |
| Needs shared mutable state at high frequency | `SharedArrayBuffer` + `Atomics` (requires cross-origin isolation headers) — rare, last resort |

Chunking sketch for DOM-bound work:

```js
async function processInChunks(items, fn, chunkSize = 200) {
  for (let i = 0; i < items.length; i += chunkSize) {
    items.slice(i, i + chunkSize).forEach(fn);
    // Yield so input/rendering can run between chunks.
    await new Promise((r) => setTimeout(r, 0));
  }
}
```

Tradeoff vs worker: chunking keeps total main-thread cost the same (just spread out) and code simple; a worker removes the cost from the thread entirely but adds messaging latency, a second file/bundle entry, and no-DOM constraints.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: client-side export of a 300k-row table to CSV freezes the UI for 4 seconds.

Buggy version:

```js
exportButton.addEventListener("click", () => {
  const csv = rows.map((r) => toCsvLine(r)).join("\n"); // 4s of CPU
  download(new Blob([csv], { type: "text/csv" }));
});
```

Trace: click handler starts → 4s synchronous string building → no clicks, no scroll, no paint; the browser may show "page unresponsive". Everything else was already async — this is pure CPU, so promises won't help.

Production-safe fix — worker + transfer back:

```js
// main
const worker = new Worker(new URL("./csv.worker.js", import.meta.url), { type: "module" });
exportButton.addEventListener("click", () => {
  exportButton.disabled = true;
  worker.postMessage(rows);                       // structured clone (see tradeoff)
  worker.onmessage = ({ data: buffer }) => {
    download(new Blob([buffer], { type: "text/csv" }));
    exportButton.disabled = false;
  };
});

// csv.worker.js
self.onmessage = ({ data: rows }) => {
  const csv = rows.map(toCsvLine).join("\n");
  const buffer = new TextEncoder().encode(csv).buffer;
  self.postMessage(buffer, [buffer]);             // transfer: O(1), no copy back
};
```

Tradeoffs, stated honestly: cloning 300k row objects *into* the worker isn't free (maybe 200-400ms — still a long task!). Better designs: keep the canonical rows in the worker/IndexedDB all along and query from it, or fetch the export server-side. The return path transfers the encoded buffer, which is the cheap direction. Also: workers are per-file bundle entries — Vite/webpack support the `new Worker(new URL(...), ...)` pattern natively, but Comlink is worth adopting once you exchange more than one message type, because hand-rolled request/response-over-postMessage grows correlation-id bookkeeping fast.

## 6. Ecosystem Notes

- **Comlink** wraps a worker in a Proxy so calls look like `await api.search(query)` — the postMessage plumbing disappears.
- **OffscreenCanvas** lets a worker render charts/WebGL without the DOM.
- React connection: heavy state derivations (`useMemo` computing a big filter/sort) still block the main thread — memoization dedupes work across renders, it doesn't make work cheap. Offload the computation and store the *result* in state.
- Don't confuse with [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers]] — those are network proxies with a lifecycle, not general compute threads.

## 7. Interview Answer

Short answer:

> Workers are separate threads with their own event loop and no DOM access, communicating by message passing. Messages are deep-copied with structured clone; large binary payloads should be transferred instead, which moves ownership in O(1) and detaches the source.

Deeper answer:

> The decision framework: worker for long pure-CPU work; chunking when the work needs the DOM; neither for I/O-bound tasks since async already covers those. The messaging cost bounds the win — if serialization exceeds computation, keep state inside the worker and exchange small messages. SharedArrayBuffer plus Atomics exists for genuine shared memory but requires cross-origin isolation and is a last resort.

## 8. Practice

1. <details><summary>"We made the sort async by wrapping it in a promise, but the UI still freezes." Why?</summary>Promises schedule *when* code runs; they don't change *where*. The sort still executes synchronously on the main thread once its microtask runs — one long task, same freeze. Fixes: chunk the sort with yields, or move it to a worker. (`await`ing doesn't split CPU work.)</details>

2. <details><summary>You postMessage a class instance `new Order(...)` with methods to a worker. What arrives?</summary>A plain object with the instance's own data properties — structured clone doesn't preserve prototypes or clone functions, so methods are gone (and posting an object that directly contains a function throws DataCloneError). Send plain data and re-hydrate (`new Order(data)` / `Object.assign`) inside the worker if behavior is needed.</details>

3. <details><summary>After `worker.postMessage({ buf }, [buf])`, main thread later calls `new Float64Array(buf)`. Result?</summary>TypeError — the ArrayBuffer was transferred, so the sender's reference is detached (`byteLength === 0`); constructing a view on a detached buffer throws. If both sides need the data, either clone (omit the transfer list) or use SharedArrayBuffer deliberately.</details>

4. <details><summary>Live search over 80k in-memory products janks on each keystroke. Sketch the worker architecture, including what NOT to send per keystroke.</summary>On startup, post the product list to the worker once (or have the worker load/index it from IndexedDB) and build an index there. Per keystroke, send only `{ id, query }` and receive top-N result ids; debounce input (~150ms) and drop stale responses by correlation id (latest-wins, same pattern as [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|race handling]]). Anti-pattern: re-sending the 80k array per keystroke — clone cost would dwarf the search.</details>

## Related Notes

- [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]
- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]]
- [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]]
- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[12 - Advanced Language Concepts/14 - Typed Arrays and Binary Data|Typed Arrays and Binary Data]]
- [[01 - Roadmap|Roadmap]]
