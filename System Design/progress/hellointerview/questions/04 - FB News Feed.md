# 04 - Design Facebook's News Feed

**Source:** [hellointerview.com/learn/system-design/problem-breakdowns/fb-news-feed](https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-news-feed)
**Difficulty:** Medium · **Pattern:** Scaling Reads · **Author:** Stefan Mai

## Understanding the Problem

Facebook's News Feed shows recent stories from users in your social graph. This is a classic system design problem about **fan-out** and data management. Assume uni-directional "follow" relationships (not bi-directional "friend" relationships).

## Functional Requirements

**Core:**
1. Users should be able to create posts.
2. Users should be able to friend/follow people.
3. Users should be able to view a feed of posts from people they follow, **in reverse chronological order** (newest first).
4. Users should be able to page through their feed.

**Below the line (out of scope):**
- Liking and commenting on posts.
- Private posts / restricted visibility.

Assume users are already authenticated (user ID in session or JWT).

## Non-Functional Requirements

1. **Highly available** (availability over consistency). Tolerate up to **1 minute of post staleness** (eventual consistency).
2. Posting and viewing the feed should be **fast: < 500ms**.
3. Handle a massive number of users (**2B**).
4. Users can follow an **unlimited** number of users and be followed by an **unlimited** number of users.

> Tip: Put quantities on non-functional requirements — a single-digit-millisecond system needs a dramatically different architecture than one that can take a second.

## Planning the Approach

The hard part is dealing with users following a massive number of people, or people with lots of followers ("fan out"). Move quickly through the base requirements so you can dive deep there. Following the functional requirements in order provides a natural structure.

## Core Entities

1. **User** — a user in the system.
2. **Follow** — a uni-directional link between users.
3. **Post** — made by a user; shown in feeds of followers.

A short list like this is fine in the interview — just align with the interviewer.

## API Design

**Create a post:**
```
POST /posts
{ "content": { } }
// -> 200 OK
{ "postId": ... }
```
Content left open for rich/structured data. Auth tokens live in request headers.

**Follow a user** (idempotent PUT — doesn't fail if clicked twice; unfollow would be DELETE):
```
PUT /users/[id]/follow
{ }
// -> 200 OK
```

**View/page the feed:**
```
GET /feed?pageSize={size}&cursor={timestamp?}
{
    items: Post[],
    nextCursor: string
}
```
Since the feed is reverse chronological, a **timestamp cursor** (oldest post seen so far) drives pagination — each page returns N posts older than the cursor.

> Tip (esp. senior candidates): don't over-invest in obvious parts. "I'll come back if I have time for this" is a great strategy — distinguishing complex pieces from trivial ones is a critical senior skill.

## High-Level Design

### 1. Users should be able to create posts

- Horizontally scaled **Post Service** behind an **API gateway / load balancer**. Each host is stateless (only writes to the DB), so scaling = add hosts.
- Database: any key-value store works; use **DynamoDB** for simplicity and scalability (very high throughput if load is spread evenly across partitions).

### 2. Users should be able to friend/follow people

Following is a many-to-many relationship — a graph. You *could* use a graph DB (Neo4j) or triple store, but the requirements here are simple: **model the graph yourself in a key-value store** and avoid scarier questions like "how do you scale Neo4j?" Graph DBs shine for traversals (friends-of-friends, embeddings) which we don't need.

**Follow table** (DynamoDB):
- Partition key: `userFollowing`, sort key: `userFollowed`.
- **GSI** with the reverse relationship (partition key `userFollowed`, sort key `userFollowing`) to look up all followers of a user.

Query patterns supported:
- Is A following B? → lookup with both keys.
- All users A follows → range query on partition key.
- All followers of B → range query on the GSI.

(AWS recommends single-table design for DynamoDB in practice; separate tables are clearer and fine for an interview.)

### 3. Users should be able to view a feed of posts from people they follow

Naive (fan-out-on-read) approach via a new **Feed Service** (separate because it's read-heavy with very different query patterns):
1. Get all users the given user follows (Follow table).
2. Get all posts from those users — requires a **GSI on the Post table**: partition key `creatorId`, sort key `createdAt`.
3. Sort all posts by time and return.

**Pattern — Scaling Reads:** feeds are quintessentially read-intensive (users check constantly, post rarely). Pre-compute feeds for active users, cache recent posts, paginate smartly. Users mostly read only the first few items, so aggressive caching of recent content pays off massively.

Flag the problems verbally (interviewers expect you to spot them fast):
1. A user may follow lots of users.
2. Each of those users may have lots of posts.
3. The total post set may be huge because of (1) or (2).

> Interview strategy: "I know this won't scale, but I'll start with a naive solution and solve scaling separately." Cover breadth first, then depth — a common failure mode is getting lost in one scaling problem before having a complete design.

### 4. Users should be able to page through their feed

Infinite scroll: the cursor is simply the **timestamp of the oldest post seen**. Using the `createdAt`-sorted GSI, return only posts older than the cursor. Same three steps as above, filtered by the cursor timestamp.

## Deep Dives

### 1) Users following a large number of users (fan-out on read)

Problem: building the feed at read time generates huge fan-out — long Follow-table queries, then many Post-table queries. 10s–100s of downstream requests per request is common; 1000s is rare and bad for latency.

**Solution: shift work to write time (fan-out on write).** Precompute feeds when posts are created.

- Note: it's also fair to ask "can we adjust the product?" — Facebook caps friends at 5,000. Capping follows, or degrading the experience for extreme users, is a very common production approach.
- Keep a **PrecomputedFeed table**: key = `userId`, value = a compact list of post IDs in reverse chronological order, capped at ~**200 posts**. Accessed only by user ID, no secondary indexes needed.
- On new post → append to the relevant precomputed feeds.
- Deep pagination beyond 200? Most systems simply don't support it (try paging deep into Google) — real users don't do this. If needed, fall back to the naive Follow+Post query.

**Storage gut-check:** 10 bytes/postID × 200 posts = 2KB/user; × 2B users = **4TB** — very reasonable. (Rule of thumb: cost per user in dollars — 2KB is a fraction of a cent/month vs ~$100/year revenue per US user.)

This fixes reads but creates the mirror problem: writing to millions of feeds when a popular user posts.

### 2) Users with a large number of followers (fan-out on write)

We have a < 1 minute staleness window to perform these writes.

**Bad: Blast the requests** — fire millions of feed writes from the Post Service at post creation. Unworkable: connection limits, latency, and wildly uneven load across Post Service hosts.

**Good: Async workers behind a queue** — since staleness is tolerated, enqueue write requests (e.g. **SQS**; needs at-least-once delivery and high scalability). On new post, enqueue `{postId, creatorId}`; workers look up followers and prepend the post to each follower's feed entry.
- *Challenges:* worker throughput must be enormous for mega accounts; queue items have highly variable work (1M followers vs 1k) and may need splitting.

**Great: Async workers with hybrid feeds** ✅
- Same async workers, plus: **choose per-account whether to precompute**. For high-follower accounts (e.g. Justin Bieber, 90M+ followers), set a flag on the Follow row marking that follow as *not precomputed*; workers skip them.
- On read, the Feed Service merges the (partially) precomputed feed with **recent posts fetched live from the non-precomputed accounts**.
- This is a hybrid of fan-out-on-read and fan-out-on-write, chosen per account — a great general design principle: no one-size-fits-all; combine solutions for different problem shapes.
- *Challenge:* merging at read time costs more Feed Service compute; tune the follower-count threshold.

### 3) Handling uneven reads of Posts (hot keys)

Most posts are read for a few days then never again; viral posts get massive reads in the first hours. DynamoDB scales only with **even load across the keyspace** — one post getting 500 rps while others get 0 is a hot-key problem.

Posts are created far more than edited, which helps caching.

**Good: Distributed post cache with large keyspace** — put a distributed cache (Redis, keyed by postID) between readers and the Post table. Long TTL + LRU eviction; invalidate on (rare) edits. N hosts × M memory of capacity.
- *Challenge:* the cache inherits the **same hot-key problem** — the shard holding a viral post gets hammered while others idle.

**Great: Redundant post cache** ✅
- Same caching idea, but instead of a **sharded** cache (each post on exactly one node), use **replicated** cache instances where *every instance can serve any post*, with a load balancer spreading requests. Instances don't coordinate.
- A viral post's traffic is spread across all N instances → **N× throughput for a hot key** with no coordination.
- Cost: more initial cache misses (up to N DB hits per post instead of 1) — but N ≪ millions of uncached requests. Also fewer distinct posts fit in cache overall; acceptable since DynamoDB can absorb some read variability.

## What is Expected at Each Level?

### Mid-level (E4)
- ~80% breadth / 20% depth; many components will be surface-level abstractions.
- Interviewer probes basics (e.g. "what does the API Gateway do?") — nothing is taken for granted.
- You drive early stages; interviewer may take over and drive later deep dives.
- **Bar for News Feed:** clearly defined API endpoints and data model; a functional high-level design meeting the requirements. May reach some "Good" solutions but not expected to cover all scaling edge cases in the deep dives.

### Senior (E5)
- ~60% breadth / 40% depth; technical detail in areas of hands-on experience.
- Know fan-out handling approaches; iteratively diagnose bottlenecks; articulate pros/cons of architectural choices (scalability, performance, maintainability).
- **Bar:** speed through the high-level design; discuss **at least 2 deep dives** in detail; proactively surface fan-out and performance issues.

### Staff+
- ~40% breadth / 60% depth; experience-backed, proactive, interviewer intervenes only to focus.
- **Bar:** cover all the deep dives (and/or others not enumerated), surface potential issues, discuss performance tuning.

## Key Takeaways for Mid-Level Prep

- Nail requirements → entities → API → high-level design in order; flag scaling issues verbally but finish breadth first.
- Fan-out on read vs fan-out on write is *the* core tradeoff; the great answer is a **hybrid per-account strategy**.
- Precomputed feed table (~200 post IDs per user) + async queue workers for writes.
- Hot keys: replicated (not just sharded) cache for viral posts.
- Idempotent PUT for follow; timestamp cursor for pagination.
