---
tags: [javascript, runtime, runtime-foundations-checklist]
module: "02 - JavaScript Runtime Foundations"
priority: must-know
status: not-started
---

# Runtime Foundations Checklist

Use this checklist after studying the runtime foundation module. Do not mark an item complete because the sentence sounds familiar. Mark it complete only when you can explain it, trace it, and connect it to a production bug.

## 1. ECMAScript vs JavaScript

- [ ] I can explain ECMAScript as the language specification and JavaScript as practical implementations in host environments.
- [ ] I can list language features defined by ECMAScript: types, objects, functions, modules, promises, jobs, and evaluation algorithms.
- [ ] I can list host/runtime features not defined by ECMAScript: DOM, `window`, `document`, `fetch`, timers, storage, rendering, Node.js APIs.
- [ ] I can explain why the same JavaScript syntax can run in browser, Node.js, workers, edge runtimes, and React Native with different available APIs.
- [ ] I can explain why TypeScript types do not exist at runtime unless I add runtime validation.
- [ ] I can explain what `globalThis` resolves to in different Next.js execution environments (server node, client browser) and how it helps write isomorphic code.
- [ ] I can name the TC39 stages (0–4, including 2.7) and explain why stage 3 is not "safe to rely on."
- [ ] I can explain what WinterTC (Ecma TC55) standardizes and why `fetch` now runs in Node, Deno, Bun, and edge runtimes.

## 2. JavaScript Engine and Runtime

- [ ] I can define engine vs runtime in one sentence.
- [ ] I can name examples of engines: V8, SpiderMonkey, JavaScriptCore.
- [ ] I can name examples of runtimes: browser, Node.js, edge runtime, React Native.
- [ ] I can describe the broad engine pipeline: parse, compile/baseline execute, profile, optimize, and deoptimize.
- [ ] I can explain why event loops, DOM, network, and file APIs belong to the runtime/host layer, not the engine alone.
- [ ] I can connect bundle size to parse/compile cost and startup performance.
- [ ] I can explain why WebAssembly (Wasm) compilation bypasses V8's tokenizing/parsing pipeline, and why Wasm never de-optimizes.
- [ ] I can name V8's tiers (Ignition, Sparkplug, Maglev, TurboFan/Turboshaft) and explain why tiered compilation exists.
- [ ] I can explain hidden classes, shape transitions, and inline caches, including monomorphic vs polymorphic vs megamorphic sites.
- [ ] I can explain why `delete obj.key` can be worse than `obj.key = undefined` in hot paths, and the semantic tradeoff between them.

## 3. Execution Context

- [ ] I can explain execution context as the runtime record for currently evaluating code.
- [ ] I can name key parts: lexical environment, variable environment, `this` binding, realm, and evaluation state.
- [ ] I can explain preparation vs execution without saying code is physically moved.
- [ ] I can connect execution context to hoisting, TDZ, closures, `this`, and stack traces.
- [ ] I can explain how React render functions create fresh local bindings on every render.
- [ ] I can explain what happens to an async function continuation at `await`.
- [ ] I can explain how V8 implements block scoping using separate LexicalEnvironment and VariableEnvironment records inside a single execution context.

## 4. Call Stack

- [ ] I can draw a stack for three nested function calls.
- [ ] I can explain last-in, first-out execution.
- [ ] I can explain run-to-completion.
- [ ] I can explain why long synchronous work blocks input and rendering.
- [ ] I can identify stack overflow risk in recursive processing.
- [ ] I can read a stack trace and separate sync call path from async history.
- [ ] I can explain why stack depth limits differ across engines and why proper tail calls (ES2015, JavaScriptCore-only) cannot be relied on for recursion safety.

## 5. Memory Heap

- [ ] I can explain object references and why two variables can point to the same object.
- [ ] I can explain reachability and why garbage collection cannot free reachable objects.
- [ ] I can identify common frontend retaining paths: event listeners, timers, closures, subscriptions, detached DOM nodes, and caches.
- [ ] I can explain why object spread is shallow.
- [ ] I can explain why module-level caches need ownership and eviction policy.
- [ ] I can connect effect cleanup to memory lifetime.
- [ ] I can explain what a `WeakRef` is and how `FinalizationRegistry` helps clean up cache keys.
- [ ] I can explain V8 Array Element Kinds (SMI vs. Double vs. Elements) and the performance cost of holey arrays.
- [ ] I can sketch generational GC: young generation (Scavenger, minor GC) vs old generation (Mark-Compact, major GC) and why "most objects die young" matters.

## 6. Realm, Agent, and Job Queue

- [ ] I can explain a Realm as a world with its own global object and intrinsic constructors.
- [ ] I can explain why `Array.isArray(value)` is safer than `value instanceof Array` across iframes.
- [ ] I can explain an Agent as an independent execution unit and connect it to workers.
- [ ] I can explain the security requirements (COOP/COEP headers) to enable `SharedArrayBuffer` in the browser.
- [ ] I can explain similar-origin window agents and browser process isolation boundaries.
- [ ] I can explain that promise reactions are scheduled jobs and do not run synchronously inside `.then`.
- [ ] I can explain how promise jobs relate to browser microtask processing.
- [ ] I can explain how unbounded promise/microtask work can starve rendering.
- [ ] I can list what structured clone preserves (Map, Set, Date, ArrayBuffer, cycles), what throws (functions, DOM nodes), and what loses identity (class instances).
- [ ] I can explain transfer vs copy for `ArrayBuffer` in `postMessage` and what "detached" means for the sender.
- [ ] I can explain why `Atomics.wait` throws on the main thread but works in workers.

## Production Debugging Drills

For each drill, write the likely layer: language, engine, host/runtime, framework, or application.

1. `window is not defined` in a Next.js route.
2. `setTimeout(..., 0)` runs after a promise callback.
3. A deeply nested comment tree crashes with maximum call stack size exceeded.
4. A modal leaks memory after being opened and closed repeatedly.
5. `value instanceof Array` is false for data from an iframe.
6. Typing freezes while filtering a large array.
7. An async function logs before and after `await` in surprising order.
8. `SharedArrayBuffer is not defined` when running worker communication.
9. Array lookup performance drops significantly after assigning an index way out of bounds (e.g. `arr[1000]`).
10. `worker.postMessage(order)` throws `DataCloneError` after a refactor added an `onSuccess` callback to the order object.

<details>
<summary>Show answer</summary>
<ol>
<li><code>window is not defined</code> in Next.js is usually a host/framework boundary bug: browser-only API read during server execution or module evaluation.</li>
<li>A timer after a promise callback is host/event-loop plus ECMAScript job behavior: the promise reaction runs through microtask processing before the later timer task.</li>
<li>A maximum-call-stack crash is call stack/language execution: recursive processing pushed too many execution contexts.</li>
<li>A modal leak is memory/reachability: an event listener, timer, subscription, cache, closure, request callback, or DOM reference still reaches old modal data.</li>
<li>Cross-iframe <code>instanceof Array</code> is a realm issue: each realm has its own intrinsic constructors. Prefer <code>Array.isArray</code>.</li>
<li>Typing freeze is usually main-thread CPU/rendering pressure: synchronous filtering, sorting, layout, or rendering work blocks input and paint.</li>
<li>Logs around <code>await</code> are promise-job/async-continuation behavior: code before <code>await</code> runs synchronously; code after <code>await</code> resumes later when the awaited promise settles.</li>
<li><code>SharedArrayBuffer is not defined</code> is a host/runtime security context issue: missing COOP/COEP isolation headers.</li>
<li>Array lookup drop is an engine optimization issue: the array transitioned to <code>HOLEY_ELEMENTS</code> kind, so element access loses the packed fast path (the engine must check the prototype chain for indexed properties and may fall back to dictionary-mode elements).</li>
<li><code>DataCloneError</code> is host/runtime plus application layer: structured clone cannot serialize functions, so the callback property makes the whole message unclonable. Fix at the application layer: send plain data, keep callbacks on the sending side, and signal completion with a response message.</li>
</ol>
</details>

## Code To Trace

```js
console.log('A');

setTimeout(() => console.log('timer'), 0);

Promise.resolve().then(() => {
  console.log('promise 1');
  queueMicrotask(() => console.log('microtask'));
});

console.log('B');
```

Expected browser output:

```txt
A
B
promise 1
microtask
timer
```

Explain it with these terms: call stack, run-to-completion, promise job, microtask checkpoint, host task.

<details>
<summary>Show answer</summary>

`A` logs first because it is synchronous script evaluation on the current call stack. `setTimeout` schedules a host timer task for later. `Promise.resolve().then(...)` registers a promise reaction job, but it does not run immediately. `B` logs while the current script still runs.

After the stack clears, the browser performs a microtask checkpoint. The promise reaction logs `promise 1` and queues another microtask with `queueMicrotask`. Because the microtask queue is drained before the browser moves to the next task, `microtask` logs before `timer`. The timer callback runs later as a host task.

Final output:

```txt
A
B
promise 1
microtask
timer
```

</details>

## Interview Readiness

- [ ] I can answer "what happens when JavaScript runs code?" in 2 minutes.
- [ ] I can answer "engine vs runtime" in 30 seconds.
- [ ] I can correct "`setTimeout` is JavaScript" accurately and respectfully.
- [ ] I can connect execution context to closures and hoisting.
- [ ] I can connect call stack to UI responsiveness.
- [ ] I can connect heap reachability to React cleanup.
- [ ] I can connect realms to iframes and workers.
- [ ] I can connect memory safety to `WeakRef` and finalizers.
- [ ] I can explain `SharedArrayBuffer` security requirements and COOP/COEP.
- [ ] I can name V8's compilation tiers and explain hidden classes and inline caches without hand-waving.
- [ ] I can explain structured clone limits and when to transfer instead of copy.
- [ ] (deep-dive) I can correct "the interpreter loops over the bytecode" with threaded dispatch, and explain why a function called once can still reach TurboFan.

<details>
<summary>Show answer</summary>

A strong two-minute answer:

JavaScript source is parsed and executed by an engine inside a host runtime. The engine evaluates code through execution contexts on a call stack, creates bindings in lexical/variable environments, allocates objects on the heap, and uses garbage collection for unreachable objects. The host runtime provides APIs such as DOM, timers, fetch, storage, files, workers, and event-loop integration. Synchronous code runs to completion on the stack. Promise reactions and async continuations are scheduled as jobs that browsers process through microtask checkpoints. Host callbacks such as timers and UI events run as tasks. In frontend work, this model explains why long CPU work freezes input, why promises run before timers, why `window` fails on the server, why cleanup affects memory, why workers/realms introduce boundaries, how security concerns disable shared buffers by default, and how V8's optimization kinds affect performance.

</details>

## Related Notes

- [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]]
- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]
- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]
- [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]
- [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]]
- [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
