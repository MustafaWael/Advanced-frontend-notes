# Low-Level Design in a Hurry — Introduction

**Source:** [https://www.hellointerview.com/learn/low-level-design/in-a-hurry/introduction](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/introduction)

## What LLD interviews are

Low-level design (a.k.a. Object-Oriented Design / OOD — same interview, different name) tests your ability to structure code for a self-contained problem: a Connect Four game, an elevator controller, a parking lot system. You design the classes, interfaces, and relationships that make it work.

The focus is code organization: What are the right objects? How do they interact? What methods do they expose? Can the design be extended without rewriting everything?

## LLD vs System Design

Despite similar names, they have almost nothing in common.

| | System Design | Low-Level Design |
|---|---|---|
| Scope | Architecture at scale | One feature/service's code structure |
| Medium | Whiteboard boxes & arrows (services, queues, DBs) | Classes, methods, relationships, state transitions (pseudocode) |
| Concerns | Traffic, storage, consistency, caching, sharding | Responsibilities, ownership, encapsulation, extensibility |
| Coding | None | Partial code or structured pseudocode |

Ride-sharing example: system design sketches matching/pricing/location services and data flow; LLD designs the `Trip` class, `TripState` enum, `PricingCalculator` interface, and how they collaborate (state-guarded transitions like `assign_driver` → `start_trip` → `complete_trip`/`cancel_trip`).

> "System design is the map. Low-level design is the blueprint for a building on the map."

## Modern approach (guide's philosophy)

- Composition over inheritance; simple state over deep hierarchies; pragmatism over pattern worship.
- Avoid overfitting to classical/academic OOP — learn only the patterns that actually appear in real interviews and codebases.

## Regional/format variants

- **US Big Tech:** partial real code (Java/Python/C++ style); patterns mentioned only when they naturally apply; prompts slightly more defined.
- **India/Asia:** structured pseudocode is fine; design patterns asked about more directly (expect to name them); requirements vaguer — you drive scoping.
- When in doubt, ask the recruiter what format to expect.

## Assessment rubric

1. **Problem Analysis** — extract key entities/responsibilities, ask clarifying questions, frame the problem before coding. Don't jump into code.
2. **Class Design** — right responsibilities, clean method signatures, clear ownership, clean boundaries. Weak class design makes everything downstream harder.
3. **Code Quality** — encapsulation, well-managed state, sensible composition/inheritance, separation of concerns, good naming, clean dependency direction (even in pseudocode).
4. **Extensibility & Maintainability** — expect a follow-up requirement; design should absorb it without rewrite. Reward practicality, not speculative future-proofing.
5. **Communication** — clear narrative, reason out loud, adjust when probed.

## Guide structure

Delivery Framework → Design Principles → OOP Concepts → Design Patterns → Concurrency (intro/correctness/coordination/scarcity) → Problem Breakdowns (9). Practice is essential — consuming material without applying it is the most common failure mode.
