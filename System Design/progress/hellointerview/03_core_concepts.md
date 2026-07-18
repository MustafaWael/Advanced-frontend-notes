# Core Concepts

**Source:** [https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts](https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts)

Core concepts are the **technology-agnostic building blocks** behind nearly every design problem — the vocabulary and grammar of system design, distinct from specific technologies (Redis, Kafka) or problem-specific patterns. Interviewers assume you know these and will probe when you propose using them. This page is the overview; each section links to a deeper article.

---

## 1. Networking Essentials

Full article: [Networking Essentials](https://www.hellointerview.com/learn/system-design/core-concepts/networking-essentials)

### Protocol choice
- **Default: HTTP over TCP.** Well-understood, works everywhere, handles ~90% of use cases. Interviewers expect this unless you have a specific reason otherwise.
- **SSE (Server-Sent Events)** — unidirectional: client opens an HTTP connection, server pushes data down it (live scores, notifications). Client can't send more data on that connection. Simpler, works with standard HTTP infrastructure.
- **WebSockets** — true bidirectional; both sides send freely (chat, live collaboration). Necessary only when clients push data back frequently.
- Both SSE and WebSockets are **stateful connections**: you can't just put them behind a standard load balancer. Plan for connection persistence and for a server dying with thousands of active connections.
- **gRPC** — binary serialization over HTTP/2; significantly faster than JSON/HTTP for internal service-to-service calls. Not for public APIs (browsers don't natively support it; gRPC-Web needs a proxy and is limited). Common pattern: **REST externally, gRPC internally**.

> Common mistake: proposing WebSockets when long polling or SSE would do. WebSockets add significant stateful complexity at scale — reach for them only for genuinely bidirectional real-time needs, not because the prompt says "real-time".

### Load balancing
- **Layer 7 (application level)** — routes based on HTTP request content (API calls to one service, page requests to another).
- **Layer 4 (TCP level)** — faster but "dumber"; distributes connections without inspecting content. Typically required for **WebSockets** (persistent TCP connections).

### Geography and latency
- New York → London has ~**80ms minimum latency** just from light through fiber, before any processing.
- Global low latency requires **regional deployments** with data replicated or partitioned by geography.
- This is why **CDNs** exist: serve static content from edge servers near users.

---

## 2. API Design

Full article: [API Design](https://www.hellointerview.com/learn/system-design/core-concepts/api-design)

- Most interviewers don't care about perfect API design — they want reasonable endpoints so you can get to the harder architectural problems. But sloppy APIs signal inexperience.
- **Default to REST for ~90% of interviews**: resources map to URLs, HTTP methods manipulate them (`GET /users/{id}`, `POST /events/{id}/bookings`).
- **Time budget: sketch 4-5 key endpoints in a couple of minutes and move on.** Still designing API details 10 minutes in = going too deep.
- Mention (but don't deep-dive unless asked):
  - **Pagination** for large result sets — **cursor-based** is better for real-time data with frequent inserts; **offset-based** is fine for most cases.
  - **Auth** — JWT tokens for user sessions; API keys for service-to-service.
  - **Rate limiting** — if the system could be hammered by bots/abuse.

---

## 3. Data Modeling

Full article: [Data Modeling](https://www.hellointerview.com/learn/system-design/core-concepts/data-modeling)

Data-model decisions have massive downstream effects on performance, scalability, and maintainability.

### Relational vs NoSQL
- **Relational (e.g. Postgres)**: structured data with clear relationships + strong consistency (users → orders → products). SQL for complex queries, transactions, foreign-key constraints.
- **NoSQL (e.g. DynamoDB, MongoDB)**: flexible schemas (structure changes often) or horizontal scaling across many servers without complex joins.

### Normalization vs Denormalization
- **Normalization**: split data across tables to avoid duplication (orders reference user_id/product_id instead of copying data). Keeps data consistent (update once, reflected everywhere) but requires **joins**, which get expensive on huge tables or multi-table joins.
- **Denormalization**: duplicate data to avoid joins and speed reads (store username directly on each order). Downside: **updates** — change a name and you must update every copy. Often worth it for **read-heavy, rarely-changing** data.
- **Interview default: start normalized/relational, then denormalize specific hot paths** when you identify read-performance issues. Don't propose denormalization upfront without a clear reason — show you understand the tradeoff.

### NoSQL access-pattern design
- DynamoDB makes you design **partition key + sort key around your access patterns**. Social app where the main query is "get all posts for user X" → partition key = `user_id` → fast single-partition lookup. But "all posts with hashtag Y" now requires a full table scan. **Know your queries upfront and design around them.**

---

## 4. Database Indexing

Full article: [Database Indexing](https://www.hellointerview.com/learn/system-design/core-concepts/db-indexing)

- Indexes make queries fast: without one, finding a user by email = scanning all rows (10M users → 10M row checks). With an index → milliseconds.
- **B-tree** — the default in most relational DBs. Sorted tree supporting both exact lookups and **range queries** (orders between date A and B).
- **Hash indexes** — faster exact matches, **no range queries**; less common.
- **Specialized indexes**: full-text (search documents by words), geospatial (restaurants within 5 miles).
- **Interview move**: index the fields you query frequently — email for auth lookups, `user_id` on orders. Composite queries ("events in San Francisco on Dec 25") → **compound index** on (city, date).
- **External indexes** for what your primary DB can't do: **Elasticsearch** for full-text search; **PostGIS** extension for geospatial in Postgres. These sync from the primary DB via **change data capture (CDC)**, so the search index **lags slightly** — reads are a bit stale, which is almost always acceptable for search.

---

## 5. Caching

Full article: [Caching](https://www.hellointerview.com/learn/system-design/core-concepts/caching) · Related pattern: [Scaling Reads](https://www.hellointerview.com/learn/system-design/patterns/scaling-reads)

- Comes up in almost every interview, usually when the database is getting hammered with reads. Store hot data in fast memory (Redis) and skip the DB.
- **Numbers**: Redis cache hit ~**1ms** vs **20-50ms** for a typical DB query — a **20-50x speedup** — plus reduced DB load (more headroom for writes, defers scaling).
- **Default pattern (~90% of the time): cache-aside with Redis.** Read → check cache → hit: return; miss: query DB, store in cache **with a TTL**, return.

### Invalidation (the hard part)
When the source data changes, the cached copy must be dealt with or reads go stale. Strategies:
- Invalidate/update the cache entry immediately after writes
- Short TTLs + accept some staleness
- Combine both — choose based on required freshness.

### Cache stampede (thundering herd)
A popular entry expires → many concurrent misses pile onto the DB to regenerate it → load spike can take the system down. Preventions:
- **Locking** — one request regenerates, the rest wait
- **Early recomputation** — refresh before expiry
- **Staggered TTLs** — entries don't all expire at once

### Full cache outage (related but distinct)
Redis goes down entirely → every request hits the DB. Defenses: small **in-process fallback cache**, **circuit breakers** to shed load, **graceful degradation** until Redis recovers.

### What to cache
- **Common mistake: caching everything.** Cache only frequently-read, rarely-changing data. Caching data that changes every request adds latency and complexity for nothing. Profile first, cache the hot paths.
- **CDN caching** — static assets (images, video, JS) at edge locations.
- **In-process caching** — small, rarely-changing values (feature flags, config).
- **External Redis caching** — the default for core application data.

---

## 6. Sharding

Full article: [Sharding](https://www.hellointerview.com/learn/system-design/core-concepts/sharding) · Related pattern: [Scaling Writes](https://www.hellointerview.com/learn/system-design/patterns/scaling-writes)

- Sharding = splitting data across multiple independent database servers, once you've outgrown one. Triggers: storage limits (single Postgres maxes out in the **TB range**), write throughput limits (**tens of thousands of writes/sec**), or read throughput even replicas can't cover.

### Shard key (the key decision)
- Determines data distribution and shapes everything downstream.
- Instagram-style app sharded by `user_id`: all of a user's posts/likes/comments on one shard → user-scoped queries fast; but global queries ("trending posts across all users") must hit **every shard** and aggregate. That's the tradeoff — state it explicitly.

### Sharding strategies
- **Hash-based** (hash key, modulo to pick shard) — most common; even distribution, avoids hot spots.
- **Range-based** — works when access patterns naturally partition (multi-tenant SaaS, each company queries only its own data); risk of hot spots if one range gets heavy traffic.
- **Directory-based** — lookup table decides placement; flexible but adds a dependency + latency on every request; rarely worth it in interviews.

### Don't shard too early
- **The biggest sharding mistake is premature sharding.** A well-tuned single DB with read replicas handles far more than most candidates think. Do the capacity math first: **10K writes/sec and 100GB of data → you don't need sharding yet.** Bring it up when numbers justify it, not as a default.

### New problems sharding creates
- **Cross-shard transactions** — nearly impossible; design shard boundaries to avoid them. A cross-shard money transfer needs distributed transactions or **sagas** (complex, slow).
- **Hot spots** — one shard gets disproportionate traffic (the "Taylor Swift shard" hammered while others idle).
- **Resharding pain** — adding a shard means moving massive amounts of data.

**Interview move**: justify why a single DB won't work, state your shard key, and name the tradeoff ("fast for X queries, slow for Y"). That's usually all the interviewer needs.

---

## 7. Consistent Hashing

Full article: [Consistent Hashing](https://www.hellointerview.com/learn/system-design/core-concepts/consistent-hashing)

- **Problem it solves**: with simple `hash(key) % N` distribution, adding/removing a server changes N, remapping almost every key → massive data movement across cache/database nodes.
- **How it works**: place servers and keys on a **virtual ring**. A key belongs to the next server clockwise. Adding a server moves only the keys between it and the previous server; removing one relocates only its keys to the next server. Everything else stays put.
- **The win**: adding one server to a 10-server cluster with modulo hashing moves ~**90%** of data; with consistent hashing, only ~**10%** moves. Makes dynamic scaling practical.
- **Where it shows up**: Memcached / Redis Cluster (distributing cache keys), Cassandra / DynamoDB (sharding), some load balancers (stable request-to-backend assignment), CDNs (routing to edge servers).
- **Interview usage**: you rarely need to explain the mechanics unless asked. Saying "we'll use consistent hashing to distribute data across cache nodes/shards" is enough — the interviewer just wants awareness. Bring it up especially when discussing **elastic scaling** (adding/removing nodes based on load).

---

## 8. CAP Theorem

Full article: [CAP Theorem](https://www.hellointerview.com/learn/system-design/core-concepts/cap-theorem)

- You can only have two of: **Consistency** (all nodes see the same data), **Availability** (every request gets a response), **Partition tolerance** (system works despite network failures between nodes). Since partitions are unavoidable in distributed systems, **you're really choosing consistency vs availability**.
- **Choose consistency** → during a partition, some nodes refuse requests rather than serve stale data; system may be down, but data is always correct.
- **Choose availability** → every node keeps answering during a partition; different nodes may temporarily disagree until the partition heals.

### Defaults and exceptions
- **Availability is the right default for most systems.** Users tolerate a 2-second-stale Instagram feed; they don't tolerate downtime. Social feeds, recommendations, analytics dashboards → **eventual consistency** (all nodes converge to the same state given enough time without updates — distinct from *weak* consistency, which makes no convergence guarantee).
- **Strong consistency** when stale data costs real money or breaks things: inventory (overselling), banking balances (fraud), booking systems like Ticketmaster (double-booked seats).
- **Mix models within one system**: e-commerce product descriptions/reviews can be eventually consistent; inventory counts and order processing need strong consistency.

### PACELC
- CAP only describes behavior **during partitions**, which are rare. In normal operation the real tradeoff is **consistency vs latency**. PACELC: during a **P**artition choose **A**vailability or **C**onsistency; **E**lse choose **L**atency or **C**onsistency. Even on a healthy network, strong consistency adds latency because nodes must coordinate before responding.
- **Interview safe answer**: eventual consistency, unless the problem involves money, inventory, or booking limited resources.

---

## 9. Numbers to Know

Full article: [Numbers to Know](https://www.hellointerview.com/learn/system-design/core-concepts/numbers-to-know)

- Per the Delivery Framework: no back-of-the-envelope math at the start — do it **when a decision depends on it** (shard the DB? can one Redis handle the cache?).
- **Modern hardware is far more powerful than most candidates assume.** A well-tuned DB server handles tens of thousands of QPS; a single Redis instance handles hundreds of thousands of ops/sec. Using 2010-era numbers makes you shard and cache way too early.

### Latency ladder (drives most decisions)
- Memory access: **nanoseconds**
- SSD read: **microseconds**
- Network within a data center: **1-10 ms**
- Cross-continent: **tens to hundreds of ms**

### Doing math in context
- When asked "how many servers?": walk it through aloud — "50K req/s, ~5K req/s per server → ~10 servers plus headroom." Interviewers want to see the reasoning, not memorized trivia.
- Storage: a single Postgres instance handles **a few TB comfortably**; sharding isn't needed until **tens-to-hundreds of TB**. Proposing sharding at 500GB adds massive complexity for no reason.

### Component reference table

| Component | Key metrics | Scale triggers |
|---|---|---|
| **Caching (Redis)** | ~1ms latency; 100k+ ops/sec; memory-bound (up to ~1TB) | Hit rate < 80%; latency > 1ms; memory > 80%; cache churn/thrashing |
| **Databases** | Up to 50k transactions/sec; sub-5ms read latency (cached); 64 TiB+ storage | Write throughput > 10k TPS; uncached read latency > 5ms; geographic distribution needs |
| **App servers** | 100k+ concurrent connections; 8-64 cores @ 2-4 GHz; 64-512GB RAM standard (up to 2TB) | CPU > 70%; response latency > SLA; connections near 100k/instance; memory > 80% |
| **Message queues** | Up to 1M msgs/sec per broker; sub-5ms end-to-end latency; up to 50TB storage | Throughput near 800k msgs/sec; ~200k partitions per cluster; growing consumer lag |

---

## Quick Interview Cheatsheet

- Protocol: HTTP/REST by default; SSE for server-push; WebSockets only for true bidirectional; gRPC internal-only.
- Data model: normalized relational first; denormalize hot read paths with justification.
- Index the columns you query; Elasticsearch (via CDC) for full-text search.
- Cache-aside with Redis + TTL; plan for invalidation and stampedes.
- Shard only when the math demands it; name the shard key and its tradeoff.
- Consistent hashing = one-line mention for elastic node scaling.
- Consistency: eventual by default; strong for money/inventory/bookings; remember PACELC.
- Do estimates only when they change a decision, using modern-hardware numbers.
