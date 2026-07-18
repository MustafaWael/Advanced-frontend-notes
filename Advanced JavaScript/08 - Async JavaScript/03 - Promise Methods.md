---
tags: [javascript, async, promise-methods]
module: "08 - Async JavaScript"
priority: must-know
status: not-started
---

# Promise Methods

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: you can choose the right promise combinator based on dependency and failure policy.
- Production signal: you avoid request waterfalls, partial-failure bugs, fake timeouts, and accidental unhandled work.
- Dependencies: [[08 - Async JavaScript/02 - Promises|Promises]], [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]]

## Source Anchors

- [MDN Promise.all](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all)
- [MDN Promise.allSettled](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled)
- [MDN Promise.race](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/race)
- [MDN Promise.any](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/any)
- [MDN Promise.withResolvers](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/withResolvers)
- [MDN Promise.try](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/try)
- [MDN AbortSignal.timeout](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static)

## 1. Concept

Promise static methods combine or create promises. The most important production skill is choosing the method that matches the dependency and failure policy.

| Method | Use when | Fulfillment | Rejection |
| --- | --- | --- | --- |
| `Promise.all` | all operations are required | all fulfill | first rejection |
| `Promise.allSettled` | partial success is acceptable | all settle | never rejects by itself |
| `Promise.race` | first settled outcome wins | first fulfillment | first rejection |
| `Promise.any` | first successful source wins | first fulfillment | all reject with `AggregateError` |
| `Promise.resolve` | normalize a value/thenable to a promise | wrapped fulfillment | follows thenable/rejection |
| `Promise.reject` | create a rejected promise | never fulfills | given reason |

Modern methods:

- `Promise.withResolvers()` returns `{ promise, resolve, reject }`.
- `Promise.try()` starts a promise chain from a callback and captures synchronous throws.

The modern methods are useful to know, but `all`, `allSettled`, `race`, and `any` are the must-know interview set.

## 2. Why It Matters

Real screens rarely load one thing:

- a dashboard loads widgets
- a profile loads user, permissions, and preferences
- a form validates several fields
- a media component tries fallback URLs
- a search page cancels or times out obsolete requests

The wrong promise method can make an entire screen fail because one optional panel failed, or can create a slow waterfall because independent requests are awaited one by one.

## 3. Official Mechanism

The combinators accept an iterable of values/promises and return a new promise. Non-promise values are treated like already fulfilled values.

Important details:

- `Promise.all` preserves input order in its fulfillment array, not completion order.
- `Promise.all` rejects as soon as one input rejects, but it does not cancel other in-flight operations.
- `Promise.allSettled` waits for every input and returns status objects.
- `Promise.race` settles with the first input to settle, whether fulfilled or rejected.
- `Promise.any` fulfills with the first fulfilled input and ignores earlier rejections unless all reject.
- `Promise.any` rejects with `AggregateError` when every input rejects.
- Empty iterables have edge cases: `Promise.all([])` fulfills with `[]`, `Promise.allSettled([])` fulfills with `[]`, `Promise.any([])` rejects with `AggregateError`, and `Promise.race([])` stays pending forever.

## 4. Mental Model

Choose by policy:

```txt
Need all or fail together?              Promise.all
Need every result, success or failure?  Promise.allSettled
Need first finished outcome?            Promise.race
Need first successful outcome?          Promise.any
Need to wrap/normalize a value?         Promise.resolve
Need to create immediate failure?       Promise.reject
```

## 5. `Promise.all`: Required Parallel Work

```js
function wait(ms, value) {
  return new Promise(resolve => setTimeout(() => resolve(value), ms));
}

const result = await Promise.all([
  wait(30, "user"),
  wait(10, "settings"),
  "cached-permissions",
]);

console.log(result);
// ["user", "settings", "cached-permissions"]
```

The values are returned in input order.

### Real Frontend Use

```ts
async function loadProfilePage(userId: string) {
  const [user, settings, permissions] = await Promise.all([
    fetchUser(userId),
    fetchSettings(userId),
    fetchPermissions(userId),
  ]);

  return { user, settings, permissions };
}
```

Use this when the page cannot render correctly without every required part.

### Common Bug: Assuming It Cancels The Rest

```js
try {
  await Promise.all([
    saveAuditLog(),
    chargeCard(),
    sendReceipt(),
  ]);
} catch (error) {
  console.log("one failed");
}
```

> [!warning] Failing fast does not cancel
> If `sendReceipt` fails first, `saveAuditLog` and `chargeCard` are not automatically canceled. They may still complete.

> [!tip] Combinators are not transactions
> Production implication: for critical mutations, design server-side idempotency, compensation, and transaction boundaries. Promise combinators are not a distributed transaction system.

## 6. `Promise.allSettled`: Partial Success

```js
const results = await Promise.allSettled([
  Promise.resolve("analytics"),
  Promise.reject(new Error("notifications failed")),
]);

console.log(results.map(result => result.status));
// ["fulfilled", "rejected"]
```

### Real Frontend Use

```ts
async function loadDashboard() {
  const results = await Promise.allSettled([
    fetchAnalytics(),
    fetchNotifications(),
    fetchRecommendations(),
  ]);

  const [analytics, notifications, recommendations] = results;

  return {
    analytics: analytics.status === "fulfilled" ? analytics.value : null,
    notifications:
      notifications.status === "fulfilled" ? notifications.value : null,
    recommendations:
      recommendations.status === "fulfilled" ? recommendations.value : null,
    errors: results
      .filter((result): result is PromiseRejectedResult => {
        return result.status === "rejected";
      })
      .map(result => result.reason),
  };
}
```

Use this when independent panels can render partial data.

## 7. `Promise.race`: First Settled Outcome

```js
function delay(ms, value) {
  return new Promise(resolve => setTimeout(() => resolve(value), ms));
}

console.log(await Promise.race([
  delay(50, "slow"),
  delay(10, "fast"),
]));

// fast
```

### Timeout Pattern: Know The Limit

```js
function timeout(ms) {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error("timeout")), ms);
  });
}

await Promise.race([
  fetch("/api/report"),
  timeout(5000),
]);
```

This rejects after 5 seconds if the timeout wins, but it does not necessarily abort the underlying fetch. Prefer `AbortSignal.timeout` for fetch when supported:

```js
const response = await fetch("/api/report", {
  signal: AbortSignal.timeout(5000),
});
```

Fallback with a controller:

```js
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 5000);

try {
  const response = await fetch("/api/report", {
    signal: controller.signal,
  });
  return response.json();
} finally {
  clearTimeout(timeoutId);
}
```

## 8. `Promise.any`: First Fulfillment

```js
const value = await Promise.any([
  Promise.reject(new Error("primary failed")),
  Promise.resolve("replica"),
]);

console.log(value);
// replica
```

### Real Frontend Use

```ts
async function loadImageFromAnyMirror(path: string): Promise<Blob> {
  try {
    return await Promise.any([
      fetch(`/cdn-a/${path}`).then(toBlob),
      fetch(`/cdn-b/${path}`).then(toBlob),
      fetch(`/cdn-c/${path}`).then(toBlob),
    ]);
  } catch (error) {
    if (error instanceof AggregateError) {
      reportError({
        message: "All mirrors failed",
        reasons: error.errors,
      });
    }

    throw error;
  }
}

async function toBlob(response: Response) {
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.blob();
}
```

Use this when any successful source is acceptable.

## 9. `Promise.resolve` And `Promise.reject`

Use these for normalization at API boundaries:

```js
function getCachedUser(id) {
  const cached = userCache.get(id);

  if (cached) {
    return Promise.resolve(cached);
  }

  return fetchUser(id);
}
```

Validation example:

```js
function requireId(id) {
  if (!id) {
    return Promise.reject(new Error("Missing id"));
  }

  return Promise.resolve(id);
}
```

In modern `async` code, you often write:

```js
async function requireId(id) {
  if (!id) {
    throw new Error("Missing id");
  }

  return id;
}
```

## 10. Modern Deep Dive: `Promise.withResolvers`

`Promise.withResolvers()` gives you a promise plus external `resolve` and `reject` functions without manually declaring them outside a constructor callback.

```js
const { promise, resolve, reject } = Promise.withResolvers();

setTimeout(() => resolve("ready"), 10);

console.log(await promise);
// ready
```

> [!tip] Prefer plain chains when possible
> Use it carefully. It can be useful when adapting event sources, queues, or streams. In ordinary API code, returning the existing promise chain is usually clearer.

## 11. Real Frontend Decision: Dashboard Widgets

### Problem

```ts
async function loadDashboard() {
  const [analytics, notifications, recommendations] = await Promise.all([
    fetchAnalytics(),
    fetchNotifications(),
    fetchRecommendations(),
  ]);

  return { analytics, notifications, recommendations };
}
```

### Bug

> [!warning] One widget sinks the dashboard
> If recommendations fail, the whole dashboard fails even though analytics and notifications could still be useful.

### Fix

```ts
async function loadDashboard() {
  const results = await Promise.allSettled([
    fetchAnalytics(),
    fetchNotifications(),
    fetchRecommendations(),
  ]);

  return results.map(result => {
    if (result.status === "fulfilled") {
      return { state: "ready", data: result.value };
    }

    return { state: "error", error: result.reason };
  });
}
```

### Tradeoff

> [!tip] Partial success is your job now
> `allSettled` moves responsibility to you. You must design partial loading, partial error UI, telemetry, and retry behavior for each panel.

## 12. Production Checklist

- Use `Promise.all` only when every operation is required.
- Use `Promise.allSettled` when partial data is acceptable.
- Use `Promise.any` for fallback sources where first success wins.
- Use `Promise.race` for first-settled behavior, not automatic cancellation.
- Preserve input order assumptions with clear destructuring.
- Remember that failing fast does not abort in-flight work.
- Do not use promise combinators as transaction control for critical mutations.
- Limit concurrency when mapping over large arrays of network requests.
- Use `AbortController` or library cancellation support when obsolete work should stop.

## Real-World Use Cases

### Concurrency-limited bulk upload

A media manager uploads 200 photos. `Promise.all(files.map(uploadFile))` fires 200 requests at once and can exhaust browser connections or trip API rate limits. Run a fixed pool of workers instead — `Promise.all` over the *workers*, not the files.

```ts
async function uploadAll(files: File[], limit = 4) {
  const queue = [...files];

  async function worker() {
    while (queue.length > 0) {
      const file = queue.shift()!;
      await uploadFile(file); // sequential within a worker
    }
  }

  await Promise.all(Array.from({ length: limit }, worker));
}
```

Works because each worker is one sequential async loop, and `Promise.all` only needs all four worker promises to fulfill — at most 4 uploads are in flight at any moment. This is the fix for the "thousands of requests at once" mistake in section 14.

### Awaitable confirmation dialog with `Promise.withResolvers`

A destructive action needs "Are you sure?" before proceeding. Instead of threading callbacks through the dialog, hand the caller a promise that the dialog buttons settle.

```tsx
let pendingConfirm: PromiseWithResolvers<boolean>;

function confirmDelete(): Promise<boolean> {
  pendingConfirm = Promise.withResolvers<boolean>();
  setDialogOpen(true);
  return pendingConfirm.promise;
}

// dialog buttons
<button onClick={() => { pendingConfirm.resolve(true); setDialogOpen(false); }}>Delete</button>
<button onClick={() => { pendingConfirm.resolve(false); setDialogOpen(false); }}>Cancel</button>

// call site reads sequentially
if (await confirmDelete()) {
  await ordersApi.remove(orderId);
}
```

Works because `withResolvers` externalizes `resolve` — the settling side (a click handler) lives in a different place than the promise creation, which is exactly the event-source adaptation section 10 describes.

### Anti-flash skeleton with `Promise.race`

Showing a skeleton for a 50ms response makes the UI flicker. Race the fetch against a 200ms delay: only show the skeleton if the data loses the race.

```ts
const dataPromise = fetchDashboard(); // start once, await twice

const winner = await Promise.race([dataPromise, delay(200, "slow")]);
if (winner === "slow") {
  setShowSkeleton(true);
}

const dashboard = await dataPromise;
setShowSkeleton(false);
render(dashboard);
```

Works because `race` settles with the first settled input but does not cancel the loser — the fetch keeps running, and awaiting the same promise again just waits for its single settlement. Here the "no cancellation" behavior that bites in the timeout pattern (section 7) is the feature. See [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]].

## 13. Interview Answer

**Short version:** `Promise.all` waits for all and fails on first rejection. `allSettled` waits for every result and never rejects by itself. `race` settles with the first settled input. `any` fulfills with the first successful input and rejects only if all fail.

**Strong version:** Promise combinators return a new promise around an iterable of inputs. The choice is about dependency and failure policy. Use `all` when every result is required, `allSettled` for partial success, `race` when first settled outcome wins, and `any` when first success wins. `all` preserves input order but does not cancel other work when one rejects. `race` is often used for timeouts, but for fetch timeouts you should prefer `AbortSignal.timeout` or an `AbortController` so the underlying request is actually aborted.

## 14. Common Mistakes

- Using `Promise.all` for independent dashboard widgets.
- Thinking `Promise.all` cancels other requests on failure.
- Using `Promise.race` timeout without aborting the request.
- Forgetting `Promise.any` rejects with `AggregateError`.
- Confusing first settled with first fulfilled.
- Creating thousands of requests at once with `Promise.all(items.map(...))` without concurrency limits.
- Destructuring `Promise.all` results in the wrong order.
- Expecting `Promise.race([])` to finish.

## 15. Practice

1. Pick `all`, `allSettled`, `race`, or `any` for a dashboard, file mirror, required profile load, and timeout.
2. Explain why `Promise.all` does not cancel other promises.
3. Write a fetch timeout using `AbortSignal.timeout`.
4. Handle `AggregateError` from `Promise.any`.
5. Rewrite a sequential API waterfall into parallel `Promise.all`.

## Related Notes

- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
- [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
- [[01 - Roadmap|Roadmap]]
