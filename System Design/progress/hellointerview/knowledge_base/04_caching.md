# Caching

**Source:** [hellointerview.com — Caching](https://www.hellointerview.com/learn/system-design/core-concepts/caching)

Caching comes up almost every time you need high read traffic: the database becomes the bottleneck, latency creeps up, and the interviewer waits for you to say "cache." Reading a user profile from Postgres might take ~50 ms; from an in-memory cache like Redis, ~1 ms — a 50x latency improvement. Databases pay disk-access cost per query; memory sits close to the CPU. Caches reduce DB load and cut latency dramatically, but create new challenges around invalidation and failure handling.

## Where to Cache

### External Caching (the default)

A standalone cache service your app talks to over the network — Redis or Memcached. Scales well because every app server shares the same cache; supports eviction policies (LRU) and TTL expiration to control memory footprint. **In interviews, external caching with Redis is the default answer** — start here, layer on CDN or client-side caching only if the problem calls for them.

### CDN (Content Delivery Network)

Geographically distributed servers caching content close to users. Modern CDNs (Cloudflare, Fastly, Akamai) can cache public API responses, HTML pages, and run edge logic — but the most common and impactful use is still **media delivery**.

Flow: user requests an image → nearest edge server → cache hit returns immediately; miss fetches from origin, stores, returns; future regional users get it instantly.

Numbers: origin in Virginia serving a user in India adds **250–300 ms** latency per request; a nearby CDN edge serves the same image in **20–40 ms**. In interviews, the safest reason to introduce a CDN is serving static media at scale.

### Client-Side Caching

Data stored close to the requester: browser HTTP cache/localStorage, mobile app local storage, or even client libraries (Redis clients cache cluster metadata — nodes and slot assignments — to route requests without querying the cluster each time). Backend has limited control: data goes stale, invalidation is harder. Examples: Strava keeping run data on-device offline and syncing later; a browser reusing a downloaded image.

### In-Process Caching

Use the app server's own memory for data requested repeatedly — faster than Redis because there's no network call. Good for small, frequently accessed, rarely changing values:

- Configuration values, feature flags
- Small reference datasets
- Hot keys, rate limiting counters
- Precomputed values

Limitation: each instance has its own cache — not shared; invalidation on one instance isn't seen by others. Mention only as an **optimization layer** after an external cache.

## Cache Architectures (Patterns)

### Cache-Aside (Lazy Loading) — default

1. App checks the cache
2. Hit → return
3. Miss → fetch from DB, store in cache, return

Only caches data when needed (lean cache); downside is extra latency on misses. **If you remember one pattern, make it this one.**

### Write-Through

App writes only to the cache; the cache synchronously writes to the DB before returning — the write isn't complete until both are updated. Requires cache infrastructure supporting write-through (a caching library with a data-store plugin; Redis doesn't natively support it).

Tradeoffs: slower writes (wait for both); can pollute the cache with never-read data; still suffers the **dual-write problem** (cache succeeds, DB fails, or vice versa → inconsistency; needs retries/error handling or acceptance that perfect consistency needs distributed transactions). Use when **reads must always be fresh** and slightly slower writes are tolerable. Less common than cache-aside in interviews.

### Write-Behind (Write-Back)

App writes only to the cache; the cache batches and flushes to the DB asynchronously. Very fast writes, but if the cache crashes before flushing you **lose data**. Use for **high write throughput with acceptable eventual consistency / occasional loss** — analytics and metrics pipelines.

### Read-Through

Cache acts as a smart proxy; the app never talks to the DB directly. On a miss the cache itself fetches, stores, returns. The read-side equivalent of write-through; often combined with it. Centralizes caching logic but adds complexity and needs specialized libraries/services. **CDNs are a form of read-through cache.** Rarely worth proposing in interviews outside CDN discussions.

## Cache Eviction Policies

- **LRU (Least Recently Used):** evicts the item unused longest; tracks access order (linked list/ring buffer) for constant-time eviction. Default in many systems — adapts to most workloads.
- **LFU (Least Frequently Used):** evicts the least-accessed item via per-key counters (sometimes approximate LFU to reduce tracking cost). Good when certain keys stay popular over time — trending videos, top playlists.
- **FIFO:** evicts the oldest inserted item (simple queue); ignores usage patterns and may evict hot items — rarely used beyond simple layers.
- **TTL (Time To Live):** not an eviction policy per se — expiration times per key, combined with LRU/LFU to balance freshness and memory. Must-have when data must eventually refresh (API responses, session tokens).

## Common Caching Problems

### Cache Stampede (Thundering Herd)

A popular entry expires and many requests rebuild it simultaneously — a brief window where every request misses and hits the DB. Example: homepage feed cached with 60 s TTL expires at 12:01:00 → every concurrent request queries the DB → spike can cause cascading failures.

Handling:
- **Request coalescing (single flight):** only one request rebuilds; others wait for its result. Most effective.
- **Cache warming:** proactively refresh popular keys before expiry. Only helps with TTL-based expiration (not write-invalidation).

### Cache Consistency

Cache and DB return different values — common because systems read from cache but write to DB first, leaving a stale window (e.g., updated profile picture still old in cache). No perfect solution; pick per freshness needs:

- **Invalidate on writes:** delete the cache entry after DB update so it repopulates fresh.
- **Short TTLs** when slight staleness is tolerable.
- **Accept eventual consistency** for feeds, metrics, analytics.

### Hot Keys

One entry gets enormous traffic — e.g., Twitter's `user:taylorswift` key getting millions of req/s can overload a single Redis node/shard even with a high hit rate.

Handling:
- **Replicate hot keys** across multiple cache nodes and load-balance reads.
- **Local fallback cache:** keep extremely hot values in-process.
- **Rate limiting** on abusive per-key traffic patterns.

(Related pattern: Scaling Reads — viral content breaks traditional caching assumptions.)

## Caching in System Design Interviews

### When to Bring It Up

Don't jump straight to caching — establish the need first:

- **Read-heavy workload:** "10M DAU × 20 requests/day = 200M reads. Even indexed, 20–50 ms/query. A cache drops that under 2 ms and offloads the DB."
- **Expensive queries:** "Personalized feed joins posts/followers/likes and takes 200 ms. Cache the computed feed for 60 s, serve in 1 ms."
- **High database CPU:** "DB CPU at 80% peak just serving repeated reads; caching hot queries cuts DB load 70–80%."
- **Latency requirements:** "Sub-10 ms API target vs 30–50 ms DB queries — we have to cache."

Pattern: identify the problem, quantify with rough numbers, explain how caching solves it (see Numbers to Know).

### How to Introduce Caching (5 steps)

1. **Identify the bottleneck** — be specific: "profile queries hit the DB 500×/s at peak, 30 ms each."
2. **Decide what to cache** — data read frequently, changing rarely, expensive to fetch/compute (profiles read every page load, updated rarely; trending feed from expensive aggregations refreshed each minute). Define cache keys: `user:123:profile`, `trending:posts:global`.
3. **Choose the architecture** — usually cache-aside; write-through for strong consistency needs; write-behind for high-volume tolerant writes; CDN for static content; in-process for extreme hot keys.
4. **Set an eviction policy** — LRU is the safe default; TTL prevents staleness: "LRU + 10-minute TTL on profiles; invalidate immediately on profile update."
5. **Address the downsides** — invalidation strategy (delete on write / TTL / eventual consistency); cache failure ("if Redis dies, requests fall back to the DB; add circuit breakers to avoid a stampede; maybe a small in-process last-resort layer"); thundering herd ("probabilistic early expiration or request coalescing"). Pick one or two relevant problems, don't list everything. Staff-level: focus on important non-obvious scenarios.

## Conclusion

Caching is what you do when reading from the DB is too slow or too expensive. Core tradeoff: faster reads and reduced backend load vs staleness/invalidation complexity, failure-mode risk (cache down → DB crushed), and hot-key bottlenecks. Don't cache everything — show you know when a well-indexed database is enough.
