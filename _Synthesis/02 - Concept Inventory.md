---
tags: [synthesis, system-design, low-level-design, inventory]
module: "_Synthesis"
priority: must-know
status: solid
verified_on: 2026-07-17
---

# Concept Inventory

The fact base, at the mature bar. One compact entry per concept: **mechanism / trigger / failure mode / tradeoff**. `🔒` marks concepts the scrapes only captured as headings (premium-locked) — Phase B fills these from primary sources, listed in [[04 - Verification Log]]. Source files are relative to `System Design/progress/hellointerview/`, `System Design/progress/greatfrontend/`, and `Low Level Design/progress/hellointerview/`.

## A. Backend System Design — Knowledge Base

### Networking (`knowledge_base/01_networking_essentials.md`)
- **TCP vs UDP** — TCP: reliable, ordered, connection + handshake overhead (default). UDP: fast, no delivery/order guarantee (video, games, DNS). *Trigger:* choose UDP only when loss is tolerable and latency is king.
- **HTTP over TCP** — the ~90% default for request/response. REST (resource-oriented, cache-friendly) vs GraphQL (client picks fields, solves over/under-fetching, harder to cache) vs gRPC (binary over HTTP/2, fast, internal service-to-service; browsers need gRPC-Web + proxy). *Pattern:* REST externally, gRPC internally.
- **SSE vs WebSockets vs WebRTC** — SSE: unidirectional server→client push over plain HTTP, auto-reconnect. WebSockets: bidirectional, stateful. WebRTC: peer-to-peer (media). *Failure mode:* SSE/WS are stateful → can't sit behind a naive load balancer; a server dying drops thousands of connections. *Common mistake:* WebSockets when SSE/polling suffices.
- **Load balancing** — client-side vs dedicated LBs; L4 (transport) vs L7 (application). Regionalization cuts latency; plan for fault modes.

### API Design (`knowledge_base/02_api_design.md`)
- **REST** — resource modeling, correct HTTP verbs, status codes; data in path/query/body. **GraphQL** — schema-first, one endpoint, resolver cost. **RPC/gRPC** — protobufs, type safety, internal.
- **Pagination** — offset (`?offset=20&limit=10`, simple, drifts under inserts → dup/skip) vs cursor (encoded record id/timestamp, stable, no random page jump). *Interview:* they care you *remembered* pagination; offset usually fine unless real-time/high-volume. → [[01 - Cross-Domain Wiring]] Bridge 5.
- **Versioning** (URI vs header vs param), **auth/authz**, **rate limiting/throttling**.

### Data Modeling (`knowledge_base/03_data_modeling.md`)
- **DB families** — relational (ACID, joins), document (flexible schema), key-value (Redis/DynamoDB, O(1) by key), wide-column (Cassandra, query-driven), graph (relationships).
- **Normalization vs denormalization** — normalize by default (one source of truth, no update anomalies); denormalize for read-heavy/analytics/audit; even then keep the source normalized and put a **denormalized cache** in front (pre-computed joins). → mirrors client store normalization, Bridge 2/8.
- **Schema from access patterns**, indexing for reads, sharding for scale.

### Caching (`knowledge_base/04_caching.md`) — fully captured
- **Where:** external (Redis/Valkey — the interview default) → CDN (media at scale; origin→India ~250–300ms vs edge ~20–40ms) → client-side → in-process (fastest, not shared).
- **Architectures:** cache-aside (lazy, default — "if you remember one, this") / write-through (fresh reads, slow writes, dual-write risk) / write-behind (fast writes, data loss on crash — metrics) / read-through (cache is proxy; CDNs are this).
- **Eviction:** LRU (default) / LFU (stable-popular) / FIFO (rare) / TTL (freshness, not really eviction).
- **Problems:** stampede/thundering-herd → request coalescing (single-flight) + cache warming; consistency → invalidate-on-write / short TTL / accept eventual; hot keys → replicate + local fallback + rate limit.
- **5-step intro:** identify bottleneck → decide what to cache (define keys `user:123:profile`) → choose architecture → set eviction → address downsides. *Don't cache everything; a well-indexed DB is often enough.*

### Sharding (`knowledge_base/05_sharding.md`)
- **Partitioning** (within one instance) vs **sharding** (across instances). Choose a shard key that spreads load and matches access patterns. *Failure mode:* hot spots/load imbalance, cross-shard queries (expensive), cross-shard consistency. *Trigger:* only when a single node genuinely can't hold/serve the data — beware premature sharding (Numbers to Know).

### Consistent Hashing (`knowledge_base/06_consistent_hashing.md`)
- **Mechanism:** hash nodes + keys onto a ring; a key belongs to the next node clockwise. Adding/removing a node moves only `1/N` of keys (vs modulo hashing which remaps almost everything). **Virtual nodes** smooth distribution and fix hot spots. *Trigger:* distributed caches, Cassandra/DynamoDB partitioning, any time you rebalance without mass data movement.

### CAP (`knowledge_base/07_cap_theorem.md`)
- **Mechanism:** under a network **partition**, choose **C** (reject/stall to stay consistent) or **A** (serve possibly-stale to stay available). No partition → have both. Real systems pick a **consistency level** (strong, read-your-writes, eventual). *Trigger:* banking/inventory lean C; feeds/likes/metrics lean A (eventual). → Bridge 4.

### Indexing (`knowledge_base/08_database_indexing.md`)
- **B-Tree** — sorted, range + point queries, read-optimized, write cost to maintain (fully covered). **LSM tree** 🔒 — write-optimized (Cassandra); *premium-locked detail.* Indexes cost write throughput and storage. → Bridge 8.

### Numbers to Know (`knowledge_base/09_numbers_to_know.md`) — 2026 hardware, verified
- Single machine now: **512 GiB / 128 vCPU** common; up to **24 TB RAM**; **60 TB local SSD**; S3 effectively unlimited. Network: **25 Gbps** standard, 50–100+ high-perf. Latency: **sub-1ms intra-AZ, 1–2ms cross-AZ, 50–150ms cross-region** (verified 2026-07, see [[04 - Verification Log]]).
- *Takeaway:* textbook "shard at 100 GB" is outdated → **premature sharding** is a top mistake. Applying-the-numbers sections (caching/DB/app-server/queue sizing, cost) are 🔒.

## B. Backend System Design — 7 Patterns (`patterns/`)
Most solution detail is 🔒; problem framing + when-to-use captured.
1. **Real-time Updates** — push fresh data to clients. Hop 1 (client↔server: polling/SSE/WS) + Hop 2 (server sourcing: pub/sub, Kafka fan-out). → Bridge 3. Problems: live comments, notifications, presence.
2. **Dealing with Contention** — concurrent writes to one resource. Race condition framing captured; solutions (locks, OCC, idempotency) 🔒. → Bridge 1. Problems: Ticketmaster, auctions, inventory.
3. **Multi-step Processes** — reliable multi-stage workflows; orchestration/choreography, sagas, event log (Kafka) 🔒. Problems: payments, order fulfillment.
4. **Scaling Reads** — three-tier progression (replicas → caching → CDN), 🔒 detail. Viral/hot content breaks naive caching. Problems: news feed, search.
5. **Scaling Writes** — sharding, write-behind, queues/batching 🔒. Problems: ad click aggregation, metrics.
6. **Handling Large Blobs** — don't stream bytes through app servers; presigned URLs + direct-to-S3 + CDN 🔒. Problems: Dropbox, YouTube upload.
7. **Managing Long-Running Tasks** — offload to a queue + workers; status polling 🔒. Problems: video transcode, web crawler.

## C. Backend Deep-Dive Technologies (`deep_dives/`)
- **Redis/Valkey** — in-memory data structures (strings/hashes/sorted-sets/streams); uses: cache, rate limiter, leaderboard (sorted set), distributed lock, pub/sub, geospatial. Single-threaded core. *Version flag:* "Redis" now spans a relicensing saga (BSD→SSPL 2024→AGPLv3 Redis 8, May 2025) and the **Valkey** fork (BSD-3, a Linux Foundation project, widely offered as the managed "Redis-compatible" engine on AWS/GCP) — see [[04 - Verification Log]].
- **Kafka** — distributed append-only log; topics/partitions/consumer-groups; ordering within a partition; durable buffer for fan-out, streams, decoupling. Backbone of patterns 1/3/5/7.
- **Elasticsearch** — inverted-index search; near-real-time (refresh interval → eventual consistency, → Bridge 8); full-text, aggregations.
- **API Gateway** — single entry: routing, auth, rate limiting, TLS termination, request shaping. → same responsibilities as a frontend BFF.
- **Cassandra** — wide-column, LSM-tree, query-driven modeling, tunable consistency, no joins; write-optimized.
- **DynamoDB** — managed key-value/document; partition + sort key; GSIs/LSIs; tunable read consistency; pay-per-capacity.
- **PostgreSQL** 🔒 (partial) — relational default; JSON, extensions; framing captured, deep sections locked.
- **Flink** 🔒 — stateful stream processing; framing only.
- **ZooKeeper** 🔒 — distributed coordination/leader election/config; motivating example only. → distributed analog of LLD locks (Bridge 1).
- **Proximity Search** — geospatial: spatial trees (quadtree/R-tree) vs encoded keys (geohash); which to use.
- **Time-Series DBs** — append-heavy, time-ordered; the cardinality problem.
- **Data Structures for Big Data** — Bloom filter (probabilistic membership, no false negatives) captured; rest 🔒.
- **Vector Databases** — embeddings + ANN search; framing + "what's a vector" captured; index detail 🔒.

## D. Low-Level Design (`Low Level Design/progress/hellointerview/`)
- **Delivery framework** (`01`) — Requirements (~5m) → Entities/Relationships (~3m) → Class Design (~10–15m, derive state + behavior from requirements) → Implementation (~10m, walk a scenario) → Extensibility (~5m). → Bridge 7.
- **Design principles** (`02`) — KISS, DRY, YAGNI, Separation of Concerns, Law of Demeter; **SOLID** (SRP/OCP/LSP/ISP/DIP). Principles produce patterns; don't force patterns. → Bridge 6.
- **OOP concepts** (`03`) — encapsulation, abstraction, polymorphism, inheritance; *when inheritance breaks* → prefer **composition**.
- **Design patterns** (`04`) — the ~5 that matter: **Factory** (creation without caller choosing; watch over-engineering), **Builder** (stepwise complex construction), **Singleton** (one instance; often an anti-pattern), **Strategy** (swap algorithm behind interface), **Observer** (subscribers react to changes), **State** (behavior by mode), + Decorator/Facade. GoF's 23 are mostly obsolete; interviews test ~5; US grades design quality over naming. → Bridge 6.
- **Concurrency** (`concurrency/`): 
  - `01` intro — LLD concurrency is **single-process** (threads + shared memory), distinct from distributed contention. Primitives: **atomics** (lock-free CAS), **locks/mutexes** (critical section), **semaphores** (bound N resources), **condition variables** (wait/signal), **blocking queues** (producer/consumer hand-off). Three problem types: correctness, coordination, scarcity.
  - `02` **Correctness** — race conditions/torn reads; solutions 🔒 (locks, atomics, immutability).
  - `03` **Coordination** — producer/consumer; anti-patterns: busy-waiting, sleep-polling, unbounded producers; needs a bounded blocking queue + condition signaling; solution detail 🔒.
  - `04` **Scarcity** — bounded resources (connection pools, rate limiters, thread pools); semaphore-based; detail 🔒.
  - → all of concurrency is Bridge 1 at the smallest scale.

## E. Frontend System Design (`greatfrontend/`) — already in vault module 29
- **FE vs BE SD** (`01`) — client architecture + client↔server boundary; server is a black box; **no** capacity estimation / DB schemas / load balancers; focus perf, UX, a11y, i18n.
- **Question types** (`02`) — Applications (news feed, chat, e-commerce) vs UI Components (autocomplete, modal, carousel, data table); product category picks deep dives.
- **RADIO** (`03`) — Requirements 10% / Architecture 20% / Data model 10% / Interface 20% / Optimizations 40%. Client architecture = View / Store / Data-access / Server-black-box. Interface = two APIs (component props + network). → Bridge 7. Already fully noted at [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]].
- **Evaluation axes** (`04`) — problem exploration, architecture, technical proficiency, tradeoffs, product/UX sense, communication (score *observed* signals).
- **Common mistakes** (`05`) — jumping in, no structure, one solution, silence, rabbit-holes, undefendable buzzwords.
- **Case studies** — News Feed (cursor pagination, store normalization, CSR/SSR, optimistic updates, virtualization) and Autocomplete (props API, debounce, race conditions, cache, ARIA combobox) — both map onto vault notes [[29 - Frontend System Design/02 - Designing an Autocomplete|Autocomplete]] and [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Infinite Scroll Feed]].

## F. Question banks (applications of the above)
- **BE questions (30)** — Bitly, Rate Limiter, Ticketmaster, News Feed, WhatsApp, Dropbox, LeetCode, Web Crawler, YouTube, Uber, GoPuff, Tinder, FB Live Comments, YouTube Top-K, Ad Click Aggregator, FB Post Search, Yelp, Instagram, Strava, Distributed Cache, Online Auction, Job Scheduler, Google News, Price Tracking, Robinhood, Google Docs, Payment System, Metrics Monitoring, Online Chess, ChatGPT. Each exercises 1–3 patterns (e.g., Ticketmaster/Auction → Contention; Ad Click/Metrics → Scaling Writes; Live Comments/Chess → Real-time; Dropbox/YouTube → Large Blobs).
- **LLD questions (partial: 6)** — Connect Four, Amazon Locker, Movie Ticket Booking, Logging Service, Rate Limiter, Inventory Management. Booking/Inventory/Rate Limiter → concurrency (Bridge 1); all → delivery framework + patterns.
- *Phase B note:* mine the question walkthroughs for the concrete Bug→Fix→Tradeoff examples the vault template wants, rather than inventing them.
