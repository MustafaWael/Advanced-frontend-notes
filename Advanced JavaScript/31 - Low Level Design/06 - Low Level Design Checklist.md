---
tags: [low-level-design, interview, checklist]
module: "31 - Low Level Design"
priority: must-know
status: not-started
---

# Low Level Design Checklist

Active test. Mark an item complete when you can do it out loud, on a whiteboard, without the notes.

## Source Anchors

- [HelloInterview — Low Level Design in a Hurry](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/introduction)

## Framework

- [ ] I run Requirements → Entities → Class Design → Implementation → Extensibility, deriving state and behavior from requirements ([[31 - Low Level Design/01 - The Delivery Framework|Delivery Framework]]).
- [ ] I walk a concrete scenario through the objects to verify clean responsibilities.
- [ ] I can map this to RADIO and the backend framework as one requirements-first skill.

## Principles and OOP

- [ ] I can name each SOLID principle, the smell it fixes, and show it in TS ([[31 - Low Level Design/02 - Design Principles|Design Principles]]).
- [ ] I apply KISS/YAGNI as a check against over-applying SOLID and patterns.
- [ ] I default to composition over inheritance and can state two signals inheritance has broken down ([[31 - Low Level Design/03 - OOP Concepts|OOP Concepts]]).
- [ ] I can point to where SRP, DIP, and OCP already appear in my frontend code.

## Patterns

- [ ] I can implement Strategy, Observer, Factory, Builder, and State in TS ([[31 - Low Level Design/04 - Design Patterns|Design Patterns]]).
- [ ] I name each pattern's trigger and where it already lives in frontend code (Observer ↔ [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]).
- [ ] I can explain why forcing a pattern (or a Singleton) is an over-engineering smell.

## Concurrency

- [ ] I can name the primitives (atomic, mutex, semaphore, condition variable, blocking queue), the three problem types, and the lock failure modes (deadlock, livelock, starvation), plus optimistic vs pessimistic locking ([[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]]).
- [ ] I can explain why ordinary JS has no *low-level* shared-memory races, what race replaces them (async interleaving at `await`), and when it still needs async mutual exclusion (`navigator.locks` / a promise queue) ([[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]).
- [ ] I can write an async concurrency limiter (the JS analog of a semaphore) and size it from the resource limit.

## Cross-Domain Fluency

- [ ] I can connect a class-level design decision to its component-architecture twin.
- [ ] I can place a contention problem at all three scales — in-process/async lock, distributed lock, client race guard — and name what changes between them (see the mapping in [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]] and [[30 - Backend System Design/10 - The Seven Access Patterns|Dealing with Contention]]).

## Related Notes

- [[31 - Low Level Design/00 - Low Level Design MOC|Low Level Design MOC]]
- [[30 - Backend System Design/00 - Backend System Design MOC|Backend System Design MOC]]
- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
