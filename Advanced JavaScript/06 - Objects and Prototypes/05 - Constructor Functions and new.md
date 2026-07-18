---
tags: [javascript, objects, prototypes, constructor-functions-and-new]
module: "06 - Objects and Prototypes"
priority: must-know
status: not-started
---

# Constructor Functions and new

## Maturity Target

- Priority: #must-know
- Study time: 90 minutes
- Interview signal: you can implement a simplified `new`, explain constructor return behavior, and connect it to prototypes and `instanceof`.
- Production signal: you can maintain legacy constructor code and choose classes or factories for modern code.
- Dependencies: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]], [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]

## Source Anchors

- [MDN - new operator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/new)
- [MDN - Working with objects](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Working_with_objects)
- [MDN - instanceof](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/instanceof)
- [ECMAScript 2026 - Construct](https://tc39.es/ecma262/2026/multipage/abstract-operations.html#sec-construct)

## 1. Concept

A constructor function is a regular function intended to be called with `new`.

```js
function User(name) {
  this.name = name;
}

User.prototype.greet = function greet() {
  return `Hi ${this.name}`;
};

const user = new User("Ava");

console.log(user.greet()); // "Hi Ava"
```

Before ES2015 classes, this was the main pattern for creating many objects with shared methods.

## 2. What `new` Does

Simplified steps:

1. Create a new object.
2. Set its internal prototype to `Constructor.prototype`.
3. Call the constructor with `this` set to the new object.
4. Return the constructor's object result if it returns an object; otherwise return the new object.

```js
function myNew(Constructor, ...args) {
  const instance = Object.create(Constructor.prototype);
  const result = Constructor.apply(instance, args);

  if (result !== null && (typeof result === "object" || typeof result === "function")) {
    return result;
  }

  return instance;
}
```

## 3. Constructor Return Behavior

```js
function ReturnsObject() {
  this.value = 1;
  return { value: 2 };
}

function ReturnsPrimitive() {
  this.value = 1;
  return 2;
}

console.log(new ReturnsObject().value);    // 2
console.log(new ReturnsPrimitive().value); // 1
```

This is a common output question. Returning an object replaces the constructed instance; returning a primitive does not.

## 4. `instanceof`

```js
function User(name) {
  this.name = name;
}

const user = new User("Ava");

console.log(user instanceof User);   // true
console.log(user instanceof Object); // true
```

`instanceof` asks whether `User.prototype` appears in `user`'s prototype chain.

Pitfall:

```js
function Product() {}
const product = new Product();

Product.prototype = {};

console.log(product instanceof Product); // false
```

The instance still points to the old prototype object.

## 5. Forgetting `new`

```js
function User(name) {
  "use strict";
  this.name = name;
}

try {
  User("Ava");
} catch (error) {
  console.log(error.name); // "TypeError"
}
```

In sloppy mode, forgetting `new` can write to `globalThis`. Classes prevent this by throwing when called without `new`.

Legacy safeguard:

```js
function User(name) {
  if (!(this instanceof User)) {
    return new User(name);
  }

  this.name = name;
}
```

Modern preference: use `class` or factory functions instead of new constructor functions in app code.

## 6. Methods Inside Constructor vs Prototype

Inefficient pattern:

```js
function User(name) {
  this.name = name;
  this.greet = function greet() {
    return `Hi ${this.name}`;
  };
}

const a = new User("A");
const b = new User("B");

console.log(a.greet === b.greet); // false
```

Shared method pattern:

```js
function User(name) {
  this.name = name;
}

User.prototype.greet = function greet() {
  return `Hi ${this.name}`;
};

const a = new User("A");
const b = new User("B");

console.log(a.greet === b.greet); // true
```

> [!tip] Tradeoff
> per-instance methods can close over constructor-local private data, but shared prototype methods are more memory-efficient.

## 7. Real Frontend Scenario: Legacy Widget

```js
function Tooltip(root) {
  this.root = root;
  this.message = root.getAttribute("data-tooltip") ?? "";
  this.show = this.show.bind(this);
}

Tooltip.prototype.mount = function mount() {
  this.root.addEventListener("mouseenter", this.show);
};

Tooltip.prototype.unmount = function unmount() {
  this.root.removeEventListener("mouseenter", this.show);
};

Tooltip.prototype.show = function show() {
  console.log(this.message);
};

const tooltip = new Tooltip(document.querySelector("[data-tooltip]"));
tooltip.mount();
```

Production notes:

- Shared methods live on the prototype.
- The event handler is bound once for stable cleanup.
- DOM ownership is explicit.
- A modern implementation might use a class or a framework component, but the prototype mechanics are the same.

## 8. Constructor vs Factory vs Class

Constructor function:

```js
function User(name) {
  this.name = name;
}
```

Factory:

```js
function createUser(name) {
  return {
    name,
    greet() {
      return `Hi ${name}`;
    }
  };
}
```

Class:

```js
class User {
  constructor(name) {
    this.name = name;
  }

  greet() {
    return `Hi ${this.name}`;
  }
}
```

Production preference:

- Use classes when you need instances, inheritance, or prototype methods.
- Use factories when you want explicit returns, closure privacy, or no `new`.
- Avoid legacy constructor functions for new app code unless matching existing code.

## Real-World Use Cases

### Platform constructors you `new` every day: `URL` and `URLSearchParams`

String concatenation for URLs breaks on encoding and duplicate `?`. The platform's answer is constructor instances with prototype methods.

```js
function buildSearchUrl(baseUrl, filters) {
  const url = new URL("/api/products", baseUrl);

  for (const [key, value] of Object.entries(filters)) {
    url.searchParams.set(key, value); // encodes "wireless & bluetooth" correctly
  }

  return url.toString();
}
```

`new URL(...)` runs the exact algorithm from section 2: fresh object, internal prototype set to `URL.prototype` (where `toString`, `searchParams` accessors live), constructor initializes own state. Same story for `new AbortController()`, `new IntersectionObserver(cb)`, `new FormData(form)` — daily frontend code is full of `new`. See [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]] and [[08 - Async JavaScript/06 - AbortController|AbortController]].

### Error branching with `instanceof` in a fetch wrapper

A data layer throws typed errors; UI code decides retry vs redirect vs toast by checking the prototype chain.

```ts
class HttpError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

try {
  await api.get("/orders");
} catch (error) {
  if (error instanceof HttpError && error.status === 401) return redirectToLogin();
  if (error instanceof TypeError) return showOfflineBanner(); // fetch network failure
  throw error;
}
```

Works because constructing with `new` (via `class`) linked the instance to `HttpError.prototype`, so `instanceof` finds it in the chain — carrying more signal than string-matching `error.message`.

> [!warning]
> If your build targets ES5, `instanceof` on subclassed errors silently breaks — see the fix in [[06 - Objects and Prototypes/04 - proto vs prototype|proto vs prototype]] and [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]].

### Cross-realm `instanceof` failure in embedded frames

A checkout page receives data from a payment iframe via `postMessage`. A defensive `instanceof Array` check rejects perfectly good arrays.

```js
window.addEventListener("message", (event) => {
  const { lineItems } = event.data;

  if (lineItems instanceof Array) {  // false for arrays born in the iframe realm
    renderLineItems(lineItems);
  }
});
```

Fails because each realm (iframe, worker, window) has its **own** `Array` constructor and `Array.prototype`; the iframe's array has the iframe's prototype in its chain, never the parent page's. `Array.isArray(lineItems)` checks the internal array-ness instead of chain membership.

> [!tip]
> Same reason libraries use `Object.prototype.toString.call(x)` or structural checks instead of `instanceof` for values that may cross boundaries. See [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]].

## 9. Interview Answer

Short answer:

> A constructor function is a function called with `new`. `new` creates an object, links it to the constructor's `.prototype`, calls the constructor with `this`, and returns the object unless the constructor returns another object.

Deeper answer:

> Methods placed on `Constructor.prototype` are shared by all instances. `instanceof` checks whether `Constructor.prototype` is in the object's prototype chain. Forgetting `new` is dangerous in constructor functions because `this` can be wrong; classes solve this by throwing when called without `new`.

Production answer:

> I mostly use classes or factories in modern code, but understanding constructor functions is essential for prototypes, legacy code, and class internals. I avoid defining methods inside constructors unless per-instance closure state is required.

## 10. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Constructor methods must be inside the constructor." | Prototype methods are shared and usually better. |
| "`new` always returns `this`." | Explicit object returns override `this`. |
| "`instanceof` checks fields." | It checks the prototype chain. |
| "Replacing `.prototype` updates old instances." | Existing instances keep their old prototype link. |
| "Constructor functions are the same safety level as classes." | Classes throw without `new`; constructor functions may not. |

## 11. Practice

1. Implement `myNew(Constructor, ...args)`.
2. Predict the output:

```js
function User() {
  this.name = "Ava";
  return { name: "Mina" };
}

console.log(new User().name);
```

Expected output: `"Mina"`.

3. Show why methods inside constructors create separate functions per instance.
4. Explain why replacing `Fn.prototype` affects future instances but not existing ones.
5. Convert a constructor function into a class and into a factory.

## Related Notes

- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[06 - Objects and Prototypes/04 - proto vs prototype|proto vs prototype]]
- [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]
- [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]
- [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]]
- [[01 - Roadmap|Roadmap]]
