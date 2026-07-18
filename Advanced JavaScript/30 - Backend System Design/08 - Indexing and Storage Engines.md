---
tags: [system-design, backend, databases, interview]
module: "30 - Backend System Design"
priority: deep-dive
status: not-started
aliases: [database index, B-Tree, LSM tree, Bloom filter]
---

# Indexing and Storage Engines

## Maturity Target

- Priority: #deep-dive
- Study time: 30 minutes
- Interview signal: Explain what an index buys and costs, contrast B-Tree (read/range) with LSM (write-optimized), and know Bloom filters as a "skip the disk read" trick.
- Production signal: You can read why a query is fast or slow, and why a search endpoint is eventually consistent, from the index behind it.
- Dependencies: [[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling and Databases]]

## Source Anchors

- [HelloInterview — Database Indexing](https://www.hellointerview.com/learn/system-design/core-concepts/database-indexing)
- [Use The Index, Luke](https://use-the-index-luke.com/)

## 1. Concept

Simple version: an index is a sorted side-structure that turns "scan every row" into "jump straight to the rows you want." It trades write speed and storage for read speed.

- **B-Tree index** — a balanced sorted tree; supports point lookups in logarithmic time *and* range/ordered scans (O(log n) to find the start, then a linear walk of the k matches). The default relational index. Every write must also update the index, so more indexes = slower writes and more storage.
- **LSM tree (Log-Structured Merge)** — buffers writes in memory (a memtable), flushes sorted runs (SSTables) to disk, and compacts them in the background. Writes are cheap (sequential appends); the costs are **read amplification** (a read may check several runs) and **write amplification** (background compaction rewrites the same data multiple times). Used by Cassandra, RocksDB — the write-optimized counterpart to B-Trees.
- **Bloom filter** — a probabilistic bit-array that answers "is this key *definitely not* here?" with no false negatives (but possible false positives). LSM engines use it to skip reading SSTables that can't contain a key — a cheap way to avoid disk I/O.
- **Inverted index** — term → list of documents; the structure behind full-text search (Elasticsearch). Refreshes on an interval, which is *why search is near-real-time / eventually consistent*.

> [!warning] Every index you add taxes writes and storage. Indexing "just in case" slows the write path and inflates the dataset. Index for the access patterns you actually have — the same discipline as not caching everything.

## 2. Why It Matters

You rarely create indexes as a frontend engineer, but they explain the *shape of the APIs you consume*: why a search endpoint lags a write (inverted-index refresh), why "jump to page N" isn't offered (no cheap ordinal index → cursor pagination), why some filters are instant and others time out. The read/write/space tradeoff triangle is also the same one you make choosing an in-memory Map (O(1) keyed lookup, more memory) vs array (compact, O(n) search) on the client, or memoizing a derived value ([[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization]]) — spend space to buy read speed.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: you build search-as-you-type against a new `/search` endpoint. A user creates a post and immediately searches for it — no result for a second or two — and files a bug.

Trace: the search is backed by an **inverted index** that refreshes on an interval (e.g., ~1s in Elasticsearch), so a just-written document isn't searchable until the next refresh — a designed near-real-time property, not a failure. It's the server-side sibling of a stale client cache.

Fix (product-level, not "make the index instant"): set the UX expectation — show the user's own new item from the write response (read-your-own-writes on the client) while the index catches up for global search; or, if truly needed, force a refresh for that document at a throughput cost.

Tradeoff: forcing refresh-per-write destroys the index's write throughput (its whole point). Accepting a sub-second window is almost always correct — design the UI around it.

## 4. Interview Answer

Short answer:

> An index is a sorted structure that trades write speed and storage for fast reads. B-Trees are the relational default and handle both point and range queries; LSM trees optimize writes by appending and compacting, which is why write-heavy stores like Cassandra use them, often with Bloom filters to skip disk reads for keys that definitely aren't present. I index for the access patterns I have, because every index slows writes.

Deeper answer:

> The frontend-relevant payoff is reading system behavior from the index: full-text search sits on an inverted index that refreshes on an interval, which is exactly why search endpoints are eventually consistent and search-as-you-type can't see a just-created document instantly. And the absence of a cheap ordinal index is why feeds offer cursor rather than offset pagination. So indexing choices upstream directly shape the API contracts and consistency guarantees I design the client against.

## 5. Practice

1. <details><summary>Why does adding indexes slow writes?</summary>Every insert/update/delete must also update each index structure to keep it sorted/consistent, plus extra storage and cache pressure. Read speed for indexed queries improves; write throughput and disk footprint get worse — so you index deliberately, not by default.</details>
2. <details><summary>Why are LSM trees good for write-heavy workloads?</summary>They turn random writes into sequential appends to an in-memory memtable, flushed as immutable sorted files and compacted in the background — cheap writes. The cost is read amplification (a read may consult several files), mitigated by Bloom filters that rule out files that can't hold the key.</details>
3. <details><summary>How does an index choice explain an API you consume?</summary>Inverted-index refresh intervals make search eventually consistent (new items appear after a short delay); lack of a cheap ordinal index pushes feeds to cursor pagination; a missing index on a filter column is why that filter is slow or unsupported. The API's shape mirrors the storage engine's strengths.</details>

## Related Notes

- [[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling and Databases]]
- [[30 - Backend System Design/03 - API Design|API Design]] (cursor pagination)
- [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]] (Elasticsearch, Cassandra)
