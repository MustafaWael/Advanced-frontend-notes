---
tags: [system-design, backend, patterns, interview]
module: "30 - Backend System Design"
priority: must-know
status: not-started
aliases: [access patterns, real-time updates, dealing with contention, scaling reads writes]
---

# The Seven Access Patterns

## Maturity Target

- Priority: #must-know
- Study time: 45 minutes
- Interview signal: Recognize which of the seven recurring patterns a problem needs, and name each one's core solution and tradeoff.
- Production signal: You see the same patterns in the systems you integrate with and can reason about their guarantees.
- Dependencies: [[30 - Backend System Design/02 - Networking and Protocols|Networking and Protocols]], [[30 - Backend System Design/05 - Caching|Caching]], [[30 - Backend System Design/06 - Sharding and Consistent Hashing|Sharding and Consistent Hashing]]

## Source Anchors

- [HelloInterview — Patterns](https://www.hellointerview.com/learn/system-design/patterns/real-time-updates)
- [microservices.io — Saga pattern](https://microservices.io/patterns/data/saga.html)
- [AWS — Presigned URLs (S3)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)

> [!note] Source coverage: HelloInterview's pattern articles are largely premium; the free scrape captured each pattern's problem framing and when-to-use but not full solution detail. This note teaches the patterns at framing depth and flags where to go deeper. Solution internals should be verified against the source before being quoted as fact — this note's `status` stays `not-started` until that pass. (Provenance caveat, not a footgun — hence a note, not a warning.)

## 1. Concept

These seven patterns are the backend analog of RADIO's optimization phase: the recurring "deep dive" shapes. Most questions are a combination of two or three.

1. **Real-time Updates** — push fresh data to clients. Two hops: *client↔server* (polling / SSE / WebSockets — [[30 - Backend System Design/02 - Networking and Protocols|protocols]]) and *server-side sourcing* (pub/sub, Kafka fan-out). Problems: live comments, notifications, presence, chat. Tradeoff: statefulness and connection-count scaling.
2. **Dealing with Contention** — concurrent writes to one resource (last seat, last item). Solutions span pessimistic locks (`SELECT ... FOR UPDATE`), optimistic concurrency (version check), distributed locks (Redis/ZooKeeper), and idempotency keys. Problems: Ticketmaster, auctions, inventory. Tradeoff: locks reduce throughput; optimistic retries add complexity.
3. **Multi-step Processes** — reliable multi-stage workflows across services that must not half-complete (you can't wrap a distributed transaction in one ACID commit). A **saga** breaks the workflow into local transactions, each with a **compensating action** that undoes it, so a failure at step 3 runs the compensations for steps 2 and 1 (semantic rollback, not a real rollback). Two coordination styles: **orchestration** (a central coordinator calls each step and drives compensation — easier to reason about, one place to change) vs **choreography** (each service reacts to the previous one's event via a durable log like Kafka — no central bottleneck, but the flow is emergent and harder to trace). Problems: payments, order fulfillment. Tradeoff: exactly-once is impractical, so every step must be idempotent to survive retries.
4. **Scaling Reads** — read-heavy load. Three-tier progression: read replicas → caching → CDN. Problems: news feed, product pages. Tradeoff: replica lag and cache staleness (eventual consistency).
5. **Scaling Writes** — write-heavy load. Sharding, write-behind buffering, queues + batching, LSM-tree stores. Problems: ad-click aggregation, metrics ingestion. Tradeoff: throughput bought with eventual consistency / possible loss.
6. **Handling Large Blobs** — big files (video, images). Don't stream bytes through app servers — issue **presigned URLs** for direct client↔object-storage (S3) transfer, then serve via CDN. Problems: Dropbox, YouTube upload. Tradeoff: client-direct upload complicates validation/virus-scanning (do it async).
7. **Managing Long-Running Tasks** — work too slow for a request cycle (transcode, crawl, report). Offload to a **queue + worker pool**; client polls or gets pushed status. Problems: video processing, web crawler. Tradeoff: added infra and eventual completion; you design the status/notification UX.

> [!tip] Frontend mirror: patterns 1 and 2 are your daily bugs at scale. Real-time Updates is the same transport table as [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]]. Dealing with Contention is [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|race conditions]] and double-submit guards, one scale up. Handling Large Blobs is why your upload widget gets a presigned URL instead of POSTing the file to your API.

## 2. Why It Matters

Naming the pattern is how you structure a deep dive: "this is a contention problem, so the core question is how I serialize the booking" orients the whole discussion. It's also how you read real systems — recognizing that your upload flow is the Large Blobs pattern, or that your notifications are Real-time Updates over SSE, tells you their failure modes in advance.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a file-upload feature POSTs files to `/api/upload`, which forwards them to S3. Large uploads time out, and the API servers' memory spikes under load.

Trace: this is the **Handling Large Blobs** pattern done wrong — bytes are streaming *through* the stateless app tier, tying up a request thread and buffering big payloads in app memory. App servers should route metadata, not megabytes.

Fix: the API returns a **presigned S3 URL**; the browser uploads the file directly to object storage and then tells the API "done, here's the key." The API never touches the bytes; downloads serve from a CDN in front of S3.

```text
client → POST /uploads (metadata) → API returns presigned PUT URL
client → PUT file directly to S3 (bypasses app tier)
client → POST /uploads/:id/complete → API records the object key
```

Tradeoff: direct-to-S3 means validation and virus scanning can't happen inline — do them asynchronously (an S3 event triggers a worker: the Long-Running Tasks pattern), and hold the object as "pending" until it passes.

## 4. Interview Answer

Short answer:

> Most backend problems are a combination of a few recurring patterns: real-time updates, contention, multi-step processes, scaling reads, scaling writes, large blobs, and long-running tasks. I identify which ones a prompt needs early — "this is read-heavy plus real-time," or "this is a contention problem" — because that names the core deep dive and its tradeoff, like replica lag for scaling reads or throughput loss for locking under contention.

Deeper answer:

> Two are the ones I know best from the frontend: contention and real-time. Contention is serializing concurrent writes — pessimistic locks trade throughput for safety, optimistic concurrency trades complexity for throughput, and idempotency keys make retries safe, which is the exact server-side analog of a double-submit guard. Real-time is the two-hop problem — the client protocol (SSE vs WebSockets) plus how the server sources and fans out the data — and the scaling cost is holding stateful connections, not the protocol itself. Large blobs and long-running tasks both come down to keeping heavy work off the request path: presigned URLs and queue-plus-workers.

## 5. Practice

1. <details><summary>A prompt: "design Ticketmaster seat booking." Which pattern dominates and what's the core decision?</summary>Dealing with Contention — many users compete for the same seat. Core decision: how to serialize the claim (a short-lived hold via a lock/reservation with TTL, or optimistic version check), plus idempotency so a retried booking doesn't double-charge. Tradeoff: holds reduce effective inventory availability and throughput.</details>
2. <details><summary>Why route large file uploads around your API servers?</summary>Streaming big files through stateless app servers ties up request threads and buffers megabytes in app memory, killing throughput. Presigned URLs let the client transfer directly to object storage; the API only handles metadata, and downloads serve from a CDN. Validation moves to async workers.</details>
3. <details><summary>Which two patterns show up most in everyday frontend work, and as what?</summary>Real-time Updates (live UI via SSE/WebSockets, and its reconnection/fan-out concerns) and Dealing with Contention (race conditions, double-submit, optimistic-update reconciliation). Both are the same problems you handle on the client, one scale larger.</details>

## Related Notes

- [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE and Polling]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]] (Kafka)
