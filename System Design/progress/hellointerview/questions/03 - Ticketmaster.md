# 03 - Ticketmaster (Ticket Booking)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/ticketmaster
**Author:** Evan King (Hello Interview) · **Difficulty:** Medium · **Patterns:** Dealing with Contention, Scaling Reads, Real-time Updates

> **What is Ticketmaster?** An online platform that lets users purchase tickets for concerts, sports events, theater, and other live entertainment.

---

## 1. Functional Requirements

Start by defining requirements: functional = "Users should be able to..."; non-functional = "The system should...". **Prioritize the top 3** and mark the rest below the line — check with the interviewer about repriorities.

**Core:**
1. Users should be able to **view events**.
2. Users should be able to **search for events**.
3. Users should be able to **book tickets** to events.

**Below the line:**
1. Users view their booked events.
2. Admins/event coordinators add events.
3. Dynamic pricing for popular events.

## 2. Non-Functional Requirements

**Core:**
1. **Availability** for search/viewing, but **consistency for booking** (no double booking).
2. Scalable to handle **popular events** (10 million users, one event).
3. **Low-latency search** (< 500ms).
4. **Read-heavy** (100:1 read:write) — support high read throughput.

**Below the line:** GDPR/user data protection, fault tolerance, secure payment transactions, CI/CD, backups.

## 3. Planning the Approach

For user-facing product questions: build the design sequentially, one functional requirement at a time; then use non-functional requirements to guide deep dives.

## 4. Core Entities

1. **Event** — date, description, type, performer/team; central information point per event.
2. **User** — the person interacting with the system.
3. **Performer** — the performing individual/group (name, description, links); "performer" is deliberately general (artist, team, company...).
4. **Venue** — physical location: address, capacity, and a **seat map** (e.g., JSON or related table defining sections/rows/seat numbers with coordinates for rendering).
5. **Ticket** — per-seat: event ID, seat details (section/row/number), price, status (available or sold). When an event is created, a ticket is generated for each seat from the venue's seat map. Client renders the interactive seat map from seat-map data + ticket statuses.
6. **Booking** — user ID, list of ticket IDs, total price, status (in-progress / confirmed). Could be folded into Ticket, but a separate Booking entity groups multi-ticket purchases under one order with shared payment status/total.

## 5. API Design

```http
GET /events/:eventId -> Event & Venue & Performer & Ticket[]
# tickets are used to render the seat map on the client
```

```http
GET /events/search?keyword={keyword}&start={start_date}&end={end_date}&pageSize={page_size}&page={page_number} -> Event[]
```

```http
POST /bookings/:eventId -> bookingId
{
  "ticketIds": string[],
  "paymentDetails": ...
}
```

It's fine to start simple and evolve — later this booking endpoint splits into **reserve** and **confirm purchase**. Communicate that plan.

## 6. High-Level Design

### 6.1 View events

Components:
- **Clients** — website/app; all requests route through an API Gateway.
- **API Gateway** — routes to microservices; handles cross-cutting concerns (auth, rate limiting, logging).
- **Event Service** — handles view requests; fetches event, venue, performer info.
- **Events DB** — tables for events, performers, venues.

Flow: client `GET /events/:eventId` → gateway → Event Service → queries Events DB → returns event + venue + performer (+ seat map) to client.

### 6.2 Search events

Start with a simple **Search Service** that filters the DB on the API request's parameters (keywords, artist, location, date, type). Known-bad performance-wise — improved in deep dives.

Flow: client `GET /events/search...` → load balancer → gateway (auth/rate limiting) → Search Service → query Events DB → results.

### 6.3 Book tickets

The core problem: **avoid two users paying for the same ticket**. Requires a database with **ACID transactions**; anything from MySQL to DynamoDB works, chosen: **PostgreSQL**. Also need proper isolation levels plus **row-level locking or Optimistic Concurrency Control (OCC)** to fully prevent double booking. *(Pattern: Dealing with Contention.)*

Additions:
- **Bookings + Tickets tables** in the Events DB (Ticket has a bookingId column linking to Booking).
- **Booking Service** — core booking logic; talks to Bookings/Tickets tables and to the payment processor; on payment confirmation sets ticket status to "sold".
- **Payment Processor (Stripe)** — external; notifies the Booking Service of transaction status.

Simple flow: user confirms on booking page → `POST /bookings` with ticket IDs → Booking Service runs a transaction: check availability → set tickets "booked" → create booking record → success/failure to client (failure if someone else booked meanwhile).

Notes:
- On event creation, a ticket row is created per seat.
- **Shared database across services is OK here** — "database per service" is dogma, not law. The data is tightly coupled (bookings need tickets need events), booking needs ACID, and splitting adds complexity for no benefit. Weigh tradeoffs; don't parrot rules.
- Known flaw: users can fill out payment details and *then* discover the ticket is gone — fixed in Deep Dive 1.

## 7. Deep Dives

Note: at mid-level, it's reasonable for the interviewer to drive most deep dives; senior/staff+ candidates are expected to proactively lead them.

### Deep Dive 1: Reserving tickets during checkout

Goal: lock a ticket while the user checks out (the familiar countdown timer); release on abandonment; mark sold on completion.

#### ❌ Bad: Long-running database locks (interactive transactions)
- `SELECT FOR UPDATE` holds a row lock for the whole checkout (~5 min).
- **Why bad:** DB locks are meant for near-instant transactions. Long-held locks strain resources, invite contention and deadlocks; `lock_timeout` fails ungracefully for user flows (errors, not queueing); crashes/network issues leave locks in uncertain states; scales poorly.

#### 👍 Good: Status field + expiration time + cron
- Add ticket status: `available | reserved | booked` plus a reservation timestamp. Reserve = set "reserved" + timestamp; purchase = "booked"; a **cron job** periodically flips expired reservations back to "available".
- **Challenges:** unlock delay between expiration and the cron run (tickets sit unavailable — bad for hot events); cron failures/delays disrupt booking.

#### ✅ Great: Implicit status (status + expiration, no cron dependency)
- Key insight: a ticket's effective status = "available" OR ("reserved" but reservation expired). Use **short transactions**:
  1. Begin transaction.
  2. Check ticket is AVAILABLE or (RESERVED and expired).
  3. Set RESERVED with expiration = now + 10 minutes.
  4. Commit.
- Guarantees single reservation AND lets users claim expired reservations immediately — no waiting on cron.
- **Challenges:** reads slightly slower (filter on two fields — mitigate with compound index / materialized views); table less legible (some "reserved" rows are actually expired — an optional sweep job cleans up, and crucially the system works fine even if the sweep is delayed).

#### ✅ Great (chosen): Distributed lock with TTL (Redis)
- Why Redis when Postgres is already consistent? We need a *temporary* reservation that auto-expires; Postgres has no row-level TTL (that's the cron approach), while Redis has built-in key expiration and is extremely fast under high concurrency.
- Flow:
  1. On seat selection, acquire a Redis lock keyed by ticket ID (value = user ID) with a TTL — `SET key value NX EX seconds` is atomic, so only one client wins.
  2. Purchase completes → DB ticket set to "booked"; app releases the lock.
  3. TTL expires (user abandoned) → Redis auto-releases; ticket available again.
- Ticket table keeps only two states (available/booked); reservation is entirely in Redis. For multi-seat bookings, acquire locks sequentially and roll back acquired locks on any failure; a Lua script can make multi-lock acquisition atomic if the keys hash to one node.
- **Challenges:**
  - *Read-path complexity:* seat map must show reserved seats. Either query Redis for locked ticket IDs per event (a Set `event:{eventId}:reserved` maintained alongside locks) or write-through a "reserved" status to the DB with Redis TTL as the expiration source of truth + periodic sweep. Call this out in the interview.
  - *Redis failure:* degraded UX only — the DB (OCC or row locking) still guarantees **no double booking**; users may just hit an error after entering payment details. Better than all tickets appearing unavailable (the failed-cron scenario).
  - *TTL expiring mid-payment:* if A's lock expires and B grabs it while A's payment completes, the DB transaction fails for one of them (OCC — only one write succeeds); auto-refund the loser via Stripe. Mitigate with a generous TTL and by **extending the lock when payment is initiated**.

**Full booking flow (final):**
1. User selects a seat → `POST /bookings` with the ticketId.
2. Gateway → Booking Service.
3. Booking Service acquires the Redis distributed lock (TTL 10 min).
4. Booking Service writes a booking row with status "in-progress".
5. Respond with bookingId; client routed to payment page. (If the user stops, the lock auto-releases after 10 min.)
6. User pays: Stripe.js tokenizes the card client-side (server never sees raw card numbers — standard PCI compliance); client sends the token + bookingId; server creates a Stripe PaymentIntent; Stripe processes and notifies via **webhook**.
7. Webhook handler reads bookingId from Stripe metadata and, in a DB transaction, sets the ticket "sold" and the booking "confirmed". Handler must be **idempotent** (Stripe retries webhooks) — use bookingId as an idempotency key and check current booking status before updating.
8. Ticket booked.

### Deep Dive 2: Scaling the view path to tens of millions of concurrent requests

*(Pattern: Scaling Reads — event pages get hammered when tickets go on sale.)*

#### ✅ Great: Caching + load balancing + horizontal scaling
- **Caching:** aggressively cache high-read, low-change data — event details, performer bios, static venue info. Keys like `eventId:eventObject`; Redis or Memcached; **read-through** strategy (miss → DB read → cache fill).
  - Invalidation/consistency: DB triggers notify the cache on changes (event dates, lineups); TTLs — long for static data (venue), short for frequently changing data (availability).
- **Load balancing:** Round Robin or Least Connections across all horizontally scaled services (mention it; no need to draw it).
- **Horizontal scaling:** the Event Service is stateless — add instances behind the load balancer.
- **Challenges:** cache/DB consistency on frequent updates (rare here); operational complexity of many instances (deployments, rollbacks).

### Deep Dive 3: Good UX for high-demand events (millions booking simultaneously)

Problem: seat maps go stale instantly; users rage-click already-taken seats.

> Interview insight: the best solution isn't always the more technically complex one. The senior→staff delta is often solving the *business* problem outside presumed constraints.

#### 👍 Good: SSE for real-time seat updates
- **Server-Sent Events** push seat status changes (booked/reserved) to clients in real time, no refresh. SSE is unidirectional server→client — a good fit.
- **Challenge:** for extreme events (the "Taylor Swift case") the map fills instantly anyway — disorienting and overwhelming.

#### ✅ Great: Virtual waiting queue for extremely popular events
- Admin-enabled queue placed **in front of the Booking Service**, before users even see the seat map:
  1. User requests the booking page → placed in a virtual queue; persistent connection (SSE or WebSocket — SSE is simpler since only server→client updates are needed) established. Queue backed by **Redis sorted set** (timestamp-ordered).
  2. Periodically (time- or tickets-booked-based) dequeue users from the front and notify them they can proceed.
  3. Mark admitted users in Redis (session ID in an `admitted:{eventId}` set with TTL); Booking Service checks this set before allowing reservations, rejecting non-admitted users.
- **Challenge:** long waits frustrate users — mitigate with real-time queue position and estimated wait time updates. *(Pattern: Real-time Updates.)*

### Deep Dive 4: Low-latency search

Naive `WHERE name LIKE '%Taylor%' OR description LIKE '%Taylor%'` forces full table scans.

#### 👍 Good: Indexing + SQL query optimization
- Index frequently searched columns (event name, date, performer name, venue location); use EXPLAIN, avoid SELECT *, use LIMIT, prefer UNION over OR.
- **Challenges:** standard indexes don't help partial string matches; indexes cost storage and slow writes; balancing index count vs performance is tricky.

#### ✅ Great: Full-text indexes in the DB
- Postgres `tsvector` + GIN indexes (MySQL has its own full-text indexing; neither uses Lucene). Much faster than LIKE scans for terms like "Taylor"/"Swift".
- **Challenges:** extra storage; can be slower than standard indexes to query; harder to maintain (special query handling).

#### ✅ Great: Dedicated search engine (Elasticsearch)
- Inverted indexes map each unique word to the documents containing it — extremely fast full-text search, complex queries, high traffic.
- Keep it in sync with Postgres via **Change Data Capture (CDC)** replicating inserts/updates/deletes to the ES index.
- Enables **fuzzy search** (typo tolerance: "Tayler Swift" → "Taylor Swift") — very hard with SQL alone.
- **Challenges:** sync complexity/consistency; extra infrastructure to run and pay for.

### Deep Dive 5: Speeding up repeated search queries / reducing search load

#### 👍 Good: Cache query results in Redis/Memcached
- Cache results of frequent searches; key built from query parameters; TTLs for freshness.
```json
{
  "key": "search:keyword=Taylor Swift&start=2021-01-01&end=2021-12-31",
  "value": ["event1", "event2", "event3"],
  "ttl": 86400
}
```
- **Challenges:** invalidation (stale results; extra-hard if caching fuzzy results — use TTLs + cache-tag invalidation triggers); misses spike load at peak times.

#### ✅ Great: Elasticsearch built-in caching + edge/CDN caching
- ES has shard-level filter caches plus a shard-level **request cache** for full responses (great for aggregations); supports adaptive caching of the most frequent queries.
- **CDN caching** (e.g., AWS CloudFront) puts results geographically near users — only valid if results are **not personalized** (same query → same results for everyone).
- **Challenges:** cache/real-data consistency (must invalidate when a new event is announced — hard because queries and results aren't directly connected); more infrastructure.

**Final design:** keep updating the diagram as deep dives evolve it. Visual clarity matters — your interviewer writes feedback later from memory and your whiteboard.

## 8. What Is Expected at Each Level?

### Mid-level (~80% breadth / 20% depth)
- High-level design meeting the functional requirements; many components can be surface-level abstractions. Interviewer probes basics (e.g., "what does the API Gateway do?") — nothing is taken for granted.
- Drive the early stages; it's fine if the interviewer drives later stages and probes the design.
- **Bar for Ticketmaster:** clearly defined API endpoints and data model; functional high-level design for at least viewing and booking; solve the no-double-booking problem with at least the **Good solution** (status field + timeout + cron). Additional depth is a bonus, not expected.

### Senior (~60% breadth / 40% depth)
- Go deep where you have hands-on experience; know a search-optimized store (Elasticsearch) for search, a **distributed lock** for reservations, and scaling strategies (sharding, replication — some interviewer hints are OK).
- Clearly articulate pros/cons and justify architectural choices; anticipate challenges proactively.
- **Bar:** speed through the high-level design to spend time on search optimization, no-double-booking (landing on a distributed lock or comparable), and popular-event handling.

### Staff+ (~40% breadth / 60% depth)
- Experience-backed design: know which technologies to use in practice, not just theory; breeze through basics (REST, normalization) to get to the interesting parts.
- Exceptional proactivity — interviewer intervenes only to focus, not steer; anticipate and pre-empt issues.
- **Bar:** dive deep into 2-3 key areas with innovative, optimal solutions; a strong signal is the interviewer coming away having learned something new.
