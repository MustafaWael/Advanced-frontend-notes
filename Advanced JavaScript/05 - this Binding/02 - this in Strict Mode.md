---
tags: [javascript, this-binding, this-in-strict-mode]
module: "05 - this Binding"
priority: must-know
status: not-started
---

# this in Strict Mode

## Maturity Target

- Priority: #must-know
- Study time: 60-75 minutes
- Interview signal: you can explain why plain calls produce `undefined` in strict mode but may use `globalThis` in sloppy mode.
- Production signal: you understand why modules, classes, bundlers, and React class methods expose `this` bugs faster.
- Dependencies: [[05 - this Binding/01 - What is this|What is this]], [[10 - Modules/01 - ES Modules|ES Modules]]

## Source Anchors

- [MDN - Strict mode](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode)
- [MDN - this](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this)
- [MDN - Classes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes)
- [ECMAScript 2026 - Function Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-function-environment-records)

## 1. Concept

Strict mode changes default `this` behavior. In sloppy mode, a plain function call may substitute `globalThis` when `this` would be `undefined` or `null`. In strict mode, JavaScript leaves `this` as provided.

```js
function sloppyThis() {
  return this;
}

function strictThis() {
  "use strict";
  return this;
}

console.log(sloppyThis() === globalThis); // true in sloppy script code
console.log(strictThis());                // undefined
```

Most modern frontend code runs as modules or through tooling that effectively puts code in strict mode. Classes are always strict.

## 2. Why It Matters

Strict mode turns silent global bugs into visible failures:

- A method passed as a callback throws instead of writing to `window`.
- A constructor called without `new` throws when assigning `this.name`.
- A class method used as an event handler loses `this` and fails immediately.
- Sloppy scripts can accidentally create or mutate global state.

This is good. Failing fast is safer than mutating the wrong object.

## 3. Official Mechanism

Non-strict functions perform this substitution:

- `null` or `undefined` `this` becomes `globalThis`.
- Primitive `this` values can be boxed into wrapper objects.

Strict functions do not perform that substitution.

```js
function sloppyType() {
  return typeof this;
}

function strictType() {
  "use strict";
  return typeof this;
}

console.log(sloppyType.call(1)); // "object"
console.log(strictType.call(1)); // "number"
```

That detail matters in rare library code, but the most important production rule is simpler: strict plain calls do not rescue you with `globalThis`.

## 4. Script vs Module

Classic script top-level `this` in browsers is usually `window`.

```js
// Classic browser script:
console.log(this === window); // true
```

ES module top-level `this` is `undefined`.

```js
// ES module:
console.log(this); // undefined
```

Even when top-level `this` differs, regular function calls still follow their own strict/sloppy rules.

Production consequence: examples copied from old script tutorials often behave differently in modern bundler/module environments.

## 5. Class Bodies Are Strict

Class code runs in strict mode.

```js
class Counter {
  count = 0;

  increment() {
    this.count += 1;
  }
}

const counter = new Counter();
const increment = counter.increment;

try {
  increment();
} catch (error) {
  console.log(error.name); // "TypeError"
}
```

The method is called as a plain function. Since class methods are strict, `this` is `undefined`.

Fix:

```js
const increment = counter.increment.bind(counter);
increment();

console.log(counter.count); // 1
```

## 6. Real Frontend Scenario: Legacy Script vs Module

Bug in legacy script:

```js
function setToken(token) {
  this.authToken = token;
}

setToken("abc");

console.log(globalThis.authToken); // "abc" in sloppy script code
```

This accidentally writes to global state. If the same function becomes strict/module code:

```js
function setToken(token) {
  "use strict";
  this.authToken = token;
}

try {
  setToken("abc");
} catch (error) {
  console.log(error.name); // "TypeError"
}
```

Fix by making ownership explicit:

```js
function setToken(session, token) {
  session.authToken = token;
}

const session = {};
setToken(session, "abc");

console.log(session.authToken); // "abc"
```

> [!tip] Tradeoff
> explicit parameters are less magical and easier to test.

## 7. Real Frontend Scenario: Event Listeners

DOM event listeners may call regular functions with `this` set to the element, but arrow functions do not receive that dynamic `this`.

```js
button.addEventListener("click", function handleClick(event) {
  console.log(this === event.currentTarget); // true in normal DOM listener calls
});
```

With an arrow:

```js
button.addEventListener("click", (event) => {
  console.log(this); // lexical this, not the button
  console.log(event.currentTarget); // use this instead
});
```

Production habit: prefer `event.currentTarget` in modern UI code. It is explicit and does not depend on dynamic `this`.

## Real-World Use Cases

### Vendor snippet pasted into a module

Analytics and tag-manager snippets from vendor docs were written for classic `<script>` tags, where top-level `this` is `window`. Pasted into a Next.js or Vite module, the same lines throw.

```js
// Vendor snippet, assumes classic script (this === window):
this.dataLayer = this.dataLayer || [];
this.dataLayer.push({ event: "page_view" });
// In an ES module: TypeError — top-level `this` is undefined
```

Fails because ES modules set top-level `this` to `undefined` and run in strict mode — no `globalThis` substitution rescues the property write. See [[10 - Modules/01 - ES Modules|ES Modules]].

> [!tip]
> Rewrite to `globalThis.dataLayer` — it names the global explicitly and, unlike `window`, does not crash during SSR on the server.

### Array callback that reads `this` — silent in scripts, loud in modules

`map`/`forEach` call their callback with `this` as `undefined` unless you pass a `thisArg`. In a sloppy script that becomes `globalThis` and produces garbage data; after migrating the file to a module it throws — the bug was always there, strict mode just surfaces it.

```js
const cart = {
  taxRate: 0.2,
  withTax(prices) {
    return prices.map(function (price) {
      return price * (1 + this.taxRate); // sloppy: NaN (this = globalThis); module: TypeError
    });
  }
};
```

Fails because default binding applies to the callback's plain call — strict code keeps `this` as `undefined` instead of substituting the global.

> [!tip]
> Three fixes, in order of preference: an arrow callback (lexical `this` from `withTax`), the often-forgotten `thisArg` — `prices.map(function (p) { ... }, this)` — or an explicit parameter. See [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]].

### Constructor called without `new`

A legacy factory is invoked without `new` somewhere deep in the codebase. In sloppy script code it silently pollutes the global; in strict/module code it fails at the call site.

```js
function Session(userId) {
  this.userId = userId;
}

const session = Session("u_42");
// Sloppy script: globalThis.userId = "u_42", session === undefined — data leaks globally
// Strict/module: TypeError — this is undefined, assignment throws immediately
```

Strict mode turns a hidden shared-state bug into a stack trace pointing at the exact call. Classes go one step further and throw without `new` in all modes — one reason to migrate. See [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]].

## 8. Debugging Checklist

- Is the file a module?
- Is the function body strict?
- Is the function a class method?
- Was the method passed as a callback?
- Is a sloppy script writing to `globalThis` by accident?
- Does the callback API provide a `thisArg`?
- Would explicit parameters avoid the issue?

## 9. Interview Answer

Short answer:

> In strict mode, a plain function call has `this === undefined`. In sloppy mode, JavaScript may substitute `globalThis`.

Deeper answer:

> Strict mode disables this substitution. If a function is called with `this` as `undefined` or `null`, it stays that way. In sloppy mode, those values become the global object, and primitives can be boxed. ES modules and class bodies use strict semantics, which is why context-loss bugs often throw in modern apps.

Production answer:

> Strict mode is helpful because it exposes context loss instead of silently mutating globals. When old code depends on sloppy `this`, I refactor to explicit objects, `bind`, or wrapper callbacks.

## 10. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Strict mode changes how method calls work." | Method receiver binding still works; plain/default calls change most visibly. |
| "Top-level module `this` is `globalThis`." | Top-level `this` in ES modules is `undefined`. |
| "Class methods auto-bind." | Class methods are strict but not automatically bound. |
| "Sloppy global `this` behavior is harmless." | It can create hidden shared state. |
| "Arrows fix strict mode." | Arrows use lexical `this`; they do not create dynamic receiver binding. |

## 11. Practice

1. Predict the output:

```js
function sloppy() {
  return this === globalThis;
}

function strict() {
  "use strict";
  return this;
}

console.log(sloppy());
console.log(strict());
```

Expected in sloppy script code:

```txt
true
undefined
```

2. Explain why class methods throw when extracted and called.
3. Convert a sloppy function that writes to `this` into one that accepts an explicit object.
4. Explain top-level `this` in a browser script vs ES module.
5. Use `event.currentTarget` instead of listener `this`.

## Related Notes

- [[05 - this Binding/01 - What is this|What is this]]
- [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]
- [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]
- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[01 - Roadmap|Roadmap]]
