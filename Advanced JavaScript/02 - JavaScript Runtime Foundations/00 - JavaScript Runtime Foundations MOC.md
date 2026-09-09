---
tags:
  - javascript
  - moc
  - runtime
module: 02 - JavaScript Runtime Foundations
priority: must-know
status: solid
---

# JavaScript Runtime Foundations MOC

This module teaches the machine model behind every JavaScript line you write: what the language specification defines, what the engine executes, and what the host runtime adds on top. It gives you the vocabulary — execution context, call stack, heap, realm, agent, job — that later modules on closures, `this`, async, and performance depend on. Mastering it unlocks debugging `window is not defined` in Next.js, promise-before-timer output questions, stack overflows, and memory leaks.

## Prerequisites

- [[00 - Start Here|Start Here]] — how to study every note in this vault.
- [[01 - Roadmap|Roadmap]] — where this module sits in the dependency order.

## Reading Order

1. [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]] — separates language spec from host APIs so you know which authority answers which question.
2. [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]] — names the engine pipeline and the runtime layer that wraps it.
3. [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]] — the runtime record that explains hoisting, TDZ, closures, and `this` later.
4. [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]] — run-to-completion, stack traces, and why long sync work freezes the UI.
5. [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]] — references, reachability, and the retaining paths behind frontend leaks.
6. [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]] — worlds, workers, and why promise reactions never run synchronously.
7. [[02 - JavaScript Runtime Foundations/07 - Runtime Foundations Checklist|Runtime Foundations Checklist]] — active self-test to prove the module is mature.

## Companion References

- [[02 - JavaScript Runtime Foundations/08 - Engine and Compilation Glossary|Engine and Compilation Glossary]] — plain-English lookup for engine jargon (bytecode, tiers, deopt, hidden classes, inline caches); read before note 02 if engine internals are new.
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] — deep-dive under note 02: threaded dispatch, pre-compiled handlers, the interrupt budget, on-stack replacement, bytecode flushing. Optional for interview readiness; read it when "the interpreter runs the bytecode" stops feeling like an explanation.
- [[32 - Compilation and Machine Foundations/00 - Compilation and Machine Foundations MOC|Compilation and Machine Foundations MOC]] — the layer *below* this module: bytecode to machine code, stack vs register encodings, LLVM, AOT vs JIT, the CPU and the memory hierarchy. Entirely optional for interviews; read it when "compiled to machine code" stops feeling like an explanation.

## You're Done When

- [ ] I can explain ECMAScript as the spec and JavaScript as host implementations, and sort features into language vs host (DOM, `fetch`, timers).
- [ ] I can define engine vs runtime in one sentence and describe the parse, compile, optimize, deoptimize pipeline.
- [ ] I can explain an execution context's parts (lexical environment, variable environment, `this`, realm) and connect it to hoisting, TDZ, and closures.
- [ ] I can draw the call stack for nested calls, explain run-to-completion, and connect long synchronous work to blocked input and rendering.
- [ ] I can explain heap reachability, name common frontend retaining paths, and connect effect cleanup to memory lifetime.
- [ ] I can explain realms (why `Array.isArray` beats `instanceof Array` across iframes) and agents (workers, `SharedArrayBuffer` with COOP/COEP).
- [ ] I can explain that promise reactions are scheduled jobs processed at microtask checkpoints, and trace the A/B/promise/microtask/timer output correctly.
- [ ] I can name V8's compilation tiers (Ignition, Sparkplug, Maglev, TurboFan) and explain hidden classes and inline caches — monomorphic vs megamorphic — as the mechanism behind stable data shapes.
- [ ] I can name the TC39 stages and explain what WinterTC standardizes across server runtimes.
- [ ] I can explain structured clone limits, transfer vs copy for large buffers, and why `Atomics.wait` is banned on the main thread.
- [ ] I can answer "what happens when JavaScript runs code?" in two minutes using stack, heap, jobs, tasks, and host APIs.
- [ ] (deep-dive) I can explain that there is no *central switch-based* dispatch loop — the fetch-and-dispatch step sits at the tail of every handler — that bytecode handlers ship pre-compiled in the browser binary, and that tier-up runs on a bytecode-size-scaled budget charged by function entries and loop back-edges.
