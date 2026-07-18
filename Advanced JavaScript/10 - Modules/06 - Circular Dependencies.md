---
tags: [javascript, modules, circular-dependencies]
module: "10 - Modules"
priority: important
status: not-started
---

# Circular Dependencies

## Maturity Target

- Priority: #important
- Study time: 90-120 minutes
- Interview signal: you can explain direct vs indirect cycles, ESM live-binding cycles, TDZ failures, and CJS partial exports.
- Production signal: you can identify and break cycles in component folders, stores, services, and barrel files.
- Dependencies: [[10 - Modules/05 - Live Bindings|Live Bindings]], [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

## Source Anchors

- [MDN JavaScript modules: Cyclic imports](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules#cyclic_imports)
- [ECMAScript Modules](https://tc39.es/ecma262/#sec-modules)
- [Node.js CommonJS cycles](https://nodejs.org/api/modules.html#cycles)
- [webpack: Circular dependencies and side effects context](https://webpack.js.org/guides/tree-shaking/)

## 1. Concept

A circular dependency happens when modules depend on each other directly or indirectly.

Direct cycle:

```txt
a.js imports b.js
b.js imports a.js
```

Indirect cycle:

```txt
a.js imports b.js
b.js imports c.js
c.js imports a.js
```

Cycles are allowed in JavaScript module systems, but they are fragile when modules read each other's values during initialization.

## 2. Why It Matters

Circular dependencies show up in frontend apps through:

- barrel files
- component folders importing from their own `index.ts`
- stores importing API clients that import stores
- services importing each other
- route modules importing shared modules that import routes
- test setup files importing app entry points

They often work for months and then break after a refactor because evaluation order changed.

## 3. Accurate Mechanism

ESM links the full module graph before evaluating modules. Live bindings allow cycles because imports can point to exports before values are assigned.

But if a module reads an imported `let`/`const` binding before the exporter has initialized it, the read can hit the temporal dead zone and throw.

CommonJS works differently. It executes modules as `require` happens and returns a cached `module.exports` object. In a cycle, a module may receive another module's partial exports.

## 4. Mental Model

Cycles are less dangerous when:

- modules only declare functions/classes
- reads happen after all modules finish evaluating
- shared types are type-only imports
- shared runtime values live in a third module

Cycles are dangerous when:

- top-level code reads imported values immediately
- modules mutate each other's setup
- barrels re-export and import back through themselves
- application state is initialized across a cycle

## 5. ESM Cycle That Works

```js
// a.js
import { getB } from "./b.js";

export const nameA = "A";

export function getAAndB() {
  return `${nameA}:${getB()}`;
}

// b.js
import { nameA } from "./a.js";

export function getB() {
  return `B sees ${nameA}`;
}
```

This works because `b.js` does not read `nameA` until `getB` is called later.

## 6. ESM Cycle That Fails

```js
// a.js
import { valueB } from "./b.js";

export const valueA = "A";
export const combined = `${valueA}:${valueB}`;

// b.js
import { valueA } from "./a.js";

export const valueB = `B sees ${valueA}`;
```

Depending on evaluation order, `b.js` can read `valueA` before `a.js` has initialized it. That can throw a TDZ error.

Safer:

```js
// b.js
import { valueA } from "./a.js";

export function getValueB() {
  return `B sees ${valueA}`;
}
```

Deferring the read into a function lets the graph finish evaluating first.

## 7. CommonJS Partial Export Cycle

```js
// a.cjs
const b = require("./b.cjs");
exports.name = "A";
exports.fromB = b.name;

// b.cjs
const a = require("./a.cjs");
exports.name = "B";
exports.fromA = a.name;
```

When `b.cjs` requires `a.cjs`, `a.cjs` is not done yet. `a.name` may be `undefined`.

CommonJS cycles usually produce partial values rather than ESM TDZ errors.

## 8. Real Frontend Bug: Barrel Cycle

### Problem

```ts
// components/index.ts
export { Button } from "./Button";
export { UserCard } from "./UserCard";

// components/UserCard.tsx
import { Button } from "./index";

export function UserCard() {
  return <Button>View</Button>;
}
```

### Bug

> [!warning] Barrel files create hidden cycles
> `index.ts` re-exports `UserCard`, and `UserCard` imports from `index.ts` — the folder imports through a barrel that imports back through itself. The cycle can yield `undefined` imports or TDZ errors at load time. Import the concrete module directly instead of through the barrel.

### Fix

```ts
// components/UserCard.tsx
import { Button } from "./Button";

export function UserCard() {
  return <Button>View</Button>;
}
```

> [!tip] Rule
> files inside a package/folder should usually import siblings directly, not through the public barrel for the same folder.

## 9. How To Break Cycles

Use one of these moves:

- extract shared constants/helpers to a third module
- move top-level reads inside functions
- invert dependency direction with callbacks or dependency injection
- split types from runtime values with `import type`
- avoid importing from a barrel inside the barrel's own folder
- move framework wiring to a composition/root module
- remove module-level initialization that crosses boundaries

## 10. Debugging Notes

Symptoms:

- `Cannot access before initialization`
- `undefined` from an imported value
- component is `undefined`
- route works in dev but fails after production build
- tests pass alone but fail as a suite
- hot reload behaves differently after full refresh

Tools:

- run a circular dependency detector
- inspect bundler warnings
- search barrel imports from inside the same folder
- log module evaluation order temporarily
- draw the import graph for the smallest failing cycle

## 11. Production Tradeoffs

- Some cycles are harmless when values are read lazily.
- Cycles across architecture layers are usually design smells.
- Barrels are convenient public APIs but risky for internal sibling imports.
- Type-only imports can remove runtime edges, but only if the import is truly type-only.
- Deferring reads can fix initialization but may hide a deeper dependency-direction problem.

## 12. Interview Answer

**Short version:** A circular dependency is when modules import each other directly or indirectly. ESM can link cycles through live bindings, but reading an imported binding before initialization can fail.

**Strong version:** ES modules build and link the module graph before evaluation, so cycles can exist. Imports are live bindings, which helps modules refer to each other. The danger is top-level initialization: if module B reads module A's `const` before A has evaluated that declaration, you can get a TDZ error. CommonJS handles cycles differently by returning partial cached `module.exports`, so consumers may see `undefined`. In production, I break cycles by extracting shared code, deferring reads into functions, using type-only imports, avoiding internal barrel imports, or inverting dependency direction.

## 13. Common Mistakes

- Thinking all circular dependencies are immediate errors.
- Thinking all circular dependencies are safe because ESM has live bindings.
- Reading imported values at top level during a cycle.
- Importing through a barrel from inside the same folder.
- Fixing a cycle with dynamic import when a shared module would be clearer.
- Ignoring type-only imports that could remove a runtime edge.
- Treating CJS partial exports and ESM TDZ behavior as the same.

## 14. Practice

1. Draw a direct cycle and an indirect cycle.
2. Explain why the lazy function ESM cycle works.
3. Explain why the top-level read ESM cycle can fail.
4. Fix the barrel cycle example.
5. Refactor a store/API-client cycle using dependency injection or a third module.

## Related Notes

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/02 - CommonJS|CommonJS]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
- [[01 - Roadmap|Roadmap]]
