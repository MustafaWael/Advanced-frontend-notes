---
tags: [javascript, async, promises]
module: "08 - Async JavaScript"
priority: must-know
status: not-started
---

# Promises

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: you can explain promise states, settlement, chaining, microtask timing, and error propagation.
- Production signal: you return promises correctly, avoid floating async work, and make caller ownership explicit.
- Dependencies: [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]], [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]

## Source Anchors

- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN Using promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Using_promises)
- [MDN Promise.prototype.then](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/then)
- [MDN Promise.prototype.catch](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/catch)
- [MDN Promise.prototype.finally](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/finally)
- [ECMAScript Promise Objects](https://tc39.es/ecma262/#sec-promise-objects)

## 1. Concept

A Promise is an object that represents the eventual result of an asynchronous operation.

It gives the caller a standard contract:

- pending: the operation has not settled yet
- fulfilled: the operation completed with a value
- rejected: the operation failed with a reason

```js
const promise = fetch("/api/user")
  .then(response => response.json());
```

The promise is not the data. It is a handle for the future data or error.

## 2. Why It Matters

Promises are the foundation under `fetch`, `async/await`, React query libraries, Next.js server data fetching, route transitions, and many browser APIs.

If you misunderstand promises, production bugs often look like:

- function starts work but callers cannot await it
- loading state clears too early
- errors become unhandled rejections
- `.catch` accidentally converts failure into success
- independent requests run in a slow waterfall
- stale promises write obsolete state

## 3. Official Mechanism

A promise has internal state and stored reactions. You cannot directly inspect or change these internal slots, but you can observe behavior through `.then`, `.catch`, `.finally`, and `await`.

Important rules:

- A promise starts pending.
- A pending promise can settle once.
- Settled means fulfilled or rejected.
- After settlement, the state and result do not change.
- `.then` returns a new promise.
- Promise reactions run asynchronously as promise jobs/microtasks.
- A promise can be "resolved" to follow another promise, so resolved is not always the same as fulfilled.
- Promises do not have built-in cancellation. You cancel the underlying operation if it supports cancellation, such as `fetch` with `AbortController`.

## 4. State And Chaining

```js
const p1 = Promise.resolve(1);

const p2 = p1.then(value => value + 1);
const p3 = p2.then(value => value * 10);

p3.then(value => console.log(value));

// 20
```

What `.then` returns:

| Handler behavior | New promise state |
| --- | --- |
| returns a value | fulfills with that value |
| returns a promise | follows that promise |
| throws an error | rejects with that error |
| no handler for current state | keeps passing the value/reason through |

Example:

```js
Promise.resolve("user")
  .then(value => {
    return `${value}:orders`;
  })
  .then(value => {
    throw new Error(`failed at ${value}`);
  })
  .catch(error => {
    return error.message;
  })
  .then(value => {
    console.log(value);
  });

// failed at user:orders
```

The `catch` returned a string, so the chain became fulfilled again.

## 5. Executor Timing

> [!example] Executor runs synchronously
> The function passed to `new Promise` runs synchronously immediately.

```js
const promise = new Promise(resolve => {
  console.log("executor");
  resolve("done");
});

promise.then(value => console.log(value));

console.log("after");

// executor
// after
// done
```

The executor ran before `after`. The `.then` handler ran later as a microtask.

## 6. Real Frontend Bug: Missing Return In A Chain

### Problem

```js
function loadUserAndOrders(userId) {
  return fetchUser(userId)
    .then(user => {
      fetchOrders(user.id);
    })
    .then(orders => {
      console.log(orders);
    });
}
```

### Bug

> [!warning] Missing return detaches the chain
> The first `.then` starts `fetchOrders` but does not return it. The next `.then` receives `undefined`, and errors from `fetchOrders` may become detached from the intended chain.

### Fix

```js
function loadUserAndOrders(userId) {
  return fetchUser(userId)
    .then(user => {
      return fetchOrders(user.id);
    })
    .then(orders => {
      console.log(orders);
      return orders;
    });
}
```

Or with concise syntax:

```js
function loadUserAndOrders(userId) {
  return fetchUser(userId)
    .then(user => fetchOrders(user.id));
}
```

### Why The Fix Works

> [!tip] Return promises to keep ownership
> Returning the promise connects the async operation to the chain. The caller can await `loadUserAndOrders`, and rejections propagate to the caller.

## 7. Real Frontend Bug: Floating Promise

### Problem

```js
async function handleSubmit(values) {
  setSaving(true);

  saveProfile(values);

  setSaving(false);
  showToast("Saved");
}
```

### Bug

> [!warning] Floating promise clears state early
> `saveProfile(values)` returns a promise, but the code does not await or return it. The loading state clears immediately, the success toast shows too early, and errors can become unhandled.

### Fix

```js
async function handleSubmit(values) {
  setSaving(true);

  try {
    await saveProfile(values);
    showToast("Saved");
  } catch (error) {
    showToast("Could not save profile");
    reportError(error);
  } finally {
    setSaving(false);
  }
}
```

## 8. Fetch With Promise Contract

```ts
type User = {
  id: string;
  name: string;
};

function fetchUser(userId: string): Promise<User> {
  return fetch(`/api/users/${userId}`).then(response => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json() as Promise<User>;
  });
}
```

Why this is useful:

- The return type tells callers they must await or handle a promise.
- HTTP failure is converted into rejection.
- JSON parsing remains part of the returned chain.

## 9. `.catch` And `.finally`

```js
fetchUser("u1")
  .catch(error => {
    console.error("load failed", error);
    throw error;
  })
  .finally(() => {
    console.log("cleanup");
  });
```

Important rules:

- `.catch(fn)` is shorthand for `.then(undefined, fn)`.
- If a `catch` returns normally, the chain becomes fulfilled with that returned value.
- If a `catch` rethrows, the chain stays rejected.
- `finally` runs after fulfillment or rejection.
- A normal `finally` return does not replace the previous value.
- A throwing or rejecting `finally` replaces the outcome with a failure.

```js
Promise.reject(new Error("bad"))
  .catch(error => {
    return "fallback";
  })
  .then(value => console.log(value));

// fallback
```

> [!warning] Catch can hide real failure
> This is useful for intentional fallback. It is dangerous when the caller still needs to know the operation failed.

## 10. Promise Constructor Anti-Pattern

Avoid wrapping a promise in another promise when you can return the original chain.

```js
function badFetchUser(id) {
  return new Promise((resolve, reject) => {
    fetch(`/api/users/${id}`)
      .then(response => response.json())
      .then(resolve)
      .catch(reject);
  });
}
```

Better:

```js
function fetchUser(id) {
  return fetch(`/api/users/${id}`).then(response => response.json());
}
```

Use `new Promise` when you are adapting callback/event APIs into a promise, not when an API already returns one.

## 11. Production Tradeoffs

- Return promises from functions that start async work.
- Do not start async work that no owner can await, cancel, or observe.
- Attach error handling at the boundary where a useful recovery decision can be made.
- Prefer `async/await` for sequential logic; prefer promise chains when composition is clearer.
- Avoid swallowing errors in low-level utilities. Add context, then rethrow.
- Use `AbortController` for cancelable host work. Promises themselves do not cancel.
- Add lint rules such as no-floating-promises in TypeScript projects when available.

## Real-World Use Cases

### In-flight request deduplication

Three components on the same screen each call `getUser("u1")` on mount. Instead of three identical requests, cache the *promise* so concurrent callers share one flight.

```ts
const inFlight = new Map<string, Promise<User>>();

function getUser(id: string): Promise<User> {
  const existing = inFlight.get(id);
  if (existing) return existing;

  const promise = fetchUser(id).finally(() => inFlight.delete(id));
  inFlight.set(id, promise);
  return promise;
}
```

Works because a promise is a shareable handle: any number of `.then`/`await` consumers can attach, and each gets the settled result — even if they attach after settlement.

> [!warning]
> Delete the cache entry on settlement (the `finally` above). If you cache forever, a rejected promise poisons the cache and every later caller re-receives the old error. See [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]].

### Promisifying an image preload

A product gallery wants the hero image decoded before swapping it in, to avoid a flash. `Image` is an event-based API, so this is the legitimate use of the `new Promise` constructor (unlike the anti-pattern in section 10).

```ts
function preloadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`Failed to load ${src}`));
    img.src = src;
  });
}

await preloadImage(product.heroUrl);
setHero(product.heroUrl); // guaranteed cached now
```

Works because the executor runs synchronously to wire up the listeners, and settlement is deferred until the host fires the event — exactly what the constructor is for: adapting callback/event APIs.

### Classic interview trap: retrying a promise instead of a promise factory

A flaky endpoint needs retries. Passing the *promise* cannot work; passing a *function that creates the promise* can.

```ts
await retry(fetchUser("u1"));       // broken: one request, already in flight
await retry(() => fetchUser("u1")); // works: each attempt is a fresh request
```

Trace: `fetchUser("u1")` runs eagerly — the executor fires synchronously (section 5) and the request is already sent before `retry` even receives the value. Settlement is one-way (section 3), so a rejected promise can never be "re-run"; awaiting it again just re-throws the same stored reason. A retry helper must call a factory to get a new pending promise per attempt. See [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]] for the backoff implementation.

## 12. Interview Answer

**Short version:** A promise represents a future value or failure. It starts pending, then settles as fulfilled or rejected, and reactions attached with `.then`, `.catch`, or `await` run asynchronously.

**Strong version:** A promise is a standard object for async completion. It has a state, a result, and reaction handlers. Settlement is one-way: pending becomes fulfilled or rejected once. `.then` always returns a new promise, and the returned promise follows the handler result: return a value to fulfill, return a promise to wait for it, or throw to reject. Promise handlers run as microtasks after the current synchronous code finishes. In production, the biggest mistakes are not returning promises, creating floating promises, swallowing rejections, and assuming promises can cancel underlying work by themselves.

## 13. Common Mistakes

- Forgetting to return a promise inside `.then`.
- Starting a promise without awaiting, returning, or catching it.
- Catching an error and returning a fallback by accident.
- Wrapping promises unnecessarily with `new Promise`.
- Thinking promise handlers run synchronously when a promise is already fulfilled.
- Thinking "resolved" always means fulfilled.
- Assuming `fetch` rejects on HTTP 404 or 500. It rejects for network-level failure, but HTTP status must be checked.
- Assuming a promise can be canceled without support from the underlying operation.

## 14. Practice

1. Predict the output of the executor timing example.
2. Write a promise chain where a `catch` converts failure into fallback success.
3. Fix a missing `return` inside a `.then` chain.
4. Refactor a Promise constructor anti-pattern into a direct return.
5. Explain why a caller cannot reliably handle errors from a floating promise.

## Related Notes

- [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
