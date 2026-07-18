---
tags: [system-design, interview, api, graphql, bff]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [REST vs GraphQL frontend, BFF, cursor pagination frontend]
---

# Network and API Design for Frontend

## Maturity Target

- Priority: #must-know
- Study time: 45 minutes
- Interview signal: Design the network API a frontend consumes — endpoint shape, REST vs GraphQL, pagination, payload discipline — and defend it from the client's needs.
- Production signal: You can push back on an API that causes over-fetching, waterfalls, or N+1 client requests.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[30 - Backend System Design/03 - API Design|Backend API Design]]

## Source Anchors

- [GraphQL — Learn](https://graphql.org/learn/)
- [MDN — HTTP methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
- [Backends for Frontends pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends)

## 1. Concept

Simple version: RADIO's Interface phase includes the *network* API — even with the server as a black box, you design the contract the client needs. The general rules live in [[30 - Backend System Design/03 - API Design|Backend API Design]]; this note is the client's-eye view.

The frontend-facing decisions:

- **REST vs GraphQL — from the client's data shape.** REST is simple, cacheable at the HTTP layer, and great when screens map to resources. GraphQL shines when a screen composes many resources with varying fields (avoids over/under-fetching and request waterfalls) — at the cost of HTTP-cacheability and added client complexity. Choose from how varied and nested the client's needs are, not fashion.
- **Over-fetching / under-fetching / waterfalls** — the three client pains. Over-fetch: the endpoint returns fields the screen ignores (mobile payload waste). Under-fetch: the screen needs data across several endpoints → a request waterfall. GraphQL or a **BFF** (Backend-for-Frontend that aggregates and reshapes for this client) fixes both.
- **Pagination — client lens.** Cursor for feeds/infinite scroll (stable under inserts); offset for jump-to-page tables. ([[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]].)
- **Payload discipline** — request only needed fields, lean shapes, GET for cacheable reads so the CDN/browser cache does scaling work.
- **Real-time channel** — REST/GraphQL for request/response, plus SSE/WebSockets for push ([[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]]).

> [!tip] The BFF is the frontend's leverage point: one thin service that aggregates microservices, trims payloads, and shapes responses per screen — turning three chatty round trips into one. It's the client-side answer to over/under-fetching when you can't change the underlying services (and the frontend cousin of an [[30 - Backend System Design/11 - Deep-Dive Technologies|API gateway]]).

## 2. Why It Matters

Even treating the server as a black box, the API contract decides client performance: over-fetching wastes mobile bandwidth, under-fetching creates waterfalls that delay first render, and non-cacheable shapes throw away the cheapest scaling lever. Interviewers want to see you design the contract from the client's needs and push back on a bad one — a senior collaboration signal.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a profile screen makes five sequential requests — user, then posts, then each post's comments count, then followers, then mutual-friends — and renders slowly because each waits on the previous.

Trace: **under-fetching → request waterfall.** The REST endpoints are resource-shaped, but the screen needs a composed view, so the client stitches it with dependent calls, each adding a round trip's latency.

Fix options with tradeoffs: (a) **GraphQL** — one query declares the whole tree, server resolves it, one round trip; costs HTTP-cache and adds resolver/N+1 concerns server-side. (b) **BFF endpoint** `GET /screens/profile/:id` that aggregates server-side and returns exactly the screen's shape; keeps REST simplicity and cacheability, costs a new service to own. (c) **Parallelize** independent calls (`Promise.all`) as a stopgap — no new infra, but still multiple requests and the payload waste remains.

Tradeoff summary: GraphQL and BFF both collapse the waterfall; GraphQL is client-flexible but harder to cache, BFF is cache-friendly but screen-coupled. Parallelizing is the cheap partial fix.

## 4. Interview Answer

Short answer:

> I design the network API from the client's data shape. REST when screens map to resources and I want HTTP caching; GraphQL when screens compose many resources with varying fields, to kill over-fetching and waterfalls. When I can't change the services, a BFF aggregates and trims per screen. Cursor pagination for feeds, offset for tables, lean GET responses so the CDN caches reads, and a separate push channel for real-time.

Deeper answer:

> The three client pains are the frame: over-fetching wastes mobile payload, under-fetching creates dependent-request waterfalls that block first paint, and non-cacheable shapes waste the cheapest scaling lever. GraphQL solves the first two by letting the client declare its tree, but I'd name the costs — HTTP cache loss and server N+1 risk. A BFF is often the pragmatic middle: one screen-shaped, cacheable endpoint that hides service chatter, at the cost of a service to maintain and a coupling to the screen. Either way I design the contract from what the screen needs and I'm willing to push back on an API that forces waterfalls.

## 5. Practice

1. <details><summary>A screen needs data from six services and renders slowly. REST-with-BFF or GraphQL — what decides it?</summary>Whether you control an aggregation layer and how varied clients are. If one screen (or a few) needs a fixed composed shape and you want HTTP caching, a BFF endpoint is simplest. If many clients need different field subsets of a rich graph, GraphQL's client-declared queries pay off. Both remove the waterfall; the trade is cacheability/simplicity (BFF) vs client flexibility (GraphQL).</details>
2. <details><summary>Why does GraphQL cost you HTTP-layer caching?</summary>GraphQL queries are typically POSTs to a single `/graphql` endpoint, so CDNs and browser caches — which key on URL + method and cache GETs — can't cache per-query out of the box. You regain caching with persisted queries or an application-level cache, but you lose the free HTTP/CDN layer REST GETs get.</details>
3. <details><summary>When is over-fetching actually fine?</summary>When the extra fields are small, the endpoint is highly cacheable, and reuse across screens outweighs the waste — a shared cached `GET /user/:id` used by many views may be better over-fetched-but-cached than many bespoke lean endpoints. On constrained mobile with large unused fields, trim it (GraphQL/BFF). It's a payload-vs-reuse trade, decided by the requirement.</details>

## 6. Real-World Use Cases

### BFF route handler — one screen, one request

A profile screen needs user, recent posts, and follower count from three services. Fanning out three round-trips from the browser is slow and leaks the backend shape; a Next.js Route Handler aggregates server-side and returns exactly the screen's shape.

```ts
// app/api/profile/[id]/route.ts  — the BFF
export async function GET(_req: Request, { params }: { params: { id: string } }) {
  const [user, posts, followers] = await Promise.all([
    getUser(params.id), getRecentPosts(params.id), getFollowerCount(params.id),
  ]);
  return Response.json({ user, posts, followerCount: followers });  // client makes ONE call
}
```

The client gets a purpose-built payload; the fan-out and its latency live on the server. See [[30 - Backend System Design/03 - API Design|Backend API Design]].

### Cursor pagination for an activity feed

An active feed can't use offset (items insert at the top and shift every page). The client sends the last cursor back and reads the next one — stable under concurrent inserts.

```ts
async function loadMore(cursor: string | null) {
  const res = await fetch(`/api/feed?limit=20${cursor ? `&cursor=${cursor}` : ""}`);
  const { items, nextCursor } = await res.json();
  return { items, nextCursor };   // pass nextCursor to the next call; null = end
}
```

Cursor encodes a stable position, so no duplicates or skips while scrolling. See [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Designing an Infinite Scroll Feed]].

### Collapsing a request waterfall

Independent calls awaited in sequence serialize needlessly — a pure client fix, no backend change. `Promise.all` runs them in parallel.

```ts
// Waterfall: 3 × latency
const user = await getUser(id);
const prefs = await getPrefs(id);     // didn't need user
const feed = await getFeed(id);       // didn't need prefs
// Parallel: 1 × latency
const [user2, prefs2, feed2] = await Promise.all([getUser(id), getPrefs(id), getFeed(id)]);
```

Only chain calls that truly depend on the previous result. See [[08 - Async JavaScript/02 - Promises|Promises]].

## Related Notes

- [[30 - Backend System Design/03 - API Design|Backend API Design]]
- [[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]]
- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]]
- [[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]]
