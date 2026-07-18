---
tags: [system-design, interview, framework]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [RADIO, RADIO framework]
---

# The Frontend System Design Framework

## Maturity Target

- Priority: #must-know
- Study time: 45 minutes
- Interview signal: You can structure any "design X" question into Requirements → Architecture → Data model → Interface → Optimizations, out loud, with deliberate time allocation.
- Production signal: Design docs and PR descriptions start stating requirements and tradeoffs before implementation details.
- Dependencies: [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]], [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]]

## Source Anchors

- [GreatFrontEnd — Front End System Design Playbook](https://www.greatfrontend.com/system-design)
- [patterns.dev](https://www.patterns.dev/)
- [web.dev — Performance patterns](https://web.dev/explore/fast)

## 1. Concept

Simple version: frontend system design questions test whether you can go from a vague product ask ("build search suggestions") to a defensible architecture — the same skill as writing a good design doc, compressed into 35 minutes.

The accurate mechanism: interviewers grade *structure* as much as content. An unstructured candidate dives into `useEffect` details; a mature one runs a framework. The standard one is **RADIO**:

| Phase | Time (of 35 min) | What you produce |
| --- | --- | --- |
| **R**equirements | ~5 min | Functional + non-functional requirements; explicit out-of-scope list |
| **A**rchitecture | ~8 min | Component/box diagram: UI pieces, controller/state layer, network layer, cache |
| **D**ata model | ~7 min | Client state shape: what's server cache vs UI state; normalization; who owns what |
| **I**nterface (API) | ~8 min | Two APIs: the component's public API (props/events) and the network API (endpoints, pagination, payload shape) |
| **O**ptimizations | ~7 min | Ranked deep dives: performance, a11y, race conditions, resilience — driven by the requirements from step 1 |

> [!tip] The requirements phase is where seniority shows. Every later decision should trace back to a requirement ("you said mobile-heavy traffic, so payload size beats render micro-optimizations"). If you can't connect a decision to a requirement, it's decoration.

Questions that earn signal in the Requirements phase: Who are the users and on what devices/networks? What's the scale (10 items or 10,000)? Real-time or eventually consistent? Offline? i18n/RTL? Which browsers? What's explicitly out of scope?

## 2. Why It Matters

Mid/senior loops increasingly replace one coding round with a design round. The failure mode is not ignorance — you know debounce and AbortController — it's *shapelessness*: 30 minutes on rendering details, zero on data model, no tradeoffs stated. RADIO prevents that mechanically. It also transfers: the same structure is a design doc template.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

The "bug" here is a failed interview transcript, not code.

Shapeless answer to "design a typeahead":

> "I'd use a `useState` for the query, a `useEffect` that fetches on change, debounce it with lodash, render a list below the input…"

Trace of why it fails: it answers *how would you code it* — never establishes scale (client-side filter vs server search are different systems), never mentions caching, races, keyboard/a11y, or the component's consumers. The interviewer has to drag every dimension out of you, and that's what caps the score.

Structured answer opens instead with:

> "Before designing: is this searching a small local dataset or a server index? Multi-tenant widget or one app? Latency target? … Given server-backed and reusable, here's my architecture: input → controller → query cache → network layer, and I'll design the component API so consumers can control or delegate selection state…"

Tradeoff of the framework itself: rigidity. Applied mechanically, RADIO wastes time on phases the question doesn't stress (a pure-UI carousel needs little network API design). Mature use means *reallocating* the minutes, and saying you're doing so.

## 4. Interview Answer

Short answer:

> "I structure design questions as requirements, architecture, data model, interface, then optimizations — RADIO. I spend the first five minutes on requirements because they decide everything else, and I keep every later choice traceable to one."

Deeper answer:

> "Two things I've learned to do deliberately: first, separate the two APIs — the component API consumers see and the network API — because they have different consumers and change at different rates. Second, treat the optimizations phase as *ranked by requirement*, not as a grab bag: if the requirement is slow networks, request-layer work (dedup, caching, payload) dominates; if it's huge lists, rendering work (virtualization, memoization) dominates. I say the ranking out loud so the interviewer hears the reasoning, not just the list."

## 5. Practice

1. <details><summary>You get "design a poll widget." What are your first four questions, and what design decision does each one gate?</summary>Embedded in third-party pages or first-party? (gates: shadow DOM/style isolation, bundle size budget, no framework assumptions). Live-updating results? (gates: WebSocket/SSE/polling — [[20 - Network and Security/08 - WebSockets SSE and Polling|transport choice]]). Auth or anonymous voting? (gates: dedup strategy, optimistic UI safety). Expected option count and vote scale? (gates: rendering approach, aggregation on server vs client).</details>
2. <details><summary>Why is "component API" a separate design phase from "architecture"?</summary>Different consumer: architecture serves the implementer; the component API serves *other developers*. Its design questions are contract questions — controlled vs uncontrolled state, events vs callbacks, composition (slots/children) vs configuration (props) — and getting them wrong is a breaking change, unlike internal architecture which can be refactored freely.</details>
3. <details><summary>Transfer: how does RADIO map onto writing a real design doc?</summary>Almost 1:1 — Requirements → "Goals / Non-goals", Architecture → system diagram, Data model → storage/state section, Interface → API spec, Optimizations → "Performance / a11y / failure modes" plus the alternatives-considered section, which is the written form of stating tradeoffs out loud.</details>

## 6. Real-World Use Cases

RADIO isn't just an interview trick — it's a design-doc template, so it earns its keep in daily work. The value in each case below is the same: requirements first, every decision traceable.

### Writing a feature RFC / design doc

Before building a new "saved filters" feature, you write a one-page RFC. RADIO is the outline: Requirements → Goals/Non-goals, Architecture → a component + data-flow diagram, Data model → where filter state lives (URL? server? local?), Interface → the API other screens call, Optimizations → the perf/a11y/failure sections plus alternatives-considered.

```md
## Goals / Non-goals            ← R
## Architecture (diagram)        ← A
## State & data model            ← D
## API (component + network)     ← I
## Performance, a11y, failure    ← O
## Alternatives considered       ← the written form of "tradeoffs out loud"
```

Works because RADIO maps almost 1:1 to a design doc — the "alternatives considered" section is just stating tradeoffs on paper. See [[15 - Interview Preparation/08 - Explaining Tradeoffs to Non-Engineers|Explaining Tradeoffs to Non-Engineers]].

### Structuring a non-trivial PR description

A reviewer opening a 600-line PR needs the *why*, not just the diff. Leading with a compressed RADIO — what this satisfies (R), the shape (A), the state decision (D), the API change (I), and what you optimized/deferred (O) — turns a wall of code into a reviewable argument and pre-empts the "why did you do it this way" round-trip.

> [!tip] A PR that opens with "Requirement: … / Approach: … / Tradeoff I made: …" gets reviewed faster and better than one that opens with "see title" — the reviewer can check decisions against intent instead of reverse-engineering them.

### Triaging an architecture disagreement

Two engineers disagree on whether filter state belongs in the URL or a store. RADIO defuses it: back up to Requirements (is shareable/bookmarkable state a requirement?). The answer decides it — if links must be shareable, URL wins; if not, it's a free choice. Most "architecture arguments" are really unstated-requirement arguments, and naming the requirement ends them. See [[15 - Interview Preparation/09 - Architecture Disagreements and Ownership Stories|Architecture Disagreements and Ownership Stories]].

## Related Notes

- [[29 - Frontend System Design/02 - Designing an Autocomplete|Designing an Autocomplete]]
- [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]
- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
- [[30 - Backend System Design/01 - The Delivery Framework|Backend Delivery Framework]] — the same requirements-first skill, backend artifacts
- [[31 - Low Level Design/01 - The Delivery Framework|LLD Delivery Framework]] — the same skill at class level
