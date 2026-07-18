# Delivery Framework

**Source:** [https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery](https://www.hellointerview.com/learn/system-design/in-a-hurry/delivery)

The recommended step-by-step structure (with timings) for a ~45-minute system design interview, built by FAANG managers and staff engineers.

---

## Why a Framework?

- The easiest way to fail a system design interview is to **not deliver a working system**. This is the **most common reason mid-level candidates fail**, and it usually gets labeled as vague "time management" problems.
- The fix usually isn't working twice as fast — it's **focusing on the right things** in the right order.
- A firm structure keeps you thinking linearly, prevents scope creep, and gives you a clear path to fall back on when you're nervous or overwhelmed. Interviewers aren't explicitly grading "delivery" (it gets bucketed into communication), but candidates who follow a structure perform measurably better.

## The Framework at a Glance

| Step | Time | Output |
|---|---|---|
| 1. Requirements | ~5 min | Top-3 functional reqs + 3-5 quantified non-functional reqs |
| 2. Core Entities | ~2 min | Bulleted list of the main entities |
| 3. API / System Interface | ~5 min | Endpoint contract between users and system |
| 4. [Optional] Data Flow | ~5 min | Ordered list of processing steps (data-processing systems only) |
| 5. High-Level Design | ~10-15 min | Boxes-and-arrows architecture satisfying the API |
| 6. Deep Dives | ~10 min | Hardening for non-functional reqs, edge cases, bottlenecks |

---

## 1. Requirements (~5 minutes)

Goal: get a clear, prioritized understanding of what you're being asked to design. Split into two parts.

### 1a) Functional Requirements

- "Users/Clients should be able to..." statements — the **core features**. Discuss these first.
- Treat it as a back-and-forth: ask targeted questions as if the interviewer were a client or product manager ("does the system need to do X?", "what happens if Y?").
- **Prioritize ruthlessly: identify the top 3 features.** These systems have hundreds of features; a long list hurts more than it helps, and top FAANGs directly evaluate your ability to focus on what matters. The rest of the interview is about satisfying the requirements you pick here.

Examples:
- Twitter: post tweets; follow other users; see tweets from followed users.
- A cache: insert items; set expirations; read items.

### 1b) Non-Functional Requirements

- "The system should be (able to)..." statements about system **qualities**.
- Put them **in context and quantify** them. "Low latency" is meaningless (everything should be); "low latency search, < 500ms" identifies where it matters and gives a target.
- Pick the **top 3-5** most relevant to this system.

Twitter examples:
- Highly available, prioritizing availability over consistency
- Scales to 100M+ DAU
- Low latency feed rendering, under 200ms

**Checklist for finding non-functional requirements:**
1. **CAP theorem** — prioritize consistency or availability? (Partition tolerance is a given in distributed systems.)
2. **Environment constraints** — mobile battery, limited memory, limited bandwidth (e.g. video over 3G)?
3. **Scalability** — unique scaling needs? Bursty traffic, holiday spikes, read-vs-write ratio (which needs to scale more)?
4. **Latency** — how fast must responses be, especially for computation-heavy requests (e.g. Yelp search)?
5. **Durability** — how bad is data loss? (Social network: tolerable; banking: not.)
6. **Security** — data protection, access control, regulatory compliance.
7. **Fault tolerance** — redundancy, failover, recovery mechanisms.
8. **Compliance** — legal/regulatory/industry standards, data protection laws.

### 1c) Capacity Estimation — mostly skip it

- Contrarian but important: upfront back-of-the-envelope math is **often unnecessary**. Computing storage/DAU/QPS just to conclude "it's a lot" gives the interviewer no signal beyond arithmetic.
- **Do calculations only when they directly influence a design decision**, and say so explicitly: "I'll skip estimation upfront and do the math during design when it matters."
- Example where it matters: a Top-K trending-topics system — estimating the number of topics decides whether one min-heap instance suffices or you must shard it, which reshapes the design.
- Still worth [learning to estimate quickly](https://www.hellointerview.com/blog/mastering-estimation) — it lets you reason through tradeoffs fast. Most people are bad at mental arithmetic under pressure; that's fine.

## 2. Core Entities (~2 minutes)

- Jot a short bulleted list of the core entities your API will exchange and your system will persist. Present it as a **first draft**.
- Don't build the full data model yet — "you don't know what you don't know." You'll discover entities and relationships as you design; flesh out columns/fields later during high-level design.
- Twitter example: **User, Tweet, Follow**.
- Questions to find entities:
  - Who are the actors in the system? Do they overlap?
  - What nouns/resources are needed to satisfy the functional requirements?
- Choose good names — some interviewers use naming as signal (naming things is famously one of the hardest problems in CS).

## 3. API or System Interface (~5 minutes)

Define the contract between your system and its users before designing. Often maps directly to functional requirements (but not always). It guides the high-level design.

**Protocol choice — don't overthink it:**
- **REST** — HTTP verbs (GET, POST, PUT, DELETE) for CRUD on resources. **Default choice for most interviews.**
- **GraphQL** — clients specify exactly the data they want (avoids over/under-fetching). Choose when you have diverse clients with different data needs.
- **RPC (e.g. gRPC)** — action-oriented, faster than REST; use for internal service-to-service APIs when performance is critical.
- Real-time features additionally need **WebSockets or Server-Sent Events** — but design the core API first.

Twitter REST example:

```
POST /v1/tweets
body: { "text": string }

GET /v1/tweets/{tweetId} -> Tweet

POST /v1/follows
body: { "followee_id": string }

GET /v1/feed -> Tweet[]
```

Conventions and security tips:
- Resources are **plural nouns** (`/tweets`, not `/tweet`).
- **Derive the current user from the auth token in the request header** — never from request bodies or path parameters. Never trust user-supplied IDs for identity; always authenticate.

## 4. [Optional] Data Flow (~5 minutes)

- Only for systems (especially **data-processing systems**) with a long sequence of actions on inputs to produce outputs. Otherwise, skip.
- Define it as a simple ordered list; use it to inform the high-level design.
- Web crawler example: 1) Fetch seed URLs → 2) Parse HTML → 3) Extract URLs → 4) Store data → 5) Repeat.

## 5. High-Level Design (~10-15 minutes)

- Draw boxes and arrows: servers, databases, caches, queues, etc. (the [Key Technologies](https://www.hellointerview.com/learn/system-design/in-a-hurry/key-technologies) chapter covers the common components).
- **Goal: an architecture that satisfies the API you designed** (and therefore the requirements). Effective tactic: go endpoint by endpoint and build the design up sequentially.
- **Stay simple first.** The most common trap is layering complexity (caches, queues) too early and never completing a working solution. When you spot an optimization opportunity, make a verbal callout, write a short note, and move on — complexity belongs in the deep dives.
- **Narrate as you draw**: be explicit about how data flows through the system and what state changes (DB, cache, queue) with each request, from API request to response.
- When a request reaches the persistence layer, start documenting the **relevant** columns/fields next to the database on the diagram — keeps schema near the components and easy to evolve. Skip types; skip obvious columns (interviewers know a User table has name/email/password hash). Only write down what's design-relevant.
- Logistics: ask your recruiter what whiteboarding software you'll use (e.g. Excalidraw) and **practice with it beforehand** so you're not fumbling live.

## 6. Deep Dives (~10 minutes)

Use the remaining time to harden your design by:
- Ensuring it meets **all non-functional requirements**
- Addressing **edge cases**
- Identifying and fixing **bottlenecks**
- Improving the design based on **interviewer probes**

Examples (Twitter):
- "Scale to 100M+ DAU" → discuss horizontal scaling, adding caches, database sharding, updating the diagram as you go.
- "Low-latency feeds" → the most interesting Twitter problem: **fanout-on-read vs fanout-on-write** plus caching.

Seniority calibration:
- **Mid-level**: expect the interviewer to jump in and point at areas to improve; responding well is enough.
- **Senior+**: expected to proactively identify weak spots and lead the deep-dive discussion yourself.

**Don't talk over your interviewer.** Even senior candidates must leave room for questions and probes — the interviewer has specific signals to collect, and monologuing means missing them and hurting your communication/collaboration score.
