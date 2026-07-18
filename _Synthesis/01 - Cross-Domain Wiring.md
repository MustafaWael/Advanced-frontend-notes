---
tags: [synthesis, system-design, low-level-design, wiring]
module: "_Synthesis"
priority: must-know
status: solid
verified_on: 2026-07-17
---

# Cross-Domain Wiring

The bridges between LLD, backend system design, and frontend concerns. Each entry states the **shared mechanism** (why they're the same idea) and the **divergence** (why you can't blindly copy one side onto the other). This is the artifact Phase B leans on hardest — it's what makes "design a system" and "design a class" and "design a widget" feel like one skill instead of three.

Format per bridge: *LLD side ↔ BE-SD side ↔ FE side*, then **Shared mechanism**, **Divergence**, **Vault anchor**.

---

## Bridge 1 — Contention is one problem at three scales

**LLD:** two threads increment the same counter; two customers grab the last inventory item; two cars race for one parking spot. Fixed with in-process primitives: a mutex/lock around the critical section, or an atomic compare-and-swap, or optimistic concurrency (read version, write only if unchanged).
**BE-SD:** the "Dealing with Contention" pattern — two users buy the last concert seat across different servers. No shared memory, so you reach for distributed locks (Redis/ZooKeeper), database row locks / `SELECT ... FOR UPDATE` (pessimistic), optimistic concurrency control with a version column, or idempotency keys so a retried request doesn't double-book.
**FE:** the client version of "two writes race" — a user double-clicks Submit, or a slow response for query "re" lands *after* the fast response for "reac" and overwrites fresher UI. Fixed with request dedup / in-flight guards, `AbortController` cancellation, and last-write-wins keyed on request sequence.

- **Shared mechanism:** concurrent actors mutate shared state with no guaranteed ordering; correctness requires either serializing access (locks) or detecting-and-retrying conflicts (optimistic). *Optimistic locking (LLD/BE) and optimistic UI (FE) are literally the same bet:* assume no conflict, proceed, reconcile if wrong.
- **Divergence:** the *unit of shared state* and the *cost of coordination* change with scale. In-process: shared RAM, a lock is nanoseconds. Distributed: no shared RAM, a distributed lock is a network round-trip and a new failure mode (lock holder dies → need leases/TTLs → ZooKeeper). Frontend: the "shared state" is the server plus the DOM, you can't lock either, so you can only cancel, dedup, and reconcile — never truly mutually exclude.
- **Vault anchor:** [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]], [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]], [[08 - Async JavaScript/06 - AbortController|AbortController]]. Phase B: this bridge is the spine of both the LLD concurrency notes and the BE "Contention" note, and each should link back to these three.

---

## Bridge 2 — Caching decisions mirror across the network boundary

**BE-SD:** cache-aside is the default (app checks cache, miss → DB → populate). Layers: in-process → Redis/Valkey → CDN. Problems: invalidation, staleness, stampede (single-flight/request coalescing), hot keys (replicate). Eviction: LRU default + TTL.
**FE:** the browser and app make the *mirror image* of every one of those decisions, on the client side of the black box. HTTP cache + `ETag`/`Cache-Control` is read-through caching you configure via headers. A normalized client store (React Query / RTK Query / Apollo) is cache-aside with the component as the app. Request deduplication is client-side single-flight against stampede. Stale-while-revalidate is "short TTL + serve stale, refresh in background."

- **Shared mechanism:** identical tradeoff — trade freshness for latency and load reduction, then manage the staleness window. Cache-aside, TTL, eviction, single-flight, and "invalidate on write" all appear on both sides with the same names.
- **Divergence:** the backend controls its cache and can invalidate authoritatively; the frontend cache is *downstream of a black box it doesn't own*, so invalidation is cooperative (the server must send cache headers or the client must poll/subscribe). The frontend also caches for offline and for perceived performance (optimistic UI), motivations the backend cache doesn't have.
- **Vault anchor:** [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]], [[28 - Frameworks and Application Architecture/06 - Server State|Server State]], [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]. Phase B: the BE Caching note's "Client-Side Caching" section should link straight here.

---

## Bridge 3 — The real-time transport table is identical on both sides

**BE-SD:** "Real-time Updates" pattern, Hop 1 = client↔server protocol. The decision table: long-polling (simple, works everywhere) → SSE (unidirectional server push, plain HTTP, auto-reconnect) → WebSockets (bidirectional, stateful, can't sit behind a naive load balancer). Common mistake: reaching for WebSockets when SSE/polling suffices.
**FE:** the exact same table, chosen from the client's perspective for a live UI (notifications, live comments, collaborative cursors). Plus the client-only concerns: reconnection/backoff, message ordering, and updating a normalized store as events arrive.

- **Shared mechanism:** one shared decision tree keyed on *directionality* and *frequency of client→server messages*. SSE and WebSockets are both stateful connections with the same scaling consequence (connection persistence, thundering-herd on server death).
- **Divergence:** the backend cares about Hop 2 (how the server *sources* the pushed data — pub/sub, Kafka fan-out, polling a DB) and about holding millions of connections. The frontend stops at Hop 1 and adds UI concerns the backend never sees: reconnection UX, optimistic vs confirmed message states, out-of-order rendering.
- **Vault anchor:** [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets SSE and Polling]]. Phase B: the BE "Real-time Updates" note and this vault note are two views of one table — cross-link and let the vault note own the client concerns, the new note own Hop 2.

---

## Bridge 4 — Eventual consistency is the same thing as a stale-UI window

**BE-SD:** CAP forces a choice under partition; most read-heavy systems pick availability + eventual consistency (feeds, likes, metrics). There's a window where replicas disagree.
**FE:** optimistic UI *deliberately creates* a local eventual-consistency window — you show the like as done before the server confirms, then reconcile (or roll back on failure). The client is, briefly, an inconsistent replica of the server.
**LLD:** optimistic concurrency is the single-process ancestor: act on a possibly-stale read, validate at commit.

- **Shared mechanism:** accept a bounded window of disagreement in exchange for latency/availability, then define the reconciliation (last-write-wins, version check, rollback).
- **Divergence:** backend eventual consistency is between *machines the operator owns* and can be tuned (quorum, read-repair). Frontend optimistic consistency is between *the user's screen and the truth* — the reconciliation is a UX event (toast, rollback animation), and getting it wrong shows the user a lie, not just a stale row.
- **Vault anchor:** [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]], [[28 - Frameworks and Application Architecture/06 - Server State|Server State]]. Phase B: BE CAP note links here to make the abstract consistency spectrum concrete for a frontend reader.

---

## Bridge 5 — Cursor vs offset pagination is one API contract, two consumers

**BE-SD:** offset pagination is simple but drifts (duplicates/skips as data shifts); cursor pagination is stable under inserts but can't jump to page N. This is an *API design* decision.
**FE:** the infinite-scroll feed consumes exactly that contract. Cursor pagination is what makes an infinite feed correct while new items arrive at the top; offset would double-show or skip items mid-scroll.

- **Shared mechanism:** identical correctness argument — cursors are stable against concurrent inserts because they name a record, not a position.
- **Divergence:** the backend weighs cursor-vs-offset against query cost and index design; the frontend weighs it against scroll UX, scroll restoration, and virtualization. The contract is shared; the reasons to prefer cursor differ (index stability vs jitter-free scrolling).
- **Vault anchor:** [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Designing an Infinite Scroll Feed]]. Phase B: the new BE "API Design" note owns the general rule; the vault feed note already applies it — cross-link so the "why" and the "use" sit together.

---

## Bridge 6 — Design patterns and SOLID recur as frontend architecture

**LLD:** the ~5 patterns that actually matter — Factory (create the right object without the caller deciding), Strategy (swap an algorithm behind an interface), Observer (subscribers react to state changes), Builder (assemble a complex object stepwise), State (behavior varies by internal mode). Plus SOLID/SoC as the reason they arise.
**FE:** these are already how good frontend code is built. Strategy = pluggable sort/filter/validation functions passed as props. Observer = the entire reactive model (subscriptions, `useSyncExternalStore`, event emitters). Factory = component/hook factories, render-prop selectors. State pattern = explicit state machines (XState) for complex widgets. SRP/SoC = the container/presentational and hooks-extraction discipline.

- **Shared mechanism:** patterns are *names for structures good design principles produce* — not things you bolt on. The golden rule ("only use a pattern when the problem calls for it; forcing one signals over-engineering") applies identically in a React codebase.
- **Divergence:** classic OOP patterns assume classes and inheritance; modern JS/React reaches the same ends with closures, composition, and functions. Observer in Java is a class hierarchy; in React it's a subscription hook. Naming the pattern matters more in some interview regions than others (US LLD rounds grade design quality, not pattern-naming).
- **Vault anchor:** [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]] (Observer), [[21 - React Internals and Patterns/11 - Custom Hook Design Patterns|Custom Hook Design Patterns]], [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]], [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]. Phase B: the LLD patterns note should carry a "these in your frontend" callout pointing at each of these.

---

## Bridge 7 — Two "framework" moments: RADIO ↔ LLD delivery framework

**FE-SD:** RADIO — Requirements → Architecture → Data model → Interface → Optimizations, with time budgets, "server as black box," verbalize every tradeoff.
**LLD:** the delivery framework — Requirements → Entities/Relationships → Class Design (state + behavior derived from requirements) → Implementation → Extensibility.
**BE-SD:** the delivery framework — Requirements (functional + non-functional) → Core Entities → API → High-level Design → Deep Dives.

- **Shared mechanism:** all three are the *same senior meta-skill*: refuse to design before requirements are explicit, then move outside-in (contract before internals), then reserve the back half for tradeoff-driven depth. "Requirements first, traceable decisions, tradeoffs out loud" is domain-independent.
- **Divergence:** what the middle steps produce differs — a component/network API vs a class diagram vs a service topology. The "deep dive" axis differs too: FE optimizes perf/a11y/i18n; LLD optimizes extensibility/patterns; BE optimizes scale/consistency/availability.
- **Vault anchor:** [[29 - Frontend System Design/01 - The Frontend System Design Framework|The Frontend System Design Framework]], [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]. Phase B: open both new modules by explicitly contrasting their framework with RADIO so the reader transfers the skill instead of re-learning it.

---

## Bridge 8 — Indexing and data structures underneath the abstractions

**BE-SD:** B-Tree indexes (range-friendly, read-optimized) vs LSM trees (write-optimized, used by Cassandra); Bloom filters (probabilistic membership, skip disk reads); the cardinality problem in time-series DBs.
**FE:** the frontend rarely touches these directly, but they explain the *shape of the API it's given* — why a search endpoint is eventually consistent (Elasticsearch inverted index refresh interval), why "search-as-you-type" tolerates staleness, why some queries are cheap (indexed) and others are paginated-only (no index to jump to page N).
**LLD/CS:** these are just data structures with tradeoffs — the same `O()` reasoning as choosing a Map vs array on the client ([[07 - Arrays and Iteration]] territory).

- **Shared mechanism:** every storage/index choice trades read cost against write cost against space — the same tradeoff triangle a frontend engineer makes choosing a normalized map vs a denormalized list in a store.
- **Divergence:** scale and durability. The backend's choice survives crashes and spans disks; the client's "index" is an in-memory object rebuilt each session.
- **Vault anchor:** [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]] (normalization), [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization]]. Phase B: keep this bridge light in the frontend notes — it's context, not a frontend skill.

---

## The one-sentence summary of all eight bridges

Concurrency/contention, caching, real-time transport, consistency, pagination, design patterns, the requirements-first framework, and the read/write/space tradeoff are each **a single idea instantiated at three scales** (in-process, cross-machine, across-the-network-boundary); a mid/senior engineer who has seen one instance should recognize the other two and can name what changes between them.
