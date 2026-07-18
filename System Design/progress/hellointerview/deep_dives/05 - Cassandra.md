# Cassandra

**Source:** https://www.hellointerview.com/learn/system-design/deep-dives/cassandra

## What Is Cassandra?

Apache Cassandra is an **open-source, distributed NoSQL database** implementing a **partitioned wide-column storage model with eventually consistent semantics**. It was originally built by Facebook to scale inbox search, and combines ideas from Amazon's Dynamo (partitioning, replication, eventual consistency) and Google's Bigtable (wide-column storage). It runs as a cluster of commodity machines and scales horizontally. Used at scale by Discord, Netflix, Apple, and Bloomberg.

## Data Model

- **Keyspace** — Top-level unit, equivalent to a "database" in Postgres/MySQL. Defines replication strategy and owns user-defined types (UDTs).
- **Table** — Lives in a keyspace, organizes rows, has a schema defining columns and primary key structure.
- **Row** — A single record, uniquely identified by a primary key.
- **Column** — The actual storage unit (name + type + value). Cassandra is a **wide-column database**: columns can vary per row (no NULL entries required for missing columns), making it more flexible than a relational table. Every column carries a **write timestamp**; conflicting writes between replicas are resolved via **last write wins**.

You can loosely picture Cassandra's data as a big nested JSON: keyspace → table → row → columns. Columns support many types including UDTs and JSON values, so it handles both flat and nested data.

### Primary Key

Every row is uniquely identified by a primary key, which consists of:

- **Partition Key** — one or more columns that determine **which partition (and therefore which node)** the row lives on.
- **Clustering Key** — zero or more columns that determine the **sort order of rows within a partition**.

Examples in CQL:

```sql
-- Partition key a, no clustering keys
CREATE TABLE t (a text, b text, c text, PRIMARY KEY (a));

-- Partition key a, clustering key b ascending
CREATE TABLE t (a text, b text, c text, PRIMARY KEY ((a), b))
WITH CLUSTERING ORDER BY (b ASC);

-- Composite partition key a + b, clustering key c
CREATE TABLE t (a text, b text, c text, d text, PRIMARY KEY ((a, b), c));

-- Partition key a, clustering keys b + c
CREATE TABLE t (a text, b text, c text, d text, PRIMARY KEY ((a), b, c));
```

This concept maps essentially 1:1 to DynamoDB's partition key + sort key.

## Key Concepts (Internals)

### Partitioning — Consistent Hashing

Cassandra partitions data across nodes using **consistent hashing**. Naive hashing (`hash(value) % num_nodes`) has two problems: adding/removing a node remaps most data, and unlucky distributions overload some nodes.

Consistent hashing instead hashes values onto a **ring** of integers. A value is stored on the first node found walking clockwise from its hash position. When a node joins or leaves, only data on the adjacent segment of the ring moves.

To fix uneven load, Cassandra maps **many virtual nodes (vnodes)** onto the ring, each owned by a physical node. This spreads load evenly and lets bigger machines own more vnodes.

### Replication

Partitions are replicated to multiple nodes: Cassandra hashes a value to a vnode, then scans clockwise to pick additional replicas, **skipping vnodes that live on the same physical node** so one machine failure doesn't take out multiple replicas.

Two replication strategies (configured per keyspace):

- **NetworkTopologyStrategy** — production-recommended; data center and rack aware, so replicas are physically separated across DCs/racks to survive real-world outages.
- **SimpleStrategy** — plain clockwise scan; useful for simple deployments and testing.

```sql
ALTER KEYSPACE hello_interview WITH REPLICATION =
  { 'class' : 'SimpleStrategy', 'replication_factor' : 3 };

ALTER KEYSPACE hello_interview WITH REPLICATION =
  { 'class' : 'NetworkTopologyStrategy', 'dc1' : 3, 'dc2' : 2 };
```

### Consistency (Tunable)

Cassandra lets you **tune the consistency vs. availability trade-off** via per-read/per-write **consistency levels** — the number of replica responses required — from `ONE` to `ALL`.

- **No transactions / ACID guarantees.** Only atomic and isolated writes at the row level within a partition.
- **QUORUM** = majority (n/2 + 1) of replicas. Using QUORUM for both reads and writes guarantees reads see writes, because at least one node overlaps between any write set and read set (e.g., with 3 replicas, writes and reads each touch 2 nodes, so they must share one).
- Baseline behavior at all levels is **eventual consistency** — all replicas converge given enough time.

### Query Routing

**Any node can act as coordinator** for a client query. Nodes know cluster state via gossip and can compute where data lives (consistent hashing + replication config), so the coordinator forwards the query to the replica nodes holding the data. No single point of failure.

### Storage Model — LSM Tree

Cassandra is **write-optimized** via a **Log-Structured Merge (LSM) tree** instead of the B-tree used by most databases. Every create/update/delete is a new append-style entry; row state is derived from the ordering of entries. Deletes are written as **tombstones**.

Three core structures:

1. **Commit Log** — write-ahead log for durability.
2. **Memtable** — in-memory structure sorted by primary key, holding recent writes.
3. **SSTable** ("Sorted String Table") — immutable on-disk file flushed from a Memtable.

Write path: write → commit log → Memtable → (on size/time threshold) flush to immutable SSTable → corresponding commit log entries purged.

Read path: check Memtable first (latest data); if absent, use a **bloom filter** to determine which SSTables might contain the key, then read SSTables newest → oldest. SSTables are sorted by primary key for fast lookup.

Two additional concepts:

- **Compaction** — periodically consolidates SSTables into fewer files, merging updates and removing tombstoned/deleted rows; efficient because SSTables are sorted.
- **SSTable Indexing** — files map keys to byte offsets in SSTables for fast on-disk retrieval (similar in spirit to a B-tree pointing at disk locations).

### Gossip

Nodes share cluster state (alive nodes, schema, etc.) peer-to-peer via **gossip**. Each node tracks a generation (bootstrap timestamp) and version (logical clock, ~per second) per known node — together forming a **vector clock** so stale gossip is ignored. Gossip is probabilistically biased toward **seed nodes**, guaranteed hotspots that prevent isolated sub-clusters; seeds are discoverable via service discovery.

### Fault Tolerance

- **Phi Accrual Failure Detector** — each node independently decides whether peers are up. Unresponsive nodes are "convicted" and stop receiving writes; they rejoin when heartbeating resumes. Nodes are never treated as permanently down unless an admin decommissions/rebuilds them (avoids rebalancing on transient failures).
- **Hinted Handoff** — when a replica is offline, the coordinator temporarily stores the write as a "hint" and delivers it when the node comes back. Hints are short-lived; long-offline nodes get rebuilt or undergo read repairs.

## Data Modeling — Query-Driven, Not Entity-Driven

Relational modeling is entity-relationship-driven and normalized. Cassandra has **no JOINs, no foreign keys, no referential integrity** — it serves single-table queries. So model around the application's **access patterns**, and **denormalize** (duplicate) data across tables as needed.

Key considerations: partition key choice, worst-case **partition size** (and whether partitions grow unboundedly), clustering key (sort order), and what to denormalize.

### Example: Discord Messages

Access pattern: users read recent messages of a channel, reverse-chronological. Initial schema:

```sql
CREATE TABLE messages (
  channel_id bigint,
  message_id bigint,
  author_id bigint,
  content text,
  PRIMARY KEY (channel_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);
```

- `message_id` is a **Snowflake ID** (chronologically sortable UUID) rather than a timestamp — avoids primary key collisions that even millisecond timestamps allow.
- Partitioning by `channel_id` serves a channel's messages from **a single partition** (no scatter-gather).

Problem: very busy channels produced **huge, ever-growing partitions**, which Cassandra handles poorly. Fix: add a time **bucket** (10 days of data, aligned to a fixed epoch) to the partition key:

```sql
CREATE TABLE messages (
  channel_id bigint,
  bucket int,
  message_id bigint,
  author_id bigint,
  content text,
  PRIMARY KEY ((channel_id, bucket), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);
```

Partitions stay bounded, new buckets roll over with time, and recent messages usually still live in one bucket.

### Example: Ticketmaster Seat Browsing

Browsing available seats tolerates **eventual consistency** (actual purchase checks a consistent store), and availability of the browsing UI matters most. First cut:

```sql
CREATE TABLE tickets (
  event_id bigint,
  seat_id bigint,
  price bigint,
  PRIMARY KEY (event_id, seat_id)
);
```

Problems: 10,000+ seat events force expensive per-query aggregation on hot partitions. The UX reveals the fix — users browse by venue **section**, so put `section_id` in the partition key:

```sql
CREATE TABLE tickets (
  event_id bigint,
  section_id bigint,
  seat_id bigint,
  price bigint,
  PRIMARY KEY ((event_id, section_id), seat_id)
);
```

This spreads an event across nodes and shrinks partitions. For the venue-overview UI, **denormalize** section stats into a second table instead of aggregating:

```sql
CREATE TABLE event_sections (
  event_id bigint,
  section_id bigint,
  num_tickets bigint,
  price_floor bigint,
  PRIMARY KEY (event_id, section_id)
);
```

Sections per event are few (<100), so this is served off one small partition. Stats tolerate eventual consistency (Ticketmaster just shows "100+").

## Advanced Features

- **Storage Attached Indexes (SAI)** — global secondary indexes on columns; slower than partition-key queries but avoids extra denormalized tables for infrequent query patterns.
- **Materialized Views** — Cassandra automatically materializes/denormalizes tables from a source table, so your app doesn't have to write to multiple tables itself.
- **Search Indexing** — plugins wire Cassandra to Elasticsearch/Solr (e.g., Stratio Lucene Index) for full-text search.

## Cassandra in an Interview

### When to Use It

- Systems that **prioritize availability over consistency** with high scalability needs.
- Especially strong for **high write throughput** (LSM-tree, append-oriented storage).
- **Flexible / sparse schemas** (wide-column model).
- Applications with a few **clear access patterns** the schema can be designed around (chat messages, activity feeds, time-series-like data).

### Limitations / Pitfalls

- **Not for strict consistency** requirements — it skews heavily toward availability; no transactions or ACID.
- **No JOINs, ad-hoc aggregations, or complex/multi-table queries.**
- Requires up-front query-driven modeling; poor partition key choices lead to **hot or unbounded partitions** (see Discord example).
- Deletes create tombstones; heavy delete workloads can bloat SSTables until compaction.

### Interview Talking Points

- Explain partition key vs. clustering key choices explicitly and justify with access patterns.
- Mention consistency-level tuning (e.g., QUORUM reads+writes for read-your-writes).
- Know the LSM write path (commit log → memtable → SSTable → compaction) for deep-dive questions.
