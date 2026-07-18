---
tags: [system-design, backend, api, interview]
module: "30 - Backend System Design"
priority: must-know
status: not-started
aliases: [REST vs GraphQL, cursor pagination, API versioning]
---

# API Design

## Maturity Target

- Priority: #must-know
- Study time: 40 minutes
- Interview signal: Design a resource-oriented API from requirements, choose REST/GraphQL/RPC deliberately, and defend cursor vs offset pagination on correctness grounds.
- Production signal: Your endpoints are cacheable and paginated by default; you know why the feed API you consume uses cursors.
- Dependencies: [[30 - Backend System Design/01 - The Delivery Framework|The Delivery Framework]], [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]]

## Source Anchors

- [HelloInterview — Core Concepts](https://www.hellointerview.com/learn/system-design/in-a-hurry/core-concepts)
- [Google — API Design Guide (resource-oriented design)](https://cloud.google.com/apis/design)
- [MDN — HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)

## 1. Concept

Simple version: model the nouns as resources, use HTTP verbs for the actions, page large collections, and don't break existing clients when you change.

The mature slice:

- **REST** — resources (`/users/42/posts`), verbs carry intent (GET safe+cacheable, POST create, PUT/PATCH update, DELETE remove), status codes carry outcome. Idempotency matters: PUT/DELETE are idempotent, POST isn't (→ idempotency keys for safe retries — the mechanics and the checkout example live in [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]], the contention angle in [[30 - Backend System Design/10 - The Seven Access Patterns|Dealing with Contention]]).
- **GraphQL** — one endpoint, the client declares the exact shape it wants. Solves over/under-fetching for rich clients; costs you HTTP-layer caching (everything is a POST to `/graphql`) and adds resolver-cost/N+1 concerns.
- **RPC / gRPC** — call remote functions with typed protobuf messages; internal service-to-service default.
- **Pagination** — never return an unbounded collection:
  - *Offset* (`?offset=20&limit=10`): simple, allows jump-to-page-N, but **drifts** — if rows are inserted/deleted mid-paging you get duplicates or skips.
  - *Cursor* (`?cursor=<opaque>&limit=10`): the cursor encodes a stable position (record id/timestamp). Correct under concurrent inserts; can't jump to an arbitrary page. Right for feeds and infinite scroll.
- **Versioning** — URI (`/v2/...`), header, or param; the point is to evolve without breaking existing clients.
- **Security** — authN/authZ at the edge, rate limiting/throttling per client.

> [!tip] Frontend mirror: the cursor-vs-offset decision is one API contract with two consumers. The backend prefers cursors for index stability; the frontend prefers them because an infinite feed with items arriving at the top must not double-show or skip while you scroll — see [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Designing an Infinite Scroll Feed]].

## 2. Why It Matters

The API is the boundary you actually integrate against as a frontend engineer. Knowing *why* an endpoint is shaped the way it is — why it's a GET (cacheable), why it's cursor-paginated (stable), why writes want idempotency keys (safe retries) — turns "the backend gave me a weird API" into a conversation you can have on equal footing.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an infinite feed occasionally shows a post twice and sometimes skips one, especially when the feed is active.

Trace: the endpoint is offset-paginated (`?offset=40&limit=20`). Between fetching page 3 and page 4, two new posts arrive at the top and shift everything down by two — so offset 60 now points two records earlier than it did, re-serving rows you already showed; a deletion does the reverse and skips rows. Offset addresses a *position* in a moving list.

Fix: switch to cursor pagination. The client sends back the opaque `next_cursor` from the previous page; the server resolves it to "everything after this exact record," which is stable no matter how many items were inserted above.

```http
GET /feed?limit=20            → { items: [...], next_cursor: "eyJpZCI6..." }
GET /feed?limit=20&cursor=eyJpZCI6...   → next stable slice
```

Tradeoff: you lose "jump to page 47" (fine for a feed, wrong for a paginated admin table where offset is the better fit). Cursors also leak an ordering assumption — change the sort and old cursors are meaningless.

## 4. Interview Answer

Short answer:

> Model resources with proper HTTP verbs and status codes, make reads cacheable GETs, and paginate every collection. For feeds and anything with concurrent inserts I use cursor pagination because it's stable under change; offset is fine for static, jump-to-page data. REST at the public edge, gRPC internally, GraphQL when clients need flexible field selection at the cost of HTTP caching.

Deeper answer:

> The non-obvious depth is idempotency and cache-friendliness. Idempotent verbs (PUT/DELETE) can be safely retried; POST can't, so create-endpoints take an idempotency key to make retries safe under network failure — the same double-submit problem the frontend guards with request dedup. And GET-with-lean-payloads isn't just tidiness: it's what lets a CDN or the browser cache the response, which is often a bigger performance win than any server optimization.

## 5. Practice

1. <details><summary>When is offset pagination the right choice over cursor?</summary>Static or slowly-changing datasets where users need random access — "jump to page 12" in an admin report, search results with page numbers. Cursor can't express arbitrary page jumps; offset can, and drift doesn't matter if the data isn't shifting under you.</details>
2. <details><summary>Why does a create endpoint need an idempotency key but a delete doesn't?</summary>DELETE is naturally idempotent — deleting the same resource twice yields the same end state. POST-create isn't: a retried request after a dropped response would create a second resource. An idempotency key lets the server recognize the retry and return the original result instead of duplicating.</details>
3. <details><summary>What does GraphQL cost you that REST gives for free?</summary>HTTP-layer caching and simple observability: GraphQL queries are POSTs to one endpoint, so CDNs/browser caches and per-route metrics don't work out of the box, and you take on resolver cost and N+1 query risk. You trade that for eliminating over/under-fetching for varied clients.</details>

## 6. Real-World Use Cases

§3 covers cursor pagination; these fill the GraphQL and versioning material §1 introduces but doesn't work through.

### GraphQL field selection — collapsing round-trips

A detail screen needs a few fields from three resources. REST either over-fetches or takes three calls; one GraphQL query asks for exactly what the screen renders.

```graphql
query ProductScreen($id: ID!) {
  product(id: $id) { name price
    reviews(first: 3) { rating body }
    seller { name rating }
  }
}
```

One request, exactly the fields used — the over/under-fetch fix, at the cost of HTTP-layer caching (it's a POST to `/graphql`). See [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]].

### Non-breaking versioning during a client rollout

Native apps and cached web builds keep hitting the old contract for weeks. Ship the new shape at `/v2` and leave `/v1` serving until the old clients drain.

```http
GET /v1/orders   → { total: 4200 }                 # cents, old clients still parse this
GET /v2/orders   → { total: { amount: 42, currency: "USD" } }   # richer shape, new clients
```

Additive evolution keeps old clients alive; you retire `/v1` when analytics show its traffic is gone. See [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]].

> [!tip] Prefer additive changes (new optional fields) over new versions — a version bump is a migration you now own for every client. Reserve `/v2` for genuinely breaking shape changes.

## Related Notes

- [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Designing an Infinite Scroll Feed]]
- [[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling and Databases]]
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]] (Dealing with Contention)
