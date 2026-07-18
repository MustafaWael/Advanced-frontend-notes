---
tags: [javascript, scope, scope-checklist]
module: "03 - Scope and Variables"
priority: must-know
status: not-started
---

# Scope Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, predict, debug, and refactor the code without looking.

## Source Anchors

- [ECMAScript 2026 - Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-environment-records)
- [MDN - Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [MDN - Hoisting](https://developer.mozilla.org/en-US/docs/Glossary/Hoisting)
- [React - Removing Effect Dependencies](https://react.dev/learn/removing-effect-dependencies)

## Scope Fundamentals

- [ ] I can define scope as identifier resolution, not property lookup.
- [ ] I can explain global, module, function, block, catch, and class scope.
- [ ] I can explain why JavaScript lexical scope depends on where code is written.
- [ ] I can explain why a function does not read local variables from its caller unless the caller is in its lexical chain.
- [ ] I can describe how script top-level scope differs from ES module top-level scope.
- [ ] I can name one safe and one dangerous use of module scope.

## Lexical Environment

- [ ] I can explain Environment Records and outer environment links.
- [ ] I can trace identifier lookup from inner to outer scope.
- [ ] I can explain the difference between a binding and the value stored in the binding.
- [ ] I can explain why React creates new render-owned bindings on every render.
- [ ] I can debug a callback by asking when it was created and when it runs.
- [ ] I can separate ECMAScript behavior from React, browser, Node.js, or Next.js behavior.

## var let const

- [ ] I can explain `var` function/global/module scope.
- [ ] I can explain `let` and `const` block scope.
- [ ] I can explain why `var` early reads produce `undefined`.
- [ ] I can explain why `let`, `const`, and `class` early reads throw `ReferenceError`.
- [ ] I can explain why `const` does not freeze objects.
- [ ] I can fix a loop closure bug with `let` and with a factory function.
- [ ] I can choose `const` vs `let` based on reassignment, not habit.

## Hoisting and TDZ

- [ ] I can explain hoisting as declaration preparation, not physical code movement.
- [ ] I can compare function declarations, function expressions, `var`, `let`, `const`, `class`, and imports.
- [ ] I can explain why `typeof` can still throw inside TDZ.
- [ ] I can identify lexical shadowing that causes TDZ errors.
- [ ] I can diagnose a circular import TDZ error.
- [ ] I can refactor top-level module work into a function or shared dependency module.

## Closures

- [ ] I can define a closure as a function plus access to its creation environment.
- [ ] I can explain why closures capture bindings, not snapshots.
- [ ] I can explain why separate function calls create separate bindings.
- [ ] I can use closures for private state, event handlers, memoization, debounce, and factories.
- [ ] I can explain when closure state is worse than explicit object/state ownership.
- [ ] I can identify closure-based memory retention.

## Closure Bugs

- [ ] I can solve the classic `var` loop output question.
- [ ] I can explain stale closures in React effects and callbacks.
- [ ] I can choose between dependency arrays, functional updaters, refs, and argument passing.
- [ ] I can clean up event listeners using the same function identity.
- [ ] I can avoid stale async responses with abort, ignore flags, or request ids.
- [ ] I can explain why suppressing React dependency lint rules is risky.

## Code Snippets to Trace

### Snippet 1: Lexical Scope

```js
const value = "global";

function read() {
  return value;
}

function run() {
  const value = "local";
  return read();
}

console.log(run());
```

Expected output:

```txt
global
```

Reason: `read` resolves `value` from where `read` was created, not from `run`'s local scope.

### Snippet 2: var vs let

```js
const varFns = [];
const letFns = [];

for (var i = 0; i < 3; i += 1) {
  varFns.push(() => i);
}

for (let j = 0; j < 3; j += 1) {
  letFns.push(() => j);
}

console.log(varFns.map((fn) => fn()).join(","));
console.log(letFns.map((fn) => fn()).join(","));
```

Expected output:

```txt
3,3,3
0,1,2
```

Reason: `var` gives all callbacks one binding; `let` gives each loop iteration its own binding.

### Snippet 3: TDZ Shadowing

```js
const status = "outer";

{
  try {
    console.log(status);
  } catch (error) {
    console.log(error.name);
  }

  const status = "inner";
  console.log(status);
}
```

Expected output:

```txt
ReferenceError
inner
```

Reason: the inner `const status` shadows the outer one for the whole block, but is uninitialized until its declaration runs.

### Snippet 4: Closure Binding

```js
function createStore() {
  let value = 0;

  return {
    read() {
      return value;
    },
    write(nextValue) {
      value = nextValue;
    }
  };
}

const store = createStore();
console.log(store.read());
store.write(5);
console.log(store.read());
```

Expected output:

```txt
0
5
```

Reason: both methods close over the same `value` binding.

### Snippet 5: Function Declaration vs Expression

```js
console.log(declared());

try {
  console.log(expressed());
} catch (error) {
  console.log(error.name);
}

function declared() {
  return "ok";
}

const expressed = () => "later";
```

Expected output:

```txt
ok
ReferenceError
```

Reason: function declarations are initialized before execution; the `const` binding for `expressed` is in TDZ until its declaration executes.

## Production Debugging Drills

1. Find a React effect with `[]`; list every prop, state value, and component-local function it reads.
2. Create a slow-network reproduction for a fetch effect that changes `userId` quickly.
3. Add logs showing when a callback is created and when it runs.
4. Inspect a module with top-level mutable variables and decide whether any value is user/request-specific.
5. Replace a stale debounced callback by passing the changing value as an argument.
6. Refactor a circular import by moving shared constants/helpers to a third module.
7. Check that event listener cleanup removes the exact same function identity.

## Interview Quick Answers

| Question | Strong short answer |
| --- | --- |
| What is scope? | Where an identifier can be resolved; JavaScript mainly uses lexical scope. |
| What is a lexical environment? | The spec model of bindings plus an outer link used for identifier lookup. |
| What is hoisting? | Declaration preparation before execution; not literal source-code movement. |
| What is TDZ? | The period where a lexical binding exists but cannot be read before initialization. |
| Difference between `var`, `let`, and `const`? | `var` is function/global scoped and early-initialized to `undefined`; `let` and `const` are block-scoped and TDZ-protected; `const` cannot be rebound. |
| What is a closure? | A function with access to the lexical environment where it was created. |
| Do closures capture values or bindings? | Bindings. They can observe later changes to the same binding. |
| What is a stale closure in React? | A callback created in an old render reads props/state from that old render. |
| How do you fix stale closures? | Dependencies, functional updaters, refs, argument passing, or cancellation depending on ownership. |
| Why can circular imports fail? | A module can read another module's lexical binding before it has been initialized. |

## Mastery Criteria

You are ready to move on when you can:

- [ ] Explain every note in this folder in plain English.
- [ ] Use at least one accurate spec term without overcomplicating the answer.
- [ ] Solve the snippets above without running them.
- [ ] Write one failing and one fixed example for each main topic.
- [ ] Connect each concept to a real frontend bug.
- [ ] Explain why the fix works, not just what code to type.
- [ ] Mention one tradeoff for each production fix.

## Related Notes

- [[03 - Scope and Variables/01 - Scope Types|Scope Types]]
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/03 - var let const|var let const]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]]
- [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]]
- [[01 - Roadmap|Roadmap]]
