---
tags: [javascript, error-handling, async-error-handling]
module: "11 - Error Handling"
priority: must-know
status: not-started
---

# Async Error Handling

## Maturity Target

- Priority: #must-know
- Study time: 120-160 minutes
- Interview signal: you can predict when `try/catch` catches an async failure, when it does not, and how promise combinators change failure behavior.
- Production signal: async operations have owners, loading states, cancellation paths, retry rules, and visible user recovery.
- Dependencies: [[08 - Async JavaScript/02 - Promises|Promises]], [[08 - Async JavaScript/04 - Async Await|Async Await]], [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]]

## Source Anchors

- [MDN async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [MDN await](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/await)
- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN Promise.all](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/all)
- [MDN Promise.allSettled](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled)
- [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)

## 1. Concept

Async error handling is the discipline of handling failures that travel through promises.

Inside an `async` function:

- returning a value fulfills the returned promise;
- throwing an error rejects the returned promise;
- awaiting a rejected promise throws the rejection reason at the `await` point;
- an uncaught throw inside the async function rejects the function's returned promise.

```js
async function fail() {
  throw new Error("no user");
}

fail().catch((error) => {
  console.log(error.message);
});
```

Expected output:

```txt
no user
```

## 2. Why It Matters

Most frontend failure paths are async: API calls, imports, form submissions, file uploads, timers, IndexedDB, auth refresh, analytics, and route transitions.

The common production problem is not that developers forget `try/catch`. It is that the wrong code owns the promise:

- a click handler starts async work and does not await it;
- an effect starts a request and does not cancel or ignore stale results;
- a form catches every error but cannot map server validation to fields;
- a dashboard uses `Promise.all` when partial results would be better;
- an error boundary is expected to catch a rejection it never sees.

## 3. Accurate Mechanism

`await` pauses the async function and registers continuation work. If the awaited promise fulfills, `await` evaluates to the fulfillment value. If it rejects, `await` throws the rejection reason inside the async function.

```js
async function demo() {
  try {
    await Promise.reject(new Error("failed"));
    console.log("after await");
  } catch (error) {
    console.log("caught:", error.message);
  }
}

demo();
```

Expected output:

```txt
caught: failed
```

Without `await`, the `try` block only sees a promise object.

```js
async function broken() {
  try {
    Promise.reject(new Error("failed"));
    console.log("after call");
  } catch {
    console.log("caught");
  }
}

broken();
```

Expected output:

```txt
after call
```

The rejection is not caught by that `catch`; it becomes an unhandled rejection unless someone handles the promise.

## 4. Mental Model

The error travels with the promise.

`try/catch` catches async failure only when the promise is awaited inside the `try`, returned to a caller that handles it, or has a `.catch()` attached.

Every promise needs an owner. The owner decides:

- what loading state is shown;
- whether cancellation is needed;
- whether retry is safe;
- what user-facing message appears;
- where technical details are logged;
- whether the error should propagate.

## 5. Pattern: Single Operation

```ts
async function loadUser(userId: string) {
  try {
    const response = await fetch(`/api/users/${userId}`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("User load failed", error);
    throw error;
  }
}
```

Why it works:

- network failures reject `fetch`;
- invalid JSON rejects `response.json()`;
- HTTP 4xx/5xx are converted into thrown errors by checking `response.ok`;
- the caller still receives the failure because the catch rethrows.

See [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]].

## 6. Pattern: Granular Steps

Use separate `try/catch` blocks when different failures have different outcomes.

```ts
async function loadProfilePage(userId: string) {
  let user: User;

  try {
    user = await fetchUser(userId);
  } catch (error) {
    // Critical: no page without the user.
    throw new Error("Could not load user profile", { cause: error });
  }

  try {
    const recommendations = await fetchRecommendations(user.id);
    return { user, recommendations };
  } catch (error) {
    // Non-critical: page can still render.
    console.warn("Recommendations unavailable", error);
    return { user, recommendations: [] };
  }
}
```

> [!tip] Tradeoff
> more code, but clearer ownership and better partial UI.

## 7. Pattern: Concurrent Work

`Promise.all` is fail-fast. Use it when every result is required.

```ts
async function loadCheckout(userId: string) {
  const [cart, addresses, paymentMethods] = await Promise.all([
    fetchCart(userId),
    fetchAddresses(userId),
    fetchPaymentMethods(userId)
  ]);

  return { cart, addresses, paymentMethods };
}
```

If any promise rejects, the `await Promise.all(...)` throws the first rejection.

`Promise.allSettled` is better when each widget can succeed or fail independently.

```ts
async function loadDashboard(userId: string) {
  const [stats, feed, alerts] = await Promise.allSettled([
    fetchStats(userId),
    fetchActivityFeed(userId),
    fetchAlerts(userId)
  ]);

  return {
    stats: stats.status === "fulfilled" ? stats.value : null,
    feed: feed.status === "fulfilled" ? feed.value : [],
    alerts: alerts.status === "fulfilled" ? alerts.value : [],
    errors: [stats, feed, alerts].filter((result) => result.status === "rejected")
  };
}
```

Production decision: do not use `allSettled` to ignore important failures. Use it when partial rendering is intentional.

## 8. Real Frontend Bug: `forEach(async ...)`

Problem:

```ts
async function saveAll(items: Item[]) {
  try {
    items.forEach(async (item) => {
      await saveItem(item);
    });
    toast.success("Saved");
  } catch {
    toast.error("Save failed");
  }
}
```

Bug:

- `forEach` does not await async callbacks;
- `toast.success` runs before saves finish;
- rejections inside callbacks do not reach the outer `catch`.

Fix:

```ts
async function saveAll(items: Item[]) {
  try {
    await Promise.all(items.map((item) => saveItem(item)));
    toast.success("Saved");
  } catch (error) {
    console.error("Bulk save failed", error);
    toast.error("Save failed");
  }
}
```

Why it works: `map` creates promises, `Promise.all` owns them, and `await` converts the first rejection into a catchable throw.

## 9. React Effect Example With Cancellation

```tsx
function UserPanel({ userId }: { userId: string }) {
  const [state, setState] = useState<
    | { status: "loading" }
    | { status: "success"; user: User }
    | { status: "error"; message: string }
  >({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setState({ status: "loading" });

      try {
        const user = await fetchUser(userId, controller.signal);
        setState({ status: "success", user });
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          // Expected cleanup path when userId changes or component unmounts.
          return;
        }

        console.error("User load failed", error);
        setState({ status: "error", message: "Could not load user." });
      }
    }

    void load();

    return () => controller.abort();
  }, [userId]);

  if (state.status === "loading") return <Spinner />;
  if (state.status === "error") return <ErrorState message={state.message} />;
  return <UserCard user={state.user} />;
}
```

Why it works:

- the effect creates an owner for the request;
- abort is treated as expected cleanup, not a user-facing error;
- real failures become renderable state;
- `void load()` marks the async call as intentionally not awaited by the effect callback, while `load` still catches internally.

See [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]].

## 10. Production Tradeoffs

| Pattern | Use when | Watch out for |
| --- | --- | --- |
| Single `try/catch` | one operation has one outcome | hides which step failed |
| Per-step `try/catch` | failures need different handling | more ceremony |
| `Promise.all` | all results are required | first rejection controls the outcome |
| `Promise.allSettled` | partial UI is acceptable | can normalize away serious failures |
| Result tuple helper | call site wants no exceptions | can make exceptional paths look ordinary |
| Global rejection handler | monitoring safety net | too late for user-level recovery |

## Real-World Use Cases

### Lazy chunk load failure after a deploy

A user keeps a tab open across a deploy; the old HTML references chunk hashes that no longer exist, so the next route navigation makes `import()` reject with a 404. The failure travels in the promise — nothing throws where `lazy` was declared.

```tsx
const SettingsPage = lazy(() =>
  import("./SettingsPage").catch((error) => {
    console.warn("Chunk load failed, likely a deploy — reloading", error);
    window.location.reload();
    return new Promise<never>(() => {}); // reload takes over from here
  })
);
```

Works because `import()` returns a promise like any fetch: the rejection must be owned where the promise is created, and here the owner's recovery is a fresh document with new chunk hashes.

> [!warning]
> Guard against reload loops (for example a sessionStorage flag) — if the chunk 404s for a non-deploy reason, unconditional reload spins forever.

### Debounced autosave owns its own errors

An editor autosaves two seconds after the last keystroke. By the time the timer fires, the keystroke handler's stack — and any `try/catch` in it — is long gone. The scheduled callback is the only possible owner.

```ts
const scheduleAutosave = debounce(async (draft: Draft) => {
  try {
    await api.saveDraft(draft);
    statusStore.set("saved");
  } catch (error) {
    console.error("Autosave failed", error);
    statusStore.set("unsaved"); // a persistent badge, not a blocking toast
  }
}, 2000);
```

Works because the error travels with the promise created inside the timer callback; no earlier caller can catch it. See [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]] for why the surrounding stack is empty when the timer runs.

### Async Server Components throwing to `error.tsx`

In the Next.js App Router, an async server component is a promise the framework awaits. A rejection during data fetching propagates to the nearest `error.tsx` — the one place async errors do reach a boundary without extra wiring.

```tsx
// app/orders/page.tsx
export default async function OrdersPage() {
  const orders = await fetchOrders(); // rejection propagates to error.tsx
  return <OrderList orders={orders} />;
}
```

Works because the framework is the promise owner here: it awaits the component, so the rejection becomes a throw the boundary can render. Contrast with client-side effects and event handlers, where no boundary sees the rejection — see [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]].

> [!tip]
> The auth token refresh queue and the return-vs-return-await catch behavior are worked through in [[08 - Async JavaScript/04 - Async Await|Async Await]] — both are async-error-ownership problems in disguise.

## 11. Interview Answer

**Short version:** In an async function, `await` turns a rejected promise into a thrown value at that line. `try/catch` catches it only if the promise is awaited inside the `try` or returned to a caller that handles it.

**Strong version:** Async functions always return promises. A thrown error inside an async function rejects that returned promise. `await` suspends the function; when the awaited promise rejects, the rejection reason is thrown at the `await` expression and can be caught by normal `try/catch`. The classic bugs are missing `await`, using `forEach(async ...)`, relying on error boundaries for async effects, and forgetting that `fetch` does not reject for HTTP 4xx/5xx. In production I assign ownership to every promise, choose fail-fast or partial-result behavior intentionally, handle cancellation, and surface user-friendly errors while preserving logs.

## 12. Common Mistakes

- `try { doAsync() } catch {}` without `await`.
- `array.forEach(async ...)` for work that must be awaited.
- Returning fallback values for unexpected errors without logging.
- Using `Promise.all` when partial rendering is the desired UX.
- Using `Promise.allSettled` and forgetting to report rejected results.
- Treating `AbortError` as a real failure shown to users.
- Catching HTTP errors from `fetch` without checking `response.ok`.
- Calling async work in a React event handler without `await` or `.catch()`.

## 13. Practice

1. What logs here?

```js
async function run() {
  try {
    Promise.reject(new Error("x"));
    console.log("A");
  } catch {
    console.log("B");
  }
  console.log("C");
}

run();
```

Expected output: `A`, then `C`; the rejection is not caught because it was not awaited.

2. Rewrite `forEach(async ...)` to use `Promise.all`.
3. Choose between `Promise.all` and `Promise.allSettled` for a dashboard with independent widgets.
4. Write a React effect that ignores `AbortError` but shows other errors.
5. Explain why an async function that throws does not throw synchronously to its caller.

## Related Notes

- [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]]
- [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]]
- [[11 - Error Handling/04 - Promise Rejections|Promise Rejections]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[01 - Roadmap|Roadmap]]
