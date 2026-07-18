---
tags: [javascript, event-loop, promise-jobs]
module: "09 - Event Loop Advanced"
priority: must-know
status: not-started
---

# Promise Jobs

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can trace promise reaction order, async function resumption, and why `.then` never calls synchronously.
- Production signal: you avoid bugs caused by assuming promise callbacks mutate state before the next sync line.
- Dependencies: [[08 - Async JavaScript/02 - Promises|Promises]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## Source Anchors

- [ECMAScript Promise Objects](https://tc39.es/ecma262/#sec-promise-objects)
- [ECMAScript Jobs and Host Operations](https://tc39.es/ecma262/#sec-jobs-and-host-operations)
- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [MDN Microtask guide](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide)

## 1. Concept

Promise jobs are ECMAScript jobs used for promise reactions and async function continuations. In browsers, the host runs these jobs through the microtask queue at microtask checkpoints.

Practical translation:

```js
Promise.resolve().then(callback);
```

`callback` is not called immediately. It runs after the current synchronous code finishes.

## 2. Why It Matters

Promise jobs explain:

- why `.then` runs after synchronous code
- why promise chains interleave
- why `await` resumes later
- why a resolved promise still behaves asynchronously
- why state reads immediately after `.then` often see old values

These details show up in interviews and in production race bugs.

## 3. Official Mechanism

When a promise settles, its stored reactions are scheduled as jobs. A `.then` call creates a new promise and registers reactions for the original promise.

Rules to know:

- The promise executor runs synchronously.
- `.then`, `.catch`, and `.finally` return new promises.
- Reaction callbacks run asynchronously, even for already-settled promises.
- An async function resumes after `await` through promise-job scheduling.
- Returning a promise from a handler makes the next promise follow/adopt that promise.

## 4. Mental Model

Promises are not "callbacks later maybe." They are a precise chain of jobs.

```txt
sync code registers reactions
promise settles
reactions become promise jobs
host runs promise jobs as microtasks
each job may settle the next promise in the chain
```

## 5. Executor Sync, Handler Async

```js
const promise = new Promise(resolve => {
  console.log("executor");
  resolve("value");
});

promise.then(value => console.log(value));

console.log("after");
```

Expected output:

```txt
executor
after
value
```

> [!example] Executor sync, handler async
> The executor is synchronous. The reaction handler is a job/microtask.

## 6. Promise Chains Interleave

```js
Promise.resolve()
  .then(() => console.log("A1"))
  .then(() => console.log("A2"))
  .then(() => console.log("A3"));

Promise.resolve()
  .then(() => console.log("B1"))
  .then(() => console.log("B2"))
  .then(() => console.log("B3"));
```

Expected output:

```txt
A1
B1
A2
B2
A3
B3
```

Why:

- the first handlers for both chains are queued
- each handler settles the next promise in its own chain
- the next handler is queued after the current job completes

Chains do not run as one uninterrupted block.

## 7. `await` Resumption

```js
async function demo() {
  console.log("A");
  await Promise.resolve();
  console.log("C");
}

demo();
console.log("B");
```

Expected output:

```txt
A
B
C
```

`await` suspends the async function and its continuation runs later as a promise job.

## 8. Real Frontend Bug: Reading Before A Promise Reaction

### Problem

```js
let token = null;

refreshToken().then(nextToken => {
  token = nextToken;
});

apiFetch("/profile", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

### Bug

> [!warning] Stale read before reaction
> `apiFetch` runs before the `.then` callback sets `token`, even if `refreshToken` returns an already-fulfilled promise.

### Fix

```js
const token = await refreshToken();

await apiFetch("/profile", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
```

Or keep dependent work inside the promise chain:

```js
refreshToken().then(token => {
  return apiFetch("/profile", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
});
```

## 9. Real Frontend Bug: Swallowing A Rejection

```js
saveProfile()
  .catch(error => {
    reportError(error);
    return null;
  })
  .then(() => {
    showToast("Saved");
  });
```

> [!warning] Catch converts failure to success
> The `catch` returns normally, so the chain becomes fulfilled and the success toast runs.

Fix:

```js
saveProfile()
  .catch(error => {
    reportError(error);
    throw error;
  })
  .then(() => {
    showToast("Saved");
  })
  .catch(() => {
    showToast("Could not save");
  });
```

## 10. Thenable Adoption

When a handler returns a promise, the next promise follows it:

```js
Promise.resolve("user")
  .then(value => {
    return fetchOrders(value);
  })
  .then(orders => {
    console.log(orders);
  });
```

The second `.then` receives the fulfilled value of `fetchOrders`, not the promise object itself.

> [!tip] Return dependent promises
> Production implication: always return the promise for dependent async work. Otherwise the chain loses ownership of the operation.

## 11. Debugging Notes

- If a variable updated in `.then` looks unchanged, check whether you read it synchronously too early.
- If two chains interleave, trace one job at a time.
- If a `catch` seems to hide failure, check whether it returned a normal value.
- If async code is "not waiting", check whether a promise is returned or awaited.
- Use code-output drills to verify your mental model before changing production code.

## 12. Interview Answer

**Short version:** Promise jobs are the scheduled reactions that run `.then`, `.catch`, `.finally`, and async-function continuations. They run asynchronously after the current synchronous code.

**Strong version:** A promise stores fulfillment and rejection reactions. When the promise settles, those reactions are scheduled as ECMAScript jobs. In the browser, the host runs those jobs as microtasks during the microtask checkpoint. This is why `.then` handlers never run synchronously, even on an already-fulfilled promise. Each `.then` returns a new promise, and each reaction job can settle the next promise in the chain. In production, this matters because dependent work must be inside the continuation or use `await`; otherwise code can read stale variables or lose error propagation.

## 13. Common Mistakes

- Expecting `.then` to run before the next synchronous line.
- Forgetting the promise executor runs synchronously.
- Forgetting each `.then` returns a new promise.
- Not returning a promise from a `.then` handler.
- Forgetting `catch` can convert rejection to fulfillment.
- Thinking a promise chain runs as one uninterrupted microtask.
- Confusing promise jobs with timer tasks.

## 14. Practice

1. Predict the executor timing example.
2. Predict the two-chain interleaving example.
3. Explain why `await Promise.resolve()` still yields.
4. Fix a `.then` chain that forgets to return a promise.
5. Show how a `catch` can accidentally trigger a success toast.

## Real-World Use Cases

### Request deduplication by caching the promise

Three components mount at once and each asks for the current user. Caching the **promise** — not the resolved value — collapses them into one request, and late callers attach to whatever is in flight.

```ts
const inflight = new Map<string, Promise<User>>();

function getUser(id: string) {
  if (!inflight.has(id)) {
    inflight.set(id, fetchUser(id).finally(() => inflight.delete(id)));
  }
  return inflight.get(id)!;
}
```

This is safe because reactions on an already-settled promise are still scheduled as jobs: a caller that arrives after fulfillment gets the value asynchronously, through exactly the same code path as a caller that arrived first. See [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]].

### Normalizing a sync-or-async cache read

A data layer returns cached results synchronously and fetches on miss. If the callback fires synchronously on hit and asynchronously on miss, callers see two different orderings and get heisenbugs.

```ts
function getProduct(id: string): Promise<Product> {
  const cached = productCache.get(id);
  // Promise.resolve(...) guarantees callers ALWAYS resume asynchronously,
  // hit or miss — one ordering to reason about.
  return cached ? Promise.resolve(cached) : fetchProduct(id);
}
```

The guarantee doing the work: `.then` handlers never run synchronously, even on a pre-fulfilled promise, so cache hits and misses interleave with surrounding code identically.

> [!tip] Promises un-release Zalgo
> Callback APIs that are "sometimes sync, sometimes async" are a classic bug source. Wrapping the sync path in `Promise.resolve` restores a single scheduling contract.

### `isSubmitting` flips before the save finishes

A form library awaits your submit handler to drive the pending state. If the handler kicks off the save without returning the promise, the handler's own promise fulfills immediately and the button re-enables mid-request.

```tsx
// Bug: handler resolves before saveSettings does
const onSubmit = handleSubmit(values => {
  saveSettings(values).then(() => toast.success("Saved"));
});

// Fix: return it, so the outer promise adopts the save
const onSubmit = handleSubmit(values =>
  saveSettings(values).then(() => toast.success("Saved"))
);
```

The mechanism is thenable adoption from section 10: only a returned promise makes the async function's result track the save; otherwise the chain loses ownership and `isSubmitting` reflects nothing. See [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]].

## Related Notes

- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/07 - Code Output Questions|Code Output Questions]]
- [[01 - Roadmap|Roadmap]]
