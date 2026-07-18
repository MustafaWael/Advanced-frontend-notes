---
tags: [system-design, backend, interview, moc]
module: "30 - Backend System Design"
priority: must-know
status: not-started
---

# Backend System Design MOC

In a frontend interview you treat the server as a black box ([[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]]). This module is about *understanding the box* — not to pass a distributed-systems loop, but because every good API-boundary decision, every "why is this endpoint eventually consistent," every integration you build against a backend is easier when you know what's on the other side. It also future-proofs you: mid→senior frontend roles increasingly include a general system-design round.

The throughline of the whole vault applies here too: know the *mechanism*, name the *failure mode*, pick a pattern with *tradeoffs*. Most of this is your frontend knowledge at a bigger scale — caching, contention, real-time transport, and consistency are the same ideas across the network boundary, called out in the "Frontend mirror" section of each note.

## Prerequisites

- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]] and [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]] — the client half of the networking picture.
- [[28 - Frameworks and Application Architecture/06 - Server State|Server State]] — server data as a cache; the client mirror of this module's caching note.
- [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]] — the framework this module's delivery framework is contrasted against.

## Reading Order

1. [[30 - Backend System Design/01 - The Delivery Framework|The Delivery Framework]] — Requirements → Entities → API → High-level → Deep-dives; the backend cousin of RADIO.
2. [[30 - Backend System Design/02 - Networking and Protocols|Networking and Protocols]] — TCP/UDP, HTTP, SSE/WebSockets/gRPC, load balancing.
3. [[30 - Backend System Design/03 - API Design|API Design]] — REST/GraphQL/RPC, cursor vs offset pagination, versioning.
4. [[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling and Databases]] — SQL/NoSQL families, normalization, choosing a store.
5. [[30 - Backend System Design/05 - Caching|Caching]] — cache-aside and friends, eviction, stampede, hot keys.
6. [[30 - Backend System Design/06 - Sharding and Consistent Hashing|Sharding and Consistent Hashing]] — horizontal scale and rebalancing.
7. [[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]] — the consistency spectrum, and how it maps to optimistic UI.
8. [[30 - Backend System Design/08 - Indexing and Storage Engines|Indexing and Storage Engines]] — B-Tree vs LSM, Bloom filters.
9. [[30 - Backend System Design/09 - Numbers to Know|Numbers to Know]] — 2026 hardware reality and premature scaling.
10. [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]] — the backend analog of RADIO's optimization phase.
11. [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]] — Redis/Valkey, Kafka, Elasticsearch, API Gateway, Cassandra, DynamoDB, ZooKeeper.
12. [[30 - Backend System Design/12 - Backend System Design Checklist|Backend System Design Checklist]] — active self-test.

## You're Done When

- [ ] Given a "design X" backend prompt, I open with functional + non-functional requirements and derive core entities before drawing boxes.
- [ ] I can pick a data store from access patterns and defend SQL vs NoSQL without buzzwords.
- [ ] I can introduce caching by naming the bottleneck, the pattern (cache-aside), eviction, and the invalidation/failure story — not just "add Redis."
- [ ] I can explain when to shard and why premature sharding is a mistake, with current hardware numbers.
- [ ] I can place a design on the consistency spectrum and connect eventual consistency to the frontend's optimistic-UI window.
- [ ] I can name which of the seven access patterns a given problem needs, and the tradeoffs of each solution.

## Related Notes

- [[31 - Low Level Design/00 - Low Level Design MOC|Low Level Design MOC]] — the class-level, single-process counterpart.
- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
