---
tags: [javascript, moc, async, promises]
module: "08 - Async JavaScript"
priority: must-know
status: not-started
---

# Async JavaScript MOC

This module builds async JavaScript from run-to-completion and microtask timing up through promises, `async/await`, error policy, cancellation, and a production API layer. It unlocks the classic frontend bug families: floating promises, loading states that clear too early, stale search results overwriting fresh state, unhandled rejections, and aborts mistaken for failures. It also covers the promise-tracing output questions and combinator-choice questions that interviews lean on hardest.

## Prerequisites

- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]
- [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]]

## Reading Order

1. [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]] — run-to-completion, tasks vs microtasks, and why async never means parallel CPU work.
2. [[08 - Async JavaScript/02 - Promises|Promises]] — the state machine and chaining contract everything else builds on.
3. [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]] — choosing `all`, `allSettled`, `race`, or `any` by dependency and failure policy.
4. [[08 - Async JavaScript/04 - Async Await|Async Await]] — syntax over promises, waterfalls vs parallelism, and React/Next.js boundaries.
5. [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]] — where rejections are created, caught, and turned into recovery decisions.
6. [[08 - Async JavaScript/06 - AbortController|AbortController]] — cooperative cancellation for obsolete reads, timeouts, and effect cleanup.
7. [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]] — assembling everything into a consistent transport, domain, and UI-state layer.
8. [[08 - Async JavaScript/08 - Async Checklist|Async Checklist]] — active-recall drills, output predictions, and production scenarios to verify mastery.

## You're Done When

- [ ] I can predict task/microtask output order and explain why promise reactions run before timers.
- [ ] I can name the promise states and say what `.then` returns when a handler returns a value, returns a promise, throws, or is missing.
- [ ] I can choose `all`, `allSettled`, `race`, or `any` from a dependency and failure policy, and I know failing fast does not cancel in-flight work.
- [ ] I can spot floating promises and `forEach(async ...)` bugs, and fix accidental waterfalls with `Promise.all`.
- [ ] I check `response.ok`, reject with `Error` objects, catch where recovery is possible, and rethrow when callers still need the failure.
- [ ] I can abort obsolete requests with `AbortController` in React effect cleanup and treat expected abort errors as cleanup, not failures.
- [ ] I know aborting a client request does not roll back server work, and I can explain why critical mutations need idempotency instead of blind retries.
