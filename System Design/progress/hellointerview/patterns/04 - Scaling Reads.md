# Scaling Reads

**Source:** https://www.hellointerview.com/learn/system-design/patterns/scaling-reads

> Note: This page is premium-locked. Everything below is the free/visible content captured on 2026-07-17. Locked sections are listed at the bottom.

## What This Pattern Is

**Scaling Reads** addresses the challenge of serving high-volume read requests when your application grows from hundreds to millions of users. While writes create data, reads consume it — and read traffic often grows faster than write traffic. The pattern covers architectural strategies to handle massive read loads without crushing your primary database.

## The Problem (free content)

Consider an Instagram feed. Opening the app immediately loads dozens of photos, each requiring multiple database queries: image metadata, user information, like counts, comment previews. That's potentially **100+ read operations just to load your feed** — while you might only post one photo per day (a single write).

This imbalance is incredibly common:

- For every tweet posted, thousands of users read it.
- For every product uploaded to Amazon, hundreds browse it.
- YouTube serves billions of video views daily but only millions of uploads.
- The standard **read-to-write ratio starts at 10:1 and often reaches 100:1 or higher** for content-heavy applications.

As reads increase, your database struggles under the load. More often than not, this isn't a software problem you can debug your way out of — **it's physics**. CPU cores execute only so many instructions per second, memory holds only so much data, and disk I/O is bounded by hardware. Once you hit those physical constraints, more code won't help.

## The Solution: Three-Tier Progression (free content, details locked)

Read scaling follows a natural progression from simple optimization to complex distributed systems:

1. **Optimize read performance within your database**
   - Indexing
   - Hardware Upgrades
   - Denormalization Strategies
2. **Scale your database horizontally**
   - Read Replicas
   - Database Sharding
3. **Add external caching layers**
   - Application-Level Caching
   - CDN and Edge Caching

The ordering itself is the takeaway for interviews: exhaust in-database optimizations first, then replicate/shard, then cache externally. (The detailed mechanics and tradeoffs of each sub-option are behind the paywall.)

## Interview Problems Using This Pattern

The page links this pattern to these Hello Interview problem breakdowns:

- Ticketmaster
- Bitly
- Instagram
- FB News Feed
- YouTube Top K
- Yelp
- Distributed Cache
- Rate Limiter
- YouTube
- FB Post Search
- Local Delivery Service (Gopuff)
- News Aggregator
- Metrics Monitoring

## When to Use in Interviews (headings — details locked)

- Common Interview Scenarios
- When NOT to Use

## Common Deep Dives (headings — details locked)

- "What happens when your queries start taking longer as your dataset grows?"
- "How do you handle millions of concurrent reads for the same cached data?" (hot key problem)
- "What happens when multiple requests try to rebuild an expired cache entry simultaneously?" (cache stampede / thundering herd)
- "How do you handle cache invalidation when data updates need to be immediately visible?"

## Locked Sections (premium-only, not captured)

- Optimize Within Your Database: Indexing, Hardware Upgrades, Denormalization Strategies (details)
- Scale Your Database Horizontally: Read Replicas, Database Sharding (details)
- Add External Caching Layers: Application-Level Caching, CDN and Edge Caching (details)
- When to Use in Interviews: Common Interview Scenarios, When NOT to Use
- All four Common Deep Dives listed above
- Conclusion
