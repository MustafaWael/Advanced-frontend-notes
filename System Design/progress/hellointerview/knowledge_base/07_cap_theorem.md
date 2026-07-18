# CAP Theorem

**Source:** [hellointerview.com — CAP Theorem](https://www.hellointerview.com/learn/system-design/core-concepts/cap-theorem)

CAP theorem is a routine point of confusion but foundational to how you approach a design — it belongs in the **non-functional requirements** phase of the interview.

## What is CAP Theorem?

In a distributed system you can only have two of three:

- **Consistency:** all nodes see the same data at the same time; after a write to one node, all subsequent reads from any node return the updated value.
- **Availability:** every request to a non-failing node gets a response — without a guarantee it's the most recent data.
- **Partition Tolerance:** the system keeps operating despite arbitrary message loss / network partitions between nodes.

Note: CAP "consistency" is quite different from ACID consistency. Confusing, yes.

Key insight for interviews: **partition tolerance is a must** — network failures will happen. So CAP reduces to a single choice: **when a partition occurs, do you prioritize consistency or availability?**

## Example: Two Servers, One Profile Update

Website with servers in the USA and Europe. User A (USA) updates their display name; the update replicates to Europe; User B (Europe) sees the new name. Then a network partition cuts the USA–Europe link. When User B views User A's profile:

- **Option A (consistency):** return an error — can't guarantee freshness.
- **Option B (availability):** show potentially stale data.

Here the answer is clear: show the old name rather than an error — stale beats nothing.

### When to Choose Consistency

Systems where brief inconsistency is catastrophic:

1. **Ticket booking:** User A books seat 6A; during a partition User B sees it available and books it too — two people, one seat.
2. **E-commerce inventory:** one toothbrush left shown as available to multiple users → overselling.
3. **Financial systems:** stock trading needs accurate order books; stale data → trades at wrong prices.

### When to Choose Availability

The majority of systems tolerate temporary inconsistency (**eventual consistency** — the system converges after seconds/minutes):

1. **Social media:** old profile picture for a few minutes is fine.
2. **Content platforms (Netflix):** stale movie description temporarily isn't catastrophic.
3. **Review sites (Yelp):** slightly outdated restaurant hours beat no information.

Litmus test: **"Would it be catastrophic if users briefly saw inconsistent data?"** Yes → consistency. No → availability.

## CAP in System Design Interviews

Discuss it early: after aligning on functional requirements, when defining non-functional requirements, ask "does this system prioritize consistency or availability?" — it meaningfully shapes the design.

**If prioritizing consistency**, your design might include:
- **Distributed transactions:** keep multiple stores (cache + DB) in sync via two-phase commit — complexity and higher user latency in exchange for cross-node consistency.
- **Single-node solutions:** one database instance = single source of truth, no propagation issues (limits scalability).
- **Technology choices:** traditional RDBMSs (PostgreSQL, MySQL), Google Spanner, DynamoDB in strong-consistency mode.

**If prioritizing availability:**
- **Multiple replicas** with asynchronous replication — reads served from any replica even if slightly behind (better read performance/availability at the cost of staleness).
- **Change Data Capture (CDC):** track primary-DB changes and propagate asynchronously to replicas, caches, and other systems; the primary stays available while updates flow eventually.
- **Technology choices:** Cassandra, DynamoDB (multi-AZ configuration), Redis clusters.

Most modern distributed databases can be configured either way — the point is knowing which to choose for the use case.

## Advanced Considerations (senior/staff level)

The choice isn't binary system-wide — real systems mix models **per feature**:

- **Ticketmaster:** strong consistency for booking a seat (no double-booking); availability for viewing event details (slightly stale descriptions OK). Say: "I'll prioritize consistency for booking transactions but optimize for availability for browsing/viewing."
- **Tinder:** consistency for matching (both users swiping right at ~the same time should both see the match immediately); availability for viewing profiles (slightly outdated photo is fine).

### Different Levels of Consistency

- **Strong consistency:** all reads reflect the most recent write. Most expensive for performance; required for absolute accuracy (bank balances).
- **Causal consistency:** related events appear in the same order to all users (comments appear after the post they're on).
- **Read-your-own-writes:** users always see their own updates immediately; others may see older versions (social profile edits).
- **Eventual consistency:** the system converges over time; temporary inconsistency allowed (DNS). The most relaxed model — the default of most distributed databases and the implicit choice when prioritizing availability.

## Conclusion

CAP sets the stage for your whole design but needn't be complicated. Ask: **"Does every read need to see the most recent write?"** Yes → prioritize consistency. No → prioritize availability.
