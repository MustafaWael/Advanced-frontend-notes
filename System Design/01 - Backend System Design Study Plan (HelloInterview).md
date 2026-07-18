# Backend System Design — Comprehensive Study Plan

> Primary source: [HelloInterview — System Design in a Hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction)
> Learned notes: `progress/hellointerview/`
> Complements: `00 - System Design Study Plan.md` (frontend, GreatFrontEnd)
> Target: mid-level interviews. Created 2026-07-17.

## Goal

Take an ambiguous product/infrastructure prompt (e.g. "Design Bitly", "Design a rate limiter") and deliver a complete design in 35–45 min: requirements → core entities → API → high-level design → deep dives, covering the basics solidly (mid-level bar) with clear tradeoff reasoning.

## How you're assessed (keep in view every session)

Four rubric themes: Problem Navigation, Solution Design, Technical Excellence, Communication & Collaboration. Mid-level bar = complete working design covering the basics well; depth is a bonus. See `progress/hellointerview/00_introduction.md`.

## Phase 1 — Framework first (Week 1)

1. Read `progress/hellointerview/00_introduction.md` and `01_how_to_prepare.md` — understand interview types and the prep loop.
2. Master `02_delivery_framework.md` — the backbone. Memorize the step order and time budgets (requirements → core entities → API → data flow → high-level design → deep dives).
3. Skim `03_core_concepts.md` end to end once; don't memorize yet.

**Checkpoint:** recite the delivery framework and its timings from memory; walk a trivial prompt (URL shortener) through all steps out loud.

## Phase 2 — Core concepts (Weeks 1–2)

Work through `progress/hellointerview/knowledge_base/` in order:

1. `01_networking_essentials.md` — protocols, load balancing, real-time options.
2. `02_api_design.md` — REST conventions, pagination, versioning.
3. `03_data_modeling.md` — entities, SQL vs NoSQL reasoning.
4. `04_caching.md` — strategies, eviction, invalidation.
5. `05_sharding.md` + `06_consistent_hashing.md` — partitioning.
6. `07_cap_theorem.md` — consistency vs availability; PACELC.
7. `08_database_indexing.md` — B-Trees (free portion; premium covers LSM/inverted/geo).
8. `09_numbers_to_know.md` — modern hardware limits for estimation.

**Checkpoint:** for each concept, state one problem where it's the key decision and the tradeoff you'd narrate.

## Phase 3 — Key technologies & patterns (Week 2–3)

1. Study `04_key_technologies.md` — know when to reach for Redis, Kafka, Postgres, DynamoDB/Cassandra, Elasticsearch, API gateways, blob storage, etc. You don't need internals at mid-level; you need "which tool, why, what breaks."
2. Go deeper with `deep_dives/` — fully free: Redis, Elasticsearch, Kafka, API Gateway, Cassandra, DynamoDB, Proximity Search, Time Series DBs. Partially locked (intro only): PostgreSQL, Flink, ZooKeeper, Big Data structures, Vector DBs.
3. Study `05_common_patterns.md` — the 8 reusable patterns (real-time updates, contention, multi-step processes, scaling reads/writes, large blobs, long-running tasks). These map directly onto deep-dive questions. Per-pattern pages in `patterns/` are premium-locked past intros; use them as indexes only.

**Checkpoint:** given any pattern name, sketch its standard architecture in under 3 minutes.

## Phase 4 — Problem breakdowns (Weeks 3–5)

Use `06_question_breakdowns.md` as the catalog. One problem per session: 35–45 min solo attempt on Excalidraw first, then read the breakdown and diff against your attempt. Suggested mid-level order:

1. Bitly (easy, canonical warm-up)
2. Rate Limiter (infra, algorithms + Redis)
3. Ticketmaster (contention)
4. FB News Feed (fan-out, scaling reads)
5. WhatsApp (real-time)
6. Dropbox (large blobs)
7. LeetCode (long-running tasks)
8. Web Crawler (multi-step processes, queues)
9. YouTube (blobs + streaming)
10. Uber (proximity, geo)

**Checkpoint:** solo designs match breakdowns on requirements, API, and high-level architecture without hints.

## Phase 5 — Mocks & gaps (Week 6)

- 3–4 full mocks (peer or AI), unseen prompts, strict timer.
- After each: score yourself against the 4 rubric themes; revisit the weakest knowledge_base note.
- Re-drill numbers from `09_numbers_to_know.md` the day before the interview.

## If really short on time

Per HelloInterview: `02_delivery_framework.md` first, skim `04_key_technologies.md`, then whatever remains on `03_core_concepts.md`.

## Progress tracking

- [ ] Phase 1 — framework
- [ ] Phase 2 — core concepts
- [ ] Phase 3 — technologies & patterns
- [ ] Phase 4 — 10 problem breakdowns
- [ ] Phase 5 — mocks

Add new learned sources as sibling folders under `progress/` (current: `greatfrontend/`, `hellointerview/`).
