---
tags: [system-design, interview, state, normalization, optimistic-ui]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [normalized store, optimistic update rollback, entity cache]
---

# State Normalization and Optimistic Updates

## Maturity Target

- Priority: #must-know
- Study time: 45 minutes
- Interview signal: Decide when to normalize client state, and design an optimistic update with reconciliation and rollback — naming both costs.
- Production signal: Shared entities update in one place; optimistic UI has a defined failure path, not a hope.
- Dependencies: [[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]], [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]

## Source Anchors

- [Redux — Normalizing State Shape](https://redux.js.org/usage/structuring-reducers/normalizing-state-shape)
- [TanStack Query — Optimistic Updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)

## 1. Concept

**Normalization** — store entities once, keyed by id (`{ [id]: entity }`), and reference them by id everywhere else, instead of duplicating objects across lists. It's the client mirror of database normalization ([[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling]]):

- One entity, one place → an update (a like count, a renamed user) propagates everywhere at once.
- Overlapping lists (feed page 1 and 2, search results, detail view) share entities → less memory, no divergence.
- Cost: indirection (selectors to re-hydrate) — over-engineering for a small, non-shared list. Say when it's *not* worth it.

**Optimistic updates** — apply the change to the UI before the server confirms, then reconcile. The client becomes a deliberately-inconsistent replica ([[30 - Backend System Design/07 - CAP and Consistency|eventual consistency]]) for the sake of instant UX:

```tsx
onMutate: async (next) => {
  await qc.cancelQueries({ queryKey: ['todos'] });          // stop races with in-flight refetch
  const prev = qc.getQueryData(['todos']);                  // snapshot for rollback
  qc.setQueryData(['todos'], (t) => applyOptimistic(t, next)); // update NOW
  return { prev };
},
onError: (_e, _next, ctx) => qc.setQueryData(['todos'], ctx.prev), // rollback on failure
onSettled: () => qc.invalidateQueries({ queryKey: ['todos'] }),    // truth wins in the end
```

> [!warning] Three optimistic footguns: (1) not snapshotting for rollback, so a failed mutation leaves the UI showing a lie; (2) not cancelling in-flight queries in `onMutate`, so a refetch that resolves after your optimistic write clobbers it; (3) **overlapping mutations on the same key** — snapshot-rollback assumes one mutation in flight, so if a second optimistic write lands before the first settles, the first's rollback restores a snapshot that *erases the second's change*. Fixes: reconcile from the server response instead of a raw snapshot restore, skip intermediate invalidations while any mutation is in flight (TanStack exposes `isMutating` for exactly this), or serialize mutations per key. All three are race conditions in disguise ([[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]).

## 2. Why It Matters

These two decisions come up in every app-level design with shared data and mutations (feed, chat, collaborative tools). Normalization is the "how do you keep the like count consistent across the feed and the detail page" answer; optimistic updates are the "how does it feel instant" answer. Interviewers probe the *costs* — rollback and reconciliation — because that's where mid-level answers stop.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a social feed shows each post in the list and, when tapped, in a detail modal. Liking a post in the modal updates the modal but the list still shows the old count; also, double-tapping like sometimes ends on the wrong count.

Trace: two issues. (1) The post object is **duplicated** — one copy in the list array, another in the modal's state — so the modal's update doesn't reach the list (denormalized divergence). (2) The optimistic like isn't cancelling the background refetch, so a stale server response overwrites the toggle.

Fix: normalize — one `posts: { [id]: Post }` store; list and modal both render `posts[id]`, so one update shows everywhere. Make the like optimistic with a snapshot + rollback, and `cancelQueries` in `onMutate` so no in-flight refetch clobbers it.

Tradeoff: normalization adds selector indirection and a bit of boilerplate; optimistic updates add rollback logic and a brief window where the UI shows unconfirmed state — unacceptable for irreversible actions, ideal for a like. Both are the right call *here* because data is shared and the interaction is high-frequency; for a one-off form, neither is worth it.

## 4. Interview Answer

Short answer:

> I normalize when entities are shared across views or mutated — store them once by id and reference by id, so one update propagates everywhere and overlapping lists don't diverge. I skip it for small, non-shared lists where it's just indirection. Optimistic updates apply the change before the server confirms for instant UX, with a snapshot for rollback and cancellation of in-flight refetches so a stale response can't clobber the optimistic write.

Deeper answer:

> Normalization is database normalization on the client — one source of truth per entity — and its payoff scales with sharing and mutation frequency; the cost is selector indirection, so I name when it's over-engineering. Optimistic UI is a deliberate eventual-consistency window: I snapshot before writing, reconcile on settle via invalidation, and roll back on error — and I cancel in-flight queries in onMutate because otherwise a refetch resolving after my write is a classic race. The line I draw: optimistic for high-frequency reversible actions (like, reorder, inline edit), pessimistic confirmation for money-moving or irreversible ones.

## 5. Practice

1. <details><summary>When is normalizing client state over-engineering?</summary>When entities aren't shared across views and aren't mutated after load — a one-off list rendered in one place gains nothing from an id-keyed store but pays indirection and boilerplate. Normalize when the same entity appears in multiple places or gets updated (feed + detail, live counts); otherwise keep it simple.</details>
2. <details><summary>Why must an optimistic mutation cancel in-flight queries before writing?</summary>A background refetch already in flight may resolve *after* your optimistic write and overwrite it with pre-mutation data — a race. Cancelling those queries in `onMutate` (and re-invalidating on settle) ensures the optimistic value isn't clobbered and the final state comes from a fresh post-mutation fetch.</details>
3. <details><summary>Which actions should NOT be optimistic, and why?</summary>Irreversible or high-stakes ones — payments, deletions without undo, anything with legal/financial weight. Optimistic UI shows unconfirmed state for a window; if the server rejects, you've shown the user a success that didn't happen. For those, show a pending state and confirm from the server before claiming success.</details>

## Related Notes

- [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]]
- [[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]]
- [[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling and Databases]]
- [[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]]
