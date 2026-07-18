---
tags: [system-design, backend, databases, interview]
module: "30 - Backend System Design"
priority: important
status: not-started
aliases: [SQL vs NoSQL, normalization, choosing a database]
---

# Data Modeling and Databases

## Maturity Target

- Priority: #important
- Study time: 40 minutes
- Interview signal: Choose a database family from access patterns, not fashion; explain normalization vs denormalization and when to break normal form.
- Production signal: You can read why an API is eventually consistent or shaped oddly from the store behind it.
- Dependencies: [[30 - Backend System Design/01 - The Delivery Framework|The Delivery Framework]], [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]

## Source Anchors

- [HelloInterview — Core Concepts (Database)](https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts)
- [PostgreSQL docs](https://www.postgresql.org/docs/)
- [Use The Index, Luke — data modeling & indexing](https://use-the-index-luke.com/)

## 1. Concept

Simple version: pick the store whose natural access pattern matches how you'll read and write, then model for those queries.

Database families and what each is *for*:

- **Relational (SQL)** — Postgres/MySQL. ACID transactions, joins, strong consistency, flexible ad-hoc queries. The correct default until a specific requirement pushes you off it.
- **Document** — MongoDB. Schema-flexible JSON documents; good when data is naturally hierarchical and read as a unit.
- **Key-Value** — Redis/DynamoDB. O(1) get/put by key; caches, sessions, simple high-scale lookups.
- **Wide-Column** — Cassandra. Query-driven modeling (you design tables per query), massive write throughput, tunable consistency, no joins.
- **Graph** — Neo4j. When relationships *are* the query (social graphs, recommendations).

**Normalization vs denormalization:**

- *Normalized* — each fact stored once (a username lives only in `users`). Prevents update anomalies; joins reassemble data at read time.
- *Denormalized* — duplicate facts for read speed (copy `username` into every `post` row). Fast reads, but a rename must update every copy or the data goes inconsistent.
- Rule: **start normalized, denormalize only when a read pattern demands it** — analytics, audit logs, read-optimized search. Even then, keep the normalized source of truth and put a **denormalized cache** (pre-computed joins) in front.

> [!tip] Frontend mirror: this is exactly the client store decision. A normalized client cache (entities keyed by id) mirrors a normalized DB; a denormalized view model mirrors a read-optimized projection. Same tradeoff — write-side consistency vs read-side speed — see [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]].

## 2. Why It Matters

"SQL vs NoSQL" is a common trap answered with buzzwords. The better answer derives the choice from access patterns and consistency needs. And most designs don't need NoSQL — modern Postgres scales far further than folklore suggests ([[30 - Backend System Design/09 - Numbers to Know|Numbers to Know]]).

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a dashboard shows a user's display name next to every one of their thousands of activity rows. A rename updates the profile but the activity list keeps showing the old name for minutes.

Trace: the activity store denormalized `displayName` into each row for fast reads. The rename updated the `users` record (source of truth) but not the copies — a denormalization consistency bug, the backend twin of copying server data into local `useState` on the client ([[28 - Frameworks and Application Architecture/06 - Server State|Server State]]).

Fix options with tradeoffs: (a) keep activity rows normalized (`userId` only) and join/lookup the name at read time — always correct, costs a join/lookup per read; (b) keep the denormalized copy but invalidate/rewrite it on rename — fast reads, and you now own a cache-invalidation problem; (c) accept eventual consistency with a short TTL if a few minutes of staleness is fine. There is no free option — you're choosing which cost to pay.

## 4. Interview Answer

Short answer:

> Default to a relational database for its transactions, joins, and flexible queries, and only move to a specialized store when a concrete requirement demands it — key-value for O(1) high-scale lookups, wide-column for write-heavy query-driven access, graph when relationships are the query. Model normalized first and denormalize a specific read path only when it's proven too slow, keeping the normalized data as the source of truth.

Deeper answer:

> Denormalization is really "an inline cache," so it inherits cache problems — invalidation and staleness. That's why the disciplined pattern is normalized source of truth plus a denormalized projection (materialized view or cache) that you invalidate deliberately, rather than scattering duplicated fields you have to keep in sync by hand. Wide-column stores like Cassandra invert the usual order — you design one table per query because there are no joins — which is the clearest example of "model for your access patterns."

## 5. Practice

1. <details><summary>Give a concrete case where denormalization is the right call despite the consistency cost.</summary>A read-heavy feed or analytics view where the source data changes rarely and read latency dominates — precompute the joined/aggregated shape, serve it fast, and refresh on write or on a short TTL. The duplicated data's staleness window is acceptable because the underlying facts are stable.</details>
2. <details><summary>Why is "just use NoSQL, it scales" a weak answer?</summary>It skips the access-pattern analysis and ignores that a single modern relational node handles very large workloads. NoSQL trades away joins, ad-hoc queries, and often strong consistency; you should only take that trade for a specific pattern (massive writes, O(1) key access), not as a default.</details>
3. <details><summary>How does DB normalization map to client-side state?</summary>Normalized DB (one fact, one place) ↔ normalized client store (entities by id, components reference ids); denormalized DB projection ↔ derived/memoized view models. Both pay write-side sync cost for read-side speed; the frontend just does it in memory per session.</details>

## Related Notes

- [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]
- [[30 - Backend System Design/05 - Caching|Caching]]
- [[30 - Backend System Design/08 - Indexing and Storage Engines|Indexing and Storage Engines]]
