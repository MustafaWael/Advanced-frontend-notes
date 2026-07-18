---
tags: [system-design, backend, interview]
module: "30 - Backend System Design"
priority: important
status: not-started
aliases: [numbers to know, back-of-envelope, latency numbers]
verified_on: 2026-07-17
version_scope: "2026 cloud hardware (AWS/Azure instance classes, current latency figures)"
---

# Numbers to Know

## Maturity Target

- Priority: #important
- Study time: 20 minutes
- Interview signal: Do back-of-envelope math with *current* hardware numbers and use them to reject over-engineering (especially premature sharding).
- Production signal: Your capacity intuition matches 2026 reality, not a 2015 textbook.
- Dependencies: [[30 - Backend System Design/06 - Sharding and Consistent Hashing|Sharding and Consistent Hashing]]

## Source Anchors

- [HelloInterview — Numbers to Know](https://www.hellointerview.com/learn/system-design/core-concepts/numbers-to-know)
- [Azure network round-trip latency](https://learn.microsoft.com/en-us/azure/networking/azure-network-latency)
- [AWS EC2 instance types (RAM/SSD/network ceilings)](https://aws.amazon.com/ec2/instance-types/)

## 1. Concept

Simple version: rough numbers decide whether you need distributed machinery or a single box. Using stale numbers leads to over-engineered designs.

**Modern hardware (2026), verified:**

- **Memory:** general instances ~512 GiB / 128 vCPU; memory-optimized up to ~4 TB; extreme up to ~24 TB RAM. *Implication: workloads that once "required" distributed systems fit on one machine.*
- **Storage:** ~60 TB local SSD per instance; hundreds of TB HDD; object storage (S3) effectively unlimited. Storage is rarely the primary constraint now.
- **Network:** ~25 Gbps standard, 50–100+ Gbps high-perf within a datacenter.
- **Latency:** **sub-1ms within an AZ, 1–2ms cross-AZ in a region, 50–150ms cross-region.** (Ranges confirmed against current AWS EC2 and Azure latency figures — see Source Anchors.)

**Useful order-of-magnitude reads (know the hierarchy, not just the digits):** a local RAM read is ~100 **ns**; an SSD random read is ~100 **µs** (~0.1 ms); a network round trip to an in-memory store like Redis in the same AZ is ~0.5–1 **ms** (dominated by the network, not the memory); a disk-backed DB query over the network is typically a few ms to tens of ms; a cross-continent round trip is ~100 ms. The case for caching is that a single ~0.5–1 ms hop to an in-memory cache replaces a multi-ms DB query *and* sheds load from the primary — often a 10–50× latency win depending on the query, plus the throughput relief ([[30 - Backend System Design/05 - Caching|Caching]]). (Watch the units: "Redis is ~1 ms" is the *network hop*, not a memory read — memory itself is ~10,000× faster than that.)

> [!warning] The top mistake these numbers guard against is **premature sharding / over-engineering for write throughput**. "Split the DB at 100 GB" is 2015 advice; a modern single node holds multi-TB in RAM. Do the arithmetic before proposing distributed complexity — often "one big box + read replicas + a cache" is the correct answer.

## 2. Why It Matters

Back-of-envelope math is a graded signal, and using outdated numbers doesn't just cost accuracy — it drives you to the *wrong architecture* (sharding a dataset that fits on one node, adding a queue for a write rate a single Postgres handles). Current numbers keep designs proportionate.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

(This note has no client-side "bug" to trace — the template slot is used here for a *design critique*, since the numbers' payoff is rejecting over-engineering.) The "bug" is an over-engineered design. Prompt: "design a bookmarking app, ~5M users, ~50 bookmarks each."

Over-engineered answer: shard the database across a cluster, add Kafka, consistent hashing, the works.

Trace of why it's wrong: 5M × 50 = 250M rows of small records — a few tens of GB. That fits comfortably in RAM on a single modern instance, let alone on disk with an index. The distributed machinery adds cross-shard cost, operational burden, and consistency headaches to solve a problem that doesn't exist yet.

Fix: one relational primary + a read replica + a cache for hot reads. State the arithmetic out loud ("250M small rows ≈ tens of GB, single-node territory") so the interviewer sees you *chose* simplicity from numbers.

Tradeoff: you must still name the growth path — "if this 100×'s, here's where I'd introduce sharding by userId" — so simplicity reads as judgment, not naivety.

## 4. Interview Answer

Short answer:

> I anchor capacity math on current hardware: single instances now reach hundreds of GB to multiple TB of RAM and tens of TB of SSD, intra-AZ latency is sub-millisecond, cross-region is 50–150ms. That usually means a dataset people assume needs sharding actually fits on one node with replicas and a cache, so I do the arithmetic before adding distributed complexity.

Deeper answer:

> The classic failure is applying textbook thresholds from a decade ago — "shard at 100 GB," "avoid large in-memory objects" — which push you to over-engineer. Grounding the estimate in 2026 numbers flips the default: prove you need to shard from the data size and write rate, don't assume it. And the memory-vs-disk gap (~50×) is the quantitative justification for caching, so these numbers also tell you *when caching actually pays* rather than caching reflexively.

## 5. Practice

1. <details><summary>~10M users, a 2 KB profile each — does this need sharding?</summary>10M × 2 KB ≈ 20 GB — trivially single-node, fits in RAM. No sharding; a single primary with a read replica and a cache is plenty. Naming the ~20 GB figure is the point.</details>
2. <details><summary>Why does using 2015-era numbers hurt your design, not just your trivia?</summary>Underestimating a single machine's capacity makes distributed solutions look necessary when they aren't, so you propose sharding/queues that add real cost and complexity. Wrong numbers → wrong architecture, which grades worse than admitting you'd measure.</details>
3. <details><summary>What quantitative fact justifies caching?</summary>A cache hit is one ~0.5–1 ms network hop to an in-memory store; the disk-backed DB query it replaces is typically several ms to tens of ms *and* consumes primary-DB capacity. So the win is both latency (often 10–50×, query-dependent) and throughput relief. Be precise about units: the ~1 ms is the *network round trip* to Redis, not a memory read (RAM itself is ~100 ns). If the DB query were already sub-millisecond and cheap, a cache wouldn't pay.</details>

## Related Notes

- [[30 - Backend System Design/06 - Sharding and Consistent Hashing|Sharding and Consistent Hashing]]
- [[30 - Backend System Design/05 - Caching|Caching]]
- [[30 - Backend System Design/01 - The Delivery Framework|The Delivery Framework]]
