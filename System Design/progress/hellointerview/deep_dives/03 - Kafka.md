# Kafka

**Source:** [hellointerview.com — Kafka Deep Dive](https://www.hellointerview.com/learn/system-design/deep-dives/kafka)

## What Kafka Is

**Apache Kafka** is an open-source distributed **event streaming platform** used by ~80% of the Fortune 100. It can be used either as a **message queue** or as a **stream processing system**. It excels at high performance, scalability, and durability — engineered to handle vast volumes of data in real time, and (with appropriate replication and acknowledgment settings) it provides strong guarantees against message loss.

## Motivating Example (World Cup)

A real-time match-stats site: events (goals, bookings, substitutions) go on a queue. The **producer** puts events on the queue; the **consumer** reads them and updates the website. Scale the tournament up and one queue server + one consumer can't keep up. Key ideas that fall out:

- Randomly distributing events across queue servers breaks ordering (goals before kickoff!). Instead, distribute by *game* — all events for one game live on the same queue and stay ordered. This is the core Kafka idea: **messages are distributed across partitions using a partitioning strategy**, and choosing the right key is critical for ordering.
- Add more consumers via a **consumer group**: each partition is assigned to exactly one consumer in the group, so each event is processed by a single consumer (at-least-once semantics mean reprocessing is possible on failure, but a message is never split across consumers).
- Separate sports (soccer vs basketball) via **topics**: consumers subscribe only to the topics they care about.

## Terminology and Architecture

- **Broker**: an individual server (physical or virtual) in the Kafka cluster; stores data and serves clients. More brokers = more storage and capacity.
- **Partition**: an ordered, **immutable, append-only sequence of messages** — like a log file. Partitions are how Kafka scales and parallelizes consumption.
- **Topic**: a *logical* grouping of partitions; you publish to and consume from topics. Always multi-producer. (Topic = logical grouping of messages; partition = physical grouping.)
- **Producers** write to topics; **consumers** read from them. Kafka doesn't care what the data is — it just stores and serves bytes.

**Queue vs stream** — the distinction is minor; both track progress via offset commits. As a queue: each message is processed by one consumer in a group, then effectively "consumed." As a stream: the log is retained and replayable, multiple consumer groups read the same data independently, and consumers process continuously.

## How Kafka Works

### Messages and Partitioning

A message (record) has four optional fields: **value** (payload), **key**, **timestamp**, and **headers**. The **key determines the partition** (ordering within a partition is by offset, not timestamp). Publishing is two steps:

1. **Partition determination**: hash the key → partition. Same key ⇒ same partition ⇒ order preserved at partition level. No key ⇒ default partitioner (modern clients use a "sticky" partitioner: batch to one partition, then rotate).
2. **Broker assignment**: cluster metadata (maintained by the controller) maps partitions to brokers; the producer sends directly to the right broker.

### Append-Only Log

Each partition is an append-only log — Kafka is a **distributed commit log**. Benefits:

1. **Immutability**: messages are never modified in place (only removed via retention or compaction) — simplifies replication, speeds recovery, avoids consistency issues.
2. **Efficiency**: append-only writes minimize disk seeks.
3. **Scalability**: add partitions across brokers; replicate each for fault tolerance.

### Offsets and Delivery Semantics

Each message gets a sequential **offset** in its partition. Consumers track and periodically **commit offsets** back to Kafka so they can resume after restarts. Default is **at-least-once**: crash after processing but before committing ⇒ the message is reprocessed. **Exactly-once** is possible but needs idempotent producers + transactional APIs.

### Replication (Leader–Follower)

- Each partition has a **leader replica** on some broker handling all writes (and by default reads; Kafka 2.4+ allows follower reads for latency).
- **Follower replicas** on other brokers passively replicate the leader and stand by to take over.
- The **controller** monitors broker health and promotes an in-sync follower on leader failure.

### Pull-Based Consumption

Consumers **poll** brokers rather than being pushed to. Deliberate design: consumers control their consumption rate, failure handling is simpler, slow consumers aren't overwhelmed, and batching is efficient.

## When to Use Kafka in Your Interview

**As a message queue**, when:

- Processing can be **asynchronous** (e.g. YouTube: serve SD video immediately, queue a transcoding job).
- Messages must be **processed in order** (e.g. Ticketmaster virtual waiting queue — admit users in arrival order).
- You want to **decouple producer and consumer** so they scale independently (producer faster than consumer; one microservice can't take down another).

**As a stream**, when:

- You need **continuous, immediate processing** of data as a real-time flow (e.g. Ad Click Aggregator real-time aggregation).
- Messages must be processed by **multiple consumers simultaneously** (e.g. FB Live Comments — Kafka as pub/sub fanning comments to many consumers).

## What to Know for Interviews

(Article's note: junior/mid-level engineers likely won't need the deeper material below; seniors should know some; staff+ most.)

### Scalability

**Single-broker limits (rough estimates)**: no hard message size limit (`message.max.bytes`) but keep messages **< 1MB**; a good broker stores ~**1TB** and handles up to ~**1M messages/sec**. If your design fits within that, scaling may not even be a conversation.

**Anti-pattern**: storing large blobs in Kafka. Kafka is not a database or file store. For YouTube-style processing, put the video in S3 and put a **pointer message** (S3 location) in Kafka.

Scaling strategies:

1. **Horizontal scaling with more brokers** — but ensure topics have **enough partitions** to use the new brokers; under-partitioning wastes them.
2. **Partitioning strategy** (the main interview focus): choose the message key. `partition = hash(key) % num_partitions` (murmur2 by default). A bad key ⇒ hot partitions. Good keys distribute evenly. You usually scale *topics* (per-topic partition counts) rather than the cluster; managed services (Confluent Cloud, AWS MSK) handle much of the rest.

**Hot partitions** (interviewers love this — e.g. Ad Click Aggregator partitioned by ad ID when Nike launches a LeBron ad):

1. **No key** — default/sticky partitioning spreads load evenly, but you lose ordering of related messages. Fine if ordering doesn't matter.
2. **Random salting** — append a random number/timestamp to the key; spreads load but complicates consumer-side aggregation.
3. **Compound key** — ad ID + region or user-ID segment; spreads traffic when you can find independently-varying attributes.
4. **Back pressure** — slow the producer (check partition lag; managed services often have this built in).

### Fault Tolerance and Durability

- Durability via replication: writes go to the leader, then followers. Producer **`acks=all`** waits for all **in-sync replicas (ISR)** — strongest durability.
- **Replication factor 3** is common (1 leader + 2 followers): one broker can fail with no data loss.
- "**Kafka is always available, sometimes consistent.**" "What if Kafka goes down?" is not very realistic — you may even gently push back.
- **What if a consumer goes down?** (the realistic question):
  1. **Offset management** — restart from last committed offset; nothing missed, some possibly reprocessed (at-least-once).
  2. **Rebalancing** — the consumer group redistributes the dead consumer's partitions among the survivors.
- **When to commit offsets** is the interview tradeoff: e.g. in Web Crawler, don't commit until the raw HTML is safely in blob storage. The more work per message, the more you redo on failure — keep consumer work small (Web Crawler split into download phase + parse phase).

### Retries and Errors

- **Producer retries**: network/broker failures happen; configure automatic retries (e.g. `retries: 5`, `initialRetryTime: 100`) and enable **idempotent producer** mode so retries don't create duplicates.
- **Consumer retries**: Kafka does **not** support consumer retries out of the box (SQS does!). Common pattern: publish failed messages to a **retry topic** processed by a separate consumer; after too many attempts, move to a **dead letter queue (DLQ)** for later investigation. (The Web Crawler breakdown chose SQS over Kafka precisely for built-in retries + DLQ.)

### Performance Optimizations

1. **Batch messages** in a single `send()` (producers batch over the network anyway; `sendBatch()` spans topics).
2. **Compress messages** (GZIP, Snappy, LZ4) — smaller payloads, faster transfer.
3. **Biggest lever: partition key choice** — maximize parallelism with even distribution. In an interview, start with the partitioning strategy.

### Retention Policies

Configured via `retention.ms` and `retention.bytes`; **default retention is 7 days**. Longer retention is possible (for replay/long storage designs) — just mind storage cost and performance.

## Summary

Kafka is a distributed event streaming platform: producers send messages to topics; consumers read them; messages live in ordered, immutable partitions replicated across brokers. Great for real-time processing and async queuing. In interviews: lead with your **partitioning strategy** and how you'll handle **hot partitions**, know the at-least-once/offset-commit mechanics, and remember — Kafka is always available, sometimes consistent.
