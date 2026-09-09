---
tags: [javascript, start-here]
module: "Vault Root"
priority: must-know
status: not-started
---

# Start Here

This vault is a mature Advanced JavaScript learning system for becoming a strong experienced mid-level frontend developer. It is not a collection of short definitions. It is a training system for explaining JavaScript accurately, debugging real frontend bugs, and making better production decisions under interview pressure.

Use it with one expectation: every concept must become something you can explain, trace, debug, and apply.

## Who This Is For

This vault is for a frontend developer who can already build React and Next.js features, but wants stronger depth:

- You know the syntax, but want to explain why the runtime behaves that way.
- You can use hooks, promises, arrays, modules, and objects, but want to debug edge cases without guessing.
- You want interview answers that sound experienced, not memorized.
- You want production judgment: cleanup, cancellation, mutation, identity, performance, error handling, hydration, and data flow.

## What Mature Means

A topic is mature only when you can do all of this:

- Define it simply without vague phrases.
- Name the accurate mechanism from the language, browser, framework, or runtime.
- Trace a small code example step by step.
- Recognize the production bug caused by misunderstanding it.
- Choose a safe implementation pattern and explain the tradeoff.
- Give a short interview answer and a deeper follow-up answer.

If you can only repeat a definition, the topic is not learned yet.

## Folder Structure

The vault is ordered by dependency, not by popularity:

```txt
Advanced JavaScript/
  00 - Start Here.md
  01 - Roadmap.md
  02 - JavaScript Runtime Foundations/
  03 - Scope and Variables/
  04 - Functions Deep Dive/
  05 - this Binding/
  06 - Objects and Prototypes/
  07 - Arrays and Iteration/
  08 - Async JavaScript/
  09 - Event Loop Advanced/
  10 - Modules/
  11 - Error Handling/
  12 - Advanced Language Concepts/
  13 - Performance and Memory/
  14 - JavaScript in React and Next.js/
  15 - Interview Preparation/
  16 - Code Output Questions/
  17 - Practical Frontend Scenarios/
  18 - Revision Plans/
  19 - DOM and Browser APIs/
  20 - Network and Security/
  21 - React Internals and Patterns/
  22 - Next.js Deep Dive/
  23 - TypeScript Deep Dive/
  24 - Testing and Quality/
  25 - Accessibility and Inclusive UX/
  26 - How the Web Works/
  27 - Frontend Tooling and Build Systems/
  28 - Frameworks and Application Architecture/
  29 - Frontend System Design/
  30 - Backend System Design/
  31 - Low Level Design/
  32 - Compilation and Machine Foundations/
  90 - Labs/
  98 - Vault Operations/
  99 - Glossary.md
```

The early modules teach the runtime model. The middle modules teach language mechanisms. The later modules force those mechanisms through React, Next.js, production scenarios, interviews, and revision. Modules 19–25 (folder numbers, not study order) go deeper on the browser platform, network/security, React internals, Next.js, TypeScript, testing, and accessibility — the [[01 - Roadmap|Roadmap]] slots them into the correct logical study order (19 after the Event Loop, 20 after Error Handling, 21 and 22 after JavaScript in React, 23–25 as the production-craft layer on top). Modules 26–29 extend into how the web works, tooling, application architecture, and frontend system design; modules 30–31 add backend system design and low-level design — not to turn you into a backend engineer, but because caching, contention, consistency, and design patterns are your frontend knowledge one scale up (each note carries a "Frontend mirror"). Module 32 sits outside the interview path entirely: it is the machine layer *below* the engine notes — bytecode to machine code, instruction encodings, LLVM, AOT vs JIT, the CPU and the memory hierarchy — and exists so that words like "compiled" and "register" stop being placeholders. Read it out of curiosity, never instead of the modules above. `90 - Labs` holds build briefs that turn notes into hands-on practice; `98 - Vault Operations` holds templates and vault housekeeping.

## Source Hierarchy

Use sources in this order:

1. [ECMAScript specification](https://tc39.es/ecma262/) for core language behavior: execution, scope, functions, objects, promises, modules, jobs, and values.
2. [MDN JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript) and Web API docs for developer-facing explanations and browser APIs.
3. [HTML Living Standard](https://html.spec.whatwg.org/multipage/webappapis.html) for browser event loop, tasks, microtasks, and rendering integration.
4. [React docs](https://react.dev/reference/react) for rendering, state, effects, memoization, and hook behavior.
5. [Next.js docs](https://nextjs.org/docs) for server/client boundaries, routing, rendering, and hydration.
6. [web.dev](https://web.dev/) for performance, Core Web Vitals, loading, responsiveness, and measurement.
7. [TypeScript handbook](https://www.typescriptlang.org/docs/handbook/intro.html) for the type system and compiler behavior.
8. [Testing Library](https://testing-library.com/docs/), [Vitest](https://vitest.dev/guide/), [Playwright](https://playwright.dev/docs/intro), and [MSW](https://mswjs.io/docs/) docs for testing behavior and tooling.
9. [WCAG](https://www.w3.org/WAI/WCAG22/quickref/) and the [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/) for accessibility requirements and widget patterns.

The notes should synthesize these sources in original wording. Do not copy long passages. Use source links to verify accuracy and to go deeper when a topic feels slippery.

## How Each Note Should Be Read

Every serious concept should be read through three layers:

| Layer                  | What you should ask                                                   |
| ---------------------- | --------------------------------------------------------------------- |
| Simple explanation     | What is the concept in one or two sentences?                          |
| Accurate mechanism     | What does the spec, browser, React, or Next.js actually guarantee?    |
| Production application | What bug does this prevent, and what tradeoff does the fix introduce? |

Do not stop at the first layer. Mid-level interviews often start simple, then test whether you can go one level deeper.

## The 8-Part Note Pattern

Many concept notes use this pattern. If a note does not use the exact headings, still study it with the same mental checklist:

| Part                    | What It Trains                                                       |
| ----------------------- | -------------------------------------------------------------------- |
| Simple explanation      | Say the concept without jargon.                                      |
| Why it matters          | Connect it to bugs, interviews, or design decisions.                 |
| Accurate mechanism      | Name the source of truth: spec, browser, React, Next.js, or runtime. |
| Mental model            | Build an image you can use while debugging.                          |
| Real frontend example   | See the concept under production pressure.                           |
| Common bug or edge case | Learn the trap before it appears in work.                            |
| Interview answer        | Practice concise technical communication.                            |
| Practice                | Prove you can retrieve and apply it.                                 |

ClaudeCode's strongest notes use this rhythm well: they do not stop at "what"; they show "why it exists," "what breaks," and "how to explain it cleanly."

## The Study Loop

Use this loop for every file:

1. Read the concept section once.
2. Close the file and write a 5-sentence explanation from memory.
3. Trace the code example by hand before running it.
4. Explain the real-world failure mode.
5. Write the fixed version or production-safe pattern.
6. Say the interview answer out loud in 30 seconds.
7. Add one follow-up: "What changes in React, Next.js, slow network, large data, or unmount?"

Reading silently feels productive, but retrieval is what makes the knowledge usable.

## Obsidian Workflow

Use Obsidian as a thinking tool, not only a file viewer:

- Open backlinks from a hard concept to see where it appears again.
- Use graph view to notice clusters: closures connect to hooks, memory, modules, and async bugs.
- Search exact mechanism names such as `Object.is`, `Promise job`, `TDZ`, `AbortController`, or `realm`.
- Add your own short notes under practice answers, but keep source-backed explanations separate from personal mnemonics.
- When a wiki link leads to a prerequisite, read the prerequisite before forcing the advanced note.

This is especially useful for runtime foundations: `execution context`, `call stack`, `job`, `microtask`, `realm`, and `agent` are not isolated terms. They explain each other.

## How To Use This Vault Efficiently

The vault is a small operating system, not a pile of notes. Five moving parts make it efficient.

### 1. The status workflow drives everything

Every note's frontmatter has a `status`: `not-started` → `learning` → `solid`. Set it to `learning` the moment you start a note, and to `solid` only when it clears the maturity bar (simple explanation → named mechanism → production bug + tradeoff → short/deep interview answer). Promotion to `solid` should mean two clean recall passes in separate sessions; one missed mechanism on a `solid` spot-check drops it back to `learning`. This field is the single input the control panel and the study skills read — keep it honest and everything else works.

### 2. `priority` tells you what not to skip

`must-know` | `important` | `deep-dive`. Under time pressure, `must-know` + `learning` is your drill list; `deep-dive` waits until the fundamentals are `solid`.

### 3. The Base is the control panel

Open [[Base.base|Base]] (or [[_Dashboard|Dashboard]]) instead of browsing folders. Its saved views are built from `status` + `priority`:

- **Quiz Pool** — `learning` + `must-know`: your daily drill queue.
- **Study Queue** — everything currently `learning`.
- **Must Know** — must-know notes not yet `solid`: the backlog you can't skip.
- **Deep Dive Queue** — `deep-dive` work, once the core is solid.
- **Version-Sensitive (re-verify)** — notes carrying `verified_on` (React/Next/tooling facts that age), oldest first — recheck these against official docs before quoting them in an interview.

### 4. The skills do the work; they read your frontmatter

Invoke these by name (they live in `.claude/skills/`):

- **frontend-interview-griller** — "quiz me / trace this code / audit my answer." Refuses shallow answers; grades against the three-layer bar.
- **spaced-review-scheduler** — give it your interview date; it turns your real `status`/`priority` into a day-by-day dated plan and orchestrates the other skills.
- **lab-runner** — runs a `90 - Labs` brief as a paced, interactive session (you write the code).
- **add-use-cases** — appends a "Real-World Use Cases" section to a concept note.
- **vault-note-authoring** — drafts a new note from the live template, following the conventions.

Because they read frontmatter, a stale `status` gives you a bad plan — another reason to keep step 1 honest.

### 5. Know which note type you're reading

- **Concept note (8-part)** — the default. Don't just read it; trace the code, name the mechanism, and answer the practice prompts from memory.
- **MOC (`00 - … MOC`)** — a module's table of contents and reading order. Enter any module here.
- **Checklist** — prove readiness by explaining and fixing out loud, not by ticking boxes.
- **RADIO / "Designing X" walkthrough** (module 29) — a design-round rehearsal, not a memorization target. Time-box yourself and produce Requirements → Architecture → Data model → Interface → Optimizations out loud.
- **The "Frontend mirror"** in modules 30/31 — read each backend/LLD concept as your client-side knowledge one scale up (server cache ↔ query cache, distributed lock ↔ client race guard, CAP eventual consistency ↔ optimistic UI).

**A minimal daily loop:** open the Base → pick from the Quiz Pool → study it via the Study Loop above → run the griller on it → mark it `solid` when it passes → let the spaced-review-scheduler resurface it later.

## Example: How To Use A Note

When you study stale closures, do not only memorize "closures remember variables." Trace the lifetime.

```tsx
function Counter() {
  const [count, setCount] = React.useState(0);

  React.useEffect(() => {
    const id = setInterval(() => {
      // This callback was created during the render where count had one value.
	  // If the effect never reruns, the callback keeps reading that old render's binding.
      console.log(count);
    }, 1000);

    // Cleanup matters because the browser keeps a reference to this callback.
    return () => clearInterval(id);
  }, []);

  return <button onClick={() => setCount(c => c + 1)}>+</button>;
}
```

The mature explanation is:

- Simple: the interval callback reads an old value.
- Accurate: the callback closes over the lexical environment from the render that created it.
- Production: use a functional update, include dependencies when resubscription is correct, or use a ref when the requirement is latest-value reading without resubscribing.
- Interview: a stale closure is a lifetime mismatch between when a function was created and when it later runs.

Use that pattern for every topic in the vault.

## Main Learning Path

Follow [[01 - Roadmap|Roadmap]] for the full dependency order. These are the main sections:

- [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|Runtime Foundations]]
- [[03 - Scope and Variables/01 - Scope Types|Scope and Variables]]
- [[04 - Functions Deep Dive/01 - Function Declarations vs Expressions|Functions Deep Dive]]
- [[05 - this Binding/01 - What is this|this Binding]]
- [[06 - Objects and Prototypes/01 - Objects Internally|Objects and Prototypes]]
- [[07 - Arrays and Iteration/01 - Array Internals|Arrays and Iteration]]
- [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Async JavaScript]]
- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Advanced]]
- [[10 - Modules/01 - ES Modules|Modules]]
- [[11 - Error Handling/01 - try catch throw finally|Error Handling]]
- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Advanced Language Concepts]]
- [[13 - Performance and Memory/01 - Memory Management|Performance and Memory]]
- [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript in React and Next.js]]

Platform & depth (folder numbers, not study order — the [[01 - Roadmap|Roadmap]] slots them correctly):

- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM and Browser APIs]]
- [[20 - Network and Security/01 - HTTP Essentials for Frontend|Network and Security]]
- [[21 - React Internals and Patterns/01 - Render and Commit Phases|React Internals and Patterns]]
- [[22 - Next.js Deep Dive/01 - Rendering Strategies|Next.js Deep Dive]]
- [[23 - TypeScript Deep Dive/01 - Type System Mental Model|TypeScript Deep Dive]]
- [[24 - Testing and Quality/01 - Testing Mental Model|Testing and Quality]]
- [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Accessibility and Inclusive UX]]
- [[26 - How the Web Works/00 - How the Web Works MOC|How the Web Works]]
- [[27 - Frontend Tooling and Build Systems/00 - Frontend Tooling and Build Systems MOC|Frontend Tooling and Build Systems]]
- [[28 - Frameworks and Application Architecture/00 - Frameworks and Application Architecture MOC|Frameworks and Application Architecture]]

Design tracks (study only if your loop has the matching round):

- [[29 - Frontend System Design/00 - Frontend System Design MOC|Frontend System Design]]
- [[30 - Backend System Design/00 - Backend System Design MOC|Backend System Design]] (general/backend SD round)
- [[31 - Low Level Design/00 - Low Level Design MOC|Low Level Design]] (OOP/LLD round)

Practice, prep & reference:

- [[15 - Interview Preparation/01 - Junior to Mid Questions|Interview Preparation]]
- [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Code Output Questions]]
- [[17 - Practical Frontend Scenarios/01 - Fixing Stale Closure in React|Practical Frontend Scenarios]]
- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Revision Plans]]
- [[90 - Labs/00 - Labs MOC|Labs]]
- [[99 - Glossary|Glossary]]

## First Pass Plan

Use this when starting fresh:

| Day | Focus                                              | Output                                                               |
| --- | -------------------------------------------------- | -------------------------------------------------------------------- |
| 1   | Runtime foundations, execution context, call stack | Explain what runs JavaScript and what the host adds.                 |
| 2   | Scope, lexical environments, hoisting, closures    | Trace identifier lookup and closure lifetime.                        |
| 3   | Functions, `this`, objects, prototypes             | Explain call forms, receivers, delegation, and copying.              |
| 4   | Promises, async/await, event loop                  | Trace output involving jobs, tasks, microtasks, and timers.          |
| 5   | React hooks and identity                           | Explain stale closures, dependency arrays, and referential equality. |
| 6   | API integration and errors                         | Handle cancellation, race conditions, retries, and user recovery.    |
| 7   | Performance, memory, and interview practice        | Diagnose leaks, long tasks, unnecessary renders, and weak answers.   |

## Fast Track For Interviews

If time is short, study these first:

1. [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
2. [[03 - Scope and Variables/05 - Closures|Closures]]
3. [[05 - this Binding/01 - What is this|this]]
4. [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype Chain]]
5. [[08 - Async JavaScript/02 - Promises|Promises]]
6. [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
7. [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
8. [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
9. [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]]
10. [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]
11. [[22 - Next.js Deep Dive/02 - The Caching Layers|The Next.js Caching Layers]]
12. [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]]
13. [[29 - Frontend System Design/01 - The Frontend System Design Framework|Frontend System Design: RADIO]] (if your loop has a design round)
14. [[30 - Backend System Design/05 - Caching|Backend System Design: Caching]] (if your loop has a general system-design round)
15. [[31 - Low Level Design/04 - Design Patterns|Low Level Design: Design Patterns]] (if your loop has an OOP/LLD round)
16. [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
17. [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]]
18. [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]
19. [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|React Component Testing Through User Behavior]]

## How To Use Different File Types

- Concept notes: learn the mechanism, real bug, tradeoff, and interview answer.
- MOC files (`00 - … MOC`): a module's table of contents and reading order — start here when entering a module.
- System-design walkthroughs (RADIO, module 29's "Designing X" notes): don't memorize; time-box yourself and produce requirements → architecture → data model → APIs → ranked optimizations out loud.
- Checklists: prove readiness by explaining and fixing, not by passively checking boxes.
- Code-output questions: predict first, then run only after committing to an answer.
- Practical scenarios: practice production reasoning with bug, fix, checklist, and tradeoff.
- Interview preparation: train communication, answer structure, and follow-up handling.
- Revision plans: schedule repetition so the knowledge stays available under pressure.
- Glossary: use precise terms when they remove ambiguity, not to sound complicated.

## Weekly Review

At the end of each week:

- Revisit [[99 - Glossary|Glossary]] and explain ten terms without reading.
- Solve five code-output questions from [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]].
- Pick one practical scenario and write the bug, root cause, and production-safe fix.
- Record yourself answering three interview questions in under 30 seconds each.
- Mark weak topics and return to the source anchors before rereading summaries.

## Start Here Self-Test

**Q1. What does "mature understanding" mean in this vault?**

<details>
<summary>Show answer</summary>

It means you can move through three layers: simple explanation, accurate mechanism, and production application. For example, "a stale closure reads an old value" is the simple explanation; "the callback closed over the lexical environment from a previous render" is the mechanism; "use a functional update, honest dependencies, or a ref depending on the lifetime you need" is the production application.

</details>

**Q2. Why does the vault start with runtime foundations instead of React hook bugs?**

<details>
<summary>Show answer</summary>

React hook bugs are ordinary JavaScript behavior made visible by rendering. To explain stale closures, dependency arrays, async effects, hydration, and UI freezes, you need the foundations first: execution contexts, lexical environments, call stack, heap reachability, host APIs, jobs, tasks, and microtasks.

</details>

**Q3. How should you use a code-output question?**

<details>
<summary>Show answer</summary>

Predict before running. Write the output, then write the mechanism for each line: creation phase, TDZ, receiver binding, prototype lookup, promise job, task, or microtask. Only then run the snippet. If you were wrong, record the exact rule you missed instead of just memorizing the final output.

</details>

**Q4. Why is source hierarchy important?**

<details>
<summary>Show answer</summary>

Different questions have different authorities. ECMAScript answers language semantics such as promises, execution contexts, and modules. HTML answers browser event-loop integration. MDN helps translate platform behavior. React and Next.js answer framework-specific rendering, effects, hydration, and server/client boundaries. Using the wrong source often creates confident but inaccurate explanations.

</details>

**Q5. What is the minimum output after studying any concept note?**

<details>
<summary>Show answer</summary>

You should have one plain-English definition, one accurate mechanism, one traced code example, one realistic frontend bug, one production-safe pattern with tradeoffs, and one interview answer. If any of those are missing, the topic is still fragile.

</details>

## Red Flags While Studying

Pause and deepen the topic when you notice any of these:

- You can say what happens, but not why.
- You rely on vague folklore phrases instead of naming the mechanism.
- You cannot draw the lifetime of the value, callback, request, or component.
- You cannot explain what changes between browser, Node.js, React, and Next.js.
- You know the fix, but not the tradeoff.
- You cannot create a small failing example yourself.

## Completion Checklist

You are ready to move past this starting module when you can explain:

- [ ] Why the vault prioritizes mechanisms over memorized slogans.
- [ ] Which sources are authoritative for language, browser, React, Next.js, and performance behavior.
- [ ] How to study a note using simple explanation, accurate mechanism, and production application.
- [ ] How to use code-output questions without fooling yourself.
- [ ] Why every important concept should connect to a real frontend bug.
- [ ] How to choose between the full roadmap and the interview fast track.

## Related Notes

- [[01 - Roadmap|Roadmap]]
- [[99 - Glossary|Glossary]]
- [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]]
- [[18 - Revision Plans/03 - 14 Day Deep Study Plan|14 Day Deep Study Plan]]
