---
tags: [compilation, jit, machine-model]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
aliases: [AOT vs JIT, Why Java Uses a JIT, Write Once Run Anywhere]
---

# AOT, JIT and the Portability Tradeoff

## Maturity Target

- Priority: #deep-dive
- Study time: 25-35 minutes
- Interview signal: you can explain why a statically typed language still profits from a JIT, and name the two things a JIT knows that no AOT compiler can.
- Production signal: you can articulate what "moving work to build time" buys and costs, and place prerendering, bundling and the React Compiler on that axis deliberately.
- Dependencies: [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon|From Source Text to Silicon]]

## Source Anchors

- [Java Virtual Machine Specification](https://docs.oracle.com/javase/specs/jvms/se21/html/index.html)
- [GraalVM Native Image - Reachability metadata](https://www.graalvm.org/latest/reference-manual/native-image/metadata/)
- [V8 - Sparkplug, a non-optimizing JavaScript compiler](https://v8.dev/blog/sparkplug)
- [V8 - Code caching for WebAssembly developers](https://v8.dev/blog/wasm-code-caching)
- [Next.js documentation](https://nextjs.org/docs)

## 1. Concept

**Simple explanation.** AOT means the CPU-specific compilation happens on the build machine, before anyone runs the program. JIT means it happens on the user's machine, while the program runs. You can have one or the other, not both for the same artifact — and which you pick is a decision about portability and startup, not about which is "faster".

**Accurate mechanism.** Every toolchain must eventually produce machine code for one specific instruction set. The only question is *where the target CPU becomes known*.

- If the build machine knows the target: compile fully ahead of time. Output is a native binary — fast to start, no warm-up, and unable to run anywhere else. C++, Rust, Go.
- If the target is unknown until run time: stop at a portable artifact and finish the job on arrival. Output is bytecode plus a runtime that interprets or JIT-compiles it. Java, C#, JavaScript, WebAssembly.

Those goals are mutually exclusive for one artifact, which is the whole answer to "why doesn't Java just produce an `.exe` like C++?" — a native `.exe` **is** the loss of "write once, run anywhere". Java gave up the native binary to keep the portability; C++ gave up the portability to keep the native binary.

### Java, traced

```txt
Foo.java  ──javac──►  Foo.class            ──JVM──►  machine code
          (static types fully checked)     (interpret, then C1, then C2)
          ▲ build machine                  ▲ user's machine
```

`javac` really does do the full static type-checking work ahead of time. What it does *not* do is emit machine code — it stops at stack-based JVM bytecode, because the target CPU is not known yet.

Then why JIT at all, given types are already resolved? Two independent reasons, and it is worth keeping them separate:

1. **Startup latency.** Compiling every method to optimized native code before running anything would make programs slow to start and waste effort on code that runs once. So the JVM interprets first, then tiers up hot methods through C1 (fast, lightly optimizing) to C2 (slow, aggressive) — structurally identical to V8's Ignition → Sparkplug → Maglev → TurboFan, and for identical reasons.
2. **Facts that only exist at run time.** Even with complete static types, some things are unknowable at build time: which classes actually got loaded (Java has dynamic class loading and reflection), which override actually runs at a given virtual call site *in practice*, which branch is hot, what the real value distribution looks like. A JIT can inline the one implementation it has actually observed and guard it; an AOT compiler must be conservative because it has only what the types *permit*.

> [!warning] Java's JIT is not solving JavaScript's problem
> V8 speculates because JavaScript has no static types — it must guess what a value is. The JVM's types are fixed and known; its JIT speculates about *behavior* (this call site is monomorphic in practice, this branch is never taken). Same machinery, different uncertainty. Saying "Java JITs because it's dynamic" is wrong and an interviewer will notice.

### The third option, which proves it was a choice

GraalVM Native Image compiles Java ahead of time into a native executable — C++-style. You gain near-instant startup and no warm-up; you give up dynamic class loading and unrestricted reflection, and must declare in *reachability metadata* whatever reflection will touch, because the AOT compiler closes the world at build time to know what it can delete. The tradeoff is not incidental; it is the same tradeoff in the other direction.

### The axis, and where JavaScript sits

| | Knows the target CPU | Knows real execution behavior | Startup | Portable artifact |
| --- | --- | --- | --- | --- |
| AOT native (C++, Rust, Go, Native Image) | Yes | No | Instant | No |
| Bytecode + JIT (JVM, CLR, V8) | Only at run time | **Yes** | Warm-up | Yes |
| Wasm | Only at run time | Mostly no (static types) | Near-instant, single-pass compile | Yes |

Wasm is the interesting middle: a portable artifact like JVM bytecode, but with types already resolved, so the on-arrival step can be one fast compile pass rather than an interpret-and-observe ladder.

### The frontend's real AOT lever

JavaScript source is what you ship, so you cannot AOT-compile *the language*. But you can move almost everything else to build time, and that is the same decision:

- **Bundling, minification, tree-shaking** — module resolution and dead-code elimination done once, at build, instead of per request.
- **SSG and prerendering** — the render executed at build time; the user gets the output, not the computation.
- **Compile-time reactivity** — Svelte and the React Compiler emit the update code instead of computing it each render (see [[32 - Compilation and Machine Foundations/05 - Reflection and Compile-Time Codegen|Reflection and Compile-Time Codegen]]).
- **Code caching** — Chrome caches V8's compiled output per script, and Wasm modules can be cached compiled. Not AOT, but the same instinct: pay once, not per visit.

And the same costs appear: build-time work is only correct if the inputs were knowable at build time. A prerendered page with per-user content is the exact analogue of an AOT compiler that guessed which classes were reachable.

## 2. Why It Matters

- It is the honest answer to "is JavaScript interpreted or compiled?" — the question is malformed, and this axis is what it should have asked.
- It reframes bundling, SSG and compiler-based frameworks as one decision you can reason about, instead of three separate best practices.
- "Which facts exist at which phase" is the single most transferable idea in this module.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

A dashboard route is prerendered at build time for speed. Loads are excellent, then support reports that some users see another tenant's currency and stale figures.

```tsx
// ❌ Build-time rendering of something only knowable per request
export const dynamic = "force-static";

export default async function Page() {
  const tenant = await getTenantFromHeaders(); // resolves to *something* at build
  const rows = await fetchMetrics(tenant.id);  // baked into the HTML, forever
  return <MetricsTable rows={rows} currency={tenant.currency} />;
}
```

Trace, and it is exactly the AOT failure mode: the build machine had no request, so `getTenantFromHeaders()` resolved against whatever ambient state existed during the build. That single answer was compiled into static HTML and served to everyone. Nothing is broken at run time — the wrong phase was chosen for a value that did not exist yet.

```tsx
// ✅ Split by what is actually knowable when
export default async function Page() {
  return (
    <>
      <DashboardChrome />                {/* genuinely static: prerender it */}
      <Suspense fallback={<TableSkeleton />}>
        <TenantMetrics />                {/* per-request: resolve at request time */}
      </Suspense>
    </>
  );
}
```

Tradeoffs: the page now has two performance profiles, and the per-request part reintroduces server work and a loading state on every visit; the skeleton has to be designed so the layout does not shift; and observability gets harder because one URL now has a build-time path and a request-time path that can fail differently.

> [!tip] The phase question, asked in general
> Before moving anything to build time — a render, a bundle graph, a memo, a compiled shader — ask: *is this input knowable at build time, for every future consumer?* If not, you are the AOT compiler guessing which classes were reachable.

## 4. Interview Answer

Short answer:

> AOT compiles to machine code on the build machine, before anyone runs the program; JIT does it on the user's machine while the program runs. AOT gives instant startup and no warm-up but produces an artifact tied to one CPU; JIT keeps one portable artifact and pays a warm-up. Java stops at portable bytecode precisely because it wanted one artifact to run anywhere.

Deeper answer:

> The real variable is where the target CPU becomes known. If the build knows it, finish the job there. If not, ship bytecode and finish on arrival. Java's `javac` fully checks static types ahead of time but deliberately stops at JVM bytecode, then interprets and tiers up through C1 and C2 — same structure as V8's tiers, for the same startup reason. But there is a second reason a JIT wins even with full static types: it knows things no AOT compiler can, namely which classes actually loaded, which virtual call sites are monomorphic in practice, and which branches are hot — so it can inline speculatively and guard. GraalVM Native Image shows this was a choice: you can AOT-compile Java, and you pay for it in dynamic class loading and reflection, which is why it demands reachability metadata. Frontend-side, we cannot AOT-compile JavaScript because source is the shipped artifact, but bundling, prerendering, compile-time reactivity and code caching are all the same move — and they fail the same way, by resolving something at build time that was only knowable per request.

## 5. Practice

1. <details><summary>Java has full static types. Name the two distinct reasons it still uses a JIT.</summary>(1) Startup: compiling everything to optimized native code before running anything is slow and wasteful for code that runs once, so it interprets first and tiers up hot methods. (2) Run-time-only information: which classes actually loaded, which implementation a virtual call site really takes, which branches are hot — an AOT compiler must be conservative over everything the types permit, a JIT can specialize on what it observed and guard the assumption.</details>
2. <details><summary>Why can't Java ship a native executable and still be "write once, run anywhere"?</summary>Machine code is instruction-set specific. A native executable is, by definition, already committed to one CPU family and OS ABI, so it cannot be the one artifact that runs everywhere. Portability requires stopping before that commitment, which is what bytecode is.</details>
3. <details><summary>Wasm is portable like JVM bytecode but needs no warm-up. What makes that possible, and what does it give up?</summary>Its instructions are statically typed and validated in a single linear pass, so the engine can compile straight to machine code on arrival with no need to observe types first. What it gives up is exactly what type feedback buys: a Wasm engine cannot specialize on observed values the way TurboFan can, and its performance is predictable rather than adaptive.</details>
4. <details><summary>Transfer: name the frontend equivalent of "the AOT compiler deleted code that reflection needed at runtime."</summary>Tree-shaking or a bundler dropping a module only reached dynamically — by a string key, a computed <code>import()</code>, or a component registry looked up at run time. Both are a closed-world assumption meeting an open-world access. Both are fixed the same way: declare the dynamic surface explicitly (a static map, an explicit include list, reachability metadata) so the build-time step can see it.</details>

## Related Notes

- [[32 - Compilation and Machine Foundations/12 - Compiled vs Interpreted and Every Stage Between|Compiled vs Interpreted, and Every Stage Between]] — the four implementation strategies side by side, and why the dichotomy dissolves.
- [[32 - Compilation and Machine Foundations/03 - LLVM and Compiler IR|LLVM and Compiler IR]] — the build-time half of the pipeline.
- [[32 - Compilation and Machine Foundations/05 - Reflection and Compile-Time Codegen|Reflection and Compile-Time Codegen]] — the same axis, applied to generating code.
- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]] — V8's tiers as one instance of this.
- [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]] — build-time vs request-time, in production terms.
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]] — the closed-world assumption in your bundler.
