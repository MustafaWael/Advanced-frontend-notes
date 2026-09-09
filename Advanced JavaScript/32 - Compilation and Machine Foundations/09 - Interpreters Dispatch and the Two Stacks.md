---
tags: [compilation, machine-model, interpreters]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
aliases: [Operand Stack vs Call Stack, Dispatch Overhead, Two Stacks, Why JIT Exists]
---

# Interpreters, Dispatch and the Two Stacks

## Maturity Target

- Priority: #deep-dive
- Study time: 30-40 minutes
- Interview signal: you can separate a VM's operand stack from the hardware call stack, explain what `PUSH`/`ADD` actually become in machine instructions, and say precisely why a JIT is a *separate program* rather than a compiler flag.
- Production signal: you can explain why generators and `async` functions are pausable while a C stack frame is not, and you stop expecting a faster host language to speed up interpreted work.
- Dependencies: [[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode|Stack, Register and Accumulator Bytecode]]

## Source Anchors

- [WebAssembly Core Specification - Validation](https://webassembly.github.io/spec/core/valid/index.html)
- [V8 - Understanding V8's bytecode](https://v8.dev/blog/understanding-v8-bytecode)
- [V8 - Firing up the Ignition interpreter](https://v8.dev/blog/ignition-interpreter)
- [V8 - Sparkplug, a non-optimizing JavaScript compiler](https://v8.dev/blog/sparkplug)
- [Java Virtual Machine Specification - Frames](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html#jvms-2.6)
- [MDN - Iterators and generators](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Iterators_and_generators)

## 1. Concept

**Simple explanation.** A stack machine's "stack" is not a CPU feature. It is an array the interpreter keeps in memory, and it is a completely different thing from the hardware call stack your function frames live on. Confusing the two is what makes the whole model feel like magic.

**Accurate mechanism.** Three separate facts, in order.

### Fact 1 — there are two stacks, and they are unrelated

| | The VM's operand stack | The hardware call stack |
| --- | --- | --- |
| What it is | An array the interpreter allocates — on the heap, or as slots inside its own frame | A region of memory addressed by one CPU register (`RSP` on x86-64, `SP` on ARM) |
| What it holds | The values *your bytecode* is computing with | The interpreter's own return addresses, spilled locals, saved registers |
| Who manages it | The interpreter, explicitly, in its own code | The CPU and the calling convention, implicitly, via `call`/`ret` |
| Resizable | Yes — it is just an array you can grow | Not arbitrarily; overflow terminates the process |
| Pausable | Yes — it is data the VM can copy out and keep alive | No — you cannot easily suspend a native frame and resume it later |

Even the hardware "stack" is not a hardware data structure. There is no push circuit. `PUSH` is a convention over ordinary memory access plus pointer arithmetic:

```asm
; PUSH on x86-64, expanded
sub rsp, 8          ; move the stack pointer down
mov [rsp], rax      ; write the value at that address

; POP, expanded
mov rax, [rsp]      ; read the value
add rsp, 8          ; move the pointer back up
```

`RSP` is a register holding an address. That is the entire mechanism.

> [!tip] This is why generators and `async` functions can pause — and V8's mechanism is concrete
> The last row of that table is the load-bearing one for frontend work, and V8 shows exactly how it is bought. Ignition's register file lives in the interpreter's own **stack frame**, not on the heap — so suspension cannot mean "keep the frame alive," because a native frame dies when its function returns. Instead V8 **copies it out**: the `SuspendGenerator` bytecode stores the parameters and the register file into the generator object (a heap object), along with the current context and bytecode offset; `ResumeGenerator` imports that register file back and marks the generator executing. A paused generator is therefore a heap snapshot of a frame, not a frozen frame.
>
> That is what makes [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]' framing — "a suspendable call-stack frame you resume with `.next()`" — implementable at all, and it is the same machinery `await` uses. The general principle behind it: VM-managed state can be resizable, inspectable (debuggers, GC, stack traces) and suspendable, because the VM decides where it lives and can move it. A raw `RSP`-based frame is none of the three, which is why every language with coroutines needs a mechanism like this one.

### Fact 2 — every bytecode `ADD` becomes load, load, add, store

The ALU can only operate on registers. A CPU cannot add two values that both live in RAM. So for an interpreter whose operand stack is an array in memory, one bytecode instruction expands into several machine instructions:

```c
// what the interpreter holds
double vm_stack[256];
int sp = 0;              // lives in a register while the loop runs
```

```asm
; bytecode: PUSH 2
mov [vm_stack + sp*8], 2
inc sp

; bytecode: PUSH 3
mov [vm_stack + sp*8], 3
inc sp

; bytecode: ADD  →  four memory touches and one real add
dec sp
mov xmm0, [vm_stack + sp*8]    ; load the top value into a register
dec sp
mov xmm1, [vm_stack + sp*8]    ; load the next one
addsd xmm0, xmm1               ; the ONE instruction that is actually the addition
mov [vm_stack + sp*8], xmm0    ; store the result back to memory
inc sp
```

So "the stack" is an *addressing convention*: it tells the interpreter which memory slots to pull into registers next. The arithmetic always happens in registers, because that is the only place it can happen. A JIT's central trick is noticing that the value never needed to leave the register between the push and the add, and deleting the round trip entirely — see [[32 - Compilation and Machine Foundations/07 - Registers Caches and RAM|Registers, Caches and RAM]].

### Fact 3 — two programs are being compiled, and they never merge

This is the insight that makes the rest of the module click, and it is worth stating starkly. When you write a bytecode interpreter in C++ and compile it with Clang:

- **The interpreter engine gets fully optimized.** The dispatch, the array accesses, the arithmetic — Clang lowers it to LLVM IR, optimizes, allocates real registers, emits machine code. Your `stack.push_back()` really does become a register write plus a pointer bump.
- **The bytecode program it executes gets no optimization at all.** To the C++ compiler, `[LOAD a, PUSH 3, ADD, LOAD b, MUL]` is bytes in a vector. It cannot see them, cannot constant-fold them, cannot allocate registers for them. It has no idea they are a program.

The consequence is that **dispatch overhead survives any amount of host-compiler optimization.** Every time the bytecode `ADD` executes, the interpreter re-reads the opcode, re-selects the handler, re-loads the operands. That repeats forever, on every execution, no matter how good your C++ compiler is.

> [!warning] "The C++ compiler does the heavy lifting" is only half true
> It optimizes your *interpreter*, never the *program your interpreter runs*. Closing that second gap requires a second, separate piece of software: a JIT that emits fresh machine code for the bytecode itself, into an executable memory page, and jumps into it. That is why V8, HotSpot and SpiderMonkey are hard engineering projects rather than well-optimized interpreters — and it is the precise reason Sparkplug exists in V8: not to optimize your code, but to delete the per-bytecode dispatch cost.

### One correction to carry forward: V8 has no dispatch loop

The teaching model for an interpreter is a `while` loop around a `switch` on the opcode. That is the right way to *build* your first VM, and the Lab uses it. It is **not** how V8 works, and mixing them up is a mistake an interviewer can catch.

V8 uses **indirect threaded dispatch**: each bytecode handler is separately pre-compiled machine code, and ends with a tail call that reads the next opcode and jumps straight into that handler. There is still iteration — the interpreter keeps fetching and dispatching bytecodes, that is what an interpreter is — but there is **no central `switch` and no single dispatch site** that control returns to. The reason is branch prediction — one central dispatch branch would mispredict on nearly every bytecode, whereas each handler's own dispatch site keeps its own prediction history. Full mechanism in [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]].

> [!warning] Do not read this note as "interpreters are stack machines"
> Execution strategy and bytecode encoding are independent axes — see the 2x2 in [[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode|Stack, Register and Accumulator Bytecode]]. Everything in this note about operand stacks, dispatch and the two-programs argument applies equally to a register-encoded interpreter like Lua's or Ignition's; the operand stack simply becomes a register file, still an array in memory. Ignition in particular is a register machine, not a stack machine, and it is still interpreted.

## 2. Why It Matters

- It removes the last piece of magic from the engine notes: once "the stack" is an array and `ADD` is load/load/add/store, tiering up is obviously about deleting overhead rather than about cleverness.
- It gives the real reason generators, `async` functions and coroutines are possible — a heap-allocated, suspendable frame — which is a genuine frontend answer, not trivia.
- It kills a common false expectation: "rewrite the interpreter in a faster language" does not speed up the interpreted program. Only compiling the program does.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

A team ships a spreadsheet-style formula engine. Users type `=SUM(A1:A200) * TAX_RATE` into cells; the app parses each formula and evaluates it. With 4,000 formula cells, recalculation blocks the main thread for ~900 ms on every keystroke.

```ts
// ❌ Re-parsing and re-walking the AST on every single evaluation
function evaluate(formula: string, ctx: Ctx): number {
  const ast = parse(formula);              // lex + parse, every call
  return walk(ast, ctx);                    // recursive tree walk, every call
}

function onCellEdit(cells: Cell[], ctx: Ctx) {
  for (const cell of cells) cell.value = evaluate(cell.formula, ctx); // 4,000x
}
```

Trace, and it is Fact 3 in a `.ts` file: the parse is pure overhead repeated on every evaluation, and the tree walk pays a megamorphic dispatch per node — `walk` switches on `node.type`, so V8 sees many shapes at that call site and cannot devirtualize it. TurboFan will happily optimize `walk` itself; it cannot optimize *the formula*, because from V8's point of view the formula is data. Rewriting `walk` more cleverly, or moving it to Wasm, attacks the wrong layer.

```ts
// ✅ Separate compile-once from evaluate-many: compile each formula to a closure
type Compiled = (ctx: Ctx) => number;

function compile(node: Node): Compiled {
  switch (node.type) {
    case "Num": { const v = node.value; return () => v; }
    case "Ref":  { const k = node.name;  return (ctx) => ctx.get(k); }
    case "BinOp": {
      const l = compile(node.left), r = compile(node.right);
      switch (node.op) {
        case "+": return (ctx) => l(ctx) + r(ctx);
        case "*": return (ctx) => l(ctx) * r(ctx);
        // …
      }
    }
  }
}

// once per formula, not once per evaluation
const programs = new Map<string, Compiled>();
function get(formula: string): Compiled {
  let p = programs.get(formula);
  if (!p) programs.set(formula, (p = compile(parse(formula))));
  return p;
}
```

This is **closure compilation**, and it is the JavaScript-level equivalent of a JIT: the structure of the formula is resolved once, and what remains is a tree of tiny monomorphic closures with no opcode fetch, no `switch`, and no node-type dispatch. V8 can now inline them, because each closure's call site sees one shape. The parse disappears from the hot path entirely.

Tradeoffs, all real: you hold a closure per distinct formula, so memory grows with formula variety and the cache needs an eviction policy for a workbook that generates formulas dynamically; the compile step must be invalidated whenever the formula text changes, which is a cache-coherence bug waiting to happen; stack traces and error messages get worse, because the failing frame is now an anonymous closure rather than a labelled AST node; and debugging a wrong result means reading closures instead of a tree you can log.

> [!tip] The reusable question
> When something interpreted is slow, ask: *am I re-deciding the same thing on every execution?* Re-parsing, re-resolving a selector, re-walking a schema, re-building a validator, re-computing a route match. Hoisting that decision out of the hot path is the same move as compiling, at whatever level you are working.

## 4. Interview Answer

Short answer:

> A stack machine's operand stack is not a CPU feature — it is an array the interpreter keeps in memory, separate from the hardware call stack, which is itself just a region of RAM addressed by the stack-pointer register. So a bytecode `ADD` expands into load two values from memory into registers, run the real hardware add, store the result back, because the ALU can only operate on registers.

Deeper answer:

> The distinction that matters is that a VM deliberately heap-allocates its operand stack and frames instead of using the machine stack, because heap data is resizable, inspectable for debuggers and GC, and — crucially — suspendable. That is what makes generators and `async` functions implementable: a paused generator is a frame kept alive as data, which you cannot do with a native `RSP`-based frame. The second thing is that when you write an interpreter in C++, two programs are in play and they never merge: the host compiler fully optimizes your interpreter engine, and does nothing at all to the bytecode program it executes, because that is just bytes in an array. So per-instruction dispatch overhead survives any amount of host optimization, and closing that gap requires a genuinely separate piece of software — a JIT that emits machine code for the bytecode itself. That is precisely what Sparkplug is for in V8: not smarter code, just no dispatch. One caveat on the model: the `while`-plus-`switch` interpreter is the right way to build your first VM, but V8 does not have the `switch` — it uses indirect threaded dispatch, where each pre-compiled handler tail-calls into the next through a dispatch table, so the per-bytecode branch gets its own prediction history instead of all bytecodes sharing one mispredicting site. The iteration is still there; the central dispatcher is not.

## 5. Practice

1. <details><summary>Name the two stacks in play when a JVM or a Wasm interpreter runs, and one thing each can do that the other cannot.</summary>The VM's operand stack — a heap array the interpreter manages, holding the bytecode program's values — and the hardware call stack, a region of memory addressed by <code>RSP</code>/<code>SP</code> holding the interpreter's own return addresses and spills. The operand stack can be grown, inspected and suspended; the hardware stack is managed implicitly by the calling convention and cannot be arbitrarily resized or paused, and overflowing it terminates the process.</details>
2. <details><summary>Why does a bytecode <code>ADD</code> become four memory touches and one arithmetic instruction?</summary>Because the operand stack is an array in memory and the ALU can only operate on registers. So: decrement the index, load the top value into a register, decrement again, load the second value, run the real add on those registers, store the result back into the array, increment the index. A JIT's core win is seeing that the value never needed to leave the register and deleting the round trip.</details>
3. <details><summary>You rewrite your JS-based interpreter in Rust and it gets 5x faster. Your users' <em>scripts</em> still feel slow. Why, and what would actually fix it?</summary>You optimized the engine, not the programs it runs. The host language cannot see the bytecode — it is data — so per-instruction dispatch overhead is unchanged in structure, just cheaper per step. Fixing it means compiling the program itself: emit machine code (a real JIT) or, at the JS level, compile each program once into a tree of closures so there is no opcode fetch and no dispatch per operation.</details>
4. <details><summary>Why do VMs heap-allocate their frames instead of using the machine stack, and which JavaScript features depend on that choice?</summary>Because heap frames are resizable, inspectable (debuggers, GC, stack traces), and suspendable. Generators depend on it directly — a paused generator is a live frame held as data — and so do <code>async</code> functions and <code>await</code>, which are the same suspend/resume machinery wired to the promise job queue.</details>
5. <details><summary>An interpreted register machine's "registers" — are they CPU registers? What decides that?</summary>No. They are slots in a memory array, exactly like an interpreted stack machine's operand stack; neither encoding is nearer to silicon. What decides whether a value reaches a physical register is whether a compiler runs a register-allocation pass — the execution-strategy axis — not whether the bytecode was stack- or register-encoded. In V8 that means Ignition never puts your values in CPU registers no matter how register-like its bytecode looks; Sparkplug and above do.</details>
6. <details><summary>Transfer: name three frontend situations that are the same "re-deciding the same thing every execution" mistake.</summary>Re-parsing a formula, schema or template on every evaluation instead of compiling it once; rebuilding a validator, regex or <code>Intl</code> formatter inside a render or a loop instead of hoisting it; re-resolving the same route match or selector per item. In each case the fix is to separate compile-once from run-many — the same move a JIT makes, one abstraction level up.</details>

## Related Notes

- [[32 - Compilation and Machine Foundations/12 - Compiled vs Interpreted and Every Stage Between|Compiled vs Interpreted, and Every Stage Between]] — where an interpreter leaves the pipeline, and the tree-walking strategy that skips bytecode entirely.
- [[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode|Stack, Register and Accumulator Bytecode]] — the encoding this note executes.
- [[32 - Compilation and Machine Foundations/07 - Registers Caches and RAM|Registers, Caches and RAM]] — why the memory round trip costs what it costs.
- [[32 - Compilation and Machine Foundations/04 - AOT JIT and the Portability Tradeoff|AOT, JIT and the Portability Tradeoff]] — why the second piece of software exists.
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] — how V8 actually dispatches, and why not with a loop.
- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]] — the suspendable-frame payoff.
- [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]] — the JS-level view of the hardware stack.
- [[90 - Labs/07 - Bytecode VM Lab|Bytecode VM Lab]] — build all of this.
