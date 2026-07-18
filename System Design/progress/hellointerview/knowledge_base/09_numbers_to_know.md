# Numbers to Know

**Source:** [hellointerview.com — Numbers to Know](https://www.hellointerview.com/learn/system-design/core-concepts/numbers-to-know)

> **Note:** This page is **partially premium-locked**. The free portion covers the framing and the "Modern Hardware Limits" section. The sections applying the numbers to Caching, Databases, Application Servers, Message Queues, the Cheat Sheet, Common Mistakes (premature sharding, overestimating latency, over-engineering for write throughput), and costs are behind the Hello Interview Premium paywall — only their headings are visible. What follows is everything available for free.

## Why This Matters

Hardware evolves fast, so even recent textbooks quote numbers off by orders of magnitude. A giveaway of book knowledge without hands-on experience is doing scale calculations with numbers from 2015 (or even 2020) that dramatically underestimate modern systems — leading to significantly over-engineered designs. Decisions like when to shard, whether to cache aggressively, and how to handle large objects all depend on an accurate sense of today's hardware.

## Modern Hardware Limits (2026)

**Compute and memory:**
- AWS M6i.32xlarge (general workloads): **512 GiB memory, 128 vCPUs**
- Memory-optimized X1e.32xlarge: **4 TB RAM**
- U-24tb1.metal: **24 TB RAM**
- Implication: many applications that once required distributed systems can now run on a single machine.

**Storage:**
- AWS i3en.24xlarge: **60 TB local SSD**
- D3en.12xlarge: **336 TB HDD** for data-heavy workloads
- Object storage (S3): effectively unlimited — petabyte-scale deployments are standard
- Storage is largely no longer a primary constraint.

**Network:**
- Within a datacenter: **25 Gbps** common for standard instances; high-performance instances **50–100+ Gbps**
- Cross-AZ bandwidth within a region: limited only by instance network capacity
- Latency: **sub-1 ms within an AZ; 1–2 ms across AZs in a region; 50–150 ms cross-region**

These are a step change, not incremental. Textbook advice like "split databases at 100 GB" or "avoid large objects in memory" comes from outdated constraints.

## Premium-locked sections (headings only)

- Applying These Numbers in System Design Interviews: **Caching**, **Databases**, **Application Servers**, **Message Queues**
- **Cheat Sheet**
- Common Mistakes in Interviews: **Premature sharding**, **Overestimating latency**, **Over-engineering given a high write throughput**
- **What about costs?**
