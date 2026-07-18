# 15 - Ad Click Aggregator

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/ad-click-aggregator
**Difficulty:** Hard · Pattern: Scaling Writes

An Ad Click Aggregator collects and aggregates data on ad clicks so advertisers can track ad performance and optimize campaigns. Assume ads displayed on a website/app like Facebook. This is a data-processing question (less user-facing product), so the delivery framework focuses on the **system interface and data flow** instead of a REST API.

---

## Functional Requirements

**Core:**
1. Users can click on an ad and be redirected to the advertiser's website.
2. Advertisers can query ad click metrics over time with a minimum granularity of **1 minute**.

**Below the line (out of scope):** ad targeting, ad serving, cross-device tracking, integration with offline marketing channels.

## Non-Functional Requirements

Ask about **scale** first — it heavily impacts DB design and architecture here. We design for **10M active ads** and a **peak of 10k clicks/second**. Using peak ≈ 10x average, average ≈ 1k clicks/sec → ~**100M clicks/day**.

**Core:**
1. Scalable to a peak of 10k clicks per second.
2. Low-latency analytics queries for advertisers (**sub-second**).
3. **Fault tolerant and accurate** — no lost click data.
4. **As real-time as possible** — queryable soon after the click.
5. **Idempotent click tracking** — never count the same click twice.

**Below the line:** fraud/spam detection, demographic/geo profiling, conversion tracking.

---

## System Interface & Data Flow

(Core entities are replaced by the system interface for data-processing problems.)

- **Input:** ad click data from users.
- **Output:** ad click metrics for advertisers.

**Data flow:**
1. User clicks an ad on a website.
2. The click is tracked and stored in the system.
3. The user is redirected to the advertiser's website.
4. Advertisers query the system for aggregated click metrics.

---

## High-Level Design

### 1) Click → redirect to the advertiser
An **Ad Placement Service** (black box — targeting/serving out of scope) places ads with their creative + metadata (redirect URL). Clicks hit our `/click` endpoint, which tracks then redirects.

**Good: Client-side redirect** — ship the redirect URL with the ad; browser navigates directly while a parallel POST tracks the click.
- *Challenge:* users can reach the advertiser without us knowing (grab the URL, browser extensions) → click-data discrepancies.

**Great: Server-side redirect** — click hits our server, we track it, then respond with a **302 redirect** to the advertiser.
- Guarantees every click is tracked; also lets us append tracking parameters.
- *Challenge:* added complexity/latency — the system must respond quickly under load.

### 2) Advertisers query metrics at 1-minute granularity

**Bad: Store and query from the same database**
Store raw click events (EventId, AdId, UserId, Timestamp) and run `GROUP BY`/`COUNT(DISTINCT UserId)` queries on demand. At 10k clicks/sec the DB becomes a bottleneck and queries are slow — breaks the low-latency requirement.

**Good: Separate analytics database with batch processing**
- Raw events → write-optimized **event store (Cassandra)** — LSM-tree engine (commit log → memtable → SSTables) handles heavy writes, but SSTables aren't good at range queries/aggregations, hence pre-aggregation.
- A cron kicks off a **Spark** job every N minutes that map-reduces raw events into (AdId, minute timestamp, click counts) rows in an **OLAP database** (Redshift/Snowflake/BigQuery) — columnar storage makes COUNT/SUM/AVG over millions of rows fast.
- Scale check: 10k clicks/sec × 5 min = 3M events ≈ 300MB/batch — small enough for one machine; Spark isn't strictly needed but gives a distribution framework and a well-understood MapReduce paradigm.
- Why not a **time-series DB** (InfluxDB/TimescaleDB)? TSDBs suit low-cardinality "metric X over range Y" queries; we have millions of AdIds and multi-dimensional slicing (device, geo, campaign) — OLAP handles high cardinality better. TSDB is reasonable only if requirements truly stay simple; know the trade-offs.
- *Challenges:* batch delay — data is always minutes old; traffic spikes make the next batch bigger, which can run longer than the batch interval → cascading staleness exactly when advertisers care most (big launches). A queue would absorb write spikes but not fix latency.

**Great: Real-time analytics with stream processing**
- Click Processor writes each event to a **stream (Kafka/Kinesis)**; a **stream processor (Flink / Spark Streaming)** aggregates in real-time and flushes windowed results to the OLAP DB.
- Why Flink over plain Kafka consumers keeping in-memory counts (which is a reasonable *mid-level* answer)? Flink provides windowed aggregations with **event-time semantics** (out-of-order events land in the right minute bucket), **watermarks** (knowing when a window can close), **exactly-once guarantees**, and built-in fault tolerance with state recovery — painful and error-prone to build yourself.
- *Latency nuance:* with a 1-minute window, latency is similar to a 1-minute batch job — but it's far more realistic to shrink the Flink window (to seconds) than to run Spark every few seconds. Even better: keep minute-boundary aggregation but configure **flush intervals of a few seconds**, so the current minute's row is simply incomplete until the boundary — best of both worlds.

**Pattern — Scaling Writes:** 10k clicks/sec of ingest dwarfs advertiser read load; stream buffering (Kafka/Kinesis), pre-aggregation (Flink), and partitioning by AdId are all driven by high write throughput without data loss.

---

## Deep Dive 1: Scaling to 10k clicks per second

Walk each bottleneck:
1. **Click Processor Service:** horizontal scaling with auto-scaling managed services + load balancer.
2. **Stream:** Kafka/Kinesis scale but need configuration — Kinesis caps at 1MB/s or 1000 records/s **per shard**. **Shard by AdId** so each AdId's events stay together and processors read shards in parallel.
3. **Stream Processor:** scale Flink horizontally — separate job per shard aggregating that shard's AdIds.
4. **OLAP DB:** managed warehouses (Snowflake/BigQuery) auto-scale; for self-managed (ClickHouse), **shard by AdvertiserId** so an advertiser's dashboard query (all their ads) hits one node. Monitor query SLAs.

**Hot shards:** a viral ad (Nike + LeBron) funnels all clicks to one shard → latency and possible data loss. Fix: append a random number to the partition key for popular ads (by spend or click volume): `AdId:0-N`. Flink strips the suffix when writing to OLAP and upserts with SUM aggregation so concurrent partition writes combine correctly (cleaner for query performance than storing sub-keys and aggregating at query time).

## Deep Dive 2: Never lose click data

- **Stream retention:** Kafka replicates across brokers, Kinesis across AZs; enable persistence with e.g. a **7-day retention period** so a crashed processor can replay what it missed.
- **Checkpointing (know when NOT to use it):** Flink checkpoints state to S3 and resumes after failure — valuable for big windows (day/week of in-memory state). Here windows are ~1 minute: a crash loses at most a minute of aggregation, and we can replay from the stream from a known timestamp. Pushing back on checkpointing "because the windows are tiny" is a **seniority signal** — think critically instead of pattern-matching.
- **Reconciliation (Lambda architecture):** clicks = money, and correctness vs. latency is a real tension. Continuously dump raw events to a **data lake (S3)** via Kafka Connect S3 Sink / Kinesis Data Firehose (no extra load on Flink). Run a periodic (hourly/daily) **Spark batch job** re-aggregating raw events; compare against the stream results, investigate discrepancies, and correct the OLAP data. This is a **Lambda architecture**: speed layer (Flink) for low latency + batch layer (Spark) as the source of truth for correctness.

## Deep Dive 3: Idempotency — preventing duplicate/abusive clicks

(Fraud detection is out of scope, but dedup the same click.)

**Bad: userId in the click payload**
Require login; dedup on (userId, adId), done *before* the stream (dedup must span aggregation windows — duplicates straddling a minute boundary would count twice).
- *Challenges:* requires all users logged in; and it's wrong for **retargeting** — the same ad is intentionally shown to the same user multiple times, so the real requirement is one click per user per **ad instance**.

**Great: Unique impression ID (the chosen solution)**
- Ad Placement Service generates a **unique impression ID per ad instance rendered** (1000 users seeing the same Nike ad = 1000 impression IDs). It's the idempotency key sent with the ad and returned with the click.
- **Dedup before the stream** (Flink can't dedup across window boundaries): check a cache for the impression ID — present → duplicate, ignore; absent → **write to the stream first, then add to cache** (if the cache update fails you get an occasional duplicate that reconciliation catches; a lost click can't be recovered).
- **Anti-forgery:** malicious users could send unique fake impression IDs. **Sign the impression ID + adId with an HMAC** (secret key); verify on click. Prevents replaying harvested IDs against other ads. HMAC verification costs microseconds — negligible latency.
- *Challenges:* added complexity; cache could bottleneck — but 100M clicks/day × 16 bytes ≈ **1.6GB** (tiny). Use **Redis Cluster** with a replica and Redis persistence (RDB/AOF) for safety.

## Deep Dive 4: Low-latency advertiser queries

Mostly solved by pre-aggregation (batch or streaming) into OLAP. Remaining slowness: aggregating over large windows (days/weeks/years). Fix: **pre-aggregate at coarser granularities** (daily/weekly tables via a nightly cron); advertisers query the coarse table and drill down as needed. It's effectively caching — trading storage for query performance on common queries.

## Final Design
Click Processor (server-side 302 redirect, HMAC-verified impression IDs, Redis dedup cache) → Kafka/Kinesis (sharded by AdId, hot-shard suffixing, 7-day retention, Firehose/Connect dump to S3) → Flink (event-time minute windows, frequent flushes) → OLAP DB (sharded by AdvertiserId, coarse pre-aggregation tables) ← advertiser queries; periodic Spark reconciliation from S3 corrects OLAP.

---

## What is Expected at Each Level?

### Mid-level (E4)
- ~80% breadth / 20% depth; interviewer probes basics; you drive early, they may drive deep dives.
- **Bar:** understand the need to pre-aggregate data and at least propose a **batch processing** solution; problem-solve effectively when probed on idempotency and database choices.

### Senior (E5)
- ~60% breadth / 40% depth; know how batch map-reduce works and how Flink real-time processing works at a high level; articulate trade-offs.
- **Bar:** speed through the high-level design; spend time on scaling optimizations, reducing click-to-query latency, and fault tolerance; justify technology choices. Ideally recognize the need for real-time processing and contrast it with batch — a fully fault-tolerant solution and full depth aren't required; a couple of deep dives done well is enough.

### Staff+ (E6+)
- ~40% breadth / 60% depth; high proactivity; practical, experience-backed technology choices.
- **Bar:** clearly weigh batch vs. real-time processing trade-offs in detail; propose a fault-tolerant solution; discuss database-choice and data-storage-strategy implications for performance and scalability. May choose different deep dives, but should drive deep and ideally teach the interviewer something new.
