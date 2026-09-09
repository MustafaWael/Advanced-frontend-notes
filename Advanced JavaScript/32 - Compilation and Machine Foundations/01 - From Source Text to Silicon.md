---
tags: [compilation, machine-model, bytecode]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
aliases: [Machine Code vs Bytecode, Binary vs Hex vs Assembly, Source to Silicon]
---

# From Source Text to Silicon

## Maturity Target

- Priority: #deep-dive
- Study time: 30-40 minutes
- Interview signal: you can say precisely what "compiled to machine code" means, and you never use *binary*, *bytecode*, *assembly* and *machine code* as loose synonyms.
- Production signal: when you read a profiler, a stack trace with no symbols, or a `.wasm` file in a network panel, you know which layer you are looking at.
- Dependencies: [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]]

## Source Anchors

- [V8 - Understanding V8's bytecode](https://v8.dev/blog/understanding-v8-bytecode)
- [WebAssembly Core Specification - Binary Format](https://webassembly.github.io/spec/core/binary/index.html)
- [MDN - WebAssembly text format](https://developer.mozilla.org/en-US/docs/WebAssembly/Guides/Understanding_the_text_format)
- [Intel 64 and IA-32 Architectures Software Developer Manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)

## 1. Concept

**Simple explanation.** Code goes through layers, and each layer is closer to hardware than the last. Only the last layer — machine code for one specific CPU family — is something silicon can actually run; everything above it needs another program to translate or interpret it first.

**Accurate mechanism.** There are four *layers*, and separately there are *notations* for viewing a layer. Conflating the two is where the confusion lives.

| Layer | What it is | Who consumes it | Portable across CPUs? |
| --- | --- | --- | --- |
| **Source text** | Characters written for humans | A parser | Yes |
| **Bytecode** | Instructions for an *invented* virtual machine | An interpreter, or a compiler that lowers it further | Yes — no real CPU knows these opcodes |
| **Compiler IR** | A compiler's private, in-memory instruction form | The rest of that same compiler; discarded before shipping | Yes, but never leaves the build |
| **Machine code** | Instructions one real CPU family was physically built to decode | The CPU, directly | **No** — tied to x86-64, ARM64, RISC-V… |

And the notations, which are *not* layers:

- **Binary** — the literal bits. Everything above, once stored, is bits. "Binary" is not a kind of code; it is what all data is.
- **Hexadecimal** — a way of *writing* bits compactly. One hex digit is exactly 4 bits, so two hex digits are exactly one byte. `8B 45 FC` and `10001011 01000101 11111100` are the same 3 bytes.
- **Assembly** — a human-readable notation for machine code, essentially one line per instruction. An assembler maps mnemonics to opcodes by table lookup; there is no optimization or analysis involved.

So: assembly and machine code are **one layer in two notations**. Hex is a notation for any bits. Bytecode is a genuinely different, earlier layer that no hardware understands.

### Trace: the same addition at every layer

```js
// Layer 1 — source text
function add(a, b) {
  return a + b;
}
```

```txt
Layer 2 — Ignition bytecode (V8). Run node --print-bytecode to see the real thing.
Ldar a1          ; load parameter b into the accumulator
Add a0, [0]      ; accumulator = a0 + accumulator, recording type feedback in slot 0
Return           ; return the accumulator
```

Read `Add a0, [0]` carefully — it names *one* register operand, uses the accumulator implicitly as the other operand *and* as the destination, and carries `[0]`, an index into this function's feedback vector. That feedback slot is the whole reason JavaScript needs the tier ladder: the opcode does not know whether this is integer addition or string concatenation, so it has to *record* what it saw. See the hidden-classes and inline-caches sections of [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]].

```wat
;; Layer 2, a different bytecode — Wasm text format (WAT)
(func $add (param $a i32) (param $b i32) (result i32)
  local.get $a
  local.get $b
  i32.add)
```

```txt
Layer 2 as it actually ships — the .wasm binary, shown in hex
00 61 73 6D 01 00 00 00   ; magic "\0asm" + version 1
...
20 00                      ; local.get 0
20 01                      ; local.get 1
6A                         ; i32.add
```

`i32.add` is a *different opcode* from `f64.add`. The type is baked into the instruction, so nothing has to be discovered at runtime — the structural reason Wasm needs no feedback vector, no inline caches and no warm-up.

Note also the shape of the file around those instructions: a magic number, a version, then a series of **tagged, length-prefixed sections** (type, function, export, code). Decoding is "read a section id byte, read a length, read that many bytes" — no ambiguity and no backtracking, which is the concrete reason a `.wasm` validates fast enough to compile while it is still downloading. Full byte-by-byte walkthrough in [[32 - Compilation and Machine Foundations/10 - Compiling to WebAssembly|Compiling to WebAssembly]].

```asm
; Layer 4 — x86-64 machine code, assembly notation
mov eax, [rbp-4]    ; load a from the stack frame
add eax, [rbp-8]    ; add b
ret
```

```txt
Layer 4 — the same instructions, hex notation
8B 45 FC   03 45 F8   C3
```

`8B 45 FC` **is** `mov eax, [rbp-4]`. Nothing was translated between those two blocks; they are the same bytes displayed for different readers.

### What the CPU does with the last layer

The CPU neither interprets nor translates. It is fixed circuitry in which specific bit patterns *are* the control signals — the opcode byte physically selects which functional units activate. That is the categorical difference from every layer above: bytecode and IR need a running program to give them meaning, machine code needs only power.

> [!warning] "Compiled" does not mean "compiled to machine code"
> `javac`, `tsc`, Babel and the Ignition BytecodeGenerator are all compilers, and none of them emit machine code. A compiler is anything that translates between representations. Ask *to what* before treating "it's compiled" as a performance claim.

## 2. Why It Matters

- **It makes the tier ladder inevitable rather than arbitrary.** Once you see that Ignition's `Add` carries a feedback slot while Wasm's `i32.add` carries a type, "why does JS need Maglev and TurboFan but Wasm doesn't" stops being trivia.
- **It fixes the most common wrong sentence about JS.** "JavaScript is interpreted" and "JavaScript is compiled" are both wrong in the same way — they name a layer boundary as if it were a property of the language.
- **It is the vocabulary for reading tooling output.** A `.wasm` in the network panel, a symbol-less native frame in a performance profile, a source map failing to map — each is a specific layer showing through.
- **It generalizes.** Everything in this vault about build-time vs runtime is this diagram with different labels.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

A team moves an image-processing step off a server and into the browser. The first attempt is plain JavaScript:

```ts
// ❌ Slow and, worse, unpredictably slow
export function toGrayscale(pixels: Uint8ClampedArray) {
  for (let i = 0; i < pixels.length; i += 4) {
    const luma = 0.299 * pixels[i] + 0.587 * pixels[i + 1] + 0.114 * pixels[i + 2];
    pixels[i] = pixels[i + 1] = pixels[i + 2] = luma; // float written into a Uint8 array
  }
}
```

Trace, mechanically: this is a hot loop, so it does reach Maglev/TurboFan — but only *after* the interpreter has run it enough times to fill the feedback vector, and only while its assumptions hold. Every arithmetic opcode in the bytecode started life generic. On a 12-megapixel photo the first frames run interpreted, and any drift in the observed types (a `luma` that stops being representable as a small integer, a differently shaped array on the next call) can bail the optimized code out mid-run. The result is code whose speed depends on history.

```ts
// ✅ Move the inner loop to a layer with no type uncertainty
const { instance } = await WebAssembly.instantiateStreaming(fetch("/grayscale.wasm"));
const grayscale = instance.exports.grayscale as (ptr: number, len: number) => void;
// copy pixels into the module's linear memory, call, copy back
```

The Wasm module's instructions carry their types, so V8's Liftoff compiler emits machine code in one pass at load and there is no warm-up phase and no feedback-driven bailout. Same algorithm, a layer lower.

Tradeoffs, and they are real: you now ship a second artifact and a toolchain to build it; every call crosses a boundary and pixel data must be copied into and out of linear memory, which can cost more than the compute for small inputs; debugging spans two source-map worlds. Wasm pays off for sustained compute on large buffers, not for a function called twice.

> [!tip] Choose the layer by the shape of the work
> Big, numeric, repeated, type-stable inner loop on a large buffer → a lower layer earns its complexity. Anything DOM-bound, string-bound, or called a handful of times → stay in JS; you would spend the win on boundary crossings.

## 4. Interview Answer

Short answer:

> Source text is parsed to an AST, compiled to bytecode for an invented virtual machine, and only the last step — a JIT or an AOT compiler — emits machine code for one specific CPU family. Assembly is just machine code written for humans, and hex is just how we write bits; bytecode is a separate, earlier layer that no CPU can execute.

Deeper answer:

> Four layers: source text, bytecode, compiler IR, machine code. Bytecode and IR are both abstract instruction sets, but they differ in lifetime — Wasm and JVM bytecode ship to the user and are executed there, LLVM IR is discarded before the binary leaves the build machine. Only machine code is executed by hardware, and it is executed rather than interpreted: the opcode bits physically are the control signals, which is why it is the one layer that is not portable. In V8 the interesting detail is that the bytecode is where JavaScript's dynamism is *recorded*: `Add a0, [0]` names a feedback slot because the opcode cannot know if this is arithmetic or concatenation. Wasm's `i32.add` encodes the type in the opcode, which is precisely why it needs no feedback, no inline caches and no tier ladder.

## 5. Practice

1. <details><summary>Someone says "hex code runs faster than binary code." What is wrong with the sentence?</summary>It compares two notations, not two things. Hex and binary are two ways of writing the same bits — one hex digit per four bits. Nothing is executed as hex; hex only exists in the tools humans read. The sentence is a category error, like asking whether Roman numerals compute faster than Arabic ones.</details>
2. <details><summary>Why can the same <code>.wasm</code> file run on an x86 laptop and an ARM phone, while a compiled C++ binary cannot?</summary>The <code>.wasm</code> file is bytecode for an abstract stack machine — no real CPU decodes it, so the engine on each machine compiles it to that machine's instruction set at load. The C++ binary already *is* machine code for one instruction set; the CPU-specific step happened on the build machine, which is exactly what buys it startup speed and costs it portability.</details>
3. <details><summary>Ignition's <code>Add a0, [0]</code> and Wasm's <code>i32.add</code> are both single bytecode instructions for addition. Name the difference that explains V8's whole tier ladder.</summary>Wasm's opcode encodes the operand type, so the answer is known before execution. Ignition's does not — JavaScript has no static types — so the instruction carries an index into a feedback vector and *records* what it saw. Speculative optimization is what you build when types must be observed rather than declared, and deoptimization is the safety net for when the observation stops holding.</details>
4. <details><summary>Transfer: your bundler is written in Rust and runs 20x faster than the JavaScript one it replaced. Which layer difference is doing the work, and which is not?</summary>The Rust tool was compiled ahead of time to native machine code with full static types, so it never pays parse-and-warm-up cost and never speculates. What is <em>not</em> doing the work is "Rust is a faster language" in the abstract — a JS bundler's hot loops do eventually reach TurboFan. The durable wins are no warm-up, no deopt risk, real threads, and control over memory layout (see [[32 - Compilation and Machine Foundations/07 - Registers Caches and RAM|Registers, Caches and RAM]]).</details>

## Related Notes

- [[32 - Compilation and Machine Foundations/12 - Compiled vs Interpreted and Every Stage Between|Compiled vs Interpreted, and Every Stage Between]] — the module's front door: all ten stages, including the front end and the linker/loader tail this note skips.
- [[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode|Stack, Register and Accumulator Bytecode]] — how the bytecode layer encodes operands.
- [[32 - Compilation and Machine Foundations/03 - LLVM and Compiler IR|LLVM and Compiler IR]] — the layer that never ships.
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] — how the bytecode layer actually executes.
- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]] — the tiers, and the Wasm bypass.
- [[32 - Compilation and Machine Foundations/10 - Compiling to WebAssembly|Compiling to WebAssembly]] — the full pipeline for one of the bytecodes above.
- [[12 - Advanced Language Concepts/14 - Typed Arrays and Binary Data|Typed Arrays and Binary Data]] — reading and writing raw bytes from JS.
