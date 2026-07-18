# Time Series Databases

**Source:** https://www.hellointerview.com/learn/system-design/deep-dives/time-series-databases

Learn the concepts behind time-series databases like LSM trees, append-only storage, and delta encoding.

---

## The Problem Space

The patterns that enable high-throughput time-series databases (TSDBs) each have wider applicability to distributed systems — especially infra-style system design interviews. None of the ideas is terribly complex; the magic is in how they're combined.

> **Caveat first:** just because you have time-series data doesn't mean you need a time-series database! The Top-K problem is a classic example where a TSDB seems helpful but actually makes the problem harder (it requires sorting/aggregating across a huge number of series — something most TSDBs aren't designed for). Stretch general-purpose databases (Postgres, DynamoDB) to fit your needs; only reach for specialized tech when you hit a true bottleneck. Understanding TSDB limits tells you when they apply.

### Motivating example

Monitoring system for a cloud provider: 100,000 servers × 5 metrics every 10 seconds = **50,000 metrics/second, ~4.3 billion data points/day**. Users query dashboards, alerts, and week-old debugging data.

Vanilla Postgres with a `metrics(timestamp, host, metric_name, value)` table:
- ~30 billion rows/week; even with indexes, "average CPU for host-42 over the past hour" is painfully slow.
- Write performance degrades as you add indexes; 50k+ writes/sec (with bursts) crushes a single instance.
- Storage is wildly inefficient: repeating full host/metric names balloons each point to 50–100 bytes when the real information (timestamp + float) is ~16 bytes.

TSDBs like **InfluxDB, TimescaleDB, and Prometheus** are built for exactly this workload — typically **10–100x better** than a general-purpose DB for their target workload.

---

## The Building Blocks

### 1. Append-Only Storage

**If you're writing a lot of data, don't update data in place — always append to the end of a file.**

- Traditional update: seek to row's location → read → modify → write back. Random I/O is the most frequent cause of performance problems (spinning disks: 100–200 random ops/sec; even SSDs strongly prefer sequential access).
- Append-only: every point goes to the end of the current file. No seeking, no read-before-write. SSDs handle hundreds of thousands of sequential writes/sec; even spinning disks manage tens of thousands.

```
Traditional: [Seek to block 4752] → [Read] → [Modify] → [Write] → [Seek...] → ...
Append-only: [Write to end] → [Write to end] → [Write to end] → ...
```

But if we only append, how do we organize data for reading? →

### 2. LSM Trees (Log-Structured Merge Trees)

The secret sauce behind many high-write-throughput databases (InfluxDB, Cassandra, LevelDB). Core idea: **transform expensive random writes into cheap sequential writes, then reorganize data in the background for reads.**

1. **Write to memory (memtable):** incoming data goes into an in-memory sorted structure (red-black tree or skip list). Blazingly fast — RAM only. Kept sorted so the flushed file is sorted too: sorted files allow binary search for point lookups, efficient range queries (adjacent keys together), and efficient merge-sort during compaction.
2. **Flush to disk (SSTable):** when the memtable fills, it's written as an immutable **Sorted String Table** — a single sequential write. Memtable is cleared.
3. **Background compaction:** many SSTables accumulate and reads get expensive (multiple files to check). Compaction merges smaller SSTables into larger ones, removing duplicates and tombstones (deleted-data markers).

**Key property:** writes never block on reads — the memtable handles new data while background threads organize older data.

**Tradeoffs (not free):**
- Read performance can suffer — you may need to check multiple SSTables to find a value.
- **Write amplification** — data gets rewritten multiple times during compaction.
- Reach for LSM when you have a high-write workload **and** you're willing to trade some read performance for write performance.

### 3. Delta Encoding and Compression

Time-series data's unique property: **adjacent values are often similar** (CPU: 45.2, 45.3, 45.1, 45.4).

**Delta encoding** — store differences instead of absolutes:
```
Raw values:     [45.2] [45.3] [45.1] [45.4]
Delta encoded:  [45.2] [+0.1] [-0.2] [+0.3]
```
Small deltas + **variable-length encoding (varint)** = small numbers stored in 1–2 bytes instead of 8. (varint: 1 takes 1 byte, 1,000,000 takes 3.)

**Timestamps — delta-of-delta encoding:** timestamps are often perfectly regular (every 10s):
```
Raw timestamps:   1000, 1010, 1020, 1030, 1040
Deltas:             10,   10,   10,   10
Delta-of-deltas:    10,    0,    0,    0
```
Facebook's Gorilla paper showed timestamps compress to as low as ~1 bit per value on average.

**Float values — XOR-based compression:** XOR two similar floats and most bits are zero; store only the position of the first differing bit and the meaningful bits after. In practice ~1.37 bytes per value vs. 8 for a raw double.

> Don't memorize "1.37 bytes" — the core idea is that data at rest with lots of redundancy compresses extremely well, and time-series data is the prime example.

### 4. Time-Based Partitioning (Sharding by Time)

Group data into partitions by time window (per day/week). Partitions don't *necessarily* live on different machines, but can if needed.

- **Writes are localized:** all incoming data goes to the current ("now") partition.
- **Reads are efficient:** "last hour of data" → the DB knows exactly which partitions to touch; skips last month entirely.
- **Retention becomes trivial:** keep 7 days? Just **drop partitions** older than 7 days — no expensive DELETE scans, just delete old files.

Nearly universal: TimescaleDB calls them "chunks"; Prometheus and custom systems do the same.

### 5. Bloom Filters for Read Optimization

LSM means a value might be in any of several SSTables; each check risks a disk read. Worst case: a long-range query seeking a single series across many partitions.

A **Bloom filter** is a probabilistic structure that answers "definitely not here" or "maybe here" with **zero disk I/O**. Each SSTable keeps a Bloom filter of its keys; the DB checks the filter first and skips files that say "not here" with absolute certainty. False positives possible; **false negatives never**.

```
SSTable-1 filter: "not here"   → skip (no disk read)
SSTable-2 filter: "not here"   → skip
SSTable-3 filter: "maybe here" → check (disk read)
SSTable-4 filter: "not here"   → skip
```

Well-tuned: ~10 bits per key, ~1% false positive rate. Turns dozens of potential disk reads into one or two.

### 6. Downsampling and Rollups

Raw 10-second resolution is great for debugging recent issues; nobody needs it for last year's data. Downsampling reduces resolution of older data, trading precision for storage.

Typical policy:
- **Last 24 hours:** full resolution (10s)
- **Last 7 days:** 1-minute averages
- **Last 30 days:** 5-minute averages
- **Last year:** 1-hour averages

Rollups are computed in the background, storing pre-aggregated values (min, max, sum, count). "Average CPU last month" reads the 5-minute rollup table — 288x less data than raw. A form of pre-computation trading storage/write amplification for dramatically faster historical reads. (See the Ad Click Aggregator breakdown for this in action.)

> **Interview gold:** downsampling frequently shows up as a **requirements negotiation**. Interviewer: "store 10s samples for 1 year." You: "that's a ton of data — do we really need fine resolution past a week? Can we downsample to 5-min averages after a month?" (a) anticipate the future problem, (b) explain the challenge, (c) offer an alternative. Even if they say no, this thinking-outside-rigid-requirements is a hallmark of staff+ candidates.

### 7. Block-Level Metadata

Maintain metadata per block — min/max timestamps, sometimes min/max values — enabling **block pruning**. If a query asks for CPU > 10% and a block's metadata says it only contains 0–5%, skip the entire block without reading it. Combined with time partitioning, another layer of filtering. (Same query-planning idea as in Elasticsearch.)

---

## Putting It Together: A Time-Series Storage Engine

### The Data Model

- **Measurements/metrics** — like tables (`cpu_usage`, `memory`)
- **Tags** — indexed metadata for filtering (`host=server-1`, `region=us-west`)
- **Fields** — the actual measured values (`value=45.2`), **not indexed**
- **Timestamps** — when the measurement was taken

```
cpu_usage,host=server-1,region=us-west value=45.2 1699999200000000000
└──────── measurement + tags ────────┘ └─field──┘ └───timestamp─────┘
```

> **Common trip-up:** use **tags** for metadata you'll filter by (host, region, service); use **fields** for the values you measure. Getting this wrong → poor query performance or cardinality explosion (below).

### The Storage Engine

1. **Write-Ahead Log (WAL):** data goes to the WAL first for durability/crash recovery.
2. **In-memory buffer** (the memtable), organized by measurement + tag combination.
3. **Flush to disk** as immutable files with compressed timestamps and values.
4. **Background compaction** merges small files, removes deleted data.

File format: blocks of (delta-of-delta + varint encoded timestamps, XOR-compressed values), with an **index at the end mapping series keys → block offsets**. Looking up a series = seek to index, seek to data — two disk ops regardless of file size.

### Query Execution

```sql
SELECT mean(value) FROM cpu_usage
WHERE host = 'server-1' AND time > now() - 1h
GROUP BY time(5m)
```

1. **Identify relevant partitions** from the time filter.
2. **Locate series** via the in-memory tag index (host='server-1').
3. **Read from buffer + disk files** (recent data in memory, older on disk); merge.
4. **Apply aggregations as a streaming operation** — no need to load everything into memory.

Key insight: TSDBs exploit **time locality** (recent data in memory/recent files) and **series locality** (related points stored together) to minimize disk access.

### Worked Example: Multi-Tag Query

8 data points across 4 servers → each unique measurement+tags combination is a **series** (4 series). Data for each series is stored together in compressed blocks (~13 bytes stored vs. 32 raw per block — ~60% reduction from delta-of-delta + XOR alone).

The DB also keeps an in-memory **tag index** — essentially an **inverted index** (the same structure that powers Elasticsearch), mapping tag values → series:

```
region=us-west → [Series 1, Series 2]
env=prod       → [Series 1, Series 2, Series 3]
...
```

Query: `WHERE region='us-west' AND env='prod'`:

1. Consult tag index for each predicate.
2. **Intersect** the series sets → [Series 1, Series 2].
3. Look up block locations in the file index.
4. Read **only those blocks** (skip the us-east blocks entirely).
5. Apply time filter.
6. Compute aggregation: mean([45.2, 47.1, 62.3, 61.8]) = 54.1.

**Why it's fast vs. Postgres:** the tag index identifies matching series without scanning data; the columnar, series-oriented storage means needed data is physically co-located. Postgres would find row IDs by index, then fetch rows from scattered disk locations — millions of scattered reads kill performance. *Writes are optimized to assist reads.*

---

## Where Things Break: The Cardinality Problem

**Cardinality** = the number of unique tag combinations. 1,000 hosts × 50 metrics = 50,000 series — manageable. Add a `user_id` tag with 10M unique users → **500 billion potential series**.

Why it breaks: TSDBs keep an **in-memory index of all series** — one entry per unique tag combination. Billions of series → out of memory; queries slow as the index balloons.

**Rule:** user IDs, request IDs, or any high-cardinality value can only be stored as **fields**, never tags. You can write them, but you lose all the read-performance benefits.

---

## Summary & Interview Takeaways

The big lesson: TSDBs make **strong assumptions about the data** (low-cardinality tags, highly regular timestamps, small deltas between points) and exploit each for massive performance gains. **Violate the assumptions and the system becomes *worse* than a general-purpose database.**

> Most candidates stumble by not understanding a database's data assumptions and proposing a solution that performs worse (or not at all). Understanding these assumptions is a hallmark of staff+ candidates. If uncertain, fall back to tech you know rather than winging it.

The patterns (each applicable well beyond TSDBs):

- **Append-only storage** — random I/O → sequential I/O
- **LSM trees** — high write throughput by deferring organization to background compaction
- **Delta encoding + specialized compression** — exploit the structure/redundancy of the data
- **Time-based partitioning** — localized writes, trivial retention (drop partitions)
- **Bloom filters** — skip SSTables without disk reads
- **Downsampling/rollups** — trade precision for storage on historical data
- **Block-level metadata** — prune blocks during queries

When you see a system handling millions of events per second, it's not magic — it's these pieces combined with careful data modeling.
