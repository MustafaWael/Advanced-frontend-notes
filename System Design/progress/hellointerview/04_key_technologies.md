# Key Technologies (System Design in a Hurry)

**Source:** https://www.hellointerview.com/learn/system-design/in-a-hurry/key-technologies

## Big Picture

- System design = assembling the most effective **building blocks** to solve a problem. Interviewers rarely care *which* specific technology you pick (e.g., which queue), but you must know **at least one** option per category.
- These categories cover ~90% of system design problems.
- **Depth expectations scale with level:** a mid-level candidate who can roughly describe Elasticsearch as "a search index" is fine; a senior candidate who can't explain the inverted index or reason about scaling it is a yellow flag. **Focus on breadth before depth.**

---

## 1. Core Database

Almost every problem needs data storage — usually a database (or blob storage).

- Pick **one** database type for your interview:
  - **Product design interviews** → relational database (e.g., Postgres).
  - **Infrastructure design interviews** → NoSQL database (e.g., DynamoDB).
- **Avoid the SQL vs NoSQL comparison pothole.** The two are highly overlapping:
  - "I need relational because I have relationships" — wrong; NoSQL handles relationships fine.
  - "I need NoSQL for scale/performance" — wrong; relational DBs scale and perform very well when used correctly.
  - Broad statements like these are **yellow flags revealing inexperience**.
- Instead, talk about specific features of the DB you chose and how they solve the problem. Good opener: *"I'm using Postgres here because its ACID properties will allow me to maintain data integrity."*

### Relational Databases (RDBMS)

**What/when:** Most common database type; used for transactional data (user records, orders); default choice for product design interviews. Data stored in tables of rows and columns; queried with SQL (declarative).

**Three key features to know:**

1. **SQL Joins** — combine data across tables (e.g., all posts by a user). Supports arbitrary joins, but joins can be a **major performance bottleneck** — minimize where possible.
2. **Indexes** — make queries fast; usually implemented as **B-Trees** or **Hash Tables**. RDBMS strengths: (a) arbitrarily many indexes to optimize different queries, (b) multi-column and specialized indexes (geospatial, full-text).
3. **Transactions** — group multiple operations into a single atomic operation (all succeed or all fail). E.g., create a user and their first post together, so you never have a post from a nonexistent user.

**Common choices:** **Postgres** and **MySQL**. If no preference, pick Postgres.

### NoSQL Databases

**What/when:** Broad category supporting key-value, document, column-family, and graph data models. No traditional table structure; often schema-less. Good for large volumes of unstructured/semi-structured data and easy horizontal scaling.

**Strong candidates when you need:**
- **Flexible data models** — evolving schema or varied data structures.
- **Scalability** — horizontal scaling across many servers for large data/high load.
- **Big data & real-time apps** — large volumes of (especially unstructured) data, real-time processing/analytics.

Caveat: NoSQL strengths are not relational weaknesses — relational DBs have JSON columns (flexible schema) and can scale horizontally with the right architecture. Discuss specific features, not broad claims.

**Things to know:**
1. **Data models** — key-value, document, column-family, graph.
2. **Consistency models** — from strong (all nodes see same data at the same time) to eventual (all nodes converge eventually).
3. **Indexing** — supported, commonly B-Tree or Hash Table indexes.
4. **Scalability** — horizontal scaling via **consistent hashing** and/or **sharding**.

**Common choices:** **DynamoDB** (broad features, widely accepted — a favorite), **Cassandra** (great for write-heavy workloads due to append-only storage model, with functionality tradeoffs), **MongoDB**.

---

## 2. Blob Storage

**What/when:** For large, unstructured blobs — images, videos, files. Storing these in a traditional DB is expensive and inefficient; use S3 / Google Cloud Storage instead. Upload a blob, get back a URL; often paired with a CDN for fast global downloads (blob storage = origin, CDN caches at edge).

**Key rule:** Don't use blob storage as your primary database. Typical setup: core DB (Postgres/DynamoDB) stores **pointers (URLs)** to blobs in S3 — DB gives low-latency query/indexing, blob storage gives cheap bulk storage.

**Canonical examples:**
- Design YouTube → videos in blob storage, metadata in DB.
- Design Instagram → images/videos in blob storage, metadata in DB.
- Design Dropbox → files in blob storage, metadata in DB.

**Standard presigned-URL flow:**
- *Upload:* client requests presigned URL from server → server returns it and records it in DB → client uploads directly to the presigned URL → blob storage notifies server the upload completed → status updated.
- *Download:* client requests file → server returns presigned URL → client downloads via CDN, which proxies to blob storage.

**Things to know:**
1. **Durability** — replication and erasure coding keep data safe through disk/server failures.
2. **Scalability** — hosted blob storage (S3) is effectively **infinitely scalable**; treat it as a given in interviews.
3. **Cost** — very cheap: S3 ≈ **$0.023/GB/month** (first 50 TB) vs DynamoDB ≈ **$1.25/GB/month** (first 10 TB).
4. **Security** — encryption at rest and in transit; access control built in.
5. **Direct client upload/download** — via **presigned URLs** granting temporary, scoped access.
6. **Chunking** — upload large files in pieces for resumability and parallelism; S3 supports this via the **multipart upload API**.

**Examples:** Amazon S3, Google Cloud Storage, Azure Blob. Default to S3 — most widely understood; other platforms often have S3-compatible APIs.

---

## 3. Search Optimized Database

**What/when:** For **full-text search** features. A naive `SELECT * FROM documents WHERE document_text LIKE '%term%'` requires a full table scan — slow and doesn't scale.

Search-optimized DBs use **inverted indexes**: a map from words → documents containing them, e.g.

```
{ "word1": [doc1, doc2, doc3], "word2": [doc2, doc3, doc4] }
```

Lookup the word, get matching documents instantly. Classic use cases: Ticketmaster event search, Twitter tweet search.

**Things to know:**
1. **Inverted indexes** — the core data structure (word → docs).
2. **Tokenization** — splitting text into individual words.
3. **Stemming** — reducing words to root form ("running", "runs" → "run") so different forms match.
4. **Fuzzy search** — tolerate misspellings/variations via **edit distance** (how many letters changed/added/removed to transform one word into another); usually a config option out of the box.
5. **Scaling** — add nodes to a cluster and shard data across them.

**Examples:** **Elasticsearch** is the clear leader (distributed, RESTful search/analytics engine on Apache Lucene; used by Netflix, Uber, Yelp). Alternatives: **Postgres GIN indexes** (full-text search) or Redis full-text search (immature). Using your existing DB can reduce design footprint.

---

## 4. API Gateway

**What/when:** Especially in microservice architectures, sits in front of the system and **routes requests to the right backend service** (e.g., `GET /users/123` → users service). Also handles cross-cutting concerns: **authentication, rate limiting, logging**.

- In nearly all **product design** interviews, include an API gateway as the first point of contact for clients.
- Interviewers rarely dig into gateway details — they'd rather ask problem-specific questions.

**Common choices:** AWS API Gateway, Kong, Apigee. nginx or Apache webserver can also serve as a gateway (early Amazon ran a giant Apache fleet for this).

---

## 5. Load Balancer

**What/when:** Distributes high traffic across multiple machines (horizontal scaling) to avoid overloading any single machine or creating hotspots. In interviews, treat it as a **black box** that spreads work.

- You technically need one anywhere multiple machines handle the same request, but drawing one in front of every service is redundant. Either omit it (just mention services are horizontally scaled) or draw a single one at the front as an abstraction.
- **L4 vs L7 rule of thumb:** persistent connections (e.g., **websockets**) → **L4** load balancer. Otherwise → **L7**, which gives flexible routing to services while minimizing downstream connection load.

**Common choices:** AWS Elastic Load Balancer (hosted), NGINX (open-source webserver often used as LB), HAProxy (open-source LB). At extreme traffic, hardware load balancers outperform self-hosted software LBs.

---

## 6. Queue

**What/when:** Buffers for **bursty traffic** and a way to **distribute work**. Producers send messages and forget; a pool of workers processes them at their own pace.

- Smooths load: 1,000-request spike with 200 rps capacity → 800 wait in queue, none are dropped.
- Decouples producer and consumer → scale them independently; take services behind the queue down/up with negligible impact.
- **Warning:** don't put queues in synchronous workloads. With strong latency requirements (e.g., < 500 ms), a queue nearly guarantees you'll break the constraint.

**Use cases:**
1. **Buffer for bursty traffic** — e.g., Uber ride-request surges at peak hours.
2. **Distribute work** — e.g., photo-processing service pushing image tasks to workers.

**Things to know:**
1. **Message ordering** — most queues are FIFO; some (Kafka) allow richer ordering guarantees (priority, time).
2. **Retry mechanisms** — configurable redelivery attempts, delays, max attempts.
3. **Dead letter queues** — store unprocessable messages for debugging/auditing.
4. **Scaling with partitions** — partition across servers; choose a partition key so related messages land together.
5. **Backpressure** — the biggest queue pitfall: 300 rps in, 200 rps capacity → the queue just hides insufficient capacity. Backpressure slows producers when the queue is overwhelmed (reject or throttle new messages, return errors upstream).

**Common choices:** **Kafka** (distributed streaming platform usable as a queue) and **AWS SQS** (fully managed).

---

## 7. Streams / Event Sourcing

**What/when:** For processing vast data in real-time or complex scenarios like **event sourcing** (state changes stored as a sequence of events that can be replayed to reconstruct state at any point — great for audit trails, reversing/replaying transactions).

Unlike queues, **streams retain data for a configurable period**, letting consumers read and re-read from a position or point in time.

**Use a stream when:**
1. **Processing large amounts of data in real-time** — e.g., real-time engagement analytics (likes/comments/shares) processed by Flink or Spark Streaming.
2. **Event sourcing** — e.g., banking: every transaction is an event in Kafka; store, process, replay; audit, rollback, reconstruct any account's state.
3. **Multiple consumers reading the same stream** — e.g., chat room where every participant subscribes; a classic **publish-subscribe** pattern.

**Things to know:**
1. **Partitioning for scale** — each partition processed by a different consumer; pick a partition key that keeps related events together.
2. **Multiple consumer groups** — independent reads of the same stream (one group updates a dashboard, another archives to a DB).
3. **Replication** — data replicated across servers for fault tolerance.
4. **Windowing** — group events by time or count for batch aggregates (e.g., mean delivery time per region over last 24 hours).

**Common choices:** **Kafka**, **Flink**, **AWS Kinesis**.

---

## 8. Distributed Lock

**What/when:** Lock a resource across systems/processes for a moderate period (e.g., a Ticketmaster seat for ~10 minutes during purchase). DB transaction locks are for short-lived consistency, not longer-term holds.

Typically implemented on a distributed key-value store (**Redis** or **ZooKeeper**) using atomic operations: set `ticket-123 = locked`; another process's attempt fails while it's held; release by unsetting. Locks can **expire (TTL)** so a crashed process doesn't leave things locked forever.

**Interview use cases:**
1. **E-commerce checkout** — hold a high-demand item (limited-edition sneakers) in a cart ~10 min during payment.
2. **Ride-sharing matchmaking** — lock a nearby driver so they aren't matched to multiple riders; hold until confirm/decline/timeout.
3. **Distributed cron jobs** — ensure a scheduled task runs on only one server at a time.
4. **Online auction bidding** — briefly lock an item in the final seconds to process a bid and update the highest bid atomically.

**Things to know:**
1. **Locking mechanisms** — e.g., **Redlock** (multiple Redis instances for safe acquire/release).
2. **Lock expiry** — TTLs prevent stuck locks after crashes.
3. **Granularity** — lock a single resource or a group (one ticket vs a stadium section).
4. **Deadlocks** — two processes each holding one lock and waiting for the other's. Be ready to discuss prevention; a common mistake is acquiring locks from far-flung parts of infrastructure/code, making deadlocks hard to spot.

---

## 9. Distributed Cache

**What/when:** A server (or cluster) storing data **in memory** — for scaling and lowering latency; ideal for data that's expensive to compute or fetch from the DB.

**Use cases:**
1. **Save aggregated metrics** — compute dashboard metrics asynchronously (e.g., hourly background job), serve from cache.
2. **Reduce DB queries** — store user sessions in cache for high-concurrency systems.
3. **Speed up expensive queries** — e.g., Twitter home timeline (multi-table joins/filters): run once, cache results.

**Things to know:**

1. **Eviction policies:**
   - **LRU** — evict least recently used.
   - **FIFO** — evict in insertion order.
   - **LFU** — evict least frequently used.
2. **Cache invalidation strategy** — keep cache fresh (e.g., invalidate a cached Ticketmaster event when the venue changes in the DB).
3. **Cache write strategies:**
   - **Write-through** — write cache + datastore simultaneously; consistent but slower writes.
   - **Write-around** — write straight to datastore, bypass cache; less cache pollution but slower subsequent reads.
   - **Write-back** — write cache first, flush to datastore asynchronously; fast writes but risk of data loss if the cache fails first.

**Pro tip:** Be explicit about *what* you're caching and the **data structure** used — modern caches aren't just key-value stores (e.g., use a **sorted set** for a popularity-ranked event list). Just saying "I'll cache it" is a missed opportunity and invites follow-ups.

**Common choices:** **Redis** (strings, hashes, lists, sets, sorted sets, bitmaps, hyperloglogs) and **Memcached** (simple key-value: strings and binary objects).

---

## 10. CDN (Content Delivery Network)

**What/when:** A type of cache using geographically distributed servers to deliver content based on user location. Commonly for static content (images, videos, HTML), but can also serve dynamic content and API responses.

**How it works:** Content cached on servers near users; request routes to nearest edge server; cache hit → serve; miss → fetch from origin, cache, serve.

**Most common interview use:** cache static media assets — e.g., Instagram profile pictures served fast worldwide.

**Things to know:**
1. **Not just static assets** — dynamic content that's read-heavy but changes rarely (e.g., a daily-updated blog post) caches well.
2. **API response caching** — reduces server load, improves API performance for frequently accessed endpoints.
3. **Eviction policies** — TTLs on cached content, or explicit cache invalidation when content changes.

**Examples:** Cloudflare, Akamai, Amazon CloudFront — caching plus DDoS protection, WAFs, and global edge networks for low latency.
