# 01 - Bitly (URL Shortener)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/bitly
**Author:** Evan King (Hello Interview) · **Difficulty:** Easy · **Pattern:** Scaling Reads

> **What is Bit.ly?** A URL shortening service that converts long URLs into shorter, manageable links (and provides analytics on them). This is a classic entry-level system design question — a great one to start with.

---

## 1. Functional Requirements

**Core:**
1. Users can submit a long URL and receive a shortened version.
   - Optionally specify a **custom alias** (e.g., `www.short.ly/my-custom-alias`).
   - Optionally specify an **expiration date**.
2. Users can access the original URL by using the shortened URL.

**Below the line (out of scope):**
- User authentication and account management.
- Analytics on link clicks (click counts, geographic data).

*Tip: zero in on the top 3-4 features; don't get distracted by bells and whistles.*

## 2. Non-Functional Requirements

**Core:**
1. **Uniqueness** — each short code maps to exactly one long URL.
2. **Low-latency redirection** — < 100ms.
3. **High availability** — 99.99% uptime (availability > consistency).
4. **Scale** — 1B shortened URLs, 100M DAU.

**Below the line:**
- Real-time analytics consistency.
- Advanced security (spam detection, malicious URL filtering).

**Key observation:** the system is *massively read-heavy* — perhaps ~1000 reads (redirects) per 1 write (new short URL). This asymmetry drives caching strategy, database choice, and overall architecture.

## 3. Core Entities

1. **Original URL** — the long URL the user wants shortened.
2. **Short URL** — the shortened URL the user receives/shares.
3. **User** — who created the shortened URL.

(A simple list is fine at this stage; document the data model in detail during high-level design.)

## 4. API Design

REST API; map endpoints roughly 1:1 to functional requirements. Choose the right HTTP verb (POST = create, GET = read, PUT = update, DELETE = delete).

```http
// Shorten a URL
POST /urls
{
  "long_url": "https://www.example.com/some/very/long/url",
  "custom_alias": "optional_custom_alias",
  "expiration_date": "optional_expiration_date"
}
-> { "short_url": "http://short.ly/abc123" }
```

```http
// Redirect to original URL
GET /{short_code}
-> HTTP 302 Redirect to the original long URL
```

## 5. High-Level Design

### 5.1 Submit a long URL, get a short one

Components:
- **Client** — web/mobile app.
- **Primary Server** — receives requests, handles business logic (short URL creation, validation).
- **Database** — stores short code → long URL mappings, custom aliases, expiration dates.

Flow (`POST /urls`):
1. Server validates the long URL format (e.g., an `is-url` library). Optional: deduplicate identical long URLs and return the existing code — but most shorteners **don't** dedupe, since different users may want separate expirations, independent analytics, or custom aliases (dedup trades storage efficiency for these features).
2. If valid, generate a short code (deep dive below). If a custom alias is supplied, validate it doesn't already exist. To prevent custom aliases colliding with future counter-generated codes, prefix generated codes with a character aliases can't use, or keep separate namespaces.
3. Insert short code (or alias), long URL, and expiration date into the DB.
4. Return the short URL.

### 5.2 Access the original URL via the short URL

The short URL lives at a domain we own (`short.ly/abc123`), so all requests hit our Primary Server.

Flow (`GET /abc123`):
1. Server looks up the short code in the DB.
2. If found and not expired, retrieve the long URL. For expired URLs return **410 Gone**.
3. Server responds with an HTTP redirect; the browser follows it transparently.

Cleanup: a periodic background job can delete expired rows (or just keep them). Importantly, set cache TTLs ≤ URL expiration times so stale entries auto-evict.

**301 vs 302 redirect:**
- **301 Moved Permanently** — browsers cache it, so future requests may bypass our server entirely.
- **302 Found (temporary)** — browsers do NOT cache; every request goes through us.

**302 is preferred** for a URL shortener because:
- More control (can update/expire links).
- No stale browser caching if we change/delete a short URL.
- Enables click tracking (even though analytics are out of scope here).

## 6. Deep Dives

### Deep Dive 1: How do we ensure short URLs are unique?

Constraints: (1) unique codes, (2) as short as possible, (3) efficient generation.

#### ❌ Bad: Long URL prefix
Take the first N chars of the input URL as the code. Fails uniqueness — any two URLs sharing a prefix collide (e.g., all `www.linkedin.com/in/...` profiles map to the same code).

#### ✅ Great: Hash function + base62
- Random number generators alone don't provide enough entropy.
- Use a hash (e.g., SHA-256) of the (canonicalized) long URL → base62-encode → take first N chars (N=8 gives 62^8 ≈ 218 trillion codes).
- **Why base62?** Compact (a-z, A-Z, 0-9); excludes base64's `+` and `/` because `/` is a URL path separator and `+` can be interpreted as a space in query strings.
- Pure hashes are deterministic: same long URL → same code (good for dedup; bad if you need multiple codes per URL or want to prevent guessability — add a secret salt/nonce, i.e., HMAC).

```python
input_url = "https://www.example.com/some/very/long/url"
canonical_url = canonicalize(input_url)  # lowercase host, strip default ports, etc.
hash_code = hash_function(canonical_url)
short_code = base62_encode(hash_code)[:8]
```

**Challenges:** collision probability grows with stored URLs (with n codes used out of space |S|, next-code collision probability is n/|S|). Handle it with a **UNIQUE constraint** on the short-code column and bounded retries (e.g., 3-5 attempts, adding a random salt each retry). Tradeoff triangle: uniqueness vs shortness vs generation efficiency.

#### ✅ Great: Unique counter + base62 encoding (chosen approach)
- Increment a global counter per new URL; base62-encode the value.
- **Redis is ideal** for the counter: single-threaded with atomic `INCR`, so two simultaneous calls always get distinct values (1000, then 1001) — no race conditions, no collision checks needed.
- Fast, guaranteed unique, and codes are decodable back to the ID for DB lookups.

**Challenges:**
- Distributed counter synchronization (all write instances must agree) — addressed in scaling deep dive.
- **Predictability/enumeration**: sequential codes let attackers iterate through all URLs. Mitigate with a reversible transformation (e.g., XOR with a secret key) before encoding, or accept it since short URLs are usually shared publicly.
- Code length grows over time — but 1B in base62 is only 6 chars (`15ftgG`); 62^6 ≈ 56B before needing 7 chars (62^7 ≈ 3.5 trillion). Fine.

### Deep Dive 2: How do we make redirects fast?

Without optimization, lookups are full table scans — terrible at millions/billions of rows. *(Pattern: Scaling Reads — extreme read:write ratios make aggressive caching essential.)*

#### 👍 Good: Add an index
- **B-tree index** on the short-code column → O(log n) lookups.
- Make the short code the **primary key**: gives indexing + enforced uniqueness in one.
- **Challenge:** disk-based DB alone may not keep up. Math: 100M DAU × 5 redirects/day = 500M redirects/day ≈ 5,787/s average; with a ~100x peak factor, design for **~600k reads/sec** — beyond a single DB instance.

#### ✅ Great: In-memory cache (Redis/Memcached)
- Cache short-code → long-URL mappings between server and DB. Cache hit = memory read; miss = DB read then populate cache.
- Speed comparison: memory ~100ns vs SSD ~0.1ms vs HDD ~10ms; memory supports millions of reads/sec vs ~100k IOPS (SSD).
- **Challenges:** cache invalidation (mitigated since URLs rarely change), cold-cache warm-up, memory limits → eviction policy (e.g., LRU), added architectural complexity. Discuss tradeoffs/invalidation with your interviewer.

#### ✅ Great: CDN + edge computing
- Serve the short domain via a CDN with global PoPs; cache mappings at the edge; optionally run redirect logic at the edge (Cloudflare Workers, Lambda@Edge) so popular codes never touch the origin.
- **Challenges:** CDN cache invalidation/consistency, edge function limits (execution time, memory, libraries), higher cost, harder debugging/monitoring. You're trading cost + complexity for latency — worth it depends on price sensitivity, UX requirements, traffic patterns.

### Deep Dive 3: How do we scale to 1B URLs and 100M DAU?

**Storage math:** ~200 bytes/row (short code ~8B, long URL ~100B, created ~8B, alias ~100B, expiry ~8B); round up to 500B with metadata → 1B rows ≈ **500GB** — fits comfortably on modern SSDs; a single Postgres instance suffices (shard only if you hit hardware limits).

**Database choice:** almost anything works — reads are offloaded to cache and writes are tiny (~100k new URLs/day ≈ 1 row/sec). Postgres, MySQL, DynamoDB all fine; pick what you know (default: Postgres).

**High availability if the DB dies:**
1. **Replication** — multiple identical copies; failover to a replica. Adds operational complexity.
2. **Backups** — periodic snapshots stored separately.

**Scaling the server tier:** split into a **Read Service** (redirects) and **Write Service** (creation) — microservices scaled independently to match the asymmetric workload; horizontally scale both.

**Scaling the counter:** horizontally scaled write services need a single source of truth. Use a **centralized Redis counter** (atomic `INCR`). To cut per-write network overhead, use **counter batching**:
1. Each write instance requests a batch (e.g., 1000 values) via `INCRBY 1000`.
2. Redis atomically advances the counter and returns the batch start.
3. The instance consumes values locally; fetches a new batch when exhausted.

- HA for the counter: Redis Sentinel / Redis Cluster with automatic failover. A single Redis handles 100k+ ops/sec — plenty, especially with batching.
- **Multi-region:** allocate disjoint counter ranges per region (A: 0–1B, B: 1B–2B) to avoid cross-region coordination. Writes go to the local region's Redis; reads served globally via distributed caches.
- If Redis fails before replicating the latest counter value, a few values may be lost — acceptable since we need uniqueness, not continuity. The DB's UNIQUE constraint is the ultimate safety net.

## 7. What Is Expected at Each Level?

### Mid-level
- Working high-level design covering shortening + redirection.
- Understand the basic flow: submit long URL → generate short code → store mapping → redirect.
- Recognize short-code generation must guarantee uniqueness; propose at least one reasonable approach (hashing OR counter-based).
- Understand why a 302 redirect is used (knowing the exact status code isn't required).
- Discuss basic DB indexing.
- With some prompting, recognize a cache helps read performance given the read-heavy workload.

### Senior
- Drive the conversation; proactively identify unique code generation at scale, fast redirects, horizontal scaling.
- Articulate hashing (collision handling) vs counter (coordination overhead) tradeoffs without much prompting.
- Detailed caching strategy including invalidation for expired URLs.
- Justify a database choice.
- Recognize read/write service separation for the asymmetric workload; scale the counter across write instances with Redis or similar.

### Staff+
- See past the textbook solution to production concerns; structure the design around read-heaviness from the start.
- Proactively cover multi-region deployment, counter range allocation, Redis failover behavior.
- Security implications of predictable codes + mitigations.
- Product thinking: custom-alias collision prevention, expiration cleanup strategy, evolution of the system; operating and maintaining at scale.
