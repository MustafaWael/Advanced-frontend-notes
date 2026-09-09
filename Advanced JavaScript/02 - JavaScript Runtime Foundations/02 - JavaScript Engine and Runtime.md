---
tags:
  - javascript
  - runtime
  - javascript-engine-and-runtime
module: 02 - JavaScript Runtime Foundations
priority: must-know
status: learning
verified_on: 2026-07-24
version_scope: V8 13.x era (Ignition/Sparkplug/Maglev/TurboFan+Turboshaft); Wasm deopt since Chrome M137
---
# JavaScript Engine and Runtime

## Maturity Target

- Priority: #must-know
- Study time: 75-90 minutes first pass, 15 on a re-read using the recap
- Interview signal: you can define engine vs runtime in one sentence, name V8's tiers and what drives tier-up, explain hidden classes and inline caches as the mechanism behind "keep shapes stable", and say why deoptimization has to exist at all.
- Production signal: you triage a slow page to engine, runtime, rendering or framework work instead of blaming "JavaScript", and you reach for shape/type discipline only where you have measured a hot path.
- Dependencies: [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]] · [[02 - JavaScript Runtime Foundations/08 - Engine and Compilation Glossary|Engine and Compilation Glossary]] if engine jargon is new

> [!tip] How to read this note — it is the longest in the module
> The spine is sections **1-4** (the distinction), **3's tier table** (the pipeline), and **7** (hidden classes and inline caches). Those three carry every interview answer. Sections 5, 6, 8 and Real-World Use Cases are worked examples — read them once, then skim on re-reads. On any re-read after the first, go straight to the **One-Screen Recap** near the end and try to reconstruct each row before scrolling up; only re-read the section behind a row you could not produce.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)
- [MDN JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
- [V8 documentation](https://v8.dev/docs)
- [V8: Maglev - V8's fastest optimizing JIT](https://v8.dev/blog/maglev)
- [V8: Land ahoy - leaving the Sea of Nodes](https://v8.dev/blog/leaving-the-sea-of-nodes)
- [V8: Sparkplug - a non-optimizing JavaScript compiler](https://v8.dev/blog/sparkplug)
- [V8: Firing up the Ignition interpreter](https://v8.dev/blog/ignition-interpreter)

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

| Tier                     | Role                         | Key facts                                                                                                                                                                                                                                                    |
| ------------------------ | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Ignition**             | Interpreter                  | Compiles source to bytecode, interprets it, and collects type feedback (which shapes and types each site sees). Its bytecode is a **register machine with an accumulator** — V8's words — *not* a stack machine, and its "registers" are frame slots in memory, never CPU registers.                                                                                     |
| **Sparkplug** (2021)     | Baseline compiler            | Compiles bytecode to machine code in a single fast pass, no type feedback needed. Its output is frame-compatible with Ignition's, which is what makes tiering up and down cheap.                                                                             |
| **Maglev** (Chrome M117) | Mid-tier optimizing compiler | Uses collected feedback to generate good-enough optimized code quickly: roughly 10x slower to compile than Sparkplug, roughly 10x faster than TurboFan.                                                                                                      |
| **TurboFan**             | Top-tier optimizing compiler | Spends real compile time on the hottest functions for peak machine code. As of 2025 its backend runs on **Turboshaft**, a CFG-based intermediate representation that has been progressively replacing the older Sea of Nodes design since Chrome 120 (2023). |

**Deoptimization** applies to every optimizing tier: Maglev and TurboFan code embeds assumptions from type feedback ("this parameter is always a small integer", "this object always has this shape"). When an assumption breaks at runtime, the optimized code bails out back to a lower tier, and the function may be re-optimized later with updated feedback.

The one-line reason deopt has to exist, and the best thing to say about it under questioning: **speculation does not produce a faster version of the same program — it produces a narrower program that is only equivalent while the bet holds.** Optimized code that assumed a fixed object shape is not merely slow for a different shape; it would read the wrong memory offset. The failure mode is incorrectness, not sluggishness, which is why a bail-out path is mandatory rather than an optimization. (A cheap in-function guard with a fallback branch is *not* the same thing as a full deopt — the distinction is drawn in [[32 - Compilation and Machine Foundations/11 - Wasm Speculation and Deopt|Wasm Speculation and Deopt]].)

**What actually triggers tier-up** is not a plain call counter. Each function carries an **interrupt budget** scaled to its bytecode length, charged at function entry *and at every loop back-edge* (the `JumpLoop` bytecode). When the budget is exhausted, execution traps into the runtime and V8 makes a tiering decision. Two consequences you can be asked about directly:

- A function called **once** containing a million-iteration loop still tiers up, because back-edges charge the budget. Otherwise the hottest code in a program would never be optimized.
- If that loop is still running when compilation finishes, V8 does **on-stack replacement**: it compiles a version entered at the loop header, migrates live values from the interpreter frame into the new frame, and jumps into machine code without the function returning first. The loop changes tiers between two iterations.

Higher tiers add further gates — Sparkplug→Maglev is on the order of hundreds of invocations, and a *change* in collected feedback resets the counter, since optimizing against feedback that is still moving is wasted compile time. Full mechanism in [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]].

> [!warning] Don't quote a fixed invocation threshold in an interview
> Numbers like "8 calls to Sparkplug" circulate widely and change between V8 versions. Describe the *mechanism* — a bytecode-size-scaled budget charged on entries and back-edges — and you're right across versions and can still mention that back-edges are why loop-heavy code tiers up.

> [!tip] Why tiers exist
> Compilation speed and code quality trade off against each other. Most functions run a handful of times, so compiling them with TurboFan would cost more than it saves. Tiers let the engine spend compile time proportionally to how hot the code actually is — the same "optimize measured hot paths" discipline you should apply to your own code.

### WebAssembly (Wasm) Compilation Bypass
WebAssembly (`.wasm`) is a binary format that represents a stack-based virtual machine with statically typed instructions. 
When V8 loads a Wasm binary, it completely **bypasses the frontend compilation pipeline** (skipping tokenization, parsing, and AST generation). V8's baseline WebAssembly compiler (Liftoff) compiles the Wasm bytecode directly to native machine code in a single, fast pass, which is then eagerly re-optimized in the background by TurboFan.
Because Wasm is statically typed, it **skips the type-feedback warmup** that JS optimization depends on, so it reaches near-native speed on the first run — ideal for heavy calculations in the frontend (e.g. image filters, PDF layout calculations, or game engines).

Wasm also, historically, never deoptimized — and the usual explanation for that is wrong even though the fact was right. Two independent claims hide inside it:

1. **Static typing removes *type* speculation.** Types are declared in the binary and validated at load, so TurboFan never guesses whether a value is a number. This half is solid and still true.
2. **The absence of deopt was a design choice**, not a consequence of (1). V8's Wasm pipeline only ever tiered up, never speculated about anything. Nothing stopped an engine speculating about facts *outside* the type system.

Since **Chrome M137 (2025)** it does: speculative inlining of `call_indirect` targets — a guess about *behaviour*, not type, so it can be wrong. Narrow and targeted, not JavaScript's guess-about-everything model, so the practical takeaway holds: Wasm still avoids the JS deopt-cliff pattern and gives predictable performance. Mechanism, and the guard-branch-versus-real-deopt distinction, in [[32 - Compilation and Machine Foundations/11 - Wasm Speculation and Deopt|Wasm Speculation and Deopt]].

> [!warning] "Wasm never deoptimizes" is now outdated
> Repeating the absolute "Wasm never deopts" in an interview will date you. Say instead: Wasm skips type-feedback warmup and historically didn't deopt, but modern V8 (M137+) added speculative optimizations that can — and be ready to say that the speculation is about call targets, not types.

> [!tip] Where the `.wasm` came from, if that is the follow-up
> A `.wasm` is portable stack-machine bytecode, not machine code, which is why the engine compiles it on arrival at all. Rust or C++ → LLVM IR (SSA, register-like) → LLVM's WebAssembly backend, which flattens SSA into stack ops only at serialization → `.wasm` → the engine's decoder, which immediately un-flattens it back into values for register allocation. So the stack machine exists only as the wire format, bracketed by register-based representations on both sides. Diagram and byte-level walkthrough in [[32 - Compilation and Machine Foundations/10 - Compiling to WebAssembly|Compiling to WebAssembly]].

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

| IC state        | Shapes seen | Speed                                                |
| --------------- | ----------- | ---------------------------------------------------- |
| **Monomorphic** | 1           | Fastest: one shape check, then direct offset access. |
| **Polymorphic** | 2–4         | Still fast: short chain of shape checks.             |
| **Megamorphic** | Many        | Falls off the fast path into generic lookup.         |

This is why the type feedback the tiers collect matters: Maglev and TurboFan generate optimized code from IC states, and a site that stays monomorphic optimizes best.

Two framings worth carrying out of this section, because they turn the advice from folklore into mechanism:

- **There is a memory-layout reason, not only a deopt reason.** A shared hidden class means a property is a load at a fixed offset; dictionary mode replaces that with a hash probe and scatters the storage, which costs locality as well as instructions. Same for arrays: one hole or one mixed type transitions the element kind, often to boxed pointers, turning a contiguous scan into a pointer chase. See [[32 - Compilation and Machine Foundations/07 - Registers Caches and RAM|Registers, Caches and RAM]].
- **"Stable shapes" is really "give the compiler a fact instead of a hint."** An inline cache is the engine betting from history, and the bet is *always guarded* — a monomorphic IC still checks the receiver's map before it reads the offset; it does not become check-free. What consistent shapes buy is that the guard stays a single, perfectly-predicted comparison, and that the optimizing tiers can specialize the load — and where they can prove the shape is fixed for a region, hoist or eliminate the check entirely. The same move appears everywhere in [[32 - Compilation and Machine Foundations/00 - Compilation and Machine Foundations MOC|module 32]]: a direct call beats a correctly-speculated indirect one, and a build-time decision beats a runtime one — because the compiler that can *prove* a fact does strictly more with it than one that merely observed it.

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

To soften this, V8 **pre-parses** top-level code eagerly (a fast scan that finds function boundaries and syntax errors) but defers **full parsing + compilation** of each function body until it is first called — this is *lazy compilation*. It reduces startup cost but doesn't eliminate it: code that runs eagerly at module load (framework setup, top-level side effects) is fully parsed and compiled up front regardless.

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

An avatar-upload flow resizes images in the browser to save bandwidth. Doing it with a Wasm codec (e.g. a Rust/squoosh module) instead of JS gives predictable performance on the first run — no type-feedback warmup and no JS-style deopt cliffs.

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

## One-Screen Recap

The whole note as anchors. On a re-read, cover the right column and try to produce it from the left; only go back to the section behind a row you could not say out loud.

| Anchor | What you should be able to say |
| --- | --- |
| **Engine vs runtime** | Engine executes ECMAScript — parse, compile, run, contexts, heap, GC. Runtime = engine + host capabilities: DOM, timers, `fetch`, files, event-loop integration, rendering. Hence `Array` everywhere, `window` and `fs` not. |
| **Why the distinction pays** | It converts "the page is slow" into a testable question: engine work, runtime/host work, rendering work, or framework work? |
| **The four tiers** | Ignition (interpret + collect feedback) → Sparkplug (fast baseline machine code) → Maglev (mid-tier optimizing) → TurboFan (top tier, now on the Turboshaft IR). Cheap tiers exist so compile time is spent proportional to heat. |
| **Ignition's bytecode** | A register machine with an accumulator, not a stack machine. Its registers are frame slots in memory, never CPU registers. |
| **What triggers tier-up** | Not a call counter: a bytecode-size-scaled interrupt budget charged at function entry *and every loop back-edge*. So a function called once with a hot loop still tiers up — and can tier up mid-loop via on-stack replacement. Never quote a fixed threshold. |
| **Hidden classes** | Same properties in the same order share a shape, so `user.name` is a load at a fixed offset. Different insertion order means a different shape chain; `delete` can drop the object into dictionary mode. |
| **Inline caches** | Monomorphic (1 shape) → fast; polymorphic (2-4) → still fast; megamorphic (many) → generic lookup. The optimizing tiers compile from these states. |
| **Why "stable shapes" matters** | Two reasons, and give both: fixed-offset loads with good locality instead of hash probes, *and* a monomorphic site the optimizer can specialize. Precise framing: the guard never disappears at the IC level — it stays one predictable check — but a proven-stable shape is what lets an optimizing tier hoist or remove it. |
| **Why deopt must exist** | Speculation makes a *narrower* program, not a faster one. Wrong assumption → wrong memory offset → incorrect, not just slow. So a bail-out is mandatory. |
| **Wasm** | Portable stack-machine bytecode, statically typed, so it skips type-feedback warm-up and Liftoff compiles it in one pass. Historically no deopt — but that was a design choice, and since M137 V8 speculates on `call_indirect` targets. |
| **The honest caveat** | All of this is for reading a profile and explaining a measurement. It is not a style guide. Optimize what you measured. |

> [!tip] The two-minute answer this note is really for
> "What happens when JavaScript runs?" — Source is parsed and compiled to bytecode per function, lazily. Ignition interprets it and records what types and shapes each site actually sees. Hot functions tier up through Sparkplug, Maglev and TurboFan, each spending more compile time for better machine code, with the optimizing tiers specializing on that recorded feedback and bailing out if the assumption breaks. Meanwhile the *runtime* — not the engine — owns the event loop, the host APIs and rendering, which is why blocking the stack blocks paint. Everything else in this note is a detail hanging off that sentence.

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
- Calling Ignition a stack machine, or calling its bytecode "stack-based". V8 describes it as a register machine with an accumulator; the hybrid is accumulator + named registers, never stack + register.
- Saying "Wasm never deoptimizes because it's statically typed". The typing half is right, the *because* is not, and since M137 the conclusion is false too.
- Describing deoptimization as "falling back to slower code" and stopping there. The reason it is mandatory is correctness: speculated code would be *wrong* for the new shape, not merely slow.
- Treating a monomorphic inline cache as check-free. It still guards the receiver's map on every access; consistent shapes make that guard cheap and predictable and let the optimizer specialize — only an optimizing tier that can prove the shape is invariant may drop the check.

## 11. Practice

1. Name two things the engine owns and two things the runtime owns.
2. Why can Chrome and Node.js both use V8 but expose different globals?
3. Why can a CPU-heavy calculation freeze the browser even if it is "just JavaScript"?
4. When would `useMemo` help, and when would it not help?
5. Explain engine vs runtime in 30 seconds for an interview.
6. What is a monomorphic call site, and why does it matter?
7. Why can the *order* you add properties to objects affect performance?
8. Why does deoptimization have to exist at all? Answer in terms of correctness, not speed.
9. Is Ignition a stack machine? What are its "registers", concretely?
10. Give two independent reasons stable object shapes help, not one.

<details>
<summary>Show answer</summary>
<ol>
<li>The engine owns parsing/executing ECMAScript and managing execution contexts, object allocation, optimization, and garbage collection. The runtime owns host APIs such as DOM, timers, fetch/networking, file APIs, event-loop integration, and rendering.</li>
<li>V8 implements ECMAScript. Chrome embeds V8 in a browser runtime with <code>window</code>, DOM, rendering, storage, and Web APIs. Node.js embeds V8 in a server runtime with <code>process</code>, filesystem, streams, and server I/O. Same engine, different host capabilities.</li>
<li>CPU-heavy JavaScript runs on the current execution stack. While the stack is busy, the browser cannot run input handlers or paint updates on that same main-thread event loop. Async APIs do not make synchronous CPU work disappear.</li>
<li><code>useMemo</code> helps when an expensive calculation can be skipped because dependencies are stable. It does not help if dependencies change every render, if rendering thousands of rows is the bottleneck, if the work should happen on a worker/server, or if the calculation is cheap and memoization adds complexity.</li>
<li>Interview version: "A JavaScript engine executes ECMAScript: parsing, compiling, running code, managing contexts and memory. A runtime embeds that engine and adds host capabilities like DOM, timers, fetch, files, event-loop integration, and rendering. That is why <code>Array</code> exists everywhere, but <code>window</code> is browser-specific and <code>fs</code> is Node-specific."</li>
<li>A monomorphic call site is a property access or call that has only ever seen one hidden class. The engine caches that shape in an inline cache, so the access becomes a single shape check plus a direct offset read, and optimizing compilers can specialize on it. Sites that see many shapes (megamorphic) fall back to generic, much slower lookup.</li>
<li>Property insertion order determines the chain of shape transitions. Two objects with identical properties added in different orders end up with different hidden classes, so code that reads them stops being monomorphic. Creating objects with a consistent literal shape (same keys, same order, nullable fields instead of conditional keys) keeps downstream accesses on the fast path.</li>
<li>Because speculation produces a <em>narrower</em> program, not a faster version of the same one. Optimized code that assumed a fixed shape reads a fixed memory offset; for a different shape that offset holds something else, so the code would be <em>incorrect</em>, not merely slow. A bail-out path is therefore mandatory rather than an optimization. (A cheap in-function guard with a fallback branch is a lighter mechanism than a full deopt, which discards the optimized function and reconstructs lower-tier state.)</li>
<li>No — V8 describes Ignition as a register machine whose bytecodes name explicit register operands, with an accumulator as an implicit extra operand and destination. So the hybrid is accumulator + named registers, not stack + register. Its "registers" are slots in the interpreter's frame — ordinary memory — and never CPU registers; physical registers only enter at Sparkplug and above, where a register allocator runs.</li>
<li>(1) Memory layout: a shared hidden class makes a property a load at a fixed offset with good locality, whereas dictionary mode means a hash probe and scattered storage. (2) Speculation: a monomorphic site gives the optimizing tiers a stable assumption to specialize on, and avoids the bail-out that a shifting shape would cause. Most people give only the second; giving both is the signal. Be precise about the limit, though — a monomorphic IC still guards the map on every access, so consistent shapes make the guard cheap and specializable rather than absent.</li>
</ol>
</details>

## Related Notes

- [[02 - JavaScript Runtime Foundations/08 - Engine and Compilation Glossary|Engine and Compilation Glossary]] — plain-English definitions for every engine term used here.
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] — the deep-dive companion: threaded dispatch, the interrupt budget, OSR, bytecode flushing.
- [[32 - Compilation and Machine Foundations/00 - Compilation and Machine Foundations MOC|Compilation and Machine Foundations MOC]] — what bytecode is a step *towards*: machine code, compiler IR, the CPU, and the memory hierarchy.
- [[32 - Compilation and Machine Foundations/10 - Compiling to WebAssembly|Compiling to WebAssembly]] — where a `.wasm` comes from, and why the engine compiles it on arrival.
- [[32 - Compilation and Machine Foundations/11 - Wasm Speculation and Deopt|Wasm Speculation and Deopt]] — the `call_indirect` story, and guard branch vs real deopt.
- [[32 - Compilation and Machine Foundations/07 - Registers Caches and RAM|Registers, Caches and RAM]] — the memory-layout half of why stable shapes matter.
- [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]]
- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]
- [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]
- [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
