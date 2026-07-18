---
tags: [javascript, interview, interview-checklist]
module: "15 - Interview Preparation"
priority: must-know
status: not-started
---

# Interview Checklist

## Maturity Target

- Priority: #must-know
- Study time: use before every mock or real interview
- Interview signal: can self-audit readiness by topic, not by vague confidence.
- Production signal: can connect fundamentals to real frontend debugging and decisions.
- Fast track: complete the "Day Before" and "Code Output" sections.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN JavaScript Reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference)
- [HTML Living Standard: event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [React docs](https://react.dev/learn)
- [Next.js docs](https://nextjs.org/docs)

## Readiness Rule

Do not check an item because you recognize the term. Check it only if you can:

1. define it plainly
2. explain the mechanism
3. trace a code example
4. name a frontend bug
5. state a safe pattern or tradeoff

## Runtime Foundations

- [ ] I can explain execution context creation vs execution.
- [ ] I can explain Lexical Environment, Environment Record, and outer reference.
- [ ] I can explain hoisting as binding creation, not physical movement.
- [ ] I can explain TDZ for `let`, `const`, and `class`.
- [ ] I can compare `var`, `let`, and `const`.
- [ ] I can explain scope types: global, module, function, block.
- [ ] I can trace `typeof` behavior for undeclared vs TDZ variables.
- [ ] I can explain falsy vs nullish values.
- [ ] I can explain `??` vs `||` with `0` and empty string examples.

Related:

- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

## Functions And `this`

- [ ] I can compare function declarations and expressions.
- [ ] I can explain arrow function differences: lexical `this`, no `arguments`, no constructor behavior.
- [ ] I can explain higher-order functions and callbacks.
- [ ] I can write debounce and throttle from memory.
- [ ] I can explain the four `this` binding rules and their precedence.
- [ ] I can explain default binding in strict vs sloppy mode.
- [ ] I can explain why extracted methods lose `this`.
- [ ] I can use `call`, `apply`, and `bind` correctly.
- [ ] I can explain why `.bind` creates a new function reference.

Related:

- [[04 - Functions Deep Dive/08 - Functions Checklist|Functions Checklist]]
- [[05 - this Binding/08 - this Checklist|this Checklist]]
- [[16 - Code Output Questions/03 - this Output Questions|this Output Questions]]

## Closures And Memory

- [ ] I can explain closures with lexical environment capture.
- [ ] I can explain how closures keep captured environments reachable.
- [ ] I can trace the `var` loop closure bug.
- [ ] I can explain why `let` creates a new binding per loop iteration.
- [ ] I can identify closure-based memory retention.
- [ ] I can explain stale closures in React.
- [ ] I can choose between dependencies, functional updates, and refs.
- [ ] I can clean up timers, listeners, observers, and async work.

Related:

- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

## Objects, Prototypes, And Classes

- [ ] I can explain property lookup through the internal \[\[Prototype\]\] link.
- [ ] I can explain own property vs inherited property.
- [ ] I can compare `__proto__` and `Constructor.prototype`.
- [ ] I can explain the four steps of `new`.
- [ ] I can explain constructor return override.
- [ ] I can explain class syntax as prototype-based behavior.
- [ ] I can explain property descriptors.
- [ ] I can compare shallow copy and deep copy.
- [ ] I can explain `Object.freeze` vs `const`.

Related:

- [[06 - Objects and Prototypes/08 - Objects Checklist|Objects Checklist]]
- [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]]

## Equality, Coercion, And Values

- [ ] I can compare primitive and reference values.
- [ ] I can compare `==`, `===`, and `Object.is`.
- [ ] I can trace `[] == ![]`.
- [ ] I can explain `ToPrimitive` at a practical level.
- [ ] I can explain `NaN`, `0`, and `-0` equality edge cases.
- [ ] I can explain truthy/falsy bugs in conditionals.
- [ ] I can explain optional chaining and nullish coalescing.
- [ ] I can explain Date, RegExp, JSON, BigInt basics.

Related:

- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]
- [[12 - Advanced Language Concepts/11 - Advanced Concepts Checklist|Advanced Concepts Checklist]]

## Arrays And Iteration

- [ ] I can identify mutating and non-mutating array methods.
- [ ] I can update arrays immutably in React.
- [ ] I can explain `map`, `filter`, `reduce`, and `forEach` tradeoffs.
- [ ] I can explain `find`, `some`, `every`, and `includes`.
- [ ] I can explain `sort` mutation and modern immutable alternatives.
- [ ] I can explain the iterator protocol.
- [ ] I can write a custom iterable or generator.
- [ ] I can choose efficient data transformations for large lists.

Related:

- [[07 - Arrays and Iteration/08 - Arrays Checklist|Arrays Checklist]]
- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]

## Async And Event Loop

- [ ] I can explain task vs microtask ordering.
- [ ] I can explain Promise state and settlement.
- [ ] I can compare Promise concurrency methods.
- [ ] I can explain async/await as Promise continuation behavior.
- [ ] I can explain why sequential awaits can create waterfalls.
- [ ] I can handle async errors with `try/catch`, returns, and awaited Promises.
- [ ] I can use `AbortController` correctly.
- [ ] I can trace timers, Promises, nested microtasks, and async functions.
- [ ] I can explain browser rendering and long tasks.

Related:

- [[08 - Async JavaScript/08 - Async Checklist|Async Checklist]]
- [[09 - Event Loop Advanced/08 - Event Loop Checklist|Event Loop Checklist]]
- [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]]

## Modules And Build Behavior

- [ ] I can explain ESM static structure.
- [ ] I can explain CommonJS runtime `require`.
- [ ] I can explain named vs default exports.
- [ ] I can explain live bindings.
- [ ] I can explain circular dependency risks.
- [ ] I can explain dynamic import and code splitting.
- [ ] I can explain tree shaking requirements.
- [ ] I can identify imports that can bloat a bundle.

Related:

- [[10 - Modules/08 - Modules Checklist|Modules Checklist]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]

## Error Handling

- [ ] I can use `try`, `catch`, `throw`, and `finally`.
- [ ] I can write a custom error class.
- [ ] I can handle Promise rejections.
- [ ] I can explain async error boundaries in React.
- [ ] I can distinguish expected aborts from real failures.
- [ ] I can design API error handling with status, code, and user-safe messages.
- [ ] I can decide what to show users and what to log/report.

Related:

- [[11 - Error Handling/07 - Error Handling Checklist|Error Handling Checklist]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]

## React And Next.js JavaScript

- [ ] I can explain render snapshots.
- [ ] I can explain closures in hooks.
- [ ] I can explain dependency arrays and `Object.is`.
- [ ] I can fix stale closures.
- [ ] I can explain referential equality and memoization.
- [ ] I can update state immutably.
- [ ] I can fix async effect race conditions.
- [ ] I can use `AbortController` in effects.
- [ ] I can explain Server vs Client Components.
- [ ] I can explain `'use client'` module graph impact.
- [ ] I can explain hydration mismatch and fixes.

Related:

- [[14 - JavaScript in React and Next.js/11 - React and Next Checklist|React and Next Checklist]]

## Performance And Memory

- [ ] I can explain reachability and garbage collection.
- [ ] I can identify memory leak patterns.
- [ ] I can clean up listeners and timers.
- [ ] I can use memoization only when identity or expensive computation matters.
- [ ] I can debug React rerenders with Profiler.
- [ ] I can debug memory with heap snapshots and retainers.
- [ ] I can explain long tasks and UI responsiveness.
- [ ] I can explain bundle size and code splitting.
- [ ] I can state a measurement plan before optimizing.

Related:

- [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]]
- [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]

## Code I Can Write From Memory

- [ ] `debounce(fn, delay)`
- [ ] `throttle(fn, interval)`
- [ ] `memoize(fn)` with bounded cache discussion
- [ ] `curry(fn)` for fixed arity
- [ ] custom iterable with `[Symbol.iterator]`
- [ ] generator `range(start, end)`
- [ ] immutable array add, remove, update, sort
- [ ] custom `ApiError`
- [ ] `sleep(ms)`
- [ ] `Promise.race` timeout
- [ ] effect ignore-flag pattern
- [ ] effect `AbortController` pattern
- [ ] hydration-safe browser-only read
- [ ] stale interval fix with functional updater

## Bugs I Can Debug

- [ ] `var` loop logs `3, 3, 3`
- [ ] extracted method loses `this`
- [ ] Promise rejection escapes `try/catch`
- [ ] effect reads old state
- [ ] effect refetches every render
- [ ] mutated React state does not rerender
- [ ] memoized child rerenders from inline props
- [ ] old search response overwrites new response
- [ ] fetch abort shows user-facing error
- [ ] hydration mismatch from localStorage
- [ ] memory leak from missing listener cleanup
- [ ] long list freezes input
- [ ] bundle grows from a client boundary or dependency import

## Day Before Interview

- [ ] Review [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]].
- [ ] Run one mock using [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]].
- [ ] Trace three questions from Module 16.
- [ ] Practice closures, event loop, `this`, stale closures, and Server/Client Components aloud.
- [ ] Prepare two real project stories: one debugging story and one performance/tradeoff story.
- [ ] Identify three strongest topics and two weaker topics.
- [ ] Sleep instead of cramming after the final review pass.

## During Interview

- [ ] Answer the direct question first.
- [ ] Ask clarification when scope is ambiguous.
- [ ] Think aloud for code output.
- [ ] State assumptions before solving.
- [ ] Say "I am not certain" when accuracy matters.
- [ ] Correct yourself cleanly if you notice an error.
- [ ] Use production examples without turning every answer into a story.
- [ ] Stop when the answer is complete.

## Final Readiness Test

Answer these without notes:

1. What exactly is hoisted for `var`, `let`, `const`, function declarations, and classes?
2. Why does a closure keep outer variables alive?
3. Why does `setTimeout(..., 0)` run after Promise callbacks?
4. Why does `Object.is({}, {})` return `false`?
5. Why can mutating React state skip a rerender?
6. How do you prevent stale async fetch results?
7. What does `'use client'` change in Next.js?
8. What causes hydration mismatch?
9. How would you debug a memory leak?
10. How would you investigate a bundle size regression?

## Related Notes

- [[15 - Interview Preparation/01 - Junior to Mid Questions|Junior to Mid Questions]]
- [[15 - Interview Preparation/02 - Mid Level Questions|Mid Level Questions]]
- [[15 - Interview Preparation/03 - Strong Mid Level Questions|Strong Mid Level Questions]]
- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
- [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]]
- [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]]
- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
