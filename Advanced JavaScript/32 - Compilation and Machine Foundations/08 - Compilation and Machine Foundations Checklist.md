---
tags: [compilation, machine-model, checklist]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
---

# Compilation and Machine Foundations Checklist

Use this as an active test, not a reading list. Mark an item complete when you can explain it out loud, unprompted, and answer one follow-up — not when you have read the note.

This module is #deep-dive. Nothing here is required to pass a mid-level frontend loop, and none of it should displace [[02 - JavaScript Runtime Foundations/07 - Runtime Foundations Checklist|Runtime Foundations]] or [[09 - Event Loop Advanced/08 - Event Loop Checklist|Event Loop]] practice. Its value is that it stops the engine notes from bottoming out in undefined words, and that the tradeoffs down here are the same ones you argue about in build config.

## Source Anchors

- [V8 - Understanding V8's bytecode](https://v8.dev/blog/understanding-v8-bytecode)
- [WebAssembly Core Specification](https://webassembly.github.io/spec/core/)
- [LLVM Language Reference Manual](https://llvm.org/docs/LangRef.html)
- [Chrome - RenderingNG architecture](https://developer.chrome.com/docs/chromium/renderingng-architecture)
- [V8 - Elements kinds in V8](https://v8.dev/blog/elements-kinds)

## The Dichotomy and the Ten Stages (front-door note 12)

- [ ] I can explain why "compiled language" and "interpreted language" are not real categories, with a counterexample in both directions.
- [ ] I can give the Hermes-versus-V8 contrast: same language, ahead-of-time bytecode and no JIT versus lazy bytecode and four tiers.
- [ ] I can name all ten stages in order, and what each consumes and produces.
- [ ] I can say which stage owns a syntax error, a type error, an unresolved import, and a wrong API shape — and why no earlier stage can catch the last one.
- [ ] I can explain why a lexer cannot decide block-versus-object-literal but a parser can, in terms of regular versus context-free.
- [ ] I can explain longest-match lexing and how automatic semicolon insertion sits at the lexer/parser boundary.
- [ ] I can explain recursive descent, precedence climbing, and why left recursion breaks a naive descent parser.
- [ ] I can say why production compilers hand-write parsers instead of generating them, and what a cover grammar is for.
- [ ] I can locate `tsc` precisely: stages 1-3 plus erasure, nothing after — and derive the shape of its guarantees from that.
- [ ] I can explain that TDZ and hoisting are semantic-analysis (binding) artefacts, not runtime behaviour.
- [ ] I can say what an object file contains beyond machine code, and why "undefined reference" is a link-time error.
- [ ] I can contrast static and dynamic linking, and map both onto bundling, externals, import maps and code splitting.
- [ ] I can describe what the loader does before the entry point runs.
- [ ] I can state the fetch-decode-execute cycle and name what real cores do on top of it.
- [ ] I can place the four implementation strategies in a table and give an example of each, including a tree-walking interpreter I have written myself.
- [ ] I can state the general rule about facts that exist only in earlier stages, and give the minified-class-name failure as an instance.

## Layers and Notations

- [ ] I can name the four layers — source text, bytecode, compiler IR, machine code — and say who consumes each.
- [ ] I can explain that assembly and machine code are one layer in two notations, and that hex is a notation for bits rather than a kind of code.
- [ ] I can explain why bytecode is portable and machine code is not, in one sentence, without saying "because it's higher level".
- [ ] I can say what the CPU does with machine code — executes it directly, bits as control signals — and why that is categorically unlike interpretation.
- [ ] I can catch the sentence "JavaScript is interpreted" and say precisely what is wrong with it.
- [ ] I can point at `Add a0, [0]` and explain what the feedback-slot operand implies about JavaScript.

## Instruction Encodings

- [ ] I can write the same expression as stack, register, and accumulator bytecode.
- [ ] I can explain what "hybrid" means in Ignition's case, given that an accumulator is itself a register.
- [ ] I can name which real systems chose stack (Wasm, JVM, CPython) and which chose register (Lua 5.x, Dalvik/ART), and give the reason each way.
- [ ] I can explain why the encoding affects interpretation cost but not compiled speed, and name the step that erases it.
- [ ] I can rebut "Wasm is stack-based, so it must be slower" and give the real reasons a Wasm module might underperform.
- [ ] I can state the two orthogonal axes — bytecode encoding vs execution strategy — and fill in all four cells of the matrix with real systems.
- [ ] I can rebut "register bytecode is closer to hardware, so its values live in real CPU registers" and name what actually decides that.
- [ ] I can say plainly that Ignition is a register machine and not a stack machine, and say what its hybrid is a hybrid *of*.

## Compiler IR

- [ ] I can explain the N-languages-times-M-architectures problem LLVM solves, and what a frontend and a backend each have to know.
- [ ] I can read an LLVM IR snippet and identify virtual registers, SSA, and the explicit types.
- [ ] I can give the one difference between LLVM IR and Wasm/JVM bytecode that all the others follow from.
- [ ] I can explain why LLVM IR would be a bad distribution format even though it is portable.
- [ ] I can say where LLVM sits in a Rust-to-Wasm build, and why my Rust-based bundler starts fast.

## AOT, JIT and Phase

- [ ] I can state the real variable — where the target CPU becomes known — and derive both models from it.
- [ ] I can give the two independent reasons Java JITs despite full static typing, and keep them separate.
- [ ] I can explain why Java's JIT speculation is a different problem from V8's, and not repeat "Java JITs because it's dynamic".
- [ ] I can explain what GraalVM Native Image gains and gives up, and why that proves bytecode was a choice.
- [ ] I can place Wasm on the axis: portable artifact, static types, single-pass compile, no warm-up.
- [ ] I can name the frontend's AOT levers — bundling, prerendering, compile-time reactivity, code caching — and the failure mode they share.
- [ ] I can ask the phase question about any optimization: is this input knowable at build time, for every future consumer?

## Reflection and Codegen

- [ ] I can define reflection as inspect, invoke, modify — and name its three costs.
- [ ] I can explain why reflection breaks closed-world analysis, and give the bundler equivalent.
- [ ] I can explain what "zero runtime cost" means for `#[derive(Serialize)]` given that code genuinely is generated.
- [ ] I can say what Rust has instead of reflection (`dyn Trait`, `Any`/`TypeId`) and why neither is introspection.
- [ ] I can locate JSX correctly as build-time and name what React's runtime overhead actually consists of.
- [ ] I can explain why a compiler can shrink React's diff but not eliminate it, using the runtime-values argument.
- [ ] I can diagnose a component-registry tree-shaking failure as a closed-world/open-world mismatch and fix it with a static registry.

## Hardware

- [ ] I can explain how the CPU reaches RAM, and how memory-mapped I/O makes device registers look like memory.
- [ ] I can explain what a driver is, in terms of register protocol.
- [ ] I can explain DMA and say what the CPU is doing during the transfer.
- [ ] I can explain interrupts, and connect them to why the event loop has an I/O side at all.
- [ ] I can explain why the GPU is a second computer rather than a device, and what the CPU's role is.
- [ ] I can derive the compositor rule — `transform`/`opacity` vs `width`/`top` — from that, rather than reciting it.
- [ ] I can explain why `getImageData` and `readPixels` stall.

## Memory Hierarchy

- [ ] I can order registers, L1, L2, L3 and RAM by rough cost and size, and state the stable ratio rather than exact cycles.
- [ ] I can explain why `a + b` in a hot function may touch no memory while `user.age` always does.
- [ ] I can define a cache line and explain why locality usually beats instruction count.
- [ ] I can give the memory-layout reason stable object shapes matter, distinct from the deopt reason.
- [ ] I can explain how one hole or one mixed type changes an array's element kind and what that costs.
- [ ] I can explain when a typed array or parallel columns beats an array of objects — and articulate the readability cost I am paying.
- [ ] I can ask "compute-bound or memory-bound?" before proposing Wasm or a worker, and say why the answer changes the fix.

## Interpreters and Dispatch (companion note 09)

- [ ] I can name the two stacks — the VM's operand stack and the hardware call stack — and say who manages each.
- [ ] I can explain that even the hardware stack is not a hardware data structure: `PUSH` is a memory write plus stack-pointer arithmetic.
- [ ] I can give the three reasons a VM heap-allocates its operand stack and frames, and name the JavaScript features that depend on the third one.
- [ ] I can expand one bytecode `ADD` into the machine instructions it becomes, and say why the ALU forces that shape.
- [ ] I can explain the two-programs argument: the host compiler optimizes the interpreter engine and never the bytecode it runs.
- [ ] I can say what Sparkplug actually deletes, and why that is a dispatch story rather than an optimization story.
- [ ] I can correct the `while`-plus-`switch` model of V8's interpreter and name what it really does instead.
- [ ] I can spot the "re-deciding the same thing every execution" mistake in ordinary frontend code and name the compile-once fix.
- [ ] I can explain V8's actual generator mechanism: the register file lives in the interpreter's stack frame, `SuspendGenerator` copies it into the generator object, `ResumeGenerator` restores it.

## WebAssembly (companion notes 10 and 11)

- [ ] I can draw the full pipeline: Rust/C++ → LLVM IR → LLVM Wasm backend → `.wasm` → engine decoder → Liftoff/TurboFan → machine code.
- [ ] I can say which layer introduces the stack encoding, which layer undoes it, and why the operand stack is never executed.
- [ ] I can explain why nothing about Rust or C++ is stack-machine-shaped, and where the stack model actually comes from.
- [ ] I can explain both senses of "binary" and place `.wat`, `.wasm`, assembly and machine code in the 2x2.
- [ ] I can name the sections of a `.wasm` binary, explain the tagged length-prefixed structure, and say why that makes streaming compilation possible.
- [ ] I can identify `20 00 20 01 6A 0B` and say what each byte is.
- [ ] I can explain what an LLVM backend is, what a target triple selects, and why the Wasm backend is unusual among them.
- [ ] I can explain why Liftoff exists and what problem TurboFan-only compilation caused.
- [ ] I can separate the three Wasm load costs — download, compile, run — and name the distinct fix for each.
- [ ] I can state the two independent facts hidden inside "Wasm never deopts because it's statically typed."
- [ ] I can explain why `call_indirect`'s target is not derivable from the binary, and what speculative inlining does with that.
- [ ] I can explain why a wrong speculation is a *correctness* problem rather than a performance one.
- [ ] I can distinguish a guard branch from a true deoptimization and say when each suffices.
- [ ] I can explain why WasmGC benefits most from call-target speculation, and which languages benefit least.
- [ ] I can connect all of this back to mono/poly/megamorphic call sites in JavaScript.

## Synthesis

- [ ] I can explain, in one connected answer, what happens between typing `a + b` and a transistor switching.
- [ ] I can name three places in this vault where the same build-time-versus-runtime tradeoff appears with different labels.
- [ ] I can explain why "speculate and recover" (V8) and "prove ahead of time" (Rust, Wasm) are both correct designs for their constraints.
- [ ] I can tell when this knowledge is load-bearing in an interview — reading a profile, justifying Wasm, explaining framework tradeoffs — and when quoting it is just noise.

## Related Notes

- [[32 - Compilation and Machine Foundations/00 - Compilation and Machine Foundations MOC|Compilation and Machine Foundations MOC]]
- [[02 - JavaScript Runtime Foundations/07 - Runtime Foundations Checklist|Runtime Foundations Checklist]]
- [[02 - JavaScript Runtime Foundations/08 - Engine and Compilation Glossary|Engine and Compilation Glossary]]
- [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]]
- [[90 - Labs/07 - Bytecode VM Lab|Bytecode VM Lab]] — the build that proves the companion note
