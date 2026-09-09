---
tags: [machine-model, performance, memory]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
aliases: [Memory Hierarchy, Registers vs RAM, Cache Locality, Cache Line]
---

# Registers, Caches and RAM

## Maturity Target

- Priority: #deep-dive
- Study time: 25-35 minutes
- Interview signal: you can order the memory hierarchy by cost, explain why JS gives you no direct control, and still name the JS-level choices that decide which layer gets hit.
- Production signal: you can explain why a typed-array hot loop beats an array of objects, and why "stable object shapes" is a memory-layout argument, not folklore.
- Dependencies: [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]]

## Source Anchors

- [Agner Fog - Software optimization resources (instruction latencies)](https://www.agner.org/optimize/)
- [MDN - JavaScript typed arrays](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Typed_arrays)
- [V8 - Elements kinds in V8](https://v8.dev/blog/elements-kinds)
- [V8 - Fast properties in V8](https://v8.dev/blog/fast-properties)

## 1. Concept

**Simple explanation.** Registers live inside the CPU and are read in about one cycle; RAM is a separate chip and costs hundreds. Caches sit between them. You never choose registers in JavaScript — the JIT's register allocator does — but you routinely decide, without noticing, whether your data is cache-friendly.

**Accurate mechanism.** One tradeoff, repeated at every level: closer and faster means smaller and more expensive.

| Layer | Where | Rough cost | Rough size |
| --- | --- | --- | --- |
| Registers | Inside the execution units | ~1 cycle | ~16-32 general-purpose slots |
| L1 cache | On-core | a few cycles | tens of KB |
| L2 cache | On-core / per-cluster | ~10-20 cycles | hundreds of KB to a few MB |
| L3 cache | Shared across cores | ~40 cycles | several to tens of MB |
| RAM | Separate chip, over a bus | ~200-300 cycles | gigabytes |

(Order of magnitude, not a spec sheet — the numbers move per microarchitecture. What is stable is the *ratio*: RAM is roughly two orders of magnitude worse than a register.)

The physical reason for the gap is distance and protocol: registers are transistors adjacent to the units that use them; RAM is a chip away, across a bus, with real signal travel time and a request/response protocol.

**Caches move data in cache lines, typically 64 bytes.** This is the single most consequential fact for code you actually write. Touching one byte pulls in its whole line, so *sequential access is nearly free after the first miss and scattered access pays a miss every time*. Locality, not instruction count, is what most "why is this loop slow" answers come down to.

### Trace: where your JS values actually live

```js
function add(a, b) {
  return a + b;
}
```

Once an optimizing tier compiles this, both parameters are short-lived integers, so they never touch memory:

```asm
mov eax, 3        ; a lives in a register
mov ebx, 4        ; b lives in a register
add eax, ebx      ; register-to-register; RAM is not involved at all
ret
```

Now an object:

```js
const user = { name: "Sam", age: 30 };
console.log(user.name);
```

An object is too large and too long-lived for a handful of registers, so it is allocated on the heap — which is RAM. What a register holds is a *pointer*:

```asm
mov rax, 0x00007f2a3000   ; register holds the ADDRESS of the object
mov rbx, [rax + 8]        ; dereference: an actual trip out to memory
```

So the honest version of a rule you have already met: **primitives in a hot function can live entirely in registers; every object property access is at minimum a pointer dereference into memory**, and whether that costs 4 cycles or 300 depends on whether the line is already in cache.

### The JS-level choices that do decide the layer

You have no `register` keyword and no control over allocation. You do control layout, and layout decides cache behaviour:

- **Stable object shapes.** V8 gives same-shape objects a shared hidden class and stores properties at fixed offsets, so `user.age` compiles to a load at a known offset. Shape drift forces dictionary-mode lookups — a hash probe instead of an offset, with worse locality. This is the *memory* argument behind the shape advice in [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]; it is not only about deopt.
- **Element kinds.** A packed array of small integers is stored as a contiguous run of values. Introduce a string, a hole, or a `delete` and V8 transitions to a more general kind — often boxed pointers, which means every element read becomes a dereference to somewhere else in the heap. One `arr[10000] = 1` on a length-3 array can flip the representation.
- **Typed arrays.** `Float64Array` is genuinely contiguous raw memory with no per-element object headers and no boxing. For numeric bulk work this is the only way to get C-like layout from JavaScript.
- **Array of objects vs parallel arrays.** `objects[i].x` walks a pointer per element to scattered heap addresses; `xs[i]` walks one contiguous run. Same algorithm, completely different miss rate.

> [!warning] This is a last-mile optimization, not a coding style
> Everything above matters in loops over tens of thousands of elements, and nowhere else. Restructuring readable domain objects into parallel typed arrays "for cache locality" in ordinary component code is a straight loss: harder to read, harder to change, unmeasurable gain. Reach for it after a profile points at a specific loop.

## 2. Why It Matters

- It supplies the mechanism behind advice you have already accepted on authority — stable shapes, packed arrays, typed arrays for numeric work.
- It explains why algorithmic complexity sometimes loses to layout: a linear scan over contiguous memory can beat a "better" structure that chases pointers.
- It is the correct frame for judging whether a Wasm or worker rewrite will help. If the loop is memory-bound, the language was never the bottleneck.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

A charting component downsamples 500,000 sensor readings on every zoom. The main thread blocks for ~600 ms and the interaction feels broken.

```ts
// ❌ Array of objects: one pointer chase per element, on every pass
type Reading = { t: number; value: number; sensorId: string };

function downsample(readings: Reading[], buckets: number) {
  const out: number[] = [];
  const size = Math.ceil(readings.length / buckets);
  for (let b = 0; b < buckets; b++) {
    let sum = 0;
    for (let i = b * size; i < Math.min((b + 1) * size, readings.length); i++) {
      sum += readings[i].value;   // deref the element pointer, then load a field
    }
    out.push(sum / size);
  }
  return out;
}
```

Trace: `readings` is an array of pointers to 500,000 separately allocated objects, scattered across the heap in allocation order that no longer matches iteration order after a GC compaction. Each `readings[i]` is a load; each `.value` is a second load at an offset in a different cache line. The loop reads 8 useful bytes per 64-byte line fetched and misses constantly. The arithmetic is trivial — the loop is memory-bound, so neither TurboFan nor a faster algorithm helps much.

```ts
// ✅ Store the numeric columns contiguously; keep the objects for the API layer
class ReadingTable {
  t: Float64Array;
  value: Float64Array;
  constructor(n: number) {
    this.t = new Float64Array(n);
    this.value = new Float64Array(n);
  }
}

function downsample(table: ReadingTable, buckets: number) {
  const { value } = table;
  const out = new Float64Array(buckets);
  const size = Math.ceil(value.length / buckets);
  for (let b = 0; b < buckets; b++) {
    let sum = 0;
    const end = Math.min((b + 1) * size, value.length);
    for (let i = b * size; i < end; i++) sum += value[i]; // one contiguous stream
    out[b] = sum / size;
  }
  return out;
}
```

Now every 64-byte line fetched yields eight consecutive `float64`s that the loop will all use, the hardware prefetcher recognizes the stride, and there are no element pointers and no boxing.

Tradeoffs, and they are not small: the ergonomic `Reading` object is gone from the hot path, so you need a conversion boundary and probably an accessor for debugging; `sensorId` cannot live in a `Float64Array`, so string data needs a parallel structure or an interned integer id; the two arrays must be kept the same length, which is an invariant the type system will not enforce for you; and the whole thing is only justified by the profile that sent you here. The complementary move — running it in a worker on a transferred buffer, see [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]] — addresses responsiveness rather than throughput, and the two compose well.

> [!tip] Ask "is this compute-bound or memory-bound?" first
> Compute-bound loops get faster from better algorithms, Wasm, or workers. Memory-bound loops get faster from better layout, and nothing else moves the needle much — which is why a Wasm rewrite of a pointer-chasing loop often disappoints.

## 4. Interview Answer

Short answer:

> Registers are inside the CPU and cost about one cycle; RAM is a separate chip and costs a couple of hundred, with L1 to L3 caches in between. In JavaScript you never choose — V8's register allocator decides, and only in the compiled tiers. Primitives in a hot function can stay entirely in registers; an object lives on the heap, so a register holds a pointer and every property access is a memory load.

Deeper answer:

> The detail that matters for code you write is that caches move data in 64-byte lines, so sequential access is almost free after the first miss while scattered access misses repeatedly. That is the real mechanism behind advice we usually give as rules: stable hidden classes mean a property is a load at a fixed offset instead of a dictionary probe; packed element kinds keep array data contiguous, while a hole or a mixed type transitions to boxed pointers; and typed arrays are the only way to get genuinely contiguous, unboxed numeric memory from JavaScript. Which is also why the compute-bound versus memory-bound question comes first: an array of 500,000 objects makes a summation loop memory-bound, so it is layout, not the optimizing tier and not a Wasm rewrite, that moves it. And I would only reach for any of this after a profile — restructuring readable domain objects into parallel typed arrays without one is a net loss.

## 5. Practice

1. <details><summary>Why can <code>a + b</code> in a hot function touch no memory at all, while <code>user.age</code> always touches memory?</summary><code>a</code> and <code>b</code> are short-lived primitives, so the register allocator keeps them in CPU registers for the function's lifetime. <code>user</code> is a heap-allocated object; the register can only hold its address, so reading a property is a dereference — a load from memory, hitting cache or RAM depending on locality.</details>
2. <details><summary>What is a cache line, and why does it decide loop performance more often than instruction count?</summary>It is the unit caches transfer, typically 64 bytes — you cannot fetch one byte. Sequential access uses all of each fetched line and is nearly free after the first miss; scattered access uses a fraction of each line and misses constantly. With RAM around two orders of magnitude slower than L1, miss rate dominates the arithmetic in most bulk loops.</details>
3. <details><summary>Give the memory-layout reason — not the deopt reason — that stable object shapes matter.</summary>Same-shape objects share a hidden class, so V8 stores each property at a fixed offset and compiles access to a direct load at that offset. Shape drift can push the object into dictionary mode, replacing an offset load with a hash lookup and scattering the property storage, which costs both instructions and locality.</details>
4. <details><summary>Transfer: a colleague proposes rewriting a slow loop over 200k objects in Wasm. What do you check first, and why might Wasm disappoint?</summary>Whether the loop is compute-bound or memory-bound. If it chases one pointer per element, the bottleneck is cache misses, and Wasm does not change the data layout — you would port the same misses to another language. Fix locality first (typed arrays or parallel columns); consider Wasm afterwards, when the loop is genuinely arithmetic-bound.</details>

## Related Notes

- [[32 - Compilation and Machine Foundations/06 - The CPU as Orchestrator|The CPU as Orchestrator]] — how the CPU reaches memory and devices.
- [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]] — the JS-level view of the same storage.
- [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]] — element kinds and packed vs holey arrays.
- [[12 - Advanced Language Concepts/14 - Typed Arrays and Binary Data|Typed Arrays and Binary Data]] — the API for contiguous memory.
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]] — when to stop optimizing the loop and cache the result.
