# 14 - YouTube Top K (Design YouTube's Top K Videos Feature)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/top-k
**Difficulty:** Hard · Patterns: Scaling Reads, Scaling Writes

Top-K is a classic problem with many variants — each interview can be unique, and interviewers often change requirements or shift scope to test adaptability. Ask targeted questions and follow the interviewer's lead (some have a specific solution in mind — adjust rather than argue). Here: a huge stream of YouTube view events (a firehose of VideoIDs); at any moment we want to query, **precisely**, the top K most-viewed videos for the last 1 hour, 1 day, 1 month, and all time. Scale cues: YouTube Shorts had **70B views/day**; ~1 hour of content uploaded every second.

---

## Functional Requirements

Requirement clarification is especially load-bearing for top-K — small changes dramatically alter the design. Key clarifications:

- **Windows:** we support "last 1 hour / 1 day / 1 month / all time".
- **Window semantics:** *sliding* windows = [T−1h, T] (at 10:06 → 9:06–10:06); *tumbling* windows = last full hour on hour boundaries (at 10:06 → 9:00–10:00). **Propose tumbling windows** (and let the interviewer object) — shows foresight and is easier to handle.
- **Arbitrary time periods** (e.g. "June 2024 queried in October 2025") would prevent precomputation → explicitly put below the line.
- **Bound K:** cap results at 1k. (Top 1M ≈ you want the full dataset — another system's job.)

**Core:**
1. Clients can query the top K videos for all-time (max 1k results).
2. Clients can query *tumbling windows* of 1 {hour, day, month} and all-time (max 1k results).

**Below the line:** arbitrary time periods; arbitrary start/end points (all queries look back from now).

## Non-Functional Requirements

**Core:**
1. Tolerate at most **1 minute delay** between a view occurring and it being tabulated (events arrive late in distributed systems).
2. **Precise results** — no approximation (revisit as a stretch deep dive).
3. Return results within **10's of milliseconds** — this eliminates many designs; we must favor **precomputation** (serve from cache).
4. Handle a **massive number of views/sec** (quantified later).
5. Support a **massive number of videos** (quantified later).

Tip: quantities on NFRs drive decisions; estimate when it influences the design.

## Core Entities

1. **Video** — the video being viewed.
2. **View** — the view event.
3. **Time Window** — "all time", "last hour", "last day", "last month".

## API

```
GET /views/top-k?window={WINDOW}&k={K} -> { videoId: string, views: number }[]
```
Pagination unnecessary — responses capped at 1k and clients specify K. Don't dawdle here: senior candidates especially must spend effort on the "interesting" parts — over-investing in trivial pieces signals you can't tell complex from trivial.

---

## High-Level Design

Plan: start with a basic, suboptimal working system (all-time first, then windows), earmark bottlenecks aloud, optimize in deep dives. Better to start with a *working* system and optimize than start "optimal" and try to make it work.

### 1) All-time top K
- Assume a **Kafka stream of view events** already exists (another YouTube system records views to this ViewEvent topic, **partitioned by video ID**) — skips boilerplate.
- A simple **View Consumer** service pulls events and increments per-video counters in **Postgres**. (Acknowledge the elephant in the room: that's a LOT of writes for one Postgres instance.)
- Reads: a **Top-K Service** behind a load balancer queries `SELECT videoId, views FROM VideoViews ORDER BY views DESC LIMIT k` — with an index on `views`, this is effectively **O(k)** (the index is a sorted list; grab the top K).
- Cost: every write now updates the index — O(1) append becomes O(log n). Acknowledge and move on. Intuition for data flow is *the* key skill in data-intensive design questions.

### 2) Tumbling windows (hour/day/month)
- Add a **timestamp column** (truncated to the hour): one row per video per hour with views. Write volume unchanged, but **row count blows up** (revisit later).
- Read side: `SELECT videoId, SUM(views) ... WHERE timestamp BETWEEN windowStart AND windowEnd GROUP BY videoId ORDER BY SUM(views) DESC LIMIT k` (+ timestamp index). But this forces **scans** — processing billions of rows takes minutes/hours, not milliseconds. Earmark for deep dives.

---

## Deep Dive 1: Cutting queries to the database (Scaling Reads)

The 1-minute tabulation grace period is a gift: it enables caching/precomputation.

**Good: Cache the top K per window**
- Distributed cache (Redis/Memcached) at the Top-K Service; key `top-k:{window}:{truncated_timestamp}`, value = full response; TTL of a couple hours. Cache hits (the overwhelming majority) return sub-millisecond.
- *Challenges:* when the cache expires, (a) a flood of DB requests (partially fixable by **request coalescing** — one DB request per server per window, others wait) and (b) those requests all break the 10s-of-ms SLA.

**Great: Precompute the top K per window with a cron**
- A cron precomputes top K for each window on fixed intervals and **warms the cache**; the Top-K Service *only ever reads the cache*, never the DB. The cron "gets ahead" of expirations, fixing the SLA-break problem.
- *Challenges:* operational complexity (cron failure, lag monitoring — usually not probed deeply). Retain cache entries a couple hours so a late cron means briefly stale data instead of nothing.

## Deep Dive 2: Handling massive write volume (Scaling Writes)

**Estimation (do it when it influences the design — and it does here):**
```
70B views/day / 100k seconds/day = 700k TPS
Videos/day = 1 hr content/sec / (6 min/video) * 100k s/day = 1M videos/day
Total videos = 1M/day * 365 * 10 years ≈ 3.6B videos
Naive storage = 4B videos * (8B ID + 8B count) = 64 GB   ← per full per-video view set
```
(Use 100k s/day to keep math easy — estimation is about implications, not mental arithmetic.) Modern RDBMSs manage ~10k+ writes/sec/node; 700k TPS is way beyond.

**Sharding ingestion:** the ViewEvent topic is already partitioned by video ID — a natural "seam". Scale view consumers horizontally per partition; shard the DB by the same scheme (each shard holds a subset of videos; each consumer writes to its shard). Getting to ~10k TPS/shard needs ~**70 shards** — works but wasteful. Note: sharding breaks the single SQL top-K query — query **each shard's top K and merge** (manually or via Citus); taking the top K from every shard mathematically guarantees the global top K is included.

**Batching ingestion:** most views concentrate on few popular videos (Mr. Beast / Taylor Swift effect). Batch counts per video and flush periodically using **Flink**:
- `BoundedOutOfOrdernessWatermarkStrategy` (~30s, under our 1-minute budget) for late events; tumbling 1-hour windows aggregating views per video.
- Flink checkpoints + Kafka rewind give fault tolerance (replay from checkpoint offset).
- Writes become hourly bulk lumps (databases handle bulk far more efficiently) and shrink 2–100x (many views per video per hour collapse to one row). Shard count drops to ~**5–10**.

## Deep Dive 3: Optimizing the top-K window queries

Cache misses still hit very inefficient windowed queries: sum views per video over the window, then extract top K — hundreds of GB processed → minutes/hours. Moving it to Spark parallelizes but pays in cost/capacity; at senior+ levels, **simplify the problem, don't throw hardware at it**.

**Good: Aggregate at coarser granularity**
- Keep daily aggregates alongside hourly; monthly queries sum ~30 daily rows instead of 720 hourly rows. Implement via periodic rollup queries, or better, extra tumbling windows in the Flink job outputting to day/month tables. Top-K service picks the right granularity table.
- *Challenges:* rollup crons add load to an already strained DB; still expensive; worst-case freshness delayed by the whole write→cron→aggregate→write→read chain. Arguably acceptable (long windows change slowly, freshness expectations lower) — but we can do better.

**Great: Maintain aggregates for each window in the database (chosen)**
- Instead of aggregates for arbitrary time slices, keep a **current running aggregate per video per window**: `VideoViewsLastHour`, `VideoViewsLastDay`, `VideoViewsLastMonth` tables, each with an index on `views` → the top-K cron reads top K straight off the index, O(k).
- Flink still aggregates at hour grain; on each flush it updates the window tables rather than an hour-grain log.
- *Challenges:* complexity moves to writes (4 tables instead of 1). Postgres bulk-write optimizations exist (unlogged tables to skip WAL, delayed fsync, tuned batch sizes) — empirical, benchmark-driven, usually beyond interview scope.

**Great (with caveats): Do everything in Flink**
- Keep window aggregates in Flink's distributed state (RocksDB state backend for disk-scale state), compute top-K natively (rolling window aggregator keyed by videoId → top-K aggregator keeping a heap per window), and sink results directly to Redis every minute. **Eliminates Postgres and the cron entirely.** Kafka acts like a tape recorder — rewind offsets to the last good checkpoint on failure.
- *Challenges:* leans heavily on Flink knowledge; interviewers may push "do it without Flink" or demand low-level explanations, turning it into a coding/LLD interview. Elegant, but **generally not recommended for a system design interview**.

## Deep Dive 4: Supporting sliding windows

If we must support true sliding windows (last hour at 10:06 = 9:06–10:06), build on the window-aggregates solution:
- Flink aggregates at **minute** grain. Each minute: read the views from exactly T−60 minutes ago (the **decrement**), write the last minute's views (the **increment**) to VideoViews, and update `VideoViewsLastHour` by (increment − decrement). Same per window; for all-time the decrement is always 0.
- *Challenges:* now reading + updating, not just inserting — magnifies DB pressure; must retain **minute-grain data for a whole month** to decrement the "last month" window — wasteful.
- Mature alternatives to propose:
  - **Hybrid product cut:** sliding window only for "last hour", tumbling for day/month — matches product expectations (monthly top videos change slowly).
  - **Lagged Kafka consumer group:** one consumer group increments, a second reads the topic on a delay and decrements expired events. Needs 1-month+ Kafka retention, but drops the minute-grain table and leverages Kafka's log performance.
- **Don't** suggest Flink native sliding windows with a 1-minute slide: memory multiplies by 60 × 24 × 30 = **43,200x**. Impractical.

## Deep Dive 5: Approximation (Count-Min Sketch)

Top-K results rarely hinge on dozens of views (top videos differ by thousands), and top-K features are about trends, not financial leaderboards — so trading a little precision buys big efficiency.

**Count-Min Sketch (CMS):** estimates item counts in hundreds of MB instead of the ~64GB+ full hash table, using hash functions mapping items into a 2D counter array — it *forgets items* but remembers counts via hashes. API: `add(item, count)` and `estimate(item)` — no list operation, so pair CMS with a **sorted list / heap**:
1. On each view: `add` to the CMS, then `estimate` (an upper bound / decent approximation).
2. Insert (videoId, estimate) into a sorted list, truncated to 1000 entries (users can't query more).
3. Top K = the top of the sorted list.
Keep a sketch + sorted list per window.

**Good: Redis** — native CMS + sorted sets: per event, `CMS.INCRBY` → `CMS.QUERY` → `ZADD`; trim ZSET to 1000; optimize by skipping ZADD below a tracked lower bound.
- *Challenges:* durability — sketch and sorted set can diverge on failures; rebuilding from Kafka is slow; AOF recovery doesn't map to Kafka offsets. Don't hand-wave — the simplicity invites probing.

**Great: Flink** — keep the CMS and sorted list in Flink's checkpointed state; just custom job code, no new infra; restore from checkpoint + Kafka replay on node failure. More resilient and efficient than Redis.
- *Challenges:* again requires interviewer/candidate Flink fluency and low-level detail on job structure and state.

Sliding windows + CMS: if you only decrement previously incremented items, CMS supports `remove` with similar guarantees — possible in Flink/custom implementations but not Redis (no `CMS.DECRBY`). Well outside interview expectations.

## Deep Dive 6: Specialized databases?

General guidance: build from simple primitives you understand deeply rather than name-dropping specialized tech — interviewers probe for understanding, and they're more sympathetic if you understand *what gave rise to* a technology than if you just know its name. **Don't memorize "TimescaleDB isn't good for top-K"; do understand that billion-scale cardinality is the core challenge, addressed by precomputation and caching.**

**Bad: InfluxDB / Prometheus** (time-series with downsampling) — billions of videoIds as series/tags means `top()` queries become full scans; these engines can't support that cardinality. Great for one videoId's time series (a graph), terrible for querying across *all* graphs.

**Good: TimescaleDB** (Postgres + hypertables + continuous aggregates) — per-hour aggregates as a hypertable with a views index gives the same O(k) queries; **continuous aggregates** (materialized-view-like rollups) replicate our LastHour/LastDay/LastMonth tables with retention/compression policies. Notably, it ends up looking *a lot* like our hand-built solution — good data design converges. Still needs caching and sharding to meet SLAs.

**Good: Real-time OLAP (Druid / Pinot / ClickHouse)** — ingest from Kafka, roll up per-minute by videoId, query topN/groupBy over a time filter; each pre-aggregates on ingest differently:
- **Druid:** ingestion-time rollup by time bucket + videoId; background compaction re-rolls older data coarser.
- **Pinot:** star-tree indexes / materialized views prune most data for fixed top-K patterns; offline pre-aggregated segments per grain.
- **ClickHouse:** Materialized Views → SummingMergeTree/AggregatingMergeTree rollup tables (pressure on writes); fixed-window queries read rollups with `ORDER BY views DESC LIMIT K`.
- *Challenges:* flakiness at scale (node outages, compaction) threatens SLAs; expect "walk me through the ingestion process" — be ready to get detailed and teach.

---

## What is Expected at Each Level?

### Mid-level (E4)
- ~80% breadth / 20% depth; interviewer probes basics; you drive early, they may drive later stages.
- **Bar for Top K:** an end-to-end solution that probably isn't optimal; some insight into pinch points, solving some of them; familiarity with relevant technologies but with some mistakes.

### Senior (E5)
- ~60% breadth / 40% depth; intuitive about data flow; know streaming vs. batch and how to pick; articulate trade-offs; proactive about bottlenecks.
- **Bar:** a near-optimal end-to-end solution; identify most bottlenecks and proactively resolve them; weigh pros/cons of relevant technologies, ideally from experience.

### Staff+ (E6+)
- ~40% breadth / 60% depth; breeze through basics; exceptional proactivity; practical, experience-backed technology usage.
- **Bar:** expand into deep dives beyond the enumerated ones; speak to alternatives without needing to fully explore them. The hallmark: **seeing the solution space clearly and speaking to options with judgement and confidence.**
