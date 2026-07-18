---
tags: [javascript, event-loop, nodejs, ssr]
module: "09 - Event Loop Advanced"
priority: important
status: not-started
aliases: [Node Event Loop, setImmediate, process.nextTick]
---

# Node.js Event Loop vs Browser

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can contrast the browser and Node event loops at overview depth, place `setImmediate` and `process.nextTick`, and say why it matters for SSR code paths.
- Production signal: you don't assume browser timing holds on the server, and you avoid `process.nextTick` starvation in Node request handlers.
- Dependencies: [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]], [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]

## Source Anchors

- [Node.js - The event loop](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick)
- [Node.js - Don't block the event loop](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop)
- [MDN - In depth: microtasks](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide/In_depth)
- [libuv - Design overview](https://docs.libuv.org/en/v1.x/design.html)

## 1. Concept

The browser and Node.js both run JavaScript on a single thread with an event loop, and both share the ECMAScript job (microtask) queue — so `Promise.then` and `queueMicrotask` behave the same. But the **host** differs: the browser's loop is defined by the HTML spec (tasks, microtasks, and a rendering step — [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]); Node's loop is built on **libuv** and organized into ordered *phases*, with no rendering step (there's no screen).

The shared rule that always holds: **the microtask queue is drained completely between each macro-step.** After every callback, all pending microtasks (promise jobs) run before the loop moves on. Everything else is host-specific.

## 2. Why It Matters

- Next.js and other SSR frameworks run your React/data code in **Node** (or an edge runtime), not the browser. Timing assumptions baked in the browser (`setTimeout` ordering, rendering frames) don't transfer — `requestAnimationFrame` doesn't exist server-side, and `setImmediate`/`process.nextTick` don't exist in the browser.
- `process.nextTick` starvation and phase ordering are classic Node interview and production gotchas for anyone writing server code.

## 3. Node's Phases (Overview)

libuv cycles through phases each loop iteration; the ones to know:

1. **timers** — `setTimeout`/`setInterval` callbacks whose time elapsed.
2. **pending callbacks** — some deferred system callbacks.
3. **poll** — retrieve new I/O events, run I/O callbacks (the phase where most of your file/network callbacks fire); may block here waiting for I/O.
4. **check** — `setImmediate` callbacks.
5. **close** — `close` event callbacks.

Two special queues run **between phases** and are drained after each callback, in this priority:

- **`process.nextTick` queue** — runs first, before other microtasks. Highest priority.
- **microtask queue** (promises) — runs after nextTick, before the loop continues.

So the ordering within a tick is: current callback → drain `process.nextTick` queue → drain promise microtasks → next phase.

## 4. setImmediate vs setTimeout(0) vs process.nextTick

```js
setTimeout(() => console.log("timeout"), 0);   // timers phase
setImmediate(() => console.log("immediate"));  // check phase
process.nextTick(() => console.log("nextTick")); // before either, this tick
Promise.resolve().then(() => console.log("promise")); // microtask, after nextTick

// Typical output: nextTick → promise → timeout → immediate
// (timeout vs immediate order at top level is NOT guaranteed; inside an I/O callback,
//  setImmediate reliably runs before setTimeout(0).)
```

- **`process.nextTick`**: runs before the loop continues *and* before promise microtasks — the earliest possible. Useful, but overuse starves the loop.
- **`setImmediate`**: runs in the *check* phase, after the current poll phase — "run after I/O, on the next iteration."
- **`setTimeout(fn, 0)`**: timers phase; at least the minimum delay, ordering vs `setImmediate` is nondeterministic at the top level.

> [!warning] process.nextTick starvation
> Because the entire `nextTick` queue drains before the loop proceeds to any phase, recursively scheduling `process.nextTick` can *starve* the event loop — I/O and timers never get a turn, and the server hangs. For "run soon but yield to the loop," prefer `setImmediate`. Reserve `nextTick` for genuinely must-run-before-anything cases (e.g., emitting an error after the current operation returns).

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an SSR data helper works in the browser during client-side testing but behaves differently under Next.js server rendering.

Buggy assumption — browser timing on the server:

```js
// A "yield to next frame" helper copied from client code
function afterPaint(cb) {
  requestAnimationFrame(() => cb());   // ❌ requestAnimationFrame is undefined in Node
}
// During SSR (Node), this throws ReferenceError, breaking the render.
```

And a Node-side batching helper that starves the loop:

```js
function drainQueue(items, handle) {
  if (!items.length) return;
  handle(items.shift());
  process.nextTick(() => drainQueue(items, handle));  // ❌ recursive nextTick → starves I/O
}
```

Trace: `requestAnimationFrame` only exists in the browser (tied to rendering); on the server it's undefined, so shared "isomorphic" code must not assume it. The `drainQueue` recursion re-enqueues on the nextTick queue, which the loop drains *entirely* before handling any incoming requests — under load the server stops responding while it chews through the queue.

Production-safe fix:

```js
// Isomorphic yield: guard browser-only APIs; use setImmediate on the server.
const yieldToLoop =
  typeof requestAnimationFrame !== "undefined"
    ? (cb) => requestAnimationFrame(cb)
    : (cb) => setImmediate(cb);   // Node: yields to the loop between iterations

function drainQueue(items, handle) {
  if (!items.length) return;
  handle(items.shift());
  setImmediate(() => drainQueue(items, handle));  // ✅ lets I/O/timers run between items
}
```

Tradeoffs: `setImmediate` yields to the loop (good for fairness) but is slightly slower per item than `nextTick` — for a small, bounded queue that must complete before returning, `nextTick` is fine; for large or unbounded work, yield with `setImmediate` (or offload to a worker thread) so the server stays responsive. The deeper lesson: isomorphic code must feature-detect host APIs rather than assume the browser; frameworks provide `useEffect` (client-only) precisely so DOM/timing code doesn't run during SSR ([[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|hydration]]).

## 6. Interview Answer

Short answer:

> Both browser and Node run JS single-threaded with an event loop and share the promise microtask queue, drained fully between macro-steps. The difference is the host: the browser's loop (HTML spec) has tasks, microtasks, and a rendering step; Node's loop (libuv) has ordered phases — timers, poll, check, close — and no rendering. `setImmediate` (check phase) and `process.nextTick` (before everything, this tick) are Node-only; `requestAnimationFrame` is browser-only.

Deeper answer:

> Within a Node tick the order is: current callback → drain the entire `process.nextTick` queue → drain promise microtasks → advance to the next phase. Recursively scheduling `nextTick` starves I/O and timers, hanging the server, so `setImmediate` is the "yield to the loop" primitive. This matters for SSR: your React and data code runs in Node under Next.js, where browser timing and `requestAnimationFrame` don't exist, so isomorphic code must feature-detect host APIs and effects that touch the DOM must be client-only.

## 7. Practice

1. <details><summary>Order the output: `setTimeout(()=>log('t'),0); setImmediate(()=>log('i')); process.nextTick(()=>log('n')); Promise.resolve().then(()=>log('p'));`</summary>`n`, `p`, then `t`/`i` in a nondeterministic order at the top level. `process.nextTick` drains first, then promise microtasks (`p`), then the loop enters phases — timer (`t`) and check (`i`) ordering isn't guaranteed at the top level (it depends on loop timing). Inside an I/O callback, `setImmediate` would reliably precede `setTimeout(0)`.</details>

2. <details><summary>Why can recursive `process.nextTick` hang a Node server but recursive `setImmediate` won't?</summary>The entire `nextTick` queue is drained before the loop advances to any phase, so continuously re-adding to it means the loop never reaches the poll phase to accept new I/O — requests never get processed, the server appears hung. `setImmediate` schedules into the check phase, so between each item the loop completes an iteration (poll, timers, etc.), letting I/O and timers run — the work is spread across iterations, keeping the server responsive.</details>

3. <details><summary>Shared "isomorphic" code calls `requestAnimationFrame`. What happens during SSR and how do you write it safely?</summary>`requestAnimationFrame` is a browser API tied to rendering; in Node it's undefined, so calling it during server rendering throws `ReferenceError` and breaks the SSR pass. Safe approaches: feature-detect (`typeof requestAnimationFrame !== 'undefined'`) and fall back to `setImmediate`/`setTimeout` on the server; or, in React, put DOM/timing code in `useEffect`, which never runs during SSR, so it only executes in the browser.</details>

4. <details><summary>What timing behavior is guaranteed to be identical in browser and Node?</summary>The ECMAScript microtask (promise job) queue semantics: `Promise.then`, `await` continuations, and `queueMicrotask` are drained completely after each macro-step in both hosts, in FIFO order. That's language-level, not host-level. Everything else — macrotask sources, phase ordering, `setImmediate`/`nextTick`, rendering/`requestAnimationFrame` — is host-specific and differs.</details>

## Related Notes

- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/04 - Timers|Timers]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[01 - Roadmap|Roadmap]]
