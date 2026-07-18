# Data Structures for Big Data

**Source:** https://www.hellointerview.com/learn/system-design/deep-dives/data-structures-for-big-data

Learn about data structures for processing and storing large amounts of data in System Design interviews.

> **Note: this page is premium-locked.** Only the introduction and the Bloom Filter intuition section are freely visible; everything below the "Locked sections" list was behind the paywall at fetch time and is NOT covered in this note.

---

## The Problem Space (free content)

Some systems must process massive amounts of data, and these problems disproportionately show up in system design interviews as a way to stress-test the depth of your knowledge. For them, simple scaling / adding machines may be insufficient — you need specialized data structures.

Why bother, when interviews rarely ask you to implement data structures? Because a specialized data structure often **changes the shape of the solution** and makes the surrounding system fundamentally different. Understanding those differences helps you design systems that are more efficient, scalable, and performant.

**The catch / pitfall:** these structures are uncommon for a reason. Employing a Bloom filter where a simple hash table would suffice is a **red flag** to an interviewer. Keep it simple.

The article's goals: (1) expand your arsenal of approaches, (2) highlight scenarios where these structures are commonly used, (3) point out common pitfalls and over-engineering temptations.

> **Author's advice for mid-level candidates:** don't start here if you're relatively new to system design — there's much higher ROI in mastering core concepts and key technologies first. A candidate who nails Count-Min Sketch but hasn't internalized caching, load balancing, and partitioning will struggle to design a performant architecture. Don't stress about these details.

---

## Bloom Filter (free content)

A **probabilistic data structure analogous to a set** (sets = insert elements, check membership).

- The standard set implementation is a hash table: O(1) insert, O(1) membership — but it needs memory for every element, infeasible for very large sets (imagine trillions of item IDs).
- Bloom filters compromise: **dramatically more memory-efficient** than hash tables, but with relaxed guarantees. They can tell you:
  - Whether an element is **likely** in the set (with configurable probability)
  - When an element is **definitely NOT** in the set

### Intuition: the village stamp analogy

A village of 1,000 people, each with a unique simple stamp. Everyone who attends a meeting stamps **one shared piece of paper**. Afterwards, to decide who gets thank-you treats:

- Look at each villager's stamp shape and check whether ink covers all of its grooves on the paper.
- If yes → they **might** have attended (could be an overlap of other people's stamps).
- If any part of their stamp is missing → they **definitely did not** attend (no treats).

Example: Albert's circle+plus present → probably attended. Bryan's circle+diagonal present → probably attended. Christina's vertical line present but her square is **not** → she definitely did not attend.

Instead of 1,000 pads of paper, one sufficed — that's the essence of a Bloom filter.

**Failure mode — saturation:** if the paper gets covered in enough ink (too many overlapping stamps, or one "solid square" stamp), you can no longer rule *anyone* out and must send treats to everyone. The approach degrades.

Lessons from the analogy:
1. Overlapping "stamps" let you make statements about set membership (specifically, who is *not* in the set).
2. You can sometimes prove an element is **not** in the set, but never prove it **is** — other elements' bits may overlap the one you're testing.
3. Stamps must be unique and limited (well-distributed hash functions, not too dense) — a solid-square stamp breaks the scheme.

(In real terms: a bit array + k hash functions; insert = set the k bits; query = check the k bits; all bits set → "maybe present," any bit unset → "definitely absent." False positives possible and rise as the filter saturates; false negatives impossible; no deletion in the basic form. The "How it Works" section formalizing this is paywalled.)

---

## Locked sections (premium-only, not captured)

The following sections were behind the "Purchase Premium to Keep Reading" wall:

- **Bloom Filter:** How it Works; Use-Cases and Pitfalls (Web Crawling; Cache Optimizations)
- **Count-Min Sketch:** Intuition; How It Works; Use-Cases and Pitfalls (Top K; Caching)
- **HyperLogLog:** Intuition; How it Works; Use-Cases and Pitfalls (Analytics and Metrics Systems; Security; Cache Sizing and Analysis)
- **Approximate Quantiles:** Intuition; How it Works (Fixed-Width Buckets; Exponential Buckets; Dynamic Histograms); Use-Cases and Pitfalls (Performance Monitoring; Service Level Objectives (SLOs); A/B Testing and Analytics; Load Balancing and Auto-scaling)
- **Conclusion**

### What the locked table of contents still tells you (for interview prep)

Even from the headings alone, the article maps four probabilistic structures to interview scenarios:

| Structure | Question it answers | Interview contexts (per the article's headings) |
|---|---|---|
| **Bloom filter** | "Have I seen this element?" (approximate set membership) | Web crawling (URL dedup), cache optimizations (avoid lookups for absent keys) |
| **Count-Min Sketch** | "Approximately how many times has this element appeared?" (frequency counting) | Top-K problems (e.g., YouTube Top K), caching |
| **HyperLogLog** | "Approximately how many *distinct* elements?" (cardinality estimation) | Analytics/metrics systems, security, cache sizing and analysis |
| **Approximate quantiles** | "What's the p95/p99?" over huge streams | Performance monitoring, SLOs, A/B testing and analytics, load balancing and auto-scaling |

The common theme: trade exactness for enormous memory savings on data too big for exact structures — and the overarching pitfall is reaching for them when a plain hash table/counter would do.
