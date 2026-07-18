# Elasticsearch

**Source:** [hellointerview.com — Elasticsearch Deep Dive](https://www.hellointerview.com/learn/system-design/deep-dives/elasticsearch)

## What Elasticsearch Is

Many system design problems involve **search and retrieval**: "I've got a lot of things and I want to find the right one(s)." Most databases handle this fine at small scale (Postgres with a full-text index is often enough), but at scale or with sophisticated requirements — sorting, filtering, ranking, faceting — you reach for a purpose-built search engine. Elasticsearch is the best-known one.

Two interview angles:

1. **How to use it** — rarely will you find a search question too complex for Elasticsearch. Great for product-architecture interviews.
2. **How it works under the hood** — a masterclass in distributed systems. Some interviewers (especially for infra-heavy roles at cloud companies) will ask you to pretend Elasticsearch doesn't exist and design the top-level concepts yourself.

Architecturally, Elasticsearch is a **high-level orchestration framework over Apache Lucene** (the low-level, highly optimized search library). Elasticsearch handles the distributed-systems parts (cluster coordination, APIs, aggregations, real-time capabilities); Lucene is the heart of search.

## Basic Concepts (Data Model)

- **Documents**: the individual units of data you search over — any JSON object (a book, a review, a user). Not just "websites."
- **Indices**: a collection of documents — think database table. Searches run against indices and return matching documents. (Overloads the general term "index" for auxiliary lookup structures.)
- **Mappings and Fields**: the mapping is the **schema** of the index — which fields exist, their types, and how they're processed/indexed. E.g. `id` as `keyword` (whole-value lookup, like a hash table) vs `title` as `text` (tokenized, "contains" queries via a reverse index).

Types can be complex: nested objects/arrays, geospatial types (`geo_point`, `geo_shape`), custom analyzers, even embeddings for semantic search.

**Performance implication**: mapping fields that aren't actually searched wastes memory per index (e.g. mapping all 10 fields of a User when only 2 are searchable). Much of your control over query performance is via the mapping and cluster parameters.

## Basic Use (REST API)

- **Create an index**: `PUT /books` with settings like `number_of_shards: 1`, `number_of_replicas: 1` (updatable later).
- **Set a mapping**: `PUT /books/_mapping` pre-registering searchable fields (`title: text`, `author: keyword`, `price: float`, `publish_date: date`, `categories: keyword`, plus a `nested` `reviews` field with its own sub-fields).
  - Nesting reviews inside books vs a separate reviews index is the **normalization/denormalization tradeoff**: nest if reviews are infrequently updated and frequently queried alongside books; otherwise separate index. Fair game for a picky interviewer.
- **Add documents**: `POST /books/_doc` with the JSON. Response includes `_id`, `_version`, shard info.
- **Update documents**:
  - Full replace: `PUT /books/_doc/{id}` — risky under concurrency (can overwrite others' changes).
  - Guarded: `PUT /books/_doc/{id}?version=1` — fails if version doesn't match → **optimistic concurrency control**; client handles conflict and retries.
  - Partial: `POST /books/_update/{id}` with `{"doc": {"price": 14.99}}` — update fields without fetching the whole doc. Explicit update semantics matter because Elasticsearch is distributed/async/concurrent and requests can arrive out of order.

### Search

JSON query DSL, SQL-like in spirit:

```jsonc
// GET /books/_search
{ "query": { "match": { "title": "Great" } } }
```

Compound queries with `bool` / `must`:

```jsonc
{ "query": { "bool": { "must": [
  { "match": { "title": "Great" } },
  { "range": { "price": { "lte": 15 } } }
] } } }
```

Nested queries use `"nested": { "path": "reviews", "query": ... }`. Results include document IDs, relevance `_score`s, and `_source` documents.

### Geospatial Search (very interview-relevant)

For Yelp/Uber-style location services, Elasticsearch shines vs a relational DB:

- **geo_point**: single lat/lon (restaurant locations, check-ins).
- **geo_shape**: arbitrary geometries — polygons, lines, circles (delivery zones, city boundaries).

Query with `geo_distance` (find docs within a radius of a point), and combine with `bool` filters: "Italian restaurants within 2 miles, sorted by rating" — exactly the multi-faceted search that makes ES a natural fit.

Under the hood: geohashes, **BKD trees** (a k-d tree variant optimized for block storage — used by `geo_point`), and R-tree-like structures, which narrow the search space in 2D without the limits of separate B-tree indexes on lat and lon.

### Sorting

- Basic: `"sort": [{ "price": "asc" }, { "publish_date": "desc" }]`.
- Script-based (Painless language) for computed values.
- Nested-field sorts need `nested.path` and a `mode` (e.g. sort books by max review rating).
- Default (no sort specified): **relevance score** (`_score`), based closely on **TF-IDF** — worth 10 minutes to learn; it comes up everywhere.

### Pagination and Cursors

1. **From/Size**: simplest (`from`, `size`), but inefficient for deep pagination (beyond ~10,000 results) — the cluster must retrieve and sort all preceding documents on each request.
2. **search_after**: use the sort values of the last result as the starting point of the next page. Efficient even deep in the result set; no duplicates or missed new documents. But: client must maintain state, forward-only, and can miss documents in prior pages if underlying data changes.
3. **Point in Time (PIT) + search_after** (cursors): `POST /my_index/_pit?keep_alive=1m` returns a PIT ID; pass it in searches with `search_after`; delete when done. Provides a **consistent view** across pages even while the index is updated — at the cost of more overhead/state.

## How It Works (Under the Hood)

### Cluster Architecture — Node Types

- **Master node**: cluster admin — add/remove nodes, create/delete indices. Elected from seed (master-eligible) nodes via leader election; one active master, others standby.
- **Data node**: stores the data — most numerous in big clusters. Specializations: hot/warm/cold/frozen tiers based on how likely data is to be queried.
- **Coordinating node**: cluster frontend — receives search requests, fans out to the right nodes, merges results.
- **Ingest node**: transforms/prepares data for indexing.
- **Machine learning node**: ML tasks.

One instance can hold multiple roles; sophisticated deployments dedicate hardware per role (CPU-heavy ingest, high-disk-I/O data nodes).

### Data Nodes

Data nodes separate the raw `_source` documents from the Lucene indexes used in search (like a separate document DB). Requests have two phases: **query** (identify relevant docs using index structures) then **fetch** (optionally pull the documents). Ideal queries never touch source documents.

The nesting doll: **Index → shards (+ replicas) → Lucene index (1:1 with shard) → Lucene segments.**

- **Shards** split data and indexes across hosts; searches execute across all relevant shards in parallel, results merged/sorted by the coordinating node.
- **Replicas** = exact copies of shards. Two purposes: high availability and throughput (X TPS per shard × Y replicas ≈ X·Y TPS); coordinating nodes load-balance across primary + replicas.

### Lucene Segments — Immutability

Segments are **immutable** containers of indexed data:

- **Writes** are batched into new segments and flushed to disk.
- **Merges**: when segments get numerous, merge into a new segment and drop the old ones.
- **Deletes** are *soft*: each segment keeps a set of deleted IDs; queries pretend deleted docs don't exist; merges physically clean them up.
- **Updates** = soft-delete old + insert new. Updates are therefore **more expensive than inserts** — a key reason Elasticsearch is a poor fit for rapidly-updating data.

Benefits of immutability: fast writes, safe caching, simple concurrency (reads never see mid-query changes), easy crash recovery, better compression, faster searches. Costs: periodic merges and temporary storage bloat. (Great pattern to cite in infra design interviews.)

### Segment Data Structures

- **Inverted index** — the heart of Lucene: maps each token (e.g. "lazy") to the documents containing it, turning an O(n) scan into an ~O(1) lookup. This is what makes keyword search fast.
- **Doc values** — columnar, contiguous storage of a single field across all docs in a segment (like Spark/Redshift columnar formats). The inverted index finds the matching docs; doc values supply the field (e.g. price) for fast sorting/aggregation without reading whole documents.

### Coordinating Nodes and Query Planning

Coordinating nodes parse queries, decide which nodes execute what, and merge results. The **query planner** picks the most efficient execution order — e.g. searching "bill nye" where "bill" has millions of postings and "nye" a few hundred: intersecting from the rare term first can be orders of magnitude faster. ES keeps statistics (field types, popular keywords, document lengths) to make these data-dependent choices — the same reason database query planners are so powerful.

## In Your Interview

Elasticsearch fits any question with complex search. **Most often it's attached via Change Data Capture (CDC) to an authoritative store like Postgres or DynamoDB.**

Rules of thumb:

1. **Don't use it as your database.** It's a search engine first; earlier versions had real consistency/durability issues. If data must persist, put it somewhere else.
2. **It's built for read-heavy workloads.** Write-heavy systems (e.g. per-post like counts, impression counters) will make it struggle — consider a write buffer or other options.
3. **It's eventually consistent** — results *will* be stale, sometimes significantly. If you can't tolerate that, look elsewhere.
4. **It's not relational** — denormalize aggressively (with write-side transformation logic); aim for results from 1–2 queries.
5. **Not every search problem needs it** — small (<100k docs) or rarely-changing data is often served fine by your primary datastore. Only add ES when a simple query proves insufficient.
6. **Keeping ES in sync with the source of truth is a common bug source** — synchronization failures cause drift.

Be prepared to justify Elasticsearch over alternatives and to discuss its limitations, not just its strengths.

### Design Lessons Worth Stealing

1. **Immutability** at the right layer enables caching, compression, and concurrency wins.
2. **Separate query execution from storage** (coordinating vs data nodes) and optimize each independently.
3. **Indexing strategy drives performance**: inverted index for full-text, doc values for sorting/aggregation — structure data for your query patterns.
4. **Distribution brings scalability and fault tolerance but also complexity** — CAP tradeoffs apply.
5. **Specialized data structures matter** (skip lists, finite state transducers, BKD trees) — choose them for your access patterns.

## References (from the article)

- Full Text Search over Postgres: Elasticsearch vs. Alternatives (ParadeDB)
- Exploring Apache Lucene — Part 1: The Index
- BKD Trees, Used in Elasticsearch
