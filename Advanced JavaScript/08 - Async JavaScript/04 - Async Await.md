---
tags: [javascript, async, async-await]
module: "08 - Async JavaScript"
priority: must-know
status: not-started
---

# Async Await

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: you can explain that async functions return promises, `await` yields, and sequential awaits can create waterfalls.
- Production signal: you write async functions with correct error handling, parallelism, cleanup, and React boundaries.
- Dependencies: [[08 - Async JavaScript/02 - Promises|Promises]], [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]

## Source Anchors

- [MDN async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [MDN await](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/await)
- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [React useEffect](https://react.dev/reference/react/useEffect)
- [Next.js: Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data)
- [ECMAScript Async Function Definitions](https://tc39.es/ecma262/#sec-async-function-definitions)

## 1. Concept

`async/await` is syntax over promises. It lets asynchronous code read like sequential code while keeping promise behavior underneath.

Rules:

- An `async` function always returns a promise.
- Returning a value fulfills that promise.
- Throwing an error rejects that promise.
- `await` waits for fulfillment or throws the rejection reason inside the async function.
- `await` yields the function continuation. It does not block the whole JavaScript thread.

```js
async function getNumber() {
  return 42;
}

console.log(getNumber() instanceof Promise);
// true

console.log(await getNumber());
// 42
```

## 2. Why It Matters

`async/await` is the dominant style for application async code. It is readable, but it can hide important behavior:

- each `await` can create a sequential dependency
- errors still travel through promises
- `try/catch` only catches awaited work inside the block
- `forEach` does not wait for async callbacks
- React effect callbacks should not be `async`
- top-level `await` depends on module/runtime context

Mature code uses `await` to express real dependency, not just because it looks clean.

## 3. Official Mechanism

When an async function is called:

1. It returns a promise immediately.
2. It runs synchronously until the first `await`, `return`, or throw.
3. `await value` converts the value with promise-like semantics.
4. The async function is suspended.
5. When the awaited promise settles, the continuation resumes as a promise job/microtask.
6. A returned value fulfills the outer promise.
7. A thrown error rejects the outer promise.

Even awaiting a non-promise yields:

```js
async function demo() {
  console.log("inside before");
  await 42;
  console.log("inside after");
}

demo();
console.log("outside");

// inside before
// outside
// inside after
```

## Async Function Internals (Deep Dive)

This is the machinery under section 3. You do not need it for most application code, but it explains *why* the ordering above happens and it separates a mid-level answer from a senior one.

### A suspendable stack frame, not magic

An async function is not special at the value level — it is a normal call-stack frame that the engine can **suspend and resume**. This is the exact capability a generator has (`yield` pauses a frame; the engine keeps the frame's locals alive and pushes it back later). `async/await` is that same resumable-frame mechanism wired to a promise scheduler instead of to `.next()`.

- At `await`, the frame is suspended and **popped** off the call stack — its locals are preserved off-stack.
- A continuation is registered on the awaited promise (a promise reaction job).
- When that promise settles, the job runs on the **microtask queue**, and the frame is pushed back and resumed at the awaited line.

So "async function = a call-stack frame that can be paused and put back" only makes sense once [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]] and [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]] are solid. The scheduler side lives in [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]] and [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]. Generators — the same suspend/resume primitive — are in [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]].

### `PromiseResolve`: the native-promise fast path

`await x` does **not** blindly wrap `x` in a new promise. The spec runs `PromiseResolve(%Promise%, x)`:

- If `x` is already a native promise, it is **passed through unchanged** — no wrapper, no extra microtask hop. (This pass-through was added in ES2019 / V8 7.2.)
- If `x` is a non-promise (like `42`), it resolves in a single microtask tick.
- If `x` is a *thenable* (a non-native object with a `.then`), the engine must adopt it via an extra job, costing an additional tick.

### The tick budget (the number people get wrong)

| Expression | Microtask ticks to resume |
|---|---|
| `await 42` / `await nativePromise` | **1** |
| `await thenable` (synchronous `.then`) | **2** (1 extra) |

> [!warning] `await thenable` is 2 ticks, not 3
> The common mistake — including one I made in an earlier session — is counting `await thenable` as ~3 ticks. Trace it: `PromiseResolve` sees a callable `.then`, enqueues `NewPromiseResolveThenableJob` (tick 1); that job calls `.then`, which resolves synchronously and enqueues the reaction (tick 2); the reaction resumes the frame. Two ticks total, **one extra** over the native path. V8's own docs describe thenable handling as adding "an extra microtask turn" — singular.

### `return p` vs `return await p`

`return await p` reads the value out and re-wraps it, historically adding a tick over `return p`. The reason to keep `return await` anyway is **stack traces**: inside a `try`, `return await p` keeps the async frame on the stack so a rejection is catchable locally and shows up in the async trace; a bare `return p` hands the promise to the caller and the frame is already gone. Prefer `return await p` inside `try/catch`; elsewhere it is a micro-optimization not worth fussing over.

## 4. Mental Model

`await` means: "pause this async function here and resume it later."

It does not mean: "pause the entire runtime."

Use sequential `await` when step B depends on step A. Start promises before awaiting when work is independent.

## 5. Sequential vs Parallel

### Slow Waterfall

```ts
async function loadDashboard(userId: string) {
  const user = await fetchUser(userId);
  const settings = await fetchSettings(userId);
  const permissions = await fetchPermissions(userId);

  return { user, settings, permissions };
}
```

If each request takes 300ms, this can take about 900ms.

### Parallel Version

```ts
async function loadDashboard(userId: string) {
  const [user, settings, permissions] = await Promise.all([
    fetchUser(userId),
    fetchSettings(userId),
    fetchPermissions(userId),
  ]);

  return { user, settings, permissions };
}
```

If each request takes 300ms, this can take about 300ms plus overhead.

### Mixed Dependency

```ts
async function loadProfile(userId: string) {
  const userPromise = fetchUser(userId);
  const settingsPromise = fetchSettings(userId);

  const user = await userPromise;
  const orders = await fetchOrders(user.id);
  const settings = await settingsPromise;

  return { user, orders, settings };
}
```

`orders` depends on `user`, but settings can start immediately.

## 6. Async Error Handling

```ts
async function fetchUser(userId: string) {
  const response = await fetch(`/api/users/${userId}`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
```

Throwing inside an async function rejects its returned promise.

```js
async function fail() {
  throw new Error("bad");
}

try {
  await fail();
} catch (error) {
  console.log(error.message);
}

// bad
```

## 7. The Async `forEach` Trap

### Problem

```js
async function loadUsers(ids) {
  const users = [];

  ids.forEach(async id => {
    const user = await fetchUser(id);
    users.push(user);
  });

  return users;
}
```

### Bug

> [!warning] forEach never waits
> `forEach` ignores the promise returned by the callback. `loadUsers` returns before the requests finish.

### Sequential Fix

```js
async function loadUsersSequential(ids) {
  const users = [];

  for (const id of ids) {
    const user = await fetchUser(id);
    users.push(user);
  }

  return users;
}
```

### Parallel Fix

```js
async function loadUsersParallel(ids) {
  return Promise.all(ids.map(id => fetchUser(id)));
}
```

> [!tip] Sequential vs parallel tradeoff
> Tradeoff: sequential is easier to rate-limit and preserves request order in time. Parallel is faster when requests are independent, but can overload an API if the list is huge.

## 8. React Boundaries

### Effect Callback Should Not Be `async`

```jsx
useEffect(async () => {
  const response = await fetch("/api/users");
  setUsers(await response.json());
}, []);
```

> [!warning] Async effect callbacks break cleanup
> This is wrong because an effect callback must return either nothing or a cleanup function. An async function returns a promise.

Use an inner async function:

```jsx
useEffect(() => {
  const controller = new AbortController();

  async function loadUsers() {
    try {
      const response = await fetch("/api/users", {
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      setUsers(await response.json());
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setError(error);
    }
  }

  loadUsers();

  return () => controller.abort();
}, []);
```

### Event Handlers Can Be `async`

```jsx
async function handleSubmit(event) {
  event.preventDefault();

  setSaving(true);

  try {
    await saveForm();
  } finally {
    setSaving(false);
  }
}
```

React will not await the returned promise for you. You still need to handle errors and duplicate submissions.

## 9. Next.js And Top-Level Await

Top-level `await` works in ES modules and is common in server-side module contexts.

```tsx
export default async function Page() {
  const response = await fetch("https://api.example.com/products");
  const products = await response.json();

  return <ProductList products={products} />;
}
```

In Next.js App Router server components, components can be async because they run on the server. Client components cannot be async components in the same way; they use effects, event handlers, or client data libraries.

Production reminder: know whether your code runs on the server, browser, edge runtime, or during build. The same `await fetch(...)` line can have different caching, credential, and environment behavior depending on where it runs.

## 10. Real Frontend Bug: Waterfall In A Route

### Problem

```ts
async function loadPage(userId: string) {
  const user = await fetchUser(userId);
  const permissions = await fetchPermissions(userId);
  const featureFlags = await fetchFeatureFlags();

  return { user, permissions, featureFlags };
}
```

### Bug

> [!warning] Accidental waterfall
> Nothing here depends on the previous result, but the requests run sequentially. This makes navigation slower than necessary.

### Fix

```ts
async function loadPage(userId: string) {
  const [user, permissions, featureFlags] = await Promise.all([
    fetchUser(userId),
    fetchPermissions(userId),
    fetchFeatureFlags(),
  ]);

  return { user, permissions, featureFlags };
}
```

### Tradeoff

> [!tip] Parallelize with intent
> Do not blindly parallelize everything. If request B depends on request A, keep the dependency. If an API rate-limits aggressively, use a concurrency limit.

## 11. Debugging Notes

- Put logs before and after each `await` to reveal ordering.
- Use Network throttling to make waterfalls visible.
- Watch for async stack traces in DevTools.
- Search for `forEach(async` during reviews.
- Search for `useEffect(async` during reviews.
- Check whether a function that starts async work returns its promise.
- Use `Promise.all` only after confirming the operations are independent.

## 12. Production Tradeoffs

- `async/await` improves readability but can hide parallel opportunities.
- `try/catch` is clearer for local recovery; letting errors bubble is better for shared utilities.
- Parallel requests are faster but can stress APIs and browsers.
- Sequential loops are slower but easier to rate-limit and reason about.
- React effects need cleanup for async work tied to a render.
- Next.js server-side async can improve user experience, but client interactivity still has browser timing and cancellation concerns.

## Real-World Use Cases

### Classic interview trap: async predicate in `filter`

Filtering users by an async permission check looks harmless and silently returns everyone.

```js
const admins = users.filter(async user => await isAdmin(user));
// admins === users — every user "passes"
```

Trace, tick by tick: the async callback returns a *promise* immediately (mechanism step 1 in section 3) — it has not even reached the `await` result yet. `filter` is synchronous and checks the return value for truthiness right now. A `Promise` object is always truthy, whatever it later fulfills with, so every element is kept. No error, no warning — just wrong data.

Fix: resolve the checks first, then filter synchronously.

```js
const checks = await Promise.all(users.map(user => isAdmin(user)));
const admins = users.filter((_, index) => checks[index]);
```

Same family as the `forEach` trap in section 7: array methods do not await callbacks. See [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]] and [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]].

> [!warning]
> `map(async ...)` has the mirror-image gotcha: it "works" but gives you `Promise[]`, not values. Anyone consuming the result without `Promise.all` sees an array of pending promises.

### Cursor pagination: when the sequential loop is right

An "Export all orders" feature pages through an API where each response carries the next cursor. This is the counterexample to section 10's waterfall bug — here every `await` expresses a real dependency, so a sequential loop is correct and `Promise.all` is impossible.

```ts
async function exportAllOrders() {
  const orders: Order[] = [];
  let cursor: string | undefined;

  do {
    const page = await apiFetch<OrdersPage>("/orders", { params: { cursor } });
    orders.push(...page.items);
    cursor = page.nextCursor;
  } while (cursor);

  return orders;
}
```

Works because `await` suspends the function until the response arrives, and the next request cannot be constructed without `page.nextCursor`. The interview-ready framing: parallelize independent work, keep dependent work sequential — the dependency graph decides, not style preference.

### Module-level bootstrap with top-level `await`

A Node/edge service module loads config before exporting its client. Top-level `await` (section 9) makes importers automatically wait for initialization.

```ts
// payments-client.ts (ES module)
const config = await loadPaymentConfig(); // module evaluation pauses here

export const paymentsClient = createClient(config.apiKey, config.region);
```

Works because ES modules treat a top-level `await` as part of module evaluation: any module importing `paymentsClient` does not execute until this settles. See [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]] for where this is allowed to run.

> [!warning]
> A slow or hanging top-level `await` blocks every importer's evaluation, and it does not work in scripts or CommonJS. Keep bootstrap awaits fast and failure-handled.

## 13. Interview Answer

**Short version:** `async/await` is syntax over promises. An async function always returns a promise, and `await` pauses that async function until the awaited value settles.

**Strong version:** Calling an async function returns a promise immediately. The function runs synchronously until an `await`, then the rest of the function resumes later as a promise job. If the awaited promise fulfills, `await` gives its value; if it rejects, `await` throws inside the async function. Returning a value fulfills the outer promise, and throwing rejects it. In production, I watch for accidental waterfalls, async `forEach`, missing error handling, and React effect cleanup.

## 14. Common Mistakes

- Thinking `await` blocks the JavaScript thread.
- Forgetting that an async function returns a promise.
- Awaiting independent requests one by one.
- Using `forEach(async ...)` when completion matters.
- Making the `useEffect` callback itself async.
- Catching errors too low and hiding failure from callers.
- Forgetting to abort or ignore obsolete async work in React effects.
- Assuming client and server `await fetch` have identical behavior in Next.js.

## 15. Practice

1. Predict the output of the `await 42` example.
2. Refactor a sequential dashboard loader into a parallel one.
3. Rewrite async `forEach` into sequential and parallel versions.
4. Write a React effect that fetches with cleanup.
5. Explain why an async event handler still needs its own error handling.

## Related Notes

- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
