# 02 - Rate Limiter (Distributed)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-rate-limiter
**Author:** Evan King (Hello Interview) · **Difficulty:** Medium · **Patterns:** Dealing with Contention, Scaling Writes, Scaling Reads

> **What is a rate limiter?** It controls how many requests a client can make within a timeframe — a traffic controller for your API (e.g., 100 requests/minute per user, excess rejected with HTTP 429). Rate limiters prevent abuse, protect servers from traffic bursts, and ensure fair usage.

**Scope:** a **request-level, server-side** rate limiter for a social media platform's API (limiting HTTP requests, not business actions). Client-side rate limiting is complementary but can't be trusted for security.

---

## 1. Functional Requirements

**Core:**
1. Identify clients by **user ID, IP address, or API key** to apply appropriate limits.
2. Limit HTTP requests based on **configurable rules** (e.g., 100 requests/min per user).
3. When limits are exceeded, **reject with HTTP 429** plus helpful headers (remaining, reset time).

**Below the line:**
- Complex querying/analytics on rate limit data.
- Long-term persistence of rate limiting data.

## 2. Non-Functional Requirements

Ask the interviewer about scale — startup vs major platform completely changes the design. Assumed: **1M requests/second across 100M DAU**.

**Core:**
1. Minimal latency overhead (**< 10ms** per check).
2. Highly available; **eventual consistency OK** (slight cross-node enforcement delays acceptable).
3. Handle 1M req/s across 100M DAU.

**Below the line:** strong consistency across all nodes.

## 3. Planning Note

This question is asked very differently by different interviewers — some want low-level design (even code), others architecture and scale. The common path (followed here): balance **algorithm selection** with **high-level distributed design**. Spend minimal time on entities/interface; most time on algorithms + scaling.

## 4. Core Entities

- **Rules** — rate limiting policies: requests per window, which clients, which endpoints (e.g., "authenticated users: 1000 req/hour"; "search API: 10 req/min per IP").
- **Clients** — the entities being limited: user IDs, IPs, API keys, or combinations; each has usage state.
- **Requests** — incoming API requests with context (client identity, endpoint, timestamp) that determine which rules apply.

Flow: Request arrives → identify Client → look up applicable Rules → check usage → allow or deny.

## 5. System Interface

```text
isRequestAllowed(clientId, ruleId) -> { passes: boolean, remaining: number, resetTime: timestamp }
```

Return values also feed response headers like `X-RateLimit-Remaining` and `X-RateLimit-Reset`.

## 6. High-Level Design

### 6.1 Where should the rate limiter live, and how do we identify clients?

**Placement options:**

#### ❌ Bad: In-process (inside each app server)
- Fastest (in-memory, no network calls), but each server sees only its own traffic. With 5 servers, a "100/min" limit can effectively become 200+ depending on load-balancer routing. Only viable with a single server or if approximate limits are acceptable.

#### 👍 Good: Dedicated rate-limiting service
- App servers call a rate-limit microservice ("allow user 12345?"). Rich context available (subscription tier, endpoint, business logic like "extra requests on Black Friday"); precise global limits via centralized state.
- **Challenges:** an extra network round trip on *every* request; another point of failure (fail open vs fail closed dilemma); operational complexity (deploy, monitor, scale, replicate); must handle slow responses/timeouts/partitions.

#### ✅ Great: API Gateway / Load Balancer (chosen)
- Rate limiter runs at the edge; every request hits it first. Blocked requests never reach app servers ("bouncer at the club"). Most popular production pattern; centralized control without extra network hops per request.
- **Challenges:** limited context — only what's in the HTTP request (headers, URL, IP, auth tokens). "Premium users get 10x" only works if that's encoded in a JWT or similar. Also needs external fast state (Redis) with its own failure modes.

**Client identification** (gateway sees only the HTTP request):
- **User ID** — authenticated APIs; from JWT in the Authorization header.
- **IP address** — public/anonymous traffic; from `X-Forwarded-For` (beware NATs/corporate firewalls).
- **API key** — developer APIs; `X-API-Key` header.

Real systems **layer multiple rules** and enforce the **most restrictive** one that applies:
- Per-user ("Alice: 1000/hour"), per-IP ("100/min"), global ("50k/sec total"), endpoint-specific ("search: 10/min; profile updates: 100/min"). If Alice has used 50/1000 but her IP hit its limit, she's blocked.

### 6.2 The rate limiting algorithm

Acknowledge the options and pick one; you rarely need to implement it in a system design interview.

| Algorithm | How it works | Pros | Cons |
|---|---|---|---|
| **Fixed Window Counter** | Time in fixed buckets (e.g., 1-min); counter resets each window | Trivially simple: hash of clientId → (counter, window_start) | **Boundary effect**: 100 reqs at 12:00:59 + 100 at 12:01:00 = 200 in 2s; starvation within a window |
| **Sliding Window Log** | Store every request timestamp; drop entries older than the window, count the rest | **Perfect accuracy**, no boundary effects | Memory-heavy (1000 req/min = 1000 timestamps per user); scan overhead |
| **Sliding Window Counter** | Keep current + previous window counters; weight previous by how far into current window you are (30% in → count 70% of previous + all of current) | Near-sliding accuracy with just two counters per client | Approximation assumes even traffic distribution; math tricky to implement |
| **Token Bucket** ✅ | Bucket of tokens (burst capacity) refilled at a steady rate; each request consumes one; empty bucket = reject | Handles both sustained load and bursts; simple state: (tokens, last_refill_time) | Choosing bucket size/refill rate; cold-start (idle clients start with full buckets) |

**Choice: Token Bucket** — best balance of simplicity, memory efficiency, and real (bursty) traffic patterns; used by companies like Stripe.

### 6.3 Storing bucket state — centralized Redis

In-gateway-memory state recreates the in-process coordination problem (Alice's 50 reqs to Gateway A + 50 to Gateway B each look fine locally). So use **Redis as the central source of truth** for all token buckets.

Flow for a request from Alice:
1. Gateway fetches state: `HMGET alice:bucket tokens last_refill`.
2. Compute refill: tokens += elapsed_time × refill_rate (capped at capacity).
3. Update atomically:
```text
MULTI
HSET alice:bucket tokens <new_token_count>
HSET alice:bucket last_refill <current_timestamp>
EXPIRE alice:bucket 3600
EXEC
```
4. If ≥ 1 token: allow and decrement; else reject.

**Race condition!** The read (`HMGET`) is outside the transaction — two simultaneous requests can both read the same count and both allow when only 1 token existed. **Fix: Redis Lua script** that reads, calculates, and updates in a single atomic step (expanding the atomic boundary to the whole read-modify-write sequence — the classic *dealing with contention* fix).

Why Redis fits: sub-millisecond ops; `EXPIRE` auto-cleans inactive buckets (no memory leaks); replicable for HA; atomic operations.

### 6.4 Rejecting requests (HTTP 429 + headers)

**Drop or queue?** Fail fast (immediate 429) — chosen. Queuing sounds friendly but consumes memory, causes duplicate retries, and makes API latency unpredictable (only niche batch systems benefit).

Helpful response headers:
- `X-RateLimit-Limit` — the ceiling (e.g., 100)
- `X-RateLimit-Remaining` — requests left (e.g., 0)
- `X-RateLimit-Reset` — Unix timestamp of reset
- `Retry-After` — seconds to wait

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
Retry-After: 60

{ "error": "Rate limit exceeded", "message": "You have exceeded the rate limit of 100 requests per minute. Try again in 60 seconds." }
```

These let well-behaved clients implement proper backoff. In the interview, just call out the 429 + headers.

## 7. Deep Dives

### Deep Dive 1: Scaling to 1M requests/second (sharding Redis)

- A single Redis instance handles ~100k-200k ops/sec; each check needs multiple ops (HMGET + HSET), so realistically **50k-100k checks/sec per instance** — a bottleneck at 1M req/s. *(Pattern: Scaling Writes.)*
- **Shard Redis** with **consistent hashing** on the client identifier (user ID / IP / API key) so each client's state always lands on the same shard — split state is useless.
- Gateways add routing logic: extract identifier → hash → route check to the right shard. Algorithm unchanged.
- ~10 shards × ~100k ops/sec ≈ 1M req/s target.
- In production, use **Redis Cluster**: keys auto-distributed across 16,384 hash slots; no custom hashing logic in gateways.

### Deep Dive 2: High availability and fault tolerance

If a shard dies, all clients on it lose rate limiting. Choose a failure mode:

#### 👍 Good: Fail-closed
- Reject all requests (503/429) when Redis is unreachable. Most restrictive.
- **Challenges:** effectively takes your API offline during Redis outages; aggressive retries add load. Legitimate uses: financial/payment systems, high-security environments where uncontrolled access is worse than downtime.

#### 👍 Good: Fail-open
- Skip rate-limit checks; forward everything. Keeps the API available.
- **Challenges:** loses protection temporarily; **cascade failure risk** — if Redis failed because you're already under load, failing open sends ALL traffic downstream, potentially collapsing the platform (especially dangerous during viral events).

Both are legitimately "good" — it depends on the system. **Chosen here: fail-closed** for the social platform, because rate-limiter failures often coincide with the traffic spikes when protection matters most; brief rejections beat total collapse.

Prevention beats damage control: **master-replica replication per shard** with automatic promotion on master failure (Redis Cluster has built-in failover). Trade-off: infrastructure cost + replication lag (usually tiny). Also: monitor Redis health (CPU, memory, connectivity), rate-limiting success rates, latencies, and alert when entering fail-open mode.

### Deep Dive 3: Minimizing latency overhead

- **Connection pooling** (most important): persistent connections to Redis avoid per-request TCP handshakes (20-50ms); most clients pool automatically — tune pool size.
- **Geographic distribution** (biggest win): deploy gateways + Redis clusters per region; Tokyo→Virginia round trips kill latency. Accept eventual consistency between regions for rate limiting.
- Briefly mentionable but usually unnecessary: local caching of limit state (risky — stale decisions), pipelining/Lua batching, request batching. In an interview, avoid unless asked.

### Deep Dive 4: Hot keys (viral / high-volume clients)

A hot key means one user/IP generating tens of thousands of req/s to one shard — often abuse, sometimes legitimate (analytics pipelines, aggressive mobile refresh). *(Pattern: Scaling Reads.)*

**For legitimate high-volume clients:**
- **Client-side rate limiting** in SDKs (respecting server headers) to smooth traffic.
- **Request batching** — many operations per request, fewer checks.
- **Premium tiers** with higher limits, possibly dedicated infrastructure.

**For abusive traffic:**
- **Automatic blocking** — clients that hit limits repeatedly (e.g., 10x in a minute) get temporarily blocklisted (list kept in a Redis shard, checked on cache misses).
- **DDoS protection** (Cloudflare, AWS Shield) upstream of the rate limiter.

Design for shared IPs (corporate NATs, public WiFi) upfront: higher IP-based limits, lean on authenticated per-user limits where possible.

### Deep Dive 5: Dynamic rule configuration

Production systems need limit changes without deploys (launches, premium tiers, emergency reductions).

#### 👍 Good: Poll-based configuration
- Rules in a DB/config service; gateways poll every ~30s and cache locally. Simple; covers most cases.
- **Challenge:** propagation delay — an emergency limit reduction may take up to the polling interval.

#### ✅ Great: Push-based configuration
- Config changes pushed immediately to all gateways — exactly what **ZooKeeper** was designed for (distributed config with real-time notifications); alternatives: Redis pub/sub, custom services with persistent connections. Updates land within seconds.
- **Challenges:** significant complexity — connection failures, partial update failures across gateways, fallback when the push system is down. Only justified when very fast updates matter (security incidents, HFT-like scenarios).

## 8. What Is Expected at Each Level?

### Mid-level (~80% breadth / 20% depth)
- Craft a high-level design meeting the functional requirements; components may be surface-level abstractions — the interviewer will probe (mention Redis → expect "how does it work, why?").
- Drive early stages (requirements, algorithm selection); not expected to proactively spot all flaws.
- Specifically: clearly explain **one** algorithm (Token Bucket is fine), place the limiter sensibly (**API Gateway**), identify **Redis** as shared state, and — when asked about scaling — recognize the need to **shard Redis** with a rough idea of how.

### Senior (~60% breadth / 40% depth)
- Confidently discuss algorithm trade-offs and justify choices.
- Understand consistent hashing, Redis Cluster, connection pooling without guidance; know Redis ops must be atomic and suggest MULTI/EXEC.
- Clearly explain fail-open vs fail-closed trade-offs; pros/cons of limiter placements.
- Proactively raise hot keys, Redis availability, latency optimizations; move quickly past algorithm basics to distributed challenges; have opinions on configuration management.

### Staff+ (~40% breadth / 60% depth)
- Deep production understanding drawn from real experience; exceptional proactivity — edge cases, observability, operational procedures without guidance.
- Naturally discuss multi-region deployment, cross-region consistency, gradual rollouts/canaries.
- Often not asked this question at all; if asked, establish fundamentals fast and spend most time on production operations, failure modes, and system integration.
