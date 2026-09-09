---
tags: [compilation, webassembly, deoptimization]
module: "32 - Compilation and Machine Foundations"
priority: deep-dive
status: not-started
aliases: [call_indirect, WasmGC, Wasm Deopt, Speculative Inlining, Guard vs Deopt]
---

# Wasm Speculation and Deopt

## Maturity Target

- Priority: #deep-dive
- Study time: 30-40 minutes
- Interview signal: you can explain why static typing removes *type* speculation but not all speculation, and you can distinguish a guard branch from a real deoptimization.
- Production signal: you can reason about why a Wasm module's throughput depends on how uniform its data is, and reduce indirect dispatch at the source instead of hoping the engine guesses well.
- Dependencies: [[32 - Compilation and Machine Foundations/10 - Compiling to WebAssembly|Compiling to WebAssembly]] · [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]

## Source Anchors

- [WebAssembly Core Specification - Control Instructions (`call_indirect`)](https://webassembly.github.io/spec/core/syntax/instructions.html#control-instructions)
- [V8 - Speculative optimizations for WebAssembly using deopts and inlining](https://v8.dev/blog/wasm-speculative-optimizations) — the primary source for everything in this note
- [WebAssembly - GC proposal](https://github.com/WebAssembly/gc)
- [MDN - WebAssembly.Table](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WebAssembly/Table)

## 1. Concept

**Simple explanation.** Wasm's types are fixed in the binary, so an engine never has to guess what a value *is*. It can still guess what the program will *do* — and a wrong guess about behaviour needs the same escape hatch JavaScript needs.

**Accurate mechanism.** Two facts that are usually welded into one wrong sentence. Keep them apart:

| | Static value types (`i32`, `f64`, struct fields) | Runtime call targets (`call_indirect`) |
| --- | --- | --- |
| Knowable from the binary? | Yes — declared and validated at load | **No** — the table index is a runtime, data-dependent value |
| Can an engine be wrong about it? | Never | Yes |
| Needs guards or deopt? | Never, then or now | Yes, since Chrome M137 (2025) |

### The panel: what Wasm's static types actually buy

Keep this table; it is the antidote to the inference "Wasm is static, therefore nothing warms up." It is also the canonical version of this claim for the whole module — the other Wasm notes link here rather than restating it.

| Genuinely settled before execution | Still dynamic in current V8 |
| --- | --- |
| Value types are declared and validated at load | Indirect-call targets are runtime data |
| No JavaScript-style *type* profiling is needed | **Liftoff emits code to update a feedback vector at every call site** |
| No deopt from a value-type mismatch — those are rejected at validation | Behaviour-based speculation can, and does, deopt |
| Baseline compilation can start immediately, so the first run is fast | Optimized code still arrives on a hotness heuristic — tier-up has not gone away |

So "Wasm has no feedback vector, no warm-up and no tier ladder" is wrong on all three counts as a general statement. What is true is narrower and still worth a lot: **no type uncertainty, therefore no type feedback, no inline caches, and a fast first run.**

The claim "Wasm never deoptimizes because it is statically typed" fails on the *because*. Static typing genuinely removes the need for type speculation — that half is solid and always was. But Wasm's historical absence of deopt was a **design choice** in V8's pipeline: compile with Liftoff, then unconditionally tier up to TurboFan using guaranteed-correct static types, and never speculate about anything. An engine was always free to speculate about facts *outside* the type system, and from Chrome M137 it does.

### What `call_indirect` is, and why it cannot be resolved statically

Wasm's function-pointer mechanism. There is a table of function references, and the call site supplies an *index* into it:

```wat
(table funcref (elem $Dog_speak $Cat_speak))

(func $makeItSpeak (param $a (ref $Animal))
  (call_indirect (type $speak_sig)
    (local.get $a)
    (struct.get $Animal $vtable_slot (local.get $a))))  ;; index — a runtime value
```

At runtime the engine must (1) read the index, (2) look up the function at that table slot, (3) check its signature matches, (4) call it. Step 1 reads a value that came from data, so **which function runs is not derivable from the binary**. Wasm's type system guarantees the *signature* is compatible; it says nothing about *which* compatible function will be there on any given call.

You never write `call_indirect` yourself. The compiler emits it for every virtual method call, function pointer, trait object, or interface dispatch.

### Speculative inlining, and why a wrong guess is a correctness problem

If profiling shows a call site has resolved to `$Dog_speak` 100,000 times running, TurboFan does not merely optimize the dispatch — it **deletes the indirection** and inlines `$Dog_speak`'s body at the call site:

```txt
; speculatively specialized machine code
if (a.vtable_slot != $Dog_speak) goto slow_path;   ; the guard
  <Dog_speak's body, inlined — no table lookup, no indirect call>
  goto done;
slow_path:
  <the honest call_indirect: read the table, check the signature, call>
```

Now a `Cat` arrives. Here is the point that answers the natural objection — *the bytecode did not change, so why is anything invalid?*

**The bytecode did not change; the generated machine code did.** That machine code is no longer general dispatch logic. It is `Dog_speak`'s body, hardcoded. Running it for a `Cat` would execute Dog's logic where Cat's was required — that is not slower, it is **wrong**. Speculation does not produce a faster version of the same program; it produces a *narrower* program that is only equivalent while the bet holds. Deoptimization exists because the bet can fail, and the failure mode is incorrectness rather than sluggishness.

> [!warning] A guard branch is not a deopt — the distinction is worth having
> The sketch above is the cheap case: a runtime check with an in-function fallback path. That is just a branch. A **true deoptimization** becomes necessary when the assumption was used to justify *other* optimizations entangled across the function — eliminating a bounds check, unboxing a field, reordering instructions across the call because Dog's fixed layout was assumed. One guard cannot unwind all of that safely. So the engine discards the whole optimized function, reconstructs correct baseline-tier state (locals, stack values) at exactly that program point, and resumes execution in the lower tier. That discard-and-rebuild-state operation is what "deopt" names, in Wasm and in JavaScript alike — see [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]].

### Why WasmGC is where this pays off

WasmGC adds garbage-collected reference types to Wasm, which makes it a practical compile target for object-oriented, GC'd languages — Kotlin, Dart, Java-family languages. Those languages lean heavily on virtual dispatch, so their output is dense with `call_indirect` through vtables. And in practice such call sites are usually **monomorphic**: the loop really does see mostly `Dog`s. That combination — structurally polymorphic, empirically monomorphic — is precisely where speculative inlining wins, which is why M137's optimization was aimed there.

C, C++ and Rust compiled to Wasm use far fewer polymorphic indirect calls, so they benefit less from this specific optimization.

> [!tip] The practical takeaway has not changed
> This is a narrow, targeted speculation about indirect call targets, not JavaScript's broad "guess about everything, including types" model. Wasm still has no type-feedback warm-up, still reaches good performance on the first run, and still avoids the JS deopt-cliff pattern. What changed is that "Wasm can never deopt" is now simply false, and the reasoning behind it was always shaky. In an interview, say: static typing removes type speculation; engines may still speculate on behaviour; V8 now does, for WasmGC-style indirect calls.

### The same shape you already know from JavaScript

This is monomorphic / polymorphic / megamorphic call sites again, one layer down. In JS the uncertainty is *what is this value*; in Wasm it is *which function is at this table slot*. Both are resolved by observing history, both are compiled into narrowed code, both need a guard, and both punish a call site that genuinely sees many cases. The lesson transfers exactly: uniform data lets a speculating engine win; heterogeneous data at a hot call site defeats it.

## 2. Why It Matters

- It repairs a claim that circulates everywhere — "Wasm never deoptimizes because it's statically typed" — and repairing it correctly requires separating two independent facts, which is good practice in itself.
- The guard-versus-deopt distinction sharpens your JavaScript deopt story too; most people use "deopt" for both and cannot say what the expensive one actually costs.
- "Speculation makes code narrower, not faster" is the cleanest one-line justification for why deoptimization has to exist at all.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

A team ships a Rust-to-Wasm markdown renderer. Benchmarks on the fixture suite are excellent. On real documents — a mix of headings, code blocks, tables, footnotes — throughput drops by roughly half, and the profile blames one loop.

```rust
// ❌ Trait objects: every node visit is an indirect call the engine must guess about
trait Visitor { fn render(&self, node: &Node, out: &mut String); }

struct Heading; struct CodeBlock; struct Table; struct Footnote;
impl Visitor for Heading   { fn render(&self, n: &Node, o: &mut String) { /* … */ } }
impl Visitor for CodeBlock { fn render(&self, n: &Node, o: &mut String) { /* … */ } }
// … four more impls

fn render_all(nodes: &[Node], visitors: &[Box<dyn Visitor>], out: &mut String) {
    for node in nodes {
        visitors[node.kind_index()].render(node, out);   // dyn dispatch → call_indirect
    }
}
```

Trace: `Box<dyn Visitor>` is a trait object, so `render` is a virtual call, which LLVM's Wasm backend emits as `call_indirect` through a function table. On the fixture suite each document is homogeneous, so the call site is monomorphic, TurboFan inlines the one target, and the numbers look great. On a real document the target changes every few nodes. The guard fails constantly, the fast path is useless, and if the engine had leaned on that assumption for surrounding optimizations it may repeatedly deopt and re-optimize — a genuine thrash. Nothing is broken; the code simply asked the engine to guess something unguessable.

```rust
// ✅ Closed enum dispatch: the call becomes direct, nothing to speculate about
enum NodeKind { Heading, CodeBlock, Table, Footnote /* … */ }

fn render_all(nodes: &[Node], out: &mut String) {
    for node in nodes {
        match node.kind {
            NodeKind::Heading   => render_heading(node, out),   // direct call
            NodeKind::CodeBlock => render_code_block(node, out),
            NodeKind::Table     => render_table(node, out),
            NodeKind::Footnote  => render_footnote(node, out),
        }
    }
}
```

A `match` over a closed enum compiles to a direct call (or a jump table) per arm. There is no table index, no signature check, no guess — the engine has nothing to be wrong about, so performance no longer depends on how uniform the document happens to be. The alternative fix, generic monomorphization (`fn render_all<V: Visitor>`), works when the type is known at each call site rather than chosen per node.

Tradeoffs, and they are the classic ones for removing dynamic dispatch: the enum is **closed**, so a plugin cannot add a node type without editing the core — you have traded extensibility for predictability, which is the wrong trade if third-party extensions are a product requirement; monomorphizing generics instead duplicates code per type and grows the `.wasm`, which you are also budgeting ([[32 - Compilation and Machine Foundations/03 - LLVM and Compiler IR|build flags]]); and the `match` must be kept exhaustive as node kinds are added, which Rust enforces but which still touches one central file on every change.

> [!tip] The general rule for any speculating engine
> Do not optimize *for* the speculation — remove the need for it. A direct call always beats a correctly-guessed indirect one, and it beats an incorrectly-guessed one by a lot. In JavaScript the same move is keeping object shapes stable at hot call sites; in Rust-to-Wasm it is preferring closed enums or generics over trait objects in hot loops. Both are "give the compiler a fact instead of a hint."

## 4. Interview Answer

Short answer:

> Wasm's value types are declared in the binary and validated at load, so an engine never speculates about types and never needs to deopt for them. But it can speculate about behaviour — since Chrome M137, V8 speculatively inlines `call_indirect` targets when a call site has consistently resolved to one function. That is a guess about data, so it can be wrong, and a wrong guess needs a deopt.

Deeper answer:

> The sentence "Wasm never deopts because it's statically typed" welds two independent facts together. Static typing removes type speculation — still true. The absence of deopt was a separate design choice: V8's Wasm pipeline only ever tiered up unconditionally, using guaranteed-correct types, never speculating. `call_indirect` is where that broke, because the table index is a runtime value: Wasm guarantees the signature matches, not which compatible function is there. So if a site always resolves to one target, TurboFan deletes the indirection and inlines that body — and the key point is that the resulting machine code is no longer a faster version of the same program, it is a *narrower* program that is only correct while the bet holds. Running it for the wrong target isn't slow, it's incorrect, which is why deoptimization has to exist. I'd also separate a guard branch from a real deopt: a cheap check with an in-function fallback is just a branch, whereas a true deopt discards the whole optimized function, reconstructs baseline-tier state at that program point and resumes there — needed once the assumption was used to justify entangled optimizations like eliminated bounds checks or unboxed fields. This matters most for WasmGC, the target for OOP languages like Kotlin and Dart, whose virtual dispatch is structurally polymorphic but usually monomorphic in practice. And it's the same shape as mono/poly/megamorphic call sites in JS, so the practical advice transfers: uniform data at hot call sites, or remove the indirection entirely.

## 5. Practice

1. <details><summary>What exactly is wrong with "Wasm never deoptimizes because it's statically typed"?</summary>The <em>because</em>. Static typing does remove type speculation, permanently. But the absence of deopt was a separate design choice in V8's pipeline — tier up unconditionally on guaranteed-correct types, never speculate. Nothing stopped an engine speculating about non-type facts, and since Chrome M137 V8 speculates on <code>call_indirect</code> targets, so the conclusion is now false while the typing half remains true.</details>
2. <details><summary>The Wasm bytecode never changes. So why does a wrong guess about a call target require discarding compiled code?</summary>Because the guess was compiled <em>into</em> the machine code. Speculative inlining removes the table lookup and hardcodes one target's body, so the generated code is only equivalent to the program while that target holds. For a different target it would execute the wrong function — a correctness failure, not a slowdown. The specialized code has to be discarded and replaced with the general path.</details>
3. <details><summary>Distinguish a guard branch from a true deoptimization, and say when each is enough.</summary>A guard branch is a cheap runtime check with an in-function slow path — sufficient when the only thing riding on the assumption is the inlined call itself. A true deopt is required when the assumption justified other, entangled optimizations across the function (removed bounds checks, unboxed fields, reordering): one branch cannot unwind those, so the engine discards the whole optimized function, reconstructs baseline-tier state at that exact point, and resumes in the lower tier.</details>
4. <details><summary>Why does WasmGC benefit most from call-target speculation, and which languages benefit least?</summary>WasmGC adds GC'd reference types, making Wasm a practical target for OOP languages (Kotlin, Dart, Java-family) whose virtual dispatch compiles to dense <code>call_indirect</code> through vtables — structurally polymorphic but usually monomorphic in practice, which is exactly the profile speculation exploits. C, C++ and Rust produce far fewer polymorphic indirect calls, so they gain little from this particular optimization.</details>
5. <details><summary>Transfer: your Rust-to-Wasm library is fast on fixtures and slow on real data. Name the likely mechanism and two fixes with their costs.</summary>A hot call site over trait objects (<code>Box&lt;dyn Trait&gt;</code>) becomes <code>call_indirect</code>; homogeneous fixtures make it monomorphic and speculation wins, heterogeneous real data makes the guard fail constantly and can cause deopt thrash. Fix 1: a <code>match</code> over a closed enum, giving direct calls — costs extensibility, since plugins can no longer add variants. Fix 2: generic monomorphization — costs binary size, which is also budgeted. Both replace a hint with a fact.</details>

## Related Notes

- [[32 - Compilation and Machine Foundations/10 - Compiling to WebAssembly|Compiling to WebAssembly]] — how the binary and its types get there.
- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]] — the JS deopt story and the Wasm bypass, at must-know depth.
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] — what a deopt reconstructs, and the downhill directions.
- [[32 - Compilation and Machine Foundations/04 - AOT JIT and the Portability Tradeoff|AOT, JIT and the Portability Tradeoff]] — what a JIT knows that an AOT compiler cannot.
- [[32 - Compilation and Machine Foundations/05 - Reflection and Compile-Time Codegen|Reflection and Compile-Time Codegen]] — dynamic dispatch versus resolving it at build time.
