# Common Patterns (System Design in a Hurry)

**Source:** https://www.hellointerview.com/learn/system-design/in-a-hurry/patterns

## Why Patterns Matter

- Combining key technologies + core concepts builds any system, but interview success under time pressure is all about **patterns**.
- Recognizing which pattern a design needs lets you fall back on best practices and avoid reinventing the wheel — a skill that often **separates senior from junior engineers** in interviews.
- Patterns tell you what's interesting vs not, and expose **common failure modes** you'd otherwise reverse-engineer on the fly.
- Patterns are **not mutually exclusive** — most systems combine several.

---

## 1. Pushing Realtime Updates

**Problem:** Chat apps, notifications, live dashboards need updates pushed to users as they happen (synchronous APIs just return a response; that's not enough here).

**Key decisions:**
- **Protocol choice:** simple HTTP polling (simplest, least efficient) vs Server-Sent Events (SSE) vs websockets (purpose-built but tricky infrastructure).
  - **Recommendation: start with HTTP polling** until it no longer serves your needs, then move to SSE or websockets.
- **Server side:**
  - **Pub/Sub services** decouple publisher and subscriber (used in the WhatsApp breakdown).
  - **Stateful servers in a consistent hash ring** (or similar) for heavier per-connection processing (used in the Google Docs breakdown).

Full detail: [Realtime Updates pattern](https://www.hellointerview.com/learn/system-design/patterns/realtime-updates) and [Networking Essentials](https://www.hellointerview.com/learn/system-design/core-concepts/networking-essentials).

---

## 2. Managing Long-Running Tasks

**Problem:** Operations too long for synchronous handling — video encoding, report generation, bulk operations, anything over a few seconds.

**Solution shape:** split into **immediate acknowledgment + background processing**:
1. Web server instantly validates the request, pushes a job to a queue (Redis or Kafka), returns a **job ID within milliseconds**.
2. Separate **worker processes** pull jobs from the queue and do the actual work.

**Benefits:** fast user response, independent scaling of web servers vs workers, fault isolation.

**Warning / tradeoff:** Candidates are too quick to push processing behind a queue — often a **bad decision**. For short-running jobs, returning status synchronously dramatically simplifies architecture, gives clearer back-pressure, and better UX.

**Key technologies:** message queues for coordination + worker pools. Must handle **job status tracking, retries, and failure scenarios** (dead letter queues for poison messages).

Full detail: [Managing Long-Running Tasks pattern](https://www.hellointerview.com/learn/system-design/patterns/long-running-tasks).

---

## 3. Dealing with Contention

**Problem:** Multiple users hitting the same resource simultaneously — booking the last concert ticket, bidding on an auction item. Need to prevent race conditions and keep data consistent.

**Solution spectrum:**
- Database-level: **pessimistic locking**, **optimistic concurrency control**, atomicity/transactions.
- Distributed coordination: **distributed locks**, **two-phase commit**, **queue-based serialization**.

**Tradeoffs:** performance vs consistency guarantees; simple single-database solutions vs complex distributed coordination. **Most problems should start with a single-database solution** before scaling to distributed approaches.

**Key insight:** Databases are *built around* contention problems. Splitting data across multiple databases means taking on all the challenges databases were designed to solve. Sometimes appropriate — but don't do it prematurely. Interviewers probe whether you understand what you're giving up by breaking data apart.

Full detail: [Dealing with Contention pattern](https://www.hellointerview.com/learn/system-design/patterns/dealing-with-contention).

---

## 4. Scaling Reads

**Problem:** Read traffic is usually the **first bottleneck** as you grow — reads consume data and grow faster than writes.

**Numbers:** read-to-write ratios start around **10:1** and often reach **100:1 or higher**. Example: opening Instagram triggers hundreds of DB queries (photo metadata, user info, engagement data), while you might post once a day (one write).

**Natural progression:**
1. Optimize reads **inside the database**: indexing, denormalization.
2. Scale horizontally with **read replicas**.
3. Add external caching layers: **Redis, CDNs**.

**Key considerations:** cache invalidation, **replication lag** on read replicas, and **hot keys** (millions of users requesting the same popular content simultaneously).

Full detail: [Scaling Reads pattern](https://www.hellointerview.com/learn/system-design/patterns/scaling-reads).

---

## 5. Scaling Writes

**Problem:** At millions of writes/second, individual DB servers and storage hit hard limits.

**Core strategies:**
- **Horizontal sharding** — distribute data across multiple servers.
- **Vertical partitioning** — separate different types of data.
- **Burst handling** — write queues to buffer temporary spikes; **load shedding** to prioritize important writes during overload.
- **Batching** — group multiple writes to reduce per-operation overhead.

**Key consideration:** choosing good **partition keys** that distribute load evenly while keeping related data together.

Full detail: [Scaling Writes pattern](https://www.hellointerview.com/learn/system-design/patterns/scaling-writes) and the [Sharding core concept](https://www.hellointerview.com/learn/system-design/core-concepts/sharding).

---

## 6. Handling Large Blobs

**Problem:** Large files (videos, images, documents) shouldn't route gigabytes through your application servers.

**Solution:** direct client-to-storage transfers.
- App server generates temporary, scoped credentials (**presigned URLs**) so clients upload **directly to blob storage** (S3).
- Downloads served from **CDNs** with signed URLs for access control.

**Benefits:** eliminates app servers as bottlenecks; enables resumable uploads, progress tracking, global distribution.

**Key challenges:** state synchronization between DB metadata and blob storage, handling upload failures, lifecycle management of large files. **Event notifications** from the storage service keep application state consistent.

Full detail: [Large Blobs pattern](https://www.hellointerview.com/learn/system-design/patterns/large-blobs).

---

## 7. Multi-Step Processes

**Problem:** Business processes spanning multiple services and long-running operations that must survive failures, retries, and external dependencies — order fulfillment, user onboarding, payment processing.

**Solution spectrum:**
- Simple **single-server orchestration**.
- **Event sourcing** — each step emits events that trigger subsequent steps (distributed approach).
- **Workflow engines / durable execution** — Temporal, AWS Step Functions: automatic state management, failure recovery, retry logic.

**Key insight:** move from scattered state management and manual error handling to **declarative workflow definitions** where the system guarantees exactly-once execution and maintains complete audit trails.

Full detail: [Multi-Step Processes pattern](https://www.hellointerview.com/learn/system-design/patterns/multi-step-processes).

---

## 8. Proximity-Based Services

**Problem:** Searching entities by location — Design Uber, Design Gopuff.

**Solution:** **Geospatial indexes** for efficient proximity queries. Options:
- Extensions to commodity DBs: **PostgreSQL + PostGIS**, **Redis geospatial data type**.
- Dedicated: **Elasticsearch with geo-queries**.

**Architecture:** divide the geographic area into manageable regions, index entities within regions — quickly excludes vast areas without relevant entities, shrinking the search space.

**When NOT to use:** geospatial indexes only pay off at **hundreds of thousands to millions of items**. For ~1,000 items, a full scan beats the overhead of a purpose-built index or service.

**Note:** most systems don't need global queries — proximity usually means users searching for entities *local* to them.

---

## Pattern Selection

- Patterns compose. Example — a video platform: **Large Blobs** for uploads + **Long-Running Tasks** for transcoding + **Realtime Updates** for progress notifications + **Multi-Step Processes** to coordinate the workflow.
- Recognize which patterns apply and understand their tradeoffs.
- **Start simple** (polling, single-server orchestration) and add complexity only when specific requirements demand it.
- Proactively identifying patterns in interviews demonstrates architectural maturity and keeps you focused on what matters instead of implementation weeds.
