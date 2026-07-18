---
tags: [labs, nextjs, caching, server-actions]
module: "90 - Labs"
priority: important
status: not-started
aliases: [next caching lab]
verified_on: 2026-07-12
version_scope: "Next.js 16"
---

# Lab 04 — Next.js Cached Dashboard Mutation

Build a small Next.js 16 dashboard where the same data appears in three places, mutations go through a secured Server Action, and cache invalidation is *provably correct* — including demonstrating every wrong-invalidation failure mode on purpose.

## Prerequisites

- [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]] · [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]] · [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]] · [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]]
- [[24 - Testing and Quality/08 - Testing Nextjs Boundaries|Testing Next.js Boundaries]] · [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]

## Build Brief

`create-next-app` (App Router, TypeScript), Next 16 with `cacheComponents` enabled; data in a JSON file or SQLite via a thin data module (no ORM required); Vitest + Playwright.

Product: a project tracker with **three views of the same data** — `/dashboard` (project list + counts), `/projects/[id]` (detail), and a "recent activity" strip in the shared layout.

1. **Reads**: each view reads through cached functions (`use cache`) tagged with `cacheTag`: granular (`project:${id}`) plus collection (`projects`). A visible "rendered at" timestamp in each view makes cache hits *observable*.
2. **Mutations**: Server Actions — `renameProject`, `completeTask`, `createProject` — each doing the full contract: authN (a fake session cookie), authZ (ownership check), Zod validation, mutation, then the *correct* invalidation:
   - `renameProject` → `updateTag('project:${id}')` + `updateTag('projects')` (the name shows in lists).
   - `completeTask` → `updateTag('project:${id}')` only — and observe what stays stale, then justify or widen.
   - `createProject` → `updateTag('projects')`.
3. **One deliberate contrast**: an "archive" action that uses `revalidateTag('projects', 'max')` (SWR) instead — document the observable difference from `updateTag` for the acting user.
4. **A per-user region**: the layout greets the session user via `cookies()` inside a Suspense boundary — keeping the rest of the shell static ([[22 - Next.js Deep Dive/01 - Rendering Strategies|PPR model]]).

## Acceptance Criteria

- [ ] `next build` output shows the intended static/dynamic split (shell prerendered; the cookie-reading region dynamic).
- [ ] After `renameProject`, all three views show the new name without a hard refresh; the "rendered at" timestamps prove which regions re-rendered and which were cache hits.
- [ ] The archive action demonstrably differs: the acting user can see stale data on the next read (SWR), where `updateTag` actions never do — write down the observed sequence.
- [ ] Every action rejects: no session, wrong owner, malformed input — and the mutation provably didn't run.
- [ ] A `refresh()`-only variant of `renameProject` (build it behind a flag) demonstrably FAILS to update the tagged views — the negative proof that router refresh ≠ cache invalidation ([[22 - Next.js Deep Dive/03 - Revalidation|refresh]]).

## Debugging Tasks (create, observe, fix)

1. **The missing tag**: remove `cacheTag` from the activity strip's read; rename a project; document the staleness and *how you'd diagnose it in production* (which layer? — walk [[22 - Next.js Deep Dive/02 - The Caching Layers|the four layers]]); restore.
2. **The over-broad tag**: tag every read `data` and invalidate `data` everywhere; measure/observe the wasted re-renders via timestamps; restore granular tags and write the tag-taxonomy rule you'd give a team.
3. **The typo'd tag**: write `updateTag('porject:1')`; observe that nothing fails loudly — then add the guard you wish existed (a shared `tags.ts` constants module so reads and writes can't drift — [[23 - TypeScript Deep Dive/06 - Type Operators and Exhaustiveness|derive, don't duplicate]]).
4. **The UI-gated action**: strip authZ from `renameProject` and demonstrate (curl or a script invoking the action endpoint) why the hidden button wasn't protection ([[22 - Next.js Deep Dive/04 - Server Actions|public endpoints]]); restore.

## Testing Expectations

- Direct-invocation tests for every action: authN/authZ/validation matrix incl. hostile inputs, plus assertion that the correct tag helper was called ([[24 - Testing and Quality/08 - Testing Nextjs Boundaries|Next boundaries]]).
- Unit tests for the data module and any DTO mapping.
- Playwright: the golden path — open dashboard, rename in detail view, assert all three views updated without reload; plus one session/auth E2E ([[24 - Testing and Quality/07 - Playwright Workflows|workflows]]). Cache behavior is only provable here — say so in your test plan.

## Accessibility Expectations

- Mutations announce their outcome (the rename succeeded/failed) via the form/announcement patterns of [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|module 25]]; forms work pre-hydration (progressive enhancement — test with JS disabled once).

## Performance and Security Considerations

- Keep the mutation → invalidation → re-render loop tight: what's the payload of the action response? Which views re-render server-side vs receive fresh RSC payload?
- The session cookie: HttpOnly, SameSite, and why the action must still re-verify it ([[20 - Network and Security/04 - Cookies and Auth Patterns|auth]]).
- Never trust the `id` argument — ownership is checked against the session, not the client's claim.

## Interview Questions

1. A user renames a project and still sees the old name in the sidebar. Walk the four caching layers and name where you'd look first, and why.
2. `updateTag` vs `revalidateTag(tag, "max")` vs `refresh()` — contracts, and one concrete use case each.
3. Why must the tag taxonomy be designed like a data model? What breaks with tags that are too broad — and too narrow?
4. How would this design change on Next 14 (no `use cache`)? Name the equivalent mechanisms and the defaults trap ([[22 - Next.js Deep Dive/02 - The Caching Layers|14→15 flip]]).

## Retrospective

[[98 - Vault Operations/Templates/Lab Retrospective Template|Template]] — plus: your one-paragraph "how I'd explain Next caching to a teammate" after seeing it move.

## Related Notes

- [[22 - Next.js Deep Dive/00 - Next.js Deep Dive MOC|Next.js Deep Dive MOC]]
- [[24 - Testing and Quality/08 - Testing Nextjs Boundaries|Testing Next.js Boundaries]]
- [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]]
- [[30 - Backend System Design/05 - Caching|Backend Caching (invalidation as a data model)]]
- [[90 - Labs/00 - Labs MOC|Labs MOC]]
