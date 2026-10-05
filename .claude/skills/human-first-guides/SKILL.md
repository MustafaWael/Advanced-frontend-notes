---
name: "human-first-guides"
description: "Use when writing, upgrading or reviewing a guide or concept note, or when one has gaps or is hard to follow — terms explained first, one spine, connected ideas, examples that tie it together."
---

# Human-First Guides

A common way for technical guides to fail their readers: they are complete but not followable. Every fact is there and mostly correct, but it is packed the way an expert stores knowledge (dense terms, lists, tables), and the relationships between ideas are left for the reader to work out. Someone who already knows the topic can unpack that. A learner can't. They stall at the first unexplained word, collect facts that never connect, and re-read without the picture forming.

The cause has a name: the curse of knowledge, and its teaching cousin, the expert blind spot. Once you know a topic, you can no longer see which words a newcomer is missing. Expert writers and AI models both fall into it, which is why the rules below check the page instead of trusting the writer's sense that it's clear.

This skill writes for a different reader: smart, new to this topic, reading top to bottom, and never needing to open another tab to understand a sentence.

**The goal.** When the reader finishes, they can explain the idea in plain words, predict what a piece of code will do because of it, recognize it in a situation the guide never showed, and say how it connects to the ideas around it.

**The test for every page.** Could that reader get from the first line to the last without stopping to ask "what is X?" or "why is this here?"

## Words this skill uses

- **Guide**: any explanatory document. In the vault, every concept note is a guide, and the same rules apply.
- **Term**: any word a smart newcomer to the topic wouldn't know or would misread. That includes jargon, spec names, abbreviations, and everyday words used in a technical sense (*binding*, *context*, *record*).
- **Table of names**: this skill's plain name for what the ECMAScript spec calls an Environment Record. It holds the names declared in one scope and their values, plus a link to the table of the scope around it.
- **Hub guide**: a guide whose smaller concepts each have a guide of their own. Execution Context is one, because lexical environment, realm and `this` each have their own notes.
- **First screen**: roughly the first 40 lines the reader sees.
- **Long guide**: more than about 300 lines.
- **Teaching part and study tools**: the study tools are the recap, interview answer, practice, checklist and related-notes list. Everything else is the teaching part, including Common Mistakes, which is where non-examples live.

## How the rules fit together

The nine rules do three jobs. Rules 1 to 3 make every sentence land: no unexplained words, a short primer for each smaller concept, and the plain idea before the official name. Rules 4 to 7, together with rule 9, make the sentences add up to connected ideas: one spine, "because" lines instead of topic lists, the confusing pairs named, and links between guides. Rule 8 removes the noise that gets in the way of both jobs.

Rule 9 does the most work. The spine and the because-lines describe connections, and examples are where the reader actually sees them happen. If you remember one rule, remember rule 9.

## Modes

- **Write**: a new guide. Follow "Writing a new guide".
- **Upgrade**: an existing guide that has gaps or is hard to follow. Follow "Upgrading an existing guide". It always starts with a diagnosis and a plan the author approves. It never starts by rewriting.
- **Review**: upgrade steps 1 to 4 only, meaning a diagnosis and a plan with nothing changed. Deliver it in chat, or as a file if it's long.

Not every guide needs every rule at full strength. "Scale it to the guide" says how much to apply, and every plan states its cost.

## Job 1: make every sentence land

### Rule 1. Explain every term before you use it

Each unexplained term is a hole the reader falls into. It's worse when a definition is made of other unexplained words, a dictionary loop: the reader has to hold several unknowns at once, and none of them can land. Learning science calls this high element interactivity without pre-training.

- Before writing, build the **term ledger**: every term the guide needs, each marked as one the reader already owns, one that needs a primer (rule 2), or the one this guide teaches.
- Track each sense of a word separately. "Binding" (a name tied to a value) and "`this` binding" are two entries, not one.
- A term counts as explained only when the explanation uses words the reader already owns. A definition made of other unexplained terms doesn't count. A bare link doesn't count. A primer with a link does.
- Hunt the small words hiding inside definitions: *binding, record, intrinsic, continuation, receiver*. They slip through because they feel ordinary to the writer.
- If a term has to appear before its explanation, say so on the spot: "the realm (explained just below)".
- Spell out abbreviations at first use: TDZ (temporal dead zone).
- Watch the density. A rule of thumb, not a law: no more than two new terms per paragraph. When a sentence needs more, split it or move the extras into primers.

> Fails: "Realm — the set of intrinsics and global object." *Intrinsics* is never explained, and the definition arrives long after the word was first used.

### Rule 2. Prime smaller concepts by their job inside the big one

Big concepts are built from smaller ones. To follow an execution context, the reader needs a few smaller ideas: a table of names, the realm, and how `this` is found. They need just enough of each to understand the big concept. Each smaller concept's full story would bury the big one.

- Before the guide starts using the smaller concepts' names, add a short **Words you need first** block. For a single term, a one-line primer where it first appears is enough. The block comes after the opening (rule 3), not before it.
- Each primer gets at most three sentences in plain words, a tiny example if it helps, then a link to that concept's own guide.
- Give each primer the same shape: the name, the question it answers, then its one job in plain words. Phrasing the job as a question ties the primer to a question-set spine (rule 4) and gives the reader a cue to recall it by.
- Write it from the big concept's angle: what job does this smaller concept do *inside the big one*? In an execution-context guide, a realm only needs "which `Array` this code sees". Agents and job queues belong to the realm's own guide.
- A primer repeats a little of another guide, so check it against that guide. If either one is corrected later, fix the other too.

> **Realm** — *answers: which `Array`, and which global object, does this code use?* One full set of built-ins (`Array`, `Object`, `Promise`…) plus a global object; each window, iframe and worker has its own. So an array you reach directly inside a same-origin iframe fails `instanceof Array` in the parent page (one sent with `postMessage` is copied into the receiver's realm, so it passes). → Full story: Realm, Agent and Job Queue.

### Rule 3. Plain idea first, official name last

A name only sticks when there is an idea for it to stick to. Leading with the formal term asks the reader to memorize a label for nothing. Go concrete, then plain idea, then official name. Learning science calls this order concreteness fading.

- Open with something the reader already understands: a question, a situation they've been in, or a few lines of code.
- Or open with the problem the concept solves: what would break without it? "`factorial(3)` calls `factorial(2)`, and both need their own `n` at the same time, so every call needs its own record." A concept introduced as the answer to a problem has a reason to exist in the reader's head.
- Explain the idea in plain words.
- Then attach the name: "The spec calls this record an *execution context*."
- Avoid "X is [formal definition]. In simpler words, …". That order makes the reader decode jargon first and only then get the plain version.

> **Before:** "An execution context is the specification model for a piece of code currently being evaluated. It tracks the code's lexical environment, variable environment, `this` binding, realm…"
>
> **After:** To run `return this.format(Array.from(items));`, JavaScript must already know four things: which `items` you mean, what `this` is right now, which `Array` to use (an iframe has its own), and where to go back when the function returns. For each running script, module or function call, it keeps a record that holds those answers or points to where they're kept, and it stacks the records so it always knows where to go back. The spec calls that record an **execution context**. *(Teaching model of the spec.)*

## Job 2: make the ideas connect

Rules 1 to 3 make each sentence understandable. Rules 4 to 7 make the sentences add up.

### Rule 4. Give the guide one spine, and make every section advance it

A guide that moves from heading to heading hands the reader a stack of separate boxes. Ideas connect when every section visibly hangs on one central thread that the reader meets early. Learning science calls this an advance organizer.

- Choose the spine before writing. Two kinds work well. A **question set**: "four questions every running piece of code must answer". A **life story**: the concept from creation to its end.
- When upgrading, look for a spine already in the guide; a good one is often buried in the middle. Use it if it works, and propose a new one only if none does.
- State the spine on the first screen.
- Open every section with one bridge sentence: where we are on the spine, and how this section follows from the last one.
- Close each stage of the spine with a one-line checkpoint, a question the reader answers before reading on. A checkpoint looks back.
- Where the next section answers a question the reader doesn't have yet, end with that question instead, so they arrive wanting the answer. Learning science calls this a prequestion. A forward question looks ahead. Use whichever the reader needs at that point, and vary the wording. The same "Now that we understand X…" line on every section is template residue (rule 8).
- When you show an example, say which part of the spine it exercises.
- Put the study tools after the teaching part. If a template fixes the headings, keep them and fit the spine inside them (the vault section shows how).

> A life-story spine for execution context, in the order the spec runs a function call: a context is **created and pushed** onto the stack (→ call stack), **sets up its names** before running any line (→ hoisting, TDZ), **runs** and looks names up the chain (→ scope chain, `this`), may **pause and resume** (`await`, `yield`), and may **leave its table of names alive** after it's popped (→ closures).

### Rule 5. Turn topic lists into "because" lines

A list of names isn't a connection. The understanding lives in the verb ("a closure *keeps* the table alive"), and that verb is exactly what a bare bullet drops. Learning science calls the added "because" elaboration.

- Every bullet that names a related topic becomes: **topic — because [a mechanism from this guide] [does what]**, plus a link to the topic's guide.
- If you can't write the because, the topic doesn't belong in the list yet.
- End at something the reader can observe: an output, an error message, a bug. "Because X, you see Y" is the shape to aim for.
- Never claim a connection you don't show, as in "once you get this, many topics stop feeling separate".

> **Before:** "Scope chains and closures."
> **After:** **Scope chain and closures** — name lookup starts at the current table of names and follows the outer links. A function keeps a link to the table it was created in, so that table can outlive the call. That's a closure.

### Rule 6. Name the confusing pairs out loud

Readers silently merge terms that sound alike and keep apart terms that are really the same thing. Either way the mental model breaks, and the reader can't tell it happened.

In a hub guide, or wherever two names collide, add a short **Don't mix these up** box. Look for four kinds of pair:

- **Same thing, two names.** The execution context stack (spec name) and the call stack (everyday name).
- **Different things, near-identical names.** In V8, "context" means two other things: the embedder's `v8::Context` (roughly a realm; Node's `vm.createContext` makes one) and the heap objects that hold variables captured by closures. Neither is an execution context. *(Named implementation: V8 12.4, as shipped in Node 22.)*
- **Layered names.** The running context's LexicalEnvironment component points to a table of names, and that table links to the ones outside it.
- **Two things that both get called "the environment".** A function's `[[Environment]]` internal slot is the table that a closure keeps. The running context's LexicalEnvironment is where lookup starts right now.

When an accurate model and a simplified one differ, say which one you're using. The accurate one is often the more connected one. In the current spec, `this` is stored in tables of names, not on the context itself, and an arrow function's own table has no `this`. So the outward walk passes through the arrow to the surrounding code's `this`, and that is the whole reason arrows inherit `this`. The older ES5 layout, which kept `this` on the context, hides that link.

In deep topics, keep three layers apart and visit them in order: the **teaching model** (the intuition), the **specification** (what every engine must guarantee), and the **implementation** (what one engine does, with its version). Label each one. An engine detail must never pose as a guarantee, and a teaching model must never pose as the spec. A V8 aside placed inside a spec explanation is an asset when it's labeled as the implementation layer, and a trap when it isn't.

### Rule 7. Connect guides to each other, not only ideas inside a guide

Guides in a series are read one at a time, so each one has to carry its own links to its neighbors. A list of related notes at the bottom doesn't help a reader stuck in the middle of a paragraph.

- Open with **Where this fits**: one or two sentences on what the reader brings from the previous guide and what this one adds.
- End with **What this unlocks**: the guides that build on this one, one line each saying what they take from it. If the guide already has a related-notes list, annotate that list rather than adding a second one.
- Put links inline, at the sentence where the question comes up.
- Reuse a neighbor's example when you can, and say so: "the `render(items)` function from the previous note".
- Check both directions. Every concept this guide primes should link to that concept's home.

## Job 3: remove the noise

### Rule 8. Cut the AI tells

These patterns make text look complete while carrying nothing. Readers learn to skim them, and then they skim the sentences that matter too.

- Definitions built from other unexplained terms.
- Hedges that carry nothing: "in many cases", "where applicable", "various", or "behavior" used as a noun with no content.
- Importance or connection claimed but not shown: "this is crucial", "everything becomes clear".
- Evaluative filler: "this is exactly what separates a senior answer from a junior one".
- Template residue: placeholder phrases pasted literally ("This works/fails because…", "Example 1", leftover ALL-CAPS slots).
- Lists and tables where the relationships are the point.
- Every paragraph the same length, every section the same shape.
- Intensifiers that add nothing: *literally, simply, actually*.
- Mechanical transitions: the same opener or closer stamped on every section.

When writing, rewrite or delete these on sight. When upgrading someone else's guide, list each one with its line number in the diagnosis and propose the fix; the author decides.

Write the way a good teacher talks at a whiteboard: "you", short sentences, active verbs, one idea per paragraph. Rule of thumb: every sentence must **explain, show, or connect**. If it does none of these, cut it.

## The connective tissue: examples

### Rule 9. Use examples and use cases to connect ideas

A definition gets stored as a separate fact. An example makes two ideas meet on the same lines of code, and that is where the connection forms. So examples are the frame of the guide, not decoration at the end. The learning science behind this: worked examples, contrasting cases and analogical comparison.

Rule 9 has three moves.

**A. One example, many concepts: links ideas to each other.**

- Pick one small **running example**, show it on the first screen, and come back to it in every section, each time through a new lens. The reader watches each part of the mechanism act on the same lines, so the parts connect.
- Include at least one **knot example**: a snippet where two or more concepts meet, annotated line by line with which concept explains which line, each linked to its home.

**B. One concept, many examples: makes the concept portable.**

- Show the mechanism in two or three situations that look different on the surface: a loop bug, a stale value in React, a debounce helper.
- Then say out loud what they share: "Same mechanism, three costumes: a function keeps the table it was created in." Comparing cases side by side is what lets the reader spot the mechanism in a situation they've never seen.
- Check that every costume really is the same mechanism. A look-alike with a different cause teaches the wrong lesson.

**C. One example, one change: shows the lever.**

- **Contrast pairs**: two versions that differ in exactly one thing (`var` → `let`, arrow → regular function). State the single change and the different result.
- **Non-examples**: where the concept doesn't apply, or where the intuitive model breaks. For example, entering a block like `{ let x = 1; }` gets a new table of names, not a new execution context.

Where and how to place them:

- **At the point of introduction.** No new idea goes more than a few lines without its first concrete example. Later sections can point back to it.
- **Predict, then trace, then explain.** Ask the reader to predict the output. Show the hidden state step by step in a small table, then explain. Choose columns that show this concept's hidden state. For closures and `this`, that's the stack, where a name is found, and `this`. For async code, it's what's on the stack and what's waiting in the queues. For realms, it's which global object and which `Array`.
- **The use-case ladder** for each main concept: a toy that isolates the mechanism, then the bug you'd actually hit at work, then the fix and what it costs, then how an interviewer asks about it.
- **Start from what the reader already knows.** A situation they've lived through comes before the spec mechanism.
- **End every example of the concept with one plain "What this shows:" sentence** that names the part of the spine it exercises. Write a real sentence, not a template phrase.
- **Minimal, runnable, verified.** Cut what doesn't serve the point, mark the line that matters (`// ← here`), and run the code in the environment you state (browser script, ES module or Node CommonJS), because `this`, globals and the frames on the stack differ between them. Every output in a comment must be one you saw.

The worked example at the end shows all three moves on one concept.

## Scale it to the guide

The rules add words, and words cost study time. Choose a tier, price it, and let the author decide.

- **Tier 1, followable.** Always do this one. It covers terms and their density (rule 1), primers where a term is used without explanation (rule 2), the opening (rule 3), the AI tells (rule 8), and the accuracy pass.
- **Tier 2, connected.** This adds the spine with bridges, checkpoints and forward questions (rule 4), because-lines (rule 5), the confusables box and labeled layers (rule 6), links between guides (rule 7), and from rule 9 an example at each point of introduction plus at least one contrast pair.
- **Tier 3, full examples.** This adds the rest of rule 9: the running example, a knot example, costumes with the shared mechanism named, the use-case ladder and trace tables.

Hub guides are the natural place for tier 3. Narrow guides usually stop at tier 2. Price every plan in words and in study minutes, and recommend the smallest tier that fixes what the diagnosis found. Pay for added words by cutting hedges, unshown claims, list sections the because-lines replace, and summaries of material that has a full home elsewhere (two or three sentences plus a link instead). Measure each section's word count before proposing cuts, because intuition about what is bloated is often wrong.

## Workflow

### Writing a new guide

1. **Find the reader's starting point.** Read the guides this one depends on and the previous guide in the reading order. Note what the reader already owns.
2. **Build the term ledger** (rule 1).
3. **Pick the spine and the running example.** Check whether a neighboring guide already has an example worth extending.
4. **Choose the tier and outline.** Show the spine, each section with its bridge sentence, where each example lands, the primers, the because-lines, the confusables box and the links, along with the cost in words and study minutes. Share the outline and wait for approval before drafting.
5. **Draft.**
6. **Run the cold-reader checklist.**
7. **Accuracy pass.** Run every code sample in its stated environment, check every claim against a primary source, and label claims the way the vault requires.

### Upgrading an existing guide

1. **Read everything relevant.** Read the whole guide. Find its prerequisites from its stated dependencies, or else take the previous guide in the reading order. Find its dependents by searching for guides that link to it. Then read the targets of its links. List anything you couldn't read; don't guess its content.
2. **Diagnose with evidence, not impressions.** Give line numbers and count where you can. "*binding*: used 22 times, never explained" beats "some terms are unclear".
   - *Term ledger*: each term and sense, where it's first used, and where (if anywhere) it's explained.
   - *Spine*: is there one? Is a good one buried? Does each section say which part it advances?
   - *Examples*: for each concept, is there an example where it's introduced, a contrast pair, a knot, costumes, a ladder? Is the best example far from the idea it explains, or hidden in an answer key?
   - *Links*: inline links in the teaching part versus a footer list, and primed concepts with no link to their home.
   - *AI tells* (rule 8).
   - *Accuracy*: run the code; flag outdated models, absolutes with no scope, engine claims with no label, contradictions with linked guides, and examples whose stated environment doesn't match their output.
3. **Name what already works** and keep it as the pattern to copy. An existing step-by-step trace is often the best thing in a guide.
4. **Propose a plan by tier.** Price each change in words, study minutes, and text that must stay in sync. List proposed changes to the author's own wording separately. Wait for approval.
5. **Apply what was approved.** You may fix text you wrote earlier in this session directly. Treat everything else as the author's: reorder and add around it, and change it only as approved.
6. **Sweep corrections.** A claim fixed in the body must also be fixed in the recap, interview answer, practice answers, checklists and glossary.

## Cold-reader checklist

Run this before calling a guide finished. Each line points to its rule, so the rules stay the single source of truth.

- [ ] Tier 1: terms (rule 1), primers (rule 2), opening (rule 3), AI tells (rule 8), code run and claims checked (rule 9, last bullet).
- [ ] Tier 2: spine, bridges, checkpoints and forward questions (rule 4), because-lines (rule 5), confusables and labeled layers (rule 6), links between guides (rule 7), examples at each point of introduction plus at least one contrast pair (rule 9).
- [ ] Tier 3: running example, knot, costumes with the shared mechanism named, ladder and traces (rule 9).
- [ ] Read-aloud test: read the opening and one middle section as if explaining to a friend who is new to the topic. Wherever they'd interrupt with "what's that?" or "so what?", fix it.

## In the Mid-Level Frontend Interview Coach vault

**Read `AGENTS.md` first.** Follow its accuracy contract, its depth calibration (including "ask once" when unsure) and its source hierarchy as written. Don't work from a summary. For behavior that only Node defines, such as CommonJS and its module wrapper, cite the Node.js docs. In the first-principles modules AGENTS.md names, rule 6's three layers carry the depth, and they map onto the vault's three labels.

**Who owns what.**
- `vault-note-authoring` owns the file: the live template in `Advanced JavaScript/98 - Vault Operations/Templates/`, frontmatter, placement and file numbering.
- `add-use-cases` owns the Real-World Use Cases section: its placement, and two to four cases.
- This skill owns teaching quality everywhere in the note.
- If either of those skills can't be loaded, treat the live template as the authority and raise structural changes as questions for the author.

**Template headings stay.** Other skills place their sections by them (`add-use-cases` does), so fit the spine inside them:
- §1 Concept opens with Where this fits, then the hook (the running example or a question), then the plain idea and the official name (this is where the template's "two sentences a junior could repeat" go), then the spine, then Words you need first. Spine stages can be `###` subsections under §1.
- §2 Why It Matters is written as because-lines.
- §3 Real Frontend Example (Bug → Fix → Tradeoff) is the work rung of the use-case ladder.
- New blocks such as Words you need first, Don't mix these up and How to read this note go inside sections or in callouts, never as new numbered sections.
- The order at the top of a note is frontmatter, Maturity Target (with Dependencies), Source Anchors, a `> [!tip] How to read this note` for long notes, then §1.

**Use cases.** Cases stay where `add-use-cases` puts them. Where an idea is introduced, add an example of three lines or fewer that points to the full case, and accept that the two must stay in sync. End each case with a "What this shows:" sentence, and after the cases add one line naming what they share.

**Other conventions.**
- **Bridge from React and Next.js.** The reader already builds React and Next.js features, so a bug they've hit there is the best opening for a runtime mechanism.
- **Labels.** Every engine-level claim is labeled *specification*, *named implementation (engine + version)* or *teaching model*.
- **Links.** Use the path from the `Advanced JavaScript` folder plus an alias, as `vault-note-authoring` shows (`[[03 - Scope and Variables/05 - Closures|Closures]]`), and make sure every link resolves.
- **Status.** Never change a note's `status`. Recommend a change when the author has earned it.
- **Callouts and long notes.** Callouts follow `vault-note-authoring`. Long notes also get a One-Screen Recap table before the Interview Answer.
- **Before handing back edits.** Changed links resolve, corrections are swept, and, if the folder is a git repository, `git diff --check` is clean.

## Worked example: Execution Context

This shows the moves on one concept. Every claim here is a teaching model of the ECMAScript spec unless it's labeled, and the code was run in Node 22 as an ES module. Don't paste this content into notes; copy its moves. If you are upgrading the Execution Context note itself, you may offer pieces of it in the plan.

**Opening** (rule 9, start from what the reader knows): "You've seen a `useEffect` interval keep logging the first render's value, however many times the component re-renders. This note is about the bookkeeping underneath that."

**Running example** (rule 9A), shown on the first screen and reused by every section:

```js
// cart.mjs (an ES module, so strict mode)
const cart = {
  label: 'Cart',
  summarize(prices) {
    var total = 0;                              // var → summarize's table
    for (let i = 0; i < prices.length; i++) {
      total += prices[i];                       // i → a fresh table each pass
    }
    return () => `${this.label}: ${total}`;     // ← keeps summarize's table, borrows its `this`
  },
};

const report = cart.summarize([5, 10]);
console.log(report()); // "Cart: 15"
```

**Trace** (predict, then trace, then explain):

| Moment | Call stack | `total` | `this` inside the arrow |
| --- | --- | --- | --- |
| `summarize` starts, before its first line | module → summarize | already exists in summarize's table, set to `undefined` | — |
| the loop runs | module → summarize | `0`, then `5`, then `15` (each pass's `i` sits in its own table) | — |
| `summarize` returns | module | its context is popped, but its table survives because the arrow still links to it | — |
| `report()` runs | module → arrow | found by walking from the arrow's table out to summarize's table: `15` | the arrow's table has none, so the walk continues outward to summarize's `this`, which is `cart` |

What this shows: names exist before the first line runs (that's hoisting), one call leaves behind a table that a later call still reads (that's the closure), and the arrow finds `this` by the same outward walk it uses for names.

**Forward question** (rule 4), closing that section: "So the arrow borrowed `summarize`'s `this` by walking outward. What happens if the returned function isn't an arrow?" The contrast pair answers it.

**Contrast pair** (rule 9C). Change only the arrow into a regular function:

```js
return function () { return `${this.label}: ${total}`; };
```

Now `report()` is a plain call, so `this` comes from how the function is called. In this module that's `undefined`, and the call throws `TypeError: Cannot read properties of undefined (reading 'label')`. It's the same `TypeError` you get when you pass a class method as a React event handler without binding it, because class bodies are strict too. (In a sloppy browser script, `this` would be the global object and it would print `"undefined: 15"`.)

What this shows: one change moved `this` from where the function was written to how it was called.

**Same mechanism, three costumes** (rule 9B):

- **A loop bug.** `for (var i = 0; i < 3; i++) setTimeout(() => console.log(i));` logs `3, 3, 3`. Every callback links to the same table, which holds the one `i`.
- **A React bug.** An interval created in `useEffect(…, [])` keeps logging the first render's `filters`, because its callback links to render 1's table.
- **A feature.** A `debounce(fn, ms)` helper returns a function that keeps `let timer` in debounce's table. Every call reaches the same timer, so only the last call in a quick burst fires.

What they share: a function keeps the table it was created in, for as long as the function lives. *(Specification model. How much of that table an engine actually keeps is an implementation detail.)*

The primer, because-line and confusables box for this concept appear under rules 2, 5 and 6.