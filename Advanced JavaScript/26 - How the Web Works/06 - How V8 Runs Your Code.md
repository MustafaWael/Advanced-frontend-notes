---
tags: [javascript, engines, performance, v8]
module: "26 - How the Web Works"
priority: deep-dive
status: not-started
aliases: [V8 pipeline, JIT compilation, How browsers understand JS]
---

# How V8 Runs Your Code

## Maturity Target

- Priority: #deep-dive
- Study time: 50 minutes
- Interview signal: Describe the parse → bytecode → JIT pipeline with real names (Ignition, Sparkplug, Maglev, TurboFan), explain inline caches and hidden classes, and say what triggers deoptimization.
- Production signal: You write monomorphic, shape-stable code by default and can explain *why* it's faster — not as superstition but as mechanism.
- Dependencies: [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]], [[26 - How the Web Works/05 - Engines Landscape|Engines Landscape]]

## Source Anchors

- [V8 blog - Ignition](https://v8.dev/blog/ignition-interpreter)
- [V8 blog - Maglev](https://v8.dev/blog/maglev)
- [V8 docs - Hidden classes / shapes](https://v8.dev/docs/hidden-classes)

## 1. Concept

Simple version: JS is not "interpreted" or "compiled" — it's both, adaptively. The engine starts executing fast with an interpreter, watches what your code actually does, and progressively compiles the hot parts into optimized machine code based on those observations. When the observations turn out wrong, it throws the optimized code away.

The accurate pipeline (V8's names; JSC/SpiderMonkey have equivalent tiers):

1. **Parse** → AST. Lazily: functions are pre-parsed (syntax-checked only) and fully parsed on first call, saving startup time.
2. **Ignition** (interpreter) → compiles AST to **bytecode** and executes it, collecting **type feedback** ("this `+` always saw two numbers", "this property access always saw this object shape").
3. **Sparkplug** → quick non-optimizing baseline compiler (bytecode → machine code, no feedback needed).
4. **Maglev / TurboFan** (optimizing JITs) → for hot functions, compile machine code **speculating** on the collected feedback. TurboFan is the top tier: aggressive inlining, escape analysis, bounds-check elimination.
5. **Deoptimization** — every speculation is guarded. If a guard fails (a string shows up where numbers were promised), the machine code is invalidated and execution *bails out* back to bytecode. Repeated deopts mean your optimization budget is being burned.

The data-structure side — **hidden classes (shapes/maps)**: objects created with the same properties in the same order share a shape. Property access compiles down to "check shape, load fixed offset" — an **inline cache (IC)**. ICs have states:

- **Monomorphic** — one shape seen. Fastest: a compare and a load.
- **Polymorphic** — 2–4 shapes. Slower: a chain of checks.
- **Megamorphic** — many shapes. Falls back to dictionary-style lookup; optimization largely gives up.

```ts
// Same logical data, radically different engine behavior:
function makePointA(x: number, y: number) { return { x, y }; }       // one shape ✅
function makePointB(x: number, y: number) {
  const p: any = {};
  p.x = x;
  if (y !== 0) p.y = y;      // two different shapes depending on input ❌
  return p;
}
// A site doing `pt.x` over makePointA results stays monomorphic;
// over makePointB results it becomes polymorphic → slower, harder to optimize.
```

## 2. Why It Matters

- "How does the browser understand and run JS?" — this note is the mature answer, several levels past "it interprets it."
- It converts perf folklore into mechanism: why consistent object shapes matter, why `delete obj.prop` is harmful (drops the object to dictionary mode), why mixed-type arrays are slower (elements-kind transitions), why hot functions "warm up."
- TypeScript connection: interfaces don't exist at runtime, but coding to consistent interfaces *tends to* produce consistent shapes — one of the quiet perf benefits of disciplined typing.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

```ts
// Buggy (perf, not correctness): a hot path in a data grid
type Row = Record<string, unknown>;
function total(rows: Row[]) {
  let sum = 0;
  for (const r of rows) sum += (r.amount as number) ?? 0;
  return sum;
}
// Rows come from three API endpoints that build objects differently:
// {id, amount, note}, {amount, id}, {id, note, amount, flags} — three shapes.
```

Trace: the `r.amount` access site sees three shapes → polymorphic IC. With more row variants it goes megamorphic: every access is a hash lookup instead of a fixed-offset load. In a 100k-row loop this is the difference between ~1ms and tens of ms — and it shows up in profiles as "self time" in an innocent-looking function.

```ts
// Fix: normalize at the boundary — one canonical shape
interface RowN { id: string; amount: number; note: string | null; flags: number }
const normalize = (raw: any): RowN => ({
  id: raw.id ?? '',
  amount: Number(raw.amount ?? 0),
  note: raw.note ?? null,
  flags: raw.flags ?? 0,
});
// Same property order, all fields always present → one hidden class → monomorphic hot loop.
```

Tradeoffs: normalization costs one pass and some memory for always-present fields. Worth it only on genuinely hot paths — this is a *measure-first* optimization ([[13 - Performance and Memory/00 - Performance and Memory MOC|Performance and Memory]]). Don't contort cold code for IC friendliness.

> [!warning] Footgun: micro-benchmarking JIT-ed code lies. A loop that runs 10M times gets TurboFan-optimized in the benchmark but may run 100 times (interpreted) in production. Profile real workloads, not synthetic loops.

## 4. Interview Answer

Short answer:

> V8 parses JS to an AST, then its Ignition interpreter compiles that to bytecode and starts executing immediately while collecting type feedback. Hot functions get compiled by optimizing JITs — Maglev and TurboFan — into machine code that *speculates* on that feedback, with guards. If a guard fails, the code deoptimizes back to bytecode. So JS execution is adaptive: interpreted first, compiled where it's hot, de-compiled when assumptions break.

Deeper answer:

> The optimization substrate is hidden classes and inline caches: objects with the same properties in the same order share a shape, so property access becomes a shape-check plus fixed-offset load. Access sites are monomorphic, polymorphic, or megamorphic depending on how many shapes they've seen, and that's the mechanical reason behind the perf advice — construct objects fully and consistently, don't delete properties, don't mix element types in hot arrays. Parsing is lazy (pre-parse then full parse on first call), which is one reason bundle size hurts startup even before execution.

## 5. Practice

1. <details><summary>Why is "JS is an interpreted language" wrong, precisely?</summary>Modern engines are multi-tier: bytecode interpretation (Ignition) with runtime type feedback, then baseline and optimizing JIT compilation (Sparkplug/Maglev/TurboFan) to machine code for hot paths, with deoptimization as the escape hatch. Interpretation is only the first tier.</details>
2. <details><summary>What is a deoptimization, what triggers one, and what does it cost?</summary>Invalidation of speculative machine code when a guard fails — e.g., a value of an unexpected type, a new object shape at a previously monomorphic site. Execution bails to bytecode, losing the optimized speed; repeated deopt/reopt cycles are worse than never optimizing.</details>
3. <details><summary>Why can `delete user.tempField` be a performance problem, and what's the alternative?</summary>Delete forces the object off its hidden-class track into dictionary (hash-map) mode, slowing every later property access on it. Alternative: set the field to undefined/null (shape preserved) or design the object without the temporary field.</details>

## Related Notes

- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]
- [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[26 - How the Web Works/05 - Engines Landscape|Engines Landscape]]
