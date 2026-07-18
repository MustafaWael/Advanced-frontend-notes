# Sharding

**Source:** [hellointerview.com — Sharding](https://www.hellointerview.com/learn/system-design/core-concepts/sharding)

As traffic and data grow, you first scale vertically (bigger instance: more CPU/memory/storage). Eventually you hit the ceiling of a single machine — queries slow, writes bottleneck, storage caps out (even Amazon Aurora maxes around **256 TiB**). Then the only real option is to **split data across multiple machines: sharding**.

Terminology: "partitioning" usually means splitting data within a single DB instance; "sharding" means splitting across machines. Engineers use the terms loosely — just be clear whether data lives on one machine or many.

## Partitioning (within one instance)

Splitting a large table into smaller pieces inside one database. Example: an orders table with 500M rows / 2 TB — queries for last month scan the whole table, indexes get huge, maintenance (vacuum/analyze/index rebuilds) can lock the table. Partitioning divides it into logical pieces the DB manages separately; a "last month" query scans only the relevant partition.

- **Horizontal partitioning:** split rows (e.g., one partition per year of orders) — same columns, fewer rows each.
- **Vertical partitioning:** split columns (frequently accessed columns in one partition, large/rarely used in another) — same rows, fewer columns each.

## What is Sharding?

Sharding = horizontal partitioning **across multiple machines**. Each shard is a standalone database with its own CPU, memory, storage, and connection pool; together the shards hold the full dataset. Storage and read/write throughput scale as you add shards. New problems: choosing a shard key, routing queries, avoiding hotspots, rebalancing.

## How to Shard Your Data

Two decisions: **what to shard by** (the key that groups data) and **how to distribute it** (the rule assigning groups to shards).

### Choosing Your Shard Key

A bad key → uneven distribution, hot spots, scatter-gather queries. A good shard key has:

- **High cardinality:** many unique values (a boolean key caps you at 2 shards; user ID over millions of users works).
- **Even distribution:** country fails if 90% of users are in the US; user ID distributes well; creation timestamps can pile writes onto the newest shard.
- **Query alignment:** common queries should hit one shard (shard users by user_id → "get profile"/"get user's orders" are single-shard).

Good examples:
- 🟢 **user_id** for a user-centric app — high cardinality, even, queries scoped per user.
- 🟢 **order_id** for e-commerce orders — high cardinality, per-order queries, even over time.

Bad examples:
- 🔴 **is_premium** (boolean) — two shards max, likely imbalanced.
- 🔴 **created_at** for a growing table — all new writes hit the latest shard (write hot spot).

### Sharding Strategies

#### Range-Based Sharding

Continuous value ranges per shard (e.g., user IDs 1–1M → shard 1, 1M–2M → shard 2, ...). Simple; efficient range scans (IDs 500K–600K hit one shard). But real access patterns rarely distribute evenly — sharding orders by created_at puts nearly all traffic and all writes on the newest shard. Best fit: **multi-tenant systems** where each tenant queries its own ID range (SaaS clients each owning a range).

#### Hash-Based Sharding (Default)

`shard = hash(key) % N`. Hashing scrambles values → even distribution. Downside: changing shard count (4 → 5) remaps almost every record → massive data movement. **Consistent hashing** fixes this by minimizing movement on add/remove (see the Consistent Hashing note). This is the default strategy and what interviewers assume unless you say otherwise.

#### Directory-Based Sharding

A lookup table/service maps each key to a shard (`User 15 → Shard 1`). Maximum flexibility: move hot users to dedicated shards, rebalance by editing the mapping, arbitrary logic. Costs: a lookup on every request (latency) and the directory becomes a critical dependency / single point of failure. Rarely the right interview answer — it invites derailing follow-ups. Most systems start hash- or range-based.

## Challenges of Sharding

### Hot Spots and Load Imbalance

One shard handles disproportionate traffic, negating sharding's benefit.

- **Celebrity problem:** shard by user_id and Taylor Swift's shard gets 1000x traffic; hashing doesn't help because the *key itself* is hot.
- **Time-based hot spots:** shard by creation date → newest shard takes all writes.
- Detect via shard metrics: query latency, CPU, request volume.

Handling:
- **Isolate hot keys to dedicated shards** (where directory-based mapping helps for specific cases).
- **Compound shard keys:** e.g., `hash(user_id + date)` spreads one user's data across shards over time.
- **Dynamic shard splitting:** MongoDB's balancer auto-splits and migrates chunks (including hashed shard keys); Vitess supports online resharding but operator-driven, not automatic.

### Cross-Shard Operations

Queries misaligned with the shard key must fan out. "Get user 12345's profile" → 1 shard. "Top 10 posts globally" over 64 shards → 64 queries, 64 responses to merge → 64x network calls and latency.

Minimize:
- **Cache results:** cache "top 10 posts" for 5 minutes — first query expensive, next thousand hit cache. Great where eventual consistency is fine: leaderboards, trending, aggregate stats.
- **Denormalize** related data onto the same shard (duplicates data, complicates updates, but enables single-shard reads).
- **Accept the hit for rare queries:** an admin "total users" dashboard loaded a few times a day can be slow.

Interview signal: saying "we'll query all shards and aggregate" for a *common* use case means rethink — denormalize? cache? precompute with a background job?

### Maintaining Consistency

Single-DB transactions are easy (ACID). Across shards, atomicity breaks. The textbook fix is **two-phase commit (2PC)** — coordinator asks all shards to prepare, then commit — but it's slow and fragile (a mid-transaction failure can wedge the system); most production systems avoid it.

Instead:
- **Design to avoid cross-shard transactions** (best): keep all of a user's data (balance, history, profile) on one shard → all transactions single-shard.
- **Sagas** for unavoidable multi-shard operations: a sequence of independent steps each with a compensating action. Money transfer across shards: (1) deduct from A on shard 1, (2) add to B on shard 2, (3) if step 2 fails, refund A. Eventual consistency without 2PC fragility.
- **Accept eventual consistency:** denormalized follower counts differing across shards for a few seconds is fine; they converge.

TLDR: if you constantly need distributed transactions, you probably chose the wrong shard key/boundaries.

## Sharding in Modern Databases

You probably won't implement sharding yourself. NoSQL stores take a partition key and handle distribution — but mechanisms differ:

- **Cassandra:** partitioner (e.g., Murmur3Partitioner) with virtual nodes — a form of consistent hashing mapping keys to token ranges.
- **DynamoDB:** hashes the partition key to internal partitions, splits/merges partitions as they grow — not classic user-exposed ring hashing.
- **MongoDB:** range-based chunks on the shard key (ranges over hash space if hashed key); a background balancer splits/migrates chunks — not classic consistent hashing.

SQL: **Vitess** and **Citus** are open-source sharding layers over MySQL/PostgreSQL handling routing, cross-shard ops, and resharding; AWS Aurora and Google Cloud Spanner offer distributed SQL with built-in sharding. In interviews it's enough to say "DynamoDB with user_id as partition key" or "shard with Vitess on user_id, plan operator-driven online resharding."

## Sharding in System Design Interviews

### When to Mention It

Don't shard prematurely — the #1 sharding mistake is introducing it before proving it's necessary. Bring it up during capacity planning when you hit a limit:

- **Storage:** "500M users × 5KB = 2.5TB. A single Postgres handles that, but at 10x growth we'd shard."
- **Write throughput:** "50K writes/sec peak — a single database will struggle; we should shard."
- **Read throughput:** "Even with read replicas, 100M DAU × multiple queries each needs distributed read load."

Formula: identify the bottleneck → explain why one DB won't scale → propose sharding. Use Numbers to Know for realistic single-DB limits.

### What to Say (social media example)

1. **Shard key from access patterns:** "Feeds query a user's posts/followers/likes — all user-scoped. Shard by user_id."
2. **Distribution strategy:** "Hash-based with consistent hashing for even distribution."
3. **Tradeoffs:** "Global queries (trending posts) get expensive — cache trending content and precompute with a background job."
4. **Growth:** "Start with 64 shards; consistent hashing means adding shards moves only a fraction of data."

## Conclusion

Sharding = splitting data across machines when one database can't handle scale. Two decisions matter: a shard key aligned with query patterns, and a distribution strategy that spreads load evenly. Get them wrong → hot spots and expensive cross-shard queries. Don't shard early — a well-tuned single database gets surprisingly far.
