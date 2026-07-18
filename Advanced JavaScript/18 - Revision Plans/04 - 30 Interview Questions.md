---
tags: [javascript, revision, interview, 30-interview-questions]
module: "18 - Revision Plans"
priority: must-know
status: not-started
---

# 30 Interview Questions

Use these questions as a structured mock interview. For each answer, follow this shape:

1. Direct answer in 1 or 2 sentences.
2. Accurate mechanism.
3. Small code example or output trace.
4. Real frontend bug or decision point.
5. Safe production pattern.

Avoid vague folklore answers. Name the actual rule: binding creation, receiver, prototype lookup, promise job, task, dependency comparison, or rendering boundary.

## Runtime and Execution

### 1. What is the difference between ECMAScript and JavaScript in the browser?

Strong answer:

ECMAScript defines the core language: syntax, values, objects, functions, promises, modules, and execution semantics. Browser JavaScript also includes host APIs such as DOM, events, timers, fetch, storage, rendering, and workers.

Production angle:

If a bug involves `setTimeout`, `fetch`, DOM events, rendering, or hydration, you need browser or framework documentation in addition to the ECMAScript spec.

Related notes: [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]], [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]

### 2. What is an execution context?

Strong answer:

An execution context is the runtime record used to execute code. It includes lexical environment information, variable environment information, and the current `this` binding for that context.

Production angle:

Execution context explains why a function has its own local bindings and why a stack trace shows nested calls in a specific order.

Related notes: [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]], [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]

### 3. Explain hoisting without saying "JavaScript moves declarations."

Strong answer:

Hoisting is a shorthand for creation-phase binding setup. Function declarations are initialized early, `var` bindings are initialized to `undefined`, and `let`/`const` bindings exist but cannot be accessed before initialization because of the TDZ.

Trap:

Saying "code moves to the top" breaks down for `let`, `const`, class declarations, imports, and temporal dead zone behavior.

Related notes: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

### 4. What is the call stack and how does it fail?

Strong answer:

The call stack tracks active function calls. Each call pushes a frame, returning or throwing unwinds frames, and excessive recursion can overflow the stack.

Production angle:

A stack trace is a debugging path. A stack overflow from recursive rendering, parser logic, or deeply nested traversal usually means you need a base case, iterative approach, or chunked work.

Related notes: [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]

### 5. What are realms, agents, and jobs in practical terms?

Strong answer:

A realm owns its global object and intrinsics. An agent is the spec-level execution agent. Jobs are scheduled pieces of ECMAScript work, such as promise reactions, while the browser maps this into its event-loop model.

Production angle:

Realms explain iframe/global-constructor surprises. Jobs and host event loops explain why promise callbacks run after sync code but before many timer callbacks.

Related notes: [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]], [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]

## Scope and Closures

### 6. What is lexical scope?

Strong answer:

Lexical scope means name resolution is determined by where code is written in the source, not where a function is called. Inner scopes can access outer bindings through the lexical environment chain.

Production angle:

Lexical scope is why callback code can access local variables from the component or function where the callback was created.

Related notes: [[03 - Scope and Variables/01 - Scope Types|Scope Types]], [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]

### 7. What is a closure?

Strong answer:

A closure is a function plus access to the lexical bindings from the environment where it was created. It retains bindings, not a magical frozen copy of every value.

Production angle:

Closures power callbacks, memoized functions, event handlers, hooks, and private state. They also cause stale values and retained-memory bugs when lifetime is misunderstood.

Related notes: [[03 - Scope and Variables/05 - Closures|Closures]], [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]

### 8. Why do stale closures happen?

Strong answer:

A stale closure happens when a callback keeps reading values from an older lexical environment while newer values exist elsewhere. In React, each render creates its own values, so an effect or timer can close over values from a previous render.

Safe pattern:

Use functional state updates, correct dependencies, refs for latest mutable values, or redesign the effect so the callback is created in the right lifecycle.

Related notes: [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]], [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

### 9. What is the temporal dead zone?

Strong answer:

The TDZ is the period between creation of a lexical binding and its initialization. Accessing `let`, `const`, or class bindings in that period throws `ReferenceError`.

Code signal:

`typeof missingName` is `"undefined"` for an undeclared name, but `typeof localName` can throw if `localName` is a lexical binding still in its TDZ.

Related notes: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

### 10. How do closures affect memory?

Strong answer:

A closure can keep outer bindings reachable after the outer function returns. This is useful for stateful callbacks, but it can keep large data, DOM nodes, or subscriptions alive longer than intended.

Production angle:

If memory grows after navigation, inspect listeners, timers, caches, subscriptions, and closures that still reference component data.

Related notes: [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]], [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]

## Functions and `this`

### 11. How do function declarations, expressions, and arrows differ?

Strong answer:

Function declarations are initialized during environment setup. Function expressions are assigned when execution reaches the assignment. Arrow functions have lexical `this`, no own `arguments`, and cannot be used as constructors.

Production angle:

Use arrows for callbacks that should inherit surrounding `this`; use regular methods when the receiver matters.

Related notes: [[04 - Functions Deep Dive/01 - Function Declarations vs Expressions|Function Declarations vs Expressions]], [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]

### 12. How is `this` determined?

Strong answer:

For regular functions, `this` is determined by the call site: default binding, implicit receiver, explicit `.call`/`.apply`/`.bind`, or constructor call with `new`. Arrow functions use lexical `this` from the surrounding scope.

Trap:

`const fn = obj.method; fn()` is not the same call site as `obj.method()`.

Related notes: [[05 - this Binding/01 - What is this|What is this]], [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]

### 13. What does `.bind` do?

Strong answer:

`.bind` returns a new function with a fixed `this` value and optionally pre-applied arguments. Calling the bound function with `.call` or `.apply` does not replace the bound `this`.

Production angle:

Binding is useful for stable callback behavior, but it creates a new function when called. Avoid binding inside hot render paths unless you understand the identity impact.

Related notes: [[05 - this Binding/05 - call apply bind|call apply bind]]

### 14. What is a higher-order function?

Strong answer:

A higher-order function receives a function, returns a function, or both. It is a tool for composition, callbacks, decorators, throttling, memoization, and data transformation.

Production angle:

Higher-order functions can improve reuse, but they can also hide side effects and make debugging harder if the abstraction is too clever.

Related notes: [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]

### 15. When would you debounce or throttle?

Strong answer:

Debounce waits until activity pauses; throttle limits work to at most once per interval. Debounce fits search-as-you-type; throttle fits scroll/resize updates where periodic feedback is enough.

Production angle:

Always think about cleanup and stale closures. A debounced callback that survives unmount or reads old state is a bug factory.

Related notes: [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]], [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]

## Objects, Prototypes, and Arrays

### 16. How does the prototype chain work?

Strong answer:

Property access first checks the object itself. If the property is not found, JavaScript follows the object's prototype chain until it finds the property or reaches `null`.

Production angle:

Use `Object.hasOwn` or `hasOwnProperty` when inherited values must not count, especially with user-provided objects.

Related notes: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]

### 17. What does `new` do?

Strong answer:

`new` creates a new object, links it to the constructor's prototype, calls the constructor with `this` bound to the new object, and returns the object unless the constructor explicitly returns another object.

Production angle:

Understanding `new` clarifies classes, inheritance, instance methods, and why arrow functions cannot be constructors.

Related notes: [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]

### 18. Why is object spread shallow?

Strong answer:

Object spread copies enumerable own properties into a new object. If a property value is itself an object, the reference is copied, not the nested object.

Production angle:

In React state, `{ ...state }` is not enough if you mutate `state.user.profile.name`. Copy each changed level or normalize the data.

Related notes: [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]], [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]

### 19. Which array methods mutate, and why does it matter?

Strong answer:

Methods like `push`, `pop`, `splice`, `sort`, `reverse`, `fill`, and `copyWithin` mutate. Methods like `map`, `filter`, `slice`, `concat`, and modern immutable methods return new arrays.

Production angle:

Mutation can break React rendering assumptions, memoization, cache integrity, and undo/history features.

Related notes: [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]], [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]

### 20. How do you choose between `map`, `filter`, `reduce`, `forEach`, and `for...of`?

Strong answer:

Use `map` to transform, `filter` to keep/remove, `reduce` to accumulate, `forEach` for side effects, and `for...of` when imperative control flow such as `break`, `continue`, or `await` is clearer.

Production angle:

Choose readability first, then optimize when measurements show the transformation is expensive.

Related notes: [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]], [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]]

## Async, Event Loop, and Errors

### 21. What is a promise?

Strong answer:

A promise represents the eventual fulfillment or rejection of an asynchronous operation. Promise reactions run later as jobs/microtasks after the current synchronous execution completes.

Production angle:

A promise is not cancellation by itself and not a thread. You still need loading state, error handling, cancellation/ignore logic, and user feedback.

Related notes: [[08 - Async JavaScript/02 - Promises|Promises]]

### 22. How does `async`/`await` work?

Strong answer:

An `async` function always returns a promise. `await` pauses the async function's continuation until the awaited value resolves or rejects, then resumes that continuation through promise-job scheduling.

Trap:

`try/catch` catches an awaited rejection, but it does not catch an unrelated future callback unless that callback is awaited or its promise is returned.

Related notes: [[08 - Async JavaScript/04 - Async Await|Async Await]], [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]

### 23. Compare `Promise.all`, `allSettled`, `race`, and `any`.

Strong answer:

`all` fulfills when all fulfill and rejects on the first rejection. `allSettled` waits for every input and reports every status. `race` settles with the first settled input. `any` fulfills with the first fulfillment and rejects only if all inputs reject.

Production angle:

Pick by UX: all-or-nothing screens use `all`; partial dashboards often use `allSettled`; timeouts can use `race`; fallback providers can use `any`.

Related notes: [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]

### 24. What are tasks and microtasks?

Strong answer:

In the browser event loop, tasks include work such as timers and events. Microtasks include promise reactions and `queueMicrotask`; they run after the current task before the browser moves on to other tasks and rendering opportunities.

Production angle:

Too many microtasks can delay rendering. Long synchronous work blocks both timers and paint.

Related notes: [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]], [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]

### 25. How should frontend API errors be handled?

Strong answer:

Separate transport failure, HTTP non-2xx response, parse failure, validation/domain error, abort, and unexpected bug. Show user-safe messages, preserve developer diagnostics, and avoid retry loops.

Production angle:

`fetch` resolves for HTTP error statuses, so you must check `response.ok` yourself.

Related notes: [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]], [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]

## React and Next.js JavaScript

### 26. Why do React hooks have dependency arrays?

Strong answer:

Dependency arrays tell React which reactive values an effect or memoized value depends on. React compares dependencies by identity using `Object.is`, so unstable object/function references can rerun effects even when their contents look similar.

Production angle:

Do not lie to the dependency array. Fix the data flow by moving code, memoizing intentionally, using refs for non-render data, or deriving values inside the effect.

Related notes: [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]], [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]

### 27. How do you prevent React state mutation bugs?

Strong answer:

Create new references for every level that changes, keep unchanged references stable, and avoid mutating arrays or objects that React state, props, caches, or memoized selectors still reference.

Production angle:

Mutation can cause missed renders, stale memoized values, corrupted caches, and hard-to-reproduce UI bugs.

Related notes: [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]], [[17 - Practical Frontend Scenarios/05 - Avoiding Mutation in State|Avoiding Mutation in State]]

### 28. How do you handle async effects and race conditions?

Strong answer:

Start async work inside the effect, clean it up when dependencies change or the component unmounts, abort when possible, and guard state updates so older results cannot overwrite newer state.

Production angle:

The user can type quickly, navigate away, retry, or lose connection. Correct async UI handles all of those without duplicate submissions or stale results.

Related notes: [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]], [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]

### 29. What is the Next.js server/client JavaScript boundary?

Strong answer:

Server Components run on the server and cannot use browser-only APIs or client hooks. Client Components opt into client-side JavaScript with `"use client"` and can use state, effects, event handlers, and browser APIs.

Production angle:

Place interactivity as low as possible in the tree, keep server-renderable data on the server, and avoid hydration mismatches from browser-only reads during server render.

Related notes: [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]

### 30. How do you debug frontend performance and memory?

Strong answer:

First identify the bottleneck: CPU, rendering/layout, memory growth, network, or bundle/loading. Use DevTools performance recordings, heap snapshots, allocation timelines, React profiling, logs, and small reproductions before choosing an optimization.

Production angle:

`useMemo` is not a universal fix. Sometimes the right answer is cleanup, virtualization, code splitting, data normalization, request dedupe, worker offloading, or simpler UI work.

Related notes: [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]], [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]], [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]

## Bonus Questions — Modules 19–22

These extend the set with browser platform, network/security, React internals, and Next.js questions. Answer them to the same standard: direct answer, mechanism, example, bug, safe pattern.

### 31. What is event delegation and why do dynamic lists use it?

Strong answer:

Attach one listener to a common ancestor and use bubbling plus `event.target.closest()` to find which descendant was activated, instead of a listener per child. It handles elements added later, uses one listener instead of thousands, and simplifies cleanup.

Trap:

`event.target` is the deepest element (could be an icon inside a button), so resolve upward with `closest()` and guard for `null`; never compare `target === row`.

Production angle:

It's the mechanism React's synthetic events use internally (root-delegated listeners dispatching through the fiber tree), which is why per-row `onClick` props are cheap.

Related notes: [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]], [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]

### 32. Does CORS protect the server? Explain the same-origin policy correctly.

Strong answer:

No — CORS protects the *user*. The same-origin policy is a browser rule that lets scripts send cross-origin requests but blocks them from *reading* the responses. CORS is the server's opt-in that permits specific origins to read responses; it is not the blocker. The server is equally reachable from curl/Postman, which have no same-origin policy.

Trap:

A "CORS-blocked" simple request still executed on the server — only the response was withheld from JavaScript. That's why CSRF defenses can't rely on CORS.

Production angle:

Credentialed cross-origin requests need `credentials: "include"`, `Access-Control-Allow-Credentials: true`, an explicit echoed origin plus `Vary: Origin`, and `SameSite=None; Secure` cookies. Fixes live server-side.

Related notes: [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]], [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]

### 33. Why do index keys corrupt state in a React list?

Strong answer:

`key={index}` tells React "the item at position 0 is always the same item." On reorder/insert/delete, positions stay `0,1,2…` while the data at them changes, so React reuses the old component instances (with their state) against new data — scrambling per-item state like draft text, focus, or checkbox selection. Use a stable id that travels with the item (`key={item.id}`).

Trap:

`key={Math.random()}` "fixes" stale display by remounting everything each render — destroying state, focus, and performance. It's a severe anti-pattern.

Production angle:

A component's identity is position + type + key, and identity decides whether state and DOM survive. You can also *reset* state deliberately with `key={id}`, replacing effect-based clearing.

Related notes: [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]

### 34. Walk through the Next.js caching layers and how you'd fix stale data.

Strong answer:

Four layers: Request Memoization (dedupes identical fetches within one render), the Data Cache (persists fetch results across requests/deploys), the Full Route Cache (rendered output of static routes), and the client Router Cache (RSC payloads of visited routes). "Stale data" means a value is trapped in one of these; you diagnose by scope (one render, across requests, across navigations).

Trap:

A bare DB write updates none of the caches — after a mutation you call `revalidateTag`/`revalidatePath` to purge the Data/Route caches and refresh the client Router Cache.

Production angle:

Defaults flipped: Next 14 cached fetch and GET handlers by default (stale surprises); Next 15 made them uncached and Router Cache staleTime 0 (extra-request surprises); Next 16 Cache Components makes caching explicit with `use cache`. Tag reads by data dependency; revalidate the tag on write.

Related notes: [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]], [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]]

### 35. Where should an auth token live, and what changes under XSS?

Strong answer:

Anything JavaScript can read (localStorage, sessionStorage, non-HttpOnly cookies) is readable by any XSS payload and exfiltratable — replayable offline until expiry. An HttpOnly cookie can't be read by script, reducing an XSS attacker to riding the open session (no offline replay). The pragmatic pattern: a short-lived access token in memory plus a rotating refresh token in an HttpOnly, Secure, SameSite cookie.

Trap:

HttpOnly isn't total immunity — XSS can still issue same-origin requests using the cookie while the tab is open. The real defense is XSS prevention + CSP + short expiry + HttpOnly together.

Production angle:

Cookie auth reopens CSRF (mitigate with SameSite=Lax + tokens); header-token auth avoids CSRF but exposes the token to XSS. You pick which attack surface, then defend it.

Related notes: [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]], [[20 - Network and Security/05 - XSS|XSS]]

### 36. Why is a Next.js Server Action a security risk if you treat it as "just a function"?

Strong answer:

A `"use server"` function becomes a public HTTP endpoint with a stable id, callable directly by anyone — not just your UI. An attacker can replay it with crafted arguments, bypassing any client-side gating. So every action must authenticate, authorize (on the specific resource), and validate its input with a schema inside the function.

Trap:

"It's only called from my admin page" is not a security control — the client UI never runs for an attacker hitting the endpoint directly. The classic hole is an "admin-only" action with no in-function authZ, replayable for privilege escalation.

Production angle:

TypeScript types are compile-time only; validate `formData`/arguments at runtime with Zod. Extract a `withAuth` wrapper so the checks are consistent and hard to forget.

Related notes: [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]], [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]

## Bonus Questions — Modules 23–25

### 37. Your API client is fully typed. Why do you still validate responses at runtime?

Strong answer:

TypeScript types are erased before the code runs — at the network boundary the annotations are hope, not enforcement. The deployed backend can be an older version, a proxy can reshape the payload, or the response can be an error body. I type the parsed JSON as `unknown` and convert it through one schema validation (Zod), inferring the static type from the schema so validator and type can't drift.

Trap:

"Our backend is TypeScript too, we share types" — shared types prove both sides *compile* against the same shape; they say nothing about what actually arrives on the wire at runtime.

Production angle:

One parse at the data-access function; components consume the validated type and never see `unknown`. Failures surface at the boundary with useful issues instead of `undefined is not a function` three screens later.

Related notes: [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|Runtime Validation]], [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]]

### 38. How do you write a test that proves a race-condition fix, given races are intermittent?

Strong answer:

Make the interleaving deterministic: keep both requests pending (MSW handlers returning promises I resolve manually), resolve the *second* request first, then the first, and assert the stale response's data never renders. The test forces exactly the arrival order that only sometimes happens in production, so it fails before the fix (abort/ignore stale) and passes after.

Trap:

Adding sleeps and hoping to hit the race — that's a flaky test *about* a flaky behavior. If you can't name the interleaving you're testing, you don't understand the bug yet.

Production angle:

Same technique pins AbortController cleanup: unmount mid-request and assert the abort fired and no state update followed. These tests are often the only reliable reproduction the bug will ever have.

Related notes: [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Deterministic Tests]], [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]], [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]

### 39. A div with an onClick "works fine." What's actually missing versus a button, and when does it bite?

Strong answer:

A `<button>` ships a role in the accessibility tree, Tab focusability, Enter and Space activation, and disabled semantics. The div has none: keyboard users can't reach or trigger it, screen readers announce nothing interactive. Reconstructing that on a div takes role, tabindex, two key handlers with correct preventDefault, disabled handling, and focus styles — five permanent maintenance burdens replacing zero.

Trap:

Adding `role="button"` alone makes it *worse*: AT now announces a button the keyboard still can't operate — a promise without the behavior.

Production angle:

Native-first is also cheaper engineering: native controls work before hydration, participate in forms, and are queryable by role in tests. Most real-world WCAG failures are rebuilt platform features.

Related notes: [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]], [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA]]

### 40. Your form shows validation errors visually, but a screen-reader user says "nothing happens" on submit. Diagnose and fix.

Strong answer:

The errors exist only as pixels: not associated with fields, not announced, and focus never moves. Fix in three relationships: per-field `aria-describedby` pointing at the error text plus `aria-invalid`; a focusable error summary (`tabindex="-1"`, focused on failed submit) listing links to each broken field; and a pending state that stays focusable (`aria-disabled` + text change) instead of a hard `disabled` that drops focus to body.

Trap:

`role="alert"` on a region that's conditionally rendered *with* its message often announces nothing — AT registers live regions at render and announces subsequent changes. Render the region always; swap its content.

Production angle:

Pin the contract in component tests — `toHaveAccessibleDescription`, `toBeInvalid`, focus assertions — so a refactor can't silently drop the wiring. Axe passes this form both before and after the fix; only behavioral tests and manual passes see it.

Related notes: [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms]], [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions]], [[24 - Testing and Quality/09 - Accessibility Testing|Accessibility Testing]]

### 41. When would you mock your own module in a test, and why is that usually wrong?

Strong answer:

Almost never — mocking my own code removes it from the tested surface and replaces it with my guess, so the suite verifies choreography between mocks. Legitimate seams are genuine boundaries: the clock and randomness (determinism), the network at request level with MSW (so my fetch/parse/error code still runs), external effects like payments, and environment-incompatible children (a WebGL map in jsdom).

Trap:

`vi.mock("./api")` hides URL construction, status handling, and parsing from every test — the classic green-suite-over-broken-app. Mock the network edge instead, so the real client pipeline executes.

Production angle:

Guard against mock drift: type mock factories against the real module (`satisfies typeof import(...)`), validate contracts with the same schemas the app uses, and let a thin E2E layer arbitrate truth.

Related notes: [[24 - Testing and Quality/10 - Mocking Seams and False Confidence|Mocking]], [[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|MSW]]

### 42. In Next 16, a Server Action mutates data but the user still sees the old value. Walk your decision tree.

Strong answer:

First: does any invalidation run at all? A bare DB write updates no cache layer. Then match the call to the contract: `updateTag(tag)` for immediate read-your-writes (the user must see their own change), `revalidateTag(tag, "max")` for stale-while-revalidate (others may briefly see stale), `revalidatePath` when the unit is a route. `refresh()` alone is the classic miss — it re-renders the client router but doesn't invalidate tagged data, so cached reads re-serve the stale value.

Trap:

A typo'd or missing tag fails silently: the write invalidates a tag no read carries. Verify the read's `cacheTag`/`tags` matches the write exactly — share tag constants.

Production angle:

Tags model data dependencies, decoupled from pages: one `updateTag('post:42')` refreshes the detail page, list, and sidebar. Add a time-based backstop so a missed tag costs bounded staleness.

Related notes: [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]], [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]

## Mock Interview Scoring Rubric

| Score | What It Sounds Like |
| --- | --- |
| 1 | Memorized phrase, no mechanism, no example. |
| 2 | Basic definition, but weak on edge cases and production impact. |
| 3 | Correct mechanism and small example, limited tradeoff depth. |
| 4 | Correct mechanism, code trace, frontend bug, and safe pattern. |
| 5 | Same as 4 plus source-level precision, caveats, and verification strategy. |

## Practice Loop

- [ ] Answer 5 questions without notes.
- [ ] Mark every vague phrase.
- [ ] Replace vague phrases with a mechanism name.
- [ ] Add one frontend bug and one safe pattern per answer.
- [ ] Re-answer the missed questions 24 hours later.

## Sources

- ECMAScript Language Specification: https://tc39.es/ecma262/
- HTML Living Standard event loops: https://html.spec.whatwg.org/multipage/webappapis.html#event-loops
- MDN JavaScript reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript
- MDN Promise reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise
- MDN AbortController reference: https://developer.mozilla.org/en-US/docs/Web/API/AbortController
- React `useEffect` reference: https://react.dev/reference/react/useEffect
- Next.js Server and Client Components docs: https://nextjs.org/docs/app/getting-started/server-and-client-components
- web.dev RAIL performance model: https://web.dev/articles/rail

## Related Notes

- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
- [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]]
- [[18 - Revision Plans/03 - 14 Day Deep Study Plan|14 Day Deep Study Plan]]
- [[18 - Revision Plans/05 - 20 Code Output Questions|20 Code Output Questions]]
- [[18 - Revision Plans/06 - 10 Practical Frontend Scenarios|10 Practical Frontend Scenarios]]
- [[01 - Roadmap|Roadmap]]
