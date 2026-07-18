---
tags: [system-design, interview, data-fetching, caching, performance]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [client data layer, dedup prefetch, stale-while-revalidate]
verified_on: 2026-07-17
version_scope: "TanStack Query v5 terminology (staleTime/gcTime — gcTime was cacheTime in v4) as of 2026"
---

# Data Fetching at Scale

## Maturity Target

- Priority: #must-know
- Study time: 50 minutes
- Interview signal: Design the client data layer for a non-trivial app — caching, deduplication, pagination, prefetch, and invalidation — and rank the optimizations by the stated requirement.
- Production signal: No hand-rolled `useEffect` fetching; cache keys, staleness, and invalidation are designed, not accidental.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[28 - Frameworks and Application Architecture/06 - Server State|Server State]]

## Source Anchors

- [TanStack Query — Overview](https://tanstack.com/query/latest/docs/framework/react/overview)
- [web.dev — Stale-while-revalidate](https://web.dev/articles/stale-while-revalidate)
- [MDN — HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)

## 1. Concept

Simple version: in the Optimizations phase, most app designs live or die on how the client fetches. The single reframe that unlocks it: **server data is a cache, and caches have cache problems** ([[28 - Frameworks and Application Architecture/06 - Server State|Server State]]) — so the design is about identity, staleness, and invalidation, not about `fetch`.

The layers of a mature client data design:

- **Identity / keys** — the same logical data (`['product', 42]`) requested from many components must dedupe to one request and share one copy. Keys must include every parameter the response depends on.
- **Deduplication** — concurrent requests for the same key collapse to one in-flight promise (client-side single-flight, the twin of a server cache stampede fix — [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]).
- **Staleness policy** — `staleTime` (how long fresh) vs `gcTime` (when evicted); refetch triggers (mount, focus, reconnect, interval). **Stale-while-revalidate**: serve cached instantly, refresh in background.
- **Pagination** — cursor for feeds, offset for jump-to-page tables ([[29 - Frontend System Design/09 - Network and API Design for Frontend|API design]]).
- **Prefetch** — fetch on intent (hover, viewport, predicted next route) so navigation feels instant.
- **Invalidation** — after a mutation, which keys are now wrong? Invalidate-and-refetch (simple, chatty) vs direct cache write / optimistic update ([[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|optimistic updates]]).

> [!tip] Frontend/backend mirror: this is the backend caching design ([[30 - Backend System Design/05 - Caching|Caching]]) reflected onto the client — cache-aside becomes the query cache, single-flight becomes request dedup, TTL becomes staleTime, invalidate-on-write becomes `invalidateQueries`. Naming the symmetry is a strong signal.

## 2. Why It Matters

The `useEffect`+`useState` fetch is the most common source of races, duplicate requests, and loading-state bugs in React apps. In a design round, "how do you fetch data?" is really "do you understand the cache problems," and the interviewer pushes on staleness and invalidation specifically. It also decides bandwidth on mobile — the non-functional requirement that often dominates.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a product page and a mini-cart both fetch the same product independently. Opening the page fires the request twice; after "add to cart," the mini-cart shows the old stock count.

Trace: two data-layer failures — no **dedup** (two components, two requests for one key) and no **invalidation** (the mutation updated its own copy, not the shared cache). This is server-state-as-owned-state, the root architecture error.

```tsx
// Fix: one keyed cache — dedup + invalidation fall out structurally
const { data: product } = useQuery({
  queryKey: ['product', id],          // shared identity → one request, shared copy
  queryFn: () => api.getProduct(id, /* signal */),
  staleTime: 30_000,
});
// after add-to-cart mutation:
onSettled: () => qc.invalidateQueries({ queryKey: ['product', id] }); // both views refetch fresh
```

Tradeoff: broad invalidation (`['product']`) refetches every product variant (simple, more requests) vs surgical `setQueryData` patching (efficient, but you hand-maintain cache coherence — easy to get wrong). Optimistic updates buy instant UX at the cost of rollback logic and a window of unconfirmed truth. Choose per endpoint.

## 4. Interview Answer

Short answer:

> I design the client data layer as a cache, because server data is borrowed and stale by definition. That means request identity via keys for dedup and sharing, an explicit staleness policy with background refetch, pagination matched to the access pattern, prefetch on intent, and deliberate invalidation after mutations. Hand-rolled useEffect fetching fails on exactly those axes — races, duplicate requests, no invalidation story.

Deeper answer:

> The keys are the API: they must include every parameter the response depends on, which also structurally kills cross-key races. I separate staleTime from gcTime — when it's stale versus when it leaves memory — and I pick an invalidation strategy per mutation: invalidate-and-refetch when simplicity wins, optimistic cache writes when latency does, accepting rollback complexity. On mobile the dominant requirement is often payload and request count, so dedup, prefetch discipline, and lean responses matter more than any render optimization — and I'd say which one I'm optimizing and why.

## 5. Practice

1. <details><summary>Why must the query key include the filter/params, and what bug does omitting it cause?</summary>The key is cache identity. If `['products']` serves all filters, responses for different filters overwrite each other and a slow stale response can replace fresh data — a race made persistent by the cache. Including params gives each variant its own entry and confines every response to its key.</details>
2. <details><summary>When is prefetch-on-hover worth it, and when is it wasteful?</summary>Worth it for high-intent, likely-next navigation (hovering a product card, a link the user is about to click) where the payload is modest — it hides latency. Wasteful when hover doesn't predict navigation (dense lists, mobile with no hover) or payloads are large, where it burns bandwidth and server load for requests that won't be used.</details>
3. <details><summary>Optimistic update vs invalidate-and-refetch — which for a "like" button, which for a "submit order"?</summary>Like: optimistic — high frequency, low stakes, latency-sensitive; instant toggle with rollback on failure. Submit order: invalidate-and-refetch (or await confirmation) — money-moving and irreversible, so a window of unconfirmed truth is unacceptable; show pending, confirm from the server.</details>

## 6. Real-World Use Cases

### Infinite scroll with cursor-based `useInfiniteQuery`

A feed accumulates pages keyed by cursor; the query layer handles dedup, caching, and "is there more."

```ts
const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
  queryKey: ["feed"],
  queryFn: ({ pageParam }) => fetchFeed(pageParam),      // pageParam = cursor
  initialPageParam: null as string | null,
  getNextPageParam: (last) => last.nextCursor ?? undefined,
});
const items = data?.pages.flatMap(p => p.items) ?? [];
```

Cursor pagination keeps it stable under inserts. See [[29 - Frontend System Design/04 - Designing an Infinite Scroll Feed|Designing an Infinite Scroll Feed]].

### Prefetch-on-hover for instant navigation

High-intent hover is a signal the user is about to click — warm the cache so the next screen is already there.

```tsx
<Link
  to={`/product/${id}`}
  onMouseEnter={() => queryClient.prefetchQuery({
    queryKey: ["product", id], queryFn: () => fetchProduct(id),
  })}
/>
```

The dedup/cache machinery means the click reads a warm entry instead of waiting on the network. See [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]].

### Server prefetch + hydration (no client waterfall)

Fetch on the server during render, dehydrate, and hand the cache to the client so the first paint has data and the client doesn't re-fetch.

```tsx
// server component / route
const qc = new QueryClient();
await qc.prefetchQuery({ queryKey: ["orders"], queryFn: getOrders });
return <HydrationBoundary state={dehydrate(qc)}><Orders /></HydrationBoundary>;
// <Orders> calls useQuery(['orders']) and reads the hydrated cache — no refetch
```

Same query key on both sides is what makes the handoff seamless. See [[28 - Frameworks and Application Architecture/06 - Server State|Server State]].

## Related Notes

- [[28 - Frameworks and Application Architecture/06 - Server State|Server State]]
- [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]]
- [[29 - Frontend System Design/09 - Network and API Design for Frontend|Network and API Design for Frontend]]
- [[30 - Backend System Design/05 - Caching|Backend Caching]]
