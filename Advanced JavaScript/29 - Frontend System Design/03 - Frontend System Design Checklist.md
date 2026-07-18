---
tags: [system-design, interview, checklist]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
---

# Frontend System Design Checklist

Use this checklist as an active test. Mark an item complete when you can do it out loud, on a whiteboard, without the notes.

## Source Anchors

- [GreatFrontEnd — Front End System Design Playbook](https://www.greatfrontend.com/system-design)
- [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/patterns/)
- [patterns.dev](https://www.patterns.dev/)

## Framework

- [ ] I can name the five RADIO phases, their rough time budgets, and what artifact each produces.
- [ ] I open every design question with requirements questions, and can state which design decision each question gates.
- [ ] I can reallocate phase time for the question type (UI-heavy vs data-heavy) and say I'm doing it.
- [ ] Every optimization I propose traces to a stated requirement; I can rank them by user impact.

## Architecture and State

- [ ] I can draw the controller / query-layer split and explain which bugs it prevents.
- [ ] I can model a widget's UI as an explicit state machine and name two impossible states it eliminates.
- [ ] I can classify every piece of state in my design as server cache vs UI state ([[28 - Frameworks and Application Architecture/06 - Server State|Server State]]).
- [ ] I can explain state normalization (ids + entity map), when it pays for itself, and when it's over-engineering.

## Interface Design

- [ ] I can design a component API with controlled + uncontrolled support and justify the dual mode.
- [ ] I can apply inversion of control (injected `getSuggestions`-style functions, render props/slots) and state its cost.
- [ ] I can design the network API for cacheability (GET, lean payloads, echoed query) and explain cursor vs offset pagination.

## Cross-Cutting Concerns (unprompted, every time)

- [ ] Race conditions: abort + compare-on-resolve guard, and why debounce alone is insufficient.
- [ ] Accessibility: the relevant APG pattern for the widget, virtual focus vs DOM focus, announcement choreography.
- [ ] Failure modes: network error, empty results, slow response — each has a designed state, and core input never breaks.
- [ ] Performance: request-layer discipline vs render-layer work, and which dominates for the stated requirements.
- [ ] Security: where untrusted content enters the render path ([[20 - Network and Security/05 - XSS|XSS]]).

## Foundations Fluency

- [ ] I can choose a rendering strategy per route from SEO, personalization, freshness, and first-paint requirements ([[29 - Frontend System Design/05 - Rendering Strategies for Design|Rendering Strategies]]).
- [ ] I can design the client data layer — keys, dedup, staleness, prefetch, invalidation — as a cache ([[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]]).
- [ ] I can pick REST vs GraphQL vs a BFF from the client's data shape and name the over/under-fetch and waterfall pains ([[29 - Frontend System Design/09 - Network and API Design for Frontend|Network and API Design]]).
- [ ] I can decide when to normalize and design an optimistic update with snapshot, rollback, and query cancellation ([[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|Normalization and Optimistic Updates]]).
- [ ] I can rank optimizations by user impact and map each to LCP, INP, or CLS ([[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance]]).
- [ ] I can name the APG pattern a widget maps to and design its focus + announcement contract ([[29 - Frontend System Design/14 - Accessibility in System Design|Accessibility in System Design]]).
- [ ] I can choose a real-time transport and design ordering, reconnection catch-up, and backpressure ([[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]]).
- [ ] I raise i18n/RTL and offline/degraded-network as requirements and design for them ([[29 - Frontend System Design/11 - Internationalization and RTL|i18n]], [[29 - Frontend System Design/12 - Offline and Resilient UX|Offline]]).

## Walkthrough Fluency

- [ ] Autocomplete: full RADIO pass in 35 minutes ([[29 - Frontend System Design/02 - Designing an Autocomplete|Autocomplete]]).
- [ ] Infinite feed: full pass including the cursor-vs-offset defense ([[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Infinite Scroll Feed]]).
- [ ] Data table: server-vs-client ops threshold, virtualization + `aria-rowcount` ([[29 - Frontend System Design/17 - Designing a Data Table|Data Table]]).
- [ ] Carousel: LCP image strategy, CLS reservation, autoplay a11y ([[29 - Frontend System Design/18 - Designing an Image Carousel|Carousel]]).
- [ ] Modal system: portal + focus trap/restore + promise-based API ([[29 - Frontend System Design/15 - Designing a Modal and Dialog System|Modal System]]).
- [ ] Toast system: module store, pausable timer, live-region announcements ([[29 - Frontend System Design/16 - Designing a Notification and Toast System|Toast System]]).
- [ ] Chat app: optimistic send states, reverse pagination, reconnection catch-up ([[29 - Frontend System Design/19 - Designing a Chat and Messaging App|Chat App]]).
- [ ] E-commerce page: render by data freshness, cart as shared state, Core Web Vitals ([[29 - Frontend System Design/20 - Designing an E-commerce Product Page|E-commerce Page]]).
- [ ] I can transfer any design to an adjacent prompt (autocomplete → mention picker, feed → chat list, modal → toast) naming exactly what changes.

## Related Notes

- [[29 - Frontend System Design/00 - Frontend System Design MOC|Frontend System Design MOC]]
- [[15 - Interview Preparation/07 - Interview Checklist|Interview Checklist]]
