# 17 - Yelp (Local Business Review Site)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/yelp

> **⚠️ Premium-locked page.** Only the "Understanding the Problem" section (functional + non-functional requirements) is freely visible. Everything from "Constraints" onward — Core Entities, API, High-Level Design, all four Deep Dives, Final Design, and the level expectations (Mid/Senior/Staff+) — is behind the Hello Interview Premium paywall. The locked section headings are listed below so you know what the full breakdown covers.

- **Difficulty:** Easy
- **Pattern tags:** Scaling Reads
- **Author:** Evan King

## Understanding the Problem

**What is Yelp?** Yelp is an online platform that allows users to search for and review local businesses, restaurants, and services.

Some interviewers will start the interview by outlining the core functional requirements for you; other times you'll be tasked with coming up with them yourself. If you've used the product, this is straightforward — if not, ask the interviewer questions to understand the system.

### Functional Requirements

**Core requirements:**

1. Users should be able to **search for businesses** by name, location (lat/long), and category.
2. Users should be able to **view businesses** (and their reviews).
3. Users should be able to **leave reviews** on businesses (mandatory 1–5 star rating and optional text).

**Below the line (out of scope):**

- Admins should be able to add, update, and remove businesses (focus is on the user).
- Users should be able to view businesses on a map.
- Users should be recommended businesses relevant to them.

### Non-Functional Requirements

**Core requirements:**

1. Low latency for search operations (**< 500ms**).
2. Highly available; **eventual consistency is fine** (availability over consistency).
3. Scalable to handle **100M daily users and 10M businesses**.

**Below the line (out of scope):**

- Protect user data / adhere to GDPR.
- Fault tolerance.
- Protection against spam and abuse.

**Tip from the breakdown:** most systems are "all these things" (fault tolerant, scalable, etc.) — the goal of non-functional requirements is to identify the *unique* characteristics that make this specific system challenging (here: read-heavy geo search at low latency with eventual consistency being acceptable).

## Structure of the Full Breakdown (🔒 premium-locked sections)

The remainder of the article follows Hello Interview's standard delivery framework. These sections exist but their content is not accessible without Premium:

- **Constraints** 🔒
- **The Set Up**
  - Defining the Core Entities 🔒
  - The API 🔒
- **High-Level Design** 🔒
  1. Users should be able to search for businesses
  2. Users should be able to view businesses
  3. Users should be able to leave reviews on businesses
- **Potential Deep Dives** 🔒
  1. How would you efficiently calculate and update the **average rating** for businesses so it's readily available in search results?
  2. How would you ensure a user can only leave **one review per business**?
  3. How can you improve **search to handle complex queries** more efficiently?
  4. How would you allow **searching by predefined location names** (cities, neighborhoods)?
- **Final Design** 🔒
- **What is Expected at Each Level?** 🔒 (Mid-level / Senior / Staff+ subsections exist but content is locked)

## Study Hints (from the visible signals, not the locked text)

These are inferences a mid-level engineer can use to self-study the locked topics — they come from the page's tags and question titles only:

- The problem is tagged **"Scaling Reads"** — expect the design to lean on read replicas, caching, denormalized/precomputed data (e.g., storing average rating on the business record rather than computing at query time), and a search-optimized index.
- Deep dive 1 (average rating) is a classic **precompute vs. compute-on-read** tradeoff.
- Deep dive 2 (one review per user per business) is a **uniqueness/constraint enforcement** question (e.g., DB unique constraint on `(user_id, business_id)`).
- Deep dives 3–4 relate to **geospatial + full-text search** (see Hello Interview's "Proximity Search" and Elasticsearch deep-dive pages, which are linked from this problem's nav).
