---
tags: [labs, moc, practice]
module: "90 - Labs"
priority: important
status: not-started
---

# Labs MOC

Labs are build briefs, not tutorials: each gives you a spec, acceptance criteria, planted debugging tasks, and the testing/accessibility/performance bar a senior reviewer would hold you to. You write all the code yourself, in a scratch repo, without installing anything unusual — Vite or `create-next-app` and the standard test stack cover everything.

How to work a lab:

1. Read the brief and the linked prerequisite notes *first* — the lab is where those mechanisms become muscle memory.
2. Build to the acceptance criteria. Check them off honestly — each is phrased as something you can demonstrate.
3. Do the debugging tasks: deliberately create each listed bug, observe the symptom with real tools, then fix it. Seeing the failure is the point.
4. Write the tests and run the accessibility passes the brief demands.
5. Answer the interview questions out loud, then write a short retrospective ([[98 - Vault Operations/Templates/Lab Retrospective Template|template]]).

## The Labs

1. [[90 - Labs/01 - Event Loop and Rendering Profiler Lab|Event Loop and Rendering Profiler]] — make tasks, microtasks, and long frames *visible*; fix jank you caused.
2. [[90 - Labs/02 - Typed API Boundary Lab|Typed API Boundary with Runtime Validation]] — one validated seam between an untrusted API and typed UI code.
3. [[90 - Labs/03 - Accessible Async Search Lab|Accessible Async Search and Form Flow]] — debounce, cancellation, announcements, and full keyboard operability in one feature.
4. [[90 - Labs/04 - Next Cached Dashboard Mutation Lab|Next.js Cached Dashboard Mutation]] — tag-based caching with correct invalidation, proven by tests.
5. [[90 - Labs/05 - Code Review Lab - The Search Results PR|Code Review Lab: The Search Results PR]] — a different format: review a plausible teammate PR with 8 planted bugs, name each mechanism, then grade yourself against the hidden model review.
6. [[90 - Labs/06 - Frontend System Design Round Lab|Frontend System Design Round Lab]] — a different format: run a timed RADIO design round out loud, then grade your walkthrough against a hidden model outline. Rehearses the design interview, not a build.
7. [[90 - Labs/07 - Bytecode VM Lab|Build a Bytecode VM]] — `#deep-dive`, **off the interview path**: compile an AST to stack IR and to register IR, write both VMs, add liveness analysis with spilling, then emit real assembly. 6-10 hours. Do not start it while `#must-know` notes are still `not-started`.

## Prerequisite Map

| Lab | Core prerequisites |
| --- | --- |
| 01 | [[09 - Event Loop Advanced/00 - Event Loop Advanced MOC|Event Loop]], [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|Render Pipeline]], [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals]] |
| 02 | [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|Runtime Validation]], [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling]], [[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|MSW]], [[29 - Frontend System Design/09 - Network and API Design for Frontend|Network & API Design]], [[30 - Backend System Design/03 - API Design|Backend API Design]] |
| 03 | [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]], [[08 - Async JavaScript/06 - AbortController|AbortController]], [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms]], [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions]], [[29 - Frontend System Design/02 - Designing an Autocomplete|Autocomplete]], [[29 - Frontend System Design/14 - Accessibility in System Design|A11y in System Design]] |
| 04 | [[22 - Next.js Deep Dive/02 - The Caching Layers|Caching Layers]], [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]], [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]], [[24 - Testing and Quality/08 - Testing Nextjs Boundaries|Testing Next Boundaries]], [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|Optimistic Updates]], [[30 - Backend System Design/05 - Caching|Backend Caching]] |
| 05 | [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Race Conditions]], [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]], [[20 - Network and Security/05 - XSS|XSS]], [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling]] |
| 06 | [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO Framework]], [[29 - Frontend System Design/03 - Frontend System Design Checklist|FSD Checklist]], [[29 - Frontend System Design/08 - Frontend Performance for System Design|Performance for System Design]], [[29 - Frontend System Design/14 - Accessibility in System Design|A11y in System Design]] |
| 07 | [[32 - Compilation and Machine Foundations/01 - From Source Text to Silicon|Source to Silicon]], [[32 - Compilation and Machine Foundations/02 - Stack Register and Accumulator Bytecode|Stack vs Register Bytecode]], [[32 - Compilation and Machine Foundations/09 - Interpreters Dispatch and the Two Stacks|Interpreters and Dispatch]], [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] |

## Related Notes

- [[17 - Practical Frontend Scenarios/00 - Practical Frontend Scenarios MOC|Practical Frontend Scenarios MOC]]
- [[24 - Testing and Quality/00 - Testing and Quality MOC|Testing and Quality MOC]]
- [[29 - Frontend System Design/00 - Frontend System Design MOC|Frontend System Design MOC]]
- [[30 - Backend System Design/00 - Backend System Design MOC|Backend System Design MOC]]
- [[31 - Low Level Design/00 - Low Level Design MOC|Low Level Design MOC]]
- [[32 - Compilation and Machine Foundations/00 - Compilation and Machine Foundations MOC|Compilation and Machine Foundations MOC]]
- [[01 - Roadmap|Roadmap]]
