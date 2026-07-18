---
tags: [javascript, moc, modules]
module: "10 - Modules"
priority: important
status: not-started
---

# Modules MOC

This module teaches how JavaScript files actually connect: ESM parse/link/evaluate, CommonJS `require` and its cache, live bindings vs copied values, and how bundlers turn module structure into tree shaking and code splitting. It unlocks a family of real production bugs — circular dependency `undefined` imports and TDZ errors, `window is not defined` from top-level side effects during SSR, barrel files that bloat routes — plus the classic ESM vs CommonJS interview questions. Finish it and you can reason about bundle size and lazy-loading decisions instead of guessing.

## Prerequisites

- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[08 - Async JavaScript/02 - Promises|Promises]]

## Reading Order

1. [[10 - Modules/01 - ES Modules|ES Modules]] — the module system the rest of the folder assumes.
2. [[10 - Modules/02 - CommonJS|CommonJS]] — the older Node system you still hit in packages, configs, and interop bugs.
3. [[10 - Modules/03 - Named vs Default Exports|Named vs Default Exports]] — export style as API design, refactor safety, and `React.lazy` compatibility.
4. [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]] — eager vs lazy loading, split points, and chunk-failure handling.
5. [[10 - Modules/05 - Live Bindings|Live Bindings]] — why imports are live read-only views, not copies; the key ESM/CJS discriminator.
6. [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]] — why cycles sometimes work, sometimes throw TDZ errors, and how to break them.
7. [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]] — turning module structure into smaller, faster production bundles.
8. [[10 - Modules/08 - Modules Checklist|Modules Checklist]] — active self-test with drills, scenarios, and interview prompts.
9. [[10 - Modules/09 - From Source to Browser|From Source to Browser]] — transpilers vs polyfills, browserslist, source maps, bundlers (extension topic).

## You're Done When

- [ ] I can explain ESM parse/link/evaluate, module scope, and strict mode in practical terms.
- [ ] I can explain CommonJS `require`, `module.exports` vs `exports`, and the module cache, and predict the `exports = ...` pitfall.
- [ ] I can compare ESM live bindings with CommonJS destructured value snapshots and predict the counter drill output.
- [ ] I can explain dynamic `import()` as a Promise for a module namespace object, including `.default`, and connect it to `React.lazy`.
- [ ] I can identify and fix a barrel-file circular dependency, and explain why a cycle works in one ESM example and fails in another.
- [ ] I can distinguish tree shaking, side-effect analysis, code splitting, and lazy loading without mixing them together.
- [ ] I keep modules side-effect-light, isolate browser-only code from SSR paths, and give lazy-loaded UI loading and error states.
- [ ] I inspect production bundle output before claiming an optimization worked.

## Related Modules

- [[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|Modules, tsconfig and Package Types]] — the TypeScript layer over these module semantics.
