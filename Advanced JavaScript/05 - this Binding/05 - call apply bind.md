---
tags: [javascript, this-binding, call-apply-bind]
module: "05 - this Binding"
priority: must-know
status: not-started
aliases: [Explicit Binding]
---

# call apply bind

## Maturity Target

- Priority: #must-know
- Study time: 90 minutes
- Interview signal: you can compare `call`, `apply`, and `bind`, then explain bound function behavior and partial arguments.
- Production signal: you can preserve context in callbacks and wrappers without losing arguments, return values, or cleanup references.
- Dependencies: [[05 - this Binding/01 - What is this|What is this]], [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]]

## Source Anchors

- [MDN - Function.prototype.call](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/call)
- [MDN - Function.prototype.apply](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/apply)
- [MDN - Function.prototype.bind](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind)
- [MDN - Reflect.apply](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Reflect/apply)
- [ECMAScript 2026 - Function.prototype.bind](https://tc39.es/ecma262/2026/multipage/fundamental-objects.html#sec-function.prototype.bind)

## 1. Concept

`call`, `apply`, and `bind` are methods available on functions.

| Method | What it does | Argument style |
| --- | --- | --- |
| `call` | Calls immediately with explicit `this` | Individual arguments |
| `apply` | Calls immediately with explicit `this` | Array or array-like arguments |
| `bind` | Returns a new function with fixed `this` and optional preset args | Individual preset arguments |

```js
function greet(greeting, punctuation) {
  return `${greeting}, ${this.name}${punctuation}`;
}

const user = { name: "Ava" };

console.log(greet.call(user, "Hello", "!"));      // "Hello, Ava!"
console.log(greet.apply(user, ["Hi", "."]));      // "Hi, Ava."
console.log(greet.bind(user, "Welcome")("?"));    // "Welcome, Ava?"
```

## 2. Why It Matters

Explicit binding is useful when:

- A method is passed as a callback.
- You need to borrow a method.
- You are writing wrappers around functions.
- You want partial application.
- You need a stable function reference for event cleanup.

It is also easy to misuse:

- `bind` creates a new function each time.
- Rebinding an already bound function does not replace its original bound `this`.
- `call`/`apply` cannot change arrow `this`.
- Wrappers can accidentally drop arguments or return values.

## 3. `call`

`call` invokes the function immediately with a chosen `this`.

```js
function format(price) {
  return `${this.currency}${price.toFixed(2)}`;
}

const usd = { currency: "$" };
const eur = { currency: "EUR " };

console.log(format.call(usd, 12)); // "$12.00"
console.log(format.call(eur, 12)); // "EUR 12.00"
```

Production use: method borrowing.

```js
function listArguments() {
  return Array.prototype.slice.call(arguments);
}

console.log(listArguments("a", "b")); // ["a", "b"]
```

Modern code often uses rest parameters instead, but method borrowing still appears in older libraries and interview questions.

## 4. `apply`

`apply` is like `call`, but arguments come from an array or array-like object.

```js
function max(a, b, c) {
  return Math.max(a, b, c);
}

console.log(max.apply(null, [2, 9, 4])); // 9
```

Modern equivalent:

```js
console.log(max(...[2, 9, 4])); // 9
```

Production warning: spreading or applying huge arrays into calls can hit engine argument limits. Use iteration for large datasets.

## 5. `bind`

`bind` returns a new function. It does not call immediately.

```js
const formatter = {
  currency: "$",
  format(price) {
    return `${this.currency}${price.toFixed(2)}`;
  }
};

const formatUsd = formatter.format.bind(formatter);

console.log(formatUsd(10)); // "$10.00"
```

`bind` can also preset leading arguments:

```js
function request(method, path, body) {
  return { method, path, body };
}

const post = request.bind(null, "POST");

console.log(post("/api/products", { name: "Keyboard" }));
// { method: "POST", path: "/api/products", body: { name: "Keyboard" } }
```

## 6. Bound Function Behavior

Binding again does not change the original bound `this`.

```js
function readName() {
  return this.name;
}

const bound = readName.bind({ name: "Ava" });
const rebound = bound.bind({ name: "Mina" });

console.log(rebound()); // "Ava"
```

Every `bind` call creates a new function reference:

```js
const a = formatter.format.bind(formatter);
const b = formatter.format.bind(formatter);

console.log(a === b); // false
```

This matters for event cleanup:

```js
button.addEventListener("click", controller.open.bind(controller));

// Bug: this is a different bound function, so the old listener remains.
button.removeEventListener("click", controller.open.bind(controller));
```

Fix:

```js
controller.boundOpen = controller.open.bind(controller);

button.addEventListener("click", controller.boundOpen);
button.removeEventListener("click", controller.boundOpen);
```

## 7. Arrows and Explicit Binding

`call`, `apply`, and `bind` cannot change an arrow function's `this`.

```js
const arrow = () => this?.name;

console.log(arrow.call({ name: "Ava" })); // undefined in ES modules
```

They can still supply arguments:

```js
const add = (a, b) => a + b;

console.log(add.call(null, 2, 3)); // 5
```

## 8. Real Frontend Scenario: Safe Wrapper

> [!warning] Bug
> a wrapper drops `this` and arguments.

```js
function withLogging(fn) {
  return function wrapped() {
    console.log("calling");
    return fn(); // Drops this and arguments.
  };
}

const cart = {
  taxRate: 0.1,
  total(subtotal) {
    return subtotal + subtotal * this.taxRate;
  }
};

const loggedTotal = withLogging(cart.total);

try {
  console.log(loggedTotal.call(cart, 100));
} catch (error) {
  console.log(error.name); // "TypeError"
}
```

Fix:

```js
function withLogging(fn) {
  return function wrapped(...args) {
    console.log("calling");
    return fn.apply(this, args);
  };
}

const loggedTotal = withLogging(cart.total);

console.log(loggedTotal.call(cart, 100)); // 110
```

Why the fix works: the wrapper forwards the call receiver and the arguments to the original function.

## 9. React Class Scenario

```jsx
class Counter extends React.Component {
  constructor(props) {
    super(props);
    this.state = { count: 0 };
    this.increment = this.increment.bind(this);
  }

  increment() {
    this.setState((state) => ({ count: state.count + 1 }));
  }

  render() {
    return <button onClick={this.increment}>{this.state.count}</button>;
  }
}
```

Binding in the constructor creates one stable callback per instance. That is usually better than calling `.bind(this)` inside `render`, which creates a new function each render.

## Real-World Use Cases

### Prefixed logger via `bind` partial application

A module-scoped logger that tags every line with its feature area — one line of setup, no wrapper function to maintain.

```js
const log = console.log.bind(console, "[checkout]");
const warn = console.warn.bind(console, "[checkout]");

log("payment intent created", intentId);
// "[checkout] payment intent created pi_3Nc..."
warn("3DS challenge required");
```

Works because the bound function stores both the receiver (`console`) and the preset leading arguments; later arguments are appended after them. Bonus: unlike `(...args) => console.log("[checkout]", ...args)`, the bound function preserves the original call site in browser devtools line numbers. See [[04 - Functions Deep Dive/06 - Currying and Partial Application|Currying and Partial Application]].

### Safe `hasOwnProperty` on untrusted objects

An API route checks keys on parsed JSON. The payload can shadow `hasOwnProperty`, and objects built with `Object.create(null)` have no prototype at all — so calling the method through the object is unsafe.

```js
const query = JSON.parse(rawBody); // could be {"hasOwnProperty": 1, "coupon": "..."}

query.hasOwnProperty("coupon"); // TypeError or attacker-controlled result

if (Object.prototype.hasOwnProperty.call(query, "coupon")) {
  applyCoupon(query.coupon); // safe: real method, explicit receiver
}
```

Works because `call` borrows the genuine prototype method and supplies the receiver explicitly, bypassing the object's own (possibly hostile or absent) property lookup. ESLint's `no-prototype-builtins` rule enforces exactly this pattern.

> [!tip]
> Modern replacement: `Object.hasOwn(query, "coupon")` — same semantics, no borrowing ceremony.

### `requestAnimationFrame` loop with a bound tick

A canvas progress ring re-schedules itself every frame. `requestAnimationFrame` invokes its callback as a plain call, so the tick method needs binding — but binding per frame allocates a new function 60 times a second.

```js
class ProgressRing {
  constructor(canvas) {
    this.ctx = canvas.getContext("2d");
    this.tick = this.tick.bind(this); // bind once, reuse every frame
  }

  tick(timestamp) {
    this.draw(timestamp);
    this.frameId = requestAnimationFrame(this.tick);
  }

  start() { this.frameId = requestAnimationFrame(this.tick); }
  stop() { cancelAnimationFrame(this.frameId); }
}
```

Works because the constructor replaces the instance's `tick` with one stable bound function — `this` is fixed, and `start`/`tick`/`stop` all share the same reference.

> [!warning]
> `requestAnimationFrame(this.tick.bind(this))` inside `tick` works but creates a fresh closure every frame — needless garbage-collector pressure in a hot path.

## 10. Debugging Checklist

- Does the function need a dynamic receiver?
- Should the call happen now (`call`/`apply`) or later (`bind`)?
- Are arguments individual or already collected in an array?
- Are you binding inside a render/loop repeatedly?
- Are you trying to rebind an already bound function?
- Are you trying to change arrow `this`?
- Does cleanup use the same bound function reference?
- Should a wrapper use `apply(this, args)`?

## 11. Interview Answer

Short answer:

> `call` and `apply` call a function immediately with an explicit `this`; `call` takes arguments individually, `apply` takes them as an array. `bind` returns a new function with fixed `this` and optional preset arguments.

Deeper answer:

> `bind` creates a bound function object that stores the target function, bound `this`, and bound arguments. Calling `bind` again can add more arguments, but it does not replace the original bound `this`. `call` and `apply` are immediate invocation tools; `bind` is for later callbacks.

Production answer:

> I use `bind` when I need a stable callback that preserves context, and I store that reference for cleanup. In wrappers, I use `fn.apply(this, args)` when the original function may rely on dynamic `this`.

## 12. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "`bind` calls the function immediately." | `bind` returns a new function. |
| "Calling `bind` twice changes `this` twice." | The first bound `this` wins. |
| "`call` and `apply` differ in `this` behavior." | They differ mainly in argument format. |
| "`call` can fix arrow `this`." | Arrow `this` is lexical. |
| "Binding inline is fine for cleanup." | Inline `bind` creates different function references. |

## 13. Practice

1. Predict the output:

```js
function read() {
  return this.value;
}

const bound = read.bind({ value: 1 });
const rebound = bound.bind({ value: 2 });

console.log(rebound());
```

Expected output: `1`.

2. Implement a `withTiming(fn)` wrapper that preserves `this`, arguments, return value, and thrown errors.
3. Explain why `removeEventListener("click", obj.fn.bind(obj))` fails when `addEventListener` used another `bind` call.
4. Convert an `apply` example to spread syntax.
5. Explain why `Function.prototype.call.bind(Array.prototype.slice)` works at a high level.

## Related Notes

- [[05 - this Binding/01 - What is this|What is this]]
- [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]
- [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]
- [[05 - this Binding/07 - React this Examples|React this Examples]]
- [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]]
- [[04 - Functions Deep Dive/06 - Currying and Partial Application|Currying and Partial Application]]
- [[01 - Roadmap|Roadmap]]
