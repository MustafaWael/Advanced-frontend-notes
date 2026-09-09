---
tags: [labs, compilation, machine-model]
module: "90 - Labs"
priority: deep-dive
status: not-started
aliases: [bytecode vm lab, stack machine lab, build a compiler lab]
---

# Lab 07 — Build a Bytecode VM (Stack IR, Register IR, and a Real Backend)

Build the thing V8 is. Write a compiler from an AST to a stack-based IR, a VM that executes it, then the register-based counterpart with its own allocator — and measure the difference instead of taking it on faith. Finish by replacing the interpreter with a backend that emits real x86-64 assembly, so the same program runs with zero dispatch overhead.

> [!warning] Read this before starting
> This lab is `#deep-dive` and it is **off the interview path**. Nothing in it will be asked in a mid-level frontend loop. Budget **6-10 hours** for stages 1-4 and treat stage 5 as optional. Do not start it while `#must-know` notes are still `not-started` — [[18 - Revision Plans/00 - Revision Plans MOC|Revision Plans]] has the work that actually moves an interview. The reason to do it anyway: the compile-once/run-many distinction it forces you to implement is the single most transferable idea in [[32 - Compilation and Machine Foundations/00 - Compilation and Machine Foundations MOC|module 32]], and you will never again wonder what "bytecode" means.

## Prerequisites

- [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon|From Source Text to Silicon]] · [[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode|Stack, Register and Accumulator Bytecode]] · [[32 - Compilation and Machine Foundations/09 - Interpreters Dispatch and the Two Stacks|Interpreters, Dispatch and the Two Stacks]]
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] — the thing you are building a toy version of, and the ways your toy will differ.
- [[32 - Compilation and Machine Foundations/07 - Registers Caches and RAM|Registers, Caches and RAM]] — for stage 4's measurements.

## Build Brief

TypeScript (strict), Vitest, Node. No parser generators, no libraries — the point is that every layer is yours. Language to implement: arithmetic over numbers and variables, then `if`/`while`, then function calls.

**Stage 1 — Lexer, parser, AST.** Recursive descent, hand-written. Support `+ - * /`, parentheses, number literals, identifiers, and correct precedence and associativity. Output a discriminated-union AST (`{ kind: "Num" } | { kind: "Var" } | { kind: "BinOp" }`), so `tsc` forces you to handle every node in every later pass.

**Stage 2 — Stack IR + VM.** Compile the AST to a flat instruction array by postorder walk: emit left, emit right, emit the operator. No register allocation, no naming — that is the whole selling point of stack IR. Then write the VM: an operand stack plus a dispatch loop. Add `DUP` and use it to compile `x * x` from a single load, so you feel the stack-juggling cost first-hand.

**Stage 3 — Register IR + VM.** Same AST, new backend. Every `compile` call now *returns which register holds its result*, and you need a `freshReg()` counter — the mini allocator the stack version never needed. Instructions become explicit: `{ op: "ADD", dest: "r2", left: "r0", right: "r1" }`. Note what disappeared (all push/pop/DUP bookkeeping) and what appeared (naming, and unbounded virtual registers).

**Stage 4 — Liveness and physical allocation.** This is the stage that earns the lab. Compute, for each virtual register, the instruction range where it is live (first write to last read). Then map virtual registers onto a *fixed* pool — start with 4 — reusing a slot the moment its occupant's last use has passed, and **spilling** to an array when 4 is not enough. Verify against the note's example: `(a + 3) * b` uses 5 virtual registers and should collapse to 2 physical ones.

**Stage 5 — A real backend (optional).** Replace `run()` with `emitAsm()`: walk the allocated register IR and emit x86-64 assembly text, assemble with `as`/`nasm`, link with `ld` or `gcc`, and execute it. `ADD dest=r2 left=r0 right=r1` becomes `mov eax, ...; add eax, ...`. When the binary prints the same number your VM did, you have crossed from interpreter to compiler.

**Stage 6 — Control flow and calls (extension).** Add `JMP` / `JMP_IF_FALSE` with label resolution, and compile `if`/`while`. Then function calls, which force the distinction the concept note makes: a **frame stack** (return address + locals) that is separate from the operand stack.

## Acceptance Criteria

- [ ] `tsc --noEmit` passes with `strict`; every pass switches exhaustively over the AST union with no `default` fallthrough and no `any`.
- [ ] Both VMs produce identical results for a shared table of at least 20 expressions, asserted in one parameterized test — this is your correctness harness for every later stage.
- [ ] `x * x` compiles to a single `LOAD` in **both** IRs: via `DUP` in the stack version, and via naming `r0` twice in the register version. You can state which cost each pays.
- [ ] Your liveness pass collapses `(a + 3) * b` from 5 virtual registers to 2 physical ones, and a test asserts the physical count.
- [ ] A deliberately register-hungry expression (nest 6+ live intermediates) triggers **spilling**, and a test asserts both that it spilled and that the result is still correct.
- [ ] A disassembler prints either IR as numbered text (`0: LOAD a`, `1: PUSH 3`, …). Debugging a compiler without one is misery — write it early, not late.
- [ ] You can state, from your own measurements, how many instruction dispatches each IR needs for the same expression, and the ratio.
- [ ] (Stage 5) An assembled binary prints the same result as both VMs for the shared expression table.

## Debugging Tasks (create, observe, fix)

1. **The unbalanced stack.** In the stack compiler, emit the operator *before* the right operand. Observe: for `-` and `/` the result is silently wrong; for others it is right by commutativity. Then write a stack-depth verifier that walks the instruction array tracking net stack effect per opcode and rejects any program that ends with depth ≠ 1. Document why Wasm can do exactly this in a single linear pass, and why that is a security property and not just a nicety ([[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode|encodings]]).
2. **The premature reuse.** In stage 4, make liveness end a range at the *first* read instead of the last. Observe a physical register being clobbered while still needed, producing a wrong answer with no crash. Fix, and write down why this class of bug is invisible to tests that only check one expression.
3. **The stack that is not the stack.** Feed the VM a deeply right-nested expression (10,000 terms). Then rewrite `run()` recursively (one function call per node) and feed it the same input. One overflows the *hardware* stack and the other does not. Explain which stack ran out and why, with reference to the two-stacks table.
4. **Dispatch overhead, measured.** Time 1,000,000 evaluations of one expression on each VM. Then hoist the work: precompile the expression into a closure tree (`compileToClosure(ast): (env) => number`) and time that. Record all three numbers. The closure version should be dramatically faster than both, and **for the same reason a JIT beats an interpreter** — no opcode fetch, no dispatch, monomorphic call sites. This is the measurement that makes [[32 - Compilation and Machine Foundations/09 - Interpreters Dispatch and the Two Stacks|Fact 3]] real.
5. **The wrong layer.** Try to speed up the interpreted program by optimizing the interpreter — swap `switch` for a handler lookup table, inline the arithmetic, use a `Float64Array` for the operand stack. Record the gain. Then compare it to the closure version's gain. Write one paragraph on why the host-level optimizations plateau: you are optimizing the engine, never the program.

## Testing Expectations

- One parameterized correctness table shared by every backend (stack VM, register VM, allocated register VM, closure compiler, and stage 5's binary). Adding a backend means adding one row to the runner, not a new test suite.
- Property-style test: generate random small ASTs, evaluate each with a plain recursive tree-walk *oracle*, and assert every backend agrees. This catches precedence, associativity and allocation bugs that hand-written cases miss.
- Snapshot tests on the disassembler output for a handful of expressions, so a codegen change that alters instruction sequences shows up as a reviewable diff.
- A test asserting the stack-depth verifier rejects a deliberately malformed program.
- Benchmarks are recorded numbers in your retrospective, not assertions — do not put timing thresholds in CI.

## Performance and Security Considerations

- **Measure dispatch count, not just wall time.** Instrument each VM with a counter. Instruction count is the stable number; wall time varies with what tier V8 happened to reach while running *your* interpreter — which is itself a nice demonstration of the problem.
- **Your operand stack is a JS array — decide deliberately.** Try `number[]` versus a preallocated `Float64Array` with an index, and note which one V8 keeps packed ([[07 - Arrays and Iteration/01 - Array Internals|element kinds]]).
- **Validation is a sandbox boundary.** Your stage-1 debugging task builds a verifier. Note that this is the same job Wasm's validator does before compiling untrusted bytes, and that an unvalidated stack machine reading past its own operand stack is a memory-safety bug in a real VM.
- If you attempt stage 5, note that emitting code into executable memory is exactly what CSP's restrictions on `eval` and JIT-less browser modes are about — the ability to write-then-execute memory is a real attack surface ([[20 - Network and Security/06 - CSRF and CSP|CSP]]).

## Interview Questions

1. "You built the same language twice. When would you actually ship stack IR rather than register IR?" Answer with the distribution-format-versus-optimization-pipeline split, and cite Wasm's validator as the concrete reason.
2. Your stage-4 allocator collapsed 5 virtual registers to 2. Explain liveness in one sentence, then explain what spilling is and when it happens.
3. "Would rewriting your VM in Rust make user scripts fast?" Answer with the two-programs argument, and use your stage-5 measurement as evidence.
4. Your recursive `run()` overflowed on a 10,000-term expression and the loop version did not. Which stack overflowed, and how does that connect to why generators can pause but a native frame cannot?
5. Where in your day job have you already written the closure-compilation fix — separating compile-once from run-many — without calling it that?

## Retrospective

[[98 - Vault Operations/Templates/Lab Retrospective Template|Template]] — plus, specifically:

- The three benchmark numbers from debugging task 4, and the plateau number from task 5.
- One sentence on what you now understand about V8 that you previously accepted on authority.
- The list of ways your toy VM differs from V8 (threaded dispatch rather than a loop, type feedback, hidden classes, tiering, OSR). Write it from memory first, then check against [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]]. The gaps are the interesting part.

## Related Notes

- [[32 - Compilation and Machine Foundations/00 - Compilation and Machine Foundations MOC|Compilation and Machine Foundations MOC]]
- [[32 - Compilation and Machine Foundations/09 - Interpreters Dispatch and the Two Stacks|Interpreters, Dispatch and the Two Stacks]]
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]]
- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
- [[90 - Labs/00 - Labs MOC|Labs MOC]]
