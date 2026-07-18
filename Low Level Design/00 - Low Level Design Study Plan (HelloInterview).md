# Low-Level Design — Study Plan

> Primary source: [HelloInterview — Low-Level Design in a Hurry](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/introduction)
> Learned notes: `progress/hellointerview/`
> Sibling modules: `System Design/`, `Advanced JavaScript/`
> Target: mid-level interviews. Created 2026-07-17.

## Goal

Take a self-contained prompt (parking lot, elevator, Connect Four) and produce clean class design in pseudocode within ~35 min: scoped requirements → core entities → class design with clear responsibilities → state transitions → absorb one extensibility follow-up without a rewrite.

## How you're assessed

Five rubric themes: Problem Analysis, Class Design, Code Quality, Extensibility & Maintainability, Communication. See `progress/hellointerview/00_introduction.md`. Modern bar: composition over inheritance, simple state, pragmatism over pattern worship.

## Phase 1 — Framework & fundamentals (Week 1)

1. `00_introduction.md` — LLD vs system design, regional variants, rubric.
2. `01_delivery_framework.md` — the step structure; memorize it.
3. `02_design_principles.md` — SOLID and friends, applied not academic.
4. `03_oop_concepts.md` — encapsulation, composition vs inheritance, interfaces.
5. `04_design_patterns.md` — only the patterns that show up in interviews (Strategy, Factory, Observer, State…); know *when*, not just *what*.

**Checkpoint:** for each pattern, name one LLD problem where it's the natural fit and say why in two sentences.

## Phase 2 — Concurrency (Week 2)

`progress/hellointerview/concurrency/` — `01_introduction.md` is complete (threads, races, locks). 02–04 (Correctness, Coordination, Scarcity) are premium-locked past their problem statements; use the free problem framings as prompts and fill gaps with standard references if needed.

**Checkpoint:** explain race condition, mutex vs semaphore, and deadlock conditions from memory.

## Phase 3 — Problem practice (Weeks 2–4)

One problem per session: 35-min solo attempt (classes + methods in pseudocode), then diff against the note in `progress/hellointerview/questions/`.

Fully documented (free pages): 1. Connect Four (state machines, win-check), 2. Amazon Locker (allocation, sizing), 3. Elevator (scheduling, state), plus complete requirements for Movie Ticket Booking, Logging Service, Rate Limiter, Inventory Management (6–9).

Requirements-only (premium-locked past requirements): Parking Lot, File System, and 6–9 designs. Treat these as pure solo practice — design from the free requirements, self-review against Phase 1 principles.

**Checkpoint:** solo designs handle each breakdown's extensibility follow-up without restructuring.

## Phase 4 — Integration (Week 4+)

- Redo Connect Four, Elevator, Parking Lot cold with a timer.
- Practice narrating: scope questions first, entities second, code last.
- Cross-link with `System Design/`: same product (e.g. Rate Limiter, Ticketmaster/BookMyShow) appears in both interview types — know which lens the interviewer wants.

## Progress tracking

- [ ] Phase 1 — framework & fundamentals
- [ ] Phase 2 — concurrency
- [ ] Phase 3 — 9 problems attempted
- [ ] Phase 4 — cold redos & narration
