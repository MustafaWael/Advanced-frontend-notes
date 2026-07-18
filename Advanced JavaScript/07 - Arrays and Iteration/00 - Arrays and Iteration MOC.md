---
tags: [javascript, moc, arrays, iteration]
module: "07 - Arrays and Iteration"
priority: must-know
status: not-started
---

# Arrays and Iteration MOC

This module teaches how JavaScript arrays really behave as objects — holes, `length` rules, shallow copies, mutating vs non-mutating methods, and the iteration protocols behind `for...of` and spread. It unlocks the production bugs interviewers love to probe: accidental mutation of React state and props, broken reference identity after `sort`, `fill` sharing one object across slots, async `forEach`, and "object is not iterable" errors. By the end you can pick the question-shaped method, keep transformations pure, and turn raw API data into UI-ready shapes without surprises.

## Prerequisites

- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]

## Reading Order

1. [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]] — how arrays really work as objects before trusting any method.
2. [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]] — the ownership and reference-identity rules behind most React array bugs.
3. [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]] — choosing the transformation method that matches the result shape.
4. [[07 - Arrays and Iteration/04 - find some every includes|find some every includes]] — question-shaped search methods, short-circuiting, and empty-array edge cases.
5. [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]] — comparators, default string sorting, and the ES2023 copy-returning methods.
6. [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]] — iterable vs iterator, `Symbol.iterator`, and why spread throws on plain objects.
7. [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]] — end-to-end API-to-UI pipelines with lookup maps, grouping, and memoization tradeoffs.
8. [[07 - Arrays and Iteration/08 - Arrays Checklist|Arrays Checklist]] — active-recall drills to prove the module before an interview.

## You're Done When

- [ ] I can explain arrays as objects with special index/`length` behavior, including holes vs explicit `undefined`.
- [ ] I can classify common methods as mutating, non-mutating, or modern copy-returning (`toSorted`, `toReversed`, `toSpliced`, `with`) and explain why mutation breaks React state and props.
- [ ] I can explain shallow copy behavior and copy every changed level when updating nested state.
- [ ] I choose the question-shaped method: `map`/`filter`/`reduce` for transformations, `find`/`some`/`every`/`includes` for answers, `forEach` only for side effects.
- [ ] I can predict the classic outputs: `[10, 2, 1].sort()`, `Array(3).fill({})`, `[].reduce(...)` without an initial value, `[].every(Boolean)`, and `[NaN].includes(NaN)`.
- [ ] I can explain iterable vs iterator, iterator exhaustion, and how to convert object maps and array-like collections into arrays.
- [ ] I build lookup maps for repeated ID access, store selected IDs instead of object references, and know when transformation work belongs in `useMemo`, the server, or virtualization.
