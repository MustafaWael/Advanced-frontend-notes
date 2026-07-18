---
tags: [javascript, moc, dom, browser-apis]
module: "19 - DOM and Browser APIs"
priority: must-know
status: not-started
---

# DOM and Browser APIs MOC

This module covers the browser as a platform: how the render pipeline turns DOM into pixels, how events propagate and delegate, what the storage options actually trade off, and the workhorse APIs — observers, fetch, forms, workers, service workers, and history — that every framework wraps. It sits logically right after the event loop: the event loop tells you *when* the browser runs your code; this module tells you *what* the browser does around it. After it, framework behavior (React synthetic events, Next.js routing and caching) stops being magic.

## Prerequisites

- [[09 - Event Loop Advanced/00 - Event Loop Advanced MOC|Event Loop Advanced MOC]] — rendering opportunities, tasks, and microtasks are assumed throughout.
- [[08 - Async JavaScript/00 - Async JavaScript MOC|Async JavaScript MOC]] — promises and AbortController are used constantly here.

## Reading Order

1. [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]] — DOM/CSSOM, reflow vs repaint, layout thrashing.
2. [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]] — capture/target/bubble, the three control methods, passive listeners.
3. [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]] — one listener for many elements; the React connection.
4. [[19 - DOM and Browser APIs/04 - Custom Events and EventTarget|Custom Events and EventTarget]] — platform-native pub/sub and system boundaries.
5. [[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]] — cookies vs Web Storage vs IndexedDB, and when each is wrong.
6. [[19 - DOM and Browser APIs/06 - Observers|Observers]] — IntersectionObserver, ResizeObserver, MutationObserver.
7. [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]] — Response semantics, streams, credentials, timeout and retry.
8. [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]] — native submission, validation, and the Server Actions bridge.
9. [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]] — structured clone, transferables, worker vs chunking.
10. [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]] — lifecycle, caching strategies, deploy incidents.
11. [[19 - DOM and Browser APIs/11 - History and Navigation APIs|History and Navigation APIs]] — pushState/popstate and what Next.js layers on top.
12. [[19 - DOM and Browser APIs/12 - DOM and Browser APIs Checklist|DOM and Browser APIs Checklist]] — active self-test.

## You're Done When

- [ ] I can trace the render pipeline, distinguish reflow/repaint/composite, and fix a layout-thrashing loop by separating reads from writes.
- [ ] I can predict listener order across capture/target/bubble and use `preventDefault`, `stopPropagation`, and `stopImmediatePropagation` correctly.
- [ ] I can write robust event delegation with `closest()` and explain how React's synthetic events relate to it.
- [ ] I can choose between cookies, localStorage, sessionStorage, and IndexedDB using security, sync/async, and capacity arguments.
- [ ] I can implement lazy loading and infinite scroll with IntersectionObserver, with correct guards and cleanup.
- [ ] I can build a production fetch wrapper: `res.ok` checks, typed errors, `AbortSignal.timeout`, and retry limited to safe cases.
- [ ] I can explain native form submission, FormData semantics, and how React 19/Next Server Actions build on them.
- [ ] I can decide worker vs chunking for a main-thread bottleneck and explain structured clone vs transferables.
- [ ] I can explain the service worker lifecycle well enough to debug a stuck deploy, and assign caching strategies per resource.
- [ ] I can explain SPA routing mechanically — pushState, popstate, scroll restoration — and what the Next.js router adds.

## Related Notes

- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[20 - Network and Security/00 - Network and Security MOC|Network and Security MOC]]
- [[01 - Roadmap|Roadmap]]
- [[25 - Accessibility and Inclusive UX/00 - Accessibility and Inclusive UX MOC|Accessibility and Inclusive UX MOC]]
