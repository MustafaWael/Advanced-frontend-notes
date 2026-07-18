---
tags: [javascript, error-handling, promise-rejections]
module: "11 - Error Handling"
priority: must-know
status: not-started
---

# Promise Rejections

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: you can explain rejection propagation, `.catch()`, unhandled rejection reporting, and why global handlers are monitoring rather than recovery.
- Production signal: no important promise is left floating without `await`, `return`, or `.catch()`.
- Dependencies: [[08 - Async JavaScript/02 - Promises|Promises]], [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]], [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]]

## Source Anchors

- [MDN Promise.prototype.catch](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/catch)
- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN Window unhandledrejection event](https://developer.mozilla.org/en-US/docs/Web/API/Window/unhandledrejection_event)
- [MDN Window rejectionhandled event](https://developer.mozilla.org/en-US/docs/Web/API/Window/rejectionhandled_event)
- [HTML Living Standard event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)

## 1. Concept

A promise rejection is a promise's failure state. A rejection becomes unhandled when no rejection handler is attached in time.

Handlers include:

- `.catch(onRejected)`;
- `.then(onFulfilled, onRejected)`;
- `await` inside a `try/catch`;
- returning the promise to a caller that handles it.

```js
Promise.reject(new Error("save failed"))
  .catch((error) => {
    console.log(error.message);
  });
```

Expected output:

```txt
save failed
```

## 2. Why It Matters

Unhandled rejections are one of the easiest ways to ship invisible failures:

- a form button appears to do nothing;
- a mutation fails without a toast;
- an analytics call causes console noise;
- a test passes while production logs fill with unhandled rejections;
- an error boundary never catches the issue because it happened outside render.

The mature habit: every promise has an owner, even fire-and-forget work.

## 3. Accurate Mechanism

`.catch(fn)` is equivalent to `.then(undefined, fn)` and returns a new promise.

```js
const p = Promise.reject(new Error("A"))
  .catch((error) => {
    console.log("caught", error.message);
    return "fallback";
  });

p.then((value) => {
  console.log(value);
});
```

Expected output:

```txt
caught A
fallback
```

The rejection handler transformed the rejected promise chain into a fulfilled chain with value `"fallback"`.

If the catch throws, the next promise rejects.

```js
Promise.reject(new Error("A"))
  .catch(() => {
    throw new Error("B");
  })
  .catch((error) => {
    console.log(error.message);
  });
```

Expected output:

```txt
B
```

## 4. Unhandled Rejection Reporting

When a promise rejects without a handler, the JavaScript engine notifies the host environment. Browsers expose this through `window` events.

```ts
window.addEventListener("unhandledrejection", (event) => {
  console.error("Unhandled promise rejection", event.reason);

  // Optional: report to your monitoring service.
  reportError(event.reason);
});
```

> [!tip] Important
> this is a safety net for logging. It is too late and too context-poor for normal application recovery.

If a handler is attached after the host already reported the rejection, browsers can fire `rejectionhandled`.

```ts
window.addEventListener("rejectionhandled", (event) => {
  console.info("A previously unhandled rejection now has a handler", event.promise);
});
```

## 5. Mental Model

A rejected promise is not a thrown exception flying through the current stack. It is a future failure stored in a promise.

You handle it by:

- awaiting it in a `try/catch`;
- attaching `.catch()`;
- returning it to a caller that does one of those;
- using a framework primitive that owns it.

## 6. Real Frontend Bug: Floating Mutation

Problem:

```tsx
function DeleteButton({ id }: { id: string }) {
  async function handleClick() {
    deleteProduct(id);
    toast.success("Deleted");
  }

  return <button onClick={handleClick}>Delete</button>;
}
```

Bug:

- `deleteProduct(id)` returns a promise;
- the click handler does not await or catch it;
- success is shown before the request finishes;
- rejection becomes unhandled or is only seen by global logging.

Fix:

```tsx
function DeleteButton({ id }: { id: string }) {
  const [isDeleting, setDeleting] = useState(false);

  async function handleClick() {
    setDeleting(true);

    try {
      await deleteProduct(id);
      toast.success("Deleted");
    } catch (error) {
      console.error("Delete failed", error);
      toast.error("Could not delete product.");
    } finally {
      setDeleting(false);
    }
  }

  return (
    <button onClick={handleClick} disabled={isDeleting}>
      {isDeleting ? "Deleting..." : "Delete"}
    </button>
  );
}
```

Why it works:

- the event handler owns the promise;
- success appears only after fulfillment;
- failure becomes user feedback and developer logging;
- `finally` cleans up the pending state.

## 7. Fire-And-Forget Work

Some work is intentionally non-blocking: analytics, logging, prefetching, background cache warming. It still needs rejection handling.

```ts
function trackCheckoutStarted(cartId: string) {
  void sendAnalytics("checkout_started", { cartId }).catch((error) => {
    // Do not block checkout, but do report broken analytics.
    console.warn("Analytics failed", error);
  });
}
```

`void` communicates that the caller is intentionally not awaiting the promise. It does not handle rejections by itself; the `.catch()` still matters.

## 8. React Boundary Misunderstanding

Problem:

```tsx
function SaveButton() {
  function handleClick() {
    saveSettings().catch((error) => {
      throw error;
    });
  }

  return <button onClick={handleClick}>Save</button>;
}
```

Bug:

- the throw happens in a promise reaction, not during render;
- a React error boundary does not catch it;
- the new thrown error becomes another rejected promise.

Fix:

```tsx
function SaveButton() {
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    try {
      await saveSettings();
    } catch (error) {
      console.error("Settings save failed", error);
      setError("Could not save settings.");
    }
  }

  return (
    <>
      <button onClick={handleClick}>Save</button>
      {error && <p role="alert">{error}</p>}
    </>
  );
}
```

If you deliberately want an async error to reach a boundary, use a framework or library integration designed for that path. See [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]].

## 9. Promise Combinators and Rejections

`Promise.all` attaches handlers to every input promise and rejects the combined promise when the first input rejects. Later input settlements are ignored for the combined result, but they are still observed by the combinator.

```js
try {
  await Promise.all([
    fetchUser(),
    fetchOrders(),
    fetchRecommendations()
  ]);
} catch (error) {
  console.log("At least one required request failed");
}
```

Use `Promise.all` when all results are required.

Use `Promise.allSettled` when every result should be inspected.

```js
const results = await Promise.allSettled([
  fetchWidget("sales"),
  fetchWidget("traffic"),
  fetchWidget("alerts")
]);

for (const result of results) {
  if (result.status === "rejected") {
    console.warn("Widget failed", result.reason);
  }
}
```

## 10. Production Checklist

- [ ] Every promise is awaited, returned, or caught.
- [ ] Intentional fire-and-forget calls use `void promise.catch(...)`.
- [ ] Click handlers show failure feedback instead of relying on global events.
- [ ] Global `unhandledrejection` is used for reporting, not normal recovery.
- [ ] Promise combinators match the UX: fail-fast or partial results.
- [ ] Rejections are not swallowed by `.catch(() => {})`.
- [ ] Linting rules such as no-floating-promises are considered for TypeScript projects.
- [ ] Error boundaries are not expected to catch async event handler failures.

## Real-World Use Cases

### Poisoned promise cache in request deduplication

To deduplicate concurrent requests, an API layer caches the in-flight promise. If a rejection is cached forever, every future caller re-observes the same failure — the app stays broken until reload.

```ts
const inflight = new Map<string, Promise<User>>();

function getUser(id: string) {
  let promise = inflight.get(id);

  if (!promise) {
    promise = fetchJson<User>(`/api/users/${id}`);
    promise.catch(() => inflight.delete(id)); // evict failures, never cache them
    inflight.set(id, promise);
  }

  return promise;
}
```

Works because a settled promise never changes state: the cached rejection replays for every consumer, so the eviction `.catch()` is what makes retry possible.

> [!warning]
> Attach the eviction handler as a side chain (`promise.catch(...)` without reassigning) and return the original promise — callers still need to handle the rejection themselves; the eviction catch is bookkeeping, not recovery.

See [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]].

### Floating promise fails CI, passes locally

A prefetch call looks harmless, but test runners like Vitest and Jest fail the process on unhandled rejections. Locally the rejection lands after the test completes; on slower CI it lands mid-run and kills the suite intermittently.

```tsx
useEffect(() => {
  prefetchRecommendations(userId); // floating promise
}, [userId]);

// Fix: own it explicitly.
useEffect(() => {
  void prefetchRecommendations(userId).catch((error) => {
    console.warn("Prefetch failed", error);
  });
}, [userId]);
```

Works because the host (Node's `unhandledRejection` process event) reports any rejection with no handler attached in time — the same mechanism as the browser's `unhandledrejection`, but test runners turn the report into a failure. The `no-floating-promises` lint rule catches this class of bug before CI does.

### Filtering `unhandledrejection` noise before reporting

A raw global handler floods monitoring with canceled-request noise from every route change. Production handlers classify before they report.

```ts
window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason;

  if (reason instanceof DOMException && reason.name === "AbortError") {
    event.preventDefault(); // expected cancellation, keep the console clean
    return;
  }

  reportError(reason); // real unowned failures still reach monitoring
});
```

Works because `event.preventDefault()` suppresses the host's default console reporting for that rejection, while everything else stays a loud signal that some promise is missing an owner. See [[08 - Async JavaScript/06 - AbortController|AbortController]].

## 11. Interview Answer

**Short version:** A promise rejection is handled by `.catch()`, a rejection handler in `.then`, or `await` inside `try/catch`. If no handler is attached, the host can report an unhandled rejection, such as the browser's `unhandledrejection` event.

**Strong version:** Promise failures live in the promise chain. `.catch()` returns a new promise and can either recover by returning a value or continue failure by throwing. `await` converts a rejection into a throw at that line. If a promise rejects and no handler is attached in time, the host environment reports it. I use global handlers only as monitoring safety nets; production code should handle failures close to the operation so it can show the right UI, preserve context, and avoid floating promises.

## 12. Common Mistakes

- Calling an async function without `await`, `return`, or `.catch()`.
- Throwing inside `.catch()` and expecting React error boundaries to catch it.
- Using `.catch(() => {})` to silence failures.
- Showing success before the promise settles.
- Treating global unhandled rejection listeners as recovery logic.
- Forgetting that `.catch()` transforms the chain if it returns a value.
- Forgetting to handle rejections in fire-and-forget analytics or logging calls.

## 13. Practice

1. What logs here?

```js
Promise.reject(new Error("A"))
  .catch(() => "B")
  .then((value) => console.log(value));
```

Expected output: `B`.

2. Why does `void sendAnalytics()` not prevent unhandled rejection by itself?
3. Rewrite a `.then()` chain with no `.catch()` into `async/await`.
4. Explain when a global `unhandledrejection` listener is useful and when it is not enough.
5. Choose `Promise.all` or `Promise.allSettled` for a dashboard where two widgets may fail independently.

## Related Notes

- [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]]
- [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]]
- [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
- [[01 - Roadmap|Roadmap]]
