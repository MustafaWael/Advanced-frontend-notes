---
tags: [vault-operations, review, curriculum, v8, webassembly]
review_status: resolved
resolved_on: 2026-09-08
reviewed_on: 2026-09-07
scope: staged changes, new Module 32, related runtime notes, Lab 07, and review notes
---

# Staged Content Review — 2026-09-07

> [!tip] Status: **RESOLVED — 2026-09-08.** The two P1 items (Wasm feedback/tier-up language, TDZ as runtime semantics) and the four P2 items (inline-cache guards, threaded dispatch, microtask ownership, the Node/browser environment mismatch) were corrected and committed. The findings below are preserved as the historical review record. Frontmatter uses `review_status` rather than `status` so this note stays out of the study views and the `status` vocabulary.

## Purpose

This is a handoff for revising the currently staged Advanced JavaScript vault changes. It distinguishes material that is sound, material that must be corrected, and improvements that would make the new module more durable.

The review covered the staged notes, Module 32, the connected V8/runtime additions, Lab 07, the glossary, and the two staged review notes. It did not change any learning content.

## Outcome

**Status: revise before committing the learning-content expansion.**

The structure is strong and the new module fills a valuable conceptual gap. However, several repeated claims turn implementation details into universal rules, and a few directly conflict with the staged notes' otherwise accurate coverage of modern V8/WebAssembly behavior. Correct the P1 items first; P2 items should be resolved in the same pass because they recur in recaps, glossary entries, and interview answers.

## Review Evidence

- The staged diff has **34 files**, about **3,660 additions** and **69 deletions**.
- `git diff --cached --check` passed: no whitespace errors were found.
- The vault's wiki-link graph resolves for the newly added and modified learning notes. Existing unresolved-looking values are code examples or template placeholders, not broken new links.
- This is a documentation/curriculum change rather than an executable application change, so there are no application tests to run. The review instead checked content consistency, source quality, local link integrity, and several version-sensitive claims against primary specifications and V8 material.

## What Is Correct and Worth Preserving

### Curriculum and navigation

- **Module 32 is clearly marked as a deep dive and off the core interview path.** Its placement in [[00 - Start Here]] and [[01 - Roadmap]] prevents it from displacing the must-know curriculum while still making it discoverable.
- **The module's shape is excellent.** It gives a coherent progression from source text and IR, through bytecode encodings and LLVM, to CPU/memory concepts, WebAssembly, deoptimization, and a practical lab.
- **Cross-linking is strong.** The module connects back to Runtime Foundations, TypeScript, frontend tooling, performance, and the labs rather than presenting machine concepts as isolated trivia.

### Teaching choices

- **The stack/register/accumulator distinction is useful and generally well explained.** In particular, separating a virtual machine's registers from CPU registers is an important misconception to address.
- **The “compile once, run many” transfer is excellent.** The lab connects interpreter overhead to real frontend decisions such as hoisting work, avoiding repeated parsing, and minimizing boundaries.
- **The Lab 07 acceptance criteria are unusually concrete.** Shared correctness tests, liveness/spilling checks, a disassembler, and a no-timing-threshold policy are all good instructional design.
- **The updated V8 note correctly emphasizes that fixed call-count folklore is not a dependable interview answer.** Keep the advice to explain the mechanism and identify version-specific details rather than memorizing a threshold.
- **The staged M137 WebAssembly material identifies a real current change.** V8 added speculative `call_indirect` inlining and Wasm deoptimization in Chrome M137. Preserve this distinction: static types remove *type* speculation; they do not prevent every possible runtime speculation. [V8: Speculative Optimizations for WebAssembly using Deopts and Inlining](https://v8.dev/blog/wasm-speculative-optimizations)

### Mechanical hygiene already verified

- The staged content passes the whitespace check.
- New/modified note links resolve.
- The source-anchor habit is good. Retain it, but make the anchors accurate and specific as described below.

## Corrections Required

### P1 — Wasm is incorrectly described as having no feedback, warm-up, or tier ladder

**Primary locations:**

- [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon]] — lines 82, 137, and 152
- [[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode]] — related absolute wording at lines 84–85 and 174

The sentence “Wasm needs no feedback vector, no inline caches and no warm-up” is too broad and internally conflicts with the staged [[32 - Compilation and Machine Foundations/11 - Wasm Speculation and Deopt|Wasm Speculation and Deopt]] note.

In current V8, Liftoff records call-target feedback at Wasm call sites, and a function tiers up to TurboFan when it is hot enough. V8 then uses that feedback to choose speculative `call_indirect` inlinees. Static Wasm types remove **JavaScript-style type feedback**, but they do not remove all profiling, optimization tiering, or warm-up for optimized code. [V8's M137 explanation](https://v8.dev/blog/wasm-speculative-optimizations)

**Required rewrite direction:**

> Wasm validates value types ahead of execution, so it avoids JavaScript's type-feedback warm-up and type-based deopts. Engines can still collect non-type feedback (such as indirect-call targets), tier hot functions, and speculate about runtime behavior.

Do not replace the old claim only in one paragraph. Search the module for variants of `no feedback`, `no warm-up`, `no tier ladder`, and `never interpreted`, then make the language consistently scoped to **type** uncertainty or to a named engine/version.

### P1 — TDZ and hoisting are misclassified as compile-time semantic-analysis behavior

**Primary location:** [[32 - Compilation and Machine Foundations/12 - Compiled vs Interpreted and Every Stage Between]] line 126.

The note says that “TDZ and hoisting are semantic-analysis artefacts rather than runtime magic.” That overstates static analysis. Static semantics establish declarations and early errors, but lexical binding initialization and the `ReferenceError` caused by reading an uninitialized lexical binding occur during evaluation at runtime. The staged [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]] note itself demonstrates the runtime mechanism through V8's hole sentinel.

**Required rewrite direction:**

> Static semantics determine which declarations and bindings are valid. During evaluation, lexical bindings are created uninitialized and become initialized when execution reaches their declaration; reading one first triggers the TDZ `ReferenceError`.

Avoid suggesting that TypeScript or a generic compile phase can reproduce every TDZ outcome; control flow and runtime evaluation matter.

### P2 — Stable object shapes do not make inline-cache checks unnecessary

**Primary locations:**

- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime]] line 230
- The same note's recap at line 350 and common-mistakes section at line 377

The note correctly says a monomorphic inline cache performs one shape check, then immediately says that consistent shapes make the engine's guess “unnecessary.” These cannot both be true for a general property access. A monomorphic IC still guards the receiver's map/shape. Optimized code may hoist or remove a guard only when it can prove a stronger invariant.

**Required rewrite direction:**

> Consistent shapes keep an inline cache monomorphic, making its guard predictable and allowing the optimizer to specialize the load. In contexts where the receiver's shape is provably fixed, the optimizer may hoist or eliminate a guard.

This retains the practical advice without promising that application code can simply remove the engine's checks.

### P2 — “There is no interpreter loop” is an overcorrection

**Primary locations:**

- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up]] lines 17, 39, 141–153, and 265
- [[02 - JavaScript Runtime Foundations/08 - Engine and Compilation Glossary]]
- references throughout Module 32 and Lab 07

V8 uses **threaded dispatch**, so it does not need one central `while` + `switch` dispatcher. Handlers dispatch directly to the next handler through a table; that improves branch prediction relative to a central dispatch site. But the interpreter still repeatedly reads/dispatches bytecode. Saying “there is no interpreter loop at all” will confuse readers and creates a brittle, implementation-shaped interview answer. [V8 discusses Ignition's dispatch-table approach](https://v8.dev/blog/regexp-tier-up)

**Required rewrite direction:**

> Ignition avoids a central switch-based dispatch loop. Its threaded handlers transfer directly to the next handler through a dispatch table, reducing the branch-prediction cost of central dispatch.

### P2 — The microtask ownership model is presented too definitively

**Primary location:** [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue]] lines 217–230.

The note assigns the microtask queue to “the engine” and says microtask ordering is identical across Chrome, Node, Deno, and Bun. That conflates an implementation mechanism with the platform model. ECMAScript defines jobs and host enqueue hooks; browser microtasks are defined by the HTML event loop, whose event loop owns a microtask queue. V8's `MicrotaskQueue` is an implementation API, not the cross-platform ownership rule. [ECMAScript host job hooks](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html), [HTML microtask queue](https://html.spec.whatwg.org/multipage/webappapis.html)

**Required rewrite direction:**

> Promise reactions are ECMAScript jobs scheduled through host hooks. In browsers, the HTML event loop owns the microtask queue and runs checkpoints; an embedding engine such as V8 provides implementation APIs that the host may use. Do not infer identical ordering across hosts beyond the specific ordering guarantees involved.

Keep the useful `process.nextTick()` distinction, but identify it as Node-specific scheduling behavior.

### P2 — The bytecode reproduction command and global-binding explanation use incompatible environments

**Primary location:** [[03 - Scope and Variables/04 - Hoisting and TDZ]] lines 123–128.

The shown bytecode describes script-like global behavior (`StaGlobal` and a function declaration as a `globalThis` property), but the suggested command is `node --print-bytecode ... file.js`. Node normally evaluates `.js` files as CommonJS modules, where top-level declarations are module-scoped rather than properties on `globalThis`. [Node's CommonJS module model](https://nodejs.org/api/modules.html)

**Required rewrite direction:** choose one of these approaches:

1. Present it explicitly as a V8 shell/browser classic-script illustration and use an appropriate V8-shell command, or
2. Keep the Node command, but rewrite the bytecode discussion around Node's CommonJS wrapper and remove claims about `globalThis.a`.

Also state that printed bytecode is V8-version and embedding dependent, so opcode sequences should illustrate a mechanism rather than be presented as universal output.

### P3 — One source anchor is mislabeled

**Location:** [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up]] line 27.

The anchor label says “Lazy deserialization / code flushing context” but links to `short-builtin-calls`, not V8's lazy-deserialization/code-flushing article. Point it to [Lazy deserialization](https://v8.dev/blog/lazy-deserialization) or [A lighter V8](https://v8.dev/blog/v8-lite), depending on the claim being sourced.

## Enhancements That Would Improve the Module

These are not blockers, but they would make the material more reliable and easier to maintain.

### 1. Add a version-scope callout for all engine-specific claims

Module 32 is admirably concrete, but its claims span V8, browsers generally, Node, Wasm, LLVM, and hardware. Add a short callout near the module MOC:

> **Implementation scope.** V8 internals, bytecode opcodes, thresholds, and tiering heuristics are implementation details that change between versions and differ across engines. Treat them as explanatory models, not API guarantees. Each implementation-specific note should name its engine and source date/version.

This prevents current M137 facts and older pre-M137 descriptions from drifting apart again.

### 2. Separate three categories consistently

The most useful maintenance rule for the module is to label claims as one of:

- **Specification:** ECMAScript, HTML, Wasm Core.
- **Named implementation:** e.g., “V8 13.x / Chrome M137.”
- **Teaching model:** a simplified diagram that intentionally omits implementation details.

This is especially important for microtasks, DOM bindings, hidden classes, bytecode flushing, CPU behavior, and Wasm execution strategy.

### 3. Add a compact “current exceptions” panel to the Wasm notes

The module already catches the M137 deoptimization change. Centralize it in one small panel and link to it from the other Wasm notes:

| Static guarantee | Still dynamic in V8 |
| --- | --- |
| Value types are validated before execution | Indirect-call targets are runtime data |
| No JS-style type profiling is needed | Call-target feedback may be collected |
| No type-based deoptimization | Behavior-based speculation may deopt |
| Baseline compilation can begin quickly | Optimized tiering still needs hotness/heuristics |

That panel will prevent the “Wasm is static, therefore nothing warms up” inference.

### 4. Treat raw engine output as illustrative, not a contract

For every `--print-bytecode`, trace flag, bytecode offset, or generated assembly example:

- name the engine/version/embedding;
- say it is representative output;
- avoid using output from a Node CommonJS context to explain browser-script globals;
- prefer semantic assertions readers can verify across versions.

### 5. Add a lightweight content-validation checklist

Before staging future vault expansions, check:

- each source anchor points to the material named by its label;
- every absolute word (`always`, `never`, `only`, `all`) has either a scope or a primary source;
- linked notes do not contradict the new note;
- examples use the same execution environment as their reproduction commands;
- recaps, glossary entries, and interview answers repeat the corrected—not a simplified contradictory—claim.

## Suggested Claude Work Plan

1. Correct the two P1 items first: Wasm feedback/tiering language and TDZ runtime semantics.
2. Search the vault for repetitions of the incorrect phrases and update each recap, glossary entry, interview answer, and lab reference in the same pass.
3. Correct the P2 inline-cache, threaded-dispatch, microtask, and Node-environment explanations.
4. Repair the mislabeled V8 source link.
5. Add the version-scope callout and the Wasm static-vs-dynamic panel.
6. Re-run the whitespace check and inspect every changed wiki-link target before staging.

## Acceptance Checklist for the Revision

- [ ] No note says Wasm has “no feedback,” “no warm-up,” or “no tier ladder” without qualifying the statement as about JavaScript-style *type* feedback or a specific engine phase.
- [ ] The M137 Wasm-deoptimization material and every older Wasm overview agree.
- [ ] TDZ is described as runtime initialization/access behavior, with static semantics clearly separated.
- [ ] A monomorphic inline cache is described as guarded/specializable, not as a check-free fact.
- [ ] Threaded dispatch is described as avoiding a central switch loop, not as eliminating interpreter iteration.
- [ ] Browser/HTML microtask ownership is not conflated with V8's embedding API.
- [ ] The V8 bytecode example and its execution command use the same runtime context.
- [ ] Every source anchor's label matches its destination.
- [ ] `git diff --cached --check` remains clean and newly modified wiki links resolve.

## Non-Content Staging Note

The staged set also includes `.DS_Store` files and an Obsidian workspace file. They may be intentional because the repository already tracks them, but they are machine-specific churn. Keep them only if the team deliberately versions local Finder/Obsidian state; otherwise split them out of the learning-content commit.
