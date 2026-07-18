---
tags: [javascript, interview, strong-mid-level-questions]
module: "15 - Interview Preparation"
priority: important
status: not-started
---

# Strong Mid Level Questions

## Maturity Target

- Priority: #important
- Study time: 150-180 minutes
- Interview signal: can handle deeper follow-ups with accurate terminology and practical judgment.
- Production signal: can reason across JavaScript internals, browser runtime behavior, React behavior, and build tooling.
- Fast track: study Q1, Q2, Q4, Q6, Q8, and Q10 first.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [HTML Living Standard: event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [MDN: Iteration protocols](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Iteration_protocols)
- [MDN: WeakMap](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakMap)
- [React docs: memo](https://react.dev/reference/react/memo)
- [Next.js docs: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)

## How To Answer Strong Questions

Strong mid-level answers do three things:

1. Name the mechanism precisely.
2. Walk through the behavior step by step.
3. Connect the mechanism to a frontend bug, performance tradeoff, or architecture decision.

If you only know the slogan, say the slogan and then reason honestly. Do not invent spec details.

## Q1. Why Can `arrayFromIframe instanceof Array` Be False?

### Model Answer

`instanceof` checks whether `Constructor.prototype` appears in an object's prototype chain. Separate browser realms, such as iframes, have separate global objects and separate intrinsic constructors. An array created inside an iframe has the iframe's `Array.prototype` in its chain, not the parent page's `Array.prototype`.

```js
const iframeArrayCtor = iframe.contentWindow.Array;
const value = new iframeArrayCtor();

console.log(value instanceof Array); // false in the parent realm
console.log(Array.isArray(value)); // true
```

`Array.isArray` is safer across realms because it checks whether the value is actually an array, not whether it was constructed by this realm's `Array` constructor.

### Production Angle

Cross-realm issues appear with iframes, embedded widgets, test environments, browser extensions, and micro-frontends. Prefer platform brand checks such as `Array.isArray` over `instanceof Array`.

Related: [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]

## Q2. Walk Through `[] == ![]`

### Model Answer

The result is `true`.

```js
console.log([] == ![]); // true
```

Step by step:

1. `![]` is evaluated first. Arrays are objects, and all objects are truthy, so `![]` becomes `false`.
2. Now compare `[] == false`.
3. For abstract equality, Boolean is converted to Number: `false` becomes `0`.
4. Now compare `[] == 0`.
5. Object compared to primitive triggers ToPrimitive. `[].toString()` gives `''`.
6. Now compare `'' == 0`.
7. String compared to Number converts string to Number: `Number('')` is `0`.
8. Now compare `0 == 0`, which is `true`.

### Production Angle

Do not rely on abstract equality with mixed types in application logic. The coercion rules are deterministic, but they are rarely what product code wants.

Related: [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]

## Q3. Compare `Object.is`, `===`, And `==`

### Model Answer

`==` can coerce types. `===` does not coerce types. `Object.is` uses SameValue semantics, which differs from `===` for `NaN`, `0`, and `-0`.

```js
console.log(null == undefined); // true
console.log(null === undefined); // false

console.log(NaN === NaN); // false
console.log(Object.is(NaN, NaN)); // true

console.log(0 === -0); // true
console.log(Object.is(0, -0)); // false
```

### Production Angle

React uses `Object.is` for dependency and state comparisons. Most code should use `===`, but React identity reasoning should use `Object.is` as the mental model.

Related: [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]

## Q4. Implement A Custom Iterable

### Model Answer

An iterable has a `[Symbol.iterator]()` method that returns an iterator. An iterator has a `next()` method returning `{ value, done }`. Language features like `for...of`, spread, array destructuring, and `Array.from` consume this protocol.

```ts
class Range implements Iterable<number> {
  constructor(
    private start: number,
    private end: number,
    private step = 1
  ) {}

  [Symbol.iterator](): Iterator<number> {
    let current = this.start;
    const end = this.end;
    const step = this.step;

    return {
      next(): IteratorResult<number> {
        if (current <= end) {
          const value = current;
          current += step;
          return { value, done: false };
        }

        return { value: undefined, done: true };
      },
    };
  }
}

console.log([...new Range(1, 3)]); // [1, 2, 3]
```

### Production Angle

Iterator knowledge explains array destructuring, spread, `Promise.all`, custom lazy data sources, generators, and why some "array-like" objects do not work with `for...of`.

Related: [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]], [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]

## Q5. Why Does `async/await` Not Create Concurrency?

### Model Answer

`async/await` structures Promise continuations. It does not create threads. An async function returns a Promise immediately. When it hits `await`, the rest of the function resumes later through Promise microtask behavior after the awaited value settles. JavaScript code still runs one frame at a time.

```js
async function serial() {
  const a = await fetch('/api/a');
  const b = await fetch('/api/b');
  return [a, b];
}

async function concurrent() {
  const aPromise = fetch('/api/a');
  const bPromise = fetch('/api/b');
  return Promise.all([aPromise, bPromise]);
}
```

The first version starts request B only after A completes. The second starts both requests before awaiting their results.

### Production Angle

Sequential awaits can create client waterfalls. In frontend performance work, starting independent async work early often matters more than micro-optimizing rendering code.

Related: [[08 - Async JavaScript/04 - Async Await|Async Await]], [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]

## Q6. Explain Module Live Bindings

### Model Answer

An ES module import is a live read-only view of the exporting module's binding, not a copied value. If the exporter updates an exported variable, importers observe the new value. The importer cannot reassign the imported binding.

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
console.log(count); // 1
```

### Production Angle

Live bindings explain cyclic module behavior, tree shaking, and why exported mutable state should be used carefully. They also distinguish ESM from CommonJS snapshots and object mutation patterns.

Related: [[10 - Modules/05 - Live Bindings|Live Bindings]], [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]

## Q7. Explain `WeakMap` Memory Behavior

### Model Answer

`Map` holds strong references to keys and values. As long as the map is reachable, its entries keep key objects alive. `WeakMap` holds weak references to object keys. If a key is no longer strongly reachable elsewhere, the garbage collector may collect it and the entry disappears invisibly.

```js
const metadata = new WeakMap();

function attachMetadata(element, value) {
  metadata.set(element, value);
}
```

There is no `WeakMap.prototype.size` and no iteration because garbage collection timing must not become observable.

### Production Angle

Use `WeakMap` for metadata attached to DOM nodes, class instances, or objects you do not own. Use `Map` when you need iteration, size, or strong cache retention with explicit eviction.

Related: [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]], [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]

## Q8. Explain A React Dependency Loop

### Model Answer

A dependency loop often happens when an effect depends on a value whose identity changes every render, and the effect sets state, causing another render.

```tsx
function Feed({ userId }: { userId: string }) {
  const [items, setItems] = React.useState<Item[]>([]);
  const options = { limit: 20 };

  React.useEffect(() => {
    fetchItems(userId, options).then(setItems);
  }, [userId, options]);
}
```

`options` is a new object every render, so React sees the dependency as changed. The fix is to move the object inside the effect or memoize it only if identity must be shared.

```tsx
React.useEffect(() => {
  const options = { limit: 20 };
  fetchItems(userId, options).then(setItems);
}, [userId]);
```

### Production Angle

The mature answer is not "remove options from deps." It is "change the code so options is no longer a reactive dependency."

Related: [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]

## Q9. Explain Hydration Mismatch From `Date`

### Model Answer

Server-rendered HTML and the first client render must match. If render calls `new Date()` or formats time differently between server and browser, the text can differ before React hydrates.

```tsx
function Clock() {
  return <time>{new Date().toLocaleTimeString()}</time>;
}
```

Fix by rendering deterministic initial output and updating after mount, or by passing a server-known timestamp and formatting consistently.

```tsx
function Clock() {
  const [time, setTime] = React.useState<string | null>(null);

  React.useEffect(() => {
    setTime(new Date().toLocaleTimeString());
  }, []);

  return <time>{time ?? 'Loading time'}</time>;
}
```

### Production Angle

Hydration mismatches can create visible flashes and client fallback rendering. They are often caused by nondeterministic render code, not by React being random.

Related: [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]

## Q10. Explain Server/Client Boundary Tradeoffs

### Model Answer

Server Components reduce client JavaScript and can access server resources. Client Components enable interactivity but add browser bundle and hydration work. The `'use client'` directive marks a module boundary; imports under that module are part of the client graph.

```tsx
// Good shape: server page, small client island.
export default async function Page() {
  const product = await getProduct();
  return <BuyBox productId={product.id} />;
}
```

```tsx
'use client';

function BuyBox({ productId }: { productId: string }) {
  const [quantity, setQuantity] = React.useState(1);
  return <button>Add {quantity}</button>;
}
```

### Production Angle

Moving the boundary lower can reduce bundle size, hydration cost, and accidental server-secret leakage. Moving it too low can make integration awkward if many siblings need shared client state. The right answer names the tradeoff.

Related: [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]

## Q11. Explain A Bundle Size Regression Investigation

### Model Answer

First measure the regression with a bundle analyzer. Compare the current build to a known good build. Look for new large dependencies, duplicate versions, incorrect imports, CommonJS entries, dynamic imports that became eager, or client boundaries that pulled server-only code into the browser graph.

```text
Checklist:
- What package changed?
- Did an import switch from per-module to namespace/default?
- Did a Client Component import a large server/static module?
- Did tree shaking fail because of CJS or side effects?
- Can the feature be lazy-loaded?
```

### Production Angle

Bundle regressions are rarely solved by guessing. They are solved by analyzer evidence, ownership of imports, and CI limits for future prevention.

Related: [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]], [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]]

## Q12. Explain A Good "I Do Not Know" Answer

### Model Answer

A strong candidate does not fake certainty. They state what they know, what they are unsure about, and how they would verify.

```text
"I am not fully certain about the exact spec step here. I know this relates to the iterator protocol because spread calls Symbol.iterator. My current hypothesis is that the object is not iterable even though it is array-like. I would verify by checking whether it has a Symbol.iterator method."
```

### Production Angle

This is how real engineering works too: isolate the known mechanism, form a testable hypothesis, and verify before shipping.

Related: [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]]

## Practice Routine

- [ ] Answer Q1-Q12 in two minutes each.
- [ ] For Q2 and Q3, write the exact code output.
- [ ] For Q4, implement the iterable without looking.
- [ ] For Q8-Q10, state the bug, fix, tradeoff, and checklist.
- [ ] Mark any answer that lacks a production consequence for review.

## Related Notes

- [[15 - Interview Preparation/02 - Mid Level Questions|Mid Level Questions]]
- [[15 - Interview Preparation/04 - Senior Style Thinking Questions|Senior Style Thinking Questions]]
- [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]]
- [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]]
- [[18 - Revision Plans/04 - 30 Interview Questions|30 Interview Questions]]
