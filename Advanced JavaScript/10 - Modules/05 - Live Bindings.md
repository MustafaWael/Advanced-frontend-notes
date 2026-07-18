---
tags: [javascript, modules, live-bindings]
module: "10 - Modules"
priority: must-know
status: not-started
---

# Live Bindings

## Maturity Target

- Priority: #must-know
- Study time: 80-110 minutes
- Interview signal: you can explain that ESM imports are live read-only views of exported bindings, not copied values.
- Production signal: you avoid mutable module state surprises and understand why cycles can work or fail.
- Dependencies: [[10 - Modules/01 - ES Modules|ES Modules]], [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]

## Source Anchors

- [MDN import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import)
- [MDN export](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/export)
- [MDN JavaScript modules: Cyclic imports](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules#cyclic_imports)
- [ECMAScript Module Namespace Exotic Objects](https://tc39.es/ecma262/#sec-module-namespace-exotic-objects)

## 1. Concept

ES module imports are live bindings. The importer reads the current value of the export binding from the exporting module.

```js
// counter.js
export let count = 0;

export function increment() {
  count += 1;
}

// main.js
import { count, increment } from "./counter.js";

console.log(count);
// 0

increment();

console.log(count);
// 1
```

The imported `count` is not a copied primitive snapshot.

## 2. Why It Matters

Live bindings explain:

- ESM circular dependency behavior
- why imported variables cannot be reassigned by importers
- why mutable module-level state is observable by all importers
- how module namespace objects stay current
- why ESM differs from CommonJS destructuring

This is a common interview discriminator because many developers know import syntax but not binding semantics.

## 3. Accurate Mechanism

During module linking, the importer is connected to the export binding. The import is read-only from the importer's perspective, but the exporting module can update its own binding if it was declared with `let` or `var`.

```js
// main.js
import { count } from "./counter.js";

count = 10;
// TypeError in module code
```

The importer cannot assign to the imported binding.

## 4. Mental Model

Import the binding, not the value.

```txt
exporter binding slot <---- importer reads this slot
```

If the exporter changes the slot, importers see the new value. If the exported value is an object, normal object reference rules also apply.

## 5. Live Binding vs Object Mutation

```js
// settings.js
export const settings = {
  theme: "light",
};

export function setTheme(theme) {
  settings.theme = theme;
}

// main.js
import { settings, setTheme } from "./settings.js";

console.log(settings.theme);
// "light"

setTheme("dark");

console.log(settings.theme);
// "dark"
```

`settings` is a const binding, but the object it points to is still mutable. Live binding and object mutability are separate concepts.

## 6. CommonJS Contrast

```js
// counter.cjs
let count = 0;

function increment() {
  count += 1;
}

module.exports = { count, increment };

// main.cjs
const { count, increment } = require("./counter.cjs");

increment();

console.log(count);
// 0
```

The destructured `count` is a local value. It does not update when the module's internal `count` changes.

## 7. Module Namespace Object

```js
import * as counter from "./counter.js";

console.log(counter.count);
// 0

counter.increment();

console.log(counter.count);
// 1
```

Namespace object properties reflect exports. Treat namespace objects as read-only views; do not try to add or overwrite properties.

## 8. Real Frontend Bug: Mutable Export As App State

### Problem

```js
// session.js
export let currentUser = null;

export function setCurrentUser(user) {
  currentUser = user;
}
```

Components import `currentUser` directly.

### Bug

> [!warning] Module-level mutable state is shared and leaks
> Every importer observes the same live binding. On the client this bypasses React rendering (the UI won't update); on the server, module-level mutable state can leak across requests when the process reuses the module. Keep request/user state in a store or request scope, not a module variable.

### Better Pattern

Use a framework-aware state store on the client:

```js
export function createSessionStore() {
  return {
    currentUser: null,
    setCurrentUser(user) {
      this.currentUser = user;
    },
  };
}
```

Or use explicit functions for non-React module-local caches:

```js
let cachedConfig;

export async function getConfig() {
  if (!cachedConfig) {
    cachedConfig = await loadConfig();
  }

  return cachedConfig;
}
```

## 9. Production Tradeoffs

- Live bindings make ESM cycles possible, but initialization order still matters.
- Mutable exported variables are useful for small demos and some library internals, but risky for app state.
- Imported bindings are read-only, but exported objects can still be mutated unless frozen.
- Module-level caches are fine for process-wide config, not per-user request data.
- Tests that mutate module state need reset/isolation.

## Real-World Use Cases

### Classic interview trap: the cycle that works for functions but throws for consts

```js
// order.js
import { applyDiscount } from "./discount.js";
export const TAX_RATE = 0.2;
export function totalOrder(items) {
  return applyDiscount(subtotal(items)) * (1 + TAX_RATE);
}

// discount.js
import { TAX_RATE } from "./order.js"; // cycle!
console.log(TAX_RATE); // ReferenceError: Cannot access 'TAX_RATE' before initialization
export function applyDiscount(value) {
  return value * 0.9;
}
```

Wrong guess: "circular imports crash" or "TAX_RATE is undefined". Trace: **link** connects both imports to export bindings before any code runs — the cycle links fine. **Evaluate** starts with `order.js`, which first evaluates its dependency `discount.js`. At that moment `TAX_RATE`'s binding exists but is uninitialized (TDZ), so reading it at top level throws. If `discount.js` only read `TAX_RATE` *inside* `applyDiscount`, everything works — by the time `totalOrder` calls it, the binding is initialized and the live binding delivers the current value. Live bindings are exactly why deferred reads across cycles succeed. See [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]] and [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]].

### Test pollution through a shared module binding

A rate-limit helper keeps a module-level counter. Test one exhausts it; test two fails mysteriously — both tests import the **same module instance**, so its bindings carry state across tests.

```ts
// rate-limit.ts
let requestCount = 0;
export function trackRequest() { requestCount += 1; return requestCount <= 100; }

// rate-limit.test.ts
beforeEach(() => {
  vi.resetModules(); // next import() builds a fresh module graph
});

it("blocks after 100 requests", async () => {
  const { trackRequest } = await import("./rate-limit");
  // fresh requestCount = 0, regardless of what earlier tests did
});
```

`resetModules` works because "one evaluation per graph instance" is per-registry — resetting the registry forces re-evaluation, giving each test its own binding slots.

### Why `vi.spyOn` on a namespace import throws in real ESM

A test spies on a sibling export to isolate a unit:

```ts
import * as api from "./api";
vi.spyOn(api, "fetchUser"); // TypeError in native ESM: cannot redefine property
```

The namespace object is a read-only **view of live bindings**, not a plain object — its properties cannot be reassigned (section 7). This "works" under some transpiled setups only because the bundler faked the namespace as a mutable object. The portable fix is `vi.mock("./api")` (which replaces the module in the registry) or injecting the dependency explicitly.

> [!warning]
> Code that relies on spying through namespace objects breaks when a repo migrates from CJS-transpiled Jest to native-ESM Vitest. It is a module-semantics bug, not a test-framework bug.

## 10. Interview Answer

**Short version:** ES module imports are live read-only views of exported bindings. Importers see changes made by the exporter, but cannot reassign the imported binding.

**Strong version:** During ESM linking, an import is connected to an export binding in the exporting module's environment. The importer does not get a snapshot of a primitive value. It reads the current binding value whenever it is accessed. This differs from CommonJS destructuring, where a primitive value can be copied out of `module.exports`. Live bindings help circular dependencies work, but reading an uninitialized binding too early can still fail. In production, I avoid using mutable exports as app state because they bypass framework lifecycles and can leak in server environments.

## 11. Common Mistakes

- Thinking named imports copy primitive values.
- Trying to assign to an imported binding.
- Confusing live binding updates with object property mutation.
- Exporting mutable app state from a module and expecting React to re-render automatically.
- Assuming CommonJS destructuring behaves like ESM imports.
- Forgetting tests can share mutated module state.

## 12. Practice

1. Write the counter live-binding example from memory.
2. Explain why `count = 10` fails in the importer.
3. Compare ESM `count` with CJS destructured `count`.
4. Show how an exported object can still be mutated.
5. Refactor a mutable exported user variable into a safer state pattern.

## Related Notes

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/02 - CommonJS|CommonJS]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[01 - Roadmap|Roadmap]]
