# 12 - Tinder (Design a Dating App)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/tinder
**Difficulty:** Medium · Product design style question

Tinder is a mobile dating app where users swipe right (like) or left (pass) on profiles. It uses location data and user-specified filters to suggest potential matches nearby. This question is mostly focused on the recommendation "feed" and swiping experience — not auxiliary features. If unsure what to focus on, clarify with the interviewer; it's typically the functionality that makes the app unique or most complex.

---

## Functional Requirements

**Core:**
1. Users can create a profile with preferences (e.g. age range, interests) and specify a maximum distance.
2. Users can view a stack of potential matches matching their preferences and within max distance of their current location.
3. Users can swipe right/left on profiles one-by-one to express "yes" or "no".
4. Users get a match notification if they mutually swipe on each other.

**Below the line (out of scope):**
- Uploading pictures
- Chat / DM after matching
- "Super swipes" and premium features

## Non-Functional Requirements

**Core:**
1. **Strong consistency for swiping** — if a user swipes "yes" on someone who already swiped "yes" on them, they should get a match notification.
2. **Scale** — 20M daily active users, ~100 swipes/user/day on average.
3. **Low latency** for loading the potential-matches stack (< 300ms).
4. **Avoid re-showing profiles** the user has previously swiped on.

**Below the line:** fake-profile protection, monitoring/alerting.

---

## Core Entities

1. **User** — both the app user and the profile shown to others (included explicitly here since users swipe on users).
2. **Swipe** — expression of "yes"/"no"; belongs to a `swiping_user`, about a `target_user`.
3. **Match** — connection between 2 users who both swiped "yes" on each other.

## API Design

All endpoints require authentication; user identity comes from headers (session token / JWT) — never pass user info in the request body (client-manipulable).

**Create/update profile preferences:**
```
POST /profile
{
  "age_min": 20,
  "age_max": 30,
  "distance": 10,
  "interestedIn": "female" | "male" | "both",
  ...
}
```

**Get the feed/stack of profiles:**
```
GET /feed?lat={}&long={}&distance={} -> User[]
```
- Other filters (age, interests) are already stored server-side from settings.
- Location is passed client-side since it always changes.
- Pagination is superfluous here — these are recommendations; the app just hits the endpoint again when the list is exhausted.

**Swipe:**
```
POST /swipe/{userId}
{ "decision": "yes" | "no" }
```

---

## High-Level Design

Build up sequentially through the functional requirements, then use non-functional requirements to drive deep dives.

### 1) Create a profile with preferences
Simple client → API Gateway → **Profile Service** → **Database** architecture. Profile Service persists preferences to the user database.

### 2) View a stack of potential matches
Start simple: Profile Service queries the User DB for users matching preferences and location:
```sql
SELECT * FROM users
WHERE age BETWEEN 18 AND 35
AND interestedIn = 'female'
AND lat BETWEEN userLat - maxDistance AND userLat + maxDistance
AND long BETWEEN userLong - maxDistance AND userLong + maxDistance
```
This is incredibly inefficient — location search even with basic indexing is slow. Improved in the deep dives (geospatial indexing).

### 3) Swipe right/left
Introduce two new components:
- **Swipe Service** — persists swipes and checks for matches.
- **Swipe Database** — stores swipe data.

**Why a separate service + DB?** Swipe writes happen far more often than profile operations, so separating lets the swipe path scale independently. Volume: 20M DAU × 100 swipes/day × ~100 bytes ≈ **200GB/day** — data must be partitioned.

**Cassandra** is a good fit: partition by `swiping_user_id` so "did A swipe on B?" hits a single partition; its write-optimized storage engine (CommitLog + Memtables + SSTables) handles massive write volume. Con: eventual consistency (addressed in deep dive 1).

Flow: client POSTs swipe → Swipe Service writes to Swipe DB → checks for inverse swipe → returns match if found.

### 4) Match notifications
- **Person B** (second swiper) is easy — right after their swipe, we detect the inverse swipe and show "You Matched!" immediately.
- **Person A** (who may have swiped weeks ago) gets a **push notification** via APNS (Apple) or FCM (Firebase).

Assume an external push service; match storage details are out of scope — clarify these assumptions with the interviewer.

---

## Deep Dive 1: Consistent, low-latency swiping

**Failure scenario:** A and B swipe right on each other at ~the same time; both inverse-swipe checks find nothing before either write lands → both swipes saved but no match notification ever fires.

Note: you *could* prioritize availability instead — a periodic reconciliation job finds matching swipes that missed match creation and notifies both users (they'd assume the other just swiped). An interesting trade-off to raise, but interviewers will likely want you to stick with consistency since it's the harder problem.

### Bad: Database polling for matches
Periodically poll the DB for reciprocal swipes. Non-starter: no immediate notification (kills the dopamine hit / engagement), adds DB load, scalability issues.

### Good: Transactions
Do the swipe write and reciprocal check in one transaction. Cassandra only has **lightweight transactions (LWT)** — Paxos-based, linearizable **within a single partition only**; no multi-partition atomicity, no isolation levels, no rollbacks, plus significant performance overhead. Challenge: at 2B swipes/day, data spans many partitions, so LWTs alone don't work — unless we force reciprocal swipes into the same partition.

### Great: Sharded Cassandra with single-partition transactions
Ensure all swipes between two users land in the **same partition** via a compound key:
```sql
CREATE TABLE swipes (
    user_pair text,      -- partition key: smaller_id:larger_id
    from_user uuid,      -- clustering key
    to_user uuid,        -- clustering key
    direction text,
    created_at timestamp,
    PRIMARY KEY ((user_pair), from_user, to_user)
);
```
Sort the two user IDs to build `user_pair`, so A→B and B→A map to the same partition; then a single-partition batch atomically inserts the swipe and reads the inverse. No cross-partition operations needed.

**Challenges:** partitions grow unbounded over time; highly active users create hot partitions. Needs a cleanup/archival strategy for old swipe data.

### Great: Redis for atomic operations (hybrid with Cassandra)
Use **Redis** for real-time atomic match detection while keeping **Cassandra as the durable storage layer**. Same key insight: combine sorted user IDs into one key (`swipes:{smaller}:{larger}`) stored as a Redis hash with each user's swipe as a field. A **Lua script** atomically sets our swipe and reads the other user's swipe — if both are "right", create a match. Consistent hashing keeps related swipes on the same shard; scales horizontally.

**Challenges:** managing the Redis cluster (node failures, ring rebalancing); memory — but since Cassandra is durable, we can aggressively expire Redis data and keep only recent swipes. Losing Redis only loses match detection for very recent swipes (users can swipe again). Hybrid gives Redis's strong consistency + Cassandra's durability.

---

## Deep Dive 2: Low-latency feed/stack generation

The naive SQL query per feed request won't meet the < 300ms requirement.

### Good: Indexed database for real-time querying
Use a search-optimized DB (**Elasticsearch/OpenSearch**) with indexes on preference fields and a **geospatial index** on location for fast radius queries.
**Challenge:** keeping the search index in sync with the primary transactional DB — solved with **change data capture (CDC)**, possibly batched since Elasticsearch is read-optimized, not write-optimized. Sync lag can mean stale/missing profiles.

### Good: Pre-computation and caching
Background jobs pre-compute feeds per user (based on preferences + location) and cache them for instant retrieval; can run off-peak.
**Challenges:** active users exhaust cached feeds (then we're back to the slow query); cached feeds may miss recent profile changes and new users → less relevant matches.

### Great: Combination of pre-computation + indexed database
- Serve the **cached pre-computed feed instantly** when the app opens.
- As the user nears the end of the stack (a few profiles left), **trigger a background refresh** using the Elasticsearch-backed real-time query — stack feels infinite.

**Avoiding stale feeds** (profiles that no longer match criteria — user moved, changed interests):
- Strict **TTL on cached feeds (< 1h)** with scheduled background recomputation.
- Pre-compute **only for truly active users** ("warm" caches only where they'll be used) — cheaper at scale.
- User actions that should trigger a background feed refresh: changing filter criteria, or significantly changing location.
- Key insight: TTL, cache size, and the active-user set are all **tunable parameters** — systems with tunable knobs let operators keep the system healthy without reworking its logic.

---

## Deep Dive 3: Avoid re-showing swiped-on profiles

Re-showing profiles suggests swipes weren't recorded, or annoys users with rejected profiles.

### Bad: DB query + contains check
Feed builder queries the swipe DB (efficient — routed by `swiping_user_id` partition) and filters out swiped profiles.
**Challenges:** (1) with eventual consistency, recent swipes may not have replicated yet → risk of re-showing; (2) users with extensive swipe histories make the contains check progressively more expensive.

### Great: Client-side cache + DB query + contains check
Add a cache of recent swipes — but manage it **client-side**, not on the backend (a backend cache just to bridge replication lag would be expensive). The client stores the K most recent swipes and filters incoming feed suggestions. Valid because a user typically uses one device — the client is legitimately part of the system.

Bonus: when the user nears the end of a 200-profile stack (~profile 150), the client pings the backend to generate a new feed, fetches it, and filters out anything swiped in the meantime.

**Challenge:** still slow for users with huge swipe histories (large contains checks).

### Great: Cache + contains check + Bloom filter
For users whose swipe history exceeds a threshold, build and cache a **Bloom filter** of swiped profiles and use it during feed filtering. (Admittedly leans "over-engineered", but a legit Bloom filter use case.)
- False positives possible → a few profiles never shown (acceptable).
- **Never false negatives** → never re-show a swiped profile (the requirement).
- Error rate vs. size is tunable.

**Challenge:** managing the Bloom filter cache — updates, and recovery after a node outage (rebuildable from swipe data, but expensive at scale).

---

## What is Expected at Each Level?

### Mid-level (E4)
- ~80% breadth / 20% depth; many components will be surface-level abstractions.
- Interviewer probes basics (e.g. "what does the API Gateway do?"); expects you to drive early stages, may drive later stages themselves.
- **Bar for Tinder:** clearly defined API endpoints and data model; a functional high-level design covering feed creation, swiping, and matching; a design supporting traditional filters + geospatial filters; and a solution to avoid re-showing swiped-on profiles. In-depth knowledge of specific technologies not required.

### Senior (E5)
- ~60% breadth / 40% depth; go deep where you have hands-on experience; articulate pros/cons of architectural choices; proactively anticipate bottlenecks.
- **Bar for Tinder:** move quickly through the high-level design to spend time on efficient/scalable feed generation and reliable match creation; proactively call out feed-building trade-offs; know the type of index that powers the feed; be aware of when feed caches become stale.

### Staff+ (E6+)
- ~40% breadth / 60% depth; breeze through basics; high proactivity — interviewer intervenes only to focus, not steer; practical technology experience guides the conversation.
- **Bar for Tinder:** deep, high-quality solutions to the complex scenarios; may steer toward a particularly interesting topic; solid grasp of trade-offs between solutions, articulated clearly, treating the interviewer as a peer.
