# 20 - Distributed Cache (like Redis)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/distributed-cache

> **⚠️ Premium-locked page.** Only the "Understanding the Problem" section (functional + non-functional requirements, with scoping commentary) is freely visible. The Planning/Core Entities/API sections, High-Level Design, all six Deep Dives, "Tying it all together," and the level expectations (Mid/Senior/Staff) are behind the Hello Interview Premium paywall. Locked section headings are listed below.

- **Difficulty:** Hard
- **Pattern tags:** Scaling Reads
- **Author:** Evan King

## Understanding the Problem

**What is a distributed cache?** A system that stores data as key-value pairs **in memory across multiple machines**. Unlike single-node caches limited by one machine's resources, distributed caches scale horizontally across many nodes to handle massive workloads. The cluster works together to **partition and replicate** data, ensuring high availability and fault tolerance when individual nodes fail.

This is an *infrastructure* design question (you're building Redis, not using it) — note there's no product/user-facing feature set.

### Functional Requirements

**Core requirements:**

1. Users (client services) should be able to **set, get, and delete** key-value pairs.
2. Users should be able to **configure expiration time (TTL)** for key-value pairs.
3. Data should be **evicted according to an LRU** (Least Recently Used) policy.

**Below the line (out of scope):**

- Configuring the cache size.

Scoping note from the breakdown: LRU was chosen here, but **ask your interviewer** what eviction policy they want — LFU, FIFO, and custom policies are all fair game.

### Non-Functional Requirements

Ask about scale first — it shapes everything. The interviewer's stated numbers for this problem: **up to 1TB of data** and a peak of **100k requests per second**.

**Core requirements:**

1. **Highly available**; eventual consistency is acceptable.
2. **Low latency**: < 10ms for get and set operations.
3. **Scalable** to 1TB of data and 100k RPS.

**Below the line (out of scope):**

- Durability (persistence across restarts).
- Strong consistency guarantees.
- Complex querying capabilities.
- Transaction support.

Scoping note from the breakdown: these are strong assumptions — confirm them with your interviewer. Some interviewers *do* care about durability, for example; just ask.

## Structure of the Full Breakdown (🔒 premium-locked sections)

- **The Set Up**
  - Planning the Approach 🔒
  - Defining the Core Entities 🔒
  - The API 🔒
- **High-Level Design** 🔒
  1. Users should be able to set, get, and delete key-value pairs
  2. Users should be able to configure the expiration time for key-value pairs
  3. Data should be evicted according to LRU policy
- **Potential Deep Dives** 🔒
  1. How do we ensure our cache is **highly available and fault tolerant**?
  2. How do we ensure our cache is **scalable**?
  3. How can we ensure an **even distribution of keys** across our nodes?
  4. What happens if you have a **hot key that is being read** from a lot?
  5. What happens if you have a **hot key that is being written** to a lot?
  6. How do we ensure our cache is **performant**?
- **Tying it all together** 🔒
- **What is Expected at Each Level?** 🔒 (Mid-level / Senior / Staff subsections exist but content is locked)

## Study Hints (inferred from question titles and standard theory, not the locked text)

- LRU + O(1) get/set on a single node is the classic **hash map + doubly linked list** structure; TTL is typically handled with lazy expiration on read plus periodic active sweeps (Redis's approach).
- "Even distribution of keys" is a strong pointer to **consistent hashing** (Hello Interview has a free core-concepts page on it) to minimize remapping when nodes join/leave.
- Availability/fault tolerance deep dive maps to **replication (leader-follower vs. peer) and failover** tradeoffs; eventual consistency being acceptable permits async replication.
- Hot **read** keys → replicate the key across nodes / add client-local caching; hot **write** keys → shard the key itself (e.g., append a random suffix and aggregate on read) or batch writes.
- Performance deep dive typically covers single-threaded event loops vs. multithreading, zero-copy networking, and connection pooling.
