---
tags: [javascript, error-handling, error-handling-checklist]
module: "11 - Error Handling"
priority: must-know
status: not-started
---

# Error Handling Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, diagnose, and fix the behavior without looking.

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes for review, more if the async drills feel slippery.
- Interview signal: you can move from syntax to failure ownership, recovery, logging, and UI state.
- Production signal: your app does not hide failures, mislabel HTTP responses, or rely on global handlers for normal recovery.

## Fast Track Order

1. [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]]
2. [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]]
3. [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]]
4. [[11 - Error Handling/04 - Promise Rejections|Promise Rejections]]
5. [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
6. [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]]

Reason: learn language mechanics first, then async propagation, then API and React production boundaries.

## Core Understanding

- [ ] I can explain `try`, `catch`, `throw`, and `finally` in plain English.
- [ ] I can explain why `finally` runs for throw, return, break, and continue.
- [ ] I can predict what happens when `finally` returns or throws.
- [ ] I can explain why throwing strings is legal but weak production practice.
- [ ] I can name common built-in error types and their typical causes.
- [ ] I can create a custom `Error` subclass with `name`, metadata, and optional `cause`.
- [ ] I can safely handle `unknown` caught values in TypeScript.
- [ ] I can explain why `JSON.stringify(new Error("x"))` gives `{}`.
- [ ] I can explain how `await` turns a rejected promise into a thrown value.
- [ ] I can explain why missing `await` makes `try/catch` ineffective.
- [ ] I can distinguish `Promise.all` from `Promise.allSettled` for failure behavior.
- [ ] I can explain what an unhandled promise rejection is.
- [ ] I can use global rejection handlers as logging safety nets, not normal recovery.
- [ ] I can explain why `fetch` resolves for HTTP 404/500 responses.
- [ ] I can explain what React error boundaries catch and do not catch.

## Source-Backed Terms

| Term | Plain meaning | Technical meaning | Production use |
| --- | --- | --- | --- |
| `throw` | Start an error path. | Produces an abrupt completion with a thrown value. | Use `Error` instances for stack and classification. |
| `catch` | Handle a thrown value. | Receives the nearest thrown completion from protected code. | Recover, translate, log, or rethrow intentionally. |
| `finally` | Always-run cleanup. | Runs before the pending completion exits the construct. | Clear loading state, release resources, abort cleanup. |
| `Error.cause` | Original failure. | Optional value attached when constructing an error. | Preserve low-level context when wrapping errors. |
| Promise rejection | Future failure. | Promise settled rejected with a reason. | Await/catch/return it so it has an owner. |
| Unhandled rejection | Rejection with no handler. | Host reports rejected promise without a handler. | Monitor globally, fix locally. |
| `response.ok` | HTTP success check. | True for status 200-299. | Convert HTTP failures into application errors. |
| Error boundary | Render failure boundary. | React class component catches descendant render/lifecycle errors. | Isolate crashing UI subtrees and show fallback. |
| `AbortError` | Canceled operation. | Common DOMException name for aborted fetch. | Usually ignore or treat as cleanup, not failure. |

## Production Readiness Checklist

- [ ] Every async operation has an owner responsible for success and failure.
- [ ] Every promise is awaited, returned, or caught.
- [ ] Fire-and-forget promises use `void promise.catch(...)`.
- [ ] API wrappers check `response.ok`.
- [ ] HTTP status codes map to specific UI behavior.
- [ ] Form-level and field-level errors are separate.
- [ ] User-facing messages are safe and not raw stack/server text.
- [ ] Technical errors are logged with context.
- [ ] Unknown errors are rethrown when the current layer cannot recover.
- [ ] `finally` blocks do cleanup only.
- [ ] Request cancellation is handled without showing false errors.
- [ ] Error boundaries are placed around risky render subtrees.
- [ ] Lazy-loaded components have both loading and error fallback paths.

## Real-World Scenario Review

### Scenario 1: `finally` suppresses an error

```js
function run() {
  try {
    throw new Error("real failure");
  } finally {
    return "ok";
  }
}

console.log(run());
```

Expected output:

```txt
ok
```

Review answer: returning from `finally` replaced the pending throw. Production fix: remove the return from `finally` and use it only for cleanup.

### Scenario 2: HTTP error treated as success

```ts
async function loadProduct(id: string) {
  const response = await fetch(`/api/products/${id}`);
  return response.json();
}
```

Bug: a 404 response resolves and may parse into an error object that the UI treats as a product.

Fix:

```ts
async function loadProduct(id: string) {
  const response = await fetch(`/api/products/${id}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}
```

### Scenario 3: Floating promise in click handler

```tsx
function SaveButton() {
  function handleClick() {
    saveSettings();
    toast.success("Saved");
  }

  return <button onClick={handleClick}>Save</button>;
}
```

Bug: the success toast appears before the promise settles, and rejection may be unhandled.

Fix: make `handleClick` async, `await saveSettings()`, show success after fulfillment, and catch failure locally.

### Scenario 4: Error boundary expected to catch async work

```tsx
useEffect(() => {
  fetchUser().then(setUser);
}, []);
```

Bug: parent error boundaries do not catch fetch rejection. The effect must catch the promise and render error state or use a deliberate boundary integration.

### Scenario 5: Error object sent to logging as `{}`

```ts
fetch("/api/log", {
  method: "POST",
  body: JSON.stringify({ error: new Error("boom") })
});
```

Bug: standard `Error` fields do not serialize as expected. Use a serializer that extracts `name`, `message`, `stack`, and `cause` carefully.

## Code-Output Drills

### Drill 1: `finally` wins

```js
function test() {
  try {
    return "try";
  } catch {
    return "catch";
  } finally {
    return "finally";
  }
}

console.log(test());
```

Expected output: `finally`.

### Drill 2: Missing `await`

```js
async function test() {
  try {
    Promise.reject(new Error("x"));
    console.log("A");
  } catch {
    console.log("B");
  }
  console.log("C");
}

test();
```

Expected output: `A`, `C`, then an unhandled rejection may be reported by the host.

### Drill 3: Catch transforms chain

```js
Promise.reject(new Error("A"))
  .catch(() => "fallback")
  .then((value) => console.log(value));
```

Expected output: `fallback`.

### Drill 4: Error serialization

```js
console.log(JSON.stringify(new Error("boom")));
```

Expected output: `{}`.

### Drill 5: Fetch status

```ts
const response = await fetch("/api/missing");
console.log(response.ok);
```

Expected behavior: if the server returns 404, the promise still fulfills and `response.ok` is `false`.

## Interview Prompts

1. Explain `try/catch/finally` and the `finally` override rule.
2. Why should production code throw `Error` objects instead of strings?
3. What does `Error.cause` solve?
4. Why does `try { doAsync() } catch {}` fail without `await`?
5. What is an unhandled promise rejection?
6. When is a global `unhandledrejection` listener useful?
7. Why does `fetch` not throw on 404?
8. How would you design an API wrapper for a React app?
9. What do React error boundaries catch?
10. Where would you place boundaries in a dashboard?

## Self-Review Rubric

| Level | What your answer sounds like |
| --- | --- |
| Weak | "Use try/catch to stop errors." |
| Junior-plus | "Async errors need await, and fetch needs response.ok." |
| Mid-level | "I catch only recoverable errors, rethrow unknowns, preserve cause, and model API failures by type." |
| Strong mid-level | "I can design error ownership across language mechanics, promises, API adapters, React state, route boundaries, logging, cancellation, retries, and user-safe recovery." |

## Final Module Test

Before leaving this module, you should be able to:

- predict output for `finally` return examples;
- write a custom `ApiError`;
- wrap an error with `cause`;
- safely narrow `unknown` in a catch block;
- explain rejected promises and unhandled rejections;
- fix a missing-`await` bug;
- choose `Promise.all` or `allSettled`;
- build a `fetchJson` wrapper;
- handle 401, 404, 422, 429, and 500 differently;
- add request cancellation to a React effect;
- explain why an error boundary will not catch async event-handler failures;
- design fallback and reset behavior for a route or widget boundary.

## Related Notes

- [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]]
- [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]]
- [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]]
- [[11 - Error Handling/04 - Promise Rejections|Promise Rejections]]
- [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[01 - Roadmap|Roadmap]]
