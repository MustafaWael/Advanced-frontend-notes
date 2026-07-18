# DynamoDB

**Source:** https://www.hellointerview.com/learn/system-design/deep-dives/dynamodb

## What Is DynamoDB?

DynamoDB is a **fully-managed, highly scalable, key-value NoSQL database** from AWS.

- **Fully-managed** — AWS handles hardware provisioning, configuration, patching, and scaling; you focus on the application.
- **Highly scalable** — handles massive data/traffic and auto-scales up/down with no downtime.
- **Key-value / NoSQL** — flexible, schema-less storage instead of the relational model.

It now **supports ACID transactions**, neutralizing the old "NoSQL has no transactions" criticism. It is **not open-source** (internals are known mainly from AWS docs and the DynamoDB paper).

Interview tip: candidates often ask "am I allowed to use DynamoDB?" — just ask your interviewer. Some want vendor-neutral/open-source alternatives.

## Data Model

- **Tables** — top-level structure; each requires a primary key; support secondary indexes.
- **Items** — like rows; a collection of attributes; must have the primary key; **max 400KB per item**.
- **Attributes** — key-value pairs; scalar types (string, number, boolean), set types, and **nested** structures.

DynamoDB is **schema-less**: items in the same table can have different attributes, and new attributes can be added anytime. This means data validation happens at the application level. JSON is only the transport format; storage format is proprietary.

### Partition Key and Sort Key

The primary key is one or two attributes:

1. **Partition Key** — hashed to determine the physical partition where the item is stored.
2. **Sort Key (optional)** — with the partition key forms a composite primary key; orders items within a partition, enabling **range queries and sorting**.

Example: a group chat app → partition key `chat_id`, sort key `message_id` → efficiently fetch all messages for a chat in chronological order.

Prefer a **monotonically increasing ID over a raw timestamp** for sort keys (timestamps can collide). Options: per-partition auto-increment counters, **UUID v7** (timestamp-first, sortable, no MAC address leak), **Snowflake IDs**, **ULID**.

**Under the hood:**

- **Hash partitioning** on the partition key; a request router consults a **centralized partition metadata service** (not a peer-to-peer hash ring like the 2007 Dynamo paper) to find the storage node; partitions split/merge automatically.
- **B-trees** within each partition, indexed by sort key, enable efficient range queries.
- Composite key queries: hash finds the node, then the B-tree finds the items.

## Secondary Indexes

For querying by attributes other than the primary key:

1. **Global Secondary Index (GSI)** — different partition key (and optional sort key) from the table. Stored on **separate physical partitions**, replicated separately, updated **asynchronously** (eventually consistent only).
2. **Local Secondary Index (LSI)** — same partition key, different sort key. Co-located with the base table's partitions (separate B-tree per partition), updated **synchronously**; supports strongly consistent reads.

Example (chat app): main table `chat_id`/`message_id`; to show all messages a user sent across chats, add a **GSI** with partition key `user_id`, sort key `message_id`. To sort within a chat by a different attribute (e.g., `num_attachments`), use an **LSI**.

| Feature | GSI | LSI |
|---|---|---|
| Partition key | Different from table | Same as table (different sort key) |
| Size limit | None | 10 GB per partition key |
| Throughput | Separate capacity from base table | Shares base table capacity |
| Consistency | Eventually consistent only | Eventual or strongly consistent |
| Creation | Add/remove anytime | **Only at table creation**; cannot remove |
| Max per table | 20 | 5 |
| Typical use | Global search across partitions (e.g., by email) | Local search within a partition (e.g., recent orders per customer) |

## Accessing Data

- **Query** — retrieves items by primary key / index key conditions; supports sort-key range queries. Efficient — prefer this.
- **Scan** — reads every item in the table; paginated; **avoid for large datasets**.

Primary interface is the AWS SDK/console (not a standalone query language), though **PartiQL** provides SQL-like syntax as a convenience layer over the same operations.

```js
// SELECT * FROM users WHERE user_id = 101
const params = {
  TableName: 'users',
  KeyConditionExpression: 'user_id = :id',
  ExpressionAttributeValues: { ':id': 101 }
};
dynamodb.query(params, ...);
```

Note on reads: you read the **entire item** by default. `ProjectionExpression` only reduces network bandwidth — you're still charged RCUs for full item size. So for large items (e.g., a Yelp business with embedded reviews), **split into separate tables** (business table + reviews table keyed by business ID) to avoid over-reading.

## CAP Theorem / Consistency

DynamoDB supports two read consistency models, chosen **per request** (not per table) via `ConsistentRead=true`:

- **Eventual consistency (default)** — highest availability, lowest latency; may not reflect the latest write. DynamoDB behaves as an AP/BASE system by default.
- **Strong consistency** — read reflects all prior successful writes; costs **2x read capacity** (1 RCU per 4KB vs 0.5) and slightly higher latency.

DynamoDB also supports **ACID transactions** via `TransactWriteItems` / `TransactGetItems` — serializable isolation across **up to 100 items spanning multiple tables**.

Caveat: **strongly consistent reads work only on the base table and LSIs — GSIs are eventually consistent only.**

**Under the hood:** each partition has a 3-replica replication group (1 leader, 2 followers) using **Multi-Paxos**. Writes go through the leader (WAL entry, acknowledged at 2-of-3 quorum). Strongly consistent reads route to the leader; eventually consistent reads can hit any replica.

## Architecture and Scalability

- **Auto-sharding**: when a partition hits size/throughput limits, DynamoDB splits it and redistributes data automatically; hash partitioning keeps distribution even.
- **Global Tables**: real-time cross-region replication for local reads/writes worldwide — usually sufficient to just mention this for global apps in interviews.
- **Fault tolerance**: data automatically replicated across **three Availability Zones** in a region (not user-configurable).

## Security

- Encryption **at rest by default**; **TLS enforced** for all API calls (in transit).
- **IAM** for fine-grained access control; **VPC endpoints** for private access.
- In interviews: mentioning default at-rest + in-transit encryption for sensitive data is usually enough; more is overkill.

## Pricing Model (Useful for Back-of-Envelope Math)

Two models: **on-demand** (per request; unpredictable workloads) and **provisioned capacity** (RCU/WCU billed hourly; cheaper for predictable load).

- **1 RCU** = one strongly consistent read/sec up to 4KB (or two eventually consistent reads). ~$1.12 per million reads.
- **1 WCU** = one write/sec up to 1KB. ~$5.62 per million writes.
- **Per-partition limits: 3,000 RCU and 1,000 WCU** → ~12MB/s reads and 1MB/s writes per partition.

Example gut-check: storing YouTube views at 10M writes/sec → each write ≥1 WCU (rounds up to 1KB) → ~10,000 partitions → roughly **$156,000/day** on provisioned capacity. Pricing math helps validate whether a design is realistic.

## Advanced Features

### DAX (DynamoDB Accelerator)

Purpose-built **in-memory cache** for DynamoDB — microsecond reads without adding Redis/Memcached. Requires swapping to the DAX client SDK (API-compatible). Operates as a **read-through and write-through** cache with two caches (item cache and query cache, both always active). Caveats:

- DAX only invalidates entries for writes **that go through DAX** — direct DynamoDB writes leave stale cache entries until TTL/eviction.
- DAX does **not cache strongly consistent reads** (passes them through).

### DynamoDB Streams (CDC)

Built-in **Change Data Capture**: every insert/update/delete is recorded as a stream record for real-time consumption. Uses:

- **Elasticsearch sync** — keep a search index consistent with the table.
- **Real-time analytics** — via Kinesis Data Streams → Firehose → S3/Redshift/OpenSearch (Firehose can't read DynamoDB Streams directly; Kinesis or a Lambda intermediary is needed).
- **Change notifications** — trigger Lambdas for notifications, cache updates, etc.

## DynamoDB in an Interview

### When to Use It

Justifiable for **almost any persistence layer**: highly scalable, durable, transactional, single-digit-millisecond latency (microseconds with DAX), plus Streams for cross-store consistency. If the interviewer allows it, it's probably a great option.

### Limitations / When Not To

1. **Cost** — per-operation pricing gets expensive at very high write volumes (hundreds of thousands of writes/sec).
2. **Complex queries** — no joins or ad-hoc aggregations; transactions exist but querying is far less flexible than SQL.
3. **Data modeling constraints** — needs careful key design; if you're leaning heavily on many GSIs/LSIs, a relational DB like PostgreSQL may fit better.
4. **Vendor lock-in** — AWS-only; some interviewers prefer vendor-neutral choices.

### Pitfalls to Remember

- Avoid Scans; design keys around query patterns.
- GSIs are eventually consistent only — don't design strong-consistency paths through a GSI.
- LSIs must be defined at table creation and cap partitions at 10GB.
- 400KB item limit; normalize large/embedded data into separate tables.
- RCU billing is by full item size regardless of projection.
