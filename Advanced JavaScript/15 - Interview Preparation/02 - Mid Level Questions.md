---
tags: [javascript, interview, mid-level-questions]
module: "15 - Interview Preparation"
priority: must-know
status: not-started
---

# Mid Level Questions

## Maturity Target

- Priority: #must-know
- Study time: 120-150 minutes
- Interview signal: can explain core mechanisms under follow-up pressure.
- Production signal: can diagnose bugs involving runtime, async, modules, React, and memory.
- Fast track: answer Q1-Q10 aloud, then write Q4, Q7, and Q9 from memory.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN: Inheritance and the prototype chain](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Inheritance_and_the_prototype_chain)
- [MDN: Promise concurrency](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [React docs: Updating Arrays in State](https://react.dev/learn/updating-arrays-in-state)
- [Next.js docs: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)

## How Mid-Level Questions Are Graded

Interviewers are usually checking four things:

| Signal | What it sounds like |
| --- | --- |
| Accuracy | "The mechanism is..." |
| Traceability | "Step by step, this is what happens..." |
| Practicality | "In frontend code this breaks when..." |
| Judgment | "I would choose this fix because..." |

Do not give only a slogan. Give the mechanism and the consequence.

## Q1. Explain Prototype Lookup

### Strong Answer

Every object has an internal \[\[Prototype\]\] slot pointing to another object or `null`. When reading a property, JavaScript checks the object for an own property first. If not found, it follows the prototype chain until it finds the property or reaches `null`.

```js
const base = {
  greet() {
    return `Hi ${this.name}`;
  },
};

const user = Object.create(base);
user.name = 'Mustafa';

console.log(user.greet()); // "Hi Mustafa"
console.log(user.hasOwnProperty('greet')); // false
```

### Production Bug

Assuming methods are copied to each object can lead to wrong debugging. The method may live on the prototype, and changing the prototype affects all objects that delegate to it.

### Follow-Up

What happens when you assign `user.greet = function () {}`?

Related: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]

## Q2. Explain The 4 Steps Of `new`

### Strong Answer

`new Constructor(args)` creates a new object, sets its internal prototype to `Constructor.prototype`, calls the constructor with `this` bound to that object, and returns the object unless the constructor explicitly returns another non-null object.

```js
function Person(name) {
  this.name = name;
}

const p = new Person('A');
console.log(Object.getPrototypeOf(p) === Person.prototype); // true

function Weird() {
  this.x = 1;
  return { y: 2 };
}

const w = new Weird();
console.log(w.x); // undefined
console.log(w.y); // 2
```

### Production Bug

Returning an object from a constructor can accidentally throw away initialized instance fields. This matters when debugging old constructor-function code or transpiled class output.

### Follow-Up

What happens if `Constructor.prototype` is not an object?

Related: [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]

## Q3. Explain `call`, `apply`, And `bind`

### Strong Answer

All three explicitly control `this` for regular functions. `call` invokes immediately with individual arguments. `apply` invokes immediately with array-like arguments. `bind` returns a new function with bound `this` and optional partial arguments. A bound function's `this` cannot be changed by later `call` or `apply`.

```js
function greet(prefix) {
  return `${prefix}, ${this.name}`;
}

const user = { name: 'Mustafa' };

console.log(greet.call(user, 'Hi')); // "Hi, Mustafa"
console.log(greet.apply(user, ['Hello'])); // "Hello, Mustafa"

const bound = greet.bind(user, 'Welcome');
console.log(bound()); // "Welcome, Mustafa"
```

### Production Bug

Passing a class method as a callback can lose `this`. Fix with binding, an arrow wrapper, or class field syntax depending on the codebase.

### Follow-Up

Why does `bind` return a new function reference, and how can that affect React props?

Related: [[05 - this Binding/05 - call apply bind|call apply bind]], [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]

## Q4. Explain Promise Concurrency Methods

### Strong Answer

All four methods accept an iterable and return a Promise, but their settlement behavior differs.

| Method | Fulfills when | Rejects when | Use case |
| --- | --- | --- | --- |
| `Promise.all` | all fulfill | first rejects | all-or-nothing data |
| `Promise.allSettled` | all settle | never by member rejection | partial batch results |
| `Promise.race` | first settles | first settles rejected | timeout or first result |
| `Promise.any` | first fulfills | all reject with `AggregateError` | redundant sources |

```js
const timeout = new Promise((_, reject) => {
  setTimeout(() => reject(new Error('timeout')), 5000);
});

const response = await Promise.race([
  fetch('/api/report'),
  timeout,
]);
```

### Production Bug

Using `Promise.all` for optional resources can fail the whole UI if one request fails. Use `allSettled` when partial success is acceptable.

### Follow-Up

Why does `Promise.any` reject with `AggregateError`?

Related: [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]

## Q5. Explain Async Error Handling

### Strong Answer

Errors in synchronous code are caught by `try/catch` immediately. Rejections from awaited Promises are also caught by `try/catch` because `await` unwraps the Promise result. But if you start a Promise without `await` or `return`, the rejection escapes that `try/catch`.

```js
async function broken() {
  try {
    fetch('/bad-url').then(() => {
      throw new Error('later');
    });
  } catch (error) {
    // This will not catch the later Promise rejection.
  }
}

async function fixed() {
  try {
    await fetch('/bad-url').then(() => {
      throw new Error('later');
    });
  } catch (error) {
    console.error('caught', error);
  }
}
```

### Production Bug

Unreturned Promises in event handlers, effects, or service functions can become unhandled rejections. In React effects, wrap async logic inside the effect and handle aborts separately.

### Follow-Up

Why does `finally` run after both fulfillment and rejection, and why can that be risky for loading state?

Related: [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]], [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]

## Q6. Explain ES Modules Vs CommonJS

### Strong Answer

ES modules are statically analyzable, always strict, loaded as a module graph, and use live read-only bindings. CommonJS uses runtime `require`, mutable `module.exports`, and is harder to tree-shake because imports are dynamic function calls.

```js
// counter.js
export let count = 0;
export function increment() {
  count += 1;
}

// main.js
import { count, increment } from './counter.js';

console.log(count); // 0
increment();
console.log(count); // 1, live binding
```

### Production Bug

Mixing CJS and ESM can break tree shaking or create confusing default import interop. In frontend bundles, prefer ESM imports from libraries that publish side-effect-aware builds.

### Follow-Up

Why can static ESM imports enable tree shaking but dynamic `require()` cannot?

Related: [[10 - Modules/01 - ES Modules|ES Modules]], [[10 - Modules/02 - CommonJS|CommonJS]], [[10 - Modules/05 - Live Bindings|Live Bindings]]

## Q7. Explain Tree Shaking

### Strong Answer

Tree shaking is build-time dead-code elimination. Bundlers analyze the ESM import/export graph, determine which exports are used, and remove unused code when they can prove removing it is safe.

```js
// Better for tree shaking when the library supports ESM.
import { debounce } from 'some-utility-library';

// Often worse: imports namespace or CJS entry.
import utils from 'some-utility-library';
```

### Production Bug

Bundle size can explode when importing an entire library, using CJS-only dependencies, or importing modules with top-level side effects. Use a bundle analyzer and verify actual output.

### Follow-Up

What does `"sideEffects": false` mean in a package manifest, and why can it be dangerous if wrong?

Related: [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]], [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]]

## Q8. Explain Garbage Collection And Reachability

### Strong Answer

JavaScript engines automatically reclaim memory for objects that are no longer reachable. A mark-and-sweep collector starts from roots such as global objects, the call stack, active closures, and engine internals, marks reachable objects, and collects unmarked objects. A memory leak happens when an object is no longer needed but is still reachable.

```js
function attach() {
  const largeData = new Array(1_000_000).fill('x');

  function onResize() {
    console.log(largeData.length);
  }

  window.addEventListener('resize', onResize);

  return () => window.removeEventListener('resize', onResize);
}
```

### Production Bug

Missing cleanup for listeners, timers, observers, or subscriptions can retain closures and large data. GC cannot collect objects that are still reachable through a listener list.

### Follow-Up

How would you prove this leak using Chrome DevTools heap snapshots?

Related: [[13 - Performance and Memory/01 - Memory Management|Memory Management]], [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]

## Q9. Explain Stale Closures In React

### Strong Answer

Every render creates new lexical bindings. If a callback from an old render runs later, it reads the values from that old render. This is a stale closure. It commonly happens in effects, timers, listeners, and memoized callbacks with missing dependencies.

```tsx
React.useEffect(() => {
  const id = window.setInterval(() => {
    setCount(count + 1);
  }, 1000);

  return () => window.clearInterval(id);
}, []);
```

This interval captures the initial `count`. Fix with a functional update:

```tsx
React.useEffect(() => {
  const id = window.setInterval(() => {
    setCount(prev => prev + 1);
  }, 1000);

  return () => window.clearInterval(id);
}, []);
```

### Production Bug

Autosave, analytics, subscriptions, and hotkeys can act on old props or state if the closure lifetime is wrong.

### Follow-Up

When would a ref be a better stale-closure fix than adding dependencies?

Related: [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

## Q10. Explain React State Immutability

### Strong Answer

React state should be treated as immutable. React compares state with `Object.is`; if you mutate an object and pass the same reference back, React can treat it as unchanged. Immutable updates create new references for changed containers and preserve unchanged branches through structural sharing.

```tsx
// Bug
items.push(nextItem);
setItems(items);

// Fix
setItems(prev => [...prev, nextItem]);
```

### Production Bug

Mutation can cause stale UI, broken memoization, and previous render snapshots changing unexpectedly. It is especially harmful with shared object references and memoized children.

### Follow-Up

Why is deep cloning every update usually worse than structural sharing?

Related: [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]

## Q11. Explain A Race Condition In `useEffect`

### Strong Answer

A race condition happens when multiple async operations are in flight, and an older one finishes after a newer one and updates the same state. React effect cleanup lets you ignore or cancel old work when dependencies change.

```tsx
React.useEffect(() => {
  let ignore = false;

  fetch(`/api/users/${userId}`)
    .then(r => r.json())
    .then(data => {
      if (!ignore) setUser(data);
    });

  return () => {
    ignore = true;
  };
}, [userId]);
```

### Production Bug

Search results, profile pages, and route transitions can show stale data under slow networks. For fetches, `AbortController` can cancel the request instead of only ignoring the result.

### Follow-Up

Why should `catch` and `finally` also be guarded?

Related: [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]], [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]

## Q12. Explain Server And Client Components

### Strong Answer

In Next.js App Router, components are Server Components by default. Server Components render on the server, can fetch server-side data, and do not ship their implementation to the browser. Client Components are marked with `'use client'`; they can use state, effects, event handlers, and browser APIs, but their module graph contributes to client JavaScript and hydration.

```tsx
// Server Component
export default async function Page() {
  const products = await getProducts();
  return <ProductList products={products} />;
}
```

```tsx
// Client Component
'use client';

function FavoriteButton() {
  const [favorite, setFavorite] = React.useState(false);
  return <button onClick={() => setFavorite(v => !v)}>Favorite</button>;
}
```

### Production Bug

Putting `'use client'` too high increases bundle size and hydration work. Reading browser APIs in a Server Component fails. Passing non-serializable data across the boundary can break.

### Follow-Up

Why should the client boundary usually be as low as practical?

Related: [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]

## Q13. Explain Hydration Mismatch

### Strong Answer

Hydration is React attaching interactivity to server-rendered HTML in the browser. A mismatch happens when the first client render produces different output from the server HTML. Common causes are `Date`, `Math.random`, `window`, `localStorage`, invalid HTML nesting, and locale differences during render.

```tsx
function Theme() {
  const [theme, setTheme] = React.useState('light');

  React.useEffect(() => {
    setTheme(localStorage.getItem('theme') ?? 'light');
  }, []);

  return <span>{theme}</span>;
}
```

Server and first client render both start with `light`; the browser-only value updates after hydration.

### Production Bug

Hydration mismatch can cause warnings, visual flashes, and client-side fallback rendering. The best fix is deterministic initial output or server-known values from cookies.

### Follow-Up

When is `suppressHydrationWarning` acceptable?

Related: [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]

## Q14. Explain How You Would Debug A Performance Regression

### Strong Answer

First reproduce and define the metric: slow input, slow route transition, high memory, or large bundle. Then use the right tool: React Profiler for rerenders, Chrome Performance for main-thread work, Memory for leaks, Network for waterfalls, and bundle analyzer for JavaScript size. Fix the measured bottleneck, not the suspected one.

### Production Bug

Adding `useMemo` randomly can hide code smell and add overhead. A mature candidate measures, forms a hypothesis, changes one thing, and verifies.

### Follow-Up

How would you distinguish too many renders from one expensive render?

Related: [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]], [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]

## Practice Routine

- [ ] Answer each question in 60 seconds.
- [ ] For Q4, Q5, Q9, and Q11, write code from memory.
- [ ] For every answer, state one production bug and one fix.
- [ ] For every answer, identify the underlying note you would review if weak.
- [ ] Record one 10-minute mock using Q1, Q6, Q9, Q12, and Q13.

## Related Notes

- [[15 - Interview Preparation/01 - Junior to Mid Questions|Junior to Mid Questions]]
- [[15 - Interview Preparation/03 - Strong Mid Level Questions|Strong Mid Level Questions]]
- [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]]
- [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]]
- [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
