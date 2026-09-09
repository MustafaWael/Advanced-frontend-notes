---
tags: [javascript, scope, hoisting-and-tdz]
module: "03 - Scope and Variables"
priority: must-know
status: not-started
aliases: [TDZ, Temporal Dead Zone]
---

# Hoisting and TDZ

## Maturity Target

- Priority: #must-know
- Study time: 90 minutes
- Interview signal: you can replace the vague phrase "moved to the top" with declaration instantiation and initialization timing.
- Production signal: you can diagnose circular imports, function expression mistakes, class TDZ errors, and lexical shadowing bugs.
- Dependencies: [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]], [[03 - Scope and Variables/03 - var let const|var let const]]

## Source Anchors

- [MDN Glossary - Hoisting](https://developer.mozilla.org/en-US/docs/Glossary/Hoisting)
- [MDN - let TDZ](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let#temporal_dead_zone_tdz)
- [MDN - ReferenceError: cannot access lexical declaration before initialization](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Errors/Cant_access_lexical_declaration_before_init)
- [MDN - import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import)
- [ECMAScript 2026 - Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-environment-records)

## 1. Concept

Hoisting is the observable behavior caused by JavaScript preparing declarations before executing statements. It does not mean the engine literally moves your source lines.

TDZ, or temporal dead zone, is the period where a lexical binding exists in its scope but has not been initialized yet. Reads during that period throw `ReferenceError`.

This is the clean distinction:

- Function declarations are initialized early.
- `var` bindings are initialized early to `undefined`.
- `let`, `const`, and `class` bindings exist early but are uninitialized.
- Imports are linked before module evaluation and are live read-only bindings.

## 2. Why It Matters

Hoisting questions are common in interviews because they test whether you understand execution phases. In real applications, the same mechanics show up when:

- A helper function works before its declaration, but a function expression does not.
- A `let` shadow creates a TDZ error even though an outer variable exists.
- A circular import reads a binding before the exporting module has initialized it.
- A class is used before its declaration.
- Legacy `var` code silently produces `undefined` instead of failing fast.

## 3. Official Mechanism

Before evaluating code in a scope, JavaScript creates the relevant bindings during declaration instantiation.

| Declaration                             | Binding created before execution? | Initialized before execution?           | Early read                    |
| --------------------------------------- | --------------------------------- | --------------------------------------- | ----------------------------- |
| Function declaration                    | Yes                               | Yes, to function object                 | Works                         |
| `var`                                   | Yes                               | Yes, to `undefined`                     | `undefined`                   |
| `let`                                   | Yes                               | No                                      | `ReferenceError`              |
| `const`                                 | Yes                               | No                                      | `ReferenceError`              |
| `class`                                 | Yes                               | No                                      | `ReferenceError`              |
| Function expression assigned to `var`   | `var` yes                         | `undefined` until assignment            | Usually `TypeError` if called |
| Function expression assigned to `const` | `const` yes                       | Uninitialized until declaration         | `ReferenceError`              |
| Static import                           | Yes, during module linking        | Depends on module evaluation and cycles | Can fail in cycles            |

## 4. Mental Model

Do not imagine code being rearranged. Imagine a two-phase process:

1. Prepare bindings for the scope.
2. Execute statements in order.

```js
console.log(typeof declaredLater); // "undefined"
var declaredLater = 1;

try {
  console.log(typeof lexicalLater);
} catch (error) {
  console.log(error.name); // "ReferenceError"
}

let lexicalLater = 2;
```

`typeof` is safe for completely undeclared names, but it is not safe for lexical bindings inside their TDZ.

```js
console.log(typeof neverDeclared); // "undefined"

try {
  console.log(typeof value);
} catch (error) {
  console.log(error.name); // "ReferenceError"
}

const value = 1;
```

### The TDZ is a real value, not a rule the engine remembers

The spec describes an uninitialized binding. V8 implements that literally: it writes a special sentinel — *the hole* — into the binding's slot, and every read emits a check for it. You can see both the hoisting and the TDZ in the bytecode.

```js
const x = 1

function a() {
  return x + 1
}

console.log(x + a())
```

```txt
LdaTheHole
StaCurrentContextSlot [2]      ; x ← the hole      ← THIS is the TDZ
CreateClosure [0], [0], #2     ; build function a
StaGlobal [0], [0]             ; globalThis.a = closure   ← THIS is hoisting
LdaSmi [1]
StaCurrentContextSlot [2]      ; x ← 1             ← the `const x = 1` line
LdaGlobal [1], [2]             ; console
...
```

Read the first four instructions: `a` is created and stored **before** `x` receives its value. That is the whole of "function declarations are initialized early," with no metaphor. And `LdaTheHole` shows the TDZ is not a rule the engine consults — it is a sentinel physically sitting in the slot until the declaration executes.

Inside `a`, the read compiles to `LdaImmutableCurrentContextSlot [2]` — *immutable* because `x` is `const`, so the compiler proved no reassignment is possible and dropped the write barrier.

> [!warning] Top-level `let` and `const` are not on the global object
> The two bindings in that snippet are stored in completely different places, which is why they get different instructions:
>
> - `x` — a top-level `const` → a numbered slot in the **script context**, a heap object. `globalThis.x` is `undefined`.
> - `a` — a function declaration → an actual **property of `globalThis`**, hence `StaGlobal`.
>
> `var` behaves like `a` here, not like `x`. This is the mechanism behind the `var`/`let` difference people usually describe only as "`let` is block-scoped": at the top level of a script they don't merely differ in scope, they live in different objects. See [[03 - Scope and Variables/03 - var let const|var let const]].

> [!tip] Reproduce it
> `node --print-bytecode --print-bytecode-filter='*' file.js` on the snippet above. The full dispatch machinery behind these instructions is in [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]].

## 5. Function Declaration vs Function Expression

Function declarations are initialized before execution:

```js
console.log(formatPrice(12)); // "$12.00"

function formatPrice(value) {
  return `$${value.toFixed(2)}`;
}
```

Function expressions follow the rules of the variable they are assigned to:

```js
try {
  console.log(formatPrice(12));
} catch (error) {
  console.log(error.name); // "ReferenceError"
}

const formatPrice = function (value) {
  return `$${value.toFixed(2)}`;
};
```

With `var`, the name exists but holds `undefined` until assignment:

```js
try {
  console.log(parseTotal("12"));
} catch (error) {
  console.log(error.name); // "TypeError"; undefined is not callable.
}

var parseTotal = function (input) {
  return Number(input);
};
```

> [!tip] Tradeoff
> function declarations are good for pure helpers that can be read top-down or bottom-up. `const` function expressions are good when you want dependency order to be explicit or when assigning callbacks conditionally is not allowed.

## 6. Lexical Shadowing and TDZ

TDZ is easiest to misunderstand when an outer variable has the same name.

```js
const status = "outer";

function render() {
  try {
    console.log(status);
  } catch (error) {
    console.log(error.name); // "ReferenceError"
  }

  const status = "inner";
  return status;
}

console.log(render()); // "inner"
```

Why: the inner `const status` is the binding for the whole function/block scope. Before its declaration runs, it is uninitialized. JavaScript does not fall back to the outer `status`.

## 7. Class TDZ

Class declarations also have TDZ behavior.

```js
try {
  new ModalController();
} catch (error) {
  console.log(error.name); // "ReferenceError"
}

class ModalController {
  open() {
    return "opened";
  }
}
```

Production example: if a file exports a class and another module participates in a circular import, reading the class too early can produce a TDZ-style failure.

## 8. Real Frontend Scenario: Circular Imports

Problem:

```js
// apiClient.js
import { authHeaders } from "./auth.js";

export const client = {
  get(path) {
    return fetch(path, { headers: authHeaders });
  }
};
```

```js
// auth.js
import { client } from "./apiClient.js";

export const authHeaders = { Authorization: "Bearer token" };

export async function refreshSession() {
  return client.get("/session");
}
```

This might work depending on evaluation order, but circular dependencies become fragile when one module reads another module's lexical binding before it has been initialized.

Bug shape:

- The error often says a lexical declaration cannot be accessed before initialization.
- The stack points at module top-level code.
- Reordering lines may appear to fix it but leaves the architecture fragile.

Safer refactor:

```js
// authHeaders.js
export function getAuthHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}
```

```js
// apiClient.js
import { getAuthHeaders } from "./authHeaders.js";

export function createClient(token) {
  return {
    get(path) {
      return fetch(path, { headers: getAuthHeaders(token) });
    }
  };
}
```

```js
// auth.js
import { createClient } from "./apiClient.js";

export async function refreshSession(token) {
  const client = createClient(token);
  return client.get("/session");
}
```

> [!tip] Tradeoff
> factories add a little wiring, but they make dependencies explicit and avoid module top-level reads that are hard to reason about.

## 9. Default Parameter TDZ

Default parameters have their own scope-like evaluation order.

```js
function createRange(start = 0, end = start + 10) {
  return [start, end];
}

console.log(createRange(5)); // [5, 15]
```

Later parameters are not available to earlier parameter initializers:

```js
function broken(start = end, end = 10) {
  return [start, end];
}

try {
  broken();
} catch (error) {
  console.log(error.name); // "ReferenceError"
}
```

Production habit: keep default parameters simple. If defaults depend on several values, compute them inside the function body with clear order.

## 10. Bug -> Fix -> Checklist

Bug: a utility module calls a function expression before initialization.

```js
export const priceLabel = createLabel(20); // ReferenceError

const createLabel = (price) => `$${price.toFixed(2)}`;
```

Fix option 1: declare before use.

```js
const createLabel = (price) => `$${price.toFixed(2)}`;

export const priceLabel = createLabel(20);
```

Fix option 2: use a function declaration when early availability is intentional.

```js
export const priceLabel = createLabel(20);

function createLabel(price) {
  return `$${price.toFixed(2)}`;
}
```

Checklist:

- Is the name a declaration, a lexical binding, or a property?
- Is the access before the declaration line?
- Is there shadowing?
- Is a circular import involved?
- Does a function expression need to be converted to a declaration, or should code be reordered?
- Would moving top-level work into a function avoid module evaluation order problems?

## 11. Interview Answer

Short answer:

> Hoisting is JavaScript preparing declarations before executing code. `var` is initialized to `undefined`, function declarations are initialized to functions, and `let`/`const`/`class` are in TDZ until their declaration runs.

Deeper answer:

> The spec behavior comes from declaration instantiation and Environment Records. A binding can exist before it is initialized. That is why `var` can be read early as `undefined`, while `let` and `const` throw a `ReferenceError`. Hoisting is a useful descriptive term, but the engine is not literally moving source code.

Production answer:

> I care because TDZ failures often appear in real apps through circular imports, top-level module work, and shadowing. The fix is usually to break cycles, move work into a function, create a shared dependency module, or reorder initialization so the binding is initialized before it is read.

## 12. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Hoisting means JavaScript rewrites the file." | It prepares bindings before executing statements. |
| "`let` and `const` are not hoisted." | Their bindings exist early, but are uninitialized and inaccessible in TDZ. |
| "`typeof` always avoids ReferenceError." | `typeof` throws for lexical bindings in TDZ. |
| "Function expressions hoist like declarations." | They follow the declaration kind of the variable they are assigned to. |
| "Circular imports are solved by line reordering." | Often they need a dependency refactor or deferred reads. |

## 13. Practice

1. Predict the output:

```js
console.log(a);

try {
  console.log(b);
} catch (error) {
  console.log(error.name);
}

var a = 1;
let b = 2;
```

Expected output:

```txt
undefined
ReferenceError
```

2. Predict the output:

```js
sayHi();

try {
  sayBye();
} catch (error) {
  console.log(error.name);
}

function sayHi() {
  console.log("hi");
}

const sayBye = () => console.log("bye");
```

Expected output:

```txt
hi
ReferenceError
```

3. Create a two-file circular import that throws a TDZ error, then refactor it with a shared third module.
4. Explain why `typeof value` can throw when `value` is declared later with `let`.
5. Rewrite a function with confusing shadowing so every binding name has one clear meaning.

## Real-World Use Cases

### `jest.mock` factory hits TDZ on a `const` defined below it

Jest's transform hoists `jest.mock(...)` calls above the imports in the file. Reference a `const` mock helper inside the factory and the test dies with "Cannot access 'mockRouter' before initialization".

```ts
import { render } from "@testing-library/react";

const mockRouter = { push: jest.fn() }; // initialized during normal evaluation

jest.mock("next/navigation", () => ({
  useRouter: () => mockRouter // factory runs BEFORE the const initializes -> TDZ
}));
```

After hoisting, the factory executes while `mockRouter`'s binding still exists-but-uninitialized — exactly the TDZ read from section 3. Jest's escape hatch is naming-based: variables prefixed `mock` are allowed, but the allowance only silences the lint; the runtime TDZ still throws if the factory runs eagerly. The robust fixes: define the value inside the factory, or reference it lazily (`useRouter: () => mockRouter` is lazy enough only if nothing calls it during module evaluation).

> [!warning]
> This is the most common real-world TDZ error React developers hit — it looks like a Jest bug but it is pure declaration-instantiation timing.

### Helpers below the component: call-time reads are safe

A component file keeps the exported component at the top and `const` helpers below it — and it works, which surprises people who just learned about TDZ.

```tsx
export function PriceTag({ cents }: { cents: number }) {
  return <span>{formatPrice(cents)}</span>; // fine: read happens at render time
}

const formatPrice = (cents: number) =>
  currencyFormatter.format(cents / 100);

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD"
});
```

TDZ is about **when the read executes**, not where it sits in the file. Module evaluation initializes all three bindings top-to-bottom before React ever calls `PriceTag`, so the render-time lookup finds initialized bindings. Move the call to module top level (`const preview = formatPrice(0)` above the helpers) and it throws — the same mechanism as the Bug in section 10.

> [!tip]
> This is why "component first, helpers below" is a safe file layout convention: function bodies defer their reads past module evaluation.

### `typeof` guard breaks when a lexical binding shadows the global

Defensive code checks for an optional analytics global before using it. Then someone adds a late `let gtag` in the same scope and the "safe" guard starts throwing.

```js
if (typeof gtag === "function") {
  gtag("event", "purchase"); // guard is safe for truly undeclared globals
}

// ...200 lines later, someone adds:
let gtag = loadGtagStub(); // now the typeof above is a TDZ read -> ReferenceError
```

`typeof` only protects against *unresolvable* names; a `let`/`const` binding anywhere in the scope exists from the top of that scope in an uninitialized state, so the early `typeof` becomes a TDZ read (section 4). Prefer explicit global access — `typeof globalThis.gtag === "function"` — which is a property lookup and immune to shadowing ([[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]] covers identifier vs property lookup).

## Related Notes

- [[03 - Scope and Variables/01 - Scope Types|Scope Types]]
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/03 - var let const|var let const]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]]
- [[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]] — where `LdaTheHole` and script contexts come from.
- [[01 - Roadmap|Roadmap]]
