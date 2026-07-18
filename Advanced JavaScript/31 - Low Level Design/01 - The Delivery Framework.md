---
tags: [low-level-design, interview, framework]
module: "31 - Low Level Design"
priority: must-know
status: not-started
aliases: [LLD framework, class design framework]
---

# The Delivery Framework

## Maturity Target

- Priority: #must-know
- Study time: 25 minutes
- Interview signal: Structure an LLD prompt as Requirements → Entities → Class Design → Implementation → Extensibility, deriving state and behavior from requirements rather than inventing classes.
- Production signal: You design a feature's types and boundaries before writing methods.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[30 - Backend System Design/01 - The Delivery Framework|BE Delivery Framework]]

## Source Anchors

- [HelloInterview — LLD Delivery Framework](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/delivery)

## 1. Concept

Simple version: same requirements-first instinct as RADIO and the backend framework, aimed at classes instead of services.

| Phase | Time | What you produce |
| --- | --- | --- |
| **Requirements** | ~5 min | Functional (what it does) + constraints; explicit out-of-scope |
| **Entities & Relationships** | ~3 min | The core nouns and how they relate (has-a, is-a, uses) |
| **Class Design** | ~10–15 min | Each class's **state** (fields) and **behavior** (methods), derived from requirements |
| **Implementation** | ~10 min | Fill in key methods; walk a concrete scenario end to end |
| **Extensibility** | ~5 min | How a likely new requirement slots in without rewrites |

The core move: **derive state and behavior from requirements.** "Users can reserve a spot" → a `reserve()` behavior and a `status` field; "spots have sizes" → a `size` field and size-matching logic. Don't start from a class diagram; start from what the system must *do*.

> [!tip] "Walk a specific scenario" in Implementation is the LLD analog of tracing code line by line elsewhere in the vault — pick "a car arrives and parks," and follow the method calls object to object. It surfaces missing methods and muddled responsibilities immediately.

## 2. Why It Matters

The failure mode is designing classes in a vacuum — a `ParkingLotManager` god-object with twenty methods, or inheritance trees nobody needs. Deriving from requirements keeps classes cohesive (each has a reason to exist) and is the same discipline as deriving a backend API from functional requirements. It's also how you actually design a non-trivial frontend feature: model the domain types first, then the component behavior.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario (framed as design critique): asked to design an elevator system, a candidate opens with a `System` class holding every field and method — request handling, movement, door logic, scheduling — all in one.

Trace: no requirements-to-entity derivation happened, so responsibilities never separated (an SRP violation, [[31 - Low Level Design/02 - Design Principles|Design Principles]]). The single class is untestable and every change touches everything — the OOP version of a 500-line React component that fetches, transforms, and renders.

Fix: derive entities from requirements — `Elevator` (state: currentFloor, direction, doorState), `Request` (origin, destination), `Scheduler` (behavior: assign a request to an elevator). Walk "request from floor 5" through them to confirm each object owns one job.

Tradeoff: more classes means more files/indirection; for a tiny prompt that's over-engineering (YAGNI). Match granularity to the requirements' actual complexity — the same judgment as when to split a component.

## 4. Interview Answer

Short answer:

> I structure LLD as requirements, entities and relationships, class design, implementation, then extensibility. The key discipline is deriving each class's state and behavior directly from the requirements rather than starting from a diagram, and walking a concrete scenario through the objects to verify responsibilities are clean.

Deeper answer:

> The requirements-to-behavior derivation is what keeps classes cohesive: every field and method traces to a stated need, so I avoid god-objects and speculative inheritance. Walking a specific scenario during implementation is my verification step — it exposes a missing method or a class doing two jobs faster than staring at a diagram. Extensibility at the end is deliberately last: I design for the requirements I have and show one clean extension point, rather than building for imagined futures, which is just YAGNI.

## 5. Practice

1. <details><summary>Why derive class state and behavior from requirements instead of drawing a class diagram first?</summary>It guarantees cohesion — every field/method exists for a stated reason — and prevents god-objects and speculative structure. The diagram falls out of the derivation; done the other way, you invent classes and then hunt for responsibilities to justify them.</details>
2. <details><summary>What does "walk a specific scenario" catch that a static design doesn't?</summary>Missing methods, unclear ownership, and objects reaching into each other's internals. Following "a car parks" call-by-call reveals whether responsibilities are actually clean, the same way tracing execution reveals a bug a diagram hides.</details>
3. <details><summary>How is this the same skill as designing a frontend feature?</summary>You model the domain types and their relationships first, then derive component state and behavior from requirements, then walk a user flow through them. God-object LLD is the twin of the do-everything component; requirements-first derivation prevents both.</details>

## Related Notes

- [[31 - Low Level Design/02 - Design Principles|Design Principles]]
- [[30 - Backend System Design/01 - The Delivery Framework|Backend Delivery Framework]]
- [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]]
