# 21 - Online Auction (eBay-style)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/online-auction

- **Author:** Evan King (Hello Interview)
- **Difficulty:** Medium
- **Key patterns:** Dealing with Contention, Real-time Updates

> **⚠️ Premium-locked page:** Only the free preview of this breakdown was accessible. The section outline below reflects the article's own structure, but the detailed content of most sections (core entities, API design, high-level design walkthroughs, all deep dives, and level expectations) is behind the Hello Interview Premium paywall and is NOT reproduced here. See "Locked sections" at the bottom.

## Understanding the Problem

**What is an online auction?** An online auction service lets users list items for sale while others compete to purchase them by placing increasingly higher bids until the auction ends, with the highest bidder winning the item.

The breakdown follows the Hello Interview System Design (delivery) Framework step by step, with more detail than would be required or possible in a real interview, for teaching purposes.

## Functional Requirements

**Core Requirements**

1. Users should be able to post an item for auction with a starting price and end date.
2. Users should be able to bid on an item. Bids are accepted if they are higher than the current highest bid.
3. Users should be able to view an auction, including the current highest bid.

**Below the line (out of scope):**

- Users should be able to search for items.
- Users should be able to filter items by category.
- Users should be able to sort items by price.
- Users should be able to view the auction history of an item.

## Non-Functional Requirements

The article advises: before diving into the non-functional requirements, **ask your interviewer about the expected scale of the system**. Understanding scale requirements early informs key architectural decisions throughout the design.

*(The specific list of non-functional requirements is premium-locked. From the deep-dive section titles, the design targets strong consistency for bids, fault tolerance/durability, real-time display of the current highest bid, and scaling to ~10M concurrent auctions.)*

## The Set Up

### Defining the Core Entities
*(Content premium-locked.)*

### API or System Interface
*(Content premium-locked.)*

## High-Level Design

The high-level design addresses each functional requirement in turn (details premium-locked):

1. Users should be able to post an item for auction with a starting price and end date.
2. Users should be able to bid on an item, where bids are accepted if higher than the current highest bid.
3. Users should be able to view an auction, including the current highest bid.

## Potential Deep Dives

The breakdown covers four main deep dives plus additional suggestions (all detail premium-locked):

1. **How can we ensure strong consistency for bids?** — the core contention problem: concurrent bids on the same auction must be serialized/validated correctly.
2. **How can we ensure that the system is fault tolerant and durable?** — no accepted bid should ever be lost.
3. **How can we ensure that the system displays the current highest bid in real-time?** — real-time updates pattern (e.g., pushing bid updates to viewers).
4. **How can we ensure that the system scales to support 10M concurrent auctions?**
5. Some additional deep dives you might consider (list locked).

## What is Expected at Each Level?

The article includes sections for **Mid-level**, **Senior**, and **Staff** expectations, but the content is premium-locked.

---

## Locked sections (premium-only, not captured)

- Non-Functional Requirements (detailed list)
- Defining the Core Entities
- API or System Interface
- High-Level Design (all three requirement walkthroughs, diagrams)
- Deep Dive 1: Strong consistency for bids (tradeoffs and "great solution")
- Deep Dive 2: Fault tolerance and durability
- Deep Dive 3: Real-time current highest bid
- Deep Dive 4: Scaling to 10M concurrent auctions
- Additional deep dives
- What is Expected at Each Level (Mid-level / Senior / Staff)
- Premium video walkthrough and quiz
