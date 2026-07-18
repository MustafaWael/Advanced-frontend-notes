---
tags: [system-design, backend, consistency, interview]
module: "30 - Backend System Design"
priority: important
status: not-started
aliases: [CAP theorem, eventual consistency, consistency spectrum]
---

# CAP and Consistency

## Maturity Target

- Priority: #important
- Study time: 35 minutes
- Interview signal: State the CAP tradeoff precisely (it's about behavior *under partition*), extend it with PACELC (latency-vs-consistency when there's no partition), tune consistency with quorum (R+W>N), place a design on the consistency spectrum, and connect eventual consistency to the frontend's optimistic-UI window.
- Production signal: You can explain why a feature is "eventually consistent" to a PM and design the UI for the staleness window.
- Dependencies: [[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling and Databases]]

## Source Anchors

- [HelloInterview — CAP Theorem](https://www.hellointerview.com/learn/system-design/core-concepts/cap-theorem)
- [Jepsen — Consistency models](https://jepsen.io/consistency)

## 1. Concept

Simple version: when the network splits so two replicas can't talk (a **partition**), you must choose — keep serving with possibly-stale data (**Availability**) or refuse/stall to avoid disagreement (**Consistency**). You can't have both *during* a partition.

**But "no partition ⇒ you get both" is the trap — that's what PACELC corrects.** CAP only describes the partition case; it says nothing about the 99.9% of the time the network is healthy. PACELC extends it: **if Partitioned, choose Availability or Consistency; Else (normal operation), choose Latency or Consistency.** Even with no partition, keeping replicas strongly consistent means every write waits for acknowledgement from other replicas (higher latency), so systems that replicate asynchronously are trading consistency for latency *all the time* — that async replication is exactly why the profile-photo example below has a staleness window with no partition in sight. DynamoDB and Cassandra are **PA/EL** (available under partition, low-latency otherwise, both eventual); a strongly-consistent store is **PC/EC**. Naming PACELC shows you know CAP describes only half the picture.

**Quorum — the dial between C and A/L.** Replicated stores let you tune consistency per operation with three numbers: **N** replicas, **W** acknowledgements required to commit a write, **R** replicas consulted for a read. The key inequality: **if R + W > N, every read set overlaps every write set**, so a read is guaranteed to see the latest acknowledged write (strong-ish consistency). Examples with N=3: `W=3, R=1` = fast reads, slow/fragile writes (all replicas must ack); `W=1, R=3` = fast writes, slower reads; `W=2, R=2` (R+W=4>3) = balanced quorum, the common default. Set `R+W ≤ N` (e.g., `W=1, R=1`) and you get maximum availability/latency but only eventual consistency — a read can miss a just-committed write. Caveat: this is the *strict* quorum guarantee; "sloppy quorums" with hinted handoff (Dynamo-style) relax it to stay available during partitions, which can resurrect stale or conflicting values you then reconcile.

The nuance interviewers want: CAP is binary in name but consistency is really a **spectrum**:

- **Strong / linearizable** — every read sees the latest write. Needed for money, inventory, unique usernames.
- **Read-your-own-writes** — you see your writes immediately; others may lag. Common UX default.
- **Eventual** — replicas converge "soon"; reads may be stale meanwhile. Feeds, likes, view counts, metrics.

Choosing availability + eventual consistency is the right call for most read-heavy consumer features — a like count off by one for two seconds is fine; a bank balance is not.

> [!tip] Frontend mirror: **optimistic UI is a deliberately created eventual-consistency window.** You show the like as done before the server confirms, making the client a briefly-inconsistent replica, then reconcile (or roll back on failure). CAP's abstract spectrum becomes concrete UX here — see [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]] and [[28 - Frameworks and Application Architecture/06 - Server State|Server State]].

## 2. Why It Matters

"Is it CP or AP?" is a stock question, and the weak answer treats CAP as a permanent property rather than partition-time behavior. The strong answer picks a consistency *level per feature* and justifies it from the product — and, as a frontend engineer, translates "eventually consistent" into a designed UI state instead of a bug report.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a user updates their profile photo; it saves, but for a minute some parts of the app still show the old photo. A bug is filed.

Trace: not a bug — an **eventual-consistency window**. The write went to the primary; reads are served from replicas (or a cache) that haven't caught up. The system chose availability/scale (serve fast from replicas) over strong consistency (read the primary every time).

Fix depends on the requirement, not "make it consistent": (a) **read-your-own-writes** — after a user's own mutation, read from the primary or optimistically update their client cache so *they* see it instantly while others lag; (b) invalidate the cache on write to shrink the window; (c) if it truly must be globally instant, pay for strong consistency (read primary, or synchronous replication) and accept the latency/availability cost.

Tradeoff: strong consistency costs latency and availability (a partition now blocks reads); eventual consistency costs a visible staleness window that the UI must handle gracefully rather than pretend away.

## 4. Interview Answer

Short answer:

> CAP says that during a network partition you choose consistency or availability — you can't have both while replicas can't communicate; without a partition you have both. In practice I pick a consistency level per feature: strong for money, inventory, and uniqueness; eventual for feeds, counts, and metrics where a brief staleness window is acceptable and availability matters more.

Deeper answer:

> The spectrum between strong and eventual is where real designs live — read-your-own-writes is the common UX compromise: route a user's own reads to the primary or update their client cache optimistically so they see their change immediately while everyone else converges eventually. On the frontend that's literally optimistic UI: I create a controlled eventual-consistency window on the client, show unconfirmed state, and reconcile or roll back — so I design the staleness into the UX instead of treating replica lag as a defect.

## 5. Practice

1. <details><summary>Why is "our system is CP" an imprecise statement?</summary>CAP only forces a choice *during a partition*. With no partition a CP system is also available. The precise claim is "when partitioned, we prioritize consistency (reject/stall) over availability" — and most real systems choose a consistency level per operation, not one global mode.</details>
2. <details><summary>Which features lean C and which lean A, and why?</summary>Lean C (strong): payments, inventory/seat booking, unique usernames — disagreement causes real harm ([[30 - Backend System Design/10 - The Seven Access Patterns|contention]]). Lean A (eventual): feeds, likes, view counts, notifications — staleness is cosmetic and availability/scale matter more.</details>
3. <details><summary>How is optimistic UI an instance of eventual consistency?</summary>The client applies the change locally before the server confirms, so the screen and the server temporarily disagree — a client-side replica lag. Reconciliation is the server response: confirm (converge) or error (roll back). Same shape as replica convergence, with the reconciliation surfaced as UX.</details>
4. <details><summary>CAP says nothing happens when the network is healthy — so why does the profile photo still go stale with no partition?</summary>Because the tradeoff PACELC names — "Else, Latency vs Consistency" — is always live. Reads served from asynchronously-updated replicas/caches lag the primary even with a perfect network; the system chose low read latency over strong consistency in the normal case. CAP only covers the partition case; PACELC covers the other 99.9% of the time.</details>
5. <details><summary>With N=3 replicas, what W and R give you a read guaranteed to see the latest write, and why?</summary>Any R and W where <strong>R + W &gt; 3</strong> — e.g., W=2, R=2. The write commits to 2 replicas and the read consults 2; with only 3 total, those sets must share at least one replica, so the read is guaranteed to touch a copy holding the newest acknowledged write. Set R+W ≤ N (e.g., W=1,R=1) and reads can miss recent writes — eventual consistency, but lower latency and higher availability.</details>

## Related Notes

- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[28 - Frameworks and Application Architecture/06 - Server State|Server State]]
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]] (Dealing with Contention)
