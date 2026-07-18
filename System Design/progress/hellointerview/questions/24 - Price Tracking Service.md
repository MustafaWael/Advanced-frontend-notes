# 24 - Price Tracking Service (CamelCamelCamel)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/camelcamelcamel

- **Author:** Evan King (Hello Interview)
- **Difficulty:** Medium

> **⚠️ Premium-locked page:** Only the free preview of this breakdown was accessible. The section outline below reflects the article's own structure, but the detailed content of most sections (planning, core entities, API, data flow, high-level design, all deep dives, final design, and level expectations) is behind the Hello Interview Premium paywall and is NOT reproduced here. See "Locked sections" at the bottom.

## Understanding the Problem

**What is CamelCamelCamel?** CamelCamelCamel is a price tracking service that monitors Amazon product prices over time and alerts users when prices drop below their specified thresholds. It also has a popular Chrome extension with 1 million active users that displays price history directly on Amazon product pages, allowing for one-click subscription to price drop notifications without needing to leave the Amazon product page.

## Functional Requirements

**Core Requirements**

1. Users should be able to view price history for Amazon products (via website or Chrome extension).
2. Users should be able to subscribe to price drop notifications with thresholds (via website or Chrome extension).

**Below the line (out of scope):**

- Search and discover products on the platform.
- Price comparison across multiple retailers.
- Product reviews and ratings integration.

## Non-Functional Requirements

The scale and performance requirements are driven by Amazon's massive product catalog and the need for timely price notifications.

**Core Requirements**

1. The system should prioritize availability over consistency (eventual consistency acceptable).
2. The system should handle 500 million Amazon products at scale.
3. The system should provide price history queries with < 500ms latency.
4. The system should deliver price drop notifications within 1 hour of a price change.

**Below the line (out of scope):**

- Strong consistency for price data.
- Real-time price updates (sub-minute).

Framing from the article: we're building a system that must be **"polite" to Amazon** while providing valuable price tracking to millions of users. This creates interesting technical challenges around data collection, storage efficiency, and notification delivery addressed in the deep dives.

## The Set Up

### Planning the Approach
*(Content premium-locked.)*

### Defining the Core Entities
*(Content premium-locked.)*

### The API
*(Content premium-locked.)*

### Data Flow
*(Content premium-locked.)*

## High-Level Design

The high-level design addresses each functional requirement in turn (details premium-locked):

1. Users should be able to view price history for Amazon products (via website or Chrome extension).
2. Users should be able to subscribe to price drop notifications with thresholds (via website or Chrome extension).

## Potential Deep Dives

Four deep dives (all detail premium-locked):

1. **How do we efficiently discover and track 500 million Amazon products?** — data collection at scale while being polite to Amazon (crawling/extension-sourced data).
2. **How do we handle potentially malicious price updates from Chrome extension users?** — trust/validation of crowdsourced price reports.
3. **How do we efficiently process price changes and notify subscribed users?** — threshold matching and notification fan-out within the 1-hour SLA.
4. **How do we serve fast price history queries for chart generation?** — time-series storage/aggregation for < 500ms chart reads.

## Final Design
*(Content premium-locked.)*

## What is Expected at Each Level?

The article includes sections for **Mid-level**, **Senior**, and **Staff+** expectations, but the content is premium-locked.

---

## Locked sections (premium-only, not captured)

- Planning the Approach
- Defining the Core Entities
- The API
- Data Flow
- High-Level Design (both requirement walkthroughs, diagrams)
- Deep Dive 1: Discovering/tracking 500M Amazon products (tradeoffs and "great solution")
- Deep Dive 2: Handling malicious price updates from extension users
- Deep Dive 3: Processing price changes and notifying subscribers
- Deep Dive 4: Fast price history queries for charts
- Final Design diagram
- What is Expected at Each Level (Mid-level / Senior / Staff+)
- Premium video walkthrough
