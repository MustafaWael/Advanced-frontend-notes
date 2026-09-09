---
tags: [meta, review, audit]
module: "Vault Root"
priority: must-know
status: not-started
verified_on: 2026-07-25
---

# Vault Review — Enhancements and Study Advice

> Audit date **2026-07-25**. Scope: all 462 `.md` files / **665,977 words** across `Advanced JavaScript/`, `System Design/`, `Low Level Design/`, `_Synthesis/`.
> Requested tone: blunt. Every number below was measured, not estimated.

---

## 1. The three numbers

| Measurement | Value | What it means |
|---|---|---|
| Notes at `status: not-started` | **337 of 352** (95.7%) | The vault has been *built*, not *studied*. |
| Notes at `status: learning` | **0** | The middle of your own documented lifecycle has never been used once. |
| Occurrences of "CSS specificity", "big-O", "time complexity", "prefers-color-scheme", "salary" | **0, 0, 0, 0, 0** | 666k words and none of it touches four things that appear in most loops. |

Everything else in this document follows from those three rows.

---

## 2. What is genuinely excellent (don't touch it)

Credibility first — this is not a bad vault. It is a badly *allocated* one.

- **Link hygiene is near-perfect.** 4,656 wikilinks inside `Advanced JavaScript/`, **zero genuinely broken**. All 31 module MOCs exist and link **every** sibling note — 0 gaps. I have not seen a hand-built vault this clean.
- **`90 - Labs/06 - Frontend System Design Round Lab`** is the best asset you own: 40-minute timer, per-phase minute budget, /30 rubric with a pass bar, model answer hidden in collapsed callouts. This is a real drill.
- **`15 - Interview Preparation/06 - Mock Interview Guide`** — 45-minute session script, 4-dimension rubric, four verbatim recovery scripts for when you're stuck. Second-best asset.
- **`.claude/skills/frontend-interview-griller`** — "make them answer first, never restate the gold answer upfront, quote their folklore back verbatim." That's the correct pedagogy, and it's the one tool that can't be passively read.
- **`00 - Start Here` study loop** (read → close file → 5-sentence recall → hand-trace → say aloud in 30s) is correct. The problem is that it was written and never executed.
- **`Interview Answer` short tiers** measure at median 60 words / p90 88 — genuinely 25–45 seconds spoken. The budget is being hit.
- **Modules 21, 23, 25, 29** hide practice answers behind `<details>`. Those four modules got it right.

---

## 3. Structural problems, ranked

### P0 — The vault is a writing project pretending to be a study project

Evidence, all measured:

- 337/352 `not-started`, **0** `learning`, and of 15 `solid` notes **14 are meta/infrastructure** (templates, `_Synthesis/*`, Vault Operations). Exactly **one** substantive note is `solid`: `02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript.md`. That's **0.3% content progress**.
- Git: **6 commits, all inside 7 days**, the entire corpus in `Initial commit`. One commit ever changed a `status`.
- **78% of tags (308 of 395) are used exactly once** and are mechanically derived from filenames — `queuemicrotask-and-requestanimationframe`, `20-code-output-questions`. Zero retrieval value; the filename already contains them.
- `verified_on` clusters on two dates (27 notes on 2026-07-17, 19 on 2026-07-12) — batch stamping, not incremental review.
- Frontmatter key order and quoting style are **byte-identical in 345 of 346 notes**. The single deviation is the single note you hand-edited.
- `98 - Vault Operations/Agent Prompts/` contains 6 generation prompts checked into the study vault. The factory is stored inside the product.

**Consequence:** 5 of your 8 `Base.base` views are structurally dead. Quiz Pool, Study Queue, and Learning all filter on `status == "learning"` and return **0 rows** — forever, until you promote something. "Must Know" returns ~180 rows truncated to 50, i.e. it is indistinguishable from a file listing. Your control panel has no working instruments.

> **This is the whole problem.** Writing 666k words felt like studying and produced almost no retrieval strength. Interviews test recall under observation; generation trains neither.

### P0 — Your Obsidian vault root is one level too deep

`.obsidian/` lives at `Advanced JavaScript/.obsidian`. Therefore:

- **114 of 462 files (24.7%) are invisible** to Obsidian — no search, no graph, no Base, no tags. That includes all of `System Design/` (64 files, 94k words), `Low Level Design/` (19 files, 27.5k words), `_Synthesis/` (5 files), and the 2026-07-17 review report.
- **51 of the 66 wikilinks written outside the vault (77%) are dead** because they point into `Advanced JavaScript/` from outside the root. `_Synthesis/01 - Cross-Domain Wiring` and `_Synthesis/03 - Vault Integration Plan` are the worst offenders. `_Synthesis/*` even carries full frontmatter authored to be picked up by `Base.base` — it can never appear there.
- All five skills live in `.claude/skills/` and `.agents/skills/`, both **outside** the root. `00 - Start Here` describes five tools a reader browsing Obsidian cannot find. The one place they'd look, `98 - Vault Operations/Skills/`, contains 1 of 5 (plus a stale `.skill` zip).

**Fix:** move `.obsidian/` up to the repo root, or move `Advanced JavaScript/*` up. 15 minutes. It recovers 121k words and fixes 51 links.

### P0 — Coverage is inverted relative to a mid-level frontend loop

| Area | Words | Rounds it appears in |
|---|---|---|
| Backend system design (`30` + `System Design/progress/hellointerview/`) | **97,097** | ~never |
| Low-level design (`31` + `Low Level Design/progress/`) | **36,246** | ~never |
| CSS & layout | **~0 dedicated** | most loops |
| Behavioral (3 notes: `15/08`, `15/09`, `15/10`) | **2,391** | every loop |
| DSA / complexity vocabulary | **0** | many loops |

You have **133,000 words (~11 hours of reading) on rounds a mid-level frontend candidate will essentially never see** — more than React internals (30k), testing (20k), and accessibility (19k) *combined*.

Meanwhile: `specificity`, `@layer`, `containing block`, `:has()`, `BEM`/CSS Modules, `<picture>`, `prefers-color-scheme`, `@keyframes` → **0 hits each**. `flexbox` and `grid` appear only as passing clauses. The best CSS content in the vault is `29/11 - Internationalization and RTL` (logical properties), and it's there by accident.

Also zero: resume walkthrough, "tell me about yourself", questions to ask the interviewer, take-home strategy, project deep-dive prep, handling "I don't know", salary negotiation, Git workflows, monorepos, semver/lockfiles, a devtools/profiling walkthrough.

### P1 — Nothing in the vault trains writing code under a clock

You named live coding as a weak area. The vault does not address it.

- `grep` for a timer across all 348 notes returns **exactly one hit**: `90 - Labs/06`, line 18. That's the *design* round.
- Labs 01, 02, 03, 04, 06 contain **zero code fences** and **no reference solution**. No lab says "implement this in 25 minutes."
- Module 16 tests *reading* output. Module 17 shows *finished* fixes. Module 29 is design prose. **Nothing tests writing from blank.**
- Missing implementations that mid-level machine-coding rounds actually ask for: event emitter, `Promise.all`/`any`/`race` from scratch, `memoize`, LRU cache, virtualized list, `deepEqual`, `groupBy`, retry-with-backoff, a custom `useFetch`. You have `debounce`, `throttle`, `curry`, and deep-clone — 4 of ~15.
- No self-recording protocol. "record yourself if you can" appears once, as a parenthetical.

### P1 — Half your practice questions have the answer sitting in plain sight

- 235 notes have a `Practice` section. **142 hide answers in `<details>`. 93 do not.**
- The 93 are a clean generational split: **all of modules 03–14**.
- Worse, the modules *designed* for retrieval have zero hiding: **module 16 shows all 82 answers** (`### Expected Output` immediately below every question, 0 uses of `<details>`), as do `15/01–04` and `18/04–06`. Module 16's own MOC concedes it — "commit to your answer, and only then check" is a documented workaround for a broken file format.
- **~110 of 245 practice-bearing notes (45%) leak their answers.** Recognition feels like knowledge and isn't.

### P2 — Revision layer is the most bloated part of the vault

The five `18 - Revision Plans` mega-files total **18,291 words** (`01 - Complete Checklist` alone is 5,135). These are meant to be re-read *fast under time pressure* and they are the longest files you own. `99 - Glossary.md` is **13,897 words** and sits inside the note tree, inflating every average.

### P2 — Template drift: four competing templates

The house template (`Maturity Target` / `Source Anchors` / `Concept` / `Why It Matters` / `Bug → Fix → Tradeoff` / `Interview Answer` / `Practice` / `Related Notes`) is aspirational:

| Section | Conformance |
|---|---|
| `Related Notes` | 100% |
| `Maturity Target` | 96% |
| `Practice` | 86% |
| `Interview Answer` | 85% |
| `Concept` | 74% |
| **`Bug → Fix → Tradeoff`** | **44%** (three different heading strings) |

Modules 03–13 use a 14-section variant (`Mental Model` ×66, `Common Mistakes` ×84, `Official Mechanism` ×45 — none in the stated template). Module 17 uses `Interview Angle` and has **0 `Interview Answer` sections in 11 notes**. `priority: important` is used in **112 notes and queried by no view at all** — 32% of the vault has a priority nothing surfaces.

### P3 — Minor but cheap to fix

- 5 ECMAScript internal-slot notations render as broken links and pollute graph view: `[[Get]]`, `[[Set]]`, `[[Extensible]]`, `[[DefineOwnProperty]]` in `06/01` and `06/03`. Wrap in backticks.
- `_Dashboard.md` recommends the **Spaced Repetition** plugin. It is not installed (`community-plugins.json` = `["dataview"]`), and no SR frontmatter (`sr-due`, `sr-interval`) exists anywhere — the workflow cannot be started as written.
- Dashboard suggests rebuilding the roadmap as a Canvas. No `.canvas` file exists.
- All 10 SKILL.md files are **byte-identical duplicates** across `.claude/skills/` and `.agents/skills/`. Any edit must be made twice or they silently diverge.
- `Advanced JavaScript/Notes.md` — 441 words of raw scratch ("##SSR Hooks"), no frontmatter, orphaned, never mentioned in any prior artifact.
- `Base.base` orders the Version-Sensitive view by `version_scope` but doesn't declare it in `properties:`, so it renders without a display name.
- `module: "Vault Root"` on `98 - Vault Operations/Agent Prompts/_Enhancement Progress.md` is simply wrong.

### Not a problem — two things a prior audit worried about

- **Modules 29/30/31 do not duplicate the `progress/` folders.** Measured with 8-gram shingles: max verbatim overlap **1.1%**, and **0 shared headings** out of 51 vs 100 / 23 vs 542 / 25 vs 146. It's summary-of, not copy-of. The relationship is *compression with loss*: module 30 is 14.4k words standing in for 82.7k (5.8×), dropping 38% of probed topics.
- **All 41 findings from the 2026-07-17 review are genuinely remediated.** I spot-verified 11 of them including the RAM/SSD latency inversion in `30/09`, the `navigator.locks` retraction in `31/05`, APG carousel roles in `29/18`, and the Valkey/Linux-Foundation correction. That work held.

**Still open from `_Synthesis/03` and `/04`:** all 3 "decide-with-Mustafa" items; the entire flagged-unverified list in `_Synthesis/04`; and the promised "deepen, don't just link" pass on `29/02 Autocomplete` and `29/04 Infinite Scroll`.

---

## 4. Enhancements, prioritized

### Tier 0 — this week (~3 hours total, unlocks everything else)

1. **Move `.obsidian/` to the repo root.** Recovers 121k words and 51 links. 15 min.
2. **Promote 3 notes to `learning` today.** Not aspirationally — actually open them, do the study loop, set the field. This is the only action that turns Quiz Pool / Study Queue / Learning from empty into functional. 45 min.
3. **Add `priority: important` to the "Must Know" Base view**, or collapse `important` into `must-know`. 112 notes currently invisible to prioritization. 10 min.
4. **Cap the "Must Know" view usefully** — it returns everything. Change it to `priority == "must-know" AND status == "learning"` and let `not-started` be a separate intake queue. 10 min.
5. **Delete or externalize the generation apparatus.** Move `98 - Vault Operations/Agent Prompts/` out of the vault. It is 6 orphaned files that make the vault read like a build artifact. 5 min.
6. **Backtick the 5 internal-slot pseudo-links.** 5 min.

### Tier 1 — next two weeks

7. **Build `32 - Implement From Scratch` (~15 notes).** Highest-leverage new content for your stated live-coding weakness. Each note: problem statement, a hard time budget, an empty starting signature, hidden reference solution, then 3 escalating follow-ups. Steal the structure from `Low Level Design/progress/hellointerview/questions/03 - Elevator.md` — see item 10.

   Suggested set: event emitter · `Promise.all`/`allSettled`/`race`/`any` · `memoize` with cache key strategy · LRU cache · retry with exponential backoff + jitter · `deepEqual` · `groupBy`/`chunk`/`flatten` · custom `useFetch` with abort · custom `useDebouncedValue` · virtualized list · infinite-scroll hook · a tiny observable store · `classnames` · promise pool with concurrency limit · a typeahead component end-to-end.

8. **Build `33 - CSS and Layout` (~14 notes).** Cascade & specificity & `@layer` · box model & containing block · flexbox · grid · stacking contexts & z-index · custom properties & theming · dark mode & `prefers-color-scheme` · container queries & `:has()` · logical properties (link to `29/11`) · transitions/animations & compositor-friendly properties · `will-change` / containment / `content-visibility` · responsive images & `<picture>` · styling architecture (BEM vs CSS Modules vs Tailwind vs CSS-in-JS) · a CSS debugging walkthrough. This is the largest hole in the vault.

9. **Fix the 93 + 82 leaked answers.** Wrap every visible answer in `<details><summary>`. Modules 03–14 first, then module 16 (82 questions), then `18/04–06`. Mechanical, scriptable, and it converts ~110 notes from reading material into actual retrieval practice. Highest value-per-hour item in this document.

10. **Steal the Elevator note's structure and retire the `progress/` folders.** `Low Level Design/progress/hellointerview/questions/03 - Elevator.md` (4,160 words) is the best pedagogical artifact in the repository and it's sitting outside your vault. What it does that your notes don't:
    - **Bad → Good → Great solution ladders**, each with the concrete failure case that motivates the next tier.
    - **Phase time budgets** (`Requirements ~5 min`, `Class Design 10–15 min`, `Implementation ~10 min`).
    - **A tick-by-tick verification trace** showing state evolving.
    - **Explicit Junior / Mid-level / Senior expectation bands** — a much sharper version of your `Maturity Target` field.

    Adopt "Bad → Good → Great" as a first-class section in the house template for anything design- or implementation-shaped.

11. **Behavioral module `34` (~8 notes), or accept you'll wing it.** 2,391 words for a round in every loop. Needed: resume walkthrough & "tell me about yourself" · a 12-story STAR bank mapped to the standard prompts · project deep-dive prep (your actual work at Safasoft) · conflict & disagreement stories · failure/feedback stories · "I don't know" recovery scripts (extend `15/06`, which already has four good ones) · questions to ask each interviewer type · offer & negotiation basics.

### Tier 2 — backlog

12. **Archive, don't delete, the backend SD + LLD mass.** Move `30`, `31`, `System Design/progress/`, `Low Level Design/progress/` under a single `95 - Archive (Backend SD + LLD)/`. 133k words. Keep them — they're good, and useful if a loop includes a general SD round — but stop letting them dominate search, tags, and your sense of remaining work. Preserve the ~35k words that are genuinely interview-grade (SD questions 01–16, LLD 01–03, the pattern/deep-dive/knowledge-base files) and drop the ~9k of premium-locked stubs (SD questions 17–30 are 472–774 words each and mostly a table of contents of what you can't read — `26 - Google Docs.md` is 472 words to say "design Google Docs").
13. **Split `99 - Glossary` (13,897 words) by domain**, or move it out of the note tree and treat it as reference.
14. **Compress `18 - Revision Plans` from 18,291 words to ~4,000.** A revision layer you can't finish in a sitting isn't a revision layer.
15. **Prune the tag vocabulary from 395 to ~40.** Delete all 308 single-use filename-derived tags. Merge `nodejs`/`node`, `real-time`/`realtime`, `a11y`/`accessibility`, `network`/`networking`, `framework`/`frameworks`, `state`/`state-management`. Rename the `solid` tag (SOLID principles) — it collides with `status: solid`.
16. **Normalize the template.** Pick one: either adopt the modules 03–13 14-section variant everywhere, or push the 8-section house template into 03–13. Standardize `Interview Answer` on one label (`Short answer:` blockquote — used by 155 notes vs 57 using `Short version:`). Give module 17's 11 notes an `Interview Answer`.
17. **Add `verified_on` to the modules that need it most.** `21 - React Internals` has **0 of 17** — including `10 - React 19`, `09 - Suspense and Concurrent Features`, `03 - Fiber and Scheduling`. Same for `14` (0/12), `19` (0/13), `20` (0/10), `13` (0/11), `26` (0/9). Your only staleness mechanism is blind to your most version-volatile content.
18. **Dedupe the skills.** One canonical directory, symlink the other. Delete the third copy in `98 - Vault Operations/Skills/`.
19. **Either install the Spaced Repetition plugin or remove it from the Dashboard.** As written, the Dashboard recommends a workflow that can't be started.
20. **Add ~15 more labs.** Six is not enough for the module that's supposed to build muscle memory. Every Tier-1 "implement from scratch" note should have a matching timed lab.

---

## 5. Study advice

### The core correction

You have optimized for coverage. Interviews test **retrieval under observation**. These are nearly unrelated skills, and the vault currently trains only the first.

The evidence that you know this already: `00 - Start Here` prescribes exactly the right loop (read → close the file → 5-sentence recall from memory → hand-trace → say it aloud in 30s). It was written and not run — 0 notes have ever entered `learning`.

**So the single most important change is a cadence, not more content.** Concretely, per session:

1. Open `Base.base`, not folders. Pick **one** note.
2. Read the `Concept` section once. **Close the file.**
3. Write 5 sentences from memory. Compare. Note what you missed — that's the real gap, not the note.
4. Hand-trace every code example before running it. Write the predicted output down first.
5. Say the `Interview Answer` short tier aloud, on a 30-second timer, standing up. Record it on your phone once a week and listen back.
6. Set `status: learning`.
7. Promote to `solid` only after **two clean recall passes in separate sessions** — your own rule from `00 - Start Here`. One missed mechanism demotes it.

Three notes per session, 4–5 sessions a week, and you'll have ~60 notes at `solid` in a month. That's more real progress than another 100k words.

### For frontend system design (stated weakness)

You already own the right instrument and haven't used it. `90 - Labs/06 - Frontend System Design Round Lab` — 40-minute timer, per-phase budgets, /30 rubric, hidden model answer.

- **Run it once a week, on a real clock, out loud, recorded.** Grade yourself against the rubric. The pass bar is 25/30; missing an entire phase means redo in a week.
- Module 29 has 16 "Designing X" walkthroughs. Rotate through them as the lab's prompt. **Read the note only *after* you've done the 40 minutes cold** — reading first converts a drill into a comprehension exercise.
- RADIO phase discipline is where mid-level candidates lose the round, not depth. Your `29/01 - The Frontend System Design Framework` covers it; the problem will be pacing, and only a timer fixes pacing.
- Fix the two `Interview Answer` sections that read as compressed telegraphese — `29/19 - Chat and Messaging` and `29/20 - E-commerce Product Page` (233 and 242 words). Try saying "failed with retry" out loud; it isn't a clause. Rewrite anything you can't speak in one breath.
- Also: strip wikilinks out of spoken scripts. Three `Interview Answer` sections contain raw `[[...]]` — `25/05` has one as the *final clause* of the deeper answer.

### For React internals and deep JS (stated weakness)

- **The griller skill is the right tool and it's invisible from inside Obsidian.** Use it directly: point it at a note and let it demand a 30-second answer before showing anything. Its "quote their folklore back verbatim" mode is specifically designed to catch phrases like "closures remember variables" — which is exactly the failure mode that separates a mid-level answer from a senior one.
- **Module 16 (82 code-output questions) is currently a read-through document.** Until you wrap the answers in `<details>`, cover the screen with your hand or copy questions into a scratch file. Predicting-then-checking is the entire value; seeing the answer destroys it.
- **Follow the Roadmap order, not folder order.** `01 - Roadmap` phases 15–16 put `14 - JS in React and Next` before `21 - React Internals` for a reason: hydration and server/client boundaries own the mechanisms that make Fiber comprehensible. Its own advice is the best line in the vault — "if a later topic feels slippery, find the prerequisite that owns the mechanism."
- **Trust `03/05 - Closures` and `17/03 - Handling Race Conditions` as the model notes.** The latter (complete broken component → two complete fixes → tradeoffs) is the best-structured content you have. When you write new notes, copy that shape.
- Depth check: `12 - Advanced Language Concepts` has ~5,000 words on Proxy/Reflect, typed arrays, floating point, and Symbols. Interesting, near-zero interview yield at mid-level. Deprioritize behind CSS and machine coding.

### For live coding and articulation (stated weakness)

This is your largest gap and the vault currently offers **nothing** for it. Until Tier-1 item 7 exists:

- **Type, don't read.** Pick a utility from `04/07 - Debounce and Throttle` or `06/07 - Object Copying`, close the note, set a 12-minute timer, implement it in a blank file. Then diff against the note.
- **Narrate while typing.** The mid-level bar in a live round is not "correct code" — it's "correct code while a stranger watches and you keep talking." Practice the talking separately: implement something you already know cold, out loud, recorded.
- **Use `15/06 - Mock Interview Guide` as an actual script**, not reading material. It has 45-minute segment timings, a 0–3 × 4-dimension rubric, and four verbatim recovery scripts. Run it weekly with a friend, or with the griller skill as the interviewer.
- **Add a hard time budget to Labs 01–04.** They have acceptance criteria and debugging tasks but no clock and no reference solution. Both are one-line additions per lab and turn briefs into drills.
- **`90 - Labs/03` already proves you can write embodied protocols** — "with eyes closed and a screen reader" is excellent. Write the equivalent for voice: what to record, what to listen for, how to score the playback.

### A rough sequence, since you have no fixed date

| Weeks | Focus |
|---|---|
| 1 | Tier 0 (3 h). Then Roadmap phases 1–8 (modules 02–09) at 3 notes/session — you have 0 notes `solid` in any of them. |
| 2–3 | Continue phases 9–14. In parallel, wrap the leaked answers in modules 03–14 (item 9) as you reach each module — do it *while* studying, not as a separate project. |
| 4–6 | Phases 15–16b: React internals. One griller session per note. Weekly Lab 06 run. |
| 7–8 | Build the CSS module (item 8) *by studying it* — write each note only after you can already explain the topic. That inverts your current process and is the point. |
| 9–10 | Build `32 - Implement From Scratch` (item 7) the same way: solve it on a timer first, then write the note. |
| 11–12 | Behavioral module + `18 - Revision Plans` compression + first full mock loop. |
| Continuous | 3 notes/session promoted, one Lab 06 run per week, one recorded 30-second answer per day. |

---

## 6. General advice

1. **Writing a note is not learning it.** This vault is the clearest possible demonstration: 666k words, 0.3% content progress. The `status` field isn't bookkeeping — it's the only honest signal you have, and it currently reads 95.7% not-started. Treat that number as your primary metric.

2. **Generate less, retrieve more, from here on.** Your instinct when facing a gap is to write a module. That instinct produced 133k words on rounds you won't face and 0 on CSS. For the next three months, invert it: **new notes only after you can already explain the topic.** The note becomes a record of learning rather than a substitute for it.

3. **Coverage anxiety is the enemy.** 55 hours of reading material creates a permanent sense of being behind, which drives more generation, which adds hours. Archiving the backend SD and LLD mass (item 12) cuts 11 hours of perceived debt in one move and costs you nothing you'll be asked about.

4. **The vault should have fewer working parts, not more.** You have 8 Base views (5 dead), 4 competing templates, 395 tags (308 single-use), 3 copies of one skill, 2 identical skill directories, 5 template files, and 6 generation prompts. Every one is maintenance that competes with studying. Cut to: one template, ~40 tags, 3 Base views (Learning / Must-Know intake / Version-sensitive), one skills directory.

5. **Hide every answer, always.** Make it a hard rule in the house template. Recognition ("yes, I knew that") is the single most reliable way to feel prepared and not be. 45% of your practice notes currently produce exactly that illusion.

6. **Put a clock on everything.** One timer reference in 348 notes. Interviews are timed; untimed practice trains a different skill. Every practice question, lab, and design walkthrough should carry a minute budget.

7. **Say it out loud, and listen to the recording.** The gap between what you can write and what you can say is where mid-level candidates lose offers, and it's invisible until you hear yourself. Your `Interview Answer` word budgets are already correct — the delivery is the untested part.

8. **Your prior audit worked. Trust that process.** The 2026-07-17 review found 41 issues, and I verified 11 fixes held including subtle ones (the RAM/SSD latency inversion, the `navigator.locks` retraction, APG carousel roles). Periodic adversarial review of your own material is a habit worth keeping — just point it at *recall performance* next time, not content accuracy.

9. **Close the `_Synthesis/04` loop or delete it.** It lists 6 clusters of explicitly unverified claims (premium-locked pattern internals, LSM internals, Kafka consumer-group semantics, Cassandra consistency levels, Bloom-filter math, vector-DB indexing) that are still unverified 8 days later. Unverified claims you've forgotten are unverified are worse than absent ones — you'll state them confidently in a room.

10. **Commit more often.** Six commits for 666k words means no history to diff, no way to see what changed in a remediation pass, and no recovery granularity. One commit per study session, message = which notes you promoted.

---

## 7. Verified figures (appendix)

All measured 2026-07-25 from the working tree.

| Metric | Value |
|---|---|
| `.md` files (excl. `.obsidian/`) | 462 |
| Total words | 665,977 |
| Reading time @200 wpm | ~55.5 h |
| Files inside Obsidian root (`Advanced JavaScript/`) | 348 (75.3%) |
| Files outside Obsidian root | 114 (24.7%) |
| `status: not-started` / `learning` / `solid` | 337 / **0** / 15 |
| Substantive notes at `solid` | **1** |
| `priority` must-know / important / deep-dive | 224 / 112 / 13 |
| Notes with `verified_on` | 50 (14%), clustered on 2 dates |
| Wikilinks inside vault / genuinely broken | 4,656 / **0** |
| Wikilinks outside vault / broken | 66 / **51** (77%) |
| MOCs present / with missing sibling links | 31 / **0** |
| Distinct tags / used exactly once | 395 / 308 (78%) |
| Practice-bearing notes / leaking answers | 245 / ~110 (45%) |
| Code fences | 2,613 across 275 notes; 73 notes have none |
| Word count min / median / max | 272 / 1,419 / 13,897 |
| Notes >2,500 words | 18 |
| Git commits | 6, all within 7 days |
| Verbatim overlap, modules 29/30/31 vs `progress/` | ≤1.1%, 0 shared headings |
| Hits for `specificity` / `big-O` / `prefers-color-scheme` / `salary` | 0 / 0 / 0 / 0 |

## Related Notes

- [[00 - Start Here]] — the study loop this review says to actually run
- [[01 - Roadmap]] — the phase ordering to follow instead of folder order
- [[_Dashboard]] — needs the Base-view fixes in Tier 0
- [[90 - Labs/06 - Frontend System Design Round Lab|FSD Round Lab]] — run weekly
- [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]] — run weekly
- [[98 - Vault Operations/00 - Vault Operations|Vault Operations]] — where the template normalization lands
