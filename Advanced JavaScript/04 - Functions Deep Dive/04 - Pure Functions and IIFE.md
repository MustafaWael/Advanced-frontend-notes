---
tags: [javascript, functions, pure-functions-and-iife]
module: "04 - Functions Deep Dive"
priority: important
status: not-started
aliases: [IIFE]
---

# Pure Functions and IIFE

## Maturity Target

- Priority: #important
- Study time: 90 minutes
- Interview signal: you can explain purity, side effects, idempotence, local mutation, and why IIFEs existed before modules.
- Production signal: you keep render/calculation code predictable and move effects to explicit boundaries.
- Dependencies: [[03 - Scope and Variables/05 - Closures|Closures]], [[10 - Modules/01 - ES Modules|ES Modules]], [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]

## Source Anchors

- [React - Components and Hooks must be pure](https://react.dev/reference/rules/components-and-hooks-must-be-pure)
- [MDN - IIFE](https://developer.mozilla.org/en-US/docs/Glossary/IIFE)
- [MDN - Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [MDN - Functions guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions)

## 1. Concept

A pure function is a function that:

1. Returns the same result for the same inputs.
2. Does not cause observable side effects while calculating the result.
3. Does not mutate values it does not own.

```js
function calculateSubtotal(items) {
  return items.reduce((total, item) => total + item.price * item.quantity, 0);
}

console.log(calculateSubtotal([{ price: 5, quantity: 2 }])); // 10
```

An IIFE, or immediately invoked function expression, is a function expression that runs immediately after it is created.

```js
const config = (() => {
  const baseUrl = "/api";
  return { baseUrl };
})();

console.log(config.baseUrl); // "/api"
```

These topics belong together because both are about boundaries: what code calculates, what code mutates, and what scope contains temporary/private values.

## 2. Why It Matters

Purity is how you make functions easy to test, cache, retry, parallelize, and reason about. In React, purity is even more important because render logic can be called multiple times.

IIFEs are less common in modern module-based code, but you still need to recognize them in legacy code and understand when immediate initialization is useful.

## 3. Pure Function Mechanics

Pure:

```js
function applyDiscount(price, percent) {
  return price - price * percent;
}

console.log(applyDiscount(100, 0.2)); // 80
```

Impure because it reads external mutable state:

```js
let currentDiscount = 0.2;

function applyCurrentDiscount(price) {
  return price - price * currentDiscount;
}
```

Impure because it mutates non-local data:

```js
function addItem(cart, item) {
  cart.items.push(item); // Mutates caller-owned object.
  return cart;
}
```

Safer pure version:

```js
function addItem(cart, item) {
  return {
    ...cart,
    items: [...cart.items, item]
  };
}
```

## 4. Local Mutation Is Not the Enemy

Local mutation can be perfectly fine when it cannot be observed outside the function.

```js
function groupByCategory(products) {
  const groups = {};

  for (const product of products) {
    const key = product.category;
    groups[key] ??= [];
    groups[key].push(product);
  }

  return groups;
}
```

This function mutates `groups`, but `groups` is created inside the function. The caller cannot observe intermediate mutation. The important question is ownership.

## 5. React Render Purity

Bug:

```jsx
const rows = [];

function ProductRows({ products }) {
  for (const product of products) {
    rows.push(<li key={product.id}>{product.name}</li>);
  }

  return <ul>{rows}</ul>;
}
```

> [!warning] Failure mode
> every render appends more rows because `rows` is created outside the component and mutated during render.

Fix:

```jsx
function ProductRows({ products }) {
  const rows = [];

  for (const product of products) {
    rows.push(<li key={product.id}>{product.name}</li>);
  }

  return <ul>{rows}</ul>;
}
```

This local mutation is safe because `rows` is recreated on every render.

Another bug:

```jsx
function Clock() {
  return <span>{new Date().toLocaleTimeString()}</span>;
}
```

`new Date()` is not idempotent during render. A better approach is to synchronize time with an effect or external store.

## 6. Side Effects Belong at Boundaries

Side effects include:

- Network calls.
- DOM mutations.
- Logging and analytics.
- Writing storage.
- Mutating arguments or module/global state.
- Starting timers.
- Subscriptions.

Good production design pushes side effects to explicit boundaries:

```js
function buildAnalyticsEvent(product, position) {
  return {
    type: "product_clicked",
    productId: product.id,
    position
  };
}

function trackProductClick(product, position) {
  const event = buildAnalyticsEvent(product, position);
  analytics.track(event);
}
```

The pure builder is easy to test. The impure sender is intentionally isolated.

## 7. IIFE Mechanics

An IIFE creates a function scope and runs immediately.

```js
(function initializeLegacyWidget() {
  const root = document.querySelector("#legacy-widget");

  if (!root) {
    return;
  }

  root.textContent = "Ready";
})();
```

Common IIFE forms:

```js
(function () {
  console.log("classic IIFE");
})();

(() => {
  console.log("arrow IIFE");
})();

const result = (function () {
  return 42;
})();

console.log(result); // 42
```

## 8. Why IIFEs Existed

Before ES modules and block-scoped declarations were common, IIFEs were used to:

- Avoid leaking variables to global scope.
- Create private state through closures.
- Run initialization once.
- Build old module patterns.

```js
const counter = (function createCounterModule() {
  let count = 0;

  return {
    increment() {
      count += 1;
      return count;
    },
    read() {
      return count;
    }
  };
})();

console.log(counter.increment()); // 1
console.log(counter.read());      // 1
```

Modern alternative:

```js
// counter.js
let count = 0;

export function increment() {
  count += 1;
  return count;
}

export function read() {
  return count;
}
```

> [!tip] Tradeoff
> modules are clearer for reusable code. IIFEs are still useful for immediate one-time setup, isolated scripts, and expression-based initialization.

## 9. Real Frontend Scenario

Problem: a selector mutates its input by sorting.

```js
function getTopProducts(products) {
  return products.sort((a, b) => b.score - a.score).slice(0, 5);
}
```

Bug: `sort` mutates `products`, so any component using the original order now sees changed data.

Fix:

```js
function getTopProducts(products) {
  return [...products]
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);
}
```

> [!tip] Tradeoff
> copying costs memory and time. For UI lists, correctness usually wins. For very large data, consider immutable data APIs, pre-sorted server data, or memoization with clear invalidation.

## 10. Bug -> Fix -> Checklist

When reviewing a function, ask:

- Does it read time, random values, globals, DOM, storage, or network?
- Does it mutate an argument?
- Does it mutate module/global state?
- Is any mutation local and unobservable?
- Would running it twice with the same inputs produce the same result?
- In React, could render run multiple times and produce duplicate effects?
- Would separating "build data" from "send/do effect" make testing easier?
- Is an IIFE hiding side effects at import time?

## 11. Interview Answer

Short answer:

> A pure function returns the same output for the same inputs and has no observable side effects. An IIFE is a function expression that is invoked immediately.

Deeper answer:

> Purity is about predictable calculation and ownership. Local mutation can be fine if the mutated value is created inside the function and not observable outside. Mutating arguments, globals, DOM, storage, or module state makes the function impure. IIFEs create an immediate private scope and were commonly used before modules to avoid globals.

Production answer:

> In frontend code, pure selectors and render helpers are easier to test and memoize. Side effects should live in event handlers, effects, route handlers, or explicit service boundaries. I avoid import-time IIFEs that start work unexpectedly.

## 12. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Pure means no variables inside." | Local variables and local mutation are fine when unobservable. |
| "Pure functions can log." | Logging is an observable side effect. |
| "React render can safely start timers." | Timers are side effects and belong outside render. |
| "IIFEs are obsolete everywhere." | Less common, but still useful for isolated one-time expression setup. |
| "Copying before `sort` is always free." | It has a cost; use it because correctness requires it. |

## 13. Practice

1. Make this function pure:

```js
let taxRate = 0.14;

function totalWithTax(subtotal) {
  return subtotal + subtotal * taxRate;
}
```

Possible answer:

```js
function totalWithTax(subtotal, taxRate) {
  return subtotal + subtotal * taxRate;
}
```

2. Explain why mutating a locally created array can still be pure.
3. Fix a React render function that writes to a module-level array.
4. Replace an IIFE module pattern with ES module exports.
5. Identify whether a function that reads `Date.now()` is pure and why.

## Related Notes

- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]
- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[01 - Roadmap|Roadmap]]
