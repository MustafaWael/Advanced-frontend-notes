---
tags: [low-level-design, oop, interview, moc]
module: "31 - Low Level Design"
priority: must-know
status: not-started
---

# Low Level Design MOC

Low-level design is the OOP/design-quality round: given a prompt like "design a parking lot" or "design a rate limiter," produce clean classes with clear responsibilities, the right relationships, and extensibility — single-process, no distributed systems. It's the class-level counterpart to [[30 - Backend System Design/00 - Backend System Design MOC|Backend System Design]].

For a frontend engineer this is closer to home than it looks: SOLID and the handful of patterns that matter are how good component and state architecture is already built ([[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]]), and the concurrency section is the smallest-scale version of the contention problem you handle as race conditions on the client. Examples here are in modern TS to match the vault, with notes on where JS's single-threaded event loop changes the concurrency picture.

## Prerequisites

- [[06 - Objects and Prototypes/00 - Objects and Prototypes MOC|Objects and Prototypes MOC]] — the object model these patterns build on.
- [[23 - TypeScript Deep Dive/00 - TypeScript Deep Dive MOC|TypeScript Deep Dive MOC]] — interfaces, generics, and variance make the patterns expressible.
- [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]] — where these patterns already show up in your frontend work.

## Reading Order

1. [[31 - Low Level Design/01 - The Delivery Framework|The Delivery Framework]] — Requirements → Entities → Class Design → Implementation → Extensibility.
2. [[31 - Low Level Design/02 - Design Principles|Design Principles]] — KISS/DRY/YAGNI/SoC + SOLID.
3. [[31 - Low Level Design/03 - OOP Concepts|OOP Concepts]] — encapsulation, abstraction, polymorphism, inheritance vs composition.
4. [[31 - Low Level Design/04 - Design Patterns|Design Patterns]] — the ~5 that matter, and where they live in your frontend.
5. [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]] — locks, semaphores, queues; and how JS differs.
6. [[31 - Low Level Design/06 - Low Level Design Checklist|Low Level Design Checklist]] — active self-test.

## You're Done When

- [ ] Given a "design X" prompt, I derive entities and their state/behavior from requirements before writing methods.
- [ ] I can name each SOLID principle, the smell it fixes, and show it in TS.
- [ ] I default to composition over inheritance and can say when inheritance actually fits.
- [ ] I can implement Factory, Strategy, Observer, Builder, and State in TS, and point to where each already appears in React/frontend code.
- [ ] I only reach for a pattern when the problem calls for it, and can name the over-engineering smell of forcing one.
- [ ] I can reason about a small concurrency problem (a shared counter, a bounded pool) and explain how JS's single thread changes the toolkit — async locks for `await`-spanning critical sections, `navigator.locks`, and Web Workers + message passing — without claiming mutual exclusion is never needed.

## Related Notes

- [[30 - Backend System Design/00 - Backend System Design MOC|Backend System Design MOC]]
- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
