# 23 - News Aggregator (Google News)

**Source:** https://www.hellointerview.com/learn/system-design/problem-breakdowns/google-news

- **Author:** Evan King (Hello Interview)
- **Difficulty:** Medium
- **Key pattern:** Scaling Reads

> **⚠️ Premium-locked page:** Only the free preview of this breakdown was accessible. The section outline below reflects the article's own structure, but the detailed content of most sections (planning, core entities, API, high-level design, all deep dives) is behind the Hello Interview Premium paywall and is NOT reproduced here. See "Locked sections" at the bottom. (This article's outline did not show a "What is Expected at Each Level" section in the free preview.)

## Understanding the Problem

**What is Google News?** Google News is a digital service that aggregates and displays news articles from thousands of publishers worldwide in a scrollable interface for users to stay updated on current events.

## Functional Requirements

**Core Requirements**

1. Users should be able to view an aggregated feed of news articles from thousands of source publishers all over the world.
2. Users should be able to scroll through the feed "infinitely".
3. Users should be able to click on articles and be redirected to the publisher's website to read the full content.

**Below the line (out of scope):**

- Users should be able to customize their feed based on interests.
- Users should be able to save articles for later reading.
- Users should be able to share articles on social media platforms.

## Non-Functional Requirements

Stated in the free preview: for a news platform, **availability is prioritized over consistency**, as users would prefer to see slightly outdated content rather than no content at all.

*(The rest of the non-functional requirements list is premium-locked. From the deep-dive titles, targets include: feed request latency < 200ms, and articles appearing in feeds within 30 minutes of publication.)*

## The Set Up

### Planning the Approach
*(Content premium-locked.)*

### Defining the Core Entities
*(Content premium-locked.)*

### API or System Interface
*(Content premium-locked.)*

## High-Level Design

The high-level design addresses each functional requirement in turn (details premium-locked):

1. Users should be able to view an aggregated feed of news articles from thousands of source publishers all over the world.
2. Users should be able to scroll through the feed "infinitely".
3. Users should be able to click on articles and be redirected to the publisher's website.

## Potential Deep Dives

Five main deep dives plus two bonus deep dives (all detail premium-locked):

1. **How can we improve pagination consistency and efficiency?** — infinite scroll pagination (e.g., cursor vs. offset concerns).
2. **How do we achieve low latency (< 200ms) feed requests?** — read-path optimization/caching.
3. **How do we ensure articles appear in feeds within 30 minutes of publication?** — ingestion freshness pipeline.
4. **How do we handle media content (images/videos) efficiently?** — blob/CDN handling.
5. **How do we handle traffic spikes during breaking news?** — burst scaling of reads.

**Bonus Deep Dives**

6. **How can we support category-based news feeds (Sports, Politics, Tech, etc.)?**
7. **How do we generate personalized feeds based on user reading behavior and preferences?**

---

## Locked sections (premium-only, not captured)

- Non-Functional Requirements (detailed list beyond the availability-over-consistency note)
- Planning the Approach
- Defining the Core Entities
- API or System Interface
- High-Level Design (all three requirement walkthroughs, diagrams)
- Deep Dive 1: Pagination consistency and efficiency (tradeoffs and "great solution")
- Deep Dive 2: Low latency (< 200ms) feed requests
- Deep Dive 3: Articles in feeds within 30 minutes of publication
- Deep Dive 4: Efficient media content handling
- Deep Dive 5: Traffic spikes during breaking news
- Bonus Deep Dives 6-7: Category-based feeds; personalized feeds
