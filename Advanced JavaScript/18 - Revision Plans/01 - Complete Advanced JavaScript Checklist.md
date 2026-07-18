---
tags: [javascript, revision, interview, complete-advanced-javascript-checklist]
module: "18 - Revision Plans"
priority: must-know
status: not-started
---

# Complete Advanced JavaScript Checklist

Use this checklist as an evidence-based review system. Do not mark an item done because you recognize the words. Mark it done when you can explain the concept, trace code, diagnose a frontend bug, and choose a production-safe pattern without opening the note.

## Mastery Labels

| Label | Meaning | Study Standard |
| --- | --- | --- |
| Must-know | Expected from a strong mid-level frontend developer. | Explain in 30 seconds, trace a code example, and name one production failure. |
| Important | Frequently appears in production reviews and stronger interviews. | Explain the tradeoff and connect it to React, Next.js, browser APIs, or API integration. |
| Deep-dive | Not always asked directly, but separates mature answers from memorized ones. | Explain the official mechanism and where simplified mental models break. |

## How To Prove Completion

For every topic below, capture proof in your own words:

- [ ] Simple explanation: one plain-English paragraph.
- [ ] Accurate mechanism: name the spec, host runtime, browser API, React rule, or Next.js boundary.
- [ ] Code trace: one snippet with expected output and the reason for each line.
- [ ] Frontend bug: one realistic failure mode from UI, forms, data fetching, rendering, state, or performance.
- [ ] Production decision: the safe default, the tradeoff, and the debugging signal.
- [ ] Interview answer: 30-second answer plus a deeper 2-minute version.

## Runtime Foundations

Related notes: [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]], [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]], [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]], [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]], [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]

- [ ] Must-know: I can separate ECMAScript language behavior from host behavior such as timers, DOM events, fetch, rendering, and Node APIs.
- [ ] Must-know: I can explain execution context creation and execution without saying "JavaScript moves code around."
- [ ] Must-know: I can trace call stack growth and unwinding through nested function calls and thrown errors.
- [ ] Important: I can explain why browser JavaScript is single-threaded for one agent, while workers and worklets introduce other agents.
- [ ] Important: I can describe what belongs to the engine, runtime, browser platform, and framework layer.
- [ ] Deep-dive: I can explain why realms matter for iframe values, globals, constructors, and `instanceof` surprises.
- [ ] Frontend proof: I can debug a UI freeze by distinguishing long synchronous work from async waiting.

## Scope, Variables, and Closures

Related notes: [[03 - Scope and Variables/01 - Scope Types|Scope Types]], [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]], [[03 - Scope and Variables/03 - var let const|var let const]], [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]], [[03 - Scope and Variables/05 - Closures|Closures]], [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]

- [ ] Must-know: I can explain lexical scope as "where code is written," not where it is called.
- [ ] Must-know: I can explain environment records, outer references, and why closures keep bindings alive.
- [ ] Must-know: I can predict `var`, `let`, and `const` behavior during creation, initialization, reassignment, and TDZ.
- [ ] Must-know: I can fix stale closures in timers, event listeners, promises, and React hooks.
- [ ] Important: I can explain when closure-retained memory is useful and when it becomes a leak.
- [ ] Deep-dive: I can explain why `typeof` is safe for undeclared variables but can still throw in a TDZ.
- [ ] Frontend proof: I can fix a debounced search callback that reads an old query or submits old form state.

## Functions

Related notes: [[04 - Functions Deep Dive/01 - Function Declarations vs Expressions|Function Declarations vs Expressions]], [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]], [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]], [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions and IIFE]], [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]], [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]

- [ ] Must-know: I can compare declarations, expressions, arrows, methods, constructors, and callbacks by behavior, not syntax alone.
- [ ] Must-know: I know arrows do not create their own `this`, `arguments`, or constructor behavior.
- [ ] Must-know: I can use higher-order functions without hiding side effects or making data flow unreadable.
- [ ] Important: I can choose debounce, throttle, `requestAnimationFrame`, or no rate limit based on user experience.
- [ ] Important: I can explain pure functions as a testability and React rendering tool, not a moral rule.
- [ ] Deep-dive: I can explain default parameter scope and how it can surprise a code-output question.
- [ ] Frontend proof: I can implement a debounced search handler with cleanup and explain the stale-state risk.

## `this` Binding

Related notes: [[05 - this Binding/01 - What is this|What is this]], [[05 - this Binding/02 - this in Strict Mode|this in Strict Mode]], [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]], [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]], [[05 - this Binding/05 - call apply bind|call apply bind]], [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]], [[05 - this Binding/07 - React this Examples|React this Examples]]

- [ ] Must-know: I can determine `this` from the call site: default, implicit, explicit, constructor, and lexical.
- [ ] Must-know: I can explain why extracting a method loses the receiver.
- [ ] Must-know: I can explain strict-mode default `this` vs sloppy-mode default `this`.
- [ ] Important: I can decide between `.bind`, wrapper functions, class fields, and regular methods.
- [ ] Important: I can explain why arrow methods can be useful for callbacks but poor for prototype sharing.
- [ ] Deep-dive: I can explain why `.call`, `.apply`, and `.bind` cannot rebind an arrow function's lexical `this`.
- [ ] Frontend proof: I can fix a class component callback or utility method that fails after being passed as a prop.

## Objects and Prototypes

Related notes: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]], [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]], [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]], [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]], [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]], [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]

- [ ] Must-know: I can distinguish own properties, inherited properties, enumerable properties, and descriptors.
- [ ] Must-know: I can explain prototype lookup and why classes are syntax over prototype-based behavior.
- [ ] Must-know: I can trace what `new` does: creates an object, links prototype, binds `this`, runs constructor, returns an object.
- [ ] Must-know: I can explain shallow copy, shared nested references, and React state mutation bugs.
- [ ] Important: I can choose spread, `Object.assign`, `structuredClone`, targeted immutable updates, or domain-specific normalization.
- [ ] Important: I can avoid prototype pollution hazards when merging untrusted objects.
- [ ] Deep-dive: I can explain descriptors and why class methods are non-enumerable.
- [ ] Frontend proof: I can fix a state update where a copied array still mutates nested objects.

## Arrays and Iteration

Related notes: [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]], [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]], [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]], [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]], [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]], [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]]

- [ ] Must-know: I can name mutating methods and avoid them in React state unless I intentionally clone first.
- [ ] Must-know: I can choose `map`, `filter`, `reduce`, `some`, `every`, `find`, and `for...of` based on intent.
- [ ] Must-know: I can explain why `forEach` returns `undefined` and is not await-aware in the way many people expect.
- [ ] Important: I can optimize large list transforms with normalization, memoization, indexing, pagination, or virtualization.
- [ ] Important: I can explain holes, sparse arrays, and why array-like objects are not automatically arrays.
- [ ] Deep-dive: I can explain iterables, iterators, generators, and where spread/destructuring depend on the iteration protocol.
- [ ] Frontend proof: I can transform API data into UI view models without mutating cached or shared objects.

## Async JavaScript

Related notes: [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]], [[08 - Async JavaScript/02 - Promises|Promises]], [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]], [[08 - Async JavaScript/04 - Async Await|Async Await]], [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]], [[08 - Async JavaScript/06 - AbortController|AbortController]], [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]

- [ ] Must-know: I can explain that a promise represents eventual completion, not a background thread.
- [ ] Must-know: I can compare `then` chains with `async`/`await` and describe where errors are caught.
- [ ] Must-know: I can choose `Promise.all`, `allSettled`, `race`, and `any` by failure semantics.
- [ ] Must-know: I can cancel fetch work with `AbortController` and guard against late results.
- [ ] Important: I can prevent duplicate submissions with disabled state, idempotency, in-flight guards, or request dedupe.
- [ ] Important: I can design error handling that separates transport errors, HTTP errors, validation errors, and unexpected bugs.
- [ ] Deep-dive: I can explain unhandled promise rejection timing and why "try/catch around a promise" often fails.
- [ ] Frontend proof: I can implement safe loading, error, success, cancellation, and retry behavior for a form or search screen.

## Event Loop and Rendering

Related notes: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]], [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]], [[09 - Event Loop Advanced/04 - Timers|Timers]], [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]], [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]], [[09 - Event Loop Advanced/07 - Code Output Questions|Event Loop Code Output Questions]]

- [ ] Must-know: I can order synchronous code, promise jobs/microtasks, timers/tasks, and rendering opportunities.
- [ ] Must-know: I can explain why promise callbacks normally run before `setTimeout(..., 0)`.
- [ ] Must-know: I can avoid starving rendering with endless microtasks or long synchronous loops.
- [ ] Important: I can use task splitting, `requestAnimationFrame`, idle work, workers, and virtualization for UI responsiveness.
- [ ] Important: I can explain why timer delay is not a precise scheduling guarantee.
- [ ] Deep-dive: I can connect ECMAScript jobs to the HTML event loop processing model without mixing the two layers.
- [ ] Frontend proof: I can fix typing jank in a large filter UI and verify it with DevTools.

## Modules

Related notes: [[10 - Modules/01 - ES Modules|ES Modules]], [[10 - Modules/02 - CommonJS|CommonJS]], [[10 - Modules/03 - Named vs Default Exports|Named vs Default Exports]], [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]], [[10 - Modules/05 - Live Bindings|Live Bindings]], [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]], [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]

- [ ] Must-know: I can explain static imports, dynamic imports, module evaluation, and strict mode in ES modules.
- [ ] Must-know: I can explain live bindings and why they are not copied snapshots.
- [ ] Must-know: I can diagnose circular import failures caused by reading uninitialized exports too early.
- [ ] Important: I can use dynamic import for route-level or interaction-level code splitting without hurting UX.
- [ ] Important: I can make modules tree-shakeable by avoiding unnecessary side effects and broad barrel exports.
- [ ] Deep-dive: I can compare ES modules and CommonJS by loading model, binding model, and tooling impact.
- [ ] Frontend proof: I can split a heavy chart/editor/admin module and explain the loading, caching, and error tradeoffs.

## Error Handling

Related notes: [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]], [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]], [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]], [[11 - Error Handling/04 - Promise Rejections|Promise Rejections]], [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]], [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]

- [ ] Must-know: I can throw, catch, rethrow, and preserve useful error context.
- [ ] Must-know: I can explain why `try/catch` catches synchronous errors and awaited rejections, but not unrelated future callbacks.
- [ ] Must-know: I can classify API failures and present user-safe messages without hiding developer diagnostics.
- [ ] Important: I can explain what React error boundaries catch and what they do not catch.
- [ ] Important: I can design retry, fallback, logging, and recovery behavior without infinite loops.
- [ ] Deep-dive: I can explain `finally` return/throw behavior and why it can accidentally swallow an error.
- [ ] Frontend proof: I can make a form submission resilient to HTTP errors, validation errors, aborts, and unexpected exceptions.

## Advanced Language Concepts

Related notes: [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]], [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]], [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]], [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]], [[12 - Advanced Language Concepts/07 - Symbols|Symbols]], [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]], [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]], [[12 - Advanced Language Concepts/10 - BigInt Date RegExp JSON|BigInt Date RegExp JSON]]

- [ ] Must-know: I can explain primitives, references, identity, equality, and `Object.is`.
- [ ] Must-know: I know which coercions are acceptable in production and which create interview and bug risk.
- [ ] Must-know: I can use optional chaining and nullish coalescing without hiding invalid data.
- [ ] Important: I can choose object, `Map`, `Set`, `WeakMap`, or `WeakSet` based on keys, uniqueness, and lifetime.
- [ ] Important: I can explain JSON limitations for `Date`, `BigInt`, `undefined`, functions, `Map`, `Set`, and circular data.
- [ ] Deep-dive: I can explain symbols, generator control flow, and iterator protocols when they appear in libraries.
- [ ] Frontend proof: I can prevent a rendering bug caused by `||` replacing valid `0`, empty string, or `false` values.

## Performance and Memory

Related notes: [[13 - Performance and Memory/01 - Memory Management|Memory Management]], [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]], [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]], [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]], [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]], [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]], [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]], [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]

- [ ] Must-know: I can explain reachability and why garbage collection is automatic but not magic.
- [ ] Must-know: I can identify leaks from retained closures, listeners, timers, caches, subscriptions, and detached DOM references.
- [ ] Must-know: I can distinguish CPU performance, memory growth, network latency, and rendering cost.
- [ ] Important: I can profile before optimizing and explain what signal I used.
- [ ] Important: I can choose memoization only when identity stability or expensive computation justifies it.
- [ ] Deep-dive: I can use heap snapshots, allocation timelines, and performance recordings to prove a leak or bottleneck.
- [ ] Frontend proof: I can fix a component that gets slower after repeated navigation.

## React and Next.js JavaScript

Related notes: [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]], [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]], [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]], [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]], [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]], [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]], [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]], [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]], [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]], [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]

- [ ] Must-know: I can explain that each render has its own values, closures, and effects.
- [ ] Must-know: I can fix stale closures with functional updates, dependencies, refs, or moving logic to the right scope.
- [ ] Must-know: I can explain dependency arrays using reactive values and referential equality.
- [ ] Must-know: I can perform immutable state updates for arrays and nested objects.
- [ ] Important: I can cancel or ignore stale async work in effects and explain cleanup timing.
- [ ] Important: I can explain the Next.js server/client boundary and why browser APIs must stay on the client side.
- [ ] Deep-dive: I can diagnose hydration mismatches from time, randomness, browser-only state, invalid HTML, or differing render inputs.
- [ ] Frontend proof: I can fix a search, dashboard, or checkout component that races requests, leaks listeners, or hydrates differently.

## DOM and Browser APIs

Related notes: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]], [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]], [[19 - DOM and Browser APIs/06 - Observers|Observers]], [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]], [[19 - DOM and Browser APIs/12 - DOM and Browser APIs Checklist|DOM and Browser APIs Checklist]]

- [ ] Must-know: I can define reflow vs repaint and fix a layout-thrashing loop by batching reads then writes.
- [ ] Must-know: I can write event delegation with `closest()` and distinguish `preventDefault`/`stopPropagation`/`stopImmediatePropagation`.
- [ ] Must-know: I can compare cookies, localStorage, sessionStorage, and IndexedDB on security and sync/async.
- [ ] Must-know: I can build lazy loading / infinite scroll with IntersectionObserver and correct cleanup.
- [ ] Must-know: I can write a fetch wrapper with `res.ok` checks, typed errors, `AbortSignal.timeout`, and safe retries.
- [ ] Important: I can decide worker vs chunking and explain structured clone vs transferables.
- [ ] Frontend proof: I can explain SPA routing mechanics (pushState/popstate) and what Next's router adds.

## Network and Security

Related notes: [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]], [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]], [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]], [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]], [[20 - Network and Security/05 - XSS|XSS]], [[20 - Network and Security/09 - Network and Security Checklist|Network and Security Checklist]]

- [ ] Must-know: I can turn status codes into deliberate code paths and write correct Cache-Control per resource.
- [ ] Must-know: I can explain that CORS protects the user (not the server) and read a preflight exchange.
- [ ] Must-know: I can defend a token-storage choice and explain the XSS blast radius of each.
- [ ] Must-know: I can classify XSS, say what React escapes, and sanitize rich text safely.
- [ ] Important: I can explain CSRF from cookie mechanics and match defenses to the auth model.
- [ ] Deep-dive: I can explain prototype pollution and name supply-chain mitigations.
- [ ] Frontend proof: I can pick polling vs SSE vs WebSocket from requirements and defend it.

## React Internals and Patterns

Related notes: [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]], [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]], [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]], [[21 - React Internals and Patterns/10 - React 19|React 19]], [[21 - React Internals and Patterns/13 - React Internals Checklist|React Internals Checklist]]

- [ ] Must-know: I can separate render from commit and explain why render must be pure.
- [ ] Must-know: I can explain why index keys corrupt stateful lists and how identity decides state survival.
- [ ] Must-know: I can choose value vs updater form and explain automatic batching.
- [ ] Must-know: I can control context re-renders by splitting contexts and stabilizing values.
- [ ] Important: I can place every effect hook on the render-to-paint timeline and choose correctly.
- [ ] Important: I can explain tearing and bind an external store with `useSyncExternalStore`.
- [ ] Must-know: I can use React 19 Actions/hooks and explain the React Compiler's impact on memoization.

## Next.js Deep Dive

Related notes: [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]], [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]], [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]], [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]], [[22 - Next.js Deep Dive/09 - Next.js Deep Dive Checklist|Next.js Deep Dive Checklist]]

- [ ] Must-know: I can choose a rendering strategy per route (and per region with PPR) from requirements.
- [ ] Must-know: I can name the four caching layers and diagnose stale data by layer.
- [ ] Must-know: I can invalidate the right cache after a mutation with tags or paths.
- [ ] Must-know: I can explain the Server Action security model and secure one properly.
- [ ] Important: I can choose Route Handler vs Server Action vs Server Component and place middleware correctly.
- [ ] Important: I can eliminate request waterfalls and dedupe reads.
- [ ] Frontend proof: I can explain why an SPA doesn't rank and how server-rendered metadata fixes it.
- [ ] Must-know (Next 16): I can distinguish `updateTag`, `revalidateTag(tag, "max")`, and `refresh()` by contract, and know `proxy.ts` replaced `middleware.ts`.

## TypeScript Deep Dive

Related notes: [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]], [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]], [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|Runtime Validation]], [[23 - TypeScript Deep Dive/09 - React and Next TypeScript Patterns|React and Next TypeScript Patterns]], [[23 - TypeScript Deep Dive/10 - TypeScript Checklist|TypeScript Checklist]]

- [ ] Must-know: I can explain structural typing and type erasure, and why types don't validate runtime input.
- [ ] Must-know: I can model async UI as a discriminated union with exhaustiveness checking.
- [ ] Must-know: I can protect an untrusted boundary with `unknown` plus schema validation and infer the static type from the schema.
- [ ] Important: I can write a constrained generic that preserves a caller relationship — and say when not to.
- [ ] Important: I can explain the `strict` family, `bundler` vs `nodenext` resolution, and where package types come from.
- [ ] Frontend proof: I can type props, events, refs, hooks, and a generic component, and map entities to DTOs at the RSC boundary.

## Testing and Quality

Related notes: [[24 - Testing and Quality/01 - Testing Mental Model|Testing Mental Model]], [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|Component Testing]], [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Deterministic Tests]], [[24 - Testing and Quality/08 - Testing Nextjs Boundaries|Testing Next.js Boundaries]], [[24 - Testing and Quality/12 - Testing Checklist|Testing Checklist]]

- [ ] Must-know: I can judge a test by confidence, cost, and failure signal, and allocate failure classes to the cheapest layer.
- [ ] Must-know: I can write component tests through user behavior (role queries, userEvent, findBy) that survive refactors.
- [ ] Must-know: I can make async tests deterministic: fake timers, MSW, forced interleavings, no sleeps.
- [ ] Must-know: I can test a Server Action by direct invocation with hostile inputs.
- [ ] Important: I can keep a Playwright suite non-flaky and explain each anti-flake rule mechanically.
- [ ] Important: I can name what typecheck, lint, format, tests, and build each uniquely catch in CI.

## Accessibility and Inclusive UX

Related notes: [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]], [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms]], [[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|Dialogs and Focus Traps]], [[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|Manual Checks]], [[25 - Accessibility and Inclusive UX/10 - Accessibility Checklist|Accessibility Checklist]]

- [ ] Must-know: I can enumerate what `<button>` provides that a div-with-handler doesn't, and apply native-first.
- [ ] Must-know: I can manage focus through transitions: dialog open/close, deletions, SPA route changes.
- [ ] Must-know: I can build a form whose async errors are associated (`aria-describedby`, `aria-invalid`) and announced (focusable summary).
- [ ] Must-know: I can state the modal contract and what `showModal()`/popover/`inert` provide.
- [ ] Important: I can choreograph live-region announcements without spamming.
- [ ] Important: I can state what axe catches vs what only keyboard/screen-reader passes find — and run both protocols.

## System and Design Rounds

Related notes: [[29 - Frontend System Design/00 - Frontend System Design MOC|Frontend System Design MOC]], [[30 - Backend System Design/00 - Backend System Design MOC|Backend System Design MOC]], [[31 - Low Level Design/00 - Low Level Design MOC|Low Level Design MOC]]

- [ ] Must-know: I can run RADIO on a "design X" prompt in 35 minutes — requirements first, every decision traceable.
- [ ] Must-know: I can introduce caching with the 5-step method and name the three cache problems (stampede, consistency, hot keys).
- [ ] Important: I can place a feature on the consistency spectrum and connect eventual consistency to optimistic UI.
- [ ] Important: I can choose a database and pagination style from access patterns, and reject premature sharding with current numbers.
- [ ] Important: I can derive clean classes from requirements, argue composition over inheritance, and name where each design pattern already lives in frontend code.

## Labs Proof

Related notes: [[90 - Labs/00 - Labs MOC|Labs MOC]]

- [ ] I have built at least two of the four labs and written retrospectives.
- [ ] I can demonstrate a race condition, a cache-invalidation failure, and a focus-loss bug on demand — and fix each.

## Practical Scenario Proof

Related notes: [[17 - Practical Frontend Scenarios/01 - Fixing Stale Closure in React|Fixing Stale Closure in React]], [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]], [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]], [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]], [[17 - Practical Frontend Scenarios/05 - Avoiding Mutation in State|Avoiding Mutation in State]], [[17 - Practical Frontend Scenarios/06 - Cleaning Event Listeners|Cleaning Event Listeners]], [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]], [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]], [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]], [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]

- [ ] I can write a failing implementation and explain the exact bug.
- [ ] I can write the fixed implementation with comments.
- [ ] I can name the tradeoff: simplicity, correctness, UX, network cost, memory, or maintainability.
- [ ] I can say how I would prove the fix with logs, tests, DevTools, or manual reproduction.
- [ ] I can answer the interview version without overfitting to React only.

## Interview and Code-Output Proof

Related notes: [[15 - Interview Preparation/02 - Mid Level Questions|Mid Level Questions]], [[15 - Interview Preparation/03 - Strong Mid Level Questions|Strong Mid Level Questions]], [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]], [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]], [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]], [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]], [[18 - Revision Plans/04 - 30 Interview Questions|30 Interview Questions]], [[18 - Revision Plans/05 - 20 Code Output Questions|20 Code Output Questions]]

- [ ] I answer with output first, then mechanism, then production relevance.
- [ ] I avoid vague folklore phrases and name the actual JavaScript or React rule.
- [ ] I can slow down and trace creation phase, call site, prototype lookup, microtask order, or identity comparison.
- [ ] I can explain what would change in modules, strict mode, browsers, Node, React, or Next.js.
- [ ] I can ask a clarifying question when environment details affect the answer.

## Final Readiness Test

Run this final audit after the 7-day or 14-day plan:

1. Choose 5 concepts from different modules.
2. For each concept, write a 30-second answer and a 2-minute answer.
3. Solve 5 code-output questions without reading the explanation.
4. Pick 2 practical scenarios and write the bug, fix, tradeoff, and verification plan.
5. Review every wrong answer and add it to a weak-area list.
6. Redo the weak-area questions 24 hours later.

## Sources

- ECMAScript Language Specification: https://tc39.es/ecma262/
- HTML Living Standard event loops and web application APIs: https://html.spec.whatwg.org/multipage/webappapis.html
- MDN JavaScript reference and guide: https://developer.mozilla.org/en-US/docs/Web/JavaScript
- MDN Promise reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise
- MDN AbortController reference: https://developer.mozilla.org/en-US/docs/Web/API/AbortController
- React `useEffect` reference: https://react.dev/reference/react/useEffect
- Next.js Server and Client Components docs: https://nextjs.org/docs/app/getting-started/server-and-client-components
- web.dev RAIL performance model: https://web.dev/articles/rail

## Related Notes

- [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]]
- [[18 - Revision Plans/03 - 14 Day Deep Study Plan|14 Day Deep Study Plan]]
- [[18 - Revision Plans/04 - 30 Interview Questions|30 Interview Questions]]
- [[18 - Revision Plans/05 - 20 Code Output Questions|20 Code Output Questions]]
- [[18 - Revision Plans/06 - 10 Practical Frontend Scenarios|10 Practical Frontend Scenarios]]
- [[01 - Roadmap|Roadmap]]
