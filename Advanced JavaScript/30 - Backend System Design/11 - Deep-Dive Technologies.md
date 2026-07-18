---
tags: [system-design, backend, technologies, interview]
module: "30 - Backend System Design"
priority: deep-dive
status: not-started
aliases: [Redis, Valkey, Kafka, Elasticsearch, Cassandra, DynamoDB, API Gateway, ZooKeeper]
verified_on: 2026-07-17
version_scope: "Redis 8/Valkey era; Kafka 4.0 (KRaft, no ZooKeeper); check specifics before quoting"
---

# Deep-Dive Technologies

## Maturity Target

- Priority: #deep-dive
- Study time: 40 minutes
- Interview signal: For each technology, say in one line what it is, the one job it's the default for, and one tradeoff — without buzzwords you can't defend.
- Production signal: You recognize these behind the APIs you consume and can reason about their guarantees.
- Dependencies: [[30 - Backend System Design/05 - Caching|Caching]], [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]]

## Source Anchors

- [HelloInterview — Deep Dives](https://www.hellointerview.com/learn/system-design/deep-dives/redis)
- [Redis — AGPLv3 announcement](https://redis.io/blog/agplv3/) · [Valkey](https://valkey.io/) · [Apache Kafka](https://kafka.apache.org/documentation/)
- [Elasticsearch docs](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html) · [Apache Cassandra](https://cassandra.apache.org/doc/latest/) · [DynamoDB developer guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)

> [!note] Version-sensitive note — verify before quoting specifics. Managed-service defaults, consistency options, and index limits drift. Two moving facts captured 2026-07: **Redis licensing/Valkey** (below) and **Kafka dropped ZooKeeper in 4.0 (KRaft)**. Several deep-dive articles were premium-locked in the source, so entries below are framing-depth; confirm internals against docs. `status` stays `not-started` until a per-technology verification pass. (Provenance/currency caveat, not a footgun — a note, not a warning.)

## 1. Concept — one line each

- **Redis / Valkey** — in-memory data-structure store (strings, hashes, sorted sets, streams). Default for: caching, sessions, rate-limit counters, leaderboards (sorted sets), distributed locks, pub/sub. Single-threaded core, sub-ms reads. *Tradeoff:* memory-bound; durability is opt-in. **Licensing (verify):** Redis moved off BSD to a dual RSALv2/SSPLv1 source-available license (March 2024, from Redis 7.4), which triggered the **Valkey** fork (BSD-3, a **Linux Foundation** project — not CNCF — forked from Redis 7.2.4, backed by AWS, Google, Oracle, Snap); Redis 8 (May 2025) added AGPLv3 as an OSI-approved open-source option. Valkey is widely offered by managed cloud services (often the "Redis-compatible" engine on AWS/GCP), so in an interview say "Redis-compatible" rather than assuming one vendor.
- **Kafka** — distributed, durable, append-only commit log; topics split into partitions, ordered within a partition, consumed by consumer groups. Default for: event streaming, decoupling producers/consumers, fan-out, buffering write spikes ([[30 - Backend System Design/10 - The Seven Access Patterns|Scaling Writes / Multi-step]]). *Tradeoff:* operational weight; ordering only within a partition. **Verify:** Kafka 4.0 (March 2025) removed ZooKeeper — clusters now use built-in **KRaft** (Raft) for metadata.
- **Elasticsearch** — distributed search over an **inverted index**; full-text, fuzzy, aggregations. Default for: search, log/observability analytics. *Tradeoff:* **near-real-time** (refresh interval → eventual consistency), not a system of record.
- **API Gateway** — the single front door: routing, auth, TLS termination, rate limiting, request shaping. The backend cousin of a frontend BFF. *Tradeoff:* a potential bottleneck/SPOF if not scaled.
- **Cassandra** — wide-column, LSM-tree, masterless. Default for: write-heavy, always-on, query-driven data (you model one table per query; no joins). Tunable consistency. *Tradeoff:* rigid access patterns, no ad-hoc queries.
- **DynamoDB** — managed key-value/document; partition + sort key; GSIs; tunable read consistency; pay-per-capacity. Default for: predictable-access, high-scale, low-ops key lookups. *Tradeoff:* modeling around keys; cost surprises at scale.
- **PostgreSQL** — the relational default: ACID, joins, JSON, extensions, mature. Default for: almost any transactional workload until a specific requirement pushes you off. *Tradeoff:* horizontal write scaling needs extra work (partitioning/sharding).
- **ZooKeeper** — distributed coordination: leader election, config, distributed locks (the distributed sibling of an in-process lock, [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]]). *Tradeoff:* one more system to run — and increasingly designed out (Kafka's KRaft).

## 2. Why It Matters

You integrate against these constantly without naming them: your search box is Elasticsearch (hence the brief indexing delay), your notifications ride Kafka fan-out, your rate limiter is a Redis counter, your requests pass an API gateway. Naming the technology tells you its guarantees — and lets you have a precise conversation with backend teammates instead of "the API is slow."

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an in-app notification feed occasionally shows events out of order — a "your order shipped" appears above "your order was placed." Notifications ride a Kafka topic; the backend team insists Kafka "guarantees ordering."

Trace: Kafka guarantees ordering **only within a partition**, not across a topic. The producer keyed messages by a random id, so a single user's events landed on different partitions and were consumed in parallel with no cross-partition order. The client rendered them in arrival order, exposing the reordering.

Fix: key the producer by `userId` (or `orderId`) so all of one entity's events hash to the same partition and stay ordered end-to-end; on the client, still render by a server `seq`/timestamp as defense in depth ([[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]]). Understanding the guarantee ("ordered within a partition, keyed to make it useful") is what lets a frontend engineer diagnose this instead of filing it as a mystery race.

Tradeoff: keying by `userId` concentrates a hot user's traffic on one partition (a hot-partition risk), and strict ordering caps that entity's parallelism — the standard ordering-vs-throughput tension.

## 4. Interview Answer

Short answer:

> I default to Postgres for transactional data, Redis (or a Redis-compatible store like Valkey) for caching and counters, Kafka for durable event streaming and decoupling, and Elasticsearch for search — knowing search is near-real-time because it's an inverted index. Cassandra and DynamoDB are for write-heavy, query-driven, high-scale key access where I model tables around the queries. An API gateway fronts it all for routing, auth, and rate limiting.

Deeper answer:

> Name the tradeoff, not the logo: Redis is memory-bound with opt-in durability; Kafka gives ordering only within a partition and, as of 4.0, runs on KRaft with no ZooKeeper; Elasticsearch is eventually consistent by refresh interval, so it's a search layer, not a source of truth; Cassandra buys write throughput by giving up joins and ad-hoc queries. And a small currency point that signals I stay current: "Redis" now spans the 2024 license change and the Valkey fork, so I say Redis-compatible.

## 5. Practice

1. <details><summary>Why is Elasticsearch a search layer and not your system of record?</summary>It's an inverted index that's near-real-time — writes become searchable after a refresh interval, so it's eventually consistent and optimized for query, not for durable transactional truth. Keep the source of truth in a transactional DB and index into Elasticsearch for search.</details>
2. <details><summary>What does "Redis-compatible" signal, and why say it?</summary>After Redis's 2024 license change (BSD → dual RSALv2/SSPLv1), the Valkey fork (BSD-3, a Linux Foundation project, AWS/Google/Oracle-backed) became a widely-offered managed engine on major clouds; Redis 8 (May 2025) later added an OSI-approved AGPLv3 option. Saying "Redis-compatible" shows you know the ecosystem split rather than assuming one vendor.</details>
3. <details><summary>Kafka gives ordering guarantees at what granularity, and why does that matter?</summary>Order is guaranteed only *within a partition*, not across a topic. So anything requiring ordered processing (a user's events) must be keyed to land on the same partition. Cross-partition ordering doesn't exist — a common design constraint.</details>

## Related Notes

- [[30 - Backend System Design/05 - Caching|Caching]] (Redis)
- [[30 - Backend System Design/08 - Indexing and Storage Engines|Indexing and Storage Engines]] (Elasticsearch, Cassandra/LSM)
- [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]] (ZooKeeper = distributed lock)
