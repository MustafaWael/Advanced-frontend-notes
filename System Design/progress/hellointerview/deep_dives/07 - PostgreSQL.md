# PostgreSQL

**Source:** https://www.hellointerview.com/learn/system-design/deep-dives/postgres

> **Note: This page is premium-locked.** Only the introduction, the motivating example, and the beginning of the "Read Performance" section are freely visible. The notes below capture the free content faithfully; the locked sections are listed at the end.

## What Is PostgreSQL (Interview Framing)?

PostgreSQL is the most beloved database in Stack Overflow's developer survey and is used by companies from Reddit to Instagram (and hellointerview.com itself). It's the default relational choice in system design interviews.

Key framing from the article: **your interviewer isn't looking for a DBA — they want informed architectural decisions.** When should you choose PostgreSQL? When should you look elsewhere? What are the trade-offs?

Two common candidate mistakes:

- Diving too deep into internals (MVCC, WAL) when the interviewer just wants to know if it can handle the data relationships.
- Making overly broad statements like "NoSQL scales better than PostgreSQL" without understanding the nuances.

## A Motivating Example

Designing a growing (not Facebook-scale) social media platform with these relationships:

- Users create posts, comment on posts, follow other users
- Users like posts and comments
- Users create direct messages (DMs) with other users

Different operations have different requirements — this is the interesting part:

- **Atomicity**: multi-step operations like creating a DM thread (create thread + add participants + store first message) must happen together.
- **Referential integrity**: comments need a valid post; follows need an existing user.
- **Eventual consistency is fine** for like counts (a few seconds of lag is acceptable).
- **Efficient reads**: profile requests must fetch recent posts, follower count, and metadata quickly.
- **Search**: users search posts and find other users.
- **Growth**: more data and more complex queries over time.

This mix — complex relationships, mixed consistency needs, search, and room for growth — is exactly where PostgreSQL's strengths and limitations show.

## Core Capabilities & Limitations (free portion)

Most PostgreSQL interview discussions center on: **read performance, write capabilities, consistency guarantees, and replication.**

### Read Performance

Reads vastly outnumber writes in most applications (users browse far more than they post), so read performance is critical.

Don't dive into query planner internals in an interview — focus on practical patterns and when different index types make sense.

Example: viewing a profile requires fetching all posts by a user. Without an index on `posts.user_id`, PostgreSQL scans every row — increasingly expensive as data grows. An index on `user_id` locates a user's posts without a full scan.

#### Basic Indexing

PostgreSQL's default index type is the **B-tree**, which is great for:

- Exact matches (`WHERE email = 'user@example.com'`)
- Range queries (`WHERE created_at > '2024-01-01'`)
- Sorting (`ORDER BY username` when ORDER BY columns match the index column order)

PostgreSQL automatically creates a B-tree index on the primary key; you add others as needed:

```sql
-- Bread and butter index
CREATE INDEX idx_users_email ON users(email);

-- Multi-column index for common query patterns
CREATE INDEX idx_posts_user_date ON posts(user_id, created_at);
```

**Interview trap: don't suggest indexing every column.** Each index:

- Slows writes (index must be updated on each write)
- Takes disk space
- May not even be used if the query planner prefers a sequential scan

## Locked Sections (premium-only, content not captured)

The following sections exist in the article but are behind the premium paywall:

- Beyond Basic Indexes
- Query Optimization Essentials
- Write Performance (Throughput Limitations, Write Performance Optimizations)
- Replication (Scaling reads, High Availability)
- Data Consistency (Transactions)
- When to Use PostgreSQL (and When Not To) / When to Consider Alternatives
- Summary
- Appendix: Basic SQL Concepts (Relational Database Principles; ACID Properties — Atomicity, Consistency, Isolation, Durability; Why ACID Matters; SQL Language / SQL Command Types)
