# 13 - FB Live Comments (Design Facebook's Live Comments System)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-live-comments
**Difficulty:** Medium · Pattern: Real-time Updates

Facebook Live Comments lets viewers post comments on a live video feed and see a continuous stream of comments in near-real-time.

---

## Functional Requirements

**Core:**
1. Viewers can post comments on a Live video feed.
2. Viewers can see new comments being posted while they are watching the live video.
3. Viewers can see comments made before they joined the live feed.

**Below the line (out of scope):** replying to comments, reacting to comments.

## Non-Functional Requirements

**Core:**
1. Scale to **millions of concurrent videos** and **thousands of comments/second per live video**.
2. **Availability over consistency** — eventual consistency is fine.
3. **Low latency** — broadcast comments in near-real time (< 200ms end-to-end under typical network conditions).

**Below the line:** security (authorized posting only), integrity (spam/hate-speech moderation).

Fun fact: humans perceive interactions under ~200ms as instantaneous — that's the target for real-time systems.

---

## Core Entities

Think of these as the "nouns" — don't enumerate every column yet, build the data model as the design progresses.

1. **User** — a viewer or broadcaster.
2. **Live Video** — the video being broadcast (owned by another team; we integrate with it).
3. **Comment** — a message posted by a user on a live video.

## API Design

**Post a comment:**
```
POST /comments/:liveVideoId
Header: JWT | SessionToken
{ "message": "Cool video!" }
```
`userId` comes from the auth header (JWT/session token), never the request body — prevents impersonation.

**Fetch past comments:**
```
GET /comments/:liveVideoId?cursor={last_comment_id}&pageSize=10&sort=desc
```
Pagination is important here (see below).

---

## High-Level Design

### 1) Viewers can post comments
Simple flow: **Commenter Client** → **Comment Management Service** → **Comments Database**.
- DB choice: **DynamoDB** — fast, scalable, highly available; comments are simple with no complex relationships/transactions. (Postgres/MySQL would also work.)

### 2) Viewers see new comments in real-time
Start with the naive approach: **polling** — clients poll `GET /comments/:liveVideoId?since={last_comment_id}` every few seconds and append new comments.

Why it fails: to hit "near real-time" you'd need to poll every few milliseconds; most polls return nothing; heavy DB strain. Doesn't scale — improved in Deep Dive 1 with a push model. (In an interview, jumping straight to the better solution is fine if you justify it; starting simple is fine too if the problem is new to you.)

### 3) Viewers see comments made before they joined
Users need (a) real-time new comments and (b) a scrollable history ("infinite scrolling"). We need "the N most recent comments before a certain point" → **pagination**.

**Bad: Offset pagination** (`?offset=0&pagesize=10`)
- Inefficient: DB counts through all preceding rows per query — gets slower as volume grows.
- Not stable: comments added/deleted while scrolling shift the offset → duplicates or missing comments.

**Great: Cursor pagination** (`?cursor={last_comment_id}&pageSize=10`)
- Efficient (with an index on the cursor field — no scanning preceding rows), stable under inserts/deletes, fits DynamoDB key-based queries (`liveVideoId = :id AND commentId < :cursor`, `ScanIndexForward: false`), and performance stays consistent as volume grows.
- Remaining cost: still one DB query per page, which matters at high traffic.

---

## Deep Dive 1: Broadcasting comments in real-time

Replace polling with a **push-based model**. Two options:

### Good: WebSockets
Two-way persistent connection; server pushes new comments immediately.
**Why not ideal here:** our read/write ratio is heavily imbalanced — most viewers read all comments but rarely post. A full duplex channel per viewer carries high connection-maintenance overhead for little benefit. (WebSockets are optimal for balanced read/write chat apps.)

### Great: Server-Sent Events (SSE)
Persistent **one-way** server→client stream over standard HTTP — simpler than WebSockets. Comment creation uses ordinary HTTP POSTs; reads use SSE streaming. Best fit for the imbalanced ratio.
**Challenges:** some proxies/load balancers buffer streaming responses (hard-to-debug issues); browsers limit concurrent SSE connections per domain (problem for watching multiple videos); long-lived connections complicate monitoring/debugging.

Updated flow: comment persisted → Comment Management Service pushes it over SSE to all clients subscribed to that live video → clients append it to the feed. (This single-service version doesn't scale — next deep dive.)

## Deep Dive 2: Scaling to millions of concurrent viewers

SSE requires an open connection per viewer. Modern servers handle ~100k connections (CPU/memory/file descriptors are the bottleneck — NOT the 65,535 port-number myth; each TCP connection is a unique 4-tuple, so one listening port can handle hundreds of thousands+). Millions of viewers → horizontal scaling.

### Part 1: Server coordination
Viewers of the same video land on different servers (UserA on Server 1, UserB on Server 2). A comment hitting Server 1 can't reach UserB. All viewers must see comments regardless of which server they're on.

**Good: Naive pub/sub — every server processes every comment**
- Separate **Realtime Messaging Servers** for read/broadcast traffic (writes are far lower volume; scale them independently). Round-robin load balancing; each server keeps an in-memory map of `liveVideoId → [SSE connections]`.
- Comment Management Service publishes each new comment to a channel; all messaging servers subscribe and forward to their relevant viewers.
- **Challenge:** every server processes every comment across all videos, even with no relevant viewers connected — wasted compute; impractical at Facebook scale.

**Great: Partitioned pub/sub with viewer co-location**
- Partition the comment stream into N channels via `hash(liveVideoId) % N` (channel-per-video would be too many, possibly infeasible in Kafka); servers subscribe only to channels they need.
- Problem: round-robin still spreads a server's viewers across many videos → many subscriptions. Fix with **intelligent routing**: an L7 load balancer (NGINX/Envoy) using **consistent hashing on liveVideoId** routes viewers of the same video to the same server; alternatively a dynamic liveVideoId→server mapping in **ZooKeeper** (more flexibility, more operational complexity).
- **Challenges:** coordinating load balancing with pub/sub subscriptions as viewer composition changes; keeping routing mappings in sync as servers scale up/down.

**Great: Dispatcher Service instead of pub/sub**
- Invert the model: a **Dispatcher Service** maintains a dynamic map of which servers host viewers of which videos (kept in sync via heartbeats/registration) and forwards each new comment directly to those servers.
- Pros: no pub/sub subscription management, centralized routing logic, easy to add sophisticated routing rules (e.g. load-based). Multiple Dispatcher instances behind a load balancer share coordination data (ZooKeeper/etcd).
- **Challenges:** keeping the mapping accurate during rapid change (viral streams); coordinated cache invalidation across Dispatcher instances.

Pub/sub technology trade-offs (advanced): **Kafka** is scalable and fault-tolerant but struggles with dynamic subscription patterns (users switching videos); **Redis pub/sub** is low-latency and handles dynamic subscriptions well — its fire-and-forget nature is fine because comments are persisted in the DB and the catch-up mechanism (Deep Dive 3) handles missed messages. Verdict: both co-located pub/sub and the dispatcher are great; **pub/sub is usually easier with fewer corner cases — the one to reach for in an interview**.

### Part 2: Mega-streams (e.g. World Cup final)
Hundreds of millions of viewers, thousands of comments/sec. At 5,000 comments/sec, each on-screen message lasts ~4ms — nobody can read that. The requirements themselves change: users experience a "vibe" of collective participation, not a readable conversation, so low latency and delivery of every message matter less.

**Good: Show a representative subset (sampling)**
- Sample the comment stream with a rate that adapts to velocity (e.g. 50% at 100/sec, 1–2% at 5,000/sec) so each viewer gets a roughly constant, readable comments/sec.
- Smarter than random: prioritize comments from followed users, comments getting reactions, verified accounts.
- **Challenge:** still millions of persistent SSE connections — infrastructure cost reduced but substantial.

**Great: CDN-based delivery with periodic snapshots**
- Switch mega-streams to a **pull model**: server keeps a ring buffer of the last 100–200 comments; every ~1 second, snapshot it to Redis/CDN origin; CDN caches at edge locations.
- Clients poll the CDN every second; new comments are **animated smoothly over the polling interval** (using timestamps for natural spacing) rather than dumped at once.
- Leverages existing infrastructure — a comment snapshot is just cacheable content.
- **Dynamic threshold:** auto-flip from SSE to CDN when a stream crosses e.g. 100k concurrent viewers or 500 comments/sec; client handles the transition seamlessly.
- **Trade-offs/challenges:** 1–2s latency instead of <200ms (acceptable at this scale); "read your own write" — client optimistically inserts the user's own comments immediately; need **hysteresis** in the threshold to avoid flapping between SSE and CDN modes.

Summary: pub/sub + co-location for normal videos; sampling as a middle ground; CDN snapshots as the most scalable mega-stream answer. Discussing sampling shows strong understanding; the CDN approach shows **staff-level thinking** (recognizing that requirements change at extreme scale).

## Deep Dive 3: Client disconnections / not missing comments

Mobile networks are flaky (tunnels, backgrounded apps, WiFi↔cellular switches).

**Bad: Ignore disconnections** — on reconnect, just stream from now onward. Users miss reactions to big moments; visible gaps; long disconnections lose all context.

**Great: Last-Event-ID with client-side tracking**
- SSE has built-in reconnection: each comment carries a unique event ID (comment ID); on auto-reconnect, the browser sends the **Last-Event-ID header** and the server replays missed comments before resuming.
- For more control, the client tracks the last comment ID locally (localStorage / app storage) and requests catch-up via `GET /comments/:liveVideoId?since={last_comment_id}&limit=100` — enabling better UX like animating missed comments at 2–3x speed or "You missed 47 comments — jump to live".
- Mobile/battery: preemptively disconnect SSE when backgrounding (recording position), reconnect and catch up on foreground — better than a throttled background connection.
- **Bounded replay:** don't replay an hour of comments; ~last 5 minutes is reasonable, with graceful degradation for longer gaps.
- **Challenges:** the user likely reconnects to a *different* messaging server, so recent comment history must live in a **shared Redis cache** any server can replay from; the client must deduplicate/merge (by comment ID) when SSE messages arrive while an HTTP catch-up response is being processed.

Interview tip: Last-Event-ID is the foundation, but mention bounded replay, client-side position tracking, and graceful degradation — shows you've thought about messy mobile realities.

---

## What is Expected at Each Level?

### Mid-level (E4)
- ~80% breadth / 20% depth; components can be surface-level abstractions; interviewer probes basics; you drive early stages, interviewer may drive later ones.
- **Bar for FB Live Comments:** proactively recognize polling's limitations and reason toward a push model; with only minor hints arrive at the pub/sub solution; scale it with some interviewer help.

### Senior (E5)
- ~60% breadth / 40% depth; know pub/sub for broadcasting and its challenges; articulate trade-offs; anticipate bottlenecks.
- **Bar:** speed through the high-level design; reason through its limitations and reach pub/sub with minimal hints; proactively lead the scaling discussion and reason through trade-offs of different solutions.

### Staff+ (E6+)
- ~40% breadth / 60% depth; breeze through basics; high proactivity (interviewer intervenes only to focus); practical technology experience.
- **Bar:** identify pub/sub, proactively call out its reliability/scalability limitations and suggest solutions; know the exact technology you'd use and discuss trade-offs in detail.
