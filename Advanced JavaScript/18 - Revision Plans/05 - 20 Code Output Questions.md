---
tags: [javascript, revision, interview, 20-code-output-questions]
module: "18 - Revision Plans"
priority: must-know
status: not-started
---

# 20 Code Output Questions

Use these as execution tracing drills. Predict the output before reading the answer. Then explain the exact mechanism: binding creation, TDZ, call site, prototype lookup, shallow copy, promise job, task, identity comparison, or cleanup behavior.

## How To Answer

For every question:

- Say the output first.
- Name the mechanism.
- Explain what changes in strict mode, modules, browsers, Node, React, or Next.js if relevant.
- Connect the rule to a real frontend bug.

## Scope and Hoisting

### Question 1: declaration vs expression

```js
console.log(typeof declared);
console.log(typeof expressed);

function declared() {}

var expressed = function () {};
```

Answer:

```txt
function
undefined
```

Why:

Function declarations are initialized during environment setup. The `var` binding also exists during setup, but it starts as `undefined` until assignment runs.

Production angle:

This is why refactoring a helper from a declaration to a `const` or `var` expression can change when it is safe to call.

Related note: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

### Question 2: temporal dead zone

```js
{
  try {
    console.log(count);
  } catch (error) {
    console.log(error.name);
  }

  let count = 1;
  console.log(count);
}
```

Answer:

```txt
ReferenceError
1
```

Why:

The `let` binding exists in the block, but it is uninitialized until the declaration runs. Reading it during the TDZ throws `ReferenceError`.

Production angle:

TDZ bugs can appear when a module or branch reads configuration before initialization, especially after circular imports or refactors.

Related note: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

### Question 3: `var` loop vs `let` loop

```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log("var", i), 0);
}

for (let j = 0; j < 3; j++) {
  setTimeout(() => console.log("let", j), 0);
}
```

Answer:

```txt
var 3
var 3
var 3
let 0
let 1
let 2
```

Why:

All `var` callbacks close over the same function/global-scoped `i` binding, which is `3` after the loop. Each `let` iteration gets a fresh per-iteration binding.

Production angle:

This is the classic version of stale callback bugs in event handlers, timers, and generated UI actions.

Related note: [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]

### Question 4: shadowing creates a TDZ

```js
const value = "global";

function read() {
  try {
    console.log(value);
  } catch (error) {
    console.log(error.name);
  }

  const value = "local";
  console.log(value);
}

read();
```

Answer:

```txt
ReferenceError
local
```

Why:

The local `const value` shadows the outer `value` for the whole function block. Before the local declaration initializes, reads hit the local TDZ instead of falling back to the global binding.

Production angle:

Shadowing can make a seemingly safe read fail after a refactor adds a local variable with the same name.

Related note: [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]

## Closures

### Question 5: independent closure state

```js
function createCounter() {
  let count = 0;

  return function increment() {
    count += 1;
    return count;
  };
}

const a = createCounter();
const b = createCounter();

console.log(a());
console.log(a());
console.log(b());
```

Answer:

```txt
1
2
1
```

Why:

Each call to `createCounter` creates a separate lexical environment. Each returned function closes over its own `count` binding.

Production angle:

This is the same mechanism behind factory functions, event handler state, memoized helpers, and hook closures.

Related note: [[03 - Scope and Variables/05 - Closures|Closures]]

### Question 6: stale timer closure

```js
let count = 0;

function scheduleLog() {
  const captured = count;

  setTimeout(() => {
    console.log(captured, count);
  }, 0);
}

scheduleLog();
count = 1;
```

Answer:

```txt
0 1
```

Why:

`captured` stores the value at scheduling time. The callback also reads the current outer `count` binding, which has changed by the time the timer runs.

Production angle:

In React, a timer can close over old render values. Fix by using functional updates, dependencies, refs, or moving the logic into the current event/effect.

Related note: [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

### Question 7: IIFE loop capture

```js
const handlers = [];

for (var i = 0; i < 3; i++) {
  handlers.push(
    ((index) => {
      return () => index;
    })(i)
  );
}

console.log(handlers.map((handler) => handler()).join(","));
```

Answer:

```txt
0,1,2
```

Why:

The IIFE creates a new `index` parameter binding for each iteration. Each handler closes over a different binding.

Production angle:

Modern code usually uses `let` for this, but the pattern teaches the closure mechanism behind stable callback values.

Related note: [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions and IIFE]]

## `this` Binding

### Question 8: extracted method in strict mode

```js
"use strict";

const user = {
  id: 7,
  read() {
    return this.id;
  },
};

const read = user.read;

console.log(user.read());

try {
  console.log(read());
} catch (error) {
  console.log(error.name);
}
```

Answer:

```txt
7
TypeError
```

Why:

`user.read()` calls the function with `user` as receiver. `read()` is a plain function call; in strict mode, default `this` is `undefined`, so reading `this.id` throws.

Production angle:

Passing methods as callbacks can lose the receiver. Use a wrapper, `.bind`, or refactor to a function that receives explicit data.

Related note: [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]

### Question 9: arrow `this`

```js
"use strict";

const user = {
  id: 1,
  regular() {
    return this.id;
  },
  arrow: () => this?.id,
};

console.log(user.regular());
console.log(user.arrow());
```

Answer:

```txt
1
undefined
```

Why:

The regular method receives `user` as `this`. The arrow function does not have its own `this`; it uses lexical `this` from the surrounding module/script scope, not `user`.

Production angle:

Do not use arrow functions as object methods when the method needs the object as receiver.

Related note: [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]

### Question 10: bound function

```js
const view = { prefix: "#" };

function label(id) {
  return this.prefix + id;
}

const bound = label.bind(view, 42);

console.log(bound());
console.log(bound.call({ prefix: "!" }, 99));
```

Answer:

```txt
#42
#42
```

Why:

`.bind` fixes `this` and pre-applies `42` as the first argument. Later `.call` cannot replace the bound `this` or the already-bound argument.

Production angle:

Bound callbacks are predictable, but creating them repeatedly can affect referential equality in React.

Related note: [[05 - this Binding/05 - call apply bind|call apply bind]]

## Objects, Prototypes, and Arrays

### Question 11: own vs inherited property

```js
const parent = { role: "admin" };
const child = Object.create(parent);

child.name = "Mina";

console.log(child.role);
console.log(Object.hasOwn(child, "role"));
console.log("role" in child);
```

Answer:

```txt
admin
false
true
```

Why:

`role` is found through prototype lookup. It is not an own property, but the `in` operator checks the whole prototype chain.

Production angle:

Use own-property checks when merging or validating object input, especially for user-controlled data.

Related note: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]

### Question 12: class methods and enumerability

```js
class User {
  read() {
    return "ok";
  }
}

const user = new User();

console.log(typeof user.read);
console.log(Object.keys(user).length);
console.log(Object.keys(User.prototype).length);
```

Answer:

```txt
function
0
0
```

Why:

The method is on `User.prototype`, not copied onto each instance. Class prototype methods are non-enumerable, so `Object.keys(User.prototype)` does not list `read`.

Production angle:

Prototype methods save memory compared with creating a new method per instance, but they depend on correct `this` binding when passed around.

Related note: [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]

### Question 13: shallow copy

```js
const original = {
  profile: {
    name: "Mina",
  },
};

const copy = { ...original };
copy.profile.name = "Sara";

console.log(original.profile.name);
console.log(copy === original);
console.log(copy.profile === original.profile);
```

Answer:

```txt
Sara
false
true
```

Why:

The outer object is new, but the nested `profile` reference is shared.

Production angle:

React state updates must copy every level that changes, not only the outer container.

Related note: [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]

### Question 14: `map` vs `forEach`

```js
const numbers = [1, 2, 3];

const mapped = numbers.map((number) => number * 2);
const each = numbers.forEach((number) => number * 2);

console.log(mapped.join(","));
console.log(each);
```

Answer:

```txt
2,4,6
undefined
```

Why:

`map` builds a new array from callback return values. `forEach` is for side effects and returns `undefined`.

Production angle:

Use the method that communicates intent. Do not use `forEach` when you need a transformed result.

Related note: [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]

### Question 15: mutating `sort`

```js
const numbers = [3, 1, 2];
const sorted = numbers.sort((a, b) => a - b);

console.log(numbers.join(","));
console.log(sorted === numbers);
```

Answer:

```txt
1,2,3
true
```

Why:

`sort` mutates the original array and returns the same array reference.

Production angle:

Sorting props, state, or cached data in place can corrupt other UI that shares the same array.

Related note: [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]

### Question 16: `Set` and iteration

```js
const tags = new Set(["react", "react", "next"]);

console.log([...tags].join(","));

const [first] = tags;
console.log(first);
```

Answer:

```txt
react,next
react
```

Why:

`Set` stores unique values and preserves insertion order. It is iterable, so spread and destructuring consume its iterator.

Production angle:

Use `Set` for uniqueness, but convert to an array when rendering lists that need array methods or stable mapping.

Related note: [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]

## Async and Event Loop

### Question 17: promise before timer

```js
console.log("A");

setTimeout(() => console.log("B"), 0);

Promise.resolve().then(() => console.log("C"));

console.log("D");
```

Answer:

```txt
A
D
C
B
```

Why:

Synchronous logs run first. The promise reaction runs as a microtask after the current task. The timer callback runs in a later task.

Production angle:

Promise callbacks do not interrupt synchronous code, but they normally run before timer callbacks scheduled from the same turn.

Related note: [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

### Question 18: `await` continuation order

```js
async function run() {
  console.log("B");
  await null;
  console.log("D");
}

console.log("A");
run();
Promise.resolve().then(() => console.log("C"));
console.log("E");
```

Answer:

```txt
A
B
E
D
C
```

Why:

`run()` logs `B` synchronously, then `await null` schedules the async function continuation as a promise job. That continuation is queued before the later `.then` callback for `C`.

Production angle:

`await` creates an async boundary even for already-available values. This can affect loading state timing and tests.

Related note: [[08 - Async JavaScript/04 - Async Await|Async Await]]

### Question 19: `all` vs `allSettled`

```js
async function load() {
  try {
    await Promise.all([
      Promise.resolve("user"),
      Promise.reject(new Error("posts failed")),
    ]);
  } catch (error) {
    console.log(error.message);
  }

  const results = await Promise.allSettled([
    Promise.resolve("user"),
    Promise.reject(new Error("posts failed")),
  ]);

  console.log(results.map((result) => result.status).join(","));
}

load();
```

Answer:

```txt
posts failed
fulfilled,rejected
```

Why:

`Promise.all` rejects on the first rejection. `Promise.allSettled` waits for every promise and reports each status.

Production angle:

Use `all` for all-or-nothing screens and `allSettled` for dashboards where partial data is still useful.

Related note: [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]

### Question 20: abort signal dispatch

```js
const controller = new AbortController();

controller.signal.addEventListener("abort", () => {
  console.log("abort event");
});

console.log(controller.signal.aborted);
controller.abort();
console.log(controller.signal.aborted);
```

Answer:

```txt
false
abort event
true
```

Why:

The signal starts as not aborted. Calling `abort()` marks it aborted and dispatches the abort event to listeners.

Production angle:

When using `fetch`, pass `signal` into the request and handle `AbortError` separately from real failures.

Related note: [[08 - Async JavaScript/06 - AbortController|AbortController]]

## Bonus — React and Event Output (Modules 19, 21)

### Question 21: state batching and snapshots

```jsx
function Counter() {
  const [n, setN] = useState(0);
  function onClick() {
    setN(n + 1);
    setN(n + 1);
    setN(n + 1);
    setN(prev => prev + 1);
  }
  // n starts at 0; what is n after one click?
}
```

Answer:

```txt
1  (from the three value-form calls) then +1 from the updater = 2
```

Why:

The three `setN(n + 1)` calls all read the same render snapshot `n === 0`, each enqueuing "replace with 1" — they collapse to 1. The functional updater `prev => prev + 1` then receives the pending state (1) and yields 2. All batched into one re-render.

Production angle:

Use the updater form whenever the next state depends on the previous, or in async code where the snapshot may be stale.

Related notes: [[21 - React Internals and Patterns/04 - State Batching and Updater Queues|State Batching and Updater Queues]], [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]]

### Question 22: event propagation order

```js
parent.addEventListener("click", () => console.log("parent capture"), { capture: true });
parent.addEventListener("click", () => console.log("parent bubble"));
child.addEventListener("click", () => console.log("child"));
// User clicks child. Output order?
```

Answer:

```txt
parent capture
child
parent bubble
```

Why:

The capturing phase runs top-down first (parent's capture listener), then the target's listeners (child), then the bubbling phase bottom-up (parent's bubble listener). Phase, not registration order across elements, drives the sequence.

Production angle:

A `stopPropagation()` in the child would prevent "parent bubble"; delegated listeners on `parent` rely on this bubbling reaching them.

Related note: [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]

## Bonus — Boundaries and Cancellation Output (Modules 23, 24)

### Question 23: abort events are synchronous

```js
const controller = new AbortController();
controller.signal.addEventListener("abort", () => console.log("A"));
Promise.resolve().then(() => console.log("B"));
controller.abort();
console.log("C");
```

Answer:

```txt
A
C
B
```

Why:

`controller.abort()` dispatches the `abort` event **synchronously** during the call — event dispatch is not queued as a task. So "A" logs while `abort()` is still on the stack, then the remaining synchronous code logs "C", and only when the stack empties does the microtask queue run "B". Cancellation callbacks run before any pending promise reactions.

Production angle:

Cleanup wired to an `abort` listener (removing UI, clearing maps) runs immediately when you abort in an effect cleanup — before any `.then` on the aborted fetch's rejection. Tests asserting cancellation order rely on exactly this ([[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|deterministic tests]]).

Related notes: [[08 - Async JavaScript/06 - AbortController|AbortController]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

### Question 24: the cast that compiles and crashes

```ts
type User = { name: string };
const data = JSON.parse('{"nome": "Ada"}') as User;   // typo'd key on the wire

console.log("start");
try {
  console.log(data.name.toUpperCase());
} catch (e) {
  console.log(e instanceof TypeError, e.message.includes("name"));
}
```

Answer:

```txt
start
true false   (a TypeError: cannot read "toUpperCase" of undefined — the message names toUpperCase, not name)
```

Why:

The `as User` assertion is erased at compile time — at runtime `data` is whatever JSON arrived, and `data.name` is `undefined`. Reading a property of `undefined` (`undefined.toUpperCase`) throws a `TypeError` that mentions the *method access that failed*, not the missing field — which is why unvalidated-boundary crashes point far away from their cause.

Production angle:

The fix is runtime validation at the boundary (`unknown` + schema parse), which would fail loudly at `JSON.parse`-time with the actual issue ("name: Required"). Types model the contract; validation enforces it ([[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|runtime validation]]).

Related notes: [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]], [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|unknown, Runtime Validation and Boundaries]]

## Mixed Final Drill

After solving all questions:

- [ ] Rewrite 3 questions with different variable names and predict whether the output changes.
- [ ] Run the snippets in strict mode and module mode where relevant.
- [ ] Explain one production bug connected to each category.
- [ ] Re-solve every missed question after 24 hours.

## Sources

- ECMAScript Language Specification: https://tc39.es/ecma262/
- HTML Living Standard event loops: https://html.spec.whatwg.org/multipage/webappapis.html#event-loops
- MDN JavaScript reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript
- MDN Promise reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise
- MDN AbortController reference: https://developer.mozilla.org/en-US/docs/Web/API/AbortController

## Related Notes

- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
- [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]]
- [[18 - Revision Plans/03 - 14 Day Deep Study Plan|14 Day Deep Study Plan]]
- [[18 - Revision Plans/04 - 30 Interview Questions|30 Interview Questions]]
- [[18 - Revision Plans/06 - 10 Practical Frontend Scenarios|10 Practical Frontend Scenarios]]
- [[01 - Roadmap|Roadmap]]
