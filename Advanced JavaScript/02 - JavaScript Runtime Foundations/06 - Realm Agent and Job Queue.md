---
tags: [javascript, runtime, realm-agent-and-job-queue]
module: "02 - JavaScript Runtime Foundations"
priority: important
status: not-started
---

# Realm Agent and Job Queue

## Maturity Target

- Priority: #important
- Study time: 50-70 minutes
- Outcome: explain realms, agents, jobs, promise ordering, cross-realm bugs, and worker boundaries.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)
- [HTML Living Standard: event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [MDN Web Workers API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API)
- [MDN: The structured clone algorithm](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API/Structured_clone_algorithm)
- [MDN Atomics](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Atomics)
- [TC39 ShadowRealm proposal](https://github.com/tc39/proposal-shadowrealm)
- [V8 API reference: MicrotaskQueue](https://v8.github.io/api/head/classv8_1_1MicrotaskQueue.html)
- [Node.js: The event loop, timers, and process.nextTick()](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick)
- [MDN: MutationObserver](https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver)

## 1. Simple Explanation

A Realm is a JavaScript world with its own global object and intrinsic objects. An Agent is an independent execution unit with its own execution context stack. A Job is a queued unit of ECMAScript work, such as a promise reaction.

These terms are more advanced, but they explain real bugs involving iframes, workers, promises, and microtask ordering.

## 2. Why It Matters

Runtime foundations are not only about the main thread. Modern frontend apps use:

- iframes and embedded widgets.
- micro-frontends.
- Web Workers.
- Service Workers.
- promise-heavy data flows.
- React and framework schedulers.

Realms explain cross-window identity surprises. Agents explain separate execution units. Jobs explain why promise callbacks run after current synchronous code and before many host tasks.

## 3. Realm

Each Realm has its own:

- Global object.
- Intrinsic constructors such as `Array`, `Object`, `Function`, and `Promise`.
- Associated global environment.

This is why constructor-based checks can fail across iframes.

```js
// In a page with an iframe:
const iframeArray = new iframe.contentWindow.Array(1, 2, 3);

console.log(iframeArray instanceof Array); // false in many cross-realm cases
console.log(Array.isArray(iframeArray));   // true
```

`instanceof Array` checks against the current realm's `Array.prototype`. The iframe array was created with the iframe realm's `Array` constructor. `Array.isArray` is the safer cross-realm check.

## 4. Agent

An Agent is the spec model for an independent JavaScript execution unit. Within an Agent, execution is strictly single-threaded and runs a single execution context stack (call stack).

In browser terms:
* **Window Agents**: Modern browsers use Process-per-Site isolation. Pages or iframes sharing the same origin and browsing context may share a single window Agent. Cross-origin pages or iframes run in entirely separate similar-origin window agents (or distinct processes at the OS level).
* **Worker Agents**: Each Web Worker and Service Worker runs as a separate Agent with its own stack and message loop.

```ts
// main thread
const worker = new Worker(new URL('./worker.ts', import.meta.url));

worker.postMessage(largeInput);

worker.onmessage = event => {
  // This callback runs back on the main thread after the worker posts a result.
  renderResult(event.data);
};
```

```ts
// worker.ts
self.onmessage = event => {
  // Heavy CPU work happens away from the main UI thread.
  const result = expensiveTransform(event.data);
  self.postMessage(result);
};
```

The practical lesson: workers can protect UI responsiveness, but they introduce serialization, messaging, lifecycle, and bundling concerns.

### Worker Tradeoffs

Workers are a good fit for CPU-heavy work that can be isolated from the DOM:

- parsing large files.
- image processing.
- search indexing.
- expensive data transforms.
- compression or crypto-style work when appropriate APIs are available.

Workers are not a magic speed button:

- They cannot directly access the DOM.
- Data is copied or transferred through structured cloning/transferables.
- Startup and message overhead can exceed the benefit for small tasks.
- Error handling and cancellation need explicit protocol design.

### Structured Clone Limits

`postMessage` serializes data with the **structured clone algorithm** — deeper than JSON (it handles `Map`, `Set`, `Date`, `RegExp`, `ArrayBuffer`, typed arrays, and cyclic references), but with hard limits:

- Functions and DOM nodes throw `DataCloneError`.
- Class instances arrive as plain objects: own data properties survive, but the prototype (methods, getters, `instanceof` identity) is lost.
- Property descriptors, getters/setters, and symbols are not preserved.

```ts
class Order {
  constructor(public items: Item[]) {}
  total() { return this.items.reduce((sum, i) => sum + i.price, 0); }
}

worker.postMessage(new Order(items));      // Arrives as { items: [...] } — no total().
worker.postMessage({ onDone: () => {} });  // Throws DataCloneError: functions can't be cloned.
```

Fix: send plain serializable data and rehydrate on arrival.

```ts
// main thread
worker.postMessage({ type: 'calc-total', items });

// worker.ts
self.onmessage = event => {
  if (event.data.type === 'calc-total') {
    const order = new Order(event.data.items); // Rehydrate behavior worker-side.
    self.postMessage({ type: 'total', value: order.total() });
  }
};
```

### Transfer vs Copy

Structured cloning *copies*. For large binary data, copying is the cost that kills the win. **Transferables** move ownership instead:

```ts
const buffer = new ArrayBuffer(100_000_000); // ~100 MB of pixel data.

// Copy: main thread keeps its buffer, worker gets a duplicate. Slow for 100 MB.
worker.postMessage({ pixels: buffer });

// Transfer: zero-copy ownership move. Fast even for 100 MB.
worker.postMessage({ pixels: buffer }, [buffer]);

console.log(buffer.byteLength); // 0 — the source is detached ("neutered").
```

After a transfer, the sender's buffer is detached: `byteLength` becomes 0 and any access to its contents fails. Transfer when the sender no longer needs the data (file parsing, image pixels, audio buffers); clone when both sides do.

### Agent Cluster & Shared Memory Security

Multiple Agents can be grouped into an **Agent Cluster** which allows them to share memory directly using a `SharedArrayBuffer`. Unlike structured cloning (which deep-copies data), this enables zero-copy shared memory concurrency.

However, in modern browsers, `SharedArrayBuffer` is **disabled by default** to prevent side-channel timing attacks (such as Spectre) that could read cross-origin process memory.

To re-enable it, the host server must send specific HTTP headers to put the browser in a **cross-origin isolated** state:

```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

* **COOP (`Cross-Origin-Opener-Policy`)** isolates your tab process from other window contexts (popups).
* **COEP (`Cross-Origin-Embedder-Policy`)** blocks cross-origin resources from loading on your page unless they explicitly allow it via CORS or CORP headers.

Production check at runtime:
```js
if (window.crossOriginIsolated) {
  // SharedArrayBuffer can be instantiated safely
  const sharedBuffer = new SharedArrayBuffer(1024);
} else {
  // Fallback to message-copying via standard postMessage
}
```

**Atomics.** Once memory is shared, plain reads and writes race. The ECMAScript `Atomics` object provides race-free operations on shared typed arrays (`Atomics.load`, `Atomics.store`, `Atomics.add`, `Atomics.compareExchange`) plus `Atomics.wait`/`Atomics.notify` for blocking coordination between agents. `Atomics.wait` throws a `TypeError` on the main thread — the spec marks the main agent as "cannot block" because a blocked main thread would freeze rendering and input for the whole page; only workers may block.

> [!tip] ShadowRealm: the future spec-level fresh realm
> The TC39 **ShadowRealm** proposal (currently Stage 2.7 — a proposal, not shipped ECMAScript) would let code synchronously create a fresh realm with its own globals and intrinsics — the spec-level answer to "run third-party code in an isolated world" that today requires iframes or workers. Callables cross the boundary only as wrapped functions exchanging primitives. Track its stage before mentioning it as available.

## 5. Job Queue and Promise Reactions

ECMAScript defines jobs for work that must happen later, especially promise reactions. Browsers integrate promise jobs into their microtask processing.

```js
console.log('A');

Promise.resolve().then(() => {
  console.log('promise');
});

console.log('B');

// Output:
// A
// B
// promise
```

The `.then` callback is not called synchronously. It is scheduled as a promise reaction job and runs after the current synchronous script finishes.

### Who Owns the Queue

This is the question that decides whether your mental model of async JavaScript is a diagram or a mechanism, and the answer is a split:

| Piece | Owned by | Consequence |
| --- | --- | --- |
| The job (microtask) queue | The **engine** — jobs are ECMAScript, so V8 must implement them regardless of host | Microtask ordering is identical in Chrome, Node, Deno and Bun. It is language-level, not runtime-level |
| The event loop, task queues, timers | The **host** — HTML Living Standard in browsers, libuv in Node | Task ordering, phases and `setTimeout` clamping differ per host |

So how does a host enqueue into a queue the engine owns? Not by reaching into internals — **the engine exposes an embedder API for exactly this.** V8's `v8::MicrotaskQueue::EnqueueMicrotask` and `v8::Isolate::EnqueueMicrotask` exist so that Blink and Node's bindings layer can schedule microtasks, and V8's `MicrotasksPolicy` lets the embedder choose who triggers the drain — with the explicit policy, the host calls `PerformMicrotaskCheckpoint()` itself at the point in its loop where the spec says a microtask checkpoint belongs. That is the whole integration: the engine owns the queue and the draining semantics, the host owns *when* the checkpoint happens.

Two facts fall out of this that are worth having ready:

- **`queueMicrotask()` is a host-provided function into an engine-owned queue.** It is defined by the HTML spec on `Window`/`WorkerGlobalScope`, not by ECMAScript — but it routes to the same queue promise reactions use, which is why it interleaves with `.then` in registration order rather than forming a second queue.
- **`process.nextTick()` is not on V8's microtask queue at all.** It is a separate list that Node manages itself, drained *before* the V8 microtask queue on every checkpoint. So Node has three levels, not two: nextTick queue → V8 microtask queue → libuv phases. See [[09 - Event Loop Advanced/09 - Node.js Event Loop vs Browser|Node.js Event Loop vs Browser]].

> [!warning] "ECMAScript features are microtasks, host APIs are tasks" has a standing exception
> `MutationObserver` is defined by the DOM spec — unambiguously a host API — and is explicitly specified to deliver its records at a microtask checkpoint, so it runs before the next task and before the next paint. The rule that actually holds is: a microtask is whatever a spec says runs at the microtask checkpoint. Usually that is the language's own deferred work; `MutationObserver` is the common counterexample an interviewer can use to test whether you memorized a slogan.

## 6. Job Starvation Bug

```js
function keepScheduling() {
  Promise.resolve().then(keepScheduling);
}

keepScheduling();
```

This keeps adding promise jobs. In a browser, unbounded microtask work can prevent the host from reaching rendering or user-input tasks. The symptom looks like a frozen page even though each individual callback is small.

Safer pattern:

```js
let remaining = 10_000;

function processChunk() {
  const end = Math.max(remaining - 500, 0);

  while (remaining > end) {
    remaining -= 1;
    // Do a small piece of work.
  }

  if (remaining > 0) {
    // A task boundary gives the browser a chance to process input and rendering.
    setTimeout(processChunk, 0);
  }
}

processChunk();
```

Edge case: switching from promises to `queueMicrotask` does not fix starvation if you keep scheduling unbounded microtasks. To let the browser handle input or rendering, yield to a task boundary, `requestAnimationFrame`, idle work, a worker, or a smaller UX flow.

## 7. Cross-Realm Micro-Frontend Bug

```js
function validatePayload(payload) {
  if (!(payload.items instanceof Array)) {
    throw new Error("items must be an array");
  }
}
```

This can fail when `payload.items` comes from an iframe or embedded remote with a different realm. The array is real, but it was created by another realm's `Array` constructor.

Safer check:

```js
function validatePayload(payload) {
  if (!Array.isArray(payload.items)) {
    throw new Error("items must be an array");
  }
}
```

> [!tip] Tradeoff
> `Array.isArray` solves array branding across realms, but it does not validate the contents. For API or micro-frontend boundaries, still validate item shape.

## 8. Interview Answer

**Short version:** A Realm has its own globals and intrinsics, an Agent is an independent execution unit, and Jobs are queued ECMAScript work such as promise reactions.

**Deeper version:** Realms explain why values from iframes can fail constructor checks like `instanceof Array`. Agents explain why workers can run JavaScript separately from the main thread. Jobs explain promise ordering: a `.then` callback runs after the current synchronous stack finishes, and browsers process promise jobs through microtask checkpoints. The host event loop and ECMAScript job model meet at that boundary.

## 9. Common Mistakes

- Assuming all arrays share the same `Array` constructor across iframes.
- Calling every async callback a promise job.
- Forgetting that workers do not share normal objects with the main thread by reference.
- Creating infinite promise chains that starve rendering.
- Mixing ECMAScript job terminology with browser task terminology without explaining the boundary.
- Assuming workers share normal object references with the main thread.
- Sending class instances through `postMessage` and expecting methods to survive. Structured clone keeps data, not prototypes.
- Copying huge `ArrayBuffer`s through `postMessage` when transferring ownership would be zero-copy.
- Calling `Atomics.wait` on the main thread — it throws; only workers may block.

## 10. Practice

1. Why can `iframeArray instanceof Array` be false?
2. What is safer for cross-realm array detection?
3. What does a Web Worker buy you, and what does it cost?
4. Why does `Promise.resolve().then(fn)` not call `fn` synchronously?
5. Explain how a microtask loop can freeze a page.
6. Why is `SharedArrayBuffer` disabled by default in browsers, and what headers are required to enable it?
7. What survives `postMessage`, what throws, and what loses its identity?
8. When should you transfer an `ArrayBuffer` instead of cloning it, and what happens to the source?

<details>
<summary>Show answer</summary>
<ol>
<li>The value was created in another realm, so its prototype chain points to that realm's <code>Array.prototype</code>, not the current realm's <code>Array.prototype</code>. <code>instanceof Array</code> checks against the current constructor/prototype relationship.</li>
<li><code>Array.isArray(value)</code> is safer because it checks the array brand rather than relying on the current realm's constructor.</li>
<li>A Worker moves CPU work away from the main UI execution unit, improving responsiveness. It costs message passing, structured clone or transfer design, separate lifecycle, no direct DOM access, bundling complexity, and explicit error/cancellation protocol.</li>
<li><code>.then(fn)</code> registers a promise reaction. Even for an already fulfilled promise, the reaction runs later as a promise job/microtask after the current synchronous stack finishes.</li>
<li>If each microtask schedules another microtask, the microtask queue may never drain. The browser keeps processing microtasks and may not reach later tasks or rendering opportunities, so the page appears frozen.</li>
<li><code>SharedArrayBuffer</code> is disabled by default to prevent Spectre-style side-channel CPU timing attacks that could read memory across processes. To enable it, the host server must send <code>Cross-Origin-Opener-Policy: same-origin</code> (COOP) and <code>Cross-Origin-Embedder-Policy: require-corp</code> (COEP) headers to opt into cross-origin isolation.</li>
<li>Plain objects, arrays, <code>Map</code>, <code>Set</code>, <code>Date</code>, <code>RegExp</code>, <code>ArrayBuffer</code>, typed arrays, and cyclic references survive structured clone. Functions and DOM nodes throw <code>DataCloneError</code>. Class instances survive as plain objects: own data properties arrive, but the prototype chain — methods, getters, <code>instanceof</code> identity — is lost. Fix: send plain data and rehydrate into classes on the receiving side.</li>
<li>Transfer when the data is large and the sender no longer needs it — parsed file bytes, image pixels, audio buffers. <code>postMessage(data, [buffer])</code> moves ownership with zero copy; the sender's buffer is detached (<code>byteLength</code> becomes 0, contents inaccessible). Clone when both sides still need the data, and accept the copy cost.</li>
</ol>
</details>

## Related Notes

- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]
