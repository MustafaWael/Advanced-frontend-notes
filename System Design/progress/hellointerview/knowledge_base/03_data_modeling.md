# Data Modeling

**Source:** [hellointerview.com — Data Modeling](https://www.hellointerview.com/learn/system-design/core-concepts/data-modeling)

Data modeling defines how your application's data is structured, stored, and related: what entities exist, how they're identified, how they connect. In a system design interview the bar is lower than a dedicated data-modeling interview — you need something clear, functional, and aligned with requirements, not full normalization or complete schema diagrams.

It appears twice in the delivery framework: (1) core entities during requirements gathering (usually mapping 1:1 to tables/collections), and (2) a basic schema sketched next to the database component in high-level design — key fields, relationships, and a note on indexing/partitioning for the main query patterns. A sloppy data model causes painful issues later; a solid "good enough" one keeps the conversation focused.

## Database Model Options

Resist the temptation to pick exotic databases to show off. **Default: relational database — recommend PostgreSQL** unless you have significant experience/strong opinions about an alternative. Knowing when other models help demonstrates tradeoff thinking.

### Relational Databases (SQL)

Tables with fixed schemas; rows = entities, columns = attributes; relationships via foreign keys; **ACID** transaction guarantees. Most problems map naturally: social apps (users, posts, comments, likes), e-commerce (users, products, orders, payments).

Example tables — Users (id PK, username, email, created_at), Posts (id PK, user_id FK, content, created_at), Likes (id PK, user_id FK, post_id FK, created_at).

- Great at complex queries: "all posts by users a given user follows, ordered by recency" is a straightforward join. But multi-table joins can become performance traps at scale — complex reporting-style queries raise yellow flags; consider denormalized views, caching, or precomputed results.
- When strong consistency is a non-functional requirement (no double-charging payments, no overselling inventory), ACID is the right tool.
- The scalability knock is exaggerated: read replicas, sharding, connection pooling, and caching scale SQL far — Facebook and Airbnb run on relational foundations. Scaling is about architecture around the DB, not just the DB.

**Examples:** PostgreSQL, MySQL, SQLite.

### Document Databases

JSON-like documents, flexible schemas. Model by nesting/embedding related data inside documents instead of normalizing across tables (e.g., posts embedded inside each user document — no joins, but updating a post means modifying the whole user document).

- Interviews scope requirements tightly, so "evolving schemas" rarely apply — only consider if the interviewer explicitly mentions rapidly changing data structures.
- **When over SQL:** frequently changing schema, deeply nested data that would need many joins, records with vastly different structures (e.g., user profiles ranging from minimal to extensive).
- **Modeling impact:** aggressive denormalization/embedding — trades storage and update complexity for read performance.

**Examples:** MongoDB, Firestore, CouchDB.

### Key-Value Stores

Simple exact-key lookups; extremely fast; minimal query capability.

- **When over SQL:** caching, session storage, feature flags, single-identifier lookups, high-write scenarios needing max performance. In practice you often use both: SQL as source of truth + key-value cache (Redis) in front for hot data.
- **Modeling impact:** very flat schema; heavy denormalization; duplicate data across keys per access pattern (no joins). Great for reads, terrible for consistency on change.

**Examples:** Redis, DynamoDB, Memcached.

### Wide-Column Databases

Column families; rows can have different column sets; optimized for massive write-heavy workloads and time-series data. E.g., new post → new row keyed by (user_id, timestamp); same partition key stored together → fast appends, efficient contiguous-range reads of a user's posts.

- **When over SQL:** enormous write volumes, time-series, append-and-aggregate analytics — telemetry, event logging, IoT sensor data.
- **Modeling impact:** design around query patterns even more than SQL; duplicate across column families for access patterns; time is a first-class citizen.

**Examples:** Cassandra, HBase.

### Graph Databases

Nodes and edges, optimized for relationship traversal.

- **When over SQL:** honestly, almost never in interviews. Even Facebook models its social graph with MySQL; LinkedIn/Twitter use SQL for core relationship data. Graph DBs sound sophisticated but add unnecessary operational complexity — a common interview mistake.

**Examples:** Neo4j, Amazon Neptune.

## Schema Design Fundamentals

### Start with Requirements

Three key factors (established during requirements/API phases):

1. **Data volume** — determines where data physically lives; data split across stores forces distinct schemas with careful cross-references.
2. **Access patterns** — the most important factor. How will data be queried? A "recent posts by followed users" feed suggests denormalized data or careful indexes; a time-aggregating analytics dashboard needs different structures. Derive from your APIs: what queries support each endpoint?
3. **Consistency requirements** — financial transactions need strong consistency (same DB, ACID); an activity feed tolerates eventual consistency (a like showing seconds late), allowing distribution across systems with schemas optimized per access pattern.

In interviews, explicitly tie schema choices to these factors: "Since we need to load feeds quickly and likes can be eventually consistent, I'll denormalize like counts into the posts table." All techniques below are tools for these three factors.

### Entities, Keys & Relationships

Map core entities to tables/collections with clear identifiers:

```
users:    id (PK), username, email
posts:    id (PK), user_id (FK → users.id), content, created_at
comments: id (PK), post_id (FK → posts.id), user_id (FK → users.id), content
likes:    user_id (FK → users.id), post_id (FK → posts.id)
```

- **Primary keys:** use system-generated IDs (user_id, post_id), not business data like emails — system keys stay stable when business rules change. In interviews, pick an obvious PK and say why.
- **Relationships:** one-to-many (user→posts, post→comments); many-to-many (users↔posts via likes); one-to-one (rare — often a sign two tables should merge).
- **Foreign keys** enforce referential integrity (no orphaned posts/comments) in SQL; application logic does it in NoSQL. FKs cost validation on each insert/update — at very large scale some companies drop them and enforce integrity in the app. Mentioning this tradeoff scores points.
- **Constraints** (NOT NULL, UNIQUE, CHECK) enforce correctness at the DB level (unique emails, positive prices) at some write overhead.

Keep the schema grounded in the problem domain (users, tweets, follows), not abstract "entities."

### Indexing for Access Patterns

Indexes let the DB find records without scanning every row — like a book index. Call out which columns are indexed and why, tied to your most important queries. Social app example:

- Index `posts.user_id` — find all posts by a user
- Index `posts.created_at` — recent posts chronologically
- Composite index `(user_id, created_at)` — a user's recent posts efficiently

Connect indexes to endpoints: "GET /users/{id}/posts needs an index on posts.user_id." (Deeper internals: see Database Indexing note.)

### Normalization vs Denormalization

**Normalization:** each piece of information stored in exactly one place (user data only in users table). Prevents update anomalies/inconsistent state. **Denormalization** duplicates (e.g., username/email copied into every post row) — if a user renames, every post must be updated; miss one and data is inconsistent.

Interview advice: **start normalized, denormalize only when needed.** Exceptions where denormalization makes sense:

- Analytics/reporting systems aggregating infrequently changing data
- Event logs and audit trails (point-in-time snapshots)
- Heavily read-optimized systems (e.g., search engines) where speed beats consistency

Even then, you can often keep the source of truth normalized and put a **cache with a denormalized representation** in front (pre-computed joins/aggregations).

### Scaling and Sharding

When data outgrows one machine, shard across machines. Choose a partition strategy that keeps related data together:

- **Shard by the primary access pattern:** mostly querying "posts by user" → shard by user_id, keeping a user's posts on one DB and avoiding cross-shard queries.
- **Beware time-range sharding:** all current writes hit the latest shard → hot shard; usually an anti-pattern for write-heavy systems. Fine for archival/analytics where recent data is read-heavy but writes spread out.
- **Avoid cross-shard queries:** a timeline of posts from many followed users sharded by user_id means querying multiple shards and merging — expensive and complex.
- Shard-key choice is often **permanent** and affects every query — think hard about access patterns first.

## Conclusion — Interview Checklist

Outline core entities early; when introducing the database in high-level design:

1. Choose the database type
2. List columns per entity to fulfill functional requirements
3. Specify primary and foreign keys for each relationship
4. Decide which columns need indexes (if any)
5. Decide whether to denormalize for performance
6. Consider sharding; if yes, pick a shard key matching the main access pattern
