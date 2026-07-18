---
tags: [javascript, functions, functions-checklist]
module: "04 - Functions Deep Dive"
priority: must-know
status: not-started
---

# Functions Checklist

Use this checklist as an active test. Mark items complete only when you can explain the mechanism, predict output, and choose the production-safe pattern.

## Source Anchors

- [MDN - Functions guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions)
- [MDN - Arrow functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions)
- [MDN - Rest parameters](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/rest_parameters)
- [React - Components and Hooks must be pure](https://react.dev/reference/rules/components-and-hooks-must-be-pure)
- [MDN - Debounce](https://developer.mozilla.org/en-US/docs/Glossary/Debounce)
- [MDN - Throttle](https://developer.mozilla.org/en-US/docs/Glossary/Throttle)

## Function Forms

- [ ] I can explain function declarations vs function expressions.
- [ ] I can predict which forms are available before their source line.
- [ ] I can explain why function expressions assigned to `const` are in TDZ before initialization.
- [ ] I can use named function expressions for debugging or recursion.
- [ ] I can avoid conditional function declarations as an architecture pattern.
- [ ] I can choose declarations for stable helpers and expressions for function values.

## Arrow Functions

- [ ] I can explain lexical `this`.
- [ ] I can explain why arrows do not have their own `arguments`.
- [ ] I can explain why arrows cannot be constructors.
- [ ] I can show why `bind` cannot replace arrow `this`.
- [ ] I can avoid arrows for object/prototype methods that need a receiver.
- [ ] I can store listener references when cleanup is required.
- [ ] I can identify when inline arrows create unnecessary identity churn in React.

## Higher-Order Functions and Callbacks

- [ ] I can define first-class functions, HOFs, and callbacks.
- [ ] I can distinguish synchronous callbacks from asynchronous callbacks.
- [ ] I can explain callback timing based on the API, not the syntax.
- [ ] I can avoid `forEach(async ...)` when I need to await completion.
- [ ] I can preserve `this`, arguments, return values, and errors in wrappers.
- [ ] I can use HOFs for logging, retry, auth, and middleware without hiding control flow.

## Purity and IIFE

- [ ] I can define a pure function.
- [ ] I can identify side effects: network, DOM, storage, logs, timers, mutation of external values.
- [ ] I can explain why local mutation can still be safe.
- [ ] I can explain why React render code must be pure/idempotent.
- [ ] I can recognize IIFEs and explain why they were used before modules.
- [ ] I can avoid import-time side effects unless they are deliberate and documented.

## Parameters, Arguments, Rest, Defaults

- [ ] I can distinguish parameters from arguments.
- [ ] I can explain rest parameters vs spread syntax.
- [ ] I can replace `arguments` with rest parameters.
- [ ] I can explain default parameters and `undefined` vs `null`.
- [ ] I can explain default parameter evaluation order.
- [ ] I can design options-object APIs for optional/evolving arguments.
- [ ] I can avoid overusing `fn.length` for runtime behavior.

## Currying and Partial Application

- [ ] I can distinguish currying from partial application.
- [ ] I can explain closures as the mechanism.
- [ ] I can write a curried validator.
- [ ] I can write a `partial` helper.
- [ ] I can explain `bind` as partial application plus `this` binding.
- [ ] I can identify when currying hurts readability.
- [ ] I can reason about function identity in curried React handlers.

## Debounce and Throttle

- [ ] I can explain debounce as waiting for quiet.
- [ ] I can explain throttle as steady rate limiting.
- [ ] I can implement debounce with preserved args and cancellation.
- [ ] I can implement throttle and describe leading/trailing behavior.
- [ ] I can choose debounce, throttle, or `requestAnimationFrame` for the right UI problem.
- [ ] I can combine debounced search with cancellation or stale-response protection.
- [ ] I can clean up timers on unmount.

## Code Snippets to Trace

### Snippet 1: Declaration vs Expression

```js
console.log(declared());

try {
  console.log(expressed());
} catch (error) {
  console.log(error.name);
}

function declared() {
  return "declared";
}

const expressed = function () {
  return "expressed";
};
```

Expected output:

```txt
declared
ReferenceError
```

### Snippet 2: Arrow `this`

```js
const user = {
  name: "Ava",
  regular() {
    return this.name;
  },
  arrow: () => this?.name
};

console.log(user.regular());
console.log(user.arrow());
```

Expected output in an ES module:

```txt
Ava
undefined
```

### Snippet 3: Sync vs Async Callback

```js
console.log("A");

[1, 2].forEach((number) => console.log(number));

setTimeout(() => console.log("timer"), 0);

console.log("B");
```

Expected output:

```txt
A
1
2
B
timer
```

### Snippet 4: Default Parameters

```js
function range(start = 0, end = start + 10) {
  return [start, end];
}

console.log(range());
console.log(range(5));
console.log(range(undefined, 3));
console.log(range(null));
```

Expected output:

```txt
[0, 10]
[5, 15]
[0, 3]
[null, 10]
```

### Snippet 5: Wrapper Losing Arguments

```js
function withLog(fn) {
  return function wrapped() {
    console.log("calling");
    return fn();
  };
}

const add = (a, b) => a + b;

console.log(withLog(add)(2, 3));
```

Expected output:

```txt
calling
NaN
```

Fix:

```js
function withLog(fn) {
  return function wrapped(...args) {
    console.log("calling");
    return fn(...args);
  };
}
```

### Snippet 6: Async `forEach`

```js
async function run(items) {
  items.forEach(async (item) => {
    await save(item);
  });

  console.log("done");
}
```

Expected behavior: `"done"` logs before the saves finish. Use `for...of` with `await` for sequential work or `Promise.all(items.map(save))` for parallel work.

## Production Review Questions

- Does this function have a clear input/output contract?
- Does it hide a side effect behind a pure-looking name?
- Does a wrapper preserve arguments, `this`, return value, and thrown errors?
- Does a callback run now or later?
- Does a callback close over render-owned values?
- Does the function identity matter for memoization or cleanup?
- Are optional parameters named clearly?
- Is a debounced/throttled function cancelled during cleanup?
- Is a module-level IIFE starting work at import time?

## Interview Quick Answers

| Question | Strong short answer |
| --- | --- |
| Declaration vs expression? | Declarations are initialized during declaration instantiation; expressions produce values when evaluated. |
| What is an arrow function? | A function expression with lexical `this`, no own `arguments`, and no constructor behavior. |
| What is a HOF? | A function that takes or returns another function. |
| Is every callback async? | No. The API decides whether and when it runs. |
| What is a pure function? | Same inputs, same output, no observable side effects. |
| What is an IIFE? | A function expression invoked immediately, often to create private scope or run setup. |
| Rest vs spread? | Rest gathers arguments; spread expands values at a call site or literal. |
| Currying vs partial application? | Currying chains one-argument functions; partial application pre-fills some arguments. |
| Debounce vs throttle? | Debounce waits for calls to stop; throttle limits calls over time. |

## Mastery Criteria

- [ ] I can solve each snippet without running it.
- [ ] I can give a 30-second interview answer for each note.
- [ ] I can connect each concept to React or browser event code.
- [ ] I can write failing and fixed examples for wrapper arguments, arrow `this`, async `forEach`, and debounced search.
- [ ] I can explain one production tradeoff for each pattern.

## Related Notes

- [[04 - Functions Deep Dive/01 - Function Declarations vs Expressions|Function Declarations vs Expressions]]
- [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]
- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions and IIFE]]
- [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]]
- [[04 - Functions Deep Dive/06 - Currying and Partial Application|Currying and Partial Application]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]]
- [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]]
- [[01 - Roadmap|Roadmap]]
