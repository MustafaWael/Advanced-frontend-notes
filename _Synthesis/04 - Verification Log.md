---
tags: [synthesis, verification]
module: "_Synthesis"
priority: important
status: solid
verified_on: 2026-07-17
---

# Verification Log

Claims checked against primary/current sources during Phase A, plus everything Phase B still needs to verify. The scrapes are secondary sources — mechanisms trusted, specifics re-confirmed.

## Verified 2026-07-17

- **Modern hardware / latency (Numbers to Know).** Scrape claims sub-1ms intra-AZ, 1–2ms cross-AZ, 50–150ms cross-region, single machines up to multi-TB RAM. Confirmed against current cloud latency data: AWS cross-AZ is "single-digit ms" (measured ~0.27–2.4ms depending on region), Azure inter-zone target <2ms RTT, intra-AZ commonly sub-millisecond. The scrape's ranges are accurate and safe to carry into the vault. Sources: [Microsoft Learn — Azure network round-trip latency](https://learn.microsoft.com/en-us/azure/networking/azure-network-latency), [Bits and Cloud — AWS cross-AZ latencies](https://www.bitsand.cloud/posts/cross-az-latencies).
- **Redis licensing + Valkey — version-sensitive, flag in the deep-dive note.** Redis moved BSD → SSPL/RSAL (March 2024), which triggered the **Valkey** fork (BSD 3-Clause, a **Linux Foundation** project — not CNCF; backed by AWS, Google, Oracle, Snap; forked from Redis 7.2.4). Redis 8.0 (May 1, 2025) added **AGPLv3** (OSI-approved) as a tri-license option; antirez rejoined Nov 2024. The fork persists with its own roadmap; AWS/GCP managed "Redis-compatible" offerings are largely Valkey now. Phase B: the `30/11 Deep-Dive Technologies` note must say "Redis" in an interview may mean Valkey, add `verified_on`/`version_scope`. Sources: [Redis — AGPLv3 announcement](https://redis.io/blog/agplv3/), [InfoQ — Redis returns to open source](https://www.infoq.com/news/2025/05/redis-agpl-license/), [Percona — the Redis license has changed](https://www.percona.com/blog/the-redis-license-has-changed-what-you-need-to-know/).

## Flagged / not yet verified (Phase B must confirm before asserting)

- **All 🔒 premium-locked content** in [[02 - Concept Inventory]]: pattern solution details (contention approaches, saga/orchestration, scaling-reads tiers, scaling-writes, blob handling, long-task queues), Numbers-to-Know application/cost sections, LSM-tree internals, PostgreSQL/Flink/ZooKeeper deep sections, Bloom-filter math, vector-DB indexing, and concurrency correctness/coordination/scarcity solutions. The scrapes captured only headings — do **not** write these as facts; fill from primary sources (hellointerview.com, official docs) with `verified_on`.
- **Deep-dive technology specifics** (Kafka partition/consumer-group semantics, Cassandra tunable consistency levels, DynamoDB GSI/LSI limits, Elasticsearch refresh-interval defaults). Mechanisms are stable and correct in the scrape at the level captured; exact numbers/defaults should be re-checked against current docs when a note asserts them.
- **GreatFrontEnd free/premium split** (which of the 20 case studies are free) may have changed since the scrape's 2026-07-17 note; re-check before citing availability.
- **Consistent-hashing "1/N keys moved"** — correct in principle; confirm the exact virtual-node behavior described matches the current article if the note quotes specifics.

## Method notes for Phase B
- Treat every deep-dive tech note as version-sensitive → `verified_on` + `version_scope` are mandatory there.
- When a scrape section is 🔒, prefer stubbing the vault note (`status: not-started`, source-anchored) over inventing content.
- Re-run this log's "verified" checks if Phase B happens more than a few months out — hardware numbers and licensing move.
