---
tags: [system-design, interview, moc]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
---

# Frontend System Design MOC

This module trains the interview format the rest of the vault only implies: "design an Autocomplete" — 30–45 minutes, whiteboard or doc, no code editor. The mechanisms all live elsewhere ([[17 - Practical Frontend Scenarios/09 - Debounced Search|debounce]], [[17 - Practical Frontend Scenarios/10 - Request Cancellation|cancellation]], [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|state taxonomy]], [[25 - Accessibility and Inclusive UX/00 - Accessibility and Inclusive UX MOC|a11y]]); what's new here is the *composition skill*: turning vague requirements into an architecture, a data model, a component API, and a prioritized list of optimizations — out loud, with tradeoffs, under time pressure.

## Prerequisites

- [[28 - Frameworks and Application Architecture/00 - Frameworks and Application Architecture MOC|Frameworks and Application Architecture MOC]] — state taxonomy and component design are assumed vocabulary here.
- [[17 - Practical Frontend Scenarios/00 - Practical Frontend Scenarios MOC|Practical Frontend Scenarios MOC]] — the bug-level view of every pattern this module designs around.
- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]] and [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]] — data-fetching decisions lean on these.

## Reading Order

Start with the framework, learn the foundations every walkthrough leans on, then work the walkthroughs (RADIO applied end to end), then self-test.

**The framework**

1. [[29 - Frontend System Design/01 - The Frontend System Design Framework|The Frontend System Design Framework]] — RADIO: the repeatable structure for any widget/app question.

**Foundations — the vocabulary the walkthroughs assume**

2. [[29 - Frontend System Design/05 - Rendering Strategies for Design|Rendering Strategies for Design]] — CSR/SSR/SSG/ISR/streaming, chosen per route.
3. [[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]] — caching, dedup, pagination, prefetch, invalidation.
4. [[29 - Frontend System Design/09 - Network and API Design for Frontend|Network and API Design for Frontend]] — REST vs GraphQL, BFF, cursor pagination.
5. [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]] — shared entities, optimistic UI with rollback.
6. [[29 - Frontend System Design/07 - Component API Design|Component API Design]] — controlled/uncontrolled, composition, IoC, headless.
7. [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]] — Core Web Vitals (LCP/INP/CLS), ranked optimization.
8. [[29 - Frontend System Design/14 - Accessibility in System Design|Accessibility in System Design]] — APG patterns, focus, announcements as design inputs.
9. [[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]] — transport, ordering, reconnection, backpressure.
10. [[29 - Frontend System Design/11 - Internationalization and RTL|Internationalization and RTL]] — formatting, layout direction, locale bundles.
11. [[29 - Frontend System Design/12 - Offline and Resilient UX|Offline and Resilient UX]] — caching layers, offline writes, conflict resolution.

**Walkthroughs — RADIO applied end to end**

12. [[29 - Frontend System Design/02 - Designing an Autocomplete|Designing an Autocomplete]] — the canonical component question.
13. [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Designing an Infinite Scroll Feed]] — cursor pagination, virtualization, scroll restoration.
14. [[29 - Frontend System Design/17 - Designing a Data Table|Designing a Data Table]] — server vs client ops, virtualization, the grid a11y pattern.
15. [[29 - Frontend System Design/18 - Designing an Image Carousel|Designing an Image Carousel]] — image loading, CLS, gestures, the carousel a11y pattern.
16. [[29 - Frontend System Design/15 - Designing a Modal and Dialog System|Designing a Modal and Dialog System]] — portals, focus trap, stacking, promise-based API.
17. [[29 - Frontend System Design/16 - Designing a Notification and Toast System|Designing a Notification and Toast System]] — queue, timing, dedup, live-region announcements.
18. [[29 - Frontend System Design/19 - Designing a Chat and Messaging App|Designing a Chat and Messaging App]] — real-time, optimistic send, reverse pagination.
19. [[29 - Frontend System Design/20 - Designing an E-commerce Product Page|Designing an E-commerce Product Page]] — SEO, rendering by freshness, cart, Core Web Vitals.

**Self-test**

20. [[29 - Frontend System Design/03 - Frontend System Design Checklist|Frontend System Design Checklist]] — active self-test across all of the above.

## You're Done When

- [ ] Given any "design X" prompt, I open with requirements questions instead of an implementation — and can say *why* each question changes the design.
- [ ] I can run RADIO on a widget in 35 minutes without prompting, allocating time deliberately across the sections.
- [ ] I can draw a component/data-flow diagram and defend every boundary in it.
- [ ] I can design a component's public API (props/events/slots) and justify controlled vs uncontrolled, composition, and headless tradeoffs.
- [ ] I can choose a rendering strategy per route from SEO, freshness, and performance requirements.
- [ ] I can design the client data layer — keys, dedup, staleness, pagination, invalidation — and the network API (REST/GraphQL/BFF) it consumes.
- [ ] I can decide when to normalize state and design an optimistic update with reconciliation and rollback.
- [ ] I can rank optimizations by user impact and map each to a Core Web Vital (LCP/INP/CLS).
- [ ] Accessibility (the right APG pattern, focus, announcements), i18n/RTL, offline, and failure states appear in my design unprompted.
- [ ] I can choose a real-time transport and design ordering, reconnection catch-up, and backpressure.
- [ ] I can walk any of the eight worked questions end to end, and transfer each to an adjacent prompt naming exactly what changes.

## Related Notes

- [[15 - Interview Preparation/00 - Interview Preparation MOC|Interview Preparation MOC]]
- [[90 - Labs/00 - Labs MOC|Labs MOC]]
- [[01 - Roadmap|Roadmap]]
