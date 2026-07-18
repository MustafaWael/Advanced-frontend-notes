---
tags: [react, state-management, server-state, react-query]
module: "28 - Frameworks and Application Architecture"
priority: must-know
status: not-started
aliases: [React Query, TanStack Query, Data fetching state]
verified_on: 2026-07-17
version_scope: "TanStack Query 5, React 19, Next.js App Router era"
---

# Server State

## Maturity Target

- Priority: #must-know
- Study time: 50 minutes
- Interview signal: Explain why server data is categorically different from client state (you don't own it; it's a *cache with staleness*), and name the problems a query library actually solves: caching, deduping, invalidation, background refetch, mutations with optimistic updates.
- Production signal: No hand-rolled `useEffect`+`useState` fetching in your codebase; cache keys are designed, not accidental; invalidation is deliberate.
- Dependencies: [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]], [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]

## Source Anchors

- [TanStack Query - Overview](https://tanstack.com/query/latest/docs/framework/react/overview)
- [TanStack Query - Important Defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults)
- [tkdodo - Practical React Query](https://tkdodo.eu/blog/practical-react-query)

## 1. Concept

Simple version: client state is data you *own* — you write it, it's instantly correct. Server state is data you *borrow* — the truth lives in the database, other users change it, and your copy starts aging the moment it arrives. Treating a borrowed, aging copy like owned state is the root architecture error.

The accurate framing — server state is a **cache**, and caches come with cache problems:

- **Identity**: the same logical data (`user 42`) is requested from many components. A cache needs **keys** — `['users', 42]` — so requests dedupe and components share one copy.
- **Staleness**: your copy is stale by definition. The question is *how stale is acceptable* (`staleTime`) and *when to refresh* (on mount, window focus, reconnect, interval).
- **Invalidation**: after a mutation, which cached data is now wrong? (`invalidateQueries({ queryKey: ['users'] })`).
- **Lifecycle**: when do unused entries leave memory (`gcTime`)? What shows during fetch (loading/error/data states, kept-previous data during refetch)?

This is why "React Query is a data-fetching library" is the wrong sentence — *you* still write the fetch. It's an **async cache manager**:

```tsx
// The hand-rolled version — and every problem it silently has:
function useUser(id: string) {
  const [user, setUser] = useState<User>();
  useEffect(() => {
    fetchUser(id).then(setUser);        // ❌ race on id change (A/B resolve out of order)
  }, [id]);                              // ❌ no cache: every mount refetches
  return user;                           // ❌ no dedupe: 3 components = 3 requests
}                                        // ❌ no error/retry, no staleness policy,
                                         // ❌ no invalidation after mutations

// The declared version:
const { data: user, isPending, error } = useQuery({
  queryKey: ['users', id],               // identity → dedupe + sharing
  queryFn: () => fetchUser(id),          // you still own the fetch
  staleTime: 60_000,                     // freshness policy, explicit
});
```

Mutations close the loop — write, then reconcile the cache:

```tsx
const qc = useQueryClient();
const { mutate } = useMutation({
  mutationFn: renameUser,
  onMutate: async (next) => {            // optimistic: update cache NOW
    await qc.cancelQueries({ queryKey: ['users', next.id] });
    const prev = qc.getQueryData(['users', next.id]);
    qc.setQueryData(['users', next.id], (u: User) => ({ ...u, name: next.name }));
    return { prev };
  },
  onError: (_e, next, ctx) => qc.setQueryData(['users', next.id], ctx!.prev), // rollback
  onSettled: (_d, _e, next) => qc.invalidateQueries({ queryKey: ['users', next.id] }), // truth wins
});
```

Server-first frameworks shift the *initial load* of this problem to the server (RSC, loaders — [[28 - Frameworks and Application Architecture/04 - Meta-Frameworks|Meta-Frameworks]]), but client-side interactivity (live lists, optimistic UI, polling) still needs the cache discipline.

## 2. Why It Matters

- "How do you handle data fetching?" — the mature answer names the *cache problems*, not a library. Interviewers push on staleness and invalidation specifically.
- The `useEffect`-fetch pattern is the single most common source of race conditions, duplicate requests, and loading-state bugs in React codebases ([[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]).
- Cache-key design is API design: keys that don't include their parameters (`['products']` for a filtered list) serve wrong data; keys that are too specific never share.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a support dashboard. Agent renames a customer in a modal; the table behind it still shows the old name. Meanwhile the table sometimes flashes wrong rows when switching filters fast.

Trace: two classic server-state failures. (1) The modal's save wrote to the server and to *its own* local copy, but the table's copy (separate `useState` from a separate fetch) was never told — *cross-component staleness after mutation*. (2) Filter switching triggers overlapping fetches; the slower older response lands last and overwrites — the *race* ([[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]).

```tsx
// Fix: one cache, keyed correctly — both bugs dissolve structurally
const { data: rows } = useQuery({
  queryKey: ['customers', { filter }],   // key includes params → per-filter entries,
  queryFn: () => fetchCustomers(filter), // stale responses can't cross keys
  placeholderData: keepPreviousData,     // no flash while switching
});
// In the modal:
onSettled: () => qc.invalidateQueries({ queryKey: ['customers'] })  // table refetches
```

Tradeoffs: invalidating the broad `['customers']` prefix refetches every filter variant (simple, chatty) vs surgical `setQueryData` patching (efficient, easy to get wrong — you're hand-maintaining cache coherence again). Optimistic updates buy instant UX and cost rollback complexity + a brief window of showing unconfirmed truth. Pick per endpoint, not globally.

> [!warning] Footgun: copying `data` into `useState` ("so I can edit it") forks the source of truth — edits fight refetches. Form drafts are *client* state seeded from server state once (`defaultValues`), reconciled on submit via mutation + invalidation.

## 4. Interview Answer

Short answer:

> Server state is fundamentally different from client state: the source of truth is remote, other actors change it, and every local copy is stale by definition. So it should be managed as a cache — keyed by request identity for deduping and sharing, with explicit staleness policy, background refetching, and invalidation after mutations. That's what React Query actually is: not a fetching library but an async cache manager. Hand-rolled useEffect fetching fails on exactly those axes — races, duplicate requests, no invalidation story.

Deeper answer:

> Depth points: query keys are the API — they must include every parameter the response depends on, which also structurally eliminates cross-key races; staleTime versus gcTime separate "when is it stale" from "when does it leave memory"; mutations reconcile via invalidation (simple, refetch-heavy) or direct cache writes and optimistic updates with rollback (fast, complex). With RSC and loaders, initial data moves server-side and the client library's role narrows to interactive, live, and optimistic flows — they're complementary layers, not competitors.

## 5. Practice

1. <details><summary>Name five distinct problems a query cache solves that useEffect-fetching doesn't.</summary>Request deduping across components; caching across mounts/navigation; staleness policy with background refetch (focus/reconnect); race-safety via key identity; mutation reconciliation (invalidation/optimistic updates) — plus retries, loading/error state machines, pagination/infinite helpers.</details>
2. <details><summary>Why must the query key include the filter object, and what bug does omitting it cause?</summary>The key is the cache identity — if `['products']` serves all filters, responses for different filters overwrite each other, and a slow stale response can replace fresh data (a race made persistent by the cache). Including params gives each variant its own entry and confines every response to its key.</details>
3. <details><summary>When would you choose optimistic updates over invalidate-and-refetch, and what two costs do you accept?</summary>High-frequency, high-confidence, latency-sensitive interactions: toggles, likes, inline renames. Costs: rollback logic for failures (and its edge cases under concurrent mutations), and a window where the UI shows unconfirmed data — unacceptable for money-moving or irreversible operations.</details>

## Related Notes

- [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
- [[22 - Next.js Deep Dive/06 - Data Fetching Patterns|Data Fetching Patterns]]
- [[30 - Backend System Design/05 - Caching|Caching]] — server-state libraries are cache-aside with staleness management
- [[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]] — optimistic UI as a deliberate eventual-consistency window
