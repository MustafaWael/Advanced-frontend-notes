---
tags: [system-design, backend, interview, checklist]
module: "30 - Backend System Design"
priority: must-know
status: not-started
---

# Backend System Design Checklist

Active test. Mark an item complete when you can do it out loud, on a whiteboard, without the notes.

## Source Anchors

- [HelloInterview — System Design in a Hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction)

## Framework

- [ ] I open with functional + non-functional requirements and derive core entities before drawing any boxes ([[30 - Backend System Design/01 - The Delivery Framework|Delivery Framework]]).
- [ ] I derive the API one endpoint per functional requirement, and drive deep dives from the non-functional numbers.
- [ ] I can state how this maps to RADIO ([[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]]) and reallocate time for the question type.

## Networking and API

- [ ] I default to HTTP request/response and reach for SSE before WebSockets, naming the stateful-connection cost ([[30 - Backend System Design/02 - Networking and Protocols|Networking and Protocols]]).
- [ ] I can justify REST vs GraphQL vs gRPC and default to gRPC internally, REST at the edge.
- [ ] I paginate every collection and defend cursor vs offset on correctness grounds ([[30 - Backend System Design/03 - API Design|API Design]]).
- [ ] I use idempotency keys on non-idempotent writes and can explain why.

## Data and Scale

- [ ] I choose a database family from access patterns, defaulting to relational until a requirement pushes me off ([[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling]]).
- [ ] I model normalized first and denormalize a specific read path only when proven necessary, keeping the source of truth normalized.
- [ ] I introduce caching with the 5-step method and address invalidation + cache-failure fallback, not just "add Redis" ([[30 - Backend System Design/05 - Caching|Caching]]).
- [ ] I can name and solve the three cache problems: stampede (single-flight), consistency, hot keys.
- [ ] I reach for replicas and caching before sharding, and use consistent hashing + virtual nodes when I do shard ([[30 - Backend System Design/06 - Sharding and Consistent Hashing|Sharding]]).
- [ ] I do back-of-envelope math with current hardware numbers (see `verified_on` in [[30 - Backend System Design/09 - Numbers to Know|Numbers to Know]]) and reject premature sharding.

## Consistency and Patterns

- [ ] I place each feature on the consistency spectrum and connect eventual consistency to optimistic UI ([[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]]).
- [ ] I state CAP as partition-time behavior and extend it with PACELC (latency-vs-consistency when healthy), instead of the sloppy "pick 2 of 3."
- [ ] I can tune consistency with quorum and explain why R+W>N guarantees a read sees the latest write ([[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]]).
- [ ] I can identify which of the seven access patterns a prompt needs and each one's tradeoff ([[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]]).
- [ ] For each core technology I can give one line: what it is, its default job, one tradeoff ([[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]]).

## Cross-Domain Fluency

- [ ] I can explain a caching, contention, real-time, or pagination decision from *both* the server side and the client side it mirrors.
- [ ] I never use a buzzword (Kafka, sharding, eventual consistency) I can't defend with a mechanism and a tradeoff.

## Related Notes

- [[30 - Backend System Design/00 - Backend System Design MOC|Backend System Design MOC]]
- [[31 - Low Level Design/00 - Low Level Design MOC|Low Level Design MOC]]
- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
