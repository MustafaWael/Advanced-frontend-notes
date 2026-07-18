# Database Indexing

**Source:** [hellointerview.com — Database Indexing](https://www.hellointerview.com/learn/system-design/core-concepts/db-indexing)

> **Note:** This page is **partially premium-locked**. The free portion covers how indexes work, their costs, and B-Tree indexes in full. The sections on LSM Trees (details), Hash Indexes, Geospatial Indexes (Geohash/Quadtree/R-Tree), Inverted Indexes, Composite Indexes, and Covering Indexes are behind the Hello Interview Premium paywall — only their headings are visible. What follows is everything available for free.

Without indexes, finding a user by email in a table of millions means scanning every row sequentially — like searching every book in a library one by one. Indexes are separate data structures optimized for searching that let the database locate records without examining every row.

Knowing when to add an index, on which columns, and which type is a key interview focus: mid-level engineers are expected to know basic indexing strategies; staff-level engineers should master index types and their tradeoffs. Indexing is a stronger focus in infrastructure-style interviews; full-stack/product roles usually just need when-and-why basics.

## How Database Indexes Work

Table data is written to disk as files — typically a **heap file**: a collection of rows in no particular order (like a notebook with entries appended as they come).

### Physical Storage and Access Patterns

Data lives on disk (typically SSDs) but is processed in memory, so every query loads data from disk into RAM. Without an index, the DB scans every page one by one — millions of pages means millions of relatively slow disk reads to find one record. Databases have prefetching and caching optimizations, but sequential full scans are still too slow.

Indexes provide a structured path directly to the needed data, minimizing pages read — the difference between checking every page of a book and using the table of contents.

Important nuance: **random access is still significantly slower than sequential access even on SSDs** (a common misconception; the gap is smaller than HDDs but real). On HDDs with large datasets the difference is even more pronounced, making indexing critical.

### Cost of Indexes

Indexes aren't free:

- **Disk space:** each index needs extra space, sometimes nearly as much as the original data.
- **Write performance:** every insert/update must update the main table *and* every index — multiple indexes mean a single write triggers several disk writes.

When indexes hurt more than help:
- **Write-heavy, read-light tables** (e.g., logging tables constantly inserting, rarely queried).
- **Very small tables** (a few hundred rows) where maintaining/traversing the index costs more than a sequential scan.

The memory impact of indexes is often overblown — modern buffer pool management reduces the hit — but monitor index usage and avoid unnecessary indexes.

## Types of Indexes

### B-Tree Indexes (free content — covered fully)

The most common index type: a **self-balancing tree** maintaining sorted data with efficient inserts, deletes, and searches. Unlike binary trees, B-tree nodes have many children — typically hundreds — each node holding an ordered array of keys and pointers to minimize disk reads.

Rules every B-tree node follows:
- All leaf nodes at the same depth
- Each node holds between m/2 and m keys (m = tree order)
- A node with k keys has exactly k+1 children
- Keys within a node are sorted

The structure maps perfectly to disk storage: each node is sized to one disk page (typically **8KB**). Finding `id=350` in PostgreSQL might need only **2–3 page reads**: root → maybe an internal node → leaf.

**Real-world examples:**
- **PostgreSQL** uses B-trees for almost everything — primary keys, unique constraints, most regular indexes. `CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE);` automatically creates two B-tree indexes (PK + unique email).
- **DynamoDB** orders items within a partition by sort key for efficient in-partition range queries; internals aren't public but it's widely understood to use an LSM-style storage engine rather than a B-tree.
- **MongoDB** uses B-trees (specifically **B+ trees** — all data in leaf nodes) for indexes: `db.users.createIndex({ "email": 1 })` builds a B-tree mapping emails to document locations.

**Why B-trees are the default:**
1. Maintain sorted order — efficient range queries and ORDER BY
2. Self-balancing — predictable performance as data grows
3. Minimize disk I/O by matching database page storage
4. Handle equality (`email = 'x'`) and range (`age > 25`) searches equally well
5. Stay balanced under random inserts/deletes — no performance cliffs

**If you need to pick an index type in an interview, B-trees are a safe bet.**

### LSM Trees (Log-Structured Merge Trees) — mostly premium

Free teaser: B-trees suit balanced workloads, but write-heavy systems (e.g., DataDog ingesting millions of metrics/second from thousands of servers — every CPU reading, memory stat, error count stored immediately) call for LSM trees. Subsections (How LSM Trees Work, Negative Impact on Reads, Real-World Examples) are premium-locked.

### Premium-locked sections (headings only)

- **Hash Indexes** (how they work, real-world usage, when to choose)
- **Geospatial Indexes** (the challenge with location data; Geohash, Quadtree, R-Tree)
- **Inverted Indexes**
- **Index Optimization Patterns:** Composite Indexes (order matters), Covering Indexes
