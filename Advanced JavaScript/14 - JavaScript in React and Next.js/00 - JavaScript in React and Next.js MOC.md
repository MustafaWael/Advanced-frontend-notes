---
tags: [javascript, moc, react, nextjs]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# JavaScript in React and Next.js MOC

This module pushes core JavaScript mechanisms — closures, identity, immutability, async timing — through React rendering and Next.js server/client boundaries. It explains render snapshots, stale closures, dependency arrays, referential equality, race conditions, and hydration as ordinary JavaScript behavior made visible by a framework. This is the highest-yield module for mid-level frontend interviews and for the everyday bugs it names: stale intervals, effects that never rerun, memo that never works, old API results winning, and hydration mismatches.

## Prerequisites

- [[03 - Scope and Variables/05 - Closures|Closures]] — every hook bug here is a closure lifetime question.
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying]] — immutable state updates depend on shallow-copy discipline.
- [[08 - Async JavaScript/02 - Promises|Promises]] — async effects and races are promise timing problems.
- [[08 - Async JavaScript/06 - AbortController|AbortController]] — the cancellation primitive used in effect cleanup.
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]] — React compares state and dependencies with `Object.is`.

## Reading Order

1. [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]] — components as functions, render snapshots, and commit vs render.
2. [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]] — why every render creates new closures.
3. [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]] — the signature bug: old callbacks reading old renders.
4. [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]] — what dependencies declare and how `Object.is` compares them.
5. [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]] — why inline objects and functions defeat memoization.
6. [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]] — copy the changed path so React can see the change.
7. [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]] — old responses winning, and the ignore-flag fix.
8. [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]] — real cancellation as effect cleanup.
9. [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]] — `'use client'`, module graphs, and serializable props.
10. [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]] — why server HTML and first client render must match.
11. [[14 - JavaScript in React and Next.js/11 - React and Next Checklist|React and Next Checklist]] — active self-test with drills, prompts, and scenarios.

## You're Done When

- [ ] I can explain state as a snapshot and why reading state right after `setState` still shows the current render's value.
- [ ] I can identify a stale closure in a timer, listener, promise callback, effect, memo, or callback, and pick the fix that matches the intended lifetime (dependencies, functional update, or ref).
- [ ] I can explain what dependency arrays declare and how React compares each element with `Object.is`.
- [ ] I can explain why object, array, and function literals are new references every render and why that breaks `React.memo`.
- [ ] I can update arrays and nested objects immutably and explain why in-place mutation can prevent rerenders.
- [ ] I can reproduce an async effect race and fix it with an ignore flag or `AbortController`, guarding success, error, and loading updates.
- [ ] I can explain Server vs Client Components, what `'use client'` does to the module graph, and why props across the boundary must be serializable.
- [ ] I can explain hydration, name common mismatch causes, and fix browser-only reads with `useEffect`, cookies, or dynamic import.

## Related Notes

- [[14 - JavaScript in React and Next.js/11 - React and Next Checklist|React and Next Checklist]]
- [[17 - Practical Frontend Scenarios/01 - Fixing Stale Closure in React|Fixing Stale Closure in React]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[01 - Roadmap|Roadmap]]
