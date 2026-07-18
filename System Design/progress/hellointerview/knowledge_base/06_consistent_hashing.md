# Consistent Hashing

**Source:** [hellointerview.com — Consistent Hashing](https://www.hellointerview.com/learn/system-design/core-concepts/consistent-hashing)

A foundational distributed-systems algorithm for distributing data across a cluster of servers while minimizing redistribution when the number of servers changes.

## Motivating Example: Sharding Ticketmaster

Start simple: one database, clients fetch event data. Growth forces sharding across multiple databases. Question: **which events go on which database instance?**

### First Attempt: Simple Modulo Hashing

```
database_id = hash(event_id) % number_of_databases
```

With 3 databases:
```
Event #1234 → hash(1234) % 3 = 1 → Database 1
Event #5678 → hash(5678) % 3 = 0 → Database 0
Event #9012 → hash(9012) % 3 = 2 → Database 2
```

Problems:
- **Adding a node:** switching `% 3` → `% 4` changes the mapping for almost *every* event (e.g., #1234 moves from DB 1 to DB 0). Massive unnecessary data movement, huge load spikes, users see errors or slow responses.
- **Removing a node** (hardware failure, bug): `% 3` → `% 2` triggers the same mass redistribution.

## Consistent Hashing

Arrange both data and databases on a circular space — a **hash ring**:

1. Create a ring with a fixed number of points (illustratively 0–100; in reality typically 0 to 2^32 − 1).
2. Place database nodes on the ring (4 DBs at points 0, 25, 50, 75).
3. To place an event: hash its ID, find that point on the ring, and **move clockwise until you hit a database node**.

Why this fixes the problem:

- **Adding DB5 at position 90:** only events hashing between 75 and 90 move (they previously belonged to DB1 at position 0). Everything else stays put. That's ~60% of DB1's events (15 of its 25-unit span) ≈ ~15% of all events — versus nearly all events under modulo.
- **Removing DB2 (position 25):** only DB2's events move — they remap to DB3 (position 50). Everything else stays.

### Virtual Nodes

Remaining problem: when DB2 dies, *all* its load lands on DB3, giving DB3 2x the load of the others. Solution: place each database at **multiple points** on the ring by hashing name variants — "DB1-vn1", "DB1-vn2", "DB1-vn3" → positions 20, 35, 65, etc. Virtual nodes from all databases intermix around the ring.

Now when DB2 fails: DB2-vn1's events go to Database 1, DB2-vn2's to Database 3, DB2-vn3's to Database 4, etc. — load spreads evenly across all survivors. More virtual nodes per database = more even distribution. Virtual nodes also help when **adding** a node: instead of relieving only one clockwise neighbor, the new node's scattered positions absorb small chunks from many existing nodes — balanced from the start.

### Addressing Hot Spots

Consistent hashing distributes **keys** evenly, not **traffic**. A Taylor Swift concert generating 100x the reads of other events still overloads one node. Strategies:

- **Read replicas:** replicate popular keys across nodes, load-balance reads (most common).
- **Key-space salting:** append random suffixes to hot keys (`taylor-swift-{0..9}`) so they hash to different nodes; scatter reads and aggregate.
- **Adaptive rebalancing:** monitor traffic and move key ranges off overloaded nodes in real time (operationally complex; DynamoDB does it automatically).

Interview distinction: **virtual nodes prevent structural imbalance (uneven key distribution); replication and key salting prevent workload imbalance (uneven traffic).**

### Data Movement in Practice

Consistent hashing says where data *should* live; it doesn't teleport terabytes on failure. Real systems pair it with **replication**:

- **DynamoDB:** each partition replicated across three availability zones; on primary failure, a replica is promoted via consensus (e.g., Raft) — no data moves.
- **Cassandra:** replicates to N consecutive ring nodes; reads served from surviving replicas.

Data movement really happens only during planned membership changes (adding capacity, permanently replacing a node to restore replication factor) — and consistent hashing bounds it to a fraction of keys.

## Consistent Hashing in the Real World

Applies wherever data is distributed across a server cluster: databases, caches, message brokers, even application servers. Used in:

1. **Apache Cassandra** — distributes data around the ring
2. **Amazon DynamoDB** — consistent hashing under the hood for partition placement
3. **CDNs** — deciding which edge server caches which content

Not universal: **Redis Cluster uses fixed hash slots instead** — 16,384 slots via `CRC16(key) mod 16384`, with slot ranges assigned to nodes. Simpler to reason about but needs more coordination when rebalancing. Consistent hashing vs fixed slots is a real design tradeoff worth discussing.

Also note (per Kleppmann, DDIA): "consistent hashing" is used loosely — some systems actually use variations like hash partitioning with fixed slot ranges. The principle that matters is **minimizing data movement during rebalancing**.

## When to Use It in an Interview

Most modern systems handle sharding for you — with DynamoDB/Cassandra, just mention they use consistent hashing (or a form of it) under the hood. It becomes crucial in **infrastructure-focused interviews** designing from scratch:

1. Design a distributed database
2. Design a distributed cache
3. Design a distributed message broker

Be prepared to explain:

1. Why consistent hashing beats modulo sharding
2. How virtual nodes improve load balancing
3. Handling node failures and additions
4. How hot spots arise and mitigations (replication, key salting)
5. The relationship between consistent hashing and replication for fault tolerance

Core concept in one line: **arrange everything in a circle and walk clockwise.** Know when to go deep vs when to acknowledge existing solutions handle it — most interviews are the latter.
