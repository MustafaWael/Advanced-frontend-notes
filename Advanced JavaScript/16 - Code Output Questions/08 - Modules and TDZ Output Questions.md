---
tags: [javascript, code-output, interview, modules, tdz, hoisting]
module: "16 - Code Output Questions"
priority: important
status: not-started
---

# Modules and TDZ Output Questions

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: can trace TDZ errors through declaration instantiation and module output through live bindings and evaluation order — never "let isn't hoisted."
- Production signal: can diagnose circular-import `undefined`s and "cannot access before initialization" in real bundles.
- Fast track: solve Q1-Q3, then explain aloud why Q1 throws instead of logging `undefined`.

## Source Anchors

- [MDN: let — temporal dead zone](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let#temporal_dead_zone_tdz)
- [MDN: JavaScript modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [ECMAScript specification — Module Semantics](https://tc39.es/ecma262/#sec-modules)

## Trace Method

For TDZ questions:

1. All declarations are registered at environment creation — `let`/`const`/`class` bindings exist but are **uninitialized** until their declaration executes. Accessing an uninitialized binding throws `ReferenceError`, not `undefined`.
2. Shadowing matters: an inner-scope `let x` puts *the inner binding* in TDZ even if an outer `x` is initialized.

For module questions:

3. Modules are instantiated (bindings linked) before any module evaluates; then evaluation runs depth-first from the entry point, each module **once**.
4. Imports are **live bindings** to the exporter's variable — not copies at import time.
5. In a cycle, the module that evaluates second sees the first's `function` declarations (initialized during instantiation) but its `let`/`const`/class bindings still in TDZ and its `var`s as `undefined`.

## Q1. TDZ Is Not "Not Hoisted"

```js
let x = 1;
{
  console.log(x);
  let x = 2;
}
```

### Expected Output

```text
ReferenceError: Cannot access 'x' before initialization
```

### Why

The block's environment registers its own `x` at creation, shadowing the outer one immediately — so `console.log(x)` resolves to the *inner* binding, which is in TDZ until `let x = 2` executes. The vague phrasing "let isn't hoisted" predicts `1` here and is wrong: the declaration **is** registered up front (that's why it shadows); it's the *initialization* that hasn't happened.

## Q2. typeof Is Not Safe in TDZ

```js
console.log(typeof undeclaredThing);
console.log(typeof declaredLater);
let declaredLater = 1;
```

### Expected Output

```text
undefined
ReferenceError: Cannot access 'declaredLater' before initialization
```

### Why

`typeof` on a name with *no binding at all* returns `"undefined"` (its historical safety valve). But `declaredLater` **has** a binding — uninitialized, in TDZ — and TDZ access throws even through `typeof`. TDZ made `typeof` unsafe for the first time in the language's history.

## Q3. Live Bindings

```js
// counter.js
export let count = 0;
export function increment() { count++; }

// main.js
import { count, increment } from "./counter.js";
console.log(count);
increment();
increment();
console.log(count);
count++; // ?
```

### Expected Output

```text
0
2
TypeError: Assignment to constant variable (binding is immutable from importer)
```

### Why

Imports are read-only *views* of the exporter's binding — not snapshots. After `increment()` mutates `count` inside counter.js, the importer's `count` reads 2: same binding, live. But writing through an import binding is a `TypeError` — only the exporting module may assign. CommonJS differs on the first half: `const { count } = require(...)` destructures a **copy** at require time and would log `0` twice.

## Q4. Circular Imports — Function vs const

```js
// a.js
import { bFn, bConst } from "./b.js";
export function aFn() { return "aFn"; }
export const aConst = "aConst";
console.log("a evaluating:", bFn(), bConst);

// b.js
import { aFn, aConst } from "./a.js";
export function bFn() { return "bFn"; }
export const bConst = "bConst";
console.log("b evaluating:", aFn());
console.log("b evaluating:", aConst);

// entry: import "./a.js";
```

### Expected Output

```text
b evaluating: aFn
ReferenceError: Cannot access 'aConst' before initialization
```

### Why

Entry pulls a.js; a.js's first line imports b.js, so **b evaluates first** (depth-first). Inside b, `aFn` works — function declarations are initialized during instantiation, before any evaluation. But `aConst` is a `const` still in TDZ because a.js's body hasn't run yet — ReferenceError, evaluation halts, a's log never prints. This asymmetry (functions survive cycles, consts don't) is why circular-import crashes feel random: they depend on *what kind of binding* crosses the cycle and in which direction evaluation happens to run.

## Q5. Modules Evaluate Once

```js
// side.js
console.log("side effect");
export const value = Math.random();

// main.js
import { value as v1 } from "./side.js";
import { value as v2 } from "./side.js";
console.log(v1 === v2);
```

### Expected Output

```text
side effect
true
```

### Why

The module registry caches by resolved specifier: side.js instantiates and evaluates once, no matter how many import statements or importers reference it. Both imports are views of the *same* binding, so `v1 === v2` even though the value came from `Math.random()`. This is the mechanism behind module-scope singletons — and behind the bug where module-scope state leaks across tests or across requests on a server ([[10 - Modules/00 - Modules MOC|Modules]]).

## Q6. Dynamic Import Timing

```js
// logger.js
console.log("logger evaluated");
export const log = (m) => console.log(m);

// main.js
console.log("start");
import("./logger.js").then(({ log }) => log("dynamic"));
console.log("end");
```

### Expected Output

```text
start
end
logger evaluated
dynamic
```

### Why

`import()` is asynchronous: it returns a promise and never evaluates the module synchronously, so "end" prints first. The module's evaluation and the `.then` callback both happen in later microtask/host ticks. Contrast a *static* `import` of logger.js, which would evaluate it before any of main.js runs — "logger evaluated" first. This ordering difference is exactly what code-splitting exploits ([[10 - Modules/00 - Modules MOC|dynamic imports]]).

## Related Notes

- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[10 - Modules/00 - Modules MOC|Modules MOC]]
- [[16 - Code Output Questions/00 - Code Output Questions MOC|Code Output Questions MOC]]
