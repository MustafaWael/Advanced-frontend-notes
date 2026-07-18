---
tags: [javascript, functions, higher-order-functions-and-callbacks]
module: "04 - Functions Deep Dive"
priority: must-know
status: not-started
aliases: [HOF, Higher Order Functions]
---

# Higher Order Functions and Callbacks

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can define first-class functions, higher-order functions, callbacks, and synchronous vs asynchronous callback timing.
- Production signal: you can build safe wrappers for logging, auth, retries, event handlers, and React hooks without hiding control flow.
- Dependencies: [[04 - Functions Deep Dive/01 - Function Declarations vs Expressions|Function Declarations vs Expressions]], [[03 - Scope and Variables/05 - Closures|Closures]], [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]

## Source Anchors

- [MDN - First-class function](https://developer.mozilla.org/en-US/docs/Glossary/First-class_Function)
- [MDN - Functions guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions)
- [MDN - Array.prototype.map](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/map)
- [MDN - Array.prototype.reduce](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/reduce)
- [React - useCallback](https://react.dev/reference/react/useCallback)

## 1. Concept

JavaScript functions are first-class values. You can store them in variables, pass them as arguments, return them from other functions, and put them in objects.

A higher-order function is a function that:

- Accepts another function, or
- Returns another function, or
- Both.

A callback is a function passed to another piece of code so it can be called later or during an operation.

```js
const numbers = [1, 2, 3];

const doubled = numbers.map((number) => number * 2);

console.log(doubled); // [2, 4, 6]
```

`map` is the higher-order function. `(number) => number * 2` is the callback.

## 2. Why It Matters

Higher-order functions are not academic in frontend work. They are the shape of most reusable behavior:

- Array transformations.
- Event listeners.
- Promise chains.
- React hooks returning handlers.
- Middleware wrappers.
- Debounce/throttle utilities.
- Retry helpers.
- Authorization wrappers.
- Test spies and mocks.

The production risk is hidden control flow: when does the callback run, with what arguments, with what `this`, and who owns cleanup/error handling?

## 3. Official Mechanism

Functions are objects with callable behavior. Passing a function does not call it. The receiving function decides if, when, and how to call it.

```js
function callTwice(callback) {
  callback("first");
  callback("second");
}

callTwice((label) => {
  console.log(label);
});

// Output:
// first
// second
```

The callback can close over outer variables:

```js
function createPrefixedLogger(prefix) {
  return function log(message) {
    console.log(`${prefix}: ${message}`);
  };
}

const logApi = createPrefixedLogger("api");
logApi("request started"); // "api: request started"
```

## 4. Synchronous vs Asynchronous Callbacks

Synchronous callback:

```js
console.log("A");

[1, 2].forEach((number) => {
  console.log(number);
});

console.log("B");

// Output: A, 1, 2, B
```

Asynchronous callback:

```js
console.log("A");

setTimeout(() => {
  console.log("timer");
}, 0);

console.log("B");

// Output: A, B, timer
```

The syntax does not tell you the timing. The API decides the timing.

## 5. Array HOFs in Real Frontend Code

```js
function buildProductViewModel(products) {
  return products
    .filter((product) => product.stock > 0)
    .map((product) => ({
      id: product.id,
      label: `${product.name} - ${product.stock} left`,
      expensive: product.price > 100
    }));
}
```

Production notes:

- `map` returns a new array.
- `filter` returns a new array.
- `forEach` returns `undefined`.
- `sort` mutates the original array unless you copy first.
- `reduce` should usually have an initial value.

Bug:

```jsx
function ProductList({ products }) {
  return (
    <ul>
      {products.forEach((product) => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
}
```

> [!warning] Failure mode
> renders nothing because `forEach` returns `undefined`.

Fix:

```jsx
function ProductList({ products }) {
  return (
    <ul>
      {products.map((product) => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
}
```

## 6. Middleware and Wrapper Functions

HOFs are useful for cross-cutting concerns.

```js
function withTiming(operationName, handler) {
  return async function timedHandler(request) {
    const start = performance.now();

    try {
      return await handler(request);
    } finally {
      const duration = Math.round(performance.now() - start);
      console.log(`${operationName} took ${duration}ms`);
    }
  };
}

const loadUserWithTiming = withTiming("loadUser", async (request) => {
  return fetch(`/api/users/${request.userId}`).then((response) => response.json());
});
```

Why this works:

- `withTiming` returns a new function.
- The returned function closes over `operationName` and `handler`.
- `finally` runs whether the handler succeeds or throws.

> [!tip] Tradeoff
> wrappers are powerful, but too many layers can make stack traces and control flow hard to follow. Name wrappers well and preserve errors.

## 7. React and Callback Identity

```jsx
function useProductActions(productId) {
  const addToCart = useCallback(() => {
    return post(`/api/cart`, { productId });
  }, [productId]);

  return { addToCart };
}
```

`useCallback` accepts a function and returns a cached function while dependencies stay equal. It is not required for every callback. It is useful when a stable function identity matters, such as passing a handler to a memoized child or using it as a dependency of another hook.

Production rule: correctness before memoization. If the callback reads `productId`, the dependency list must include `productId`.

## 8. Common Production Bugs

### Bug: Method Reference Loses `this`

```js
const tracker = {
  prefix: "checkout",
  track(eventName) {
    console.log(`${this.prefix}:${eventName}`);
  }
};

const events = ["opened", "submitted"];

try {
  events.forEach(tracker.track);
} catch (error) {
  console.log(error.name); // TypeError in strict mode
}
```

Fix:

```js
events.forEach((eventName) => tracker.track(eventName));
```

or:

```js
events.forEach(tracker.track.bind(tracker));
```

### Bug: Async `forEach`

```js
async function saveAll(items) {
  items.forEach(async (item) => {
    await saveItem(item);
  });

  console.log("done"); // Runs before saves finish.
}
```

Fix for sequential saves:

```js
async function saveAllSequentially(items) {
  for (const item of items) {
    await saveItem(item);
  }

  console.log("done");
}
```

Fix for parallel saves:

```js
async function saveAllInParallel(items) {
  await Promise.all(items.map((item) => saveItem(item)));
  console.log("done");
}
```

> [!tip] Tradeoff
> sequential is easier on rate limits and ordering; parallel is faster but needs error/rate-limit handling.

## 9. Bug -> Fix -> Checklist

When using a callback, ask:

- Who calls this function?
- When is it called: immediately, later, once, many times, after paint, after network?
- What arguments are passed?
- What `this` does it receive?
- Does it close over changing values?
- Does it need cleanup or cancellation?
- Are errors returned, thrown, swallowed, or converted?
- Does the callback identity need to be stable?

## 10. Interview Answer

Short answer:

> A higher-order function takes a function, returns a function, or both. A callback is a function passed into another function to be called by it.

Deeper answer:

> JavaScript supports higher-order functions because functions are first-class values. A callback can run synchronously, like `map`, or asynchronously, like `setTimeout` or a network continuation. The API determines the timing and arguments. HOFs often use closures to preserve configuration in returned functions.

Production answer:

> HOFs are useful for reusable behavior like retry, logging, authorization, debounce, and React handlers. The risks are hidden timing, lost `this`, stale closures, swallowed errors, and confusing function identity.

## 11. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Callback means asynchronous." | Some callbacks are synchronous; the API decides. |
| "Passing a method keeps its object." | Passing `obj.method` loses the receiver unless bound or wrapped. |
| "`forEach(async ...)` waits." | `forEach` ignores returned promises. |
| "`useCallback` makes code faster automatically." | It caches identity; it can add complexity if not needed. |
| "HOFs are always cleaner." | Too many wrappers can hide control flow and errors. |

## 12. Practice

1. Predict the output:

```js
console.log("A");

[1, 2].map((number) => {
  console.log(number);
  return number * 2;
});

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

2. Implement `withRetry(fn, attempts)` as a HOF.
3. Fix an async `forEach` bug using `for...of` and `Promise.all`.
4. Explain why passing `tracker.track` loses `this`.
5. Create a React custom hook that returns a stable handler and list its dependencies.

## Real-World Use Cases

### Classic interview trap: `["1", "2", "3"].map(parseInt)`

Interviewers love this one because it knots together callback argument passing and function signatures.

```js
console.log(["1", "2", "3"].map(parseInt));
```

Wrong guess: `[1, 2, 3]`. Actual output: `[1, NaN, NaN]`.

Trace, call by call — `map` invokes its callback with **three** arguments `(element, index, array)`, and `parseInt` accepts two `(string, radix)`:

1. `parseInt("1", 0)` — radix `0` means "auto-detect", so `1`.
2. `parseInt("2", 1)` — radix 1 is invalid, so `NaN`.
3. `parseInt("3", 2)` — `"3"` is not a binary digit, so `NaN`.

The mechanism: the HOF decides what arguments the callback receives; passing a function reference forwards *all* of them whether the function wants them or not.

Fix by controlling the arguments explicitly:

```js
["1", "2", "3"].map((value) => parseInt(value, 10)); // [1, 2, 3]
["1", "2", "3"].map(Number);                          // [1, 2, 3] — Number takes one argument
```

See [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]] and [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]].

### `withAuth` wrapper for Next.js Route Handlers

Every protected API route repeats the same session check. A HOF centralizes it without hiding the handler's own logic.

```ts
function withAuth(handler) {
  return async function protectedHandler(request: Request) {
    const session = await getSession(request);
    if (!session) {
      return Response.json({ error: "unauthorized" }, { status: 401 });
    }
    return handler(request, session);
  };
}

export const GET = withAuth(async (request, session) => {
  return Response.json(await getOrdersForUser(session.userId));
});
```

Works because the returned function closes over `handler` and controls if and when it runs — the same shape as `withTiming` in section 6, but gating instead of measuring.

> [!tip]
> Keep wrapper contracts explicit: `withAuth` *adds* a `session` argument. Document the augmented signature or TypeScript it, or the next developer will wonder where `session` comes from.

### `once` guard for third-party SDK initialization

An analytics SDK crashes (or double-counts) if initialized twice, but three different components might mount first. A `once` HOF makes initialization idempotent.

```js
function once(fn) {
  let called = false;
  let result;

  return function onceWrapper(...args) {
    if (!called) {
      called = true;
      result = fn.apply(this, args);
    }
    return result;
  };
}

const initAnalytics = once(() => loadSegmentSnippet({ writeKey: KEY }));
// Safe to call from every component's mount path.
```

Works because the closure holds `called` and `result` across every invocation — the wrapper decides *whether* to call the wrapped function at all, and replays the cached result otherwise.

See [[03 - Scope and Variables/05 - Closures|Closures]] and [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]].

## Related Notes

- [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]
- [[04 - Functions Deep Dive/06 - Currying and Partial Application|Currying and Partial Application]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]
- [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[01 - Roadmap|Roadmap]]
