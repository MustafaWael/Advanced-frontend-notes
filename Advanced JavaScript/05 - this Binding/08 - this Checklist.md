---
tags: [javascript, this-binding, this-checklist]
module: "05 - this Binding"
priority: must-know
status: not-started
---

# this Checklist

Use this checklist as an active test. Do not mark an item complete because you recognize the syntax. Mark it complete when you can identify the call site, predict the output, and choose the right production fix.

## Source Anchors

- [MDN - this](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this)
- [MDN - Strict mode](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Strict_mode)
- [MDN - Arrow functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions)
- [MDN - Function.prototype.bind](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind)
- [React - Component](https://react.dev/reference/react/Component)

## Core Understanding

- [ ] I can define `this` as a special binding, not an ordinary variable.
- [ ] I can explain why regular function `this` depends on the call site.
- [ ] I can identify implicit, explicit, new, default, and lexical arrow binding.
- [ ] I can explain why method extraction loses the receiver.
- [ ] I can explain why the immediate receiver matters in `a.b.fn()`.
- [ ] I can explain why arrows are an exception to the call-site rule.

## Strict Mode and Modules

- [ ] I can explain sloppy default binding to `globalThis`.
- [ ] I can explain strict default binding to `undefined`.
- [ ] I can explain top-level `this` in browser scripts vs ES modules.
- [ ] I can explain why class bodies are strict.
- [ ] I can spot old code that accidentally writes to globals through sloppy `this`.

## Objects and Functions

- [ ] I can fix `const fn = obj.method; fn()` bugs.
- [ ] I can fix `items.map(obj.method)` bugs.
- [ ] I can fix nested regular functions that lose outer method `this`.
- [ ] I can choose between wrapper functions, `bind`, arrows, and explicit parameters.
- [ ] I can write a wrapper that preserves `this`, arguments, return value, and errors.

## Arrow Functions

- [ ] I can explain lexical `this`.
- [ ] I can explain why `call`, `apply`, and `bind` cannot change arrow `this`.
- [ ] I can avoid arrow object methods that need dynamic receivers.
- [ ] I can use arrows inside methods when preserving outer `this` is intended.
- [ ] I can store arrow listener references for cleanup.
- [ ] I can compare class field arrows with prototype methods.

## call apply bind

- [ ] I can compare `call`, `apply`, and `bind`.
- [ ] I can use `call` for immediate explicit binding.
- [ ] I can use `apply` with an argument array.
- [ ] I can use `bind` for later callbacks and partial arguments.
- [ ] I can explain why binding twice does not replace the first bound `this`.
- [ ] I can avoid inline `bind` when cleanup needs the same function reference.

## Constructors and Classes

- [ ] I can explain what `new` does.
- [ ] I can explain constructor object-return override.
- [ ] I can explain why classes must be called with `new`.
- [ ] I can explain why derived constructors need `super()` before `this`.
- [ ] I can explain static `this` vs instance `this`.
- [ ] I can choose prototype methods or arrow fields based on memory/callback tradeoffs.

## React

- [ ] I can explain why class component methods are not auto-bound.
- [ ] I can fix class handler `this` bugs with constructor binding.
- [ ] I can fix class handler `this` bugs with arrow class fields.
- [ ] I can explain inline arrow wrappers in render and their identity tradeoff.
- [ ] I can explain that function components do not have instance `this`.
- [ ] I can distinguish class `this` bugs from hook stale-closure bugs.

## Code Snippets to Trace

### Snippet 1: Method Extraction

```js
"use strict";

const obj = {
  value: 10,
  read() {
    return this.value;
  }
};

const read = obj.read;

console.log(obj.read());

try {
  console.log(read());
} catch (error) {
  console.log(error.name);
}
```

Expected output:

```txt
10
TypeError
```

### Snippet 2: Immediate Receiver

```js
const app = {
  value: "app",
  feature: {
    value: "feature",
    read() {
      return this.value;
    }
  }
};

console.log(app.feature.read());
```

Expected output:

```txt
feature
```

### Snippet 3: Arrow Lexical this

```js
const obj = {
  value: 1,
  method() {
    const arrow = () => this.value;
    return arrow;
  }
};

const arrow = obj.method();

console.log(arrow());
console.log(arrow.call({ value: 2 }));
```

Expected output:

```txt
1
1
```

### Snippet 4: Bound Function

```js
function read() {
  return this.value;
}

const bound = read.bind({ value: "first" });
const rebound = bound.bind({ value: "second" });

console.log(rebound());
```

Expected output:

```txt
first
```

### Snippet 5: Constructor Return

```js
function A() {
  this.value = 1;
  return { value: 2 };
}

function B() {
  this.value = 1;
  return 2;
}

console.log(new A().value);
console.log(new B().value);
```

Expected output:

```txt
2
1
```

### Snippet 6: Wrapper Preserving this

```js
function withLog(fn) {
  return function wrapped(...args) {
    console.log("calling");
    return fn.apply(this, args);
  };
}

const cart = {
  taxRate: 0.1,
  total(subtotal) {
    return subtotal + subtotal * this.taxRate;
  }
};

console.log(withLog(cart.total).call(cart, 100));
```

Expected output:

```txt
calling
110
```

## Production Debugging Drills

1. Find every `onClick={this.method}` in a class component and verify binding.
2. Search for `.bind(this)` inside render methods and decide if it creates unnecessary identity churn.
3. Review event listeners and confirm cleanup uses the same function reference.
4. Review utility wrappers and confirm they use `apply(this, args)` when needed.
5. Replace a method that does not need dynamic dispatch with an explicit-parameter pure function.
6. Convert a class component handler to a function component handler and explain what replaced `this`.
7. Create a strict-mode reproduction for a method extraction bug.

## Interview Quick Answers

| Question | Strong short answer |
| --- | --- |
| What is `this`? | A special binding usually determined by how a regular function is called. |
| What is implicit binding? | `obj.method()` sets `this` to `obj`. |
| What is default binding? | Plain function call; `undefined` in strict mode, global substitution in sloppy mode. |
| What is explicit binding? | `call`, `apply`, or `bind` supplies `this`. |
| What is new binding? | `new Fn()` sets `this` to the new instance. |
| What is lexical `this`? | Arrow functions read `this` from the surrounding scope. |
| Why does method extraction fail? | The function is called without its receiver. |
| What does `bind` return? | A new function with fixed `this` and optional preset args. |
| Do class methods auto-bind? | No. Bind them, use arrow fields, or wrap calls. |
| Do hooks use `this`? | No. Function components use closures, state, refs, and effects. |

## Mastery Criteria

- [ ] I can solve every snippet above without running it.
- [ ] I can explain `this` using call-site language, not vague object ownership.
- [ ] I can name one real bug for every binding rule.
- [ ] I can fix context loss while preserving cleanup and function identity.
- [ ] I can explain the difference between class `this` bugs and hook stale closures.
- [ ] I can mention at least one production tradeoff for `bind`, arrow fields, and inline wrappers.

## Related Notes

- [[05 - this Binding/01 - What is this|What is this]]
- [[05 - this Binding/02 - this in Strict Mode|this in Strict Mode]]
- [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]
- [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]
- [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]
- [[05 - this Binding/07 - React this Examples|React this Examples]]
- [[16 - Code Output Questions/03 - this Output Questions|this Output Questions]]
- [[01 - Roadmap|Roadmap]]
