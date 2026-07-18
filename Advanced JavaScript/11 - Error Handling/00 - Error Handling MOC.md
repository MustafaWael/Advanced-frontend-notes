---
tags: [javascript, moc, error-handling]
module: "11 - Error Handling"
priority: important
status: not-started
---

# Error Handling MOC

This module turns error handling from "wrap it in try/catch" into a system of failure ownership: who catches, who rethrows, who logs, and what the user sees. It covers the language mechanics of `try/catch/finally` and `Error` objects, then the bugs that dominate mid-level interviews and production incidents: swallowed errors, missing `await`, unhandled promise rejections, error boundaries that never see async failures, and `fetch` calls that treat a 500 as success. By the end you can design user-facing recovery — field errors, fallback UI, retry rules, cancellation — instead of shipping invisible failures.

## Prerequisites

- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]

## Reading Order

1. [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]] — the synchronous control-flow baseline before async errors.
2. [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]] — structured errors callers can classify, wrap with `cause`, and log.
3. [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]] — how failures travel through promises and where `try/catch` actually works.
4. [[11 - Error Handling/04 - Promise Rejections|Promise Rejections]] — giving every promise an owner and using global handlers as monitoring only.
5. [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]] — what boundaries catch, what they miss, and where to place them.
6. [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]] — turning network, HTTP, abort, and parse failures into predictable UI states.
7. [[11 - Error Handling/07 - Error Handling Checklist|Error Handling Checklist]] — self-test drills and scenarios that prove the module is actually done.

## You're Done When

- [ ] I can predict `finally` override behavior and explain why a `return` inside `finally` suppresses the real error.
- [ ] I can write custom errors with `name`, a stable `code`, and `cause`, and narrow `unknown` catch values in TypeScript.
- [ ] I can explain why `try/catch` misses unawaited promises and fix a missing-`await` or `forEach(async ...)` bug on sight.
- [ ] I can choose between `Promise.all` and `Promise.allSettled` and justify fail-fast versus partial UI.
- [ ] I can make sure every promise is awaited, returned, or caught, using `unhandledrejection` only as a logging safety net.
- [ ] I can build a `fetchJson` wrapper that checks `response.ok` and maps 401, 404, 422, 429, and 500 to distinct UI actions.
- [ ] I can explain what React error boundaries catch and do not catch, and design fallback plus reset behavior for routes and widgets.
- [ ] I can add cancellation to a React effect and treat `AbortError` as cleanup, not a user-facing failure.

## Related Notes

- [[11 - Error Handling/07 - Error Handling Checklist|Error Handling Checklist]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[01 - Roadmap|Roadmap]]
