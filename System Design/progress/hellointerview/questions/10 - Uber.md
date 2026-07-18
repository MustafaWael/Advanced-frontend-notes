# 10 - Uber (Ride-Sharing Service)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/uber
**Author:** Evan King · Difficulty: **Hard** · Patterns: **Real-time Updates**, **Multi-step Processes**

> Uber is a ride-sharing platform connecting passengers with drivers offering transportation in personal vehicles. Users book on-demand rides from their smartphones and are matched with a nearby driver who takes them from pickup to destination.

---

## 1. Understanding the Problem

### Functional Requirements

> Start by defining functional ("Users should be able to...") and non-functional ("The system should...") requirements. **Prioritize the top 3** functional requirements; mark everything else "below the line" and check with the interviewer.

**Core:**
1. Riders can input a start location and destination and get a **fare estimate**.
2. Riders can **request a ride** based on the estimated fare.
3. Upon request, riders are **matched with a nearby, available driver**.
4. Drivers can **accept/decline** a request and navigate to pickup/drop-off.

**Below the line:** ratings (rider↔driver), scheduled rides, ride categories (X, XL, Comfort).

### Non-Functional Requirements

**Core:**
1. **Low latency matching** (< 1 minute to match or fail).
2. **Strong consistency in ride matching** — no driver may be assigned multiple rides simultaneously.
3. **High throughput**, especially peak hours / special events (100k requests from the same location).

**Below the line:** security/privacy (GDPR), resiliency/failover, monitoring/logging/alerting, CI/CD.

> Listing out-of-scope features shows product thinking and lets the interviewer reprioritize — but it's a nice-to-have; don't waste time if they don't come quickly.

---

## 2. The Set Up

### Planning the Approach
Build the design sequentially through the functional requirements, then use the non-functional requirements to drive deep dives.

### Core Entities
1. **Rider** — user requesting rides; personal info, payment methods.
2. **Driver** — registered driver; personal details, vehicle info (make/model/year), preferences, availability status.
3. **Fare** — an estimated fare: pickup + destination, estimated fare, ETA. (Could live on the Ride object instead — no right or wrong answer.)
4. **Ride** — an individual ride from fare confirmation to completion: rider/driver identities, vehicle, state, planned route, actual fare, pickup/drop-off timestamps.
5. **Location** — real-time driver location: lat/long + last-update timestamp. Crucial for matching and ride tracking.

### API Design

Fare estimate (POST because it creates a Fare entity):
```
POST /fare -> Fare
Body: { pickupLocation, destination }
```

Request ride (kicks off matching in the backend — no separate matching endpoint needed):
```
POST /rides -> Ride
Body: { fareId }
```

Driver location update (called periodically by the driver client):
```
POST /drivers/location -> Success/Error
Body: { lat, long }
// driverId comes from session cookie / JWT — NOT body or path params
```

Accept/decline ride request:
```
PATCH /rides/:rideId -> Ride
Body: { accept/deny }
```
The returned Ride contains pickup/destination so the driver client can display them.

> **Security red flag to avoid:** never pass userId, timestamps, or fareEstimate from the client — clients can't be trusted. User identity comes from session/JWT; timestamps are server-generated; fares are read from the DB.

---

## 3. High-Level Design

### 1) Fare estimate
Components: **Rider Client** (iOS/Android) → **API Gateway** (routing, auth, rate limiting) → **Ride Service** (manages ride state, calculates fares) → **Third-Party Mapping API** (e.g., Google Maps, for distance/travel time) + **Database** (stores Fare entities).

Flow: rider enters pickup + destination → `POST /fare` → gateway auth/rate-limit → Ride Service calls mapping API for distance/time, applies pricing model → creates Fare in DB → returns Fare to client for accept/decline.

### 2) Request a ride
No new services — just add a **Ride table**. Flow: client `POST /rides` with fareId → Ride Service creates Ride linked to the accepted Fare with status `requested` → triggers the matching flow.

### 3) Match with a nearby available driver
New components:
- **Driver Client** — receives ride requests, sends location updates.
- **Location Service** — receives driver location updates, stores them, serves latest locations to matching.
- **Ride Matching Service** — consumes ride requests; matching algorithm (abstracted for the interview) ranks available drivers by proximity, availability, rating, etc.

Flow: ride request → Ride Service → Ride Matching Service. Meanwhile drivers continuously post locations to the Location Service (DB updated with latest lat/long). Matching queries the closest available drivers for an optimal match.

### 4) Driver accepts/declines and navigates
One new service:
- **Notification Service** — pushes real-time notifications to drivers via **APNs** (iOS) / **FCM** (Android).

Flow: matching service notifies the top-ranked driver → driver accepts via `PATCH /rides/:rideId` (decline → notify next driver on the list) → Ride Service sets status `accepted`, assigns driver, returns pickup coordinates → driver navigates with on-device GPS.

> **Pattern: Real-time Updates** — push notifications to drivers; options range from long-polling to SSE to WebSockets.

---

## 4. Deep Dives

> How proactively you drive deep dives is a function of seniority: mid-level interviews can be interviewer-driven; senior/staff+ candidates should proactively "look around corners."

### Deep Dive 1: Frequent driver location updates + efficient proximity search

Two problems with the naive design:
1. **Write volume:** ~10M drivers × update every 5s ≈ **2M writes/sec**. DynamoDB or PostgreSQL would fall over or be prohibitively expensive (DynamoDB at ~$1.25/M WRUs → **$200k+/day**).
2. **Query efficiency:** proximity search over lat/long needs a full table scan; B-tree indexes are poor for multi-dimensional geo data. Non-starter.

- **Bad: direct DB writes + raw proximity queries.** Doesn't scale; overload, high latency.
- **Good: batch processing + specialized geospatial DB.** Aggregate updates over an interval and batch-write (fewer write transactions, less lock contention). Use geospatial indexing — e.g., **quad-trees** (recursive quadrant partitioning of 2D space) — for fast radius queries. PostgreSQL's **PostGIS** plugin gives geospatial types/functions without a separate DB. *Challenge:* batching delay → stale locations → suboptimal matches.
- **Great: real-time in-memory geospatial store (Redis).** Redis geospatial commands use **geohashing** (lat/long → 52-bit score in a sorted set keyed by driverId). `GEOADD` for updates, `GEOSEARCH` for radius/bounding-box queries (replaces GEORADIUS since Redis 6.2). No batching needed — each GEOADD overwrites the previous location, so the latest position is always there. Handle stale/offline drivers with a periodic cleanup (companion sorted set keyed by timestamp; remove entries older than ~30s from both sets).
  *Challenge:* **durability** — in-memory data can be lost. Mitigate with Redis persistence (RDB/AOF) and Redis Sentinel for failover. Even with data loss, locations refresh every 5s, so full state rebuilds in seconds.

### Deep Dive 2: Reducing update volume while keeping location accuracy

- **Great: Adaptive location update intervals.** The driver app uses on-device sensors/algorithms to pick the update frequency dynamically: stationary/slow → infrequent updates; fast-moving or frequently changing direction (or near pending requests) → frequent updates. *Challenge:* algorithm complexity and testing, but done well it dramatically cuts update volume.

> **Don't neglect the client.** Client-side logic often improves efficiency and scalability (here: adaptive pings; in file-upload systems: chunking and compression).

### Deep Dive 3: Preventing multiple ride requests to the same driver (consistency)

One driver per request, one request per driver, 10-second accept window — nearly identical to Ticketmaster's ticket reservation problem.

- **Bad: application-level locking with manual timeout checks.** Each matching-service instance marks a request "locked" and runs a local timer. *Problems:* no cross-instance coordination (race conditions), inconsistent lock state if an instance crashes before releasing (locked forever), worsens as instances scale.
- **Good: database status update + timeout handling.** Move the lock into the DB (transactional): set driver status `outstanding_request`, then `accepted`/`available`. *Challenge:* still relies on an in-memory timeout in the Ride Service — a crash loses the timer and the lock hangs. A cron job to release expired locks works but adds complexity and delay.
- **Great: distributed lock with TTL (Redis).** On sending a request, acquire a lock on `driverId` with **TTL = 10s**. While held, no other instance can send that driver a request. Accept → update ride to `accepted` in DB, release lock. No response → lock expires automatically, driver becomes eligible again. *Challenge:* dependence on the in-memory store's availability/performance (needs monitoring + failover) — but 10s lock lifetime makes recovery easy; a reasonable tradeoff.

### Deep Dive 4: No dropped ride requests during peak demand

- **Bad: first-come-first-served, no queue** (current design). Surges overwhelm the service before horizontal scaling can react; if a matching-service instance crashes, its in-flight requests are lost — riders wait forever.
- **Great: queue with dynamic scaling.** Put ride requests on a queue; matching service consumes; scale consumers horizontally when the queue grows. **Partition queues by geographic region.** Use **Kafka** and commit the message offset only *after* a match succeeds — if the service dies, the request stays on the queue for another instance (fault tolerance, no lost requests). *Challenges:* operating a queue (use managed: SQS / Amazon MSK / Confluent Cloud); FIFO head-of-line blocking — consider a **priority queue** (proximity, rating, etc.) so important requests process first.

### Deep Dive 5: What if a driver fails to respond in time?

> **Pattern: Multi-step Processes.** Human-in-the-loop flows signal this pattern — Uber originally authored Cadence, which birthed Temporal, for exactly these use cases.

- **Good: delay queue.** When a request goes to a driver, simultaneously schedule a delayed message (e.g., SQS delay queue) for the 10s timeout. When it fires, if the ride is still unassigned, send to the next ranked driver and schedule another delayed message. *Challenges:* canceling delayed messages when a driver accepts; race conditions between the delay queue and matching service.
- **Great: durable execution (Temporal / AWS Step Functions).** Model the whole matching flow as a durable workflow with built-in timeouts, retries, and persistent state that survives crashes/restarts: send request to driver #1 → 10s timeout → accept completes the workflow; decline/timeout advances to the next driver until matched or exhausted. *Challenges:* added orchestration complexity, new tooling to learn/monitor — but guaranteed execution and fault tolerance usually outweigh this for mission-critical flows where dropped requests cost revenue.

### Deep Dive 6: Further scaling for latency and throughput

- **Bad: vertical scaling.** Expensive, needs downtime, has hard limits, not fault-tolerant. Barely worth discussing at this scale.
- **Great: geo-sharding with read replicas.** Shard data (and services, queues, databases) **geographically**; use read replicas for read throughput. Also cuts latency by moving servers closer to clients. Scatter-gather across shards is only needed for proximity searches at region boundaries. *Challenges:* shard management and rebalancing — use **consistent hashing** for distribution plus a replication strategy for fault tolerance/HA.

---

## 5. What is Expected at Each Level?

### Mid-level
- **Breadth over depth (80/20).** High-level design meeting the functional requirements; many components as surface-level abstractions.
- Interviewer probes basics (e.g., what an API Gateway does); expects you to drive early stages while they may drive the later deep dives.
- **Bar for Uber (E4):** clearly defined API endpoints and data model; functional high-level design meeting requirements; recognized the need for **some spatial index** for location search (a specific solution not required); implemented **at least the "good" solution** to the ride-request locking problem (DB status + timeout).

### Senior
- **60% breadth / 40% depth**; hands-on technical detail; discuss distributed cache for locking drivers and detailed scaling strategies (sharding, replication — probing/hints OK); articulate pros/cons of architectural choices.
- **Bar for Uber (E5):** speed through the high-level design; discuss in detail **at least 2 of**: location-search speedups, ride-request locking, ride-request queueing — plus tradeoffs on scalability/performance/maintainability.

### Staff+
- **40% breadth / 60% depth**; experience-backed practical technology choices; high proactivity (interviewer intervenes only to focus, not steer).
- **Bar for Uber:** deep dives into **3+ key areas** with innovative, optimal solutions; the interviewer should come away having learned something.

---

## Key Takeaways (study notes)
- Two hard NFRs dominate: **strong consistency in matching** (one ride per driver) and **low-latency matching at surge scale**.
- Location firehose (≈2M writes/s) → **Redis geospatial (GEOADD/GEOSEARCH, geohashing)** instead of a durable DB; loss is fine since drivers re-ping every 5s. Reduce volume further with **adaptive client-side update intervals**.
- Driver locking = Ticketmaster reservation problem → **Redis distributed lock with 10s TTL**.
- Surge protection → **Kafka queue, offset committed only after match**, geo-partitioned, dynamically scaled consumers; consider priority queues.
- Driver timeouts → **durable execution (Temporal/Step Functions)** for the multi-step matching workflow.
- Global scale → **geo-sharding + read replicas + consistent hashing**.
- API hygiene: identity from JWT/session, server-generated timestamps, fares from the DB — never trust the client.
