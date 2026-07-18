# 05 - Scaling Writes

**Source:** https://www.hellointerview.com/learn/system-design/patterns/scaling-writes

> **⚠️ Premium-locked page.** Only the introduction, "The Challenge" section, the solution overview, and the section outline were freely visible. All detailed sections (marked 🔒 below) require Hello Interview Premium and are not reproduced here.

---

## What the Pattern Is

**Scaling Writes** addresses the challenge of handling high-volume write operations when a single database or single server becomes the bottleneck. As an application grows from hundreds to millions of writes per second, individual components hit hard limits on **disk I/O, CPU, and network bandwidth** — and interviewers love to probe exactly these bottlenecks.

## The Problem It Solves (The Challenge)

- Many system design problems start with modest scaling requirements before the interviewer asks: **"how does it scale?"**
- The read side is usually the familiar part (read replicas, caching, etc.) — the **write side is often a much bigger challenge**.
- **Bursty, high-throughput writes with lots of contention** are hard to build around. There are many design choices that can either handle them well or make things worse.
- Interviewers probe write bottlenecks to see how you'd react to runaway success of a product ("what if traffic 100x's?").

## The Solution (Overview — free content)

Key framing from the article: write scaling isn't (only) about throwing more hardware at the problem — there are **architectural choices** that improve the system's ability to scale. The article presents **four strategies** that, combined, let you scale writes beyond what a single unoptimized database or server can handle:

1. **Vertical Scaling and Database Choices** — first, scale as far as possible while staying in a single-server, single-database architecture (bigger machine, write-optimized database choice) before adding distributed complexity.
2. **Sharding and Partitioning** — split write load across machines:
   - Horizontal sharding (split rows/keys across shards)
   - Vertical partitioning (split by column/domain)
3. **Handling Bursts with Queues and Load Shedding**
   - Write queues to absorb/buffer bursts
   - Load shedding strategies when the system can't keep up
4. **Batching and Hierarchical Aggregation**
   - Batching writes to reduce per-write overhead
   - Hierarchical aggregation (aggregate at multiple layers before hitting the database)

The article's recommended order: exhaust single-node optimizations first, then distribute.

## Article Structure (🔒 = premium-locked detail)

- The Challenge *(free — summarized above)*
- The Solution *(overview free; details locked)*
  - 🔒 Vertical Scaling and Write Optimization
    - 🔒 Vertical Scaling
    - 🔒 Database Choices
  - 🔒 Sharding and Partitioning
    - 🔒 Horizontal Sharding
    - 🔒 Vertical Partitioning
  - 🔒 Handling Bursts with Queues and Load Shedding
    - 🔒 Write Queues for Burst Handling
    - 🔒 Load Shedding Strategies
  - 🔒 Batching and Hierarchical Aggregation
    - 🔒 Batching
    - 🔒 Hierarchical Aggregation
- 🔒 When to Use in Interviews
  - 🔒 Common Interview Scenarios
  - 🔒 When NOT to Use in Interviews
- 🔒 Common Deep Dives
  - 🔒 "How do you handle resharding when you need to add more shards?"
  - 🔒 "What happens when you have a hot key that's too popular for even a single shard?"
    - 🔒 Split All Keys
    - 🔒 Split Hot Keys Dynamically
- 🔒 Conclusion

## Interview Problems Where This Pattern Applies

The article links this pattern to these Hello Interview problem breakdowns (each has a "scaling writes" section):

- **YouTube Top K** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/top-k#scaling-writes
- **Strava** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/strava#scaling-writes
- **Rate Limiter** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-rate-limiter#scaling-writes
- **Ad Click Aggregator** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/ad-click-aggregator#scaling-writes
- **FB Post Search** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-post-search#scaling-writes
- **Metrics Monitoring** — https://www.hellointerview.com/learn/system-design/problem-breakdowns/metrics-monitoring#scaling-writes

Pattern signal: high-ingest, event/metric/click-stream style problems where write throughput dominates.

## Related Free Reading (linked from the article)

- Sharding core concept (free): https://www.hellointerview.com/learn/system-design/core-concepts/sharding

## Locked Sections — Study Gaps to Fill Elsewhere

The premium content covers (per the outline): specifics of vertical scaling limits and write-optimized DB choices (e.g., LSM-tree stores like Cassandra), how to shard and pick partition keys, queue-based burst absorption vs. load shedding tradeoffs, batching/hierarchical aggregation mechanics, resharding approaches, and hot-key/hot-shard mitigation (split all keys vs. dynamically splitting hot keys). These details are **not** captured here because they are premium-only.
