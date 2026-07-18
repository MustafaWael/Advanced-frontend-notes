---
tags: [javascript, this-binding, what-is-this]
module: "05 - this Binding"
priority: must-know
status: not-started
---

# What is this

## Maturity Target

- Priority: #must-know
- Study time: 75-90 minutes
- Interview signal: you can determine `this` from the call site, not from where the function was written.
- Production signal: you can spot context loss when methods are passed as callbacks, used in event handlers, or wrapped by utilities.
- Dependencies: [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]], [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]

## Source Anchors

- [MDN - this](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this)
- [MDN - Strict mode](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode)
- [MDN - Arrow functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions)
- [MDN - Function.prototype.bind](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind)
- [ECMAScript 2026 - ResolveThisBinding](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-resolvethisbinding)

## 1. Concept

`this` is a special binding created by JavaScript for many execution contexts. In regular functions, its value is usually determined by how the function is called.

```js
function readName() {
  return this.name;
}

const user = { name: "Ava", readName };

console.log(user.readName()); // "Ava"
```

> [!example] Same function, different this
> The same function can produce a different `this` value when called differently:

```js
const read = user.readName;

try {
  console.log(read());
} catch (error) {
  console.log(error.name); // "TypeError" in strict/module code
}
```

The binding was not attached permanently to the function when the object was created.

## 2. Why It Matters

Most `this` bugs are not syntax bugs. They are ownership bugs:

- A method is passed as a callback and loses its receiver.
- An object method is written as an arrow function and reads outer `this`.
- A class method is used as an event handler without binding.
- A wrapper calls `fn(...args)` instead of `fn.apply(this, args)`.
- Code behaves differently in script vs module or strict vs sloppy mode.

In interviews, `this` questions test whether you reason from the call expression. In production, they test whether your callbacks preserve the owner they need.

## 3. Official Mechanism

For regular functions, each call creates a function execution context with a `ThisBinding`. The call evaluation decides what value is used.

The useful decision order:

1. Was the function called with `new`? Then `this` is the newly created object.
2. Was it called with `call`, `apply`, or a bound function? Then explicit binding controls it.
3. Was it called as `obj.method()`? Then `this` is the object used as the call receiver.
4. Was it a plain function call? Then default binding applies: `undefined` in strict mode, global object substitution in sloppy mode.
5. Is it an arrow function? It does not have its own `this`; it reads `this` lexically from the enclosing environment.

This order is a learning model, not a replacement for the spec, but it predicts the real cases you see in frontend work.

## 4. Mental Model

Treat `this` like a hidden first argument supplied by the call form.

```js
user.readName();
// Similar mental model:
// readName.call(user);

const read = user.readName;
read();
// Similar mental model in strict mode:
// readName.call(undefined);
```

When you pass a function value around, you pass the function, not the receiver.

## 5. Call-Site Rules

### Implicit Binding

```js
const cart = {
  total: 42,
  readTotal() {
    return this.total;
  }
};

console.log(cart.readTotal()); // 42
```

The object to the left of the final property access is the receiver.

```js
const app = {
  cart: {
    total: 42,
    readTotal() {
      return this.total;
    }
  }
};

console.log(app.cart.readTotal()); // 42; this is app.cart, not app
```

### Explicit Binding

```js
function readTotal(currency) {
  return `${currency}${this.total}`;
}

console.log(readTotal.call({ total: 42 }, "$")); // "$42"
```

### New Binding

```js
function User(name) {
  this.name = name;
}

const user = new User("Ava");
console.log(user.name); // "Ava"
```

### Default Binding

```js
function showThis() {
  "use strict";
  return this;
}

console.log(showThis()); // undefined
```

## 6. Real Frontend Scenario: Method Passed as Callback

Bug:

```js
const analytics = {
  prefix: "checkout",
  track(eventName) {
    console.log(`${this.prefix}:${eventName}`);
  }
};

["opened", "submitted"].forEach(analytics.track);
```

> [!warning] Callback loses the receiver
> Failure mode: `track` is called by `forEach` as a plain callback. In strict/module code, `this` is `undefined`, so `this.prefix` throws.

Fix with a wrapper:

```js
["opened", "submitted"].forEach((eventName) => {
  analytics.track(eventName);
});
```

Fix with `bind`:

```js
const trackCheckout = analytics.track.bind(analytics);

["opened", "submitted"].forEach(trackCheckout);
```

> [!tip] Wrapper vs bind tradeoff
> Tradeoff: wrappers make the receiver obvious. `bind` is useful when a stable callback reference is needed for add/remove listener or memoization.

## Real-World Use Cases

### Illegal invocation: detached platform methods

You build a tiny DOM helper module and alias the long native names. Native browser methods validate their receiver, so the detached call throws immediately.

```js
const qs = document.querySelector;

qs(".submit-btn"); // TypeError: Illegal invocation
```

The call is a plain function call, so `this` is no longer `document` — and unlike your own strict-mode functions, the C++-backed method rejects the wrong receiver with its own error.

```js
const qs = document.querySelector.bind(document); // works
const qsAlt = (sel) => document.querySelector(sel); // also works
```

See [[05 - this Binding/05 - call apply bind|call apply bind]].

### Toast auto-dismiss timer loses its manager

A notification system schedules each toast to close itself after five seconds. Passing the method straight to `setTimeout` detaches it.

```js
class ToastManager {
  toasts = [];

  dismiss(id) {
    this.toasts = this.toasts.filter((t) => t.id !== id);
  }

  show(toast) {
    this.toasts.push(toast);
    setTimeout(this.dismiss, 5000, toast.id); // this === undefined when it fires
  }
}
```

The timer performs a plain call, so default binding applies — class code is strict, so `this.toasts` throws. Fix with an arrow wrapper: `setTimeout(() => this.dismiss(toast.id), 5000)`, which reads `this` lexically from `show`. See [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]].

### Destructured SDK client method

A class-based API client stores its base URL on the instance. Destructuring the method for convenience severs the receiver — a very common bug when wiring clients into React Query or server actions.

```ts
class ApiClient {
  constructor(private baseUrl: string) {}

  get(path: string) {
    return fetch(`${this.baseUrl}${path}`).then((r) => r.json());
  }
}

const api = new ApiClient("https://api.shop.dev");
const { get } = api;

useQuery({ queryKey: ["orders"], queryFn: () => get("/orders") }); // TypeError
```

Destructuring copies the function value only; the later call is plain, so `this.baseUrl` is gone.

> [!tip]
> SDK authors defend against this by declaring methods as arrow class fields (`get = (path) => ...`), which capture the instance at construction — the reason destructuring `axios` or Supabase clients usually works. See [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]].

## 7. Debugging Checklist

- Find the exact call expression.
- Is the function regular, arrow, bound, method, constructor, or class method?
- If it is `obj.method()`, which object is immediately before the call?
- Was the method extracted into a variable?
- Was it passed as a callback?
- Is the file an ES module or strict mode?
- Is a wrapper preserving `this` with `apply`?
- Would a normal parameter be clearer than relying on `this`?

## 8. Interview Answer

Short answer:

> `this` is a special binding whose value is usually determined by how a regular function is called. Method calls set it to the receiver object, `call`/`apply`/`bind` set it explicitly, `new` sets it to the new object, and plain calls use default binding. Arrow functions use lexical `this`.

Deeper answer:

> In the spec, functions run in execution contexts that can have a `ThisBinding`. For regular calls, call evaluation derives the value from the call form. The common bug is context loss: `const fn = obj.method; fn()` calls the same function without the object reference, so `this` is no longer `obj`.

Production answer:

> When I see a `this` bug, I look for method extraction, callback passing, wrapper functions, and strict/module mode. Fixes include wrapper functions, `bind`, arrow class fields, or refactoring the function to accept explicit parameters.

## 9. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "`this` means the object where the function was defined." | For regular functions, it depends on how the function is called. |
| "Passing `obj.method` keeps `obj`." | It passes only the function value. |
| "The outermost object in `a.b.fn()` is `this`." | The immediate receiver is `b`. |
| "`bind` works on arrow `this`." | Arrows do not have their own `this` to replace. |
| "`this` is always an object." | In strict mode it can be `undefined` or a primitive. |

## 10. Practice

1. Predict the output:

```js
"use strict";

const obj = {
  value: 10,
  getValue() {
    return this.value;
  }
};

const fn = obj.getValue;

console.log(obj.getValue());

try {
  console.log(fn());
} catch (error) {
  console.log(error.name);
}
```

Expected output:

```txt
10
TypeError
```

2. Explain which `this` rule applies to each call:

```js
obj.method();
method.call(obj);
new Constructor();
method();
```

3. Fix a method-passed-as-callback bug with a wrapper and with `bind`.
4. Explain why arrow functions are an exception to call-site `this`.
5. Rewrite a method that does not need `this` into a pure function with explicit parameters.

## Related Notes

- [[05 - this Binding/02 - this in Strict Mode|this in Strict Mode]]
- [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]
- [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]
- [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]
- [[05 - this Binding/07 - React this Examples|React this Examples]]
- [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]
- [[01 - Roadmap|Roadmap]]
