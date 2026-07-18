---
tags: [javascript, this-binding, this-in-objects-and-functions]
module: "05 - this Binding"
priority: must-know
status: not-started
---

# this in Objects and Functions

## Maturity Target

- Priority: #must-know
- Study time: 90 minutes
- Interview signal: you can explain implicit binding, context loss, nested function traps, and method borrowing.
- Production signal: you can fix object-method bugs in callbacks, array methods, event listeners, and utility wrappers.
- Dependencies: [[05 - this Binding/01 - What is this|What is this]], [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]

## Source Anchors

- [MDN - this](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this)
- [MDN - Function.prototype.call](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/call)
- [MDN - Function.prototype.bind](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind)
- [MDN - Working with objects](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Working_with_objects)

## 1. Concept

For regular functions used as object methods, `this` is based on the call receiver.

```js
const user = {
  name: "Ava",
  greet() {
    return `Hi ${this.name}`;
  }
};

console.log(user.greet()); // "Hi Ava"
```

The method is not permanently bound to `user`. It is a function value stored on an object property.

## 2. Why It Matters

Object-method `this` bugs happen when code accidentally separates the function from the object:

- `const fn = user.greet; fn()`
- `items.map(formatter.format)`
- `button.addEventListener("click", controller.handleClick)`
- `setTimeout(obj.method, 0)`
- A wrapper returns a function but does not preserve `this`

These are common in real frontend code because callbacks are everywhere.

## 3. Implicit Binding

```js
const formatter = {
  prefix: "$",
  format(value) {
    return `${this.prefix}${value.toFixed(2)}`;
  }
};

console.log(formatter.format(10)); // "$10.00"
```

Only the object used in the call expression matters:

```js
const otherFormatter = {
  prefix: "USD ",
  format: formatter.format
};

console.log(otherFormatter.format(10)); // "USD 10.00"
```

The function is reused, and `this` becomes `otherFormatter`.

## 4. Context Loss

```js
const format = formatter.format;

try {
  console.log(format(10));
} catch (error) {
  console.log(error.name); // "TypeError" in strict/module code
}
```

The call is now `format(10)`, a plain function call. The receiver is gone.

This is *the* classic interview trap for `this` — expect it in some form (`const fn = obj.method; fn()`). Trace it step by step:

1. `formatter.format` is a **property read**. It evaluates to the plain function value — the receiver is part of the call expression, never part of the function value.
2. `format(10)` is a **plain call**, so **default binding** applies.
3. In strict/module code, default binding leaves `this` as `undefined` (see [[05 - this Binding/02 - this in Strict Mode|this in Strict Mode]]), so reading `this.prefix` throws a `TypeError`. In a sloppy script, `this` would be substituted with `globalThis` and you would silently get `"undefined10.00"` — arguably worse.

Fix with a wrapper:

```js
const format = (value) => formatter.format(value);

console.log(format(10)); // "$10.00"
```

Fix with `bind`:

```js
const format = formatter.format.bind(formatter);

console.log(format(10)); // "$10.00"
```

## 5. Nested Function Trap

```js
const counter = {
  count: 0,
  incrementLater() {
    function increment() {
      this.count += 1;
    }

    increment();
  }
};

try {
  counter.incrementLater();
} catch (error) {
  console.log(error.name); // "TypeError" in strict/module code
}

console.log(counter.count); // 0
```

`incrementLater` is called as a method, so inside it `this === counter`. But `increment()` is a plain call, so its own `this` is not `counter`.

Fix with an arrow callback:

```js
const counter = {
  count: 0,
  incrementLater() {
    const increment = () => {
      this.count += 1; // lexical this from incrementLater
    };

    increment();
  }
};

counter.incrementLater();
console.log(counter.count); // 1
```

Fix by passing the receiver explicitly:

```js
function increment(counter) {
  counter.count += 1;
}

const counter = {
  count: 0,
  incrementLater() {
    increment(this);
  }
};
```

Production preference: if a helper does not need dynamic dispatch, explicit parameters are easier to test than hidden `this`.

## 6. Method Borrowing

`call` and `apply` can deliberately borrow a method for another receiver.

```js
function formatValue(value) {
  return `${this.prefix}${value}`;
}

const usd = { prefix: "$" };
const eur = { prefix: "EUR " };

console.log(formatValue.call(usd, 10)); // "$10"
console.log(formatValue.call(eur, 10)); // "EUR 10"
```

Old array-like conversion:

```js
function toArray() {
  return Array.prototype.slice.call(arguments);
}

console.log(toArray("a", "b")); // ["a", "b"]
```

Modern code often prefers rest parameters:

```js
function toArray(...items) {
  return items;
}
```

## 7. Real Frontend Scenario: Controller Methods

Bug:

```js
class ModalController {
  constructor(root) {
    this.root = root;
  }

  open() {
    this.root.hidden = false;
  }

  mount(button) {
    button.addEventListener("click", this.open);
  }
}
```

> [!warning] Failure mode
> when the click fires, the browser calls the listener without the controller as receiver. `this` is not the controller.

Fix with constructor binding:

```js
class ModalController {
  constructor(root) {
    this.root = root;
    this.open = this.open.bind(this);
  }

  open() {
    this.root.hidden = false;
  }

  mount(button) {
    button.addEventListener("click", this.open);
  }

  unmount(button) {
    button.removeEventListener("click", this.open);
  }
}
```

Why this fix works: `this.open` is replaced with a bound function whose `this` is permanently the controller instance. The same reference can be used for cleanup.

## 8. Object Methods vs Closures

Sometimes `this` is the wrong abstraction.

```js
function createFormatter(prefix) {
  return function format(value) {
    return `${prefix}${value.toFixed(2)}`;
  };
}

const formatUsd = createFormatter("$");

console.log(formatUsd(10)); // "$10.00"
```

This closure-based design avoids receiver binding completely. It is excellent for configured utilities. Use object methods when you need polymorphism, shared prototypes, or method dispatch through an object.

## Real-World Use Cases

### Analytics method passed to a router event

A page-view tracker subscribes to Next.js router events. The emitter calls listeners as plain functions, so the method arrives without its instance.

```js
class Tracker {
  constructor(appId) {
    this.appId = appId;
  }

  pageView(url) {
    navigator.sendBeacon("/collect", JSON.stringify({ app: this.appId, url }));
  }
}

const tracker = new Tracker("shop-web");
router.events.on("routeChangeComplete", tracker.pageView); // this lost on every navigation
```

Fails because passing `tracker.pageView` copies only the function value — the emitter's internal call is plain, so default binding applies.

> [!tip]
> Store one bound reference: `const onRoute = tracker.pageView.bind(tracker)`. You need that exact reference again for `router.events.off("routeChangeComplete", onRoute)` — an inline `bind` at unsubscribe time is a different function and removes nothing. See [[05 - this Binding/05 - call apply bind|call apply bind]].

### `items.map(formatter.format)` in a render path

A price list maps raw cents through a shared formatter object. Passing the method directly to `map` is the same detached call, hidden one level deeper.

```jsx
const priceFormatter = {
  locale: "en-US",
  format(cents) {
    return (cents / 100).toLocaleString(this.locale, { style: "currency", currency: "USD" });
  }
};

function PriceList({ cents }) {
  const prices = cents.map(priceFormatter.format); // TypeError: this is undefined
  return <ul>{prices.map((p) => <li key={p}>{p}</li>)}</ul>;
}
```

Fails because `map` invokes its callback as a plain call; the receiver from `priceFormatter.format` never travels with the function.

> [!tip]
> Wrapper arrow `cents.map((c) => priceFormatter.format(c))`, or the often-forgotten second argument: `cents.map(priceFormatter.format, priceFormatter)` — `map`, `forEach`, `filter`, `some`, and `every` all accept a `thisArg`.

### Promise chain feeding a store method

Fetched data is handed straight to a store method inside `.then`. The failure only appears when the promise resolves — as an unhandled rejection with a stack trace pointing into promise internals, far from the buggy line.

```js
class OrdersStore {
  orders = [];

  save(data) {
    this.orders = data;
  }
}

const store = new OrdersStore();

fetch("/api/orders")
  .then((response) => response.json())
  .then(store.save); // TypeError — but only later, on a microtask
```

Fails for the same reason as `const fn = obj.method`: `.then` receives the bare function and calls it plainly when the microtask runs. Fix with `.then((data) => store.save(data))`.

> [!warning]
> Because the plain call happens asynchronously, strict mode's fast failure is deferred — the error surfaces as an unhandled rejection in a later microtask. See [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]].

## 9. Debugging Checklist

- Is the failing function called with `obj.method()` or as a plain function?
- Was a method assigned to a variable?
- Was a method passed to `map`, `forEach`, `setTimeout`, or an event listener?
- Is the method called through another object?
- Would `bind` create a stable callback reference?
- Would an arrow inside a method preserve outer `this`?
- Would explicit parameters remove hidden context?

## 10. Interview Answer

Short answer:

> When a regular function is called as `obj.method()`, `this` is `obj`. If you extract the method and call it as `fn()`, the object is lost.

Deeper answer:

> Method calls preserve a receiver through the call expression. JavaScript functions are first-class values, so assigning or passing a method copies the function reference, not the receiver. That is why context loss happens in callbacks. Fixes include wrappers, `bind`, arrows inside methods, or refactoring to explicit parameters.

Production answer:

> In frontend code, I watch for methods passed to event listeners, timers, array callbacks, and custom wrappers. If cleanup matters, I prefer a stable bound method or stored wrapper so `removeEventListener` receives the same function reference.

## 11. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Methods remember their object." | The call expression supplies the receiver. |
| "Nested functions share outer `this`." | Regular nested functions get their own `this` based on their own call. |
| "`a.b.c()` means `this` is `a`." | `this` is `a.b`. |
| "A wrapper always preserves behavior." | It must forward `this`, arguments, returns, and errors deliberately. |
| "Use `this` for every helper in an object." | Explicit parameters are often clearer for pure utilities. |

## 12. Practice

1. Predict the output:

```js
"use strict";

const obj = {
  x: 1,
  getX() {
    return this.x;
  }
};

const fn = obj.getX;

console.log(obj.getX());

try {
  console.log(fn());
} catch (error) {
  console.log(error.name);
}

console.log(obj.getX.call({ x: 99 }));
```

Expected output:

```txt
1
TypeError
99
```

2. Fix a nested function trap using an arrow and using explicit parameters.
3. Explain why `items.map(formatter.format)` can fail.
4. Write a wrapper that preserves `this` using `apply`.
5. Compare object-method style and closure factory style for a formatter.

## Related Notes

- [[05 - this Binding/01 - What is this|What is this]]
- [[05 - this Binding/02 - this in Strict Mode|this in Strict Mode]]
- [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]
- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[01 - Roadmap|Roadmap]]
