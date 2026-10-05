# Execution Context: diagnosis and upgrade plan

This document covers `human-first-guides` upgrade steps 1 to 4 for `Advanced JavaScript/02 - JavaScript Runtime Foundations/03 - Execution Context.md`.

The note hasn't been changed yet. The plan below needs your approval first.

**The note today:**
- 284 lines: about 1,600 words of prose and 190 words of code.
- `must-know`, module 02. AGENTS.md treats this as a first-principles module, so the plan uses the spec model, with V8 facts as labeled asides.
- `status` stays `learning`.

## The diagnosis in six lines

1. **Terms.** 25 terms are used. 15 are never explained, and 4 are "defined" only with other unexplained words. The worst is *binding*: 22 uses, in two different senses, and neither sense is explained.
2. **Spine.** A good spine is already in the note but buried at L98: the four questions ("what names exist?", "what does `this` mean?", "where are we resuming?", "which realm's built-ins?"). None of the sections says which question it answers.
3. **Examples.** The first examples of block scoping, `this` and realm arrive 117, 94 and 175 lines after those ideas are introduced. None of the 8 code blocks ends by saying what it shows. The clearest closure sentence is hidden in answer 5 (L273).
4. **Links.** Sections 1 to 8 contain no links. Realm, `this`, async/await and generators never link to their own notes.
5. **Accuracy.** 13 items, all verified (listed below). Four are serious: `this` is described as a part of the context, which is the ES5 layout; a module's environment is called its "execution context"; the iframe case says the array is *posted* while the code reads it directly; and `Array.isArray` is said to check "the internal slot".
6. **Strengths.** Three passages are the best in the note and the plan builds on them: the tick-by-tick loop trace (L190–197), the block-entry steps labeled as specification (L61–66), and the `var`/`let` hoisting pair (L78–86).

## Step 1: what I read

- **The note itself.** Its sha256 is unchanged since 2026-10-05 17:45.
- **Prerequisite: note 02, Engine and Runtime.** The note has no `Dependencies:` line, so I took the previous note in the reading order. Note 02 names the "execution context stack" (L125) and says the engine "manages execution contexts" (L365, L398), but never explains either. So you arrive knowing the phrase and nothing else.
- **Dependents:** 21 notes link here. I checked the ones that rely on its model:
  - Call Stack (L24): "the stack of active execution contexts".
  - Lexical Environment.
  - What is this.
  - Async Await.
  - ES Modules.
  - Glossary.
  - The module checklist and the MOC.
  - 30 Interview Questions.
- **Link targets.** All 9 resolve. I read §1 of each, so the primers can't contradict them:
  - var let const
  - Closures
  - Tasks vs Microtasks
  - ES Modules
  - Server vs Client JS in Next.js
  - Call Stack
  - Lexical Environment
  - Hoisting and TDZ
  - Stale Closures
- **Homes of concepts the note primes:**
  - Realm, Agent and Job Queue (§1 and §3)
  - What is this
  - Arrow Functions and Lexical this
  - Async Await
  - Iterators and Generators
- **Authorship.** All commits are yours. Per the skill, existing prose is treated as yours, so the wording changes are listed separately below for you to approve.

## Step 2: diagnosis

### Term ledger (condensed)

| Term | First use | Explained? | Fix |
| --- | --- | --- | --- |
| *binding* (a name tied to a value) | L50 | never; 16 uses | primer |
| *binding*, as in "`this` binding" | L26 | never told apart from the sense above; 6 uses | taught here, and goes in the confusables box |
| lexical environment / variable environment | L26 | only with other unexplained words (L50–51) | primers, then the Q1 section |
| Environment Record, outer link, "declarative" | L62, L50 | never | primer ("table of names") |
| realm | L26 | "intrinsics" at L53 is never explained; first concrete meaning comes at L238, 212 lines later | primer, plus a 3-line example where it's introduced |
| continuation, promise scheduling, microtask | L95 | never; 8 + 5 uses | primer: "the rest of the function after `await`" |
| suspend / resume | L95 | only in Common Mistakes (L249) | Q4 section |
| execution context stack vs call stack | L56 / L37 | never said to be the same thing | confusables box, plus a link to note 04 |
| closure | L35 | only in answer 5 (L273) | Q1 section, copying that sentence |
| TDZ | L34 | spelled out at L86, 52 lines later | spell it out at first use |
| receiver, strict mode, module environment | L161, L93 | never | short glosses |
| evaluation / evaluate | L16 | never; 17 uses, used to mean "run" | plain words |

Density: L26 introduces 5 new terms in one sentence. The skill's rule of thumb is two per paragraph.

### Spine, examples, links

- **Spine.** The four questions at L98 can carry the whole note: every existing section already answers one of them. Bridge sentences: 0 of 12 sections have one. Checkpoints: none.
- **Examples:**
  - There's no running example; the 8 code blocks are never reused.
  - No predict-first prompts, and there's no trace table.
  - Three costumes of one mechanism are scattered and never compared: the render closure (§6), the `var` loop (Use Case 1) and stale closures.
  - No code block says which environment it runs in.
- **Links.** 0 inline links in the teaching sections. "Where this fits" and "What this unlocks" are both missing. The template's Interview signal, Production signal and Dependencies lines are missing too.

### AI tells (rule 8)

| Line | Text | Tell |
| --- | --- | --- |
| L26 | definition built from five unexplained terms | dictionary loop |
| L28 | "In simpler words:" | formal-then-plain order |
| L32–42 | seven bare topic bullets, plus "many advanced topics stop feeling separate" | list where the relationships are the point, and a connection claimed but not shown |
| L46, L52, L244 | "At a high level", "where applicable" | hedges |
| L51, L92, L254, L272 | "…behavior" | a word with no content |
| L68–69 | "a senior interview signal… separates a memorized answer from a mature one" | evaluative filler |
| L181 | "The one interviewers reach for when they want to see if you actually understand…" | evaluative framing |
| L216 | "This works/fails because" | template residue |
| L95, L140, L248–249, L256, L272 | the `await` suspension is explained five times | repetition |

### Accuracy (all verified, 2026-10-06)

| # | Where | Problem | Correct version | Evidence |
| --- | --- | --- | --- | --- |
| A1 | L26, L52, L94, L242, L244 | `this` is listed as a part of the context. | That's the ES5 layout. In the current spec, `this` lives in tables of names: a function's environment record holds it, and lookup walks outward from the LexicalEnvironment. Arrow functions' records have no `this`. | read262 §9.4 tables; Function Environment Records; ES5.1 §10.3 Table 19 |
| A2 | L59 | "The separation … is what enables ES6 block scoping." | The split already existed in ES5, where `with` and `catch` moved the LexicalEnvironment while the VariableEnvironment stayed put. ES2015 reused it for blocks. | ES5.1 §10.3 |
| A3 | L65 | `var` "written directly to the VariableEnvironment's record" | The binding is *created* there at function entry. A `var x = 1` inside a block *writes* to it by walking outward from the LexicalEnvironment. | spec: VariableStatement / ResolveBinding |
| A4 | L62 | an "`if` block or `for` loop" creates the record | The `{ … }` block creates it. `for (let …)` makes one record per pass. | spec: Block, CreatePerIterationEnvironment |
| A5 | L69 | "V8 only heap-allocates a scope when a closure actually captures…" | V8 decides from the source, at compile time. A local that any inner function *refers to* goes into a heap context even if that closure is never created at runtime. Uncaptured locals live in the interpreter's register file, which is part of the stack frame. No version is given. | captured: `--print-bytecode`, V8 12.4.254.21 / Node 22 |
| A6 | L93 | modules are "strict by default" | Module code is *always* strict; there is no opt-out. | spec |
| A7 | L216 | "module evaluation is a single execution context whose environment stays reachable" | The module's context is popped when evaluation ends. What lives on is its module environment record, held by the cached module. This line mixes up the two things the note teaches apart. | spec |
| A8 | L203, L216 | "once per realm", "shared across every request" | It needs a scope: "for as long as that server process keeps the module loaded". | host behavior |
| A9 | L225 vs L229 | the widget "posts an array" | A *posted* array is copied into the parent's realm, so `instanceof Array` is `true`. The bug needs a direct same-origin reference, which is what the code actually does. | captured: `structuredClone` of a `vm`-realm array gives `instanceof Array === true` |
| A10 | L238 | `Array.isArray` "checks the internal slot" | IsArray checks whether the value is an Array exotic object (unwrapping proxies), whichever realm made it. | read262 §7.2.2 |
| A11 | L251 vs L26 | "a precise runtime record" vs "specification model" | The spec calls it "a specification device that is used to track the runtime evaluation of code". Engines needn't build it literally. | read262 §9.4 |
| A12 | L193 | "closes over that single environment record" | Each pass of the loop body gets its own block record. All three arrows reach the same `i` binding. | spec: Block |
| A13 | L194 | "the current execution context runs to completion" | Run-to-completion belongs to the task: the whole stack empties before a timer task runs. Note 04 phrases it this way. | HTML |

The ES5 `this` layout (A1) is repeated in four other places. Fixing these is step 6, the sweep:
- `99 - Glossary.md` L291
- the MOC "You're Done When" checklist, L40
- `07 - Runtime Foundations Checklist` L39
- `18 - Revision Plans/04 - 30 Interview Questions` L38

## Step 3: what already works (kept as the pattern)

1. The loop trace at L190–197 becomes the note's **knot example**, with each step labeled by concept and linked.
2. The block-entry steps at L61–66 are the note's only explicit spec label, and they become the model for labeling everything else.
3. The two-phase hoisting pair at L73–86 already does example-at-introduction and contrast.
4. The four questions at L98 become the spine.
5. The `SaveButton` pair in §8 is a real one-change contrast pair taken from React work.
6. L123: "This is normal JavaScript; React makes the lifetime visible." This is exactly the React bridge the vault wants.

## Step 4: the plan

### Shape after the upgrade

| Part | Change | Tier |
| --- | --- | --- |
| Maturity Target | Add Interview signal, Production signal and Dependencies (note 02). Re-estimate study time. | 1 |
| Source Anchors | Point to the spec sections themselves: Execution Contexts and Environment Records. | 1 |
| `[!tip] How to read this note` | Say which parts are the spine and which are optional depth. | 3 |
| §1 Simple Explanation | The new order:<br>1. Where this fits.<br>2. A React hook.<br>3. A running example with "predict the output".<br>4. The four questions, moved up from L98.<br>5. The official name.<br>6. The spine sentence.<br>7. **Words you need first**: binding; table of names and outer link; realm; call stack; continuation.<br>8. A checkpoint. | 1–3 |
| §2 Why It Matters | The 7 bullets become because-lines, each with a link and each ending at something observable. | 2 |
| §3 Accurate Mechanism | Organized by the four questions. The table is rewritten with a "question it answers" column, and A1 is fixed. The block steps are kept (with A2 to A4 fixed). The V8 aside is labeled as implementation, fixed per A5. A **Don't mix these up** box is added. | 1–2 |
| §4 Creation vs Execution | Kept, with a bridge ("Q1 in time order") and the spec order (the context is pushed, then names are set up). Adds the running example's **trace table**. | 2–3 |
| §5–§8 | Kept. Each opens with a bridge naming its question and ends with "What this shows". Glosses for continuation and receiver. §8 states its single change, why the arrow fixes it, and what the fix costs. | 2 |
| Real-World Use Cases | Kept in place. Use Case 1 gets knot labels. A7 to A10 are fixed. Each case gets "What this shows", and one closing line says what the cases share. | 2 |
| Same mechanism, three costumes | The `var` loop, the React interval and a debounce helper, plus the shared mechanism. Module state is called out as a *different* mechanism. | 3 |
| One-Screen Recap | The four questions, plus closure, block vs context, and realm. Goes before the Interview Answer. | 3 |
| §9–§11 | Corrections swept into these. Common Mistakes gets 2 non-examples and drops the duplicate `await` callout. | 1 |
| Related Notes | Each link annotated with what it takes from this note, and the missing homes added. | 2 |

### Cost by tier

| Tier | Prose added | Study time (now 50–70 min) |
| --- | --- | --- |
| 1, followable | about +300 words (primers +170, glosses and fixes +190, cuts −60) | 55–75 min |
| 1 + 2, connected | about +1,250 words | 65–85 min |
| 1 + 2 + 3, full examples | about +2,000 words, plus about 25 lines of code | 75–95 min |

**Text that has to stay in sync afterwards:**
- Each primer and its home note.
- The closure sentence in Q1 and in answer 5.
- The realm example at its introduction and in Use Case 3.
- The A1 correction in §1, §3, the recap, the interview answer, and the four sweep files.

### Your wording I'd change

Everything not listed here stays word-for-word.

| Lines | Words now | Change |
| --- | --- | --- |
| L26, L28 | 61 | Replaced by the plain-first opening (A1, A11) |
| L32–42 | 43 | Replaced by because-lines; L42 dropped |
| L46 | 4 | "At a high level," dropped |
| L48–54 (table) | about 75 | Rows rewritten as "question → plain job"; A1 fixed in the `this` row |
| L59, L62, L65 | about 90 | A2, A4, A3 precision fixes |
| L68–69 | 87 | Content kept; labeled V8 12.4 implementation; A5 fixed; the evaluative tail dropped |
| L93–96 | about 50 | Glosses added; A6 fixed |
| L181 | 20 | Replaced by a bridge sentence |
| L192–194 | about 60 | A3, A12, A13 tweaks |
| L203, L216, L219 | about 90 | A7 and A8 fixed; "works/fails" removed |
| L225, L238 | about 45 | A9 and A10 fixed |
| L242–244 | about 75 | A1 and A11 swept |
| L248–249 or L256 | 56 or 14 | Keep one of the two duplicates |
| L251 | 19 | Aligned with "specification device" (A11) |

### Not in this pass (follow-ups)

- Realm §7 repeats the "posted array" overstatement (A9).
- Realm and Call Stack don't link back here inline.
