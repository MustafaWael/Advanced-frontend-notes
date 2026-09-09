---
tags: [javascript, runtime, glossary, javascript-engine]
module: "02 - JavaScript Runtime Foundations"
priority: important
status: not-started
aliases: [Engine Glossary, V8 Glossary, Compilation Glossary]
verified_on: 2026-07-24
version_scope: "V8 13.x era (Ignition/Sparkplug/Maglev/TurboFan+Turboshaft); Wasm deopt since Chrome M137"
---

# Engine and Compilation Glossary

## Maturity Target

- Priority: #important
- Study time: 20-30 minutes
- Interview signal: define any engine term in [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]] in one plain sentence, then name the mechanism.
- Production signal: read a DevTools/flame-chart discussion or a V8 blog post without getting lost in jargon.
- Dependencies: read this *before* [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]] if engine internals are new to you.

## Source Anchors

- [V8 documentation](https://v8.dev/docs)
- [V8: Sparkplug — a non-optimizing JavaScript compiler](https://v8.dev/blog/sparkplug)
- [V8: Maglev — V8's fastest optimizing JIT](https://v8.dev/blog/maglev)
- [V8: Speculative Optimizations for WebAssembly using Deopts and Inlining](https://v8.dev/blog/wasm-speculative-optimizations)

## How to use this note

This is a companion glossary for [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]. The terms are ordered so each one builds on the last — read top to bottom once, then use it as a lookup. Every definition is *simple sentence first, mechanism second*.

> [!tip] Two chains carry 80% of the jargon
> Most of these words collapse into two short stories: **type feedback → tier up → deopt** (the optimization story) and **hidden class → inline cache → monomorphic** (the "make V8 happy" story). Learn those two chains and the rest is vocabulary.

## 1. How code becomes something the CPU runs

- **Machine code (native code):** the raw instructions your CPU actually executes — the genuinely fast layer. Every other step exists to produce this.
- **Tokenize:** chops source text into meaningful pieces, e.g. `const x = 1` → `const`, `x`, `=`, `1`.
- **Parse:** checks those tokens form valid grammar and builds a tree from them.
- **AST (Abstract Syntax Tree):** that tree — your code as a structured object the engine can walk instead of a flat string. `a + b` becomes a "plus" node with two children.
- **Bytecode:** a compact engine-internal instruction set, lower-level than JS but higher-level than machine code. A middle language the engine runs quickly without compiling all the way to native yet.
- **Interpreter:** runs bytecode instruction by instruction, immediately, no heavy compilation. Fast to *start*, slow to *run*. (V8's is **Ignition**.)
- **Compiler:** translates code into faster machine code *before* running it. Slow to start, fast to run.
- **JIT (Just-In-Time) compilation:** compiling *while the program runs* rather than ahead of time. The core trick of modern JS engines: interpret first, then compile the parts that prove they matter.

## 2. The tiered compilation model (the heart of the engine note)

Compiling is expensive and most functions run only a few times, so engines don't treat all code equally — they use **tiers**.

- **Hot path / hot code:** code that runs many times (a loop body, a constantly-called function). "Hot" = worth spending compile effort on. Cold code isn't.
- **Baseline compiler:** compiles quickly to *okay* machine code with no cleverness — a fast step up from the interpreter. (V8's is **Sparkplug**.)
- **Optimizing compiler:** takes real time to produce *excellent* machine code, only for hot code. (V8: **Maglev** = fast/good-enough, **TurboFan** = slow/best.)
- **Tier up / tiering:** promoting a function to a fancier compiler once it proves it's hot.
- **Interrupt budget:** how "hot" is actually measured — a per-function allowance scaled to its bytecode length, charged at function entry *and* at loop back-edges. At zero, the engine picks a tier. Not a plain call counter, which is why a function called once with a big loop still gets optimized. Avoid quoting fixed thresholds like "~8 invocations"; the numbers move between V8 versions.
- **Back-edge:** the jump from the end of a loop body back to its start (V8's `JumpLoop` bytecode). Charging the budget here is what makes loops count toward tier-up.
- **OSR (on-stack replacement):** swapping a running function to a higher tier *without waiting for it to return* — compile an entry point at the loop header, move live values into the new frame, jump in. Your loop changes tiers between two iterations.
- **Threaded dispatch:** how the interpreter runs bytecode — each opcode's handler ends by tail-jumping directly into the next handler. There is no interpreter loop and no central `switch`.
- **Bytecode flushing:** discarding a cold function's bytecode (not just its machine code) under memory pressure, to be regenerated from the source text if it's called again.
- **Type feedback (runtime feedback):** as the interpreter runs, it records what *actually* flows through your code ("this has always been a number," "this object always has these fields"). Optimizing compilers bet on these observations.
- **Warmup:** the period before a function has run enough to be optimized; it runs slower during this time. (Why a freshly-deployed SSR server is slow for a minute.)
- **Deoptimization (deopt / bailout):** when an optimized function's bet turns out wrong ("assumed number, got string"), the engine discards the optimized code and drops back to a slower tier.
- **Deopt cliff:** a sudden performance drop caused by that happening repeatedly.

## 3. V8's specific names (just labels for section 2)

- **Ignition** = interpreter · **Sparkplug** = baseline compiler · **Maglev** = mid-tier optimizer · **TurboFan** = top-tier optimizer · **Liftoff** = the baseline compiler for WebAssembly specifically.
- **IR (Intermediate Representation):** an internal data structure a compiler uses to reason about your code while optimizing — not source, not machine code, something in between built for analysis.
- **CFG (Control-Flow Graph):** one IR style that models code as boxes (blocks of instructions) with arrows (which block runs next). Traditional and easy to reason about.
- **Sea of Nodes:** an older, more abstract IR V8 used inside TurboFan. **Turboshaft** is its CFG-based replacement. You don't need the internals — V8 swapped one internal representation for a simpler one. Deep-dive trivia; skim it.

## 4. Object shapes (why property order affects speed)

- **Property bag:** the mental model of a JS object as "a bag of key→value pairs you can add to anytime." True in the spec, too slow to implement literally.
- **Hidden class (a.k.a. shape / map / structure):** the engine's per-object layout record — which properties exist, in what order, at which memory position. Objects built the same way share one hidden class, skipping dictionary lookups.
- **Offset:** a fixed memory position. If `name` always lives at offset 1, reading `user.name` is "grab slot 1" — as fast as a C struct field, no key search.
- **Shape transition / shape chain:** adding a property moves an object to a *new* hidden class. Add properties in a different order and you get a *different* chain, so identical-looking objects can have different shapes.
- **Dictionary mode (slow mode):** when an object becomes too irregular (e.g. after `delete`), the engine abandons the fast layout and falls back to a per-access hash-map lookup. Much slower.
- **Inline cache (IC):** each spot in your code that reads a property remembers which shapes it has seen there, so it can skip re-checking:
  - **Monomorphic** — one shape seen → fastest.
  - **Polymorphic** — a few (2–4) shapes → still fast, short check.
  - **Megamorphic** — many shapes → engine gives up caching, uses slow generic lookup.

## 5. Remaining terms

- **WebAssembly (Wasm):** a low-level binary format that runs in the browser near native speed. Skips JS's parse/type-feedback pipeline because it's already compiled and statically typed. **WasmGC** is a newer Wasm extension with garbage collection. **`call_indirect`** is a Wasm instruction for calling a function chosen at runtime.
- **Static vs dynamic typing (here):** *dynamic* (JS) = a variable's type can change at runtime, so the engine must observe and guess. *Static* (Wasm) = types fixed up front, no guessing needed.
- **Pre-parse vs lazy compilation:** V8 quickly scans (*pre-parses*) all your code for errors and function boundaries but delays fully compiling each function body until it's first called (*lazy*). This is why "unused JavaScript still costs something."

> [!warning] "Wasm never deoptimizes" is outdated
> A common older claim is that Wasm never deopts. Since **Chrome M137 (2025)**, V8 added *speculative* Wasm optimizations (e.g. `call_indirect` inlining) that **can** deopt, mainly benefiting WasmGC. Say instead: Wasm skips type-feedback warmup and historically didn't deopt, but modern V8 can.

## Related Notes

- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]
- [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]]
- [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]]
- [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]
