# Module 02 — Runtime Foundations Enhancement Prompt

Copy everything below the line into a new session with this vault folder connected.

---

You have access to my Obsidian vault "Advanced JavaScript". Work ONLY inside `02 - JavaScript Runtime Foundations` (plus the small cross-file updates listed in Phase 4). The vault targets a mature mid-level/senior frontend developer: mechanisms, production bugs, tradeoffs, and interview answers — never memorized definitions.

Before writing anything, read all 8 notes in `02 - JavaScript Runtime Foundations` to internalize the house style: **Maturity Target → Source Anchors → numbered sections (simple explanation, why it matters, accurate mechanism, real frontend example, common bugs, interview answer, practice with `<details><summary>Show answer</summary>` blocks) → Related Notes**. Wikilinks use full path + alias: `[[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]`. Callouts: `> [!warning]` for footguns, `> [!tip]` for production patterns, 2–5 per note. Keep frontmatter fields exactly as they are (tags, module, priority, status) — do not reset my `status` values.

## Phase 1 — Accuracy fixes (do these first)

1. **`03 - Execution Context`, section "Block Scoping under Lexical vs. Variable Environments"**: it attributes spec behavior to V8 ("V8 creates a Block Environment Record"). Fix the layering: the spec model creates a new **declarative Environment Record** for the block; that is ECMAScript, not V8. Then add one `> [!tip]` on what engines actually do: V8 only heap-allocates an environment when a closure captures its bindings; uncaptured `let`/`const` live in stack slots or registers. This distinction (spec model vs engine storage) is itself a senior interview signal — say so.
2. **`05 - Memory Heap`, section 9 "The Cost of Holes"**: "degrades lookup performance from O(1) to a linear walk" is overstated. Correct mechanism: a hole forces the engine off the fast element-access path — it must check `Array.prototype` and `Object.prototype` for an indexed property (a prototype-chain check, not a linear walk over elements) and often falls back to dictionary/slow elements. Keep the production rule. Also add: `new Array(n).fill(0)` produces a PACKED array, so preallocation is fine when immediately filled. Fix the same "prototype walk" phrasing in practice answer 6 and in checklist drill answer 9.
3. **`05 - Memory Heap`, section 9 heading placement**: element kinds are engine optimization, not heap lifetime. Keep the section but open it with one sentence acknowledging the layer ("this is engine implementation detail, not spec behavior — useful for hot paths, not a daily rule").

## Phase 2 — Upgrade `02 - JavaScript Engine and Runtime`

1. Replace the generic pipeline diagram with V8's actual named tiers, keeping the note engine-agnostic in framing ("V8's current pipeline, as one concrete example; SpiderMonkey and JavaScriptCore have analogous tiers"):
   - **Ignition** — compiles to bytecode, interprets, collects type feedback.
   - **Sparkplug** (2021) — baseline compiler, bytecode → machine code in one pass, no feedback needed (~8 invocations to tier up).
   - **Maglev** (Chrome M117) — mid-tier optimizing compiler using feedback; ~10x slower to compile than Sparkplug, ~10x faster than TurboFan.
   - **TurboFan** — top tier for the hottest code; since 2025 its backend runs on **Turboshaft** (CFG-based IR replacing Sea of Nodes).
   - Deoptimization: any tier's optimized code bails back to lower tiers when type feedback assumptions break.
   Verify current details against https://v8.dev/blog/maglev and https://v8.dev/blog/leaving-the-sea-of-nodes before writing; add them as Source Anchors.
2. Add a new section **"Hidden Classes and Inline Caches"** — this is the missing name for what the existing "Engine-Friendly Data Shape" section demonstrates:
   - Hidden classes / shapes / maps: engines assign each object a shape describing its property layout; objects created with the same property order share a shape.
   - Shape transitions: adding properties in different orders, or deleting properties, creates divergent shapes.
   - Inline caches (ICs): call/property sites cache the shapes they've seen — **monomorphic** (1 shape, fastest) → **polymorphic** (2–4) → **megamorphic** (many, falls to slow path).
   - Traced example: an API-normalizing function that receives objects with consistent vs inconsistent key order, and why `delete obj.key` is worse than setting `undefined` (with the tradeoff: `in`/`Object.keys` semantics differ).
   - Close with the existing note's discipline: this explains the *why* behind stable data shapes; optimize measured hot paths only.
3. Extend the "Common Mistakes" and practice Q&A to cover the new material (e.g. "what is a monomorphic call site?", "why can property order matter?").

## Phase 3 — Targeted gap fills in the other notes

1. **`01 - ECMAScript vs JavaScript`**:
   - Name the TC39 process explicitly: stages 0–4 (including 2.7), stage 3 ≠ safe to rely on, stage 4 = finished and merged into the annual ECMAScript edition. One short table or list, link https://tc39.es/process-document/.
   - Add one paragraph on runtime interoperability: `fetch` is host API but now ships in Node 18+, Deno, Bun, and edge runtimes; **WinterTC** (formerly WinterCG) standardizes a minimum common API across server-side runtimes. Verify current WinterTC naming/status before writing. This sharpens the note's existing point: "host API" no longer means "browser-only", it means "defined outside ECMA-262".
2. **`04 - Call Stack`**:
   - Add a short section **"Stack Limits and Tail Calls"**: stack size is engine- and thread-configurable, not spec-defined (so overflow depth differs across browsers/Node); ES2015 specifies proper tail calls but only JavaScriptCore (Safari) ships them — so never rely on PTC for recursion safety. Interview-bait quality.
   - Add a `> [!tip]` on async stack traces: DevTools stitches frames across `await`/`.then` boundaries; `error.stack` is non-standard and formats differ across engines; Node's `Error.captureStackTrace` is V8-specific.
3. **`05 - Memory Heap`**:
   - Add a brief section **"Generational Collection (Overview)"**: most objects die young; V8 splits the heap into young generation (minor GC, Scavenger, cheap and frequent) and old generation (major GC, Mark-Compact, concurrent/incremental via Orinoco). Keep it to ~10 lines and link to [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]] as the deep-dive home — do not duplicate module 13 content.
4. **`06 - Realm Agent and Job Queue`**:
   - Extend the Worker section with **structured clone limits**: functions and DOM nodes throw `DataCloneError`; class instances lose their prototype (arrive as plain objects); `Map`/`Set`/`Date`/`ArrayBuffer` survive. Show a 5-line failing `postMessage` example and the fix (send plain data, rehydrate on arrival).
   - Add **transfer vs copy**: `postMessage(buffer, [buffer])` transfers ownership (zero-copy, source is neutered) vs structured clone copy — one traced example with a large `ArrayBuffer`.
   - Add a short **Atomics** paragraph next to the SharedArrayBuffer section: `Atomics` provides race-free reads/writes and `Atomics.wait` for blocking — but `Atomics.wait` throws on the main thread (only workers may block). One sentence on why.
   - Optionally mention the **ShadowRealm** proposal as the future spec-level answer to "run code in a fresh realm" — verify its current TC39 stage at https://github.com/tc39/proposals before writing; if still not stage 4, label it clearly as a proposal.

## Phase 4 — Integration pass

1. Update `07 - Runtime Foundations Checklist`: add checklist items for hidden classes/ICs (monomorphic vs megamorphic), V8 tier names, TC39 stages, tail calls/stack limits, structured clone limits, transferables, Atomics main-thread restriction, and generational GC. Fix drill answer 9 per Phase 1.2. Add one new debugging drill (e.g. "worker postMessage throws DataCloneError" → host/runtime + application layer).
2. Update `00 - JavaScript Runtime Foundations MOC`: extend the "You're Done When" list with the new outcomes.
3. Add cross-links both directions where new content touches other modules: `02` engine tiers ↔ `13 - Performance and Memory` notes; `06` structured clone ↔ `19 - DOM and Browser APIs/09 - Web Workers and Offloading Work`; `01` TC39 stages ↔ `99 - Glossary` (add terms: hidden class, inline cache, monomorphic, megamorphic, transferable, WinterTC, proper tail call, Scavenger, Mark-Compact — only if the glossary exists and the terms are missing).

## Phase 5 — Verification (do not skip)

- Verify every technical claim added in Phases 2–3 against v8.dev, tc39.es, MDN, or the HTML Living Standard; every new section needs at least one real Source Anchor URL added to its note.
- Grep all `[[...]]` wikilinks you added or touched and confirm each resolves to a real file.
- Confirm no existing content was lost — new material extends, never replaces, except the specific fixes in Phase 1.
- Confirm every extended note still reads as one coherent note (renumber internal sections if needed; never rename files).
- Print a final summary: files modified, sections added, claims verified with their source URLs, link-check result.

Quality over speed. If session limits force a stop, finish the current note cleanly and tell me the exact resume point.
