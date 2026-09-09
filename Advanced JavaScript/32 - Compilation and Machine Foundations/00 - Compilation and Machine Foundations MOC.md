---
tags: [compilation, machine-model, moc]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
---

# Compilation and Machine Foundations MOC

This module answers the question that sits *underneath* [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]: what is bytecode actually a step *towards*, and what happens at the end of the chain? It walks the full path from text you type to voltages in silicon — source, bytecode, compiler IR, machine code, CPU, memory hierarchy — and names each layer with the real term for it.

None of this is required to pass a mid-level frontend interview. It is here because the vault's engine notes keep bottoming out in words that get used as if they were self-explanatory — "bytecode", "machine code", "binary", "register", "compiled" — and because the *shape* of the tradeoffs down here repeats one level up, in your own work: build-time vs runtime, portable artifact vs specialized artifact, speculate-and-recover vs prove-ahead-of-time. Svelte-vs-React is the same argument as Rust-macros-vs-Java-reflection. Recognizing that is the payoff.

> [!tip] Start at note 12, whatever its number says
> [[32 - Compilation and Machine Foundations/12 - Compiled vs Interpreted and Every Stage Between|Compiled vs Interpreted, and Every Stage Between]] is the front door: it dissolves the compiled-versus-interpreted question and walks all ten stages from characters to executing instructions once, end to end, routing to every other note for the detail. It carries a number in the teens only because this module appends rather than renumbers. If you read one note here, read that one.

> [!warning] Implementation scope — read this before quoting anything here
> This module names concrete engines on purpose, which makes it useful and makes it perishable. V8 internals, bytecode opcodes, tiering heuristics, thresholds, printed bytecode and generated assembly are **implementation details that change between versions and differ across engines** — treat them as explanatory models, never as API guarantees. When a claim matters, check which of three kinds it is:
>
> | Kind | Example | How long it stays true |
> | --- | --- | --- |
> | **Specification** | ECMAScript jobs; the HTML event loop's microtask checkpoints; Wasm's validation rules | Years; changes go through a standards process |
> | **Named implementation** | "V8 13.x / Chrome M137 speculatively inlines `call_indirect` targets" | One or two release cycles — name the engine *and* the version |
> | **Teaching model** | "an interpreter is a loop with a switch"; the ten-stage pipeline diagram | Deliberately simplified; correct as a mental model, wrong as a description of V8 |
>
> Every note here carries `Source Anchors`. If a claim you want to repeat is not traceable to one of them, treat it as a teaching model rather than a fact.

> [!tip] Read the rest as a horizontal, not a ladder
> The interview-facing modules are dependency-ordered — you need scope before closures. This one is not. After note 12, each note stands alone, and the honest reason to read any of them is "a word in the engine notes stopped feeling like an explanation."

## Prerequisites

- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]] — the tiers, type feedback, and deoptimization are assumed throughout.
- [[02 - JavaScript Runtime Foundations/08 - Engine and Compilation Glossary|Engine and Compilation Glossary]] — read first if "bytecode" and "JIT" are still fuzzy; this module goes *below* that glossary, not around it.
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] — how Ignition's bytecode actually executes; note 01 here picks up where that ends.

## Reading Order

0. [[32 - Compilation and Machine Foundations/12 - Compiled vs Interpreted and Every Stage Between|Compiled vs Interpreted, and Every Stage Between]] — **start here.** The dichotomy dissolved, all ten stages once through, the four implementation strategies side by side, and the bundler-is-a-linker mapping.
1. [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon|From Source Text to Silicon]] — the full layer stack, and why binary, hex, assembly and machine code are not four things.
2. [[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode|Stack, Register and Accumulator Bytecode]] — the three ways to encode an instruction set, why Wasm chose one and Ignition another.
3. [[32 - Compilation and Machine Foundations/03 - LLVM and Compiler IR|LLVM and Compiler IR]] — the IR that never ships, and why it exists at all.
4. [[32 - Compilation and Machine Foundations/04 - AOT JIT and the Portability Tradeoff|AOT, JIT and the Portability Tradeoff]] — why Java JITs despite static types, and what the frontend's version of AOT is.
5. [[32 - Compilation and Machine Foundations/05 - Reflection and Compile-Time Codegen|Reflection and Compile-Time Codegen]] — runtime introspection vs generating code before the program exists; React vs Svelte as the same decision.
6. [[32 - Compilation and Machine Foundations/06 - The CPU as Orchestrator|The CPU as Orchestrator]] — MMIO, drivers, DMA, interrupts, and why the GPU is a second computer.
7. [[32 - Compilation and Machine Foundations/07 - Registers Caches and RAM|Registers, Caches and RAM]] — the memory hierarchy, and the parts of it your JS accidentally controls.
8. [[32 - Compilation and Machine Foundations/08 - Compilation and Machine Foundations Checklist|Compilation and Machine Foundations Checklist]] — active self-test.

## Companion References

Appended after the checklist, in the vault's usual pattern — read when the corresponding note stops feeling finished.

- [[32 - Compilation and Machine Foundations/09 - Interpreters Dispatch and the Two Stacks|Interpreters, Dispatch and the Two Stacks]] — deep-dive under note 02: the VM's operand stack versus the hardware call stack (and why generators can pause), what `PUSH`/`ADD` actually compile to, and why a host compiler optimizes your interpreter but never the bytecode it runs.
- [[32 - Compilation and Machine Foundations/10 - Compiling to WebAssembly|Compiling to WebAssembly]] — the WebAssembly track, part 1: the whole pipeline from Rust/C++ or `.wat` down to machine code, with a byte-level walk through a real `.wasm`, LLVM's Wasm backend, and Liftoff. Read after notes 01-03.
- [[32 - Compilation and Machine Foundations/12 - Compiled vs Interpreted and Every Stage Between|Compiled vs Interpreted, and Every Stage Between]] — the module's front door, appended last but read first: the full stage pipeline including the compiler front end (lexer, parser, semantic analysis) and the machine-facing tail (assembler, linker, loader, fetch-decode-execute) that the other notes assume.
- [[32 - Compilation and Machine Foundations/11 - Wasm Speculation and Deopt|Wasm Speculation and Deopt]] — part 2: why static types remove type speculation but not all speculation, `call_indirect` inlining as a correctness bet, guard branch versus real deopt, and what WasmGC has to do with it.
- [[90 - Labs/07 - Bytecode VM Lab|Bytecode VM Lab]] — build all of it: stack IR, register IR, a liveness pass with spilling, and an assembly-emitting backend. 6-10 hours, off the interview path; read the lab's own warning first.

## You're Done When

- [ ] I can name every layer between source text and executing silicon, and say which layers are software translating and which layer is hardware executing.
- [ ] I can dissolve "is JavaScript compiled or interpreted?" rather than answering it, and give the Hermes-versus-V8 counterexample.
- [ ] I can name all ten stages in order and say which class of error each one owns.
- [ ] I can explain why a bundler is a linker, and name three failure modes the mapping predicts.
- [ ] I can explain that assembly and machine code are one thing in two notations, that hex is a notation for bits, and that bytecode is a different layer entirely.
- [ ] I can contrast stack-based, register-based and accumulator-based instruction encodings, say which real systems chose which, and explain why the choice stops mattering once code is compiled.
- [ ] I can explain what LLVM IR is for and give the single sharpest difference between it and Wasm/JVM bytecode.
- [ ] I can explain why a statically typed language still benefits from a JIT, and name what a JIT knows that an AOT compiler cannot.
- [ ] I can explain reflection, explain Rust's macro alternative, and map both onto React reconciliation vs Svelte/React-Compiler-style build-time output.
- [ ] I can explain how a CPU reaches RAM, a GPU and a network card, and why DMA and interrupts exist.
- [ ] I can order registers, L1/L2/L3 and RAM by cost, and explain which JS-level choices change which layer gets hit.
- [ ] (companion) I can separate a VM's operand stack from the hardware call stack, and name what each can do that the other cannot.
- [ ] (companion) I can explain why a host compiler optimizes an interpreter's engine but never the bytecode program it executes — and what that implies about JITs.
- [ ] (companion) I can trace a `.wasm` from Rust source to executing machine code and say which layer introduces the stack encoding and which layer removes it.
- [ ] (companion) I can explain why "Wasm never deoptimizes because it's statically typed" is wrong in its *because*, and what changed in Chrome M137.

## Related Notes

- [[26 - How the Web Works/06 - How V8 Runs Your Code|How V8 Runs Your Code]] — the browser-facing version of this pipeline.
- [[12 - Advanced Language Concepts/14 - Typed Arrays and Binary Data|Typed Arrays and Binary Data]] — the JS API that exposes raw memory layout.
- [[12 - Advanced Language Concepts/15 - Proxy and Reflect|Proxy and Reflect]] — JavaScript's own reflection surface.
- [[27 - Frontend Tooling and Build Systems/00 - Frontend Tooling and Build Systems MOC|Frontend Tooling and Build Systems MOC]] — build-time vs runtime, one abstraction level up.
- [[01 - Roadmap|Roadmap]]
