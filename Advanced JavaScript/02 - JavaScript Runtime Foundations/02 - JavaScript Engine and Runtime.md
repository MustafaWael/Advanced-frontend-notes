---
tags: [javascript, runtime, javascript-engine-and-runtime]
module: "02 - JavaScript Runtime Foundations"
priority: must-know
status: not-started
---

# JavaScript Engine and Runtime

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Outcome: explain what the engine executes, what the runtime adds, and why that distinction matters for performance and platform bugs.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)
- [MDN JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
- [V8 documentation](https://v8.dev/docs)
- [V8: Maglev - V8's fastest optimizing JIT](https://v8.dev/blog/maglev)
- [V8: Land ahoy - leaving the Sea of Nodes](https://v8.dev/blog/leaving-the-sea-of-nodes)
- [V8: Sparkplug - a non-optimizing JavaScript compiler](https://v8.dev/blog/sparkplug)

## 1. Simple Explanation

A JavaScript engine reads, compiles, optimizes, and executes ECMAScript. A JavaScript runtime is the engine plus the host environment around it: APIs, event loop integration, I/O, rendering, files, networking, and platform-specific globals.

Examples:

- V8 is an engine used by Chrome and Node.js.
- SpiderMonkey is Firefox's engine.
- JavaScriptCore is Safari's engine.
- Node.js is a runtime that embeds V8 and adds Node APIs.
- A browser runtime embeds an engine and adds Web APIs, DOM, events, storage, rendering, and networking.

## 2. Why It Matters

When performance or platform bugs appear, "JavaScript is slow" is too vague. You need to ask:

- Is the engine spending time parsing, compiling, or executing script?
- Is the browser spending time on style, layout, paint, or compositing?
- Is the runtime waiting on network, disk, timers, or task scheduling?
- Is React doing unnecessary render work because identities keep changing?
- Is the app shipping too much JavaScript to parse on startup?

The engine/runtime distinction turns vague blame into a debugging plan.

## 3. Accurate Mechanism

Modern engines usually follow this broad pipeline, with implementation details varying by engine:

```txt
source text
  -> parse/tokenize
  -> abstract syntax tree or internal representation
  -> bytecode or baseline execution
  -> profiling/type feedback
  -> optimized machine code for hot paths
  -> deoptimization when assumptions break
```

### V8's Named Tiers (One Concrete Example)

V8's current pipeline is the concrete version of that diagram. SpiderMonkey and JavaScriptCore have analogous tiers with different names.

| Tier | Role | Key facts |
| --- | --- | --- |
| **Ignition** | Interpreter | Compiles source to bytecode, interprets it, and collects type feedback (which shapes and types each site sees). |
| **Sparkplug** (2021) | Baseline compiler | Compiles bytecode to machine code in a single fast pass, no type feedback needed. Functions tier up from Ignition after roughly 8 invocations. |
| **Maglev** (Chrome M117) | Mid-tier optimizing compiler | Uses collected feedback to generate good-enough optimized code quickly: roughly 10x slower to compile than Sparkplug, roughly 10x faster than TurboFan. |
| **TurboFan** | Top-tier optimizing compiler | Spends real compile time on the hottest functions for peak machine code. Since 2025 its backend runs on **Turboshaft**, a CFG-based intermediate representation replacing the older Sea of Nodes design. |

**Deoptimization** applies to every optimizing tier: Maglev and TurboFan code embeds assumptions from type feedback ("this parameter is always a small integer", "this object always has this shape"). When an assumption breaks at runtime, the optimized code bails out back to a lower tier, and the function may be re-optimized later with updated feedback.

> [!tip] Why tiers exist
> Compilation speed and code quality trade off against each other. Most functions run a handful of times, so compiling them with TurboFan would cost more than it saves. Tiers let the engine spend compile time proportionally to how hot the code actually is — the same "optimize measured hot paths" discipline you should apply to your own code.

### WebAssembly (Wasm) Compilation Bypass
WebAssembly (`.wasm`) is a binary format that represents a stack-based virtual machine with statically typed instructions. 
When V8 loads a Wasm binary, it completely **bypasses the frontend compilation pipeline** (skipping tokenization, parsing, and AST generation). V8's baseline WebAssembly compiler (Liftoff) compiles the Wasm bytecode directly to native machine code in a single, fast pass, which is then further optimized in the background by TurboFan.
Because Wasm is statically typed, it **never de-optimizes (no JIT bailouts)**, enabling predictable, near-native execution performance for heavy calculations in the frontend (e.g. image filters, PDF layout calculations, or game engines).

The runtime wraps that engine with capabilities the engine itself does not own:

| Piece                      | Engine or runtime?    | Example                                      |
| -------------------------- | --------------------- | -------------------------------------------- |
| Parser/compiler            | Engine                | Parse `function add(a, b) { return a + b; }` |
| Execution context stack    | Engine/spec model     | Track active calls                           |
| Heap and garbage collector | Engine implementation | Allocate objects and functions               |
| DOM                        | Browser runtime       | `document.querySelector`                     |
| Timers                     | Host/runtime          | `setTimeout`, `setInterval`                  |
| Networking                 | Host/runtime          | `fetch`, Node HTTP APIs                      |
| File system                | Node runtime          | `fs.readFile`                                |
| Rendering pipeline         | Browser runtime       | style, layout, paint                         |

## 4. Mental Model

Engine equals language execution. Runtime equals engine plus environment capabilities.

The same engine can live in different runtimes. V8 in Chrome has browser APIs; V8 in Node.js has Node APIs. The same JavaScript syntax can run in both, but available globals and scheduling details differ.

## 5. Real Frontend Example

```tsx
function ProductList({ products }: { products: Product[] }) {
  // This transformation runs synchronously on the engine's call stack.
  // If products is huge and this runs on every render, the browser cannot paint
  // or handle input until the calculation finishes.
  const visibleProducts = products
    .filter(product => product.inStock)
    .toSorted((a, b) => a.price - b.price);

  return <Rows products={visibleProducts} />;
}
```

Improved version:

```tsx
function ProductList({ products }: { products: Product[] }) {
  const visibleProducts = React.useMemo(() => {
    // useMemo does not move work off the main thread.
    // It only skips recomputation when products is the same reference.
    return products
      .filter(product => product.inStock)
      .toSorted((a, b) => a.price - b.price);
  }, [products]);

  // If rendering many rows is the bottleneck, virtualization is still needed.
  return <VirtualizedRows products={visibleProducts} />;
}
```

## 6. Engine-Friendly Data Shape Example

```ts
// More predictable shape: every object has the same properties.
const users = apiUsers.map(user => ({
  id: user.id,
  name: user.name ?? null,
  email: user.email ?? null
}));

// Less predictable shape: each object may have a different property layout.
const usersWithChangingShape = apiUsers.map(user => {
  const result: Partial<User> = { id: user.id };
  if (user.name) result.name = user.name;
  if (user.email) result.email = user.email;
  return result;
});
```

> [!tip] Optimize measured hot paths only
> You do not need to micro-optimize every object shape. The production lesson is narrower: hot code benefits from predictable data, while premature engine-specific tuning can make code worse.

## 7. Hidden Classes and Inline Caches

The previous section showed the effect; this is the mechanism behind it — and the vocabulary interviewers listen for.

### Hidden Classes (Shapes / Maps)

JavaScript objects are spec-defined as dynamic property bags, but engines cannot afford a dictionary lookup on every property access. Instead, each object gets a **hidden class** (V8 calls them *maps*, SpiderMonkey *shapes*, JavaScriptCore *structures*) describing its property layout: which properties exist, in which order, at which memory offsets.

- Objects created with the same properties in the same order share one hidden class, so `user.name` compiles down to "read the value at offset 1" — as fast as a struct field access.
- Adding a property triggers a **shape transition** to a new hidden class. Adding the same properties in a *different order* produces a *different* chain of transitions, so the objects end up with divergent shapes even though they look identical.
- `delete obj.key` typically forces the object out of its shape chain entirely, often into slow dictionary mode.

```ts
// One shared hidden class: same properties, same order.
const a = { id: 1, name: "Nour" };
const b = { id: 2, name: "Omar" };

// Divergent shapes: same properties, different insertion order.
const c = { id: 3 };
c.name = "Sara";

const d = { name: "Ziad" };
d.id = 4; // d's shape chain differs from c's.
```

### Inline Caches (ICs)

Every property access and call site caches the hidden classes it has seen:

| IC state | Shapes seen | Speed |
| --- | --- | --- |
| **Monomorphic** | 1 | Fastest: one shape check, then direct offset access. |
| **Polymorphic** | 2–4 | Still fast: short chain of shape checks. |
| **Megamorphic** | Many | Falls off the fast path into generic lookup. |

This is why the type feedback the tiers collect matters: Maglev and TurboFan generate optimized code from IC states, and a site that stays monomorphic optimizes best.

### Traced Example: API Normalization

```ts
// Consistent shape: every normalized user has the same keys in the same order.
// The property accesses downstream stay monomorphic.
function normalizeUser(raw: RawUser) {
  return {
    id: raw.id,
    name: raw.name ?? null,
    email: raw.email ?? null,
  };
}

// Inconsistent shapes: conditional keys create several hidden classes.
// A hot loop reading user.email now sees multiple shapes -> polymorphic or worse.
function normalizeUserLoose(raw: RawUser) {
  const user: Partial<User> = { id: raw.id };
  if (raw.name) user.name = raw.name;
  if (raw.email) user.email = raw.email;
  return user;
}
```

> [!warning] delete vs setting undefined
> In hot code, `delete obj.key` can push the object into dictionary mode; assigning `obj.key = undefined` keeps the shape stable. Tradeoff: the two are not semantically identical — `'key' in obj`, `Object.keys(obj)`, and JSON serialization still see the `undefined` property. Choose `delete` when the semantics require the key to be truly gone; prefer normalized shapes with nullable fields when they do not.

The discipline from the previous section still rules: this explains *why* stable data shapes help, but you optimize measured hot paths only. A shape transition in code that runs twice is irrelevant.

## 8. Startup Cost Example

Large frontend bundles can be expensive before your app logic even runs:

```txt
download JavaScript
  -> parse source
  -> compile/baseline execute
  -> evaluate modules
  -> run framework rendering
  -> hydrate or attach interactivity
```

> [!warning] Unused JavaScript is not free
> This is why "unused JavaScript" is not free. A utility module imported on every route can cost parse/evaluation time even if the user never opens the feature that needs it.

```tsx
// Better for rare, heavy UI: load at the interaction boundary.
async function openChart() {
  const { ChartPanel } = await import("./ChartPanel");
  showModal(<ChartPanel />);
}
```

> [!tip] Split only avoidable code
> Tradeoff: dynamic import improves initial load only if the split code is truly avoidable and the loading state is handled well. If every user immediately needs the module, splitting can add unnecessary latency.

## Real-World Use Cases

### Triaging a jank report with a DevTools Performance trace

A PM reports "the dashboard stutters while filtering." Before touching code, you record a trace and read which layer owns the time: yellow scripting blocks are the engine executing your JavaScript; purple layout and green paint belong to the browser runtime. You can also ship this triage to production:

```ts
// Report long tasks (main thread blocked > 50ms) from real users.
new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    reportMetric({ type: "long-task", duration: entry.duration });
  }
}).observe({ entryTypes: ["longtask"] });
```

The engine/runtime split from this note is the triage plan: a long yellow block means fix your algorithm or move work; a long purple block means fewer DOM writes and less layout thrash — different layers, different fixes. See [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]].

### Client-side image resize with WebAssembly before upload

An avatar-upload flow resizes images in the browser to save bandwidth. Doing it with a Wasm codec (e.g. a Rust/squoosh module) instead of JS gives predictable performance on the first run — no warmup, no deopt cliffs.

```ts
async function makeThumbnail(file: File) {
  const { resize } = await import("@app/wasm-image"); // compiled to .wasm
  const buffer = await file.arrayBuffer();
  return resize(buffer, { width: 256 }); // near-native speed, first call included
}
```

Works because Wasm bypasses the parse/AST/tiering pipeline entirely and is statically typed, so it never deoptimizes — the mechanism from the Wasm section above.

### The post-deploy latency spike on an SSR server

After every deploy of a Next.js service, p95 render time spikes for a minute, then settles. Nothing is broken: the fresh Node process starts executing render-path functions in Ignition, and they only tier up through Sparkplug/Maglev/TurboFan as type feedback accumulates under real traffic.

```ts
// Deploy hook: warm the hottest routes before the instance joins the load balancer,
// so tier-up happens on synthetic traffic instead of real users.
for (const route of ["/products", "/product/warmup-sku", "/cart"]) {
  await fetch(`http://localhost:3000${route}`, { headers: { "x-warmup": "1" } });
}
```

The same tiered-compilation model you learn for browsers explains server latency curves, because Node embeds the same engine — JIT state lives in the process and dies with every restart.

> [!tip]
> This is also why microbenchmarks lie: a loop run 10,000 times measures TurboFan-optimized code, while your real function may run twice in Ignition. Benchmark at realistic call counts.

## 9. Interview Answer

**Short version:** A JavaScript engine executes ECMAScript. A runtime embeds that engine and adds APIs such as DOM, fetch, timers, files, networking, event loops, and rendering.

**Deeper version:** The engine parses and executes code, manages execution contexts, allocates objects, and performs garbage collection. Modern engines optimize hot paths using runtime feedback, but details differ by engine. The runtime is the environment around the engine. In a browser, it provides Web APIs and rendering. In Node.js, it provides server-side APIs and I/O. That distinction explains why `Array` and `Promise` exist everywhere, while `window`, `document`, and `fs` depend on where the code runs.

## 10. Common Mistakes

- Calling Node.js an engine. Node.js is a runtime that embeds an engine.
- Saying the event loop is part of V8. Event-loop integration belongs to the host/runtime.
- Assuming `useMemo` moves CPU work off the main thread. It only caches a value for stable dependencies.
- Treating engine internals as stable API. Hidden classes and JIT details help intuition, but application code should optimize measured bottlenecks.
- Ignoring parse and compile cost when shipping large JavaScript bundles.
- Blaming V8 for browser rendering work such as layout, paint, image decoding, or compositing.
- Using `delete` in hot paths without knowing it can force objects into dictionary mode — or avoiding `delete` everywhere without knowing the `in`/`Object.keys` semantic difference.
- Saying "V8 compiles JavaScript to machine code" as if it were one step. It is a tiered pipeline (Ignition, Sparkplug, Maglev, TurboFan) driven by type feedback.

## 11. Practice

1. Name two things the engine owns and two things the runtime owns.
2. Why can Chrome and Node.js both use V8 but expose different globals?
3. Why can a CPU-heavy calculation freeze the browser even if it is "just JavaScript"?
4. When would `useMemo` help, and when would it not help?
5. Explain engine vs runtime in 30 seconds for an interview.
6. What is a monomorphic call site, and why does it matter?
7. Why can the *order* you add properties to objects affect performance?

<details>
<summary>Show answer</summary>

1. The engine owns parsing/executing ECMAScript and managing execution contexts, object allocation, optimization, and garbage collection. The runtime owns host APIs such as DOM, timers, fetch/networking, file APIs, event-loop integration, and rendering.

2. V8 implements ECMAScript. Chrome embeds V8 in a browser runtime with `window`, DOM, rendering, storage, and Web APIs. Node.js embeds V8 in a server runtime with `process`, filesystem, streams, and server I/O. Same engine, different host capabilities.

3. CPU-heavy JavaScript runs on the current execution stack. While the stack is busy, the browser cannot run input handlers or paint updates on that same main-thread event loop. Async APIs do not make synchronous CPU work disappear.

4. `useMemo` helps when an expensive calculation can be skipped because dependencies are stable. It does not help if dependencies change every render, if rendering thousands of rows is the bottleneck, if the work should happen on a worker/server, or if the calculation is cheap and memoization adds complexity.

5. Interview version: "A JavaScript engine executes ECMAScript: parsing, compiling, running code, managing contexts and memory. A runtime embeds that engine and adds host capabilities like DOM, timers, fetch, files, event-loop integration, and rendering. That is why `Array` exists everywhere, but `window` is browser-specific and `fs` is Node-specific."

6. A monomorphic call site is a property access or call that has only ever seen one hidden class. The engine caches that shape in an inline cache, so the access becomes a single shape check plus a direct offset read, and optimizing compilers can specialize on it. Sites that see many shapes (megamorphic) fall back to generic, much slower lookup.

7. Property insertion order determines the chain of shape transitions. Two objects with identical properties added in different orders end up with different hidden classes, so code that reads them stops being monomorphic. Creating objects with a consistent literal shape (same keys, same order, nullable fields instead of conditional keys) keeps downstream accesses on the fast path.

</details>

## Related Notes

- [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]]
- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]
- [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]
- [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
