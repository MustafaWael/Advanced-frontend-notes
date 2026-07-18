---
tags: [system-design, backend, interview, framework]
module: "30 - Backend System Design"
priority: must-know
status: not-started
aliases: [Backend SD framework, Requirements Entities API High-level Deep-dives]
---

# The Delivery Framework

## Maturity Target

- Priority: #must-know
- Study time: 30 minutes
- Interview signal: You can structure any backend "design X" question as Requirements → Core Entities → API → High-Level Design → Deep Dives, allocate time deliberately, and keep every later decision traceable to a requirement.
- Production signal: Design docs open with goals/non-goals and a data model before any box diagram.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]]

## Source Anchors

- [HelloInterview — Delivery Framework](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)
- [HelloInterview — Core Concepts](https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts)

## 1. Concept

Simple version: the framework is the same senior instinct RADIO trains — refuse to design before requirements are explicit, then work outside-in. Only the artifacts differ.

The accurate structure, for a ~35–45 minute backend round:

| Phase | Time | What you produce |
| --- | --- | --- |
| **Requirements** | ~5 min | Functional ("what can users do") + non-functional ("how fast/available/consistent"); explicit out-of-scope |
| **Core Entities** | ~2 min | The nouns the system stores (User, Post, Booking) — the seed of the data model |
| **API** | ~5 min | The endpoints, one per functional requirement; request/response shape |
| **High-Level Design** | ~10–15 min | The box diagram: clients → gateway → services → data stores → queues; data flow for each API |
| **Deep Dives** | ~15–20 min | Requirement-driven depth: scaling, caching, consistency, the specific bottleneck |

> [!tip] Non-functional requirements are where seniority shows — the same role the Requirements phase plays in RADIO. "10M DAU, read-heavy 100:1, sub-200ms reads, eventual consistency acceptable for the feed" *is* the design brief. Every deep dive should trace back to one of these numbers.

The standard high-level shape to reach for: clients → **API gateway / load balancer** → **stateless application services** → **data stores** (primary DB + cache + search + blob) → **async workers** fed by a **queue**. You rarely need more; you often need less.

## 2. Why It Matters

The failure mode is identical to the frontend one: shapelessness. A candidate who jumps to "I'd use Kafka and Cassandra" before stating the read/write ratio is guessing. The framework forces the order that makes the rest defensible, and it's the same order a good design doc uses — so it transfers directly to your real work of writing them.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

The "bug" is a failed answer to "design a URL shortener."

Shapeless: *"I'll hash the URL to a short code, store it in a database, and redirect."* — no scale, no read/write ratio, no mention that reads dominate 100:1 (so the design is really a caching problem), no collision handling.

Fix — run the framework: *"Functionally: create short→long mapping, redirect. Non-functionally: extremely read-heavy, redirects must be <100ms, 100M URLs. Core entity: a Mapping{shortCode, longUrl, createdAt}. API: `POST /urls`, `GET /{code}`. High level: the read path is a cache-first lookup because it dominates; the write path generates a collision-free code. Deep dive: code generation (counter+base62 vs hash+dedup) and cache strategy, because those are where the requirements bite."*

Tradeoff of the framework: rigidity. A pure algorithm-flavored question (design a rate limiter) spends less time on entities and more on the one core mechanism — reallocate the minutes and say you're doing so, exactly like reallocating RADIO phases.

## 4. Interview Answer

Short answer:

> I structure backend design as requirements, core entities, API, high-level design, then deep dives. I spend the first few minutes nailing non-functional requirements — read/write ratio, latency, consistency, scale — because they decide everything downstream, and I keep each later choice traceable to one.

Deeper answer:

> The two moves that carry the interview: derive the API from the functional requirements one-to-one so nothing is missing or invented, and drive the deep dives from the non-functional numbers rather than from whatever technology I find interesting. If it's read-heavy, the deep dive is caching and read replicas; if it's write-heavy, it's sharding and queues. Naming that mapping out loud is the point. It's the same discipline as RADIO — only the artifacts change from component/network APIs to services and data stores.

## 5. Practice

1. <details><summary>Why derive the API directly from the functional requirements, one endpoint per requirement?</summary>It guarantees completeness (every capability has an endpoint) and prevents invention (no endpoint without a requirement behind it). It also makes the high-level design fall out — each endpoint's data flow is a line through the boxes.</details>
2. <details><summary>Two designs both say "10M users." One shards immediately, one doesn't. What single number resolves who's right?</summary>The data size and per-node capacity — with 2026 hardware a single machine holds multi-TB in RAM and tens of TB on disk ([[30 - Backend System Design/09 - Numbers to Know|Numbers to Know]]), so 10M modest records fit comfortably on one node. Premature sharding is the more common mistake.</details>
3. <details><summary>How does this map onto RADIO?</summary>Requirements↔Requirements, Core Entities + API↔Data model + Interface, High-Level Design↔Architecture, Deep Dives↔Optimizations. Same outside-in, requirements-first meta-skill; the backend version just draws services and stores instead of components and a network API.</details>

## Related Notes

- [[30 - Backend System Design/03 - API Design|API Design]]
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]]
- [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]]
