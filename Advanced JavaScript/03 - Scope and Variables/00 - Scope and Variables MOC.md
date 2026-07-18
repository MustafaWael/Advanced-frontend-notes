---
tags: [javascript, moc, scope, closures]
module: "03 - Scope and Variables"
priority: must-know
status: not-started
---

# Scope and Variables MOC

This module teaches how identifiers are resolved: scope types, lexical environments, `var`/`let`/`const`, hoisting with the temporal dead zone, and closures as functions that keep access to their creation environment. It is the single highest-leverage module for interviews — loop output questions, TDZ traps, and stale-closure bugs in React all live here. After it, you can trace any "what does this log?" question and debug callbacks by asking when they were created versus when they run.

## Prerequisites

- [[02 - JavaScript Runtime Foundations/00 - JavaScript Runtime Foundations MOC|Runtime Foundations MOC]] — execution contexts and environments are defined there.
- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]] — the record whose environments this module explores in depth.

## Reading Order

1. [[03 - Scope and Variables/01 - Scope Types|Scope Types]] — global, module, function, block, catch, and class scope as identifier resolution.
2. [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]] — Environment Records and outer links, the mechanism behind every lookup.
3. [[03 - Scope and Variables/03 - var let const|var let const]] — scoping, initialization, and rebinding differences that decide loop and TDZ behavior.
4. [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]] — declaration preparation vs execution, and why early reads throw or return `undefined`.
5. [[03 - Scope and Variables/05 - Closures|Closures]] — functions plus their creation environment; bindings, not snapshots.
6. [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]] — the classic loop bug, stale React closures, and cleanup identity traps.
7. [[03 - Scope and Variables/07 - Scope Checklist|Scope Checklist]] — active self-test with snippets to trace and drills.

## You're Done When

- [ ] I can define scope as identifier resolution and explain global, module, function, block, catch, and class scope.
- [ ] I can trace identifier lookup through Environment Records and outer links, and distinguish a binding from the value it holds.
- [ ] I can explain `var` vs `let`/`const` scoping, why `var` early reads give `undefined` while `let`/`const` throw, and why `const` does not freeze objects.
- [ ] I can explain hoisting as preparation (not code movement), diagnose TDZ shadowing errors, and explain circular import TDZ failures.
- [ ] I can define a closure as function plus creation environment and explain why closures capture bindings, not snapshots.
- [ ] I can solve the classic `var` loop output question and fix it with `let` or a factory function.
- [ ] I can explain stale closures in React and choose between dependency arrays, functional updaters, refs, and argument passing.
- [ ] I can solve the checklist's five trace snippets without running them.
