---
tags: [compilation, bytecode, machine-model]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
aliases: [Stack Machine vs Register Machine, Accumulator Machine, Bytecode Encoding]
---

# Stack, Register and Accumulator Bytecode

## Maturity Target

- Priority: #deep-dive
- Study time: 25-35 minutes
- Interview signal: you can explain what "WebAssembly is a stack-based virtual machine" actually claims, and say why that claim has nothing to do with how fast the compiled result runs.
- Production signal: you stop reasoning about Wasm's speed from its bytecode design, and reason about it from warm-up and boundary crossings instead.
- Dependencies: [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon|From Source Text to Silicon]]

## Source Anchors

- [WebAssembly Core Specification - Instructions](https://webassembly.github.io/spec/core/syntax/instructions.html)
- [V8 - Understanding V8's bytecode](https://v8.dev/blog/understanding-v8-bytecode)
- [V8 - Firing up the Ignition interpreter](https://v8.dev/blog/ignition-interpreter)
- [The Implementation of Lua 5.0 (register-based VM rationale)](https://www.lua.org/doc/jucs05.pdf)
- [Java Virtual Machine Specification - The Structure of the JVM](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html)
- [Android - Dalvik bytecode](https://source.android.com/docs/core/runtime/dalvik-bytecode)

## 1. Concept

**Simple explanation.** Stack-based, register-based and accumulator-based are three ways to write down *where an instruction's operands come from*. They are competing designs for the same layer — the bytecode — not different layers and not different hardware.

**Accurate mechanism.** Real CPUs are register machines; that is the only thing that physically exists. A bytecode designer, however, gets to choose an encoding, and the choice is a tradeoff between how compact and easy-to-generate the format is and how fast it is to *interpret*.

- **Stack-based** — instructions take no operand names. They pop their inputs from an operand stack and push their result. Compact, trivial to generate (the compiler needs no register allocator), and easy to validate in a single linear pass.
- **Register-based** — every instruction names its operand slots explicitly. Fewer instructions per operation and fewer dispatches, at the cost of a bulkier encoding and a bytecode generator that must do its own slot allocation.
- **Accumulator-based** — one designated register is the implicit second operand *and* the implicit destination, so most instructions name only one operand. A middle ground: denser than register encoding, cheaper to interpret than push/pop.

### Trace: `(2 + 3) * 4` in each encoding

```txt
Stack-based (Wasm, JVM, CPython)
i32.const 2      ; stack: [2]
i32.const 3      ; stack: [2, 3]
i32.add          ; pop 3, pop 2, push 5      → [5]
i32.const 4      ; stack: [5, 4]
i32.mul          ; pop 4, pop 5, push 20     → [20]
```

```txt
Register-based (Lua 5.x, Dalvik/ART)
LOADK  r0, 2
LOADK  r1, 3
ADD    r2, r0, r1     ; one instruction, all three slots named
LOADK  r3, 4
MUL    r4, r2, r3
```

```txt
Accumulator + registers (V8's Ignition)
LdaSmi [2]       ; accumulator = 2
Star r0          ; r0 = accumulator
LdaSmi [3]       ; accumulator = 3
Add r0, [0]      ; accumulator = r0 + accumulator     (accumulator implicit twice)
Star r1
LdaSmi [4]
Mul r1, [1]      ; accumulator = r1 * accumulator
```

Notice what "hybrid" means concretely in Ignition: there *are* named registers (`r0`, `r1`, and `a0`/`a1` for parameters), but the accumulator is never named — it is the implied input and output of `Lda*`, `Add`, `Mul`, `Star`. That is a third point on the spectrum, not a synonym for "register-based".

### Who chose what, and why

| Bytecode | Encoding | Stated priority |
| --- | --- | --- |
| WebAssembly | Stack | Small binaries, single-pass validation, portable compile target |
| JVM bytecode | Stack | Simplicity and verifiability, 1995-era constraints |
| CPython | Stack | Simplicity of the compiler |
| Lua 5.0+ | Register | Interpretation speed — Lua moved *from* stack *to* register for exactly this |
| Dalvik / ART | Register | Interpretation speed on constrained mobile CPUs |
| V8 Ignition | Accumulator + registers | Dense bytecode (memory) plus fast dispatch, since it never leaves V8 |

The pattern: **formats designed to travel choose stack; formats designed to be interpreted fast choose register or accumulator.** Wasm and JVM bytecode are distribution artifacts that will be compiled again on arrival, so compactness and verifiability win. Ignition's bytecode never leaves the process and *is* interpreted directly, so dispatch cost wins.

> [!warning] "Wasm is stack-based, so it must be slower"
> This is the single most common wrong inference here, and it is worth saying out loud: the encoding's interpretation cost is irrelevant to Wasm, because Wasm is **never interpreted** in a production browser engine. V8's Liftoff compiles it in one pass; the optimizing tier compiles it further. Both do register allocation, so the operand stack is bookkeeping the compiler *sees through* — it tracks which pushed value feeds which instruction and then emits ordinary register machine code. The abstract stack does not exist at runtime.

### Two orthogonal axes — the confusion this note exists to prevent

Almost every muddle about bytecode comes from collapsing two independent questions into one. Keep them apart:

- **Axis 1 — encoding.** Does an instruction operate on whatever is on top of an implicit stack, or does it name its operand slots? A property of the *bytecode format*, fixed at design time.
- **Axis 2 — execution strategy.** Is each instruction read and dispatched one at a time at run time, or is the whole thing translated to native machine code? A property of the *engine*, and independent of axis 1.

Every combination exists:

| | Interpreted | JIT- or AOT-compiled |
| --- | --- | --- |
| **Stack encoding** | CPython — stack bytecode, dispatched instruction by instruction | Wasm in V8 — stack bytecode, compiled by Liftoff then the optimizing tier; JVM bytecode under C1/C2 |
| **Register encoding** | Lua 5.x, Dalvik — register bytecode, still dispatched one instruction at a time | **V8's Ignition bytecode compiled by Sparkplug, Maglev or TurboFan** — the same bytecode, now native code with real register allocation |

> [!warning] "Register bytecode is closer to the hardware, so its values live in real CPU registers"
> No — and this is the specific wrong inference to watch for. An **interpreted** register machine's registers are slots in a memory array, exactly like an interpreted stack machine's operand stack. Neither is nearer to silicon than the other; both are the interpreter performing ordinary loads and stores. Whether any value reaches a physical CPU register is decided entirely by **axis 2** — is there a compiler doing register allocation — and not at all by axis 1. The word "register" in "register-based bytecode" names an addressing mode in a bytecode format, not a piece of hardware.

And one label to get right, because it is easy to hear it wrong: **Ignition is not a stack machine.** V8's own introduction of it says Ignition is "a register machine, with each bytecode specifying its inputs and outputs as explicit register operands," expressly contrasted with a stack machine's implicit stack. It has an accumulator on top of that register file, which is why this note calls it a hybrid — but the hybrid is between *accumulator and named registers*, never between stack and register.

### Where the overhead actually is, and is not

```txt
Wasm bytecode (stack)        Compiled x86-64 (registers)
i32.const 2            →     mov eax, 2
i32.const 3                  add eax, 3     ; no push, no pop, no memory traffic
i32.add
```

- **Interpreting** stack bytecode is genuinely slower than interpreting register bytecode: three dispatches instead of one, and every intermediate value round-trips through the interpreter's operand stack, which is ordinary memory. This is the measured effect Lua 5.0 chased.
- **Compiling** either one erases the difference. Register allocation maps values to real registers and spills to the stack only under pressure. Nothing in the output remembers which encoding it came from.

> [!tip] What "register allocation" actually does, in three steps
> Worth naming, because it is the step that erases the encoding — and the step where register IR pays off. (1) **Liveness analysis**: for each value, find the instruction range between its definition and its last use. (2) **Allocation** — graph colouring or linear scan — assign physical registers, reusing one the moment its previous occupant's live range has ended. (3) **Spilling**: when more values are live than there are physical registers, write the excess to stack memory and reload it later. A physical register is not assigned to a value for the whole function, either: the same JavaScript variable can live in `rax` at one point, move to `rbx` later, and be spilled to the stack later still, depending on register pressure at that point in the code. Register IR makes step 1 cheap because the dataflow is already written down — "is `r0` read after this instruction?" is a lookup. On stack IR the compiler must first replay stack states to reconstruct which push feeds which pop, which is why optimizing compilers convert stack bytecode to a register or SSA form *before* doing real work on it. Build it yourself in [[90 - Labs/07 - Bytecode VM Lab|Lab 07]], stage 4.

So the encoding matters for exactly one audience: whoever interprets it. For anything JIT- or AOT-compiled, it is a build-time convenience, not a runtime property.

## 2. Why It Matters

- It disarms the "stack machine sounds slow" reflex, which is otherwise a confident wrong answer in an interview.
- It explains Ignition's design as a deliberate choice — bytecode that is dense *and* fast to dispatch — rather than an oddity to memorize.
- It is the cleanest small example of a recurring principle: an artifact's design is driven by who consumes it and when, not by which option is "better".

## 3. Real Frontend Example: Bug → Fix → Tradeoff

A PR rejects a Wasm-based CSV parser with a review comment that reads, plausibly: *"Wasm is a stack machine, so per-row parsing will be slower than our JS version once V8 warms up — let's not add a toolchain for a regression."* The team benchmarks and finds the Wasm version *is* slower. The comment is wrong and the benchmark is right, for unrelated reasons.

```ts
// ❌ The actual cause: one boundary crossing and one copy per row
for (const row of rows) {
  const bytes = encoder.encode(row);          // allocate
  const ptr = wasm.exports.alloc(bytes.length); // allocate in linear memory
  new Uint8Array(wasm.exports.memory.buffer, ptr, bytes.length).set(bytes); // copy
  wasm.exports.parseRow(ptr, bytes.length);   // cross
  wasm.exports.free(ptr);
}
```

Trace: the stack encoding cost nothing — Liftoff compiled it to register machine code at load. What costs is the per-row call overhead plus two copies across the JS/Wasm memory boundary, repeated 200,000 times. The fix is not to abandon Wasm or to argue about encodings; it is to move the loop across the boundary.

```ts
// ✅ One crossing, one copy: hand the whole buffer over
const bytes = new Uint8Array(await file.arrayBuffer());
const ptr = wasm.exports.alloc(bytes.length);
new Uint8Array(wasm.exports.memory.buffer, ptr, bytes.length).set(bytes);
const rowCount = wasm.exports.parseAll(ptr, bytes.length); // loop lives inside Wasm
wasm.exports.free(ptr);
```

Tradeoffs: the whole file must now fit in linear memory at once, which rules out streaming and raises peak memory; error reporting gets coarser, because a per-row callback into JS would reintroduce the crossings you just removed; and the module's API is now shaped by the boundary rather than by what reads nicely.

> [!tip] The reusable rule for any language boundary
> Wasm, workers, native modules, IPC: cost scales with *number of crossings*, not with the language on the other side. Design the interface so the loop lives on one side.

## 4. Interview Answer

Short answer:

> They are three ways to encode where an instruction's operands come from, all at the bytecode layer. Stack machines leave operands implicit on an operand stack, register machines name them, and an accumulator machine has one implicit register that most instructions read and write. Real CPUs are register machines, so any bytecode gets translated to registers eventually — which means the encoding only affects interpretation cost, not compiled speed.

Deeper answer:

> The choice tracks who consumes the bytecode. Wasm and JVM bytecode are shipped artifacts that get compiled on arrival, so they optimize for compactness and single-pass validation and chose stack. Lua and Dalvik are interpreted directly and chose register encoding for fewer dispatches — Lua explicitly switched from stack to register in 5.0 for that reason. V8's Ignition is a third option, accumulator plus a register file, which keeps bytecode dense while cutting the operand shuffling a pure stack machine would need. And the important consequence: once a compiler does register allocation, the stack is a dataflow bookkeeping device it sees straight through, so "Wasm is stack-based" says nothing at all about how fast the compiled code runs.

## 5. Practice

1. <details><summary>Same expression, stack vs register bytecode: which uses more instructions, and does that make the compiled machine code slower?</summary>Stack uses more — <code>push, push, add</code> versus a single <code>add r2, r0, r1</code>. It makes <em>interpretation</em> slower, because dispatch cost is per instruction. It does not make compiled output slower: register allocation produces the same machine code either way.</details>
2. <details><summary>Why is Ignition described as hybrid rather than register-based, given that an accumulator is itself a register?</summary>The label describes the <em>encoding</em>, not the hardware. A pure register encoding names every operand every time. Ignition leans on one register that is never named — implicit source and destination for most opcodes — while still having named registers for locals and parameters. Physically it is all registers; the distinction is how many slots each instruction has to spell out.</details>
3. <details><summary>Lua switched from stack-based to register-based bytecode and got faster. Would switching Wasm to a register encoding make Wasm faster?</summary>Essentially no. Lua's win came from cheaper interpretation, and Lua interprets its bytecode. Wasm is compiled, not interpreted, in production engines, so the encoding is erased before execution. Wasm would only <em>lose</em> — bigger binaries, slower download and validation, no compensating gain.</details>
4. <details><summary>Transfer: why is this the same argument as "should the compiler or the runtime do the work?"</summary>Both are about moving cost to whichever phase can absorb it. Stack encoding pushes work to the consumer (allocate registers on arrival) in exchange for a smaller, more portable artifact; register encoding front-loads it. The same trade runs through [[32 - Compilation and Machine Foundations/04 - AOT JIT and the Portability Tradeoff|AOT vs JIT]] and through bundling vs runtime module resolution in [[27 - Frontend Tooling and Build Systems/00 - Frontend Tooling and Build Systems MOC|tooling]].</details>

## Related Notes

- [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon|From Source Text to Silicon]] — the layer this note zooms into.
- [[32 - Compilation and Machine Foundations/03 - LLVM and Compiler IR|LLVM and Compiler IR]] — a register-style IR, and why it never ships.
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] — how Ignition dispatches these opcodes.
- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]] — the same boundary-crossing cost model.
- [[32 - Compilation and Machine Foundations/09 - Interpreters Dispatch and the Two Stacks|Interpreters, Dispatch and the Two Stacks]] — what executing either encoding actually costs.
- [[90 - Labs/07 - Bytecode VM Lab|Bytecode VM Lab]] — implement both encodings and measure the difference.
- [[32 - Compilation and Machine Foundations/10 - Compiling to WebAssembly|Compiling to WebAssembly]] — where Wasm's stack encoding is introduced, and un-done.
