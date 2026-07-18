# Redis

**Source:** [hellointerview.com — Redis Deep Dive](https://www.hellointerview.com/learn/system-design/deep-dives/redis)

## What Redis Is

Redis is a self-described **"data structure store"** written in C. It keeps everything **in memory** and executes commands **one at a time on a single thread**, making it both very fast and easy to reason about. The single-threaded design is deliberate: command execution never needs locks, and for such simple operations a single core is rarely the bottleneck. Newer versions offload I/O and background work to other threads, but the mental model is: *one command at a time, in order*.

Why it matters for interviews: Redis is uniquely **versatile** — instead of learning dozens of technologies, you can learn Redis deeply and cover caching, locks, leaderboards, rate limiting, queues, pub/sub, and geospatial search. It's also **simple**: its features resemble data structures you already know from coding (hashes, sets, sorted sets, streams), so reasoning about scaling implications is straightforward. Redis avoids "magic" (no query optimizers/planners) — it just executes simple operations **fast**.

### Durability — The Big Caveat

Redis is **not durable by default**. Two persistence modes:

- **RDB**: periodic snapshots — a crash loses everything since the last snapshot.
- **AOF**: logs every write, but only fsyncs **once per second** by default — a crash loses up to a second of acknowledged writes. You *can* fsync every write, but few do because it kills the speed.

This is an intentional tradeoff: you don't get the "commit-is-on-disk" guarantee a relational database gives you. If you need real durability with Redis semantics, alternatives like **AWS MemoryDB** trade some speed for disk-based durability.

## Core Data Model

Everything is a **key-value store**: every object is a value stored at a string key; the value is where the data structure lives. Fundamental structures:

- **Strings**
- **Hashes** (objects/dictionaries)
- **Lists**
- **Sets**
- **Sorted Sets** (priority queues)
- **Streams** (append-only logs)
- **Geospatial Indexes**

Redis 8 also ships probabilistic structures (Bloom filters), JSON, and time series in core (previously Redis Stack modules). Redis also supports communication patterns like **Pub/Sub** and **Streams**, partially standing in for Kafka or SNS/SQS.

**Key design is critical**: keys may live on separate nodes depending on cluster configuration. How you organize keys is how you organize your data and scale your cluster.

### Commands

Redis speaks a simple wire protocol (**RESP**) — commands travel over the wire close to how you'd type them:

```
SET foo 1
GET foo     # Returns 1
INCR foo    # Returns 2
XADD mystream * name Sara surname OConnor  # Adds to a stream
```

Commands are readable when grouped by data structure (e.g. Sets: `SADD`, `SCARD`, `SMEMBERS`, `SISMEMBER`).

## Infrastructure Configurations

Redis can run as: **single node**, **HA replica setup**, or **cluster**.

- **Cluster mode**: every key hashes to one of **16,384 hash slots**; each slot is assigned to a node (this is sharding). Clients cache the slot-to-node map and connect directly to the right node. On rebalance/failover a node replies `MOVED` and the client refreshes its map (e.g. via `CLUSTER SHARDS`). Nodes share cluster state via gossip. Nodes will *not* forward requests for you.
- **Replication is asynchronous**: the primary acknowledges a write before the replica sees it. If the primary dies, a promoted replica may be missing the last acknowledged writes — this is *the* deepest reason Redis isn't a system of record (and why Redis locks are shaky).
- Redis clusters are deliberately basic — they hand you primitives, not solutions. With few exceptions, **all data for a request must live on a single node**. Choosing key structure is how you scale.
- **Hash tags**: only the part of the key in `{braces}` is hashed, so `{user:123}:posts` and `{user:123}:likes` land in the same slot — enabling `MULTI` transactions across both.

## Performance

- A single node handles roughly **~100k writes/second**; commands execute in **microseconds**; sub-millisecond reads over the network.
- This speed makes some anti-patterns feasible: an N+1 query pattern that would ruin a SQL DB is survivable in Redis, especially with pipelining or `MGET` (one round trip instead of a hundred). Still better avoided, but it won't sink your design.
- Speed comes entirely from being in-memory.

## Common Interview Use Cases

### 1. Cache (most common)

Cache keys = Redis keys; cached values = Redis values (e.g. `product:123` → JSON blob or Hash). Trivially distributed across the cluster; add nodes for capacity.

- Use a **TTL** per key — Redis guarantees you never read an expired key.
- **Expiration handles staleness, not memory pressure**: by default Redis *rejects writes* when memory is full. For caching, configure an eviction policy like `allkeys-lru` (Redis approximates LRU by sampling keys — fine for a cache).
- Caching doesn't solve the **hot key** problem (see below).

### 2. Distributed Lock

Used for consistency during updates (Ticketmaster seat booking) or preventing concurrent actions (Uber matching). The lock is just an agreed-upon key:

```
SET lock:concert:343 my-token NX EX 30
```

- `NX` = succeed only if the key doesn't exist (acquired = you own it; otherwise wait/retry).
- `EX 30` = expiry so a crashed holder can't lock forever.
- `my-token` = random value unique to you.

**Releasing**: don't blindly `DEL` — your lock may have expired and been re-granted to someone else. Check-and-delete atomically via a Lua script (scripts run as one command on the single thread):

```lua
if redis.call("GET", KEYS[1]) == ARGV[1] then return redis.call("DEL", KEYS[1]) end
```

Note this is **pessimistic** locking (grab lock before work). Redis also supports optimistic concurrency: `WATCH` a key + `MULTI`/`EXEC` — the transaction aborts if the watched key changed.

**Failure mode**: async replication means a promoted replica may never have heard of your lock and will grant it again. **Redlock** (acquire on a majority of independent nodes) exists for this but is controversial — a paused/slow client can still act after its lock expired (see Kleppmann's critique). The standard defense is a **fencing token** (increasing number; storage rejects stale writes) — Redis has nothing built in for that.

**Rule of thumb**: treat a Redis lock as an *efficiency tool that occasionally fails*, not a correctness guarantee. If a stale lock holder would corrupt data, enforce the invariant where the data lives (`SELECT ... FOR UPDATE`, or `UPDATE ... WHERE version = X`) or use a consensus system (ZooKeeper/etcd).

### 3. Leaderboards

**Sorted sets** maintain ordered data queryable in log time — great where SQL starts to struggle at scale. Example (top liked posts per keyword):

```
ZADD tiger_posts 500 "SomeId1"
ZADD tiger_posts 1 "SomeId2"
ZREMRANGEBYRANK tiger_posts 0 -6   # Keep only the top 5
```

`ZADD` replaces an existing member's score (re-adding a post with new like count just moves its rank). Negative indexes count from the highest rank.

### 4. Rate Limiting

- **Fixed window**: `INCR` the counter for the current window; reject if count > N (return 429 with `Retry-After`). Subtlety: set expiry **only when INCR returns 1** — calling `EXPIRE` on every request keeps pushing the reset forward and a steady stream never gets a fresh window. Run `INCR` + `EXPIRE` as one Lua script (crash between them leaves a counter that never resets).
- **Sliding window**: one sorted set per user, timestamps as scores. On each request: `ZREMRANGEBYSCORE` (drop old entries), `ZCARD` (count), `ZADD` if under N — all in one Lua script for atomicity.

### 5. Proximity Search

Native geospatial commands:

```
GEOADD key longitude latitude member
GEOSEARCH key FROMLONLAT lon lat BYRADIUS radius unit
```

Search runs in **O(N + log M)** — N = elements in the grid-aligned bounding box, M = items actually within the radius. Under the hood it uses **geohashes** stored in a sorted set (log term from the sorted-set seek); geohash boxes are grid-aligned/imprecise, so a second pass filters candidates to the exact radius.

### 6. Event Sourcing / Work Queues (Streams)

**Streams** are append-only logs similar to Kafka topics. Producers `XADD`; **consumer groups** (`XREADGROUP`, `XCLAIM`/`XAUTOCLAIM`) coordinate which consumer processes which item.

Work queue pattern: worker reads via `XREADGROUP`, processes, acknowledges. The group tracks pending entries with idle times; if a worker dies, another claims the entry with `XCLAIM` and restarts the job. Since Redis can't tell a slow worker from a dead one, **items can be processed twice — make processing idempotent**. Also: streams are only as durable as your persistence settings (defaults can lose recent entries).

**Streams vs Kafka**: Streams fit when Redis is already in your design and the queue is modest (background jobs, notification fan-out, work distribution). Kafka earns its complexity when you need long retention, replay for many independent consumers, or durable ordered throughput where message loss is unacceptable.

### 7. Pub/Sub

Streams = catch up on what you missed; **Pub/Sub** = deliver to whoever's listening *right now*. Real-time broadcast to subscribers (chat, real-time notifications, decoupling producers/consumers).

```
PUBLISH channel message
SUBSCRIBE channel
```

- Channels need no setup — publishing/subscribing brings them into existence.
- **Not durable, at-most-once**: offline subscribers miss messages entirely. Need persistence/replay? Use Streams, Kafka/RabbitMQ, SNS→SQS, or an outbox pattern.
- Old limitation now fixed: classic cluster Pub/Sub broadcast every message to every node. Since **Redis 7, sharded Pub/Sub** (`SPUBLISH`/`SSUBSCRIBE`) routes each channel to the shard owning its slot — capacity scales with the cluster.
- Connection overhead is **per node, not per channel**: a subscriber holds one connection to a node and receives all subscribed channels over it. Millions of channels ≠ millions of connections.

**Don't roll your own Pub/Sub** (e.g. storing subscriber-server lists per topic key): it adds a network hop (3 vs 2), forces cold TCP connections per publish, and requires heartbeat/TTL bookkeeping to detect dead servers. If it looks like Pub/Sub, use Pub/Sub.

## Shortcomings and Remediations

### Hot Key Issues

Uneven load across keys means one node absorbs disproportionate traffic (e.g. one viral ecommerce item on a 100-node cluster) and starts failing. Not unique to Redis (Memcached, DynamoDB too). Remediations, all with tradeoffs:

1. **Client-side caching**: small in-memory cache of the hottest items on each app server; most reads never hit Redis. Cost: a second cache to keep coherent — staleness up to its TTL; best with short TTLs on a small key set.
2. **Key copies**: store the same data under several keys (`product:123:1`…`:10`) hashing to different nodes; readers pick a random suffix. Readers must know which keys are duplicated, and every write fans out to all copies.
3. **Read replicas**: multiplies read capacity — but cluster clients read from the primary *by default* (must configure replica reads), and replicas do nothing for a **write-hot** key.

Interview tip: recognizing hot keys is good (+); proactively designing remediations is better (++).

### When NOT to Use Redis

- **As a system of record**: async replication + persistence loss windows mean acknowledged writes can vanish.
- **When the working set can't economically fit in RAM** (memory is the most expensive place to keep data).
- **When you need query flexibility**: no joins, no cross-key queries; cluster multi-key ops only work within a single slot (hash tags aside).
- **When you need durable, replayable streams** with long retention for many independent consumers — that's Kafka's job.

## Summary

Redis is powerful, versatile, and simple. Because its capabilities are built on simple data structures, reasoning through scaling implications is straightforward — letting you go deep with an interviewer without needing deep internals knowledge. Know the durability tradeoffs, the hot key problem, and the limits of Redis locks, and you can justify (or reject) Redis in almost any design.
