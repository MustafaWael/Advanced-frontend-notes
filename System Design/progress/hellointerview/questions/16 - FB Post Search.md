# 16 - FB Post Search

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-post-search

**Difficulty:** Medium · **Author:** Stefan Mai · **Patterns:** Scaling Reads, Scaling Writes

> Access note: This breakdown was fully readable for free (no premium lock). Only the practice tool, video walkthrough, and quiz are premium.

---

## Understanding the Problem

Facebook is a social network centered around "posts". Users consume posts via a timeline of posts from users they follow (or algorithmic recommendations). Posts can be replied to, liked, or shared.

This problem zooms in on the **search experience**. It is primed for infrastructure-style interviews testing how deeply you understand **data layout, indexing, and scaling**.

**Key constraint:** The interviewer explicitly forbids using a search engine like **Elasticsearch** or a pre-built full-text index (like Postgres Full-Text). Disallowing specific technologies is common — the intent is to test fundamentals of data organization and indexing rather than knowledge of a particular tool. Be prepared for this.

## Functional Requirements

**Core:**
1. Users should be able to create and like posts.
2. Users should be able to search posts by keyword.
3. Users should be able to get search results sorted by recency or like count.

**Below the line (out of scope):**
- Fuzzy matching on terms (e.g. "bird" matching "ostrich")
- Personalization in search results
- Privacy rules and filters
- Sophisticated relevance/ranking algorithms
- Images and media
- Realtime updates to the search page as new posts come in

**Insight:** De-scoping personalization dramatically simplifies the problem and makes caching much more effective — worth explicitly asking whether it's a firm requirement. Interviewers are usually fine with assertions like "I'm leaving privacy out of scope" and will correct you if needed.

## Non-Functional Requirements

In infrastructure-focused questions, NFRs take center stage — the interviewer wants to see how you identify and solve bottlenecks.

**Core:**
1. Fast: median queries return in **< 500ms**.
2. Support a high volume of requests.
3. New posts searchable in **< 1 minute**.
4. **All** posts must be discoverable, including old/unpopular posts (these can take more time).
5. Highly available.

**Insight (hot vs cold data):** With lots of data you'll have "hot" data (frequently accessed, served fast from memory) and "cold" data (infrequently accessed, served from disk/remote storage/tape). Requirement 4's "can take more time" foreshadows a hot/cold storage split later in the design.

## Scale Estimations

Don't estimate for the sake of estimation — use it to determine the nature of the design.

Assumptions: 1B users, 1 post/user/day average, 10 likes/user/day, ~100k seconds/day.

**Writes:**
- Posts created: 1B / 100k s = **10k posts/second**
- Likes created: 1B × 10 / 100k s = **100k likes/second**

**Reads:**
- Searches: 1B × 1/day / 100k s = **10k searches/second** (may burst 10x+)

Key observations:
- Likes vastly outnumber post creations.
- The system is **write-heavy**, not read-heavy — a common mistake is to fixate on the search side and assume reads dominate.

**Storage** (10 years of posts, ~1kb metadata each):
- 1B posts/day × 365 × 10 = **~3.6T posts**
- 3.6T × 1kb = **~3.6 PB** — we'll need to constrain this.

## Core Entities

1. **User** — creates posts.
2. **Post** — the thing being searched; has content, creator, and implicitly a like count.
3. **Like** — created when a user likes a post; we mostly care about the *count*.

## API / System Interface

Two paths:
- **Write path:** endpoints for creating posts and creating likes.
- **Read path:** a search endpoint (query, sort parameter).

Note: in a real system these write events would likely be consumed from a Kafka stream/event bus rather than direct API endpoints — call this out to the interviewer.

## High-Level Design

### 1) Users should be able to create and like posts

The search system is part of a larger product, so assume an internal "Post Service" and "Like Service" already exist and send events to our **Ingestion Service**, which writes to our index storage.

Given the different scales of likes vs posts, a single ingestion service is over-simplified — acknowledge this and promise to revisit. **Tip:** the longer you leave unacknowledged flaws in your design, the more the interviewer assumes you didn't see them.

### 2) Users should be able to search posts by keyword

Read leg: API Gateway (auth, rate limiting) → horizontally scaled Search Service → queries the Index.

**Options for the index:**

- **Bad — Scale an un-indexed database:** `SELECT * FROM posts WHERE content LIKE '%keyword%'`. Correct but terribly slow — scans every post at query time over petabytes. Sharding/replication only helps marginally (N/M posts per node) — a dead end.

- **Great — Create an Inverted Index:** a dictionary mapping keywords → list of post IDs containing them. Use **Redis** to keep the inverted index in memory for blazing-fast queries (durability concerns are surmountable, e.g. MemoryDB, or address in a deep dive). On post creation, the Ingestion Service **tokenizes** the post into keywords and appends the post ID to each keyword's list.
  - Challenges: post ID lists get very large for common keywords; each post triggers writes to many keys (10–1,000 keywords per post).

### 3) Results sorted by recency or like count

- **Bad — Request-time sorting:** fetch all post IDs for the keyword, look up timestamp/like count for each, sort in memory. For common keywords ("Taylor" = 10s of millions of results), payloads could be 100s of MB, plus millions of lookups and a huge request-time sort. Not viable.

- **Great — Multiple indexes:** maintain two indexes per keyword:
  - **Creation index:** a standard Redis **list** (always append; queries take the last elements).
  - **Likes index:** a Redis **sorted set**, ordered by like-count score (priority-queue-like insert/query complexity).
  - New post → add to both indexes for every keyword. Like event → update score in the sorted set.
  - Tradeoffs: doubles index storage (valid tradeoff for massive query performance win); like events are frequent and each requires updating many scores — stress to address later.

## Deep Dives

### 1) Handling the large volume of read requests

Two convenient requirements: no personalization (identical queries → identical results) and up to 1 minute staleness allowed. **Caching** is the obvious tool. (Pattern: Scaling Reads.)

- **Good — Distributed cache alongside the search service:** cache recent results per search query; check cache first, populate on miss. Use a **TTL < 1 minute** to honor the new-post SLA.
- **Great — CDN edge caching on top:** add `cache-control` headers to `/search` responses; CDN (Cloudflare/CloudFront) caches geographically close to users. Cache hits return in **10s of ms** vs 100s of ms through gateway → service → cache; misses proxy through as usual.

### 2) Multi-keyword / phrase queries ("Taylor Swift")

- **Good — Intersection and filter:** fetch postId sets for "Taylor" and "Swift", intersect, fetch contents, filter to those actually containing the phrase (not "My friend Taylor made a swift exit"), return in order.
  - Challenges: huge sets are expensive to transfer and intersect (megabytes into hash tables) — hard within 500ms; heavy filtering when words co-occur but not adjacently.
- **Great — Bigrams / shingles:** index each adjacent word pair ("saw Taylor", "Taylor Swift", ...) into the Likes and Creation indexes; phrase queries hit the "Taylor Swift" key directly.
  - Challenges: dramatically larger index — bigrams are far more unique/sparse (10M single keywords → 100M+ keys). Remediation: only index bigrams *likely to be searched* (use count-min sketch or other probabilistic structures to estimate bigram frequency), falling back to intersection otherwise — at the cost of complexity.

### 3) Handling the large volume of writes

**Post creation:** a 100-word post can trigger 100+ index writes; bursts could overwhelm ingestion or lose events. Fixes:
- Put a **Kafka log/stream** in front to buffer bursts and fan out/partition creation requests across multiple ingestion instances.
- **Shard the indexes by keyword** across many Redis instances so writes spread out. (Pattern: Scaling Writes.)

**Like events** (the elephant in the room — likes are 10x post creations):
- **Good — Batch likes before writing:** a "batcher" service aggregates like events per postId over a fixed window (~30s), then writes one increment (e.g. +500) back to Kafka for ingestion. Challenge: only helps viral posts; most posts get sparse likes (1/minute uniform gets no batching benefit) and the batcher adds overhead.
- **Great — Two-stage architecture:** only write like counts to the index when they cross milestones (powers of 2 or 10: 1, 2, 4, 8, ...). Writes drop exponentially — 1000 likes → ~10 index writes.
  - Tradeoff: index is **inherently stale**, but *ordering is approximately correct* (a 10k-like post still beats a 1-like post).
  - At query time: fetch top **N×2** posts from the Like index, query the Like Service for fresh counts, re-sort, return top N. Approximate storage, precise final results. This "approximately correct first stage + more expensive re-ranking stage" is a very common pattern in information retrieval/recommendation systems.
  - Challenges: more engineering complexity; the semantics of the stored count change — name it "approxLikes"/"logLikes" to make this clear.

### 4) Optimizing storage

- **Cap the inverted indexes:** you rarely need all 10M posts containing "Mark"; keeping 1k–10k items per keyword cuts storage by orders of magnitude.
- **Hot/cold tiering:** most keywords are rarely or never searched. Run a batch job using search analytics to move rarely-accessed keyword indexes from Redis to cheap **blob storage (S3/R2)**. Query path: try Redis first; on miss, read the index from blob storage with a small latency penalty (allowed by our NFRs for old/unpopular content).

Note: most candidates — especially mid-level — won't get through all these deep dives, and that's expected.

## What is Expected at Each Level?

### Mid-Level
- ~80% breadth / 20% depth. A high-level design meeting the functional requirements is the focus; optimality is icing.
- Interviewer probes basics (e.g. cache eviction policy) — nothing taken for granted.
- Mix of driving and taking a backseat: drive the early stages; interviewer may drive later stages.
- **Bar for this problem:** clearly defined API endpoints and data model, and both sides of the system built (ingestion and query). Using a "Bad" solution is OK if the discussion is good — no expectation of jumping straight to great solutions.

### Senior
- ~60% breadth / 40% depth; go deep where you have hands-on experience.
- Problem's red flags (write volume, storage size, duplicate inputs) should jump out; reasonable solutions expected.
- Clearly articulate pros/cons of architectural choices and justify tradeoffs; proactively anticipate challenges and bottlenecks.
- **Bar for this problem:** speed through high-level design; at minimum, ingestion + query detailed with a proper reverse index and an appropriate caching strategy.

### Staff+
- ~40% breadth / 60% depth; "been there, done that" expertise; breeze through basics.
- Exceptional proactivity — identify and solve issues independently, preemptively.
- **Bar for this problem:** get through several deep dives with innovative, optimal solutions. A strong signal is the interviewer learning something new from the discussion.

## Key Takeaways

- Do the math first: this system is **write-heavy** (100k likes/s vs 10k searches/s) — that shapes everything.
- No Elasticsearch allowed → build an **inverted index** yourself (Redis lists + sorted sets), with **separate indexes per sort order**.
- Reads: cache aggressively (distributed cache with TTL < 1 min, plus CDN) because results are non-personalized and staleness is tolerated.
- Writes: Kafka buffering + keyword sharding for posts; **milestone-based (log) like updates + two-stage re-ranking** for likes.
- Storage: cap index sizes and tier cold keywords to blob storage.
