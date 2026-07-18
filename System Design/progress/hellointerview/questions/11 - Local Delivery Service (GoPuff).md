# 11 - Local Delivery Service (GoPuff)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/gopuff
**Difficulty:** Easy · **Pattern:** Scaling Reads · **Author:** Stefan Mai (Hello Interview)

> **What is GoPuff?** GoPuff delivers convenience-store goods via rapid delivery from 500+ micro distribution centers (DCs). The emphasis of this problem is *aggregating item availability across nearby DCs* and *placing orders without double-booking inventory* — not catalog/search.

---

## 1. Functional Requirements

**Core:**
1. Customers can **query availability of items**, deliverable in **1 hour**, by location (effective availability = union of inventory across all nearby DCs).
2. Customers can **order multiple items** at the same time.

**Below the line (out of scope):**
- Payments/purchases
- Driver routing and deliveries
- Search functionality and catalog APIs
- Cancellations and returns

*Tip:* You can assert scoping ("I'll leave privacy out of scope") — interviewers will correct you if needed.

## 2. Non-Functional Requirements

**Core:**
1. Availability requests should be **fast (<100ms)** to support use cases like search.
2. Ordering must be **strongly consistent** — two customers must not be able to buy the same physical item.
3. Support **10k DCs** and **100k items** in the catalog.
4. Order volume ~ **10M orders/day**.

**Out of scope:** privacy/security, disaster recovery.

## 3. Core Entities

Key distinction: **Item vs Inventory** — like Class vs Instance in OOP. Customers care about Items (e.g., "Cheetos"); the system must track where physical units actually live.

- **Item** — a *type* of product (what customers see in a catalog).
- **Inventory** — a physical instance of an Item located at a specific DC. Availability for a user = sum of Inventory across nearby DCs.
- **DistributionCenter (DC)** — physical location storing inventory; determines what's available to a user.
- **Order** — a collection of Inventory ordered by a user (plus shipping/billing info).

*Tip:* Start from concrete physical/business entities (items, users) and work up to abstract ones (orders, carts) so you don't miss anything.

## 4. API Design

Keep it minimal — only two endpoints are needed (a common mistake is over-detailing APIs):

```
GET /availability?lat={lat}&long={long}&keyword={optional}&page=...   → paginated list of {item, quantityAvailable}
POST /orders  { lat, long, items: [{itemId, quantity}], shipping/billing info }  → order
```

Note: **location is passed to both APIs** — before an order is processed, the backend must confirm inventory is close enough to deliver within 1 hour.

## 5. High-Level Design

### 5.1 Query availability by location

Two steps, both must be fast (<100ms end-to-end):
1. **Find DCs close enough** to deliver in 1 hour. All inventory lives in a DC, so this prunes the search.
2. **Check inventory** of those serviceable DCs and return the union.

Components:
- **Availability Service** — handles user availability requests for a location.
- **Nearby Service** — internal API: takes lat/long, returns DCs deliverable within 1 hour. Initially a crude distance calc against a DC table (Euclidean or Haversine to account for Earth's curvature) with a distance threshold — not fully satisfying the 1-hour requirement yet (fixed in deep dive 1).
- **Inventory + Items tables** — Postgres; join Inventory with Item to get name/description plus quantity.

*Note:* Real e-commerce systems separate the Catalog from Inventory (different consumers/workloads) and add a search index like Elasticsearch — worth mentioning, but colocating keeps this design simple.

Flow: client → Availability Service → Nearby Service (get DC list) → query DB with those DC IDs → sum results → return.

### 5.2 Place orders (strong consistency — no double booking)

Latency matters less here, but we must never promise the same inventory to two users. Classic "double booking" problem → needs some form of locking: check inventory, record the order, and decrement inventory **atomically**.

#### Good solution: Two data stores + distributed lock
- **Approach:** Separate DBs for orders and inventory. On order: lock relevant inventory records, create order record, decrement inventory, release lock. Lets you pick the best store per use case (KV for inventory, relational for orders).
- **Challenges (nasty failure modes):**
  - Service crashes after creating the order but before decrementing inventory → later user can order promised inventory; need sweeps/reversals.
  - **Deadlock** with overlapping inventory: User1 holds lock A, User2 holds lock B, both want A+B — neither proceeds.

#### Great solution: Single Postgres transaction ✅
- **Approach:** Put orders AND inventory in the **same Postgres database** and use one ACID transaction with isolation level **SERIALIZABLE**. If two users order the same item concurrently, one transaction fails to commit.
- **Order flow:**
  1. User → Orders Service with items A, B, C.
  2. Single transaction to Postgres leader: check inventory for A/B/C > 0 → if any out of stock, fail → else mark inventory "ordered", insert rows in Orders + OrderItems → commit.
  3. On success, return order to user.
- **Challenges:** Couples scaling of inventory and orders; can't use the ideal store per workload. Also, if *any* item is unavailable, the whole order fails (return a meaningful error — still preferable to a partial order that makes no sense, e.g., device without its battery).
- **Key lesson:** When atomicity is required, colocate data in one ACID store; cross-store transactions add complexity you don't want to spend interview time on.

### 5.3 Putting it together
Three services — Availability, Orders, and shared Nearby Service (used by both). One Postgres database for inventory + orders, **partitioned by region**. Availability reads via **read replicas**; Orders writes to the **leader** with atomic transactions.

## 6. Deep Dives

### Deep Dive 1: Availability lookups should use real drive time + traffic

A DC across a river or border can be near in miles but far in drive time; traffic matters too. The functional requirement is *1 hour of drive time*.

- **Bad: Simple SQL distance.** Lat/long table + Euclidean/Haversine distance with a threshold. Ignores traffic, roads, and multiple DCs in one city.
- **Bad: Travel-time estimation service against ALL DCs.** DCs rarely change (they're buildings), so sync the DC table into service memory every ~5 min, then call an external travel-time service for every DC. Problem: far too many queries — most DCs are nowhere near deliverable range.
- **Great: Travel-time service against NEARBY candidates only. ✅** Sync DC table to memory periodically (~5 min). On request, prune candidates with a fixed radius (e.g., 60 miles — the most optimistic 1-hour drive), then send only those candidates to the external travel-time estimation service for the final estimate.

### Deep Dive 2: Make availability lookups fast and scalable

**Back-of-envelope (quantitative estimation flags the bottleneck and impresses interviewers):**
Assume each buyer views ~10 pages before buying, and only 5% of browsers buy:
```
10M orders/day ÷ 100k sec/day × 10 pages ÷ 0.05 conversion ≈ 20k queries/second
```
Classic **scaling reads** pattern: availability reads vastly outnumber inventory writes → aggressive caching with short TTLs + replicas.

- **Great: Query inventory through a cache. ✅** Add Redis: Availability Service checks cache per input set; on miss, query DB and write-through to cache. **Low TTL (~1 min)** keeps results fresh. *Challenge:* Orders Service must expire affected cache entries when it writes inventory.
- **Great: Postgres read replicas + partitioning. ✅** Since reads only touch nearby DCs, group DCs into a **region ID (first 3 digits of zipcode)** and partition inventory by region — queries hit mostly 1–2 partitions. Use **read replicas** for availability (small staleness is tolerable); orders stay on the leader for strong consistency. *Challenges:* sizing replicas to traffic; balancing partitions so none is overloaded.

Both "great" solutions combine in the final design.

## 7. What Is Expected at Each Level?

### Mid-Level
- ~**80% breadth / 20% depth**. Craft a high-level design meeting functional requirements; optimality is icing, not the focus.
- Interviewer probes basics (e.g., if you use DynamoDB, expect index questions). Nothing taken for granted.
- Mixture of driving and taking the backseat — you drive the early stages; interviewer may drive later probing.
- **Bar for GoPuff:** Clearly defined API endpoints and data model; built both routes (availability + orders). Using a "Bad" solution is OK if you can discuss it well — no expectation of jumping straight to great solutions.

### Senior
- ~**60% breadth / 40% depth**; technical detail in areas of hands-on experience.
- Certain aspects should jump out (read volume, trivial partitioning); articulate pros/cons and tradeoffs; proactively spot bottlenecks.
- **Bar for GoPuff:** Speed through the high-level design; spend time optimizing critical paths. Expected to have optimized solutions for both the atomic order transactions and availability scaling.

### Staff+
- ~**40% breadth / 60% depth**; "been there, done that" practical expertise; breeze through basics.
- High proactivity: anticipate issues and preempt them; deep dives into 2–3 key areas with unique insights on follow-ups of increasing difficulty; ideally the interviewer learns something.
