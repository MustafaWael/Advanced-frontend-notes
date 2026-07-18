---
tags: [javascript, functions, function-declarations-vs-expressions]
module: "04 - Functions Deep Dive"
priority: must-know
status: not-started
---

# Function Declarations vs Expressions

## Maturity Target

- Priority: #must-know
- Study time: 75-90 minutes
- Interview signal: you can explain availability, hoisting, names, stack traces, and call timing.
- Production signal: you choose declarations or expressions based on dependency order, readability, testability, and callback ownership.
- Dependencies: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]], [[03 - Scope and Variables/05 - Closures|Closures]]

## Source Anchors

- [MDN - function declaration](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function)
- [MDN - function expression](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/function)
- [MDN - Functions guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions)
- [ECMAScript 2026 - Function definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-function-definitions)
- [ECMAScript 2026 - Function Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-function-environment-records)

## 1. Concept

A function declaration is a statement that creates a named function binding in a scope.

```js
function formatPrice(value) {
  return `$${value.toFixed(2)}`;
}
```

A function expression creates a function value as part of an expression, usually assigned to a variable or passed as an argument.

```js
const formatPrice = function (value) {
  return `$${value.toFixed(2)}`;
};
```

The important difference is not "old syntax vs modern syntax." It is when the binding is created, when the function object is available, and how the function value is used.

## 2. Why It Matters

Frontend code is full of functions:

- React components.
- Event handlers.
- Promise continuations.
- Validators and selectors.
- Route handlers.
- Debounced or throttled wrappers.
- Array callbacks.
- Hook return values.

Function syntax affects stack traces, hoisting, dependency order, `this`, callback identity, and how easy the code is to test.

## 3. Official Mechanism

Function declarations are initialized during declaration instantiation. That means they can be called before their source line in the same scope.

Function expressions follow normal runtime evaluation. If the expression is assigned to `const` or `let`, the binding is in TDZ before initialization. If assigned to `var`, the binding is `undefined` before assignment.

```js
console.log(declared(2)); // 4

function declared(value) {
  return value * 2;
}

try {
  console.log(expressed(2));
} catch (error) {
  console.log(error.name); // "ReferenceError"
}

const expressed = function (value) {
  return value * 2;
};
```

With `var`:

```js
try {
  console.log(legacy(2));
} catch (error) {
  console.log(error.name); // "TypeError"; legacy is undefined.
}

var legacy = function (value) {
  return value * 2;
};
```

## 4. Mental Model

Use declarations for stable named capabilities that belong to the module or scope.

Use expressions when the function is a value:

- Passed to another function.
- Returned from a function.
- Created conditionally.
- Stored in an object.
- Memoized or wrapped.
- Given a closure over local configuration.

```js
function createFormatter(locale) {
  const formatter = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "USD"
  });

  // Function expression because the returned function is a value
  // configured by the locale argument.
  return function formatCurrency(value) {
    return formatter.format(value);
  };
}

const formatUsd = createFormatter("en-US");
console.log(formatUsd(10)); // "$10.00"
```

## 5. Named Function Expressions

Function expressions can be named. The name is useful for recursion and stack traces.

```js
const retry = function retryOperation(operation, attemptsLeft) {
  return operation().catch((error) => {
    if (attemptsLeft <= 1) {
      throw error;
    }

    return retryOperation(operation, attemptsLeft - 1);
  });
};
```

`retryOperation` is available inside the function body. Outside, the binding is `retry`.

## 6. Block-Level Function Declarations

> [!warning] Block declarations are mode-sensitive
> In strict mode and modules, function declarations inside blocks are scoped to the block. In sloppy script mode, historical behavior can be inconsistent and should not be used for app architecture.

```js
"use strict";

if (true) {
  function insideBlock() {
    return "ok";
  }

  console.log(insideBlock()); // "ok"
}

// console.log(insideBlock()); // ReferenceError
```

Production rule: avoid conditional function declarations. Prefer explicit assignment:

```js
const getVariant = featureEnabled
  ? function getNewVariant() {
      return "new";
    }
  : function getOldVariant() {
      return "old";
    };
```

## 7. Real Frontend Scenario

> [!example] Tracing a TDZ module bug
> Problem: a module computes a value before a `const` function expression is initialized.

```js
// priceLabels.js
export const defaultLabel = createLabel(20); // ReferenceError

const createLabel = (price) => `$${price.toFixed(2)}`;
```

Fix 1: move the expression above the call.

```js
const createLabel = (price) => `$${price.toFixed(2)}`;

export const defaultLabel = createLabel(20);
```

Fix 2: use a declaration when early availability is a feature of the design.

```js
export const defaultLabel = createLabel(20);

function createLabel(price) {
  return `$${price.toFixed(2)}`;
}
```

Tradeoff:

- Declaration: good for named helpers and clean stack traces.
- Expression: good when function identity is a value and initialization order should stay explicit.

## 8. React and Components

Both forms can define components:

```jsx
function ProductCard({ product }) {
  return <h2>{product.name}</h2>;
}

const ProductCardExpression = function ProductCardExpression({ product }) {
  return <h2>{product.name}</h2>;
};
```

Practical differences:

- Function declarations are easy to scan and can be defined after helper constants if your style prefers top-level components first.
- Named function expressions keep useful names in stack traces.
- Anonymous default exports make stack traces and search harder.
- Arrow components are common, but they are still function expressions with lexical `this`; see [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]].

> [!tip] Clarity over style wars
> Prefer clarity over style wars. The important thing is stable names, predictable initialization, and avoiding accidental early calls.

## 9. Bug -> Fix -> Checklist

> [!warning] Refactors can reorder initialization
> Bug: a helper is used before initialization after a refactor from declaration to expression.

```js
export function getVisibleProducts(products) {
  return products.filter(isVisible);
}

const isVisible = (product) => product.stock > 0; // TDZ before this line.
```

Fix:

```js
const isVisible = (product) => product.stock > 0;

export function getVisibleProducts(products) {
  return products.filter(isVisible);
}
```

Checklist:

- Is the function called before its declaration/initialization?
- Is it a declaration, function expression, or arrow function?
- Is the binding `var`, `let`, or `const`?
- Does the function need a stable name for stack traces?
- Is the function meant to be a reusable capability or a local configured value?
- Would moving the call below initialization make dependencies easier to read?

## 10. Interview Answer

Short answer:

> Function declarations create a named binding that is initialized before code runs in that scope, so you can call them before their source line. Function expressions create function values when the expression is evaluated.

Deeper answer:

> A declaration participates in declaration instantiation. An expression follows normal runtime evaluation and the variable it is assigned to follows `var`, `let`, or `const` rules. A named function expression can improve recursion and stack traces. The choice should be about availability, readability, and whether the function is a stable capability or a value being passed around.

Production answer:

> In modules, I use declarations for stable helpers and named components, and expressions for callbacks, factories, memoized functions, and conditionally configured behavior. I avoid anonymous default exports and avoid relying on conditional function declarations.

## 11. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Function expressions are never named." | They can be named, and that helps recursion and debugging. |
| "Declarations are always better because they hoist." | Hoisted availability can hide dependency order; use it intentionally. |
| "Arrow functions are declarations." | Arrows are expressions. |
| "A function expression assigned to `var` is hoisted with its value." | The `var` binding is hoisted to `undefined`; the function value is assigned later. |
| "Conditional function declarations are a good feature flag pattern." | Prefer explicit function values; sloppy-mode behavior is historically messy. |

## 12. Practice

1. Predict the output:

```js
console.log(a());

try {
  console.log(b());
} catch (error) {
  console.log(error.name);
}

function a() {
  return "A";
}

const b = function () {
  return "B";
};
```

Expected output:

```txt
A
ReferenceError
```

2. Convert an anonymous function expression into a named function expression and explain the debugging benefit.
3. Refactor a conditional function declaration into an explicit function value.
4. Decide whether a helper in a module should be a declaration or expression and justify the tradeoff.
5. Explain why a React component should have a searchable name.

## Real-World Use Cases

### Readable Sentry stack traces from named functions

Your error monitoring dashboard groups crashes by stack frame. A checkout module full of anonymous arrows assigned to `const` produces frames like `<anonymous>` in minified builds, so three distinct bugs collapse into one unreadable group.

```js
// Hard to trace after minification:
export default async (order) => submitOrder(order);

// Named declaration survives as a searchable frame:
export default async function submitCheckoutOrder(order) {
  return submitOrder(order);
}
```

Works because declarations and named function expressions set the function's `name` property from the source, which engines use in stack traces; an anonymous default export has no name to infer.

> [!tip]
> Named function expressions give the same benefit when the function must be a value: `const retry = function retryOperation(...) {...}`.

See [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]].

### "Public API first" module layout in a Next.js Route Handler

A route handler file reads best with the exported handler at the top and helpers below. Declarations make that ordering safe because they are initialized before the module body runs.

```ts
// app/api/orders/route.ts
export async function POST(request: Request) {
  const payload = await request.json();
  return Response.json(buildOrderResponse(validateOrder(payload)));
}

// Helpers after the export — callable because declarations hoist fully.
function validateOrder(payload) { /* ... */ }
function buildOrderResponse(order) { /* ... */ }
```

Works because of declaration instantiation: `validateOrder` exists before `POST` is ever invoked. Had the helpers been `const` arrows below the export *and called during module evaluation*, you would hit the TDZ bug from section 7.

See [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]].

### React Fast Refresh needs named components

During development, editing a file with an anonymous default export forces a full reload and loses component state, because Fast Refresh identifies components by name.

```jsx
// Breaks Fast Refresh state preservation:
export default function ({ product }) {
  return <ProductDetails product={product} />;
}

// Preserves state across hot updates:
export default function ProductPage({ product }) {
  return <ProductDetails product={product} />;
}
```

Works because the tooling reads the declaration's binding name to match the old and new component versions — an anonymous function value has nothing stable to match on.

## Related Notes

- [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]
- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions and IIFE]]
- [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[05 - this Binding/01 - What is this|What is this]]
- [[01 - Roadmap|Roadmap]]
