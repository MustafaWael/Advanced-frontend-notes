---
tags: [javascript, moc, functions]
module: "04 - Functions Deep Dive"
priority: must-know
status: not-started
---

# Functions Deep Dive MOC

This module treats functions as values: declarations vs expressions, arrow functions, higher-order functions and callbacks, purity, parameter handling, currying, and the debounce/throttle patterns built from all of them. It turns closure theory into production skill — writing wrappers that preserve arguments and errors, choosing callback timing consciously, and rate-limiting UI work. It unlocks interview staples like "arrow vs regular function", broken wrapper output questions, and `forEach(async ...)` bugs.

## Prerequisites

- [[03 - Scope and Variables/00 - Scope and Variables MOC|Scope and Variables MOC]] — closures and TDZ explain most function behavior here.
- [[03 - Scope and Variables/05 - Closures|Closures]] — the mechanism behind currying, debounce, and callback context.

## Reading Order

1. [[04 - Functions Deep Dive/01 - Function Declarations vs Expressions|Function Declarations vs Expressions]] — which form exists before its source line, and why.
2. [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]] — lexical `this`, no `arguments`, no `new`, and where arrows do not belong.
3. [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]] — functions as values and why the API, not syntax, decides callback timing.
4. [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions and IIFE]] — side effects, render purity in React, and private-scope setup patterns.
5. [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]] — rest vs spread, default evaluation, and options-object API design.
6. [[04 - Functions Deep Dive/06 - Currying and Partial Application|Currying and Partial Application]] — pre-filling arguments with closures and when it hurts readability.
7. [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]] — waiting for quiet vs steady rate limiting, with cancellation and cleanup.
8. [[04 - Functions Deep Dive/08 - Functions Checklist|Functions Checklist]] — active self-test with trace snippets and review questions.

## You're Done When

- [ ] I can explain declarations vs expressions, predict which forms are callable before their source line, and explain the TDZ for `const`-assigned expressions.
- [ ] I can explain arrow functions' lexical `this`, missing `arguments`, and non-constructability, and avoid arrows for methods that need a receiver.
- [ ] I can distinguish synchronous from asynchronous callbacks by the API contract and avoid `forEach(async ...)` when completion matters.
- [ ] I can define a pure function, identify side effects, and explain why React render code must stay pure.
- [ ] I can write a wrapper that preserves arguments, `this`, return value, and thrown errors.
- [ ] I can explain rest vs spread, default parameter evaluation with `undefined` vs `null`, and design options-object APIs.
- [ ] I can distinguish currying from partial application and explain closures as the mechanism.
- [ ] I can implement debounce and throttle with preserved arguments, cancellation, and cleanup on unmount.
