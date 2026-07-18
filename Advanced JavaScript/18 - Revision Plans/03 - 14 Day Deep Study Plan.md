---
tags: [javascript, revision, interview, 14-day-deep-study-plan]
module: "18 - Revision Plans"
priority: must-know
status: not-started
---

# 14 Day Deep Study Plan

This plan is for turning the vault into durable skill. It is slower than the [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]] because it asks you to build examples, debug failure modes, and explain production tradeoffs instead of only reviewing notes.

## Daily Template

Each day should produce visible evidence:

- Recall: write what you know before reading.
- Mechanism: write the official or precise rule.
- Trace: solve at least two code-output examples.
- Production: write a realistic frontend bug and fix.
- Interview: record or speak one short answer and one deeper answer.
- Weak area: log what you missed and schedule a repeat.

Recommended daily time: 90 to 150 minutes. If you have less time, keep the trace and production sections.

## Week 1: Foundations

Week 1 builds the language model: runtime, scope, closures, functions, `this`, objects, prototypes, and arrays. This is where many interview answers become either precise or vague.

## Day 1: ECMAScript, Runtime, Execution Context, and Call Stack

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You do not confuse the JavaScript language with browser APIs.

Study:

- [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]]
- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]
- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]
- [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]

Build:

- [ ] Draw a two-column map: ECMAScript language features vs browser/runtime features.
- [ ] Trace a nested function call until the stack unwinds.
- [ ] Explain why `fetch`, `setTimeout`, DOM events, and rendering are not defined by ECMAScript itself.

Frontend scenario:

A dashboard freezes when a large calculation runs after a button click. Explain why async APIs are irrelevant if the CPU work is still synchronous, then suggest splitting work, moving work to a worker, or reducing the work.

## Day 2: Memory, Realms, Agents, and Job Queues

Label: Important  
Estimated time: 2 hours  
Interview signal: You can go deeper without pretending every browser detail is the same as the ECMAScript spec.

Study:

- [[02 - JavaScript Runtime Foundations/05 - Memory Heap|Memory Heap]]
- [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]
- [[13 - Performance and Memory/01 - Memory Management|Memory Management]]
- [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]

Build:

- [ ] Explain reachability with one object graph.
- [ ] Explain why objects from different iframes can make `instanceof` checks surprising.
- [ ] Explain how jobs relate to promise reactions without calling them "threads."

Frontend scenario:

A rich editor keeps memory after closing a modal. Trace what might still reach the editor data: listener, timer, closure, cache, global registry, or DOM reference.

## Day 3: Scope, Lexical Environments, `var`, `let`, `const`, Hoisting, and TDZ

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can explain hoisting accurately without saying code is physically moved.

Study:

- [[03 - Scope and Variables/01 - Scope Types|Scope Types]]
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/03 - var let const|var let const]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

Build:

- [ ] Write a snippet where `var` logs `undefined`.
- [ ] Write a snippet where `let` throws `ReferenceError`.
- [ ] Write a snippet where function declaration hoisting is useful but function expression hoisting is not.

Frontend scenario:

A module imports configuration and reads a variable before it is initialized because a circular import changed evaluation order. Explain the TDZ risk and the fix: move shared constants, break the cycle, or defer access behind a function.

## Day 4: Closures, Stale Closures, and Retained Memory

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can explain closures as retained bindings and connect them to React and memory.

Study:

- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]

Build:

- [ ] Implement a counter factory with independent state.
- [ ] Implement a stale timer bug and fix it.
- [ ] Explain when a closure-retained value is intentional and when it becomes a leak.

Frontend scenario:

A save button schedules a retry with old form values. Fix it using a fresh read, effect dependency, functional state update, ref, or moving the retry logic into the submission flow.

## Day 5: Functions, Arrows, Higher-Order Functions, Purity, Debounce, and Throttle

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You choose function forms by semantics, not style preference.

Study:

- [[04 - Functions Deep Dive/01 - Function Declarations vs Expressions|Function Declarations vs Expressions]]
- [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]
- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions and IIFE]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]

Build:

- [ ] Compare a regular method and an arrow callback.
- [ ] Write a pure transformation function for API data.
- [ ] Implement a debounced search handler and show cleanup.

Frontend scenario:

A search page sends a request on every keypress. Choose debounce for "after the user pauses" behavior, throttle for "at most once per interval" behavior, and no rate limit when every event must be handled.

## Day 6: `this`, `call`, `apply`, `bind`, Constructors, and Classes

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can determine `this` from the call site under pressure.

Study:

- [[05 - this Binding/01 - What is this|What is this]]
- [[05 - this Binding/02 - this in Strict Mode|this in Strict Mode]]
- [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]
- [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]
- [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]

Build:

- [ ] Write one example for each binding rule.
- [ ] Extract a method and show the failure mode.
- [ ] Bind a function and show why `.call` cannot override the bound `this`.

Frontend scenario:

A callback passed to `addEventListener` or a component prop loses its receiver. Fix it and explain whether a wrapper, binding, or refactor is best.

## Day 7: Objects, Prototypes, Classes, Copying, and Week 1 Review

Label: Must-know  
Estimated time: 2 to 3 hours  
Interview signal: You can move from object internals to everyday immutability decisions.

Study:

- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]
- [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]]
- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]
- [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]

Build:

- [ ] Trace own vs inherited property lookup.
- [ ] Explain descriptors: writable, enumerable, configurable, getter, and setter.
- [ ] Fix a shallow-copy mutation bug in React state.
- [ ] Solve 5 Week 1 code-output questions from [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]], [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]], and [[16 - Code Output Questions/03 - this Output Questions|this Output Questions]].

Frontend scenario:

A copied settings object mutates the original cache. Explain shared nested references and choose targeted immutable update, `structuredClone`, normalization, or a library based on data size and shape.

## Week 2: Applied JavaScript

Week 2 connects the language model to async behavior, modules, error handling, performance, React, Next.js, and interviews.

## Day 8: Arrays, Iteration, Data Transformation, and Collection Choices

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You use array methods by intent and understand mutation cost.

Study:

- [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]
- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
- [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]
- [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]

Build:

- [ ] Transform API rows into UI sections with `map`, `filter`, and `reduce`.
- [ ] Replace a mutating `sort` with a safe immutable approach.
- [ ] Choose object, `Map`, `Set`, or `WeakMap` for a concrete UI cache.

Frontend scenario:

A product list rerenders incorrectly because sorting mutates props. Fix with an immutable copy or modern immutable method, then explain the cost for large lists.

## Day 9: Promises, Promise Methods, Async/Await, and Async Errors

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can design concurrency and failure behavior deliberately.

Study:

- [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]

Build:

- [ ] Compare sequential `await` with parallel `Promise.all`.
- [ ] Explain `Promise.allSettled` for partial success UIs.
- [ ] Show why `try/catch` needs `await` or a returned promise to catch a rejection.

Frontend scenario:

A profile page loads user, posts, and permissions. Decide which calls are required, which can fail independently, and whether the UI should block, partially render, retry, or show fallback content.

## Day 10: AbortController, API Integration, Race Conditions, and Duplicate Requests

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can make async UI correct when users click fast, navigate, or type quickly.

Study:

- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]
- [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]

Build:

- [ ] Write a single-flight guard for a submit button.
- [ ] Write a latest-request-wins search example.
- [ ] Write a fetch cancellation example with `AbortController`.

Frontend scenario:

A user types "react", then deletes to "re". The slower "react" response arrives last and overwrites newer results. Fix with abort, request id, or both.

## Day 11: Event Loop, Rendering, Timers, Microtasks, and Responsiveness

Label: Must-know  
Estimated time: 2 hours  
Interview signal: You can predict output and explain UI timing.

Study:

- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[09 - Event Loop Advanced/04 - Timers|Timers]]
- [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]

Build:

- [ ] Solve 5 event-loop output questions.
- [ ] Show how a microtask loop can delay timers and rendering.
- [ ] Use `requestAnimationFrame` in a small UI measurement/update example.

Frontend scenario:

An input feels stuck while a filter runs. Explain why the browser cannot paint during long JavaScript execution and choose a fix based on data size and UX needs.

## Day 12: Modules, Code Splitting, Error Handling, and Error Boundaries

Label: Important  
Estimated time: 2 hours  
Interview signal: You can connect module design, reliability, and user experience.

Study:

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]]
- [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]]

Build:

- [ ] Explain static vs dynamic import with loading and error states.
- [ ] Diagnose a circular dependency with a minimal example.
- [ ] Explain what an error boundary catches and what it does not catch.

Frontend scenario:

A dynamic import for a chart fails on a poor network. Explain how the UI should show loading, failure, retry, and fallback states without crashing the whole page.

## Day 13: Advanced Concepts, Performance, Memory, React, and Next.js

Label: Important  
Estimated time: 2 to 3 hours  
Interview signal: You can reason across language, framework, and browser layers.

Study:

- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]
- [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]

Build:

- [ ] Explain how `Object.is` relates to React dependency comparison.
- [ ] Fix a dependency-array identity bug.
- [ ] Explain a hydration mismatch and how to prevent it.
- [ ] Profile or reason through one performance bottleneck.

Frontend scenario:

A Next.js component reads `localStorage` during render and hydrates differently from the server output. Move browser-only work to a client component/effect or render a stable server fallback.

## Day 14: Full Mock Interview and Weak-Area Consolidation

Label: Must-know  
Estimated time: 2 to 3 hours  
Interview signal: You can integrate fundamentals, tracing, and production judgment under pressure.

Use:

- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
- [[18 - Revision Plans/04 - 30 Interview Questions|30 Interview Questions]]
- [[18 - Revision Plans/05 - 20 Code Output Questions|20 Code Output Questions]]
- [[18 - Revision Plans/06 - 10 Practical Frontend Scenarios|10 Practical Frontend Scenarios]]
- [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]]
- [[15 - Interview Preparation/07 - Interview Checklist|Interview Checklist]]

Mock interview structure:

- [ ] 10 minutes: runtime, scope, closure, or `this` explanation.
- [ ] 15 minutes: two code-output questions.
- [ ] 15 minutes: async/event loop/API scenario.
- [ ] 15 minutes: React/Next.js JavaScript scenario.
- [ ] 10 minutes: performance or memory debugging.
- [ ] 10 minutes: review weak answers and rewrite them.

Final deliverables:

- [ ] A weak-area list with exact mistakes, not broad labels.
- [ ] A corrected answer for every missed question.
- [ ] A final "production patterns I trust" list.
- [ ] A final "interview traps I now recognize" list.

## Readiness Signals

You are ready for strong mid-level interviews when:

- [ ] You can answer "What happens before this code runs?" for hoisting and execution context questions.
- [ ] You can answer "What is the receiver?" for `this` questions.
- [ ] You can answer "Is this a copy or shared reference?" for object/array questions.
- [ ] You can answer "What queue does this callback use?" for async/event-loop questions.
- [ ] You can answer "What values did this render close over?" for React closure questions.
- [ ] You can answer "What happens if the user clicks twice, navigates away, or the slower request resolves last?" for frontend scenarios.
- [ ] You can answer "How would you verify that?" for performance and memory questions.

## Sources

- ECMAScript Language Specification: https://tc39.es/ecma262/
- HTML Living Standard event loops and web application APIs: https://html.spec.whatwg.org/multipage/webappapis.html
- MDN JavaScript guide and reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript
- MDN Promise reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise
- MDN AbortController reference: https://developer.mozilla.org/en-US/docs/Web/API/AbortController
- React `useEffect` reference: https://react.dev/reference/react/useEffect
- Next.js Server and Client Components docs: https://nextjs.org/docs/app/getting-started/server-and-client-components
- web.dev RAIL performance model: https://web.dev/articles/rail

## Related Notes

- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
- [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]]
- [[18 - Revision Plans/04 - 30 Interview Questions|30 Interview Questions]]
- [[18 - Revision Plans/05 - 20 Code Output Questions|20 Code Output Questions]]
- [[18 - Revision Plans/06 - 10 Practical Frontend Scenarios|10 Practical Frontend Scenarios]]
- [[01 - Roadmap|Roadmap]]
