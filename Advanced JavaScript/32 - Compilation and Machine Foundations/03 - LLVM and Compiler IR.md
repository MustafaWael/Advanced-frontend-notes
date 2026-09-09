---
tags: [compilation, llvm, machine-model]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
aliases: [LLVM IR, Compiler Intermediate Representation, Frontend vs Backend Compiler]
---

# LLVM and Compiler IR

## Maturity Target

- Priority: #deep-dive
- Study time: 20-30 minutes
- Interview signal: you can state the one difference that matters between LLVM IR and Wasm/JVM bytecode — lifetime, not shape — and explain why a shared IR exists at all.
- Production signal: you understand what is actually happening when you build a Rust or C++ crate to `wasm32-unknown-unknown`, and why your Rust-based bundler is a native binary.
- Dependencies: [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon|From Source Text to Silicon]]

## Source Anchors

- [LLVM Language Reference Manual](https://llvm.org/docs/LangRef.html)
- [The Architecture of Open Source Applications - LLVM](https://aosabook.org/en/v1/llvm.html)
- [Rust - Platform support and codegen backends](https://doc.rust-lang.org/rustc/platform-support.html)
- [Emscripten documentation](https://emscripten.org/docs/introducing_emscripten/about_emscripten.html)

## 1. Concept

**Simple explanation.** LLVM IR is a compiler's own private instruction language. Many languages translate *into* it and many CPUs are targeted *from* it, so each language gets every CPU without writing its own optimizer and code generator.

**Accurate mechanism.** Without a shared middle layer, supporting N languages on M architectures is N x M pieces of work, each needing its own inliner, dead-code eliminator, loop optimizer and register allocator. LLVM splits the problem at a single interface:

```txt
C / C++  ──(Clang)──┐
Rust     ──(rustc)──┼──►  LLVM IR  ──►  LLVM optimizer  ──►  x86-64
Swift    ──(swiftc)─┘                                    ──►  ARM64
                                                          ──►  RISC-V
                                                          ──►  wasm32
```

- A **frontend** only has to lower its own language to LLVM IR. It needs to know nothing about real CPUs.
- The **backend** only has to optimize IR and emit code per target. It needs to know nothing about C++ or Rust syntax.

A new language targeting LLVM IR gets every supported architecture and every optimization pass for free. That is the whole value proposition.

### Trace: what LLVM IR looks like

```c
int add(int a, int b) { return a + b; }
```

```llvm
define i32 @add(i32 %a, i32 %b) {
entry:
  %sum = add nsw i32 %a, %b
  ret i32 %sum
}
```

Three things to read off it:

- **`%a`, `%b`, `%sum` are virtual registers** — an unbounded supply, in SSA form (each is assigned exactly once). Mapping them onto the roughly sixteen real registers a CPU has is the backend's register-allocation job, done per target. So LLVM IR is a *register-style* IR, consistent with targeting register hardware — unlike Wasm's stack encoding.
- **Every value carries a type** (`i32`). Like Wasm and unlike Ignition bytecode, nothing about types is left to be discovered later, because the source language already proved them.
- **It has a readable text form**, but that is a debugging convenience. It normally exists as in-memory data structures or serialized bitcode inside one compiler invocation.

### The distinction that actually matters

|  | LLVM IR | Wasm / JVM / Ignition bytecode |
| --- | --- | --- |
| Ships to the user | No — compiler-internal | **Yes** — this artifact is what gets distributed |
| Consumed when | Build time, on your machine or CI | Run time, on the user's machine |
| Lifetime | Minutes, then discarded | The life of the program |
| Can exploit runtime facts | No — nothing has executed yet | Yes for a JIT: observed types, hot paths, which callee actually gets called |
| Portability goal | One frontend, many *build* targets | One artifact, many *user* machines |

Shape-wise they are cousins: typed, abstract, more structured than machine code. The difference is *when they are consumed*, and it dictates everything else. LLVM IR is a private scratch format thrown away before the program reaches a user; Wasm and JVM bytecode are distribution and sandboxing formats whose whole point is to still exist when the real target CPU finally becomes known.

> [!warning] LLVM is not a standard, and not universal
> There is no spec body mandating LLVM the way TC39 specifies JavaScript, and LLVM IR is explicitly *not* stability-guaranteed across versions. GCC has its own IRs (GIMPLE, RTL). Go ships its own backend. Even within LLVM, rustc has additional IRs above it (HIR, MIR) where borrow checking and much monomorphization happen before LLVM IR is emitted at all.

### Why a frontend developer meets it anyway

- **Wasm.** `wasm32` is an LLVM target. Compiling Rust or C++ to WebAssembly means source → (MIR) → LLVM IR → LLVM's Wasm backend → `.wasm`. So a Wasm module in your bundle typically passed through LLVM IR on someone's build machine — one IR feeding into another format, which is exactly the layer picture from note 01. And it makes the Wasm backend **unusual among LLVM backends**: every other one emits machine code for physical hardware, while this one emits portable bytecode, so its output is not the end of the road — a second backend-like step (Liftoff and TurboFan in V8, Cranelift in Wasmtime) is still required on the user's machine. See [[32 - Compilation and Machine Foundations/10 - Compiling to WebAssembly|Compiling to WebAssembly]].
- **Your toolchain.** esbuild is Go; swc, Rolldown, Biome, Turbopack and the Rust half of the ecosystem go through LLVM. The speed you feel in `pnpm build` is partly "this program is native machine code that never warms up."

## 2. Why It Matters

- It answers "if bytecode is a portable middle layer, why do C++ and Rust have one too?" — they have one for the *compiler's* convenience, not for the program's portability.
- It gives you the sharpest one-line contrast for an interview: **ships or does not ship**.
- It explains the shape of modern frontend tooling: the reason a Rust rewrite of a JS tool is fast is not mysterious, and it is not that Rust is magic.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

A team adds a Rust image codec to a web app and the `.wasm` lands at 2.1 MB, blowing the performance budget.

```toml
# ❌ Default release profile: LLVM optimizes for speed and keeps everything reachable
[profile.release]
opt-level = 3
lto = false
panic = "unwind"
```

Trace: `opt-level = 3` tells LLVM to inline and unroll aggressively, which trades size for speed; with LTO off, LLVM optimizes each crate's IR separately and cannot see across the boundaries to delete what is provably unreachable; `panic = "unwind"` keeps unwinding tables and formatting machinery for panic messages. Every one of those knobs is a decision made *while LLVM IR is being lowered* — the bundle size is a compiler-configuration outcome, not a Rust-language one.

```toml
# ✅ Ask LLVM for a different tradeoff
[profile.release]
opt-level = "z"       # optimize for size
lto = true            # cross-crate IR visibility → real dead-code elimination
codegen-units = 1     # one unit, so nothing is hidden from LTO
panic = "abort"       # drop unwinding machinery
strip = true
```

Paired with `wasm-opt -Oz` and `wasm-bindgen`'s snippet pruning, this routinely takes such a module well under a megabyte.

Tradeoffs, all real: `opt-level = "z"` gives up throughput, which may partly undo the reason you reached for Wasm; `lto = true` with `codegen-units = 1` serializes codegen and makes CI builds noticeably slower; `panic = "abort"` means a panic tears down the module instance instead of being catchable, so error handling has to be explicit `Result` plumbing rather than recovered panics.

> [!tip] Budget the artifact, not the language
> "Rust is fast" and "this Wasm module is 2 MB" are both true at once. Treat a Wasm dependency the way you treat any large JS dependency: measure the transferred bytes, lazy-load it behind the interaction that needs it, and check whether the compute actually beats the download.

## 4. Interview Answer

Short answer:

> LLVM IR is a shared, typed, register-style intermediate representation that many language frontends compile into and many CPU backends compile out of, so each language gets every target and every optimization pass without writing them itself. The key difference from Wasm or JVM bytecode is lifetime: LLVM IR never ships — it is discarded before the binary leaves the build machine.

Deeper answer:

> It exists to turn an N-languages-times-M-architectures problem into N plus M. Clang, rustc and swiftc lower to it; LLVM's backends lower it to x86-64, ARM64, RISC-V and wasm32. Structurally it is SSA with unlimited virtual registers and a type on every value, which is why C++ and Rust's toolchain is register-style all the way down while JVM and Wasm chose stack encodings for their shipped artifacts. The consequence of never shipping is that LLVM can only use static information — it has never seen the program run — whereas a JIT like TurboFan can specialize on observed types and hot paths. That is the real axis: an AOT compiler knows more about the target machine, a JIT knows more about the actual execution. Frontend-wise it is not academic — anything compiled to Wasm from Rust or C++ went through LLVM IR, and most of the fast Rust-based build tooling is LLVM output.

## 5. Practice

1. <details><summary>Both LLVM IR and Wasm are typed, portable and more abstract than machine code. Give the one difference from which the others follow.</summary>Lifetime. LLVM IR is consumed at build time and discarded; Wasm is consumed at run time on the user's machine. Everything else follows — Wasm needs a stable spec, a compact binary encoding and load-time validation for sandboxing; LLVM IR needs none of those and is explicitly unstable across versions.</details>
2. <details><summary>If LLVM IR is portable across CPUs, why can't you ship it and compile on the user's machine?</summary>Nothing physically stops you, and Apple's bitcode did something close. But it is a bad distribution format: no stability guarantee across LLVM versions, no defined sandboxing or validation semantics, target-specific assumptions (pointer width, ABI, calling convention) baked in during lowering, and it is much bulkier than a purpose-built binary format. Wasm was designed for the job LLVM IR only accidentally resembles.</details>
3. <details><summary>Why is LLVM IR register-style while JVM and Wasm bytecode are stack-style?</summary>They optimize for different consumers. LLVM IR is consumed by an optimizer and register allocator targeting register hardware, so naming values explicitly in SSA is exactly what the analysis wants. JVM and Wasm bytecode are shipped artifacts optimized for size and single-pass verification, where an implicit stack removes the need to encode operand slots at all.</details>
4. <details><summary>Transfer: which frontend artifact is the closest analogue of LLVM IR, and which is the closest analogue of Wasm?</summary>A bundler's internal module graph and intermediate AST are the LLVM IR analogue — real, structured, essential, and gone before deploy. The emitted JS chunks are the Wasm analogue: the shipped artifact interpreted and compiled on the user's machine. That is also why source maps exist: they are the bridge back across a layer that was supposed to be internal.</details>

## Related Notes

- [[32 - Compilation and Machine Foundations/12 - Compiled vs Interpreted and Every Stage Between|Compiled vs Interpreted, and Every Stage Between]] — the stages either side of IR, including code generation, assembly and linking.
- [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon|From Source Text to Silicon]] — where IR sits in the stack.
- [[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode|Stack, Register and Accumulator Bytecode]] — why the encoding differs.
- [[32 - Compilation and Machine Foundations/04 - AOT JIT and the Portability Tradeoff|AOT, JIT and the Portability Tradeoff]] — static knowledge vs observed knowledge.
- [[27 - Frontend Tooling and Build Systems/02 - Transpilation|Transpilation]] — the same frontend/backend split in JS tooling.
- [[10 - Modules/09 - From Source to Browser|From Source to Browser]] — the JS pipeline this mirrors.
- [[90 - Labs/07 - Bytecode VM Lab|Bytecode VM Lab]] — write a liveness pass and a register allocator yourself.
