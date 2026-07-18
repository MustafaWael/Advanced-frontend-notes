---
tags: [javascript, dom, dom-checklist]
module: "19 - DOM and Browser APIs"
priority: must-know
status: not-started
---

# DOM and Browser APIs Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, predict, debug, and refactor the code without looking.

## Source Anchors

- [web.dev - Rendering performance](https://web.dev/articles/rendering-performance)
- [DOM Living Standard](https://dom.spec.whatwg.org/)
- [Fetch Living Standard](https://fetch.spec.whatwg.org/)
- [MDN - Web APIs](https://developer.mozilla.org/en-US/docs/Web/API)

## Render Pipeline

- [ ] I can name the pipeline stages: DOM/CSSOM → render tree → layout → paint → composite.
- [ ] I can define reflow vs repaint and give property examples for each tier, including compositor-only.
- [ ] I can explain forced synchronous layout and list three properties that trigger it.
- [ ] I can spot layout thrashing in a loop and fix it by separating reads from writes.
- [ ] I can explain why `transform`/`opacity` animations stay smooth while `top`/`left` ones jank.
- [ ] I can explain the difference between `display: none` and `visibility: hidden` in pipeline terms.

## Events

- [ ] I can name the three propagation phases in order and predict listener firing order for nested elements.
- [ ] I can distinguish `preventDefault`, `stopPropagation`, and `stopImmediatePropagation` precisely.
- [ ] I can explain what `{ passive: true }` promises and why it improves scroll performance.
- [ ] I can explain `target` vs `currentTarget` and why delegation needs `closest()`.
- [ ] I can write the delegation pattern from memory, including the null guard and non-bubbling event workarounds.
- [ ] I can explain how React's synthetic event system relates to native delegation and what changed in React 17.
- [ ] I can build pub/sub with `new EventTarget()` and dispatch a namespaced `CustomEvent` with `detail`, `bubbles`, and `composed` set deliberately.
- [ ] I can clean up listener groups with one `AbortController` signal.

## Storage

- [ ] I can compare cookies, localStorage, sessionStorage, and IndexedDB on size, sync/async, scope, lifetime, and worker access.
- [ ] I can explain why localStorage is a security risk for tokens and what HttpOnly changes.
- [ ] I can explain why a large synchronous localStorage write janks the main thread.
- [ ] I can implement cross-tab logout with the `storage` event or BroadcastChannel.
- [ ] I can wrap storage access defensively for private mode and quota errors.
- [ ] I can pick IndexedDB (or Cache Storage) for offline/large/binary data and justify it.

## Observers

- [ ] I can explain why IntersectionObserver beats scroll + getBoundingClientRect mechanically.
- [ ] I can implement lazy loading and an infinite-scroll sentinel with correct `isIntersecting` guards and cleanup.
- [ ] I can explain the initial-entry-on-observe behavior and the analytics bug it causes.
- [ ] I can explain the ResizeObserver loop error and two ways to avoid it.
- [ ] I can explain when MutationObserver callbacks run and why records are batched.

## fetch

- [ ] I can explain why fetch resolves on 404 and what it actually rejects on.
- [ ] I can explain "body stream consumed once" and when `clone()` is required.
- [ ] I can name the three credentials modes and the CORS requirements for `include`.
- [ ] I can implement timeout with `AbortSignal.timeout` and distinguish TimeoutError from a caller's AbortError.
- [ ] I can design retry logic: which status codes, which error types, backoff with jitter, and the idempotency problem with POST.
- [ ] I can read a body incrementally with `getReader()` for progress or streaming UIs.

## Forms

- [ ] I can list the successful-control rules and diagnose a field missing from submission.
- [ ] I can explain why FormData bodies must not have a manual Content-Type.
- [ ] I can use `getAll` for multi-value fields and explain what `Object.fromEntries` drops.
- [ ] I can use the Constraint Validation API including `setCustomValidity` and `novalidate`.
- [ ] I can explain how React 19 form actions and Next.js Server Actions build on FormData and native submission.

## Workers and Service Workers

- [ ] I can list what a Web Worker can and cannot access, and what structured clone refuses to copy.
- [ ] I can explain transferables, O(1) transfer vs O(n) clone, and buffer detachment.
- [ ] I can choose between worker, chunking, and "neither" for a given performance problem.
- [ ] I can explain the service worker lifecycle and why users get stuck on old deploys.
- [ ] I can assign a caching strategy per resource type and explain the white-screen-after-deploy bug.
- [ ] I can explain why sw.js itself must not be HTTP-cached.

## History and Navigation

- [ ] I can describe DIY SPA routing: click interception, pushState, render, popstate.
- [ ] I can explain when popstate fires and when it does not.
- [ ] I can choose push vs replace for filters, wizards, and tabs, and defend it.
- [ ] I can name what SPAs owe users after taking over navigation: rendering, scroll restoration, focus, server rewrites.
- [ ] I can explain what Next.js `<Link>` adds on top of pushState: interception, RSC payload fetch, prefetch, router cache.

## Exit Test

- [ ] Diagnose and fix a layout-thrashing loop live, explaining each forced layout.
- [ ] Build delegated list actions (delete/expand) with `closest()`, handling icon clicks and empty-space clicks.
- [ ] Write a fetch wrapper with typed HTTP errors, timeout, abort passthrough, and bounded jittered retry.
- [ ] Explain to a junior why their token-in-localStorage design is risky and what to use instead.
- [ ] Sketch the update-toast + skipWaiting flow that unsticks a stale service worker deploy.

## Related Notes

- [[19 - DOM and Browser APIs/00 - DOM and Browser APIs MOC|DOM and Browser APIs MOC]]
- [[09 - Event Loop Advanced/08 - Event Loop Checklist|Event Loop Checklist]]
- [[20 - Network and Security/09 - Network and Security Checklist|Network and Security Checklist]]
- [[01 - Roadmap|Roadmap]]
