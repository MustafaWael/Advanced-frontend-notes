---
tags: [system-design, backend, caching, interview]
module: "30 - Backend System Design"
priority: must-know
status: not-started
aliases: [cache-aside, write-through, cache stampede, hot keys]
verified_on: 2026-07-17
version_scope: "Latency figures and Redis/Valkey references — recheck against 30/09 and 30/11 before quoting exact numbers"
---

# Caching

## Maturity Target

- Priority: #must-know
- Study time: 45 minutes
- Interview signal: Introduce caching by naming the bottleneck, the pattern (cache-aside by default), eviction, and the invalidation + failure story — not "add Redis."
- Production signal: You recognize the client-side versions (HTTP cache, query cache, dedup) as the same patterns and design invalidation deliberately.
- Dependencies: [[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling and Databases]], [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]

## Source Anchors

- [HelloInterview — Caching](https://www.hellointerview.com/learn/system-design/core-concepts/caching)
- [Redis docs](https://redis.io/docs/latest/)

## 1. Concept

Simple version: caching keeps a fast copy of expensive-to-fetch data close to where it's needed. A well-indexed point read from Postgres is often only a few ms server-side, but under load — cold cache, contention, an expensive join or aggregation, plus the network hop — it climbs into tens of ms and eats primary-DB capacity; a hit on an in-memory store like Redis is one ~0.5–1 ms hop and offloads that work entirely. The win is latency *and* throughput relief; the cost is a second copy that can go stale. (See [[30 - Backend System Design/09 - Numbers to Know|Numbers to Know]] for the latency hierarchy — and don't quote "50ms Postgres" as a fixed fact; it's workload-dependent.)

**Where to cache** (layer outward only as needed): in-process (app memory, fastest, not shared) → external (Redis/Valkey — the interview default, shared across app servers) → CDN (media/edge, origin→far user ~250–300ms vs edge ~20–40ms) → client-side (browser/HTTP cache).

**Cache architectures:**

- **Cache-aside (lazy)** — app checks cache; hit returns; miss → read DB, populate cache, return. The default; if you remember one, this. Downside: extra latency on misses, brief inconsistency window.
- **Write-through** — write to cache, which synchronously writes to DB before returning. Reads always fresh, writes slower; risks the dual-write problem.
- **Write-behind (write-back)** — write to cache, flush to DB asynchronously. Very fast writes; data loss if the cache dies before flush. Metrics/analytics.
- **Read-through** — cache is a proxy that fetches on miss itself; CDNs are this.

**Eviction vs expiration** (distinct, often conflated): *eviction* is what the cache drops under memory pressure — LRU (default, drops least-recently-used) / LFU (keeps stably-popular keys) / FIFO (rare). *Expiration* is TTL — a per-key deadline for freshness regardless of memory. You use both together: TTL bounds staleness, the eviction policy handles capacity.

**The three classic problems:**

- **Stampede / thundering herd** — a hot key expires and thousands of concurrent requests all miss and hit the DB at once. Fix: **request coalescing (single-flight)** — one request rebuilds, the rest wait for its result; plus cache warming.
- **Consistency** — cache and DB disagree during the write window. Fix: invalidate-on-write, short TTLs, or accept eventual consistency for feeds/metrics.
- **Hot keys** — one key (`user:taylorswift`) gets millions of req/s and overloads its node. Fix: replicate the key across nodes, local in-process fallback, per-key rate limiting.

> [!tip] Frontend mirror: every one of these has a client twin. HTTP cache with `ETag`/`Cache-Control` is read-through you configure via headers; a query cache (React Query) is cache-aside with the component as the app; request deduplication is client-side single-flight against a stampede; stale-while-revalidate is "short TTL, serve stale, refresh in background." See [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]] and [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]].

## 2. Why It Matters

Caching is the single most common scaling lever and the one candidates most often bolt on carelessly ("add Redis"). The disciplined approach is the 5-step introduction: identify the bottleneck with a number, decide *what* to cache and its key, choose the architecture, set eviction/TTL, then address the downside (invalidation + what happens when the cache dies). The last step is where seniority shows — a cache that, when it fails, sends every request to a DB sized for cache-hit-rate traffic causes a cascading outage.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: the home feed is cached in Redis with a 60s TTL. Every minute at the expiry tick, latency spikes and the DB CPU briefly redlines.

Trace: **cache stampede.** At `t=60s` the key expires; every concurrent request misses simultaneously and independently recomputes the expensive feed query, hammering the DB in a thundering herd — the backend twin of a client firing duplicate requests for the same data.

Fix: **request coalescing** — the first request to miss takes a short lock and rebuilds the value; concurrent requests wait for that single rebuild instead of each hitting the DB. Optionally, probabilistic early expiration (refresh slightly before TTL) so the rebuild happens off the cliff edge.

```text
miss → acquire single-flight lock on key
        ├─ winner: recompute, set cache, release
        └─ others: block on lock, then read the freshly-set value
```

Tradeoff: coalescing adds coordination (a lock per hot key) and a small latency for the waiters; if the rebuild is slow, they wait. Alternative — never let it expire, refresh in the background (cache warming) — trades freshness precision for smoothness.

## 4. Interview Answer

Short answer:

> Introduce caching only after naming the bottleneck with a number — "200M reads/day, 30ms/query, we need sub-10ms." Default to external cache-aside with Redis, LRU plus a TTL, and design invalidation deliberately: invalidate on write, or accept a bounded staleness window. Then address failure — if the cache dies, requests fall back to a DB that must not be sized only for cache-hit traffic, so add circuit breakers and coalescing.

Deeper answer:

> The three problems that separate levels are stampede, consistency, and hot keys. Stampede is solved with single-flight coalescing so one request rebuilds a hot key while others wait, not everyone hammering the DB. Consistency is a spectrum choice — strong needs write-through or invalidate-on-write; feeds and metrics tolerate eventual. Hot keys need replication or a local fallback because even a 100% hit rate can overload one node. And "don't cache everything" is itself signal — a well-indexed database is often enough, and every cache you add is an invalidation problem you now own.

## 5. Practice

1. <details><summary>Walk the five steps to introduce caching in an interview.</summary>1) Identify the bottleneck with numbers (reads/s, latency). 2) Decide what to cache and its key (`user:123:profile`) — read-often, change-rarely, expensive. 3) Choose architecture (cache-aside default). 4) Set eviction + TTL (LRU + 10min, invalidate on update). 5) Address downsides: invalidation strategy, cache-failure fallback + circuit breaker, stampede coalescing. Pick one or two relevant problems, don't list all.</details>
2. <details><summary>Cache-aside vs write-through: when each?</summary>Cache-aside (default): lazy, lean cache, tolerates a brief stale window — most read-heavy systems. Write-through: reads must always be fresh and slightly slower writes are acceptable; you pay dual-write risk and can pollute the cache with never-read data.</details>
3. <details><summary>Why can a hot key overload a node even at a 99% hit rate?</summary>Hit rate measures how often you avoid the DB, not how much load lands on one node. A single key taking millions of requests/second saturates the CPU/network of the one node/shard that owns it regardless of hits. Fix by replicating the key across nodes and load-balancing reads, or keeping it in an in-process local cache.</details>

## Related Notes

- [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]
- [[28 - Frameworks and Application Architecture/06 - Server State|Server State]]
- [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
- [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]] (Redis/Valkey)
