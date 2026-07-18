---
tags: [javascript, glossary]
module: "Vault Root"
priority: must-know
status: not-started
---

# Glossary

Use this as a review-quality reference, not as a dictionary to memorize. A mature interview answer usually needs one precise term, one mechanism, and one production example.

Each entry uses this shape:

- Plain English: the everyday meaning.
- Technical Meaning: the accurate JavaScript, browser, React, or Next.js mechanism.
- Why It Matters: the frontend bug, interview signal, or production decision.
- Example: a small code or scenario anchor.

## Abstract Operation

**Plain English:** A named algorithm in the ECMAScript specification.

**Technical Meaning:** Abstract operations such as `ToNumber`, `ToString`, `GetValue`, `Set`, and `SameValueZero` describe required engine behavior. They are specification algorithms, not functions you call from JavaScript.

**Why It Matters:** Abstract operations explain coercion, equality, property access, assignment, iteration, and many "why did this output happen?" questions.

```js
console.log("5" - 2); // 3
// Numeric subtraction applies number conversion to "5".
```

Related notes: [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]], [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]

## Agent

**Plain English:** One independent JavaScript execution unit.

**Technical Meaning:** In ECMAScript, an agent has its own execution context stack, job queues, and execution state. A browser window and a Web Worker are separate agent-like execution environments.

**Why It Matters:** This is the precise version of "JavaScript runs one piece of JS at a time" for one agent. Workers introduce separate execution, not shared call stacks.

```js
// The window and a Worker do not share a call stack.
const worker = new Worker("/worker.js");
```

Related note: [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]

## Agent Cluster

**Plain English:** A group of agents that can share memory.

**Technical Meaning:** Agent clusters model which agents may communicate through shared memory such as `SharedArrayBuffer` and `Atomics`.

**Why It Matters:** Most frontend work uses message passing, but performance-heavy worker code may use shared memory. This is advanced and should be treated carefully.

```js
// SharedArrayBuffer enables shared memory patterns with workers.
const shared = new SharedArrayBuffer(1024);
```

Related note: [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]

## Arguments Object

**Plain English:** An array-like object containing arguments passed to a regular function.

**Technical Meaning:** Regular functions get an `arguments` object. Arrow functions do not create their own `arguments`; use rest parameters instead.

**Why It Matters:** Interview questions often test why an arrow callback cannot read its own `arguments`. Production code should prefer rest parameters for clarity and array methods.

```js
function sum() {
  return Array.from(arguments).reduce((total, value) => total + value, 0);
}

const modernSum = (...values) =>
  values.reduce((total, value) => total + value, 0);
```

Related note: [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]]

## Array-Like Object

**Plain English:** An object that looks like an array because it has numeric keys and `length`.

**Technical Meaning:** Array-like objects are not necessarily arrays and do not automatically have array prototype methods. Examples include older DOM collections and `arguments`.

**Why It Matters:** Use `Array.from`, spread when iterable, or real arrays before calling array methods.

```js
function logFirst() {
  const args = Array.from(arguments);
  console.log(args.map(String)[0]);
}
```

Related note: [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]

## Async Function

**Plain English:** A function that returns a promise and can use `await`.

**Technical Meaning:** Calling an `async` function always returns a promise. Returned values fulfill the promise; thrown errors reject it. `await` schedules the continuation through promise job behavior.

**Why It Matters:** `try/catch` catches awaited rejections, but not unrelated async callbacks. Async functions also create timing boundaries that affect UI state and tests.

```js
async function loadUser() {
  const response = await fetch("/api/user");
  if (!response.ok) throw new Error("Request failed");
  return response.json();
}
```

Related note: [[08 - Async JavaScript/04 - Async Await|Async Await]]

## Await

**Plain English:** Pause this async function until a value is resolved.

**Technical Meaning:** `await` converts the value with promise resolution semantics, suspends the async function, and resumes it later as a promise continuation.

**Why It Matters:** `await` does not block the main thread, but code after `await` runs later. That can change loading-state timing and error handling.

```js
async function demo() {
  console.log("A");
  await Promise.resolve();
  console.log("B"); // Runs after the current synchronous turn.
}
```

Related note: [[08 - Async JavaScript/04 - Async Await|Async Await]]

## Call Stack

**Plain English:** The stack of active function calls.

**Technical Meaning:** Function calls push execution contexts onto the stack. Returning or throwing unwinds the stack. JavaScript runs the top context until it completes.

**Why It Matters:** Stack traces, recursion bugs, and run-to-completion behavior all depend on the call stack.

```js
function a() {
  b();
}
function b() {
  console.trace();
}
a();
```

Related note: [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]

## Closure

**Plain English:** A function that keeps access to variables from where it was created.

**Technical Meaning:** A function object has an internal environment reference to its creation lexical environment. The closure keeps those bindings reachable as long as the function is reachable.

**Why It Matters:** Closures power callbacks, hooks, factories, event handlers, and private state. They also cause stale-value bugs and retained-memory bugs when lifetime is misunderstood.

```js
function createCounter() {
  let count = 0;
  return () => {
    count += 1;
    return count;
  };
}
```

Related notes: [[03 - Scope and Variables/05 - Closures|Closures]], [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]

## Completion Record

**Plain English:** The spec's way to represent how evaluation finished.

**Technical Meaning:** Completion records represent normal completion, return, throw, break, and continue. They explain how control flow propagates through code.

**Why It Matters:** `try/finally`, thrown errors, return behavior, and loop control all become clearer when you know statements complete with structured outcomes.

```js
function demo() {
  try {
    return "value";
  } finally {
    console.log("finally still runs");
  }
}
```

Related note: [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]]

## Declarative Environment Record

**Plain English:** Internal storage for lexical bindings.

**Technical Meaning:** Declarative environment records store bindings for functions, blocks, catch clauses, classes, and modules. `let`, `const`, and class bindings are created but uninitialized before their declaration runs.

**Why It Matters:** This is the mechanism behind TDZ, lexical scope, closures, and module bindings.

```js
{
  let status = "ready";
  console.log(status);
}
```

Related note: [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]

## Dependency Array

**Plain English:** The list of reactive values a React hook depends on.

**Technical Meaning:** React compares dependency entries with `Object.is`. Effects and memoized values should include values from component scope that they read and that participate in rendering/data flow.

**Why It Matters:** Missing dependencies cause stale closures. Unstable object/function dependencies cause unnecessary reruns. The fix is honest dependencies plus better data flow.

```jsx
useEffect(() => {
  document.title = `Search: ${query}`;
}, [query]);
```

Related note: [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]

## Environment Record

**Plain English:** Internal storage for names in a scope.

**Technical Meaning:** Every lexical environment has an environment record that maps identifiers to bindings. Identifier lookup checks the current record, then outer lexical environments.

**Why It Matters:** Variables, closures, TDZ, modules, and scope chains all use this model.

```js
function outer() {
  const value = 1;
  return function inner() {
    return value;
  };
}
```

Related note: [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]

## Error Boundary

**Plain English:** A React component that catches render-time errors below it.

**Technical Meaning:** Error boundaries catch errors during rendering, lifecycle methods, and constructors of child components. They do not catch event handler errors, async callback errors, or server-side errors by default.

**Why It Matters:** Error boundaries are for UI containment, not general promise error handling. API errors and event errors still need explicit handling.

```jsx
// Event handlers still need their own try/catch or promise handling.
async function handleClick() {
  try {
    await save();
  } catch (error) {
    setError(error);
  }
}
```

Related note: [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]]

## Event Loop

**Plain English:** The host mechanism that schedules work over time.

**Technical Meaning:** In browsers, the HTML event loop runs tasks, performs microtask checkpoints, and gives the browser rendering opportunities. ECMAScript defines jobs; the host integrates them into the event loop.

**Why It Matters:** Event loop knowledge explains promise-before-timer output, UI responsiveness, rendering delays, and async timing bugs.

```js
console.log("A");
setTimeout(() => console.log("task"), 0);
Promise.resolve().then(() => console.log("microtask"));
console.log("B");
// A, B, microtask, task
```

Related notes: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## Execution Context

**Plain English:** The runtime record for code currently executing.

**Technical Meaning:** Execution contexts include lexical environment, variable environment, `this` binding, realm, function/module/script references, and evaluation state.

**Why It Matters:** Hoisting, `this`, scope, closures, strict mode, and stack traces all depend on execution context mechanics.

```js
function greet(name) {
  const message = `Hi ${name}`;
  return message;
}
```

Related note: [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]

## Exotic Object

**Plain English:** An object with special internal behavior.

**Technical Meaning:** Exotic objects customize some internal methods. Arrays, functions, proxies, module namespace objects, and typed arrays have behavior ordinary objects do not.

**Why It Matters:** Arrays update `length` specially, functions are callable, proxies intercept operations, and module namespace objects behave differently from plain objects.

```js
const values = [];
values[3] = "x";
console.log(values.length); // 4
```

Related note: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]

## Function Environment Record

**Plain English:** The environment record for a function call.

**Technical Meaning:** It stores parameters, local bindings, and regular function `this` binding behavior. Arrow functions do not create their own `this` binding.

**Why It Matters:** Explains `arguments`, parameters, local variables, regular `this`, and arrow lexical `this`.

```js
const user = {
  id: 1,
  read() {
    return this.id;
  },
};
```

Related notes: [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]], [[05 - this Binding/01 - What is this|What is this]]

## Garbage Collection

**Plain English:** Automatic cleanup of unreachable objects.

**Technical Meaning:** JavaScript engines reclaim objects that cannot be reached from roots such as the stack, globals, closures, host references, and active tasks/listeners.

**Why It Matters:** Memory leaks happen when objects remain reachable accidentally. Common frontend causes: listeners, timers, subscriptions, caches, pending requests, and retained closures.

```js
window.addEventListener("resize", handler);
// If handler closes over component data and is never removed, it can retain memory.
```

Related notes: [[13 - Performance and Memory/01 - Memory Management|Memory Management]], [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]

## Global Environment Record

**Plain English:** The environment record for global code.

**Technical Meaning:** It combines object-backed global bindings and declarative global bindings. In browser scripts, top-level `var` can create a property on `window`, while top-level `let` and `const` do not.

**Why It Matters:** Helps explain global pollution, script vs module behavior, and why globals differ across browser, Node, worker, and test environments.

```js
// Browser script behavior:
var oldGlobal = 1;
let lexicalGlobal = 2;
```

Related note: [[03 - Scope and Variables/03 - var let const|var let const]]

## Host Environment

**Plain English:** The system embedding the JavaScript engine.

**Technical Meaning:** The host provides APIs outside ECMAScript: DOM, timers, fetch, storage, rendering, workers, files, sockets, and process APIs.

**Why It Matters:** Do not blame ECMAScript for browser APIs. `setTimeout`, `document`, `localStorage`, and rendering behavior are host/framework topics.

```js
setTimeout(() => {}, 0); // Host API, not ECMAScript core.
```

Related note: [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]]

## Hoisting

**Plain English:** Binding setup that happens before code executes.

**Technical Meaning:** During environment setup, function declarations are initialized, `var` bindings are initialized to `undefined`, and `let`/`const`/class bindings are created but remain uninitialized until evaluated.

**Why It Matters:** Strong answers avoid saying declarations "move." The real distinction is binding creation and initialization.

```js
console.log(a); // undefined
var a = 1;

// console.log(b); // ReferenceError
let b = 2;
```

Related note: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

## Hydration

**Plain English:** React attaching client behavior to server-rendered HTML.

**Technical Meaning:** Hydration expects the client render output to match the server HTML closely enough for React to attach events and continue. Different render inputs can cause mismatches.

**Why It Matters:** Time, randomness, browser-only data, invalid HTML, and client-only state can create Next.js hydration problems.

```jsx
// Risky during server render because the client value may differ.
const now = new Date().toLocaleTimeString();
```

Related note: [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]

## Idempotency

**Plain English:** Running an operation more than once has the same intended effect as running it once.

**Technical Meaning:** In frontend/API work, idempotency is often implemented with server-side keys, request dedupe, or operation design so retries and double-clicks do not create duplicates.

**Why It Matters:** UI guards are helpful, but critical writes such as payments need server-side duplicate protection.

```js
await fetch("/api/payments", {
  method: "POST",
  headers: { "Idempotency-Key": paymentAttemptId },
});
```

Related note: [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]

## Internal Slot

**Plain English:** A hidden spec field used to define object behavior.

**Technical Meaning:** Internal slots are written in the spec with double brackets, such as escaped here as \[\[Prototype\]\], \[\[Environment\]\], or \[\[PromiseState\]\]. They are not normal properties.

**Why It Matters:** Internal slots let you speak precisely about promises, functions, prototypes, and closures without pretending those fields are public JavaScript properties.

```js
const proto = Object.getPrototypeOf([]);
console.log(proto === Array.prototype); // true
```

Related note: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]

## Intrinsic Object

**Plain English:** A built-in object created for a realm.

**Technical Meaning:** Each realm has its own intrinsic objects such as `Array`, `Object`, `Function`, `Promise`, and `Map`.

**Why It Matters:** Cross-realm values can fail `instanceof` checks because their constructors come from another realm. Prefer brand-safe checks such as `Array.isArray` when appropriate.

```js
Array.isArray(value); // Better than value instanceof Array across realms.
```

Related note: [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]

## Iterable Protocol

**Plain English:** The protocol that lets an object work with `for...of`, spread, and destructuring.

**Technical Meaning:** An iterable has a `[Symbol.iterator]()` method that returns an iterator. The iterator has a `next()` method returning `{ value, done }`.

**Why It Matters:** Arrays, strings, maps, sets, generators, and many browser collections rely on iteration protocols. Custom data structures can join the same syntax.

```js
const ids = new Set([1, 2, 2]);
console.log([...ids]); // [1, 2]
```

Related note: [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]]

## Iterator

**Plain English:** An object that produces a sequence of values.

**Technical Meaning:** An iterator exposes `next()`, which returns an object with `value` and `done`. Generators create iterators automatically.

**Why It Matters:** Iterators explain lazy sequences, generators, spread syntax, destructuring, and `for...of`.

```js
function* range() {
  yield 1;
  yield 2;
}

console.log([...range()]); // [1, 2]
```

Related note: [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]

## Job

**Plain English:** A queued ECMAScript unit of work.

**Technical Meaning:** Promise reactions and async continuations are represented with jobs. Hosts integrate jobs with their microtask processing.

**Why It Matters:** Jobs explain why `.then` callbacks and `await` continuations run after current synchronous work.

```js
Promise.resolve().then(() => console.log("promise job"));
```

Related note: [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]

## Lexical Environment

**Plain English:** Binding storage plus a link to an outer environment.

**Technical Meaning:** A lexical environment contains an environment record and an outer reference. Identifier lookup walks this chain.

**Why It Matters:** This is the concrete model behind lexical scope, closures, TDZ, and module bindings.

```js
const label = "outer";
function read() {
  return label;
}
```

Related note: [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]

## Lexical Scope

**Plain English:** Scope is based on where code is written.

**Technical Meaning:** Identifier resolution follows the outer environment links determined by source structure, not by who calls the function.

**Why It Matters:** Lexical scope is why closures are predictable and why a callback can read values from the function/component where it was created.

```js
const value = "global";
function outer() {
  const value = "outer";
  return () => value;
}
console.log(outer()()); // "outer"
```

Related note: [[03 - Scope and Variables/01 - Scope Types|Scope Types]]

## Live Binding

**Plain English:** An imported binding reflects the current exported value.

**Technical Meaning:** ES module imports are connected to exported module environment bindings. They are not copied snapshots.

**Why It Matters:** Live bindings explain module updates and circular dependency behavior. They also explain why imports are read-only from the importer side.

```js
// Importers read the exported binding's current value.
import { currentUser } from "./session.js";
```

Related note: [[10 - Modules/05 - Live Bindings|Live Bindings]]

## Main Thread

**Plain English:** The browser thread that runs JavaScript, handles many events, and coordinates rendering.

**Technical Meaning:** In the window context, heavy synchronous JavaScript can block input handling, style/layout work, and paint opportunities.

**Why It Matters:** Long computations, huge loops, and expensive renders cause jank even when the algorithm is correct.

```js
// A huge synchronous loop can delay input and paint.
for (let i = 0; i < 50_000_000; i++) {}
```

Related note: [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]

## Memoization

**Plain English:** Cache a computed result and reuse it when inputs are the same.

**Technical Meaning:** Memoization relies on stable input identity or equality checks. In React, `useMemo` caches a value between renders while dependencies are equal by `Object.is`.

**Why It Matters:** Memoization can reduce expensive work, but it adds complexity and can fail if dependencies are unstable or wrong.

```jsx
const visible = useMemo(() => {
  return products.filter((product) => product.name.includes(query));
}, [products, query]);
```

Related note: [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]

## Microtask

**Plain English:** High-priority work run after current synchronous code and before many later tasks.

**Technical Meaning:** Browser microtask checkpoints process promise reactions, `queueMicrotask`, and related callbacks after a task completes. The microtask queue is drained before moving on.

**Why It Matters:** Microtasks explain promise-before-timer output and why too many microtasks can delay rendering.

```js
queueMicrotask(() => console.log("microtask"));
setTimeout(() => console.log("task"), 0);
```

Related note: [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## Module Graph

**Plain English:** The network of modules connected by imports.

**Technical Meaning:** Static imports let the host parse, link, and evaluate a module graph. Dynamic imports load a module asynchronously when requested.

**Why It Matters:** Module graph shape affects startup cost, circular dependencies, tree shaking, and code splitting.

```js
const Chart = await import("./Chart.js"); // Dynamic import boundary.
```

Related note: [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]

## Module Record

**Plain English:** The spec's representation of a module.

**Technical Meaning:** A module record tracks requested modules, imports, exports, environment, and evaluation state.

**Why It Matters:** Module records explain live bindings, linking, evaluation order, and circular import failure modes.

```js
// Static imports are known before module evaluation.
import { formatPrice } from "./money.js";
```

Related note: [[10 - Modules/01 - ES Modules|ES Modules]]

## Nullish

**Plain English:** `null` or `undefined`.

**Technical Meaning:** Optional chaining and nullish coalescing check specifically for `null` and `undefined`, not all falsy values.

**Why It Matters:** `??` preserves valid falsy values like `0`, `false`, and `""`, which matters for form values and UI display.

```js
const count = 0;
console.log(count || 10); // 10
console.log(count ?? 10); // 0
```

Related note: [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]

## Object Identity

**Plain English:** Objects are compared by reference, not by shape.

**Technical Meaning:** Two separate object allocations are different identities even if their properties match. Object identity affects strict equality, `Object.is`, maps, sets, React dependencies, and memoization.

**Why It Matters:** Recreating objects/functions during render can retrigger effects and invalidate memoization.

```js
console.log({ id: 1 } === { id: 1 }); // false
```

Related notes: [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]], [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]

## Object.is

**Plain English:** A precise equality check used by React dependency comparisons.

**Technical Meaning:** `Object.is` uses SameValue semantics. It treats `NaN` as equal to itself and distinguishes `+0` from `-0`.

**Why It Matters:** React uses `Object.is` for dependency comparisons in hooks. Identity still matters for objects and functions.

```js
console.log(Object.is(NaN, NaN)); // true
console.log(Object.is(+0, -0)); // false
```

Related note: [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]

## Ordinary Object

**Plain English:** A normal object with standard internal behavior.

**Technical Meaning:** Ordinary objects use standard internal methods for property access, property definition, prototype lookup, and extensibility.

**Why It Matters:** Knowing ordinary behavior helps you recognize when arrays, functions, proxies, module namespace objects, or typed arrays are special.

```js
const user = { name: "Mina" };
console.log(Object.getPrototypeOf(user) === Object.prototype);
```

Related note: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]

## Promise

**Plain English:** A value representing eventual completion or failure.

**Technical Meaning:** A promise has internal state: pending, fulfilled, or rejected. Reactions registered with `.then`, `.catch`, or `.finally` run later as jobs/microtasks.

**Why It Matters:** Promises do not cancel work by themselves, do not create threads, and do not make synchronous CPU work non-blocking.

```js
fetch("/api/user")
  .then((response) => response.json())
  .then((user) => console.log(user));
```

Related note: [[08 - Async JavaScript/02 - Promises|Promises]]

## Promise Job

**Plain English:** The job that runs promise reactions.

**Technical Meaning:** When a promise settles, registered reactions are queued as promise jobs. `await` continuation also resumes through promise-job behavior.

**Why It Matters:** Promise jobs are why `then` callbacks usually run before timers scheduled in the same turn.

```js
Promise.resolve().then(() => console.log("then"));
console.log("sync");
// sync, then
```

Related note: [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]

## Property Descriptor

**Plain English:** The full metadata for an object property.

**Technical Meaning:** Data descriptors have value and writable attributes. Accessor descriptors have getter and setter. Both have enumerable and configurable attributes.

**Why It Matters:** Descriptors explain `Object.defineProperty`, `Object.freeze`, getters/setters, class method enumerability, and why `const` does not freeze object contents.

```js
const obj = {};
Object.defineProperty(obj, "id", {
  value: 1,
  writable: false,
  enumerable: true,
});
```

Related note: [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]]

## Prototype

**Plain English:** The object used as a fallback for property lookup.

**Technical Meaning:** Most objects have an internal prototype reference. If property lookup does not find a property directly on the object, JavaScript checks the prototype chain.

**Why It Matters:** Prototypes explain shared methods, classes, constructor functions, inheritance, and why own-property checks matter.

```js
const parent = { role: "admin" };
const child = Object.create(parent);
console.log(child.role); // "admin"
```

Related note: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]

## Prototype Chain

**Plain English:** The linked path followed during property lookup.

**Technical Meaning:** Property access checks the object, then its prototype, then the next prototype, until the property is found or the chain reaches `null`.

**Why It Matters:** Inherited properties can appear present even when they are not own properties. This matters for validation and merging.

```js
console.log("toString" in {}); // true, inherited from Object.prototype.
```

Related note: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]

## Race Condition

**Plain English:** A bug where timing changes the result.

**Technical Meaning:** In frontend async code, multiple requests, timers, effects, or user actions can complete in a different order than they started.

**Why It Matters:** Search results, route data, form submissions, and optimistic updates can show stale data unless old work is canceled or ignored.

```js
let latestRequest = 0;
async function search(query) {
  const requestId = ++latestRequest;
  const data = await fetchResults(query);
  if (requestId === latestRequest) render(data);
}
```

Related note: [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]

## Realm

**Plain English:** A JavaScript world with its own globals and built-ins.

**Technical Meaning:** A realm contains intrinsic objects, a global object, and a global environment. Iframes and workers can have separate realms.

**Why It Matters:** Cross-realm values can have different constructors. This is why `Array.isArray` is often better than `instanceof Array`.

```js
Array.isArray(value); // Works reliably for arrays across realms.
```

Related note: [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]

## Reference Record

**Plain English:** The spec representation of a reference before it is read or written.

**Technical Meaning:** Reference records hold a base, referenced name, strict flag, and sometimes a `this` value. `GetValue` turns a reference into an actual value.

**Why It Matters:** Reference records explain why `obj.method()` preserves a receiver but `const fn = obj.method; fn()` does not.

```js
const obj = {
  id: 1,
  read() {
    return this.id;
  },
};
```

Related note: [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]

## Referential Equality

**Plain English:** Equality by reference identity.

**Technical Meaning:** Objects, arrays, and functions are equal only when they are the same allocation/reference. React hook dependencies and memoized components depend on this.

**Why It Matters:** Inline objects/functions can cause rerenders and effects. Mutating an object can keep the same reference and hide a real change.

```jsx
useEffect(() => {
  connect(options);
}, [options]); // Reruns whenever options is a new object reference.
```

Related note: [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]

## Render

**Plain English:** React calling components to calculate UI output.

**Technical Meaning:** A render is a pure calculation of what the UI should look like for the current props, state, and context. Effects run after rendering/commit, not during render.

**Why It Matters:** Side effects during render create bugs. Each render also creates new closures and values, which matters for stale closures and dependency arrays.

```jsx
function UserName({ user }) {
  return <span>{user.name}</span>;
}
```

Related note: [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]

## Run To Completion

**Plain English:** JavaScript finishes the current piece of work before another callback interrupts it.

**Technical Meaning:** A currently executing task or job runs until the call stack is empty. Other callbacks wait in queues.

**Why It Matters:** This prevents mid-function interruption, but long work blocks responsiveness.

```js
console.log("start");
setTimeout(() => console.log("later"), 0);
console.log("end");
```

Related note: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]

## SameValueZero

**Plain English:** An equality algorithm used by several collection operations.

**Technical Meaning:** SameValueZero treats `NaN` as equal to `NaN` and treats `+0` and `-0` as equal. `Array.prototype.includes`, `Map`, and `Set` use it for matching.

**Why It Matters:** Explains why `[NaN].includes(NaN)` is true while `NaN === NaN` is false.

```js
console.log([NaN].includes(NaN)); // true
console.log(new Set([NaN, NaN]).size); // 1
```

Related note: [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]

## Scope

**Plain English:** Where a name can be accessed.

**Technical Meaning:** Scope is implemented through lexical environments and environment records. JavaScript has global, module, function, block, and catch scopes.

**Why It Matters:** Scope prevents naming collisions, controls lifetime, and defines what closures can capture.

```js
if (true) {
  const local = "inside";
}
// local is not available here.
```

Related note: [[03 - Scope and Variables/01 - Scope Types|Scope Types]]

## Scope Chain

**Plain English:** The sequence of scopes searched for a name.

**Technical Meaning:** Identifier lookup checks the current lexical environment, then each outer lexical environment until the binding is found or lookup fails.

**Why It Matters:** Scope chain is the lookup mechanism behind closures and shadowing bugs.

```js
const value = "outer";
function read() {
  const value = "inner";
  return value; // Finds the inner binding first.
}
```

Related note: [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]

## Server Component

**Plain English:** A Next.js/React component that renders on the server by default in the App Router.

**Technical Meaning:** Server Components can access server resources and reduce client JavaScript, but they cannot use client hooks, event handlers, or browser-only APIs.

**Why It Matters:** Keep data fetching and non-interactive rendering on the server when possible. Move interactivity into Client Components.

```jsx
// Server Component: no useState, no window, no click handler.
export default async function Page() {
  const products = await getProducts();
  return <ProductList products={products} />;
}
```

Related note: [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]

## Client Component

**Plain English:** A component that runs in the browser and can use interactivity.

**Technical Meaning:** In Next.js App Router, a file marked with `"use client"` defines a client boundary. Components inside can use state, effects, event handlers, and browser APIs.

**Why It Matters:** Use Client Components for interactivity, but keep the boundary as small as practical to avoid unnecessary client JavaScript.

```jsx
"use client";

export function FavoriteButton() {
  const [liked, setLiked] = useState(false);
  return <button onClick={() => setLiked((value) => !value)}>Like</button>;
}
```

Related note: [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]

## Shallow Copy

**Plain English:** Copy the outer container, but keep nested references.

**Technical Meaning:** Object spread, array spread, `slice`, and `Object.assign` create shallow copies. Nested objects remain shared unless explicitly copied.

**Why It Matters:** Shallow copies are common in React state updates. They are correct only when unchanged nested references are not mutated.

```js
const original = { profile: { name: "Mina" } };
const copy = { ...original };
copy.profile.name = "Sara";
console.log(original.profile.name); // "Sara"
```

Related note: [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]

## Strict Mode

**Plain English:** A stricter JavaScript mode that rejects unsafe behavior.

**Technical Meaning:** Strict mode changes semantics for default `this`, undeclared assignments, duplicate parameters, `with`, `eval`, deletion errors, and more. ES modules and classes are strict by default.

**Why It Matters:** Many interview `this` answers depend on whether strict mode applies.

```js
"use strict";
function readThis() {
  return this;
}
console.log(readThis()); // undefined
```

Related note: [[05 - this Binding/02 - this in Strict Mode|this in Strict Mode]]

## Stale Closure

**Plain English:** A callback reads old values from an earlier scope/render.

**Technical Meaning:** The callback still points to the lexical environment where it was created. In React, each render creates new values, so old callbacks can read old render values.

**Why It Matters:** Stale closures break intervals, debounced search, async effects, event listeners, and submitted form values.

```jsx
setCount((current) => current + 1); // Avoids stale count in previous-state updates.
```

Related notes: [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]], [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

## Task

**Plain English:** A host-scheduled unit of work such as a timer or event.

**Technical Meaning:** Browser event loops run tasks from task queues. After a task finishes, the browser performs a microtask checkpoint before moving on.

**Why It Matters:** Timers, click handlers, script execution, and many I/O events are task-based. Promise reactions usually run before the next task.

```js
setTimeout(() => console.log("task"), 0);
```

Related note: [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## TDZ

**Plain English:** The period where a lexical binding exists but cannot be accessed yet.

**Technical Meaning:** `let`, `const`, and class bindings are created when the scope is entered, but they are uninitialized until their declaration runs. Access before initialization throws `ReferenceError`.

**Why It Matters:** TDZ explains why lexical declarations are safer than `var` but can still surprise during refactors and circular imports.

```js
// ReferenceError:
// console.log(status);
let status = "ready";
```

Related note: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

## ThisBinding

**Plain English:** The value of `this` for an execution context.

**Technical Meaning:** For regular functions, `this` is determined by call site: default, implicit receiver, explicit `.call`/`.apply`/`.bind`, or constructor call. Arrows use lexical `this`.

**Why It Matters:** Extracted methods, event callbacks, class methods, and object methods all depend on correct receiver reasoning.

```js
const user = {
  id: 1,
  read() {
    return this.id;
  },
};

const read = user.read;
// read() loses the user receiver.
```

Related note: [[05 - this Binding/01 - What is this|What is this]]

## Type Coercion

**Plain English:** Automatic conversion from one type to another.

**Technical Meaning:** Coercion uses abstract operations such as `ToPrimitive`, `ToNumber`, `ToString`, and `ToBoolean`. `==` performs abstract equality comparison; `===` does not coerce types.

**Why It Matters:** Coercion explains confusing output questions and real bugs in forms, query params, validation, and conditional rendering.

```js
console.log("5" + 1); // "51"
console.log("5" - 1); // 4
```

Related note: [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]

## Variable Environment

**Plain English:** The execution-context component that stores `var` and function declarations.

**Technical Meaning:** `var` and function declarations are handled through the variable environment during context creation. In many function contexts it starts as the same environment as the lexical environment, but the distinction matters for spec accuracy.

**Why It Matters:** Explains function-scoped `var`, hoisting to `undefined`, and why `let`/`const` behave differently.

```js
function demo() {
  console.log(value); // undefined
  var value = 1;
}
```

Related note: [[03 - Scope and Variables/03 - var let const|var let const]]

## Well-Known Symbol

**Plain English:** A built-in symbol that customizes language behavior.

**Technical Meaning:** Well-known symbols such as `Symbol.iterator`, `Symbol.asyncIterator`, `Symbol.toPrimitive`, and `Symbol.toStringTag` are extension points used by built-in operations.

**Why It Matters:** They explain iteration, coercion customization, async iteration, and library-level behavior.

```js
const range = {
  *[Symbol.iterator]() {
    yield 1;
    yield 2;
  },
};
console.log([...range]); // [1, 2]
```

Related note: [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]

## WeakMap

**Plain English:** A key/value collection where object keys are held weakly.

**Technical Meaning:** WeakMap keys must be objects or non-registered symbols. If a key becomes unreachable elsewhere, its entry can be collected. WeakMaps are not enumerable.

**Why It Matters:** Useful for metadata tied to object lifetime without forcing objects to stay in memory.

```js
const metadata = new WeakMap();
const node = document.createElement("button");
metadata.set(node, { tracked: true });
```

Related note: [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]

## WeakRef

**Plain English:** A reference that does not keep its target alive.

**Technical Meaning:** `WeakRef` lets code attempt to access an object without preventing garbage collection. `.deref()` returns the object if still alive or `undefined` otherwise.

**Why It Matters:** Rare in application code, but useful to recognize in cache/library discussions. Do not use it as a normal cleanup tool; lifetime is intentionally nondeterministic.

```js
let object = { expensive: true };
const ref = new WeakRef(object);
object = null;

const maybeObject = ref.deref();
```

Related note: [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]

## Terms from Modules 19–22 and Extensions

These entries cover the browser platform, network/security, React internals, and Next.js modules. They follow the same shape; they are grouped here rather than interleaved alphabetically so the newer material stays discoverable as one set.

### Reflow (Layout)

**Plain English:** The browser recomputing where and how big elements are.

**Technical Meaning:** The layout stage of the render pipeline: geometry (position/size) is recalculated for affected boxes when the DOM/CSSOM changes in a way that affects geometry. Reading layout-dependent properties (`offsetHeight`, `getBoundingClientRect`) while layout is dirty forces a synchronous reflow.

**Why It Matters:** Interleaving DOM reads and writes causes layout thrashing — many forced reflows per frame — the most common non-network frontend performance bug.

Related note: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]

### Repaint

**Plain English:** Redrawing pixels without moving anything.

**Technical Meaning:** The paint stage reruns for visual-only changes (`color`, `background`, `box-shadow`) that don't affect geometry. Cheaper than reflow; `transform`/`opacity` can skip even paint and run on the compositor.

**Why It Matters:** Knowing which properties trigger reflow vs repaint vs composite is how you keep animations at 60fps.

Related note: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]

### Layout Thrashing

**Plain English:** Making the browser recompute layout over and over in a loop.

**Technical Meaning:** Alternating layout writes and layout-dependent reads so each read forces a synchronous reflow. Fixed by batching all reads, then all writes.

**Why It Matters:** A textbook performance footgun hidden inside innocent-looking measurement loops.

Related note: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]

### Event Delegation

**Plain English:** One listener on a parent handling events for many children.

**Technical Meaning:** Attach a listener to an ancestor and use event bubbling plus `event.target.closest()` to identify the originating descendant. Works for dynamically added elements; one listener instead of thousands.

**Why It Matters:** The mechanism React's synthetic event system uses internally, and the right pattern for dynamic lists/tables.

Related note: [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]]

### Passive Listener

**Plain English:** A scroll/touch listener that promises not to block scrolling.

**Technical Meaning:** `addEventListener(type, fn, { passive: true })` guarantees the handler won't call `preventDefault()`, so the browser can start compositor-driven scrolling immediately instead of waiting for JavaScript.

**Why It Matters:** Removes scroll jank; modern browsers make touch/wheel listeners passive by default, which silently broke old preventDefault-based code.

Related note: [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]

### Same-Origin Policy

**Plain English:** A browser rule stopping one site's scripts from reading another site's responses.

**Technical Meaning:** Scripts may send cross-origin requests but cannot read the responses (or touch cross-origin DOM/storage) unless explicitly permitted. Origin = scheme + host + port.

**Why It Matters:** It protects the *user* (a malicious page can't read your bank data using your session). CORS is the opt-out, not the blocker.

Related note: [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]]

### Preflight (CORS)

**Plain English:** A permission-check request the browser sends before certain cross-origin requests.

**Technical Meaning:** An automatic `OPTIONS` request asking the server whether the actual method and headers are allowed; sent for non-"simple" requests (JSON content type, custom headers, PUT/DELETE). The real request proceeds only if the preflight passes.

**Why It Matters:** Explains why switching a body to `application/json` suddenly triggers `OPTIONS` requests, and why CORS fixes live server-side.

Related note: [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]]

### ETag

**Plain English:** A version fingerprint for a cached response.

**Technical Meaning:** A response header identifying a resource version; on revalidation the client sends `If-None-Match: "<etag>"` and the server returns `304 Not Modified` (no body) if unchanged.

**Why It Matters:** The revalidation half of HTTP caching — cheap freshness checks that save bandwidth.

Related note: [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]

### CSP (Content Security Policy)

**Plain English:** A header telling the browser which sources may load and run.

**Technical Meaning:** Directives (`script-src`, `connect-src`, `frame-ancestors`…) restrict resource origins and inline execution. Strict CSP uses per-request nonces plus `strict-dynamic`; `script-src` without `'unsafe-inline'` stops injected inline scripts.

**Why It Matters:** Containment for XSS — it limits the damage of an injection that slips past sanitization.

Related note: [[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]

### Prototype Pollution

**Plain English:** Poisoning every object by writing to the shared prototype.

**Technical Meaning:** Attacker-controlled keys like `__proto__` in a recursive merge/set write onto `Object.prototype`, so the injected property appears on every object via the prototype chain.

**Why It Matters:** Corrupts auth checks, config gates, and templates; defended by rejecting `__proto__`/`constructor`/`prototype` keys and validating input shape.

Related note: [[20 - Network and Security/07 - Prototype Pollution and Supply-Chain Basics|Prototype Pollution and Supply-Chain Basics]]

### Structured Clone

**Plain English:** A deep copy the platform makes when moving data between contexts.

**Technical Meaning:** The algorithm behind `structuredClone()`, `postMessage`, and IndexedDB; deep-copies objects, arrays, Map, Set, Date, ArrayBuffer, etc., but not functions, DOM nodes, or class prototypes.

**Why It Matters:** Defines what can cross a worker boundary and why class instances arrive as plain objects.

Related note: [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]

### Transferable

**Plain English:** Handing off ownership of binary data instead of copying it.

**Technical Meaning:** `postMessage(buf, [buf])` moves an ArrayBuffer (or MessagePort, ImageBitmap, OffscreenCanvas) to another context in O(1) and *detaches* it on the sender side, versus O(n) structured-clone copying.

**Why It Matters:** The efficient way to send large binary payloads to a worker without doubling memory.

Related note: [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]

### RSC Payload

**Plain English:** The serialized description of a server-rendered React tree.

**Technical Meaning:** The React Server Components output streamed to the client — a compact representation of rendered Server Components plus references to Client Components — used on client navigation instead of HTML.

**Why It Matters:** It's what a Next.js App Router client navigation fetches and reconciles, and what the Router Cache stores.

Related note: [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]

### Lane (React)

**Plain English:** A priority level for a React update.

**Technical Meaning:** React's scheduling model tags updates with priority lanes (implemented as bitmasks); urgent lanes (clicks, typing) preempt transition lanes (`startTransition`), which can be interrupted and restarted.

**Why It Matters:** The mechanism that lets a transition keep the UI responsive while heavy renders happen in the background.

Related note: [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling Overview]]

### Tearing

**Plain English:** Different parts of one screen showing inconsistent state.

**Technical Meaning:** Under concurrent rendering, an interruptible render can pause while an external store changes, so components read different values in one commit. Prevented by `useSyncExternalStore`.

**Why It Matters:** Why external stores need a dedicated hook rather than `useEffect` + `useState` under concurrent React.

Related note: [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]

### Reconciliation

**Plain English:** How React figures out what changed between renders.

**Technical Meaning:** Diffing the new element tree against the previous with heuristics: different type at a position remounts; same type updates in place; list children match by `key`. Identity (position + type + key) decides whether state and DOM survive.

**Why It Matters:** Explains why index keys corrupt state on reordering and how to reset state deliberately with a key.

Related note: [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]

### Server Action

**Plain English:** A server function you can call from client code.

**Technical Meaning:** An async `"use server"` function; the framework creates an RPC endpoint, so calling it from the client runs it on the server. Arguments/results must be serializable; it works as a `<form action>` with progressive enhancement.

**Why It Matters:** It's a *public endpoint* — must authenticate, authorize, and validate inside — and the App Router's default mutation mechanism.

Related note: [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]

### Revalidation

**Plain English:** Making cached data fresh again.

**Technical Meaning:** Time-based (`revalidate: N` → serve stale, refresh in background = ISR) or on-demand (`revalidateTag`/`revalidatePath` after a mutation). Tags model data dependencies; paths target routes.

**Why It Matters:** The fix for "my mutation doesn't show up" and the lever that makes aggressive caching safe.

Related note: [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]]

### PPR (Partial Prerendering)

**Plain English:** One page that's part static, part dynamic.

**Technical Meaning:** A prerendered static shell served instantly, with dynamic regions (runtime-API reads) wrapped in `<Suspense>` that stream at request time. The Next.js 16 default with Cache Components.

**Why It Matters:** Stops the all-static-or-all-dynamic choice per page — you annotate each region's nature (`use cache` vs Suspense).

Related note: [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]

### Code Unit vs Code Point vs Grapheme

**Plain English:** Three different meanings of "one character."

**Technical Meaning:** A UTF-16 code unit is one 16-bit value (`.length`, indexing); a code point is one Unicode scalar (needs a surrogate pair above U+FFFF; iterated by spread/`for...of`); a grapheme is a user-perceived character (may be several code points — emoji with modifiers, combining accents; segmented by `Intl.Segmenter`).

**Why It Matters:** Why `"😀".length` is 2 and why code-unit slicing corrupts emoji; character limits/truncation should use graphemes.

Related note: [[12 - Advanced Language Concepts/13 - Strings Unicode and Template Literals|Strings, Unicode and Template Literals]]

### IEEE 754 (Double)

**Plain English:** The floating-point format all JS numbers use.

**Technical Meaning:** 64-bit double precision (sign + 11-bit exponent + 52-bit mantissa). Most decimals aren't exactly representable (`0.1 + 0.2 !== 0.3`); integers are exact only up to 2^53−1.

**Why It Matters:** Compare computed floats within `Number.EPSILON`, use BigInt past the safe integer range, and store money as integer cents.

Related note: [[12 - Advanced Language Concepts/12 - Numbers and Floating Point|Numbers and Floating Point]]

### Hidden Class

**Plain English:** The engine's internal description of an object's property layout.

**Technical Meaning:** V8 calls them *maps*, SpiderMonkey *shapes*, JSC *structures*. Objects created with the same properties in the same order share a hidden class, so property reads compile to fixed-offset access. Adding properties in different orders, or `delete`, creates divergent shapes or dictionary mode.

**Why It Matters:** Explains why consistent object shapes (same keys, same order, nullable fields) keep hot code fast.

Related note: [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]

### Inline Cache (Monomorphic / Megamorphic)

**Plain English:** A per-site memory of which object shapes a property access has seen.

**Technical Meaning:** A site that has seen one hidden class is *monomorphic* (one shape check, direct offset read); 2–4 shapes is *polymorphic*; many shapes is *megamorphic*, falling back to generic slow lookup. Optimizing tiers (Maglev, TurboFan) specialize code from IC feedback.

**Why It Matters:** The mechanism behind "keep data shapes stable in hot paths."

Related note: [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]

### Proper Tail Call (PTC)

**Plain English:** Reusing the current stack frame for a call in tail position.

**Technical Meaning:** Specified in ES2015, but only JavaScriptCore (Safari) ships it; V8 and SpiderMonkey removed their implementations over debugging/stack-trace concerns.

**Why It Matters:** Never rely on tail recursion for stack safety — code that works in Safari overflows elsewhere. Classic "in the spec vs shipped in engines" example.

Related note: [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]

### Scavenger / Mark-Compact (Generational GC)

**Plain English:** The cheap frequent collector for new objects and the heavier one for old objects.

**Technical Meaning:** V8 splits the heap into a young generation (minor GC via the Scavenger, copying few survivors) and an old generation (major GC via Mark-Compact, concurrent/incremental under Orinoco). Objects surviving minor GCs get promoted.

**Why It Matters:** Short-lived allocations are cheap; churning long-lived references and accidental reachability are what hurt.

Related note: [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]

### WinterTC

**Plain English:** The standards body making server runtimes agree on web APIs.

**Technical Meaning:** Ecma TC55 (formerly the WinterCG community group), which standardizes the *Minimum Common Web API* — the subset of web platform APIs (`fetch`, `URL`, streams, `TextEncoder`, timers, `crypto`) that Node.js, Deno, Bun, and edge runtimes implement for interoperability.

**Why It Matters:** Why the same fetch code runs in browser, server, and edge — and why "host API" no longer means "browser-only."

Related note: [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]]

### Element (React)

**Plain English:** A small immutable object describing what React should render.

**Technical Meaning:** JSX or `createElement` creates an object with a `type`, `props`, `key`, and React-owned metadata. It is a description, not a DOM node or a component instance; reconciliation matches new elements to existing fibers.

**Why It Matters:** Explains why JSX creation does no DOM work and why type/key/position decide whether component state survives.

Related note: [[21 - React Internals and Patterns/15 - Elements JSX and Component Identity|Elements JSX and Component Identity]]

### Fiber

**Plain English:** React's persistent internal record for one mounted component or host node.

**Technical Meaning:** A fiber is a linked unit of render work that retains state, effects, and links to child/sibling/parent work. React can build a work-in-progress fiber tree, pause it, abandon it, and atomically commit the finished result.

**Why It Matters:** Makes component “instances,” interruptible rendering, and state preservation concrete without treating internal field names as application APIs.

Related note: [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling Overview]]

### Synthetic Event

**Plain English:** The normalized event object React gives an event handler.

**Technical Meaning:** React listens at its root boundary (with exceptions), wraps the native browser event, and dispatches capture/bubble handlers through the React tree. `nativeEvent` exposes the underlying DOM event; pooling was removed in React 17.

**Why It Matters:** Explains native/React listener ordering, why `persist()` is obsolete, and why propagation debugging starts with attachment points.

Related note: [[21 - React Internals and Patterns/16 - Synthetic Events and Portals|Synthetic Events and Portals]]

### Portal (React)

**Plain English:** React content placed in a different DOM container without leaving its React parent tree.

**Technical Meaning:** `createPortal(children, domNode)` changes physical DOM placement, while context and synthetic-event bubbling continue through the same React fiber ancestry.

**Why It Matters:** The key to debugging modals, tooltips, and click-outside logic where DOM containment and React propagation disagree.

Related note: [[21 - React Internals and Patterns/16 - Synthetic Events and Portals|Synthetic Events and Portals]]

### Effect Event

**Plain English:** An effect-fired callback that always reads the latest props and state without itself becoming reactive.

**Technical Meaning:** `useEffectEvent` returns a function callable only from an Effect or another Effect Event in its owner component or Hook. It must not appear in dependency arrays or be passed to other components or Hooks.

**Why It Matters:** Separates non-reactive event logic (such as a connection notification) from the dependencies that should actually restart the Effect.

Related note: [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]]

### Activity (React)

**Plain English:** A React 19.2 component that hides a subtree without discarding its state.

**Technical Meaning:** `<Activity mode="hidden">` keeps state and DOM available, unmounts effects, and deprioritizes updates; switching back to `visible` remounts effects and resumes normal work.

**Why It Matters:** A deliberate middle ground between conditional rendering (state loss) and CSS hiding (effects continue running).

Related note: [[21 - React Internals and Patterns/10 - React 19|React 19]]

### Virtual DOM

**Plain English:** The JavaScript element-tree description React compares before changing the browser DOM.

**Technical Meaning:** React re-runs components to create new element objects, reconciles that output against the previous tree, and commits the required DOM mutations. The description/diff is overhead compared with perfect manual updates, but enables a declarative programming model.

**Why It Matters:** Corrects the folklore that the virtual DOM is inherently fast and focuses performance reasoning on render, commit, and paint costs.

Related note: [[21 - React Internals and Patterns/14 - Why React Exists|Why React Exists]]

### Fine-grained Reactivity

**Plain English:** A model where state tracks the computations or bindings that read it so updates can be highly targeted.

**Technical Meaning:** Solid signals directly notify dependent bindings; Svelte compiles reactive invalidation from runes; Vue tracks dependencies to schedule updates and commonly patches VDOM within an updated component. These are related models, not interchangeable implementation details.

**Why It Matters:** Lets you compare “signals versus VDOM” as a concrete work-model tradeoff instead of framework tribalism.

Related note: [[21 - React Internals and Patterns/14 - Why React Exists|Why React Exists]]

## Terms from Modules 23–25

### Structural Typing

**Plain English:** A value fits a type when it has the required shape, regardless of what it was declared as.

**Technical Meaning:** TypeScript checks compatibility by comparing members, not nominal identity; any object with the right properties is assignable. Types are erased at emit, so this is a compile-time relation only.

**Why It Matters:** Explains why extra properties usually pass, why two independently-defined shapes interoperate, and why "the type says so" proves nothing about runtime data.

Related note: [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]]

### Type Erasure

**Plain English:** Types disappear before the code runs.

**Technical Meaning:** The emitted JavaScript contains no type information (`enum`/`namespace` excepted as runtime syntax). Annotations and assertions cannot inspect or reject runtime values.

**Why It Matters:** The root reason `as User` on a fetch result is a claim, not a check — and why untrusted boundaries need runtime validation.

Related note: [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|unknown, Runtime Validation and Boundaries]]

### Narrowing

**Plain English:** The compiler shrinking a union type after seeing runtime evidence.

**Technical Meaning:** Control-flow analysis refines a value's type through `typeof`, `in`, equality checks, discriminant fields, and user-defined type predicates/assertion functions.

**Why It Matters:** The mechanism behind discriminated-union state modeling and safe handling of `unknown`.

Related note: [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]

### Discriminated Union

**Plain English:** A set of variants sharing one literal tag field that identifies each variant.

**Technical Meaning:** A union whose members carry a common property with distinct literal types (`kind: "loading" | "error" | ...`); switching on the tag narrows to the exact member, and a `never` default proves exhaustiveness.

**Why It Matters:** Makes impossible UI states unrepresentable — the antidote to `isLoading`/`error`/`data` boolean soup.

Related note: [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]

### Variance

**Plain English:** The rules for when a function type may stand in for another.

**Technical Meaning:** Under `strictFunctionTypes`, parameters are contravariant (a handler must accept at least what it will receive), returns covariant; method-shorthand signatures remain bivariant by design.

**Why It Matters:** Explains why a `MouseEvent` handler can't serve where an `Event` handler is expected, and why callback APIs should use property-style signatures.

Related note: [[23 - TypeScript Deep Dive/07 - Function Types Overloads and Variance|Function Types, Overloads and Variance]]

### satisfies

**Plain English:** Check an expression against a type without changing its inferred type.

**Technical Meaning:** `expr satisfies T` validates assignability while the expression keeps its own (usually narrower) inferred type, unlike an annotation which widens to `T`.

**Why It Matters:** The tool for validated-but-precise config objects, route maps, and derived unions.

Related note: [[23 - TypeScript Deep Dive/02 - Inference Widening and satisfies|Inference, Widening and satisfies]]

### Test Double (Stub vs Mock)

**Plain English:** A stand-in for something real in a test.

**Technical Meaning:** A stub supplies canned state for outcome assertions; a mock records interactions for call assertions. Every double removes its target from the tested surface and substitutes an assumption.

**Why It Matters:** Over-mocking your own code produces green suites over broken apps; the legitimate seams are nondeterminism, the network edge, and external effects.

Related note: [[24 - Testing and Quality/10 - Mocking Seams and False Confidence|Mocking: Seams and False Confidence]]

### Deterministic Test

**Plain English:** A test whose result depends only on its inputs, never on timing or machine speed.

**Technical Meaning:** Achieved by owning time (fake timers), orchestrating async explicitly (resolving promises in chosen order), and replacing sleeps with condition-based waits (`findBy`, `waitFor`, web-first assertions).

**Why It Matters:** Flaky tests corrode the whole suite's signal; determinism is what makes race-condition and cancellation fixes provable.

Related note: [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Timers, Races, Cancellation and Deterministic Tests]]

### Web-First Assertion

**Plain English:** An assertion that keeps re-checking the page until it becomes true or times out.

**Technical Meaning:** Playwright's `await expect(locator).toHaveText(...)` re-queries the locator and retries — a convergence claim matching async UI, versus a one-shot snapshot comparison of an extracted value.

**Why It Matters:** The single biggest anti-flake lever in E2E tests.

Related note: [[24 - Testing and Quality/07 - Playwright Workflows|Playwright Workflows]]

### Accessibility Tree

**Plain English:** The parallel structure of roles, names, and states that assistive technology reads instead of pixels.

**Technical Meaning:** The browser derives it from DOM semantics and ARIA attributes; each node exposes a role, computed accessible name (accname algorithm), optional description, and states.

**Why It Matters:** All accessibility work is mechanically "getting the right things into this tree" — and devtools can show you exactly what's there.

Related note: [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA: Roles, Names and States]]

### Accessible Name

**Plain English:** What a control is called when announced.

**Technical Meaning:** Computed by priority: `aria-labelledby` → `aria-label` → native mechanisms (label, text content, alt) → title. `aria-label` overrides visible text.

**Why It Matters:** Unnamed icon buttons announce as just "button"; diverging visible/accessible names break voice control.

Related note: [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA: Roles, Names and States]]

### Live Region

**Plain English:** A DOM area whose content changes get announced even though focus is elsewhere.

**Technical Meaning:** `aria-live="polite"`/`role="status"` queues announcements; `assertive`/`role="alert"` interrupts. The region must exist before the message; mutations to its content trigger the announcement.

**Why It Matters:** The mechanism that makes async UI — loading, results, errors, toasts — perceivable without sight.

Related note: [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions, Loading States and Announcements]]

### Focus Trap

**Plain English:** Keeping Tab cycling inside an overlay while it's open.

**Technical Meaning:** Part of the modal contract: focus in on open, trapped while open, background inert (unfocusable and hidden from AT), Escape closes, focus restored to the trigger. `<dialog>.showModal()` implements it natively.

**Why It Matters:** Without it keyboard users escape into a dimmed page they can't see; without restore they're dumped to the top of the document.

Related note: [[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|Dialogs, Menus, Popovers and Focus Traps]]

### Roving Tabindex

**Plain English:** Making a composite widget one tab stop with arrow-key navigation inside.

**Technical Meaning:** The active item holds `tabindex="0"`, all siblings `-1`; arrow keys move both the tabindex and DOM focus. Specified per widget by the WAI-ARIA Authoring Practices.

**Why It Matters:** A 20-item toolbar must not be 20 tab stops; this is how tabs, menus, and grids stay keyboard-usable.

Related note: [[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|Keyboard Interaction and Focus Management]]

### updateTag vs revalidateTag (Next 16)

**Plain English:** Two ways to tell Next.js that tagged cached data changed — one immediate, one lazy.

**Technical Meaning:** `updateTag(tag)` (Server Actions only) expires and refreshes so the actor reads their own write; `revalidateTag(tag, "max")` marks stale and serves stale-while-revalidate; the single-argument form is deprecated in Next 16. `refresh()` re-renders the client router without invalidating any tagged data.

**Why It Matters:** Choosing wrong produces either stale reads after a user's own mutation or unnecessary blocking refreshes.

Related note: [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]]

## Review Drill

- [ ] Pick 10 terms and explain each in one sentence.
- [ ] For each term, name the exact mechanism.
- [ ] For each term, name one frontend bug or production decision.
- [ ] Pick 5 terms and write code that demonstrates the behavior.
- [ ] Revisit any term where your answer used vague wording.

## Sources

- ECMAScript Language Specification: https://tc39.es/ecma262/
- HTML Living Standard event loops and web application APIs: https://html.spec.whatwg.org/multipage/webappapis.html
- MDN JavaScript reference and guide: https://developer.mozilla.org/en-US/docs/Web/JavaScript
- MDN Promise reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise
- MDN AbortController reference: https://developer.mozilla.org/en-US/docs/Web/API/AbortController
- React `useEffect` reference: https://react.dev/reference/react/useEffect
- React `useEffectEvent` reference: https://react.dev/reference/react/useEffectEvent
- React Activity reference: https://react.dev/reference/react/Activity
- React Server Components reference: https://react.dev/reference/rsc/server-components
- Solid fine-grained reactivity: https://docs.solidjs.com/advanced-concepts/fine-grained-reactivity
- Svelte runes: https://svelte.dev/docs/svelte/what-are-runes
- Vue reactivity in depth: https://vuejs.org/guide/extras/reactivity-in-depth.html
- Next.js Server and Client Components docs: https://nextjs.org/docs/app/getting-started/server-and-client-components
- web.dev RAIL performance model: https://web.dev/articles/rail
- TypeScript Handbook: https://www.typescriptlang.org/docs/handbook/intro.html
- Next.js revalidateTag / updateTag references: https://nextjs.org/docs/app/api-reference/functions/revalidateTag
- Playwright auto-waiting and assertions: https://playwright.dev/docs/actionability
- Testing Library guiding principles: https://testing-library.com/docs/guiding-principles/
- WAI-ARIA 1.2 and Authoring Practices: https://www.w3.org/WAI/ARIA/apg/
- Accessible Name and Description Computation: https://www.w3.org/TR/accname-1.2/

## Related Notes

- [[00 - Start Here|Start Here]]
- [[01 - Roadmap|Roadmap]]
- [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[05 - this Binding/01 - What is this|What is this]]
- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]

## Terms from Modules 30–31

### Cache-Aside (Lazy Loading)

**Plain English:** Check the cache; on a miss, read the database, put it in the cache, and return it.

**Technical Meaning:** The default caching pattern — the application (not the cache) owns the read-through logic, so only requested data is cached. Contrast write-through (write cache+DB synchronously, fresh reads/slow writes) and write-behind (write cache, flush to DB async, fast writes/loss risk).

**Why It Matters:** The one caching pattern to remember; its client twin is a query cache (React Query) with the component as the app.

Related note: [[30 - Backend System Design/05 - Caching|Caching]]

### Cache Stampede (Thundering Herd)

**Plain English:** A popular cached value expires and thousands of requests all miss and rebuild it at once, hammering the database.

**Technical Meaning:** Fixed with request coalescing (single-flight — one request rebuilds, others wait) and cache warming / probabilistic early expiration.

**Why It Matters:** The server-side version of firing duplicate requests; single-flight is the same idea as client request deduplication.

Related note: [[30 - Backend System Design/05 - Caching|Caching]]

### Consistent Hashing

**Plain English:** A way to spread keys across nodes so adding or removing a node moves only a small fraction of them.

**Technical Meaning:** Keys and nodes are hashed onto a ring; a key belongs to the next node clockwise. Adding a node relocates only ~1/N of keys (vs modulo hashing, which remaps almost everything). Virtual nodes even out distribution.

**Why It Matters:** Why distributed caches, Cassandra, and DynamoDB rebalance without mass data movement.

Related note: [[30 - Backend System Design/06 - Sharding and Consistent Hashing|Sharding and Consistent Hashing]]

### CAP Theorem

**Plain English:** During a network partition you must choose between staying consistent or staying available — not both.

**Technical Meaning:** Consistency (every read sees the latest write) vs Availability (every request gets a response) under Partition. Without a partition you get both; real systems pick a consistency *level* (strong, read-your-writes, eventual) per feature.

**Why It Matters:** Eventual consistency is the same shape as optimistic UI — a deliberate window where the client and server disagree, then reconcile.

Related note: [[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]]

### Cursor vs Offset Pagination

**Plain English:** Cursor pagination points at a specific record ("everything after this"); offset pagination counts from the start ("skip 40").

**Technical Meaning:** Offset (`?offset=40&limit=20`) is simple and allows page jumps but drifts (duplicates/skips) when rows are inserted/deleted mid-paging. Cursor (`?cursor=<opaque>`) is stable under concurrent inserts but can't jump to an arbitrary page.

**Why It Matters:** One API contract with two consumers — the backend prefers cursors for index stability, the frontend for jitter-free infinite scroll.

Related note: [[30 - Backend System Design/03 - API Design|API Design]]

### Idempotency Key

**Plain English:** A token that lets a retried write be recognized so it isn't applied twice.

**Technical Meaning:** POST/create operations aren't naturally idempotent; a client-supplied key lets the server dedupe retries after a dropped response and return the original result.

**Why It Matters:** The server-side counterpart to a client double-submit guard — same problem, different scale.

Related note: [[30 - Backend System Design/03 - API Design|API Design]]

### Sharding

**Plain English:** Splitting data across multiple database instances so no single one holds it all.

**Technical Meaning:** Horizontal partitioning across machines by a shard key that must spread load and keep common queries single-shard. Three strategies: hash-based (even spread, no range scans), range-based (fast ranges but hot-tail risk), directory/lookup-based (flexible, extra hop). Costs: hot spots, cross-shard queries (scatter-gather), cross-shard consistency. Reach for replicas and caching first.

**Why It Matters:** Premature sharding is a top interview mistake — modern single nodes hold multi-TB, so most datasets don't need it yet.

Related note: [[30 - Backend System Design/06 - Sharding and Consistent Hashing|Sharding and Consistent Hashing]]

### LSM Tree vs B-Tree

**Plain English:** Two index shapes — B-Trees are read/range-friendly; LSM trees are write-optimized.

**Technical Meaning:** B-Tree: sorted balanced tree, point + range queries, write cost to maintain. LSM: buffer writes in memory, flush sorted files, compact in background (Cassandra, RocksDB); reads may check several files, sped by Bloom filters.

**Why It Matters:** Explains the read/write/space tradeoff behind a store, and why search (inverted index) is eventually consistent.

Related note: [[30 - Backend System Design/08 - Indexing and Storage Engines|Indexing and Storage Engines]]

### Access Patterns (the seven)

**Plain English:** The recurring problem shapes most backend designs are built from.

**Technical Meaning:** Real-time updates, dealing with contention, multi-step processes, scaling reads, scaling writes, handling large blobs, managing long-running tasks. The backend analog of RADIO's optimization phase.

**Why It Matters:** Naming the pattern structures a deep dive and reveals a system's failure modes; contention and real-time are your frontend bugs one scale up.

Related note: [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]]

### Valkey

**Plain English:** An open-source fork of Redis, widely offered as the managed "Redis-compatible" engine on major clouds.

**Technical Meaning:** After Redis relicensed (BSD → dual RSALv2/SSPLv1, March 2024), the **Linux Foundation** (not CNCF) launched Valkey (BSD-3, backed by AWS, Google, Oracle) from Redis 7.2.4; Redis 8 (May 2025) later added an OSI-approved AGPLv3 option. Wire-compatible with Redis.

**Why It Matters:** Say "Redis-compatible" — it signals you track the ecosystem split rather than assuming one vendor.

Related note: [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]]

### SOLID

**Plain English:** Five object-oriented design principles for code that's cohesive and easy to change.

**Technical Meaning:** Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion. Each fixes a specific smell (god-object, growing switch, unsafe subtype, fat interface, hard-wired dependency).

**Why It Matters:** The vocabulary for *why* a refactor is better — and you already apply it (SRP as container/presentational, DIP as injected services).

Related note: [[31 - Low Level Design/02 - Design Principles|Design Principles]]

### Composition over Inheritance

**Plain English:** Build behavior by combining small pieces rather than subclassing.

**Technical Meaning:** Inheritance couples a subclass to a parent's implementation and forces one rigid hierarchy; when behavior varies on independent axes it explodes combinatorially. Composition injects collaborators (the Strategy pattern), staying flexible and swappable at runtime.

**Why It Matters:** Why React composes components and hooks instead of subclassing a base `Button`.

Related note: [[31 - Low Level Design/03 - OOP Concepts|OOP Concepts]]

### Strategy / Observer / Factory / Builder / State

**Plain English:** The five design patterns worth knowing — most of which you already use on the frontend.

**Technical Meaning:** Strategy (swap an algorithm behind an interface), Observer (subscribers react to changes), Factory (create the right object without the caller choosing), Builder (assemble a complex object stepwise), State (behavior by mode as an explicit machine). Use one only when the problem calls for it; forcing a pattern is over-engineering.

**Why It Matters:** Observer is `useSyncExternalStore`; Strategy is a `renderItem` prop; State replaces boolean soup with a discriminated union.

Related note: [[31 - Low Level Design/04 - Design Patterns|Design Patterns]]

### Concurrency Primitives (and how JS differs)

**Plain English:** The classic tools for coordinating threads — and how the toolkit changes in JavaScript.

**Technical Meaning:** Atomics, mutexes/locks, semaphores, condition variables, blocking queues, addressing correctness/coordination/scarcity. JS is single-threaded (event loop), so *low-level* shared-memory races (torn reads, lost `count++`) can't occur — but a critical section spanning an `await` still needs mutual exclusion, because two async tasks can interleave. True parallelism uses Web Workers (message passing, no shared memory); the exceptions are SharedArrayBuffer + Atomics (needs cross-origin isolation) and the Web Locks API (`navigator.locks`) for cross-tab exclusion.

**Why It Matters:** Frontend race fixes are cancellation/sequence checks for last-write-wins, but an async lock or promise-queue for serialize-this-section — not "no locks needed."

Related note: [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]]

### Read-Through Cache

**Plain English:** A cache that fetches from the database itself on a miss, so the app only ever talks to the cache.

**Technical Meaning:** The counterpart to write-through/write-behind — the cache (not the app) owns the read path. CDNs work this way. Contrast cache-aside, where the *application* populates the cache on a miss.

**Why It Matters:** Its client twin is the HTTP cache you configure with headers — the browser fetches and caches for you.

Related note: [[30 - Backend System Design/05 - Caching|Caching]]

### PACELC

**Plain English:** CAP's missing half — even when the network is fine, you still trade latency against consistency.

**Technical Meaning:** If Partitioned, choose Availability or Consistency; Else (normal operation), choose Latency or Consistency. Strongly-consistent replication makes every write wait for acks (higher latency), so async-replicated stores trade consistency for latency all the time. DynamoDB/Cassandra are PA/EL; a strongly-consistent store is PC/EC.

**Why It Matters:** Naming PACELC shows you know CAP only describes the (rare) partition case — the replica-lag window most systems have exists with no partition at all.

Related note: [[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]]

### Quorum (R + W > N)

**Plain English:** Tuning consistency with three numbers so a read is guaranteed to see the latest write.

**Technical Meaning:** With N replicas, W write-acknowledgements, and R read-replicas consulted, R + W > N forces the read set to overlap the write set — so the read touches a copy holding the newest acknowledged write. R + W ≤ N gives lower latency/higher availability but only eventual consistency.

**Why It Matters:** The dial behind "tunable consistency" in Cassandra/DynamoDB; the concrete mechanism under the CAP/PACELC choice.

Related note: [[30 - Backend System Design/07 - CAP and Consistency|CAP and Consistency]]

### Presigned URL

**Plain English:** A short-lived signed link that lets the browser upload/download directly to object storage.

**Technical Meaning:** The API issues a signed S3 URL; the client transfers bytes straight to storage (bypassing app servers), then tells the API the object key. Validation/virus-scanning move to async workers.

**Why It Matters:** Why an upload widget gets a presigned URL instead of POSTing the file through your API — the "Handling Large Blobs" access pattern.

Related note: [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]]

### Saga / Compensating Action

**Plain English:** A multi-step workflow split into local steps, each with an undo, so a late failure rolls back the earlier ones.

**Technical Meaning:** You can't wrap a cross-service transaction in one ACID commit, so a saga runs local transactions and, on failure at step N, runs compensating actions for steps N-1…1 (semantic rollback). Coordinated by **orchestration** (a central driver — easy to trace, one bottleneck) or **choreography** (services react to each other's events on a durable log — no central point, harder to trace). Every step must be idempotent.

**Why It Matters:** The standard answer to "how do payments/order-fulfillment stay consistent across services."

Related note: [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]]

### API Gateway / BFF

**Plain English:** The single front door in front of your services — and its frontend cousin, a Backend-for-Frontend.

**Technical Meaning:** A gateway centralizes routing, auth, TLS termination, and rate limiting. A BFF is a per-client API layer (often a Next.js route handler) that aggregates services and returns exactly the shape a screen needs; it can speak REST to the browser while calling services over gRPC.

**Why It Matters:** Why the browser talks to one purpose-built endpoint instead of fanning out to many services.

Related note: [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]]

### Kafka (partition / KRaft)

**Plain English:** A durable, append-only log for streaming events between producers and consumers.

**Technical Meaning:** Topics split into partitions; ordering is guaranteed only *within* a partition, so events you need ordered must share a key. Since Kafka 4.0 (2025) it runs on built-in KRaft (Raft) for metadata instead of ZooKeeper.

**Why It Matters:** Explains out-of-order notifications (spread across partitions) and how backends decouple/fan-out work your UI reacts to.

Related note: [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]]

### DynamoDB / Cassandra / Elasticsearch

**Plain English:** Three specialized stores you'll meet behind the APIs you consume.

**Technical Meaning:** DynamoDB — managed key-value/document, partition+sort key, tunable read consistency, modeled around access patterns. Cassandra — masterless wide-column LSM store for write-heavy, always-on, query-driven data (one table per query, no joins). Elasticsearch — distributed search over an inverted index; near-real-time, so a search layer, not a system of record.

**Why It Matters:** Naming the store tells you its guarantees — why search lags a write, why a feed is cursor-paginated, why some queries aren't offered.

Related note: [[30 - Backend System Design/11 - Deep-Dive Technologies|Deep-Dive Technologies]]

### KISS / DRY / YAGNI

**Plain English:** The general design maxims that sit alongside SOLID and keep it from being over-applied.

**Technical Meaning:** Keep It Simple (prefer the simplest thing that works); Don't Repeat Yourself (one source of truth per piece of knowledge — but don't over-abstract things that merely look alike); You Aren't Gonna Need It (don't build for imagined future requirements).

**Why It Matters:** SOLID applied speculatively becomes its own smell — these are the check against needless interfaces and indirection.

Related note: [[31 - Low Level Design/02 - Design Principles|Design Principles]]

### Dependency Injection vs DIP

**Plain English:** DIP is a principle about which way dependencies point; injection is one technique for wiring them.

**Technical Meaning:** DIP: high-level policy and low-level detail both depend on an abstraction the *high-level* module owns, so the arrow points toward policy. Dependency injection just supplies the concrete implementation at runtime — you can inject and still violate DIP (if the low-level module dictates the interface), and satisfy DIP without a DI container.

**Why It Matters:** A classic senior probe ("difference between DIP and DI?") that conflation gives away.

Related note: [[31 - Low Level Design/02 - Design Principles|Design Principles]]

### Singleton

**Plain English:** A single shared global instance — convenient, and usually a trap.

**Technical Meaning:** It's effectively global mutable state: it hides dependencies (breaking DIP) and makes tests share state. In JS a module is already a singleton, so prefer injecting a shared instance over enforcing one.

**Why It Matters:** The one pattern to be wary of — reach for injection first.

Related note: [[31 - Low Level Design/04 - Design Patterns|Design Patterns]]

### Deadlock / Livelock / Starvation

**Plain English:** The three ways lock-based coordination goes wrong.

**Technical Meaning:** Deadlock — two holders each wait on a lock the other holds (fix: lock ordering or timeouts). Livelock — parties keep reacting to each other and make no progress (busy but stuck). Starvation — one party never wins the resource (fix: fair scheduling).

**Why It Matters:** Standard interview follow-ups the moment you mention locks.

Related note: [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]]

### Optimistic vs Pessimistic Locking

**Plain English:** Lock-first-then-act, versus act-and-commit-only-if-nothing-changed.

**Technical Meaning:** Pessimistic locks the resource before acting (safe, lower throughput under contention). Optimistic reads a version/timestamp and commits only if unchanged, retrying on conflict (compare-and-swap; better under low contention).

**Why It Matters:** Optimistic locking is the direct sibling of the client's "is this response still the latest request?" guard.

Related note: [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]]

### Web Locks API

**Plain English:** A real mutex the browser ships, scoped to one origin's tabs and workers.

**Technical Meaning:** `navigator.locks.request(name, cb)` grants named, exclusive (or shared) mutual exclusion across an origin's tabs, windows, and workers; the lock auto-releases when the callback resolves or the holder closes. Baseline across browsers since 2022.

**Why It Matters:** The right tool for "only one tab runs the background sync / holds the leader role" — proof that "JS has no locks" is wrong.

Related note: [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]]

### Async Mutual Exclusion

**Plain English:** Even single-threaded JS needs to serialize a section that spans an `await`.

**Technical Meaning:** A check-then-act like "if no request in flight, start one" can be entered twice, because the event loop runs other tasks while you're suspended at the `await`. Serialize with a promise queue / async-mutex, or dedupe on the in-flight promise. Cancellation/sequence checks handle last-write-wins races, not this.

**Why It Matters:** The nuance behind "single-threaded doesn't mean no coordination" — a token-refresh stampede is the canonical case.

Related note: [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]]

## Terms from Module 29 (Frontend System Design)

### RADIO Framework

**Plain English:** The repeatable structure for "design X" frontend interviews.

**Technical Meaning:** Requirements → Architecture → Data model → Interface (component + network APIs) → Optimizations, time-boxed, with every decision traced back to a requirement. The frontend cousin of the backend delivery framework.

**Why It Matters:** Turns an open-ended design prompt into a covered checklist so you don't forget races, caching, a11y, or failure states.

Related note: [[29 - Frontend System Design/01 - The Frontend System Design Framework|The Frontend System Design Framework]]

### Core Web Vitals (LCP / INP / CLS)

**Plain English:** Google's three field metrics for loading, responsiveness, and visual stability.

**Technical Meaning:** LCP < 2.5s (largest contentful paint), INP < 200ms (interaction to next paint — replaced FID in March 2024), CLS < 0.1 (cumulative layout shift), each graded at the 75th percentile of real users.

**Why It Matters:** The scoreboard you rank frontend performance work against; INP is the one people miss.

Related note: [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]

### Rendering Strategies (CSR / SSR / SSG / ISR / Streaming / RSC)

**Plain English:** Where and when a page's HTML is produced — chosen per route.

**Technical Meaning:** CSR (browser), SSR (per request), SSG (build time), ISR (static + revalidate), streaming SSR (shell first, stream the rest), RSC (server components ship no client JS). Decide by SEO need, personalization, freshness, and interactivity — not one mode per app.

**Why It Matters:** App-level design questions are half-won in the rendering decision; it drives SEO, first paint, and cost.

Related note: [[29 - Frontend System Design/05 - Rendering Strategies for Design|Rendering Strategies for Design]]

### Optimistic UI

**Plain English:** Show the expected result immediately, then reconcile with the server.

**Technical Meaning:** Apply the change locally before the server confirms; on success reconcile, on failure roll back (snapshot restore or inverse patch), cancelling in-flight refetches so a stale response can't clobber it. A deliberate client-side eventual-consistency window.

**Why It Matters:** The client instance of CAP eventual consistency — the screen and server disagree, then converge.

Related note: [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]]

### State Normalization

**Plain English:** Store each entity once by id, and reference it by id everywhere.

**Technical Meaning:** An id-keyed map (`{[id]: entity}`) with lists holding ids gives O(1) updates and one source of truth, so the same entity in a feed and a detail view can't diverge. The client twin of a normalized database.

**Why It Matters:** How you keep a like count consistent across views; over-engineering for small, non-shared lists.

Related note: [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]]

### Service Worker Caching Strategies

**Plain English:** Per-resource rules for what to serve from cache versus network.

**Technical Meaning:** Cache-first (static/app shell), network-first (fresh data, cache fallback), stale-while-revalidate (serve cache, refresh in background). Chosen per resource type, not globally.

**Why It Matters:** The difference between an app that opens offline and one that shows a blank screen.

Related note: [[29 - Frontend System Design/12 - Offline and Resilient UX|Offline and Resilient UX]]

### Background Sync

**Plain English:** A Service Worker API that flushes queued writes once connectivity returns, even after the tab closed.

**Technical Meaning:** Ideal trigger for draining an offline outbox — but Chromium-only (no Safari/Firefox), so treat it as progressive enhancement with a portable fallback (flush on the `online` event and on next launch).

**Why It Matters:** Offline-write support that silently fails for a large user share unless you add the fallback.

Related note: [[29 - Frontend System Design/12 - Offline and Resilient UX|Offline and Resilient UX]]

### Real-Time Transports (WebSocket / SSE / Long Polling)

**Plain English:** The channels for pushing live data, from simplest to most capable.

**Technical Meaning:** Short polling → long polling → SSE (unidirectional, auto-reconnect, native resume) → WebSocket (bidirectional, stateful). The transport doesn't solve ordering, reconnection, or backpressure — you design those.

**Why It Matters:** "Design a real-time X" tests the client concerns, not whether you can name WebSocket.

Related note: [[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]]

### Last-Event-ID

**Plain English:** SSE's built-in resume token so a reconnect replays what you missed.

**Technical Meaning:** When the server sends `id:` on each event, the browser resends it as the `Last-Event-ID` header on auto-reconnect, letting the server replay the gap — resume you'd otherwise hand-build over WebSockets.

**Why It Matters:** Naming the native primitive beats reinventing catch-up logic.

Related note: [[29 - Frontend System Design/13 - Real-Time UI Patterns|Real-Time UI Patterns]]

### Virtual Focus (aria-activedescendant)

**Plain English:** Keep the keyboard in one element while a highlight moves through a list.

**Technical Meaning:** In composite widgets (combobox, grid), real DOM focus stays on the input and the active option is pointed to via `aria-activedescendant`, so the user keeps typing while the screen reader announces the highlighted choice.

**Why It Matters:** The correct pattern for autocomplete/menus — moving real focus would break typing and thrash the screen reader.

Related note: [[29 - Frontend System Design/14 - Accessibility in System Design|Accessibility in System Design]]

### APG Patterns

**Plain English:** The official per-widget accessibility recipes you implement against.

**Technical Meaning:** The WAI-ARIA Authoring Practices Guide specifies roles, states, and the full keyboard model for each widget (combobox, dialog, carousel, grid, tabs…). A modal is `role="dialog"` + `aria-modal` + focus trap/restore; a carousel is a `region` container with `group` slides; a toast is a `status`/`alert` live region — you follow the pattern, not invent one.

**Why It Matters:** Designing to the APG pattern up front means the a11y contract is built in, not retrofitted.

Related note: [[29 - Frontend System Design/14 - Accessibility in System Design|Accessibility in System Design]]

### inert / aria-modal

**Plain English:** How a modal correctly turns off the page behind it.

**Technical Meaning:** `inert` makes the background unfocusable and hidden from assistive tech (native `<dialog>.showModal()` does this via the top layer); `aria-modal="true"` tells AT the rest of the page is inactive. `aria-hidden` alone does *not* stop keyboard focus — you need `inert`.

**Why It Matters:** The difference between a modal that traps focus correctly and one keyboard users can tab out of.

Related note: [[29 - Frontend System Design/15 - Designing a Modal and Dialog System|Designing a Modal and Dialog System]]
