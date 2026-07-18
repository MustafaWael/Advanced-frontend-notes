---
tags: [javascript, async, async-checklist]
module: "08 - Async JavaScript"
priority: must-know
status: not-started
---

# Async Checklist

Use this as an active review. A checkbox is complete only when you can explain the idea, predict code output, name the production bug, and write the safer pattern without looking.

## Fast Track Order

1. [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]]
2. [[08 - Async JavaScript/02 - Promises|Promises]]
3. [[08 - Async JavaScript/04 - Async Await|Async Await]]
4. [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
5. [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
6. [[08 - Async JavaScript/06 - AbortController|AbortController]]
7. [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]

## Core Understanding

- [ ] I can separate ECMAScript promise behavior from browser host APIs such as `fetch`, timers, and DOM events.
- [ ] I can explain run-to-completion and why callbacks do not interrupt each other halfway.
- [ ] I can explain tasks vs microtasks at a practical level.
- [ ] I know promise states: pending, fulfilled, rejected, and settled.
- [ ] I know that resolved is not always the same as fulfilled.
- [ ] I can explain why `.then` returns a new promise.
- [ ] I can explain what happens when a `.then` handler returns a value, returns a promise, throws, or is missing.
- [ ] I know that an async function always returns a promise.
- [ ] I know that `await` yields the async function continuation, not the whole thread.
- [ ] I can explain why promises do not provide cancellation by themselves.

## Promise Combinators

- [ ] I use `Promise.all` when all operations are required.
- [ ] I know `Promise.all` preserves input order in the result array.
- [ ] I know `Promise.all` fails fast but does not cancel other in-flight operations.
- [ ] I use `Promise.allSettled` when partial success is acceptable.
- [ ] I can process `PromiseSettledResult` objects safely.
- [ ] I use `Promise.race` when the first settled result wins.
- [ ] I know a `Promise.race` timeout does not automatically abort fetch.
- [ ] I use `Promise.any` when the first successful source wins.
- [ ] I know `Promise.any` rejects with `AggregateError` when all inputs reject.
- [ ] I can describe the empty iterable behavior for `all`, `allSettled`, `race`, and `any`.

## Async Await Readiness

- [ ] I can rewrite a promise chain as `async/await` without changing behavior.
- [ ] I can identify sequential awaits that should be parallelized.
- [ ] I can identify real dependencies that should stay sequential.
- [ ] I can fix `forEach(async ...)` with `for...of` or `Promise.all(arr.map(...))`.
- [ ] I know why a React `useEffect` callback should not be async.
- [ ] I can write an async React event handler with `try/catch/finally`.
- [ ] I can explain top-level await and server/client placement in Next.js.

## Error Handling

- [ ] I check `response.ok` for fetch.
- [ ] I understand that fetch rejects for network-level failure and abort, not for HTTP 404/500 by itself.
- [ ] I catch async errors where recovery is possible.
- [ ] I rethrow errors when callers still need to know the operation failed.
- [ ] I use `Error` objects or custom error classes instead of rejecting strings.
- [ ] I can explain how a `catch` can turn a rejected chain into a fulfilled chain.
- [ ] I distinguish abort, timeout, validation, auth, not-found, conflict, and server errors.
- [ ] I do not blindly retry non-idempotent mutations.
- [ ] I can add useful telemetry context to API failures.

## Cancellation And Race Conditions

- [ ] I can create an `AbortController` and pass its `signal` to fetch.
- [ ] I can abort a request in React effect cleanup.
- [ ] I ignore expected abort errors in UI.
- [ ] I know that a signal remains aborted forever.
- [ ] I know not to reuse an aborted controller.
- [ ] I can use `AbortSignal.timeout` where supported.
- [ ] I can combine signals with `AbortSignal.any` where supported.
- [ ] I can implement stale response protection with a request id.
- [ ] I know aborting a client request does not prove server work was rolled back.

## API Integration

- [ ] I can write a typed `apiFetch` boundary.
- [ ] I can parse error bodies safely.
- [ ] I handle `204 No Content`.
- [ ] I separate transport utilities from domain API operations.
- [ ] I model request state without contradictory booleans.
- [ ] I prevent duplicate submits in UI and know when server idempotency is required.
- [ ] I can decide whether a request belongs in a server component, client effect, event handler, route handler, or query layer.
- [ ] I test success, loading, failure, abort, stale response, invalid JSON, and duplicate submit paths.

## Code Output Drills

### Microtasks Before Timers

```js
console.log("1");

setTimeout(() => console.log("2"), 0);

Promise.resolve()
  .then(() => console.log("3"))
  .then(() => console.log("4"));

console.log("5");
```

Expected:

```txt
1
5
3
4
2
```

Why: synchronous code runs first, promise reactions run as microtasks, and the timer callback runs as a later task.

### Promise Executor Timing

```js
const promise = new Promise(resolve => {
  console.log("executor");
  resolve("value");
});

promise.then(value => console.log(value));

console.log("after");
```

Expected:

```txt
executor
after
value
```

Why: the executor runs synchronously, but the `.then` handler runs later.

### Catch Converts Failure

```js
Promise.reject(new Error("bad"))
  .catch(error => error.message)
  .then(value => console.log(value));
```

Expected:

```txt
bad
```

Why: `catch` returned a normal value, so the chain became fulfilled.

### Await Yields

```js
async function demo() {
  console.log("A");
  await 1;
  console.log("C");
}

demo();
console.log("B");
```

Expected:

```txt
A
B
C
```

Why: `await` yields even for a non-promise value.

### Async forEach Trap

```js
async function run() {
  [1, 2].forEach(async value => {
    await Promise.resolve();
    console.log(value);
  });

  console.log("done");
}

run();
```

Expected:

```txt
done
1
2
```

Why: `forEach` does not wait for promises returned by its callback.

### Promise.all Order

```js
function wait(ms, value) {
  return new Promise(resolve => setTimeout(() => resolve(value), ms));
}

const values = await Promise.all([
  wait(20, "slow"),
  wait(1, "fast"),
]);

console.log(values);
```

Expected:

```js
["slow", "fast"]
```

Why: `Promise.all` returns values in input order, not completion order.

### Promise.any Total Failure

```js
try {
  await Promise.any([
    Promise.reject(new Error("A")),
    Promise.reject(new Error("B")),
  ]);
} catch (error) {
  console.log(error instanceof AggregateError);
  console.log(error.errors.length);
}
```

Expected:

```txt
true
2
```

Why: `Promise.any` rejects only after every input rejects.

## Production Scenarios To Practice

- [ ] Build a search box that aborts obsolete requests.
- [ ] Build a save button that prevents duplicate submission.
- [ ] Build a dashboard that uses `allSettled` for independent widgets.
- [ ] Build a required profile loader with `Promise.all`.
- [ ] Add a fetch timeout with `AbortSignal.timeout` or controller fallback.
- [ ] Write an `apiFetch` wrapper that throws `ApiError`.
- [ ] Map a 422 response to field-level form errors.
- [ ] Add retry with backoff only for retryable errors.
- [ ] Log a request id through start, response, state apply, abort, and failure.
- [ ] Explain why a payment mutation needs server idempotency.

## Interview Prompts

1. What is the difference between sync and async JavaScript?
2. What are promise states, and can a promise settle more than once?
3. What does `.then` return?
4. Why does `Promise.resolve().then(...)` run before `setTimeout(..., 0)`?
5. What is the difference between `Promise.all` and `Promise.allSettled`?
6. What is the difference between `Promise.race` and `Promise.any`?
7. Why does `await` not block the JavaScript thread?
8. Why is `forEach(async ...)` a bug when completion matters?
9. Why does fetch need `response.ok` checks?
10. How does `AbortController` prevent stale React effects?
11. Does aborting a request roll back server work?
12. How would you design a production API layer?

## Self-Review Rubric

| Level | What you can do |
| --- | --- |
| Junior | Use `await fetch` and basic `try/catch`. |
| Growing mid-level | Explain promises, combinators, and common async bugs. |
| Strong mid-level | Design cancellation, error policy, retries, dedupe, and request state. |
| Senior signal | Reason about server/client placement, idempotency, observability, stale data, and UX recovery. |

## Related Notes

- [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
