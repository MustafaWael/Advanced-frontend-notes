---
tags: [javascript, interview, junior-to-mid-questions]
module: "15 - Interview Preparation"
priority: must-know
status: not-started
---

# Junior to Mid Questions

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: can turn a simple definition into a mechanism-based answer.
- Production signal: can connect each fundamental to a real frontend bug or decision.
- Fast track: answer Q1-Q8 aloud, then compare with the strong-answer signals.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)
- [HTML Living Standard: event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [React docs: State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)

## How To Use This File

For each question:

1. Give a 20-second answer first.
2. Add the official mechanism.
3. Add one tiny code example.
4. Add one frontend production consequence.
5. Invite a follow-up only after the core answer is clear.

The goal is not to sound academic. The goal is to sound precise, calm, and useful.

## Answer Formula

Use this structure when you freeze:

```text
Simple: one plain-English sentence.
Mechanism: spec, browser, React, or Next.js rule.
Example: tiny code or frontend bug.
Tradeoff: when the simple rule is not enough.
```

## Q1. What Is Hoisting?

### Weak Answer

"JavaScript moves declarations to the top."

### Strong Answer

Hoisting is the observable result of the creation phase of an execution context. Before code executes, the engine creates bindings for declarations. `var` bindings are created and initialized to `undefined`; function declarations are created and initialized to the function object; `let`, `const`, and `class` bindings are created but left uninitialized until execution reaches the declaration. That uninitialized period is the Temporal Dead Zone.

```js
console.log(a); // undefined
var a = 1;

console.log(b); // ReferenceError
let b = 2;

sayHi(); // "hi"
function sayHi() {
  console.log('hi');
}
```

### Production Angle

Hoisting bugs show up when code relies on a value before initialization, especially during module initialization or complex conditional setup. A mid-level engineer should say "binding creation and initialization timing," not "JavaScript physically moves code."

### Follow-Up

Why does `typeof missingVariable` return `"undefined"` but `typeof tdzVariable` can throw?

Related: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

## Q2. What Is A Closure?

### Weak Answer

"An inner function can access variables from its outer function."

### Strong Answer

A closure is a function together with the lexical environment it captured when the function was created. In spec terms, a function object has an internal environment reference that points to the outer lexical environment. As long as the function is reachable, the captured environment stays reachable too.

```js
function createCounter() {
  let count = 0;

  return function increment() {
    count += 1;
    return count;
  };
}

const inc = createCounter();
console.log(inc()); // 1
console.log(inc()); // 2
```

### Production Angle

Closures power callbacks, hooks, debounced functions, and event listeners. They can also retain memory. In React, every render creates closures over that render's props and state, which is why stale closure bugs exist.

### Follow-Up

What keeps `count` alive after `createCounter` returns?

Related: [[03 - Scope and Variables/05 - Closures|Closures]], [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]

## Q3. What Is The Difference Between `var`, `let`, And `const`?

### Weak Answer

"`var` is function scoped, `let` and `const` are block scoped, and `const` cannot change."

### Strong Answer

`var` is scoped to the nearest function or global scope and is initialized to `undefined` during creation. `let` and `const` are block scoped and exist in the Temporal Dead Zone until their declarations are evaluated. `const` prevents reassignment of the binding, not mutation of the value.

```js
const user = { name: 'A' };
user.name = 'B'; // allowed: object mutation

// user = {}; // TypeError: binding reassignment
```

### Production Angle

Use `const` by default for bindings you do not reassign, `let` for intentional reassignment, and almost never `var` in modern app code. In React state, `const` does not make objects immutable; you still need immutable update patterns.

### Follow-Up

Why does `const items = []` still allow `items.push(1)`?

Related: [[03 - Scope and Variables/03 - var let const|var let const]], [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]

## Q4. What Does `this` Refer To?

### Weak Answer

"`this` is the object that calls the function."

### Strong Answer

For regular functions, `this` is determined by the call site. The main rules are: `new` binding, explicit binding with `call`/`apply`/`bind`, implicit binding through `obj.method()`, and default binding. In strict mode, default binding gives `undefined`; in sloppy mode it can give the global object. Arrow functions do not have their own `this`; they close over `this` from the surrounding scope.

```js
const user = {
  name: 'Mustafa',
  getName() {
    return this.name;
  },
};

console.log(user.getName()); // "Mustafa"

const fn = user.getName;
console.log(fn()); // undefined in strict mode
```

### Production Angle

This matters when passing object methods as callbacks, integrating older class components, or using DOM/event APIs. Extracting a method loses the receiver unless you bind it or use a wrapper.

### Follow-Up

Why does `button.addEventListener('click', user.getName)` not call it with `user` as `this`?

Related: [[05 - this Binding/01 - What is this|What is this]], [[05 - this Binding/05 - call apply bind|call apply bind]]

## Q5. What Is The Event Loop?

### Weak Answer

"JavaScript is single-threaded and the event loop runs callbacks when the stack is empty."

### Strong Answer

JavaScript execution runs one piece of code at a time per agent. In browsers, the HTML event loop runs a task, then drains the microtask queue completely, then the browser may render, then it picks another task. Promise reactions and `queueMicrotask` are microtasks. Timers and user events are tasks.

```js
console.log('A');

setTimeout(() => console.log('D'), 0);

Promise.resolve()
  .then(() => console.log('C'));

console.log('B');

// Output: A, B, C, D
```

### Production Angle

Event loop knowledge explains why Promise callbacks run before timers, why long synchronous work freezes the UI, and why many microtasks can delay rendering.

### Follow-Up

Why can a long Promise chain delay a `setTimeout` and browser paint?

Related: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## Q6. What Are Promises?

### Weak Answer

"Promises are a nicer way to write async callbacks."

### Strong Answer

A Promise represents the eventual fulfillment or rejection of an async operation. It starts pending and then settles exactly once. `.then`, `.catch`, and `.finally` register reactions that run as microtasks after the current synchronous code completes. Every `.then` returns a new Promise, which is why chaining works.

```js
console.log('start');

Promise.resolve(1)
  .then(value => value + 1)
  .then(value => console.log(value));

console.log('end');

// Output: start, end, 2
```

### Production Angle

Promise mechanics matter for error handling, race conditions, loading state, and code-output interviews. A rejected Promise must be handled or returned from async flows.

### Follow-Up

Why does `try/catch` around a Promise without `await` not catch the asynchronous rejection?

Related: [[08 - Async JavaScript/02 - Promises|Promises]], [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]

## Q7. How Does `async/await` Work?

### Weak Answer

"It makes async code synchronous."

### Strong Answer

`async/await` is syntax over Promises. Calling an async function returns a Promise immediately. Code before the first `await` runs synchronously. At `await`, the function suspends and the continuation after `await` is scheduled through Promise microtask behavior when the awaited value settles.

```js
async function run() {
  console.log('A');
  await Promise.resolve();
  console.log('C');
}

run();
console.log('B');

// Output: A, B, C
```

### Production Angle

Sequential `await`s are serial. Start independent requests first and then `await Promise.all` when concurrency is desired.

```js
const [user, permissions] = await Promise.all([
  fetchUser(),
  fetchPermissions(),
]);
```

### Follow-Up

Why does `await` not block the JavaScript thread?

Related: [[08 - Async JavaScript/04 - Async Await|Async Await]], [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]

## Q8. What Is Prototype Inheritance?

### Weak Answer

"Objects inherit from other objects."

### Strong Answer

Objects have an internal \[\[Prototype\]\] link to another object or `null`. When reading a property, JavaScript checks own properties first, then follows the prototype chain. Constructor functions and `class` syntax use prototypes for method sharing.

```js
function User(name) {
  this.name = name;
}

User.prototype.greet = function () {
  return `Hi ${this.name}`;
};

const user = new User('Mustafa');

console.log(user.hasOwnProperty('greet')); // false
console.log(user.greet()); // "Hi Mustafa"
```

### Production Angle

Prototype knowledge helps debug class methods, third-party library objects, `instanceof`, and why methods should live on prototypes rather than be recreated per instance when appropriate.

### Follow-Up

What is the difference between `obj.__proto__` and `Constructor.prototype`?

Related: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]], [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]

## Q9. What Is The Difference Between `==`, `===`, And `Object.is`?

### Weak Answer

"`==` converts types, `===` does not, so always use `===`."

### Strong Answer

`==` uses the Abstract Equality Comparison algorithm, which can coerce types. `===` compares without type coercion, but treats `NaN` as not equal to itself and `0` and `-0` as equal. `Object.is` uses SameValue semantics: `Object.is(NaN, NaN)` is `true`, and `Object.is(0, -0)` is `false`.

```js
console.log(null == undefined); // true
console.log(null === undefined); // false
console.log(NaN === NaN); // false
console.log(Object.is(NaN, NaN)); // true
console.log(Object.is(0, -0)); // false
```

### Production Angle

React uses `Object.is` for state and dependency comparisons. Referential equality is why mutating an object and returning the same reference can skip a render.

### Follow-Up

Why does `Object.is({}, {})` return `false`?

Related: [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]], [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]

## Q10. What Is A Pure Function?

### Weak Answer

"A pure function returns the same output for the same input."

### Strong Answer

A pure function is deterministic and has no side effects. Same inputs produce the same output, and calling it does not mutate external state, perform I/O, or depend on hidden changing values. This gives referential transparency: the call can be replaced by its result.

```js
function add(a, b) {
  return a + b;
}

let total = 0;
function addImpure(value) {
  total += value;
  return total;
}
```

### Production Angle

React render logic is expected to be pure. If a component fires analytics, mutates a cache, or starts network requests during render, repeated renders and Strict Mode checks can create duplicate side effects.

### Follow-Up

Why is a pure reducer easier to test and memoize?

Related: [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions and IIFE]], [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]

## Q11. What Are Mutating And Non-Mutating Array Methods?

### Weak Answer

"Some methods change the array and some return a new array."

### Strong Answer

Mutating methods change the existing array reference, such as `push`, `pop`, `splice`, `sort`, and `reverse`. Non-mutating methods return a new value or do not modify the original, such as `map`, `filter`, `slice`, `concat`, and newer methods like `toSorted`, `toReversed`, and `toSpliced`.

```js
const items = [3, 1, 2];
const sortedWrong = items.sort();

console.log(items); // [1, 2, 3], original mutated

const next = [3, 1, 2].toSorted();
console.log(next); // [1, 2, 3]
```

### Production Angle

In React state, mutating arrays can prevent rerenders or mutate previous snapshots. Copy before sorting or reversing.

### Follow-Up

Why is `[...items].sort()` safer than `items.sort()` in state updates?

Related: [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]], [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]

## Q12. What Makes A Good Mid-Level Answer?

### Weak Answer

It lists facts without structure.

### Strong Answer

A good answer begins simple, then explains the mechanism, then proves it with a small example, then connects to production. It does not over-explain before answering the direct question.

```text
"A closure is a function that remembers its lexical scope.
Technically, the function keeps a reference to the environment where it was created.
In React, this is why an interval can read old state from an earlier render.
The fix depends on intent: dependencies, functional update, or ref."
```

### Production Angle

Interview communication mirrors production engineering: lead with the decision, explain the reasoning, and be honest about tradeoffs.

### Follow-Up

How would you turn a 30-second answer into a 2-minute answer without rambling?

Related: [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]], [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]]

## Practice Routine

- [ ] Answer Q1-Q12 in one sentence each.
- [ ] Pick the three weakest and give a two-minute version.
- [ ] For each weak answer, name the missing mechanism.
- [ ] For each strong answer, add one React, browser, or Next.js production bug.
- [ ] Revisit the related notes for every question you cannot answer cleanly.

## Related Notes

- [[15 - Interview Preparation/02 - Mid Level Questions|Mid Level Questions]]
- [[15 - Interview Preparation/03 - Strong Mid Level Questions|Strong Mid Level Questions]]
- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
- [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]]
- [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]]
- [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]]
