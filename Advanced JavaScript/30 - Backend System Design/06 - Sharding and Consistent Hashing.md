---
tags: [system-design, backend, scaling, interview]
module: "30 - Backend System Design"
priority: important
status: not-started
aliases: [sharding, partitioning, consistent hashing, virtual nodes]
---

# Sharding and Consistent Hashing

## Maturity Target

- Priority: #important
- Study time: 35 minutes
- Interview signal: Explain when to shard, the three strategies (hash / range / directory) and their tradeoffs, how to choose a shard key, the problems sharding creates, and why consistent hashing beats modulo hashing for rebalancing.
- Production signal: You don't propose sharding before it's needed and can name the cross-shard costs.
- Dependencies: [[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling and Databases]], [[30 - Backend System Design/09 - Numbers to Know|Numbers to Know]]

## Source Anchors

- [HelloInterview — Sharding](https://www.hellointerview.com/learn/system-design/core-concepts/sharding)
- [HelloInterview — Consistent Hashing](https://www.hellointerview.com/learn/system-design/core-concepts/consistent-hashing)

## 1. Concept

Simple version: when one machine can't hold or serve the data, split it across many. A common distinction: **partitioning** divides data within one instance (e.g. Postgres table partitions), **sharding** spreads it across separate instances, each owning a subset — though terminology varies (Cassandra calls its shards "partitions"), so define your terms in an interview.

**Three ways to assign data to shards:**
- **Hash-based** — `shard = hash(key)`, ideally via consistent hashing (below). Spreads load evenly and makes point lookups trivial, but *destroys range queries* (adjacent keys scatter) and you can't easily add capacity with naive modulo. The default for key-value/point-access workloads (DynamoDB, Cassandra).
- **Range-based** — contiguous key ranges per shard (`A–F`, `G–M`, …, or time ranges). Keeps range scans and "recent items" queries fast, but is prone to **hot tails**: monotonically increasing keys (timestamps, auto-increment ids) send all new writes to one shard. Used by HBase, Bigtable, Spanner.
- **Directory / lookup-based** — a lookup service maps key → shard explicitly. Maximum flexibility (rebalance by editing the map, mix strategies) at the cost of a lookup hop and a directory that's itself a scaling/availability concern.

**Choosing a shard key** is the whole game: it must (a) spread load evenly and (b) match your access pattern so common queries hit one shard. Shard users by `userId` and "get my data" is single-shard; shard by `region` and one hot region overloads a shard.

**Problems sharding creates:**
- **Hot spots** — a bad key concentrates load (celebrity user, popular region).
- **Cross-shard operations** — a query spanning shards (global search, join across users) is slow: scatter-gather across nodes.
- **Cross-shard consistency** — a transaction touching two shards needs distributed coordination.

**Consistent hashing** solves *rebalancing*. Naive modulo hashing (`shard = hash(key) % N`) remaps almost every key when `N` changes (add one node → nearly all data moves). Consistent hashing places nodes and keys on a ring; a key belongs to the next node clockwise. Add/remove a node and only ~`1/N` of keys move — the keys between the new node and its predecessor. **Virtual nodes** (each physical node placed at many ring positions) smooth out uneven distribution and hot spots.

Walk it on a 12-position ring. Place three nodes: **A@2, B@5, C@9**. A key hashes to a position, then travels clockwise to the first node it meets:

```text
ring:  0 1 [2=A] 3 4 [5=B] 6 7 8 [9=C] 10 11 →(wraps to 0)
key k1→pos 3  ⇒ next node clockwise = B
key k2→pos 8  ⇒ next node clockwise = C
key k3→pos 11 ⇒ wraps past 0,1 to A
key k4→pos 5  ⇒ B (lands on it)

Now add node D@7:
key k2→pos 8 ⇒ still C (8→9), unchanged
key at pos 6 ⇒ was C, now D   ← only keys in segment (5, 7] move
everything else stays on the same node.
```

Adding D only steals the arc between B(5) and D(7) — the keys in `(5,7]` move from C to D; k1, k3, k4 don't budge. That's the "~1/N keys move" property: contrast modulo, where changing N reshuffles nearly everything. **Virtual nodes** mean A also sits at, say, positions 2, 14, 21, 30… on a larger ring, so a handful of physical nodes still spread evenly and losing one node scatters its load across many others instead of dumping it all on a single neighbor.

> [!warning] Premature sharding is a top interview mistake. With current hardware a single node holds multi-TB in RAM and tens of TB on disk ([[30 - Backend System Design/09 - Numbers to Know|Numbers to Know]]) — most "10M users" designs fit on one machine with read replicas. Reach for replicas and caching first; shard only when a single node genuinely can't cope. Sharding adds cross-shard cost to *every* future query.

> [!tip] Frontend mirror: the same "assign items to buckets so lookups stay cheap" logic runs on the client. **Hash-based** ↔ a normalized entity store keyed by id (`{[id]: entity}`) for O(1) point access — the client's shard key is the id ([[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization]]). **Range-based** ↔ route- or date-bucketed code-splitting and windowed list ranges. And the **hot-tail** problem has a direct UI twin: an infinite feed keyed by insertion order gets all its churn at the top, which is exactly why the client reaches for cursor pagination ([[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Infinite Scroll Feed]]).

## 2. Why It Matters

Sharding is the classic "sounds senior, usually wrong" lever. Knowing the *cost* it imposes (cross-shard queries and consistency) and the *cheaper alternatives first* (replicas, cache) is the mature signal. Consistent hashing is the specific mechanism that makes distributed caches and databases (Cassandra, DynamoDB) rebalance without mass data movement — a strong differentiator to name.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario (framed as a design critique): a chat backend shards messages by `hash(messageId) % N`. Traffic grows, they add a node, and the cache/DB effectively cold-starts — latency spikes for hours.

Trace: modulo hashing. Changing `N` from 4 to 5 changes `messageId % N` for ~80% of keys, so almost all data is now "on the wrong node," forcing mass migration / cache repopulation — a self-inflicted thundering-herd against the origin.

Fix: consistent hashing with virtual nodes. Adding the fifth node only steals the ring segment between it and its predecessor — ~1/5 of keys move, the rest stay put, and the cache stays mostly warm.

Tradeoff: consistent hashing is more complex (ring management, virtual-node bookkeeping) and range queries across the ring are still awkward. It buys smooth scaling, not query flexibility.

## 4. Interview Answer

Short answer:

> Shard only when a single node can't hold or serve the data — with modern hardware that's later than people think, so I reach for read replicas and caching first. When I do shard, the shard key must spread load and keep common queries single-shard, and I use consistent hashing with virtual nodes so adding or removing a node moves only about 1/N of the data instead of remapping everything the way modulo hashing does.

Deeper answer:

> The costs sharding imposes are the real content: cross-shard queries become scatter-gather, cross-shard writes need distributed transactions or careful idempotency, and a poor shard key creates hot spots that defeat the whole point. Consistent hashing is specifically about the rebalancing failure of modulo hashing — it localizes data movement to one ring segment, which is why distributed caches and Cassandra/DynamoDB use it. Virtual nodes exist because a few physical nodes on a bare ring distribute unevenly; scattering each node across many ring positions evens the load.

## 5. Practice

1. <details><summary>Why does modulo hashing fall apart when you add a node, and how does consistent hashing fix it?</summary>`hash(key) % N` depends on N, so changing N changes the target shard for almost every key → mass migration. Consistent hashing maps keys and nodes onto a ring; a new node only takes over the segment between it and its predecessor, so only ~1/N of keys relocate.</details>
2. <details><summary>You must shard a social app. What makes a good shard key here?</summary>Usually `userId` — most queries are "this user's data," which stays single-shard, and users spread load evenly. Avoid keys that concentrate (region, or anything correlated with celebrity/hot entities) since those create hot-spot shards.</details>
3. <details><summary>Name the cheaper scaling levers to exhaust before sharding.</summary>Vertical scale (bigger box — modern nodes are huge), read replicas for read-heavy load, and caching hot data. Sharding is last because it taxes every future cross-shard query and complicates consistency permanently.</details>

## Related Notes

- [[30 - Backend System Design/09 - Numbers to Know|Numbers to Know]]
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]] (Scaling Writes)
- [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]] (Cassandra, DynamoDB)
