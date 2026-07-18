---
tags: [javascript, moc, code-output, interview]
module: "16 - Code Output Questions"
priority: must-know
status: not-started
---

# Code Output Questions MOC

This module is pure retrieval practice: small snippets whose output proves whether you actually understand creation phase, closures, receivers, prototype lookup, and task/microtask ordering. Always predict before running — write the output and the mechanism for each line, commit to your answer, and only then check. If you were wrong, record the exact rule you missed instead of memorizing the final output.

## Prerequisites

- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[05 - this Binding/01 - What is this|What is this]]
- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## Reading Order

1. [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]] — creation phase, TDZ, and shadowing traps first.
2. [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]] — bindings vs values, loop closures, and module patterns.
3. [[16 - Code Output Questions/03 - this Output Questions|this Output Questions]] — call-site rules, extraction, arrows, and `bind`.
4. [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]] — lookup, shadowing, `instanceof`, and class inheritance.
5. [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]] — task vs microtask ordering under timers and `await`.
6. [[16 - Code Output Questions/07 - Generator and Iterator Output Questions|Generator and Iterator Output Questions]] — suspended execution, the `next(value)` handshake, exhausted iterators, and `finally` on early termination.
7. [[16 - Code Output Questions/08 - Modules and TDZ Output Questions|Modules and TDZ Output Questions]] — TDZ through shadowing and `typeof`, live bindings, circular-import asymmetry, and dynamic import timing.
8. [[16 - Code Output Questions/09 - TypeScript Inference Output Questions|TypeScript Inference Output Questions]] — the compiler's verdict as the output: widening, `satisfies`, narrowing in closures, exhaustiveness.
9. [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]] — coercion, generators, symbols, and combined traps as the final drill.

## You're Done When

- [ ] You predicted the output of every question in writing before running or reading the answer.
- [ ] You solved all questions in files 01-05 with the correct mechanism named for each line, not just the right output.
- [ ] You can apply the trace method from memory: sync lines first, then microtasks, then tasks, tracking bindings and closures.
- [ ] You re-solved every question you missed at least 24 hours later and got it right.
- [ ] You can explain each miss as a specific rule (TDZ, receiver, prototype lookup, microtask drain), not "I forgot".
- [ ] You solved the Mixed Advanced drill cold with at most two errors.
