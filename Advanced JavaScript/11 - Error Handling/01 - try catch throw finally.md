---
tags: [javascript, error-handling, try-catch-throw-finally]
module: "11 - Error Handling"
priority: must-know
status: not-started
---

# try catch throw finally

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can explain control flow, rethrowing, `finally` override behavior, and why sync `try/catch` does not catch later async work.
- Production signal: you catch only what you can handle, preserve diagnostic context, and avoid hiding failures.
- Dependencies: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]], [[08 - Async JavaScript/04 - Async Await|Async Await]], [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]]

## Source Anchors

- [MDN try...catch](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/try...catch)
- [MDN throw](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/throw)
- [MDN Error](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error)
- [MDN async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [ECMAScript Completion Records](https://tc39.es/ecma262/#sec-completion-record-specification-type)

## 1. Concept

`try/catch/finally` is JavaScript's structured exception handling syntax.

- `try` runs code that might fail.
- `throw` creates an exception path.
- `catch` handles a thrown value from the nearest protected `try`.
- `finally` runs cleanup code before the whole construct exits.

```js
try {
  JSON.parse("{ bad json");
} catch (error) {
  console.log("Could not parse JSON");
} finally {
  console.log("Finished parse attempt");
}
```

Expected output:

```txt
Could not parse JSON
Finished parse attempt
```

## 2. Why It Matters

Error handling is not only about preventing crashes. In frontend work it decides:

- whether users see a recoverable UI or a blank screen;
- whether developers receive useful logs;
- whether validation errors are separated from programmer bugs;
- whether cleanup runs after failed work;
- whether unknown errors keep propagating to a higher owner.

A mature codebase treats error paths as part of the control flow contract, not as leftover code in a generic `catch`.

## 3. Official Mechanism

In the ECMAScript model, statements complete with a completion type such as normal, throw, return, break, or continue. A thrown exception is an abrupt completion. A `catch` handles a throw completion. A `finally` block runs before the pending completion continues.

```js
function example() {
  try {
    return "try";
  } finally {
    console.log("cleanup");
  }
}

console.log(example());
```

Expected output:

```txt
cleanup
try
```

The return from `try` is pending while `finally` runs. Because `finally` does not return or throw, the original return continues.

## 4. The `finally` Override Rule

If `finally` produces its own control flow, it overrides the pending one from `try` or `catch`.

```js
function dangerous() {
  try {
    throw new Error("database failed");
  } catch {
    return "fallback";
  } finally {
    return "finally wins";
  }
}

console.log(dangerous());
```

Expected output:

```txt
finally wins
```

> [!warning] Finally return suppresses errors
> Failure mode: the thrown error and the `catch` return were both suppressed by the `finally` return.

> [!tip] Cleanup only in finally
> Production rule: use `finally` for cleanup, not for returning business values.

```ts
async function submitWithLock(payload: Payload) {
  setSubmitting(true);

  try {
    return await savePayload(payload);
  } finally {
    // Cleanup only. Do not return from here.
    setSubmitting(false);
  }
}
```

## 5. Mental Model

`catch` is for recovery or translation. `finally` is for cleanup.

Ask three questions:

1. Can this layer actually recover?
2. If not, should it add context and rethrow?
3. What cleanup must happen whether the operation succeeds or fails?

## 6. Real Frontend Example: Local Storage Recovery

> [!example] Local storage recovery walkthrough
> Problem: local storage can contain invalid JSON, be unavailable, or throw in privacy/storage-limit scenarios. The app should recover with defaults, but it should not hide every bug.

```ts
type Preferences = {
  theme: "light" | "dark";
  compact: boolean;
};

const DEFAULT_PREFERENCES: Preferences = {
  theme: "light",
  compact: false
};

function isPreferences(value: unknown): value is Preferences {
  return (
    typeof value === "object" &&
    value !== null &&
    (value as Preferences).theme === "light" || (value as Preferences).theme === "dark"
  );
}
```

The guard above has a precedence bug. The `||` part can run even when `value` is not an object. Make the grouping explicit.

```ts
function isPreferences(value: unknown): value is Preferences {
  if (typeof value !== "object" || value === null) return false;

  const maybe = value as Partial<Preferences>;
  return (
    (maybe.theme === "light" || maybe.theme === "dark") &&
    typeof maybe.compact === "boolean"
  );
}

export function readPreferences(): Preferences {
  try {
    const raw = localStorage.getItem("preferences");
    if (raw === null) return DEFAULT_PREFERENCES;

    const parsed: unknown = JSON.parse(raw);
    if (!isPreferences(parsed)) {
      return DEFAULT_PREFERENCES;
    }

    return parsed;
  } catch (error) {
    // Expected recovery boundary: corrupt storage should not break app startup.
    console.warn("Using default preferences after storage read failed", error);
    return DEFAULT_PREFERENCES;
  }
}
```

Why this works:

- the `try` block is narrow and protects only storage/parsing logic;
- the fallback is domain-appropriate;
- the catch logs enough context for debugging;
- the code does not catch unrelated rendering errors.

## 7. Rethrow Pattern

Catch only what this layer understands. Rethrow the rest.

```ts
class ValidationError extends Error {
  constructor(public fieldErrors: Record<string, string>) {
    super("Validation failed");
    this.name = "ValidationError";
  }
}

async function createAccount(input: AccountInput) {
  try {
    return await submitAccount(input);
  } catch (error) {
    if (error instanceof ValidationError) {
      return {
        ok: false,
        fieldErrors: error.fieldErrors
      };
    }

    // Unknown failures still belong to a higher-level handler.
    throw error;
  }
}
```

> [!tip] Handle known, rethrow unknown
> Production benefit: validation errors become form state, while unexpected errors still reach logging, an error boundary, or a route-level error page.

## 8. Sync Boundary vs Async Boundary

`try/catch` catches synchronous throws inside its dynamic execution path. It does not catch errors that occur later unless you `await` the promise inside the `try`.

```js
async function broken() {
  try {
    Promise.reject(new Error("late failure"));
  } catch {
    console.log("caught");
  }
}

broken();
```

> [!warning] Unawaited rejections escape catch
> Expected behavior: `catch` does not run. The rejection belongs to the promise that was created and then ignored.

Fix:

```js
async function fixed() {
  try {
    await Promise.reject(new Error("late failure"));
  } catch (error) {
    console.log("caught:", error.message);
  }
}

fixed();
```

Expected output:

```txt
caught: late failure
```

See [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]] and [[11 - Error Handling/04 - Promise Rejections|Promise Rejections]].

## 9. Production Tradeoffs

| Decision | Good when | Risk |
| --- | --- | --- |
| Catch locally | the layer can recover or translate | broad catch hides programmer bugs |
| Rethrow unknown errors | higher layer has better context | user may need a fallback UI |
| Return fallback data | degraded UI is acceptable | fallback can mask data integrity issues |
| Throw typed errors | callers need branching behavior | too many custom types can become noise |
| Use `finally` | cleanup must always run | returning or throwing there can suppress the real outcome |

## 10. Debugging Checklist

- Find the first throw, not only the place where the error was observed.
- Check whether the error is sync or promise-based.
- Check whether a `catch` is swallowing without logging or rethrowing.
- Search for `return` or `throw` inside `finally`.
- Make sure cleanup code cannot throw and hide the original problem.
- Normalize non-`Error` thrown values before logging.

## Real-World Use Cases

### Third-party script isolation at app boot

Analytics, chat widgets, and A/B testing SDKs initialize during app startup, and any of them can throw on a bad config or blocked network. One broken vendor must not blank the whole app.

```ts
function initThirdParty() {
  for (const vendor of [initAnalytics, initChatWidget, initABTesting]) {
    try {
      vendor();
    } catch (error) {
      console.error(`Third-party init failed: ${vendor.name}`, error);
      // Boot continues; the app works without this vendor.
    }
  }
}
```

This is a legitimate catch-and-continue boundary: the layer can genuinely recover (the product works without the vendor), so log-and-swallow is correct here — the same rule that makes it wrong for your own business logic.

### Optimistic UI rollback, then rethrow

A favorites button flips local state instantly, then persists. On failure this layer knows how to undo the state but not what UI to show — so it rolls back and rethrows.

```ts
async function toggleFavorite(productId: string) {
  const previous = favoritesStore.get();
  favoritesStore.toggle(productId); // optimistic update

  try {
    await api.toggleFavorite(productId);
  } catch (error) {
    favoritesStore.set(previous); // undo what this layer owns
    throw error;                  // the caller still owns user feedback
  }
}
```

This is partial handling plus rethrow: `catch` runs the rollback, and rethrowing keeps the abrupt completion propagating to a handler with UI context.

### Measuring request duration in `finally`

A search box reports latency to monitoring. The measurement must record on success and failure alike, without altering either outcome.

```ts
async function searchProducts(query: string) {
  const started = performance.now();

  try {
    return await fetchJson<Product[]>(`/api/search?q=${encodeURIComponent(query)}`);
  } finally {
    reportMetric("search_duration_ms", performance.now() - started);
  }
}
```

Works because `finally` runs before both normal and throw completions continue — and because it only performs side effects, it never overrides them.

> [!warning]
> The `return await` is load-bearing: with a bare `return fetchJson(...)`, the function exits before the promise settles, so `finally` would measure scheduling time, not request time. See [[08 - Async JavaScript/04 - Async Await|Async Await]] for the full return-vs-return-await behavior.

## 11. Interview Answer

**Short version:** `try` protects code, `throw` creates an exception path, `catch` handles the thrown value, and `finally` always runs before the construct exits. `finally` is for cleanup, and a `return` or `throw` inside `finally` overrides any pending result from `try` or `catch`.

**Strong version:** JavaScript models exceptions as abrupt completion. A thrown value propagates until a matching `catch` handles it. `finally` runs for normal completion, thrown exceptions, returns, breaks, and continues. If `finally` produces its own completion, it replaces the pending one, which is why returning from `finally` can accidentally suppress errors. In production I keep `try` blocks narrow, catch only expected failures, rethrow unknown errors, and use `finally` only for cleanup. For async work, I remember that `try/catch` catches awaited rejections, not floating promises.

## 12. Common Mistakes

- Catching every error and returning `null` with no log.
- Returning from `finally`.
- Throwing strings instead of `Error` objects.
- Catching an error, wrapping it, and losing the original cause.
- Assuming `try/catch` catches `setTimeout`, event handler, or unawaited promise failures.
- Putting too much unrelated code inside one `try` block.
- Using `catch {}` as a way to hide real bugs.

## 13. Practice

1. What does this return, and why?

```js
function test() {
  try {
    return 1;
  } catch {
    return 2;
  } finally {
    return 3;
  }
}

console.log(test());
```

Expected output: `3`. The `finally` return overrides the pending `try` return.

2. Rewrite a broad `catch` so it handles `ValidationError` locally and rethrows everything else.
3. Explain why `try { fetch("/api") } catch {}` does not catch an HTTP 500 response.
4. Write a `finally` block that correctly clears a loading state without changing the operation result.

## Related Notes

- [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]]
- [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]]
- [[11 - Error Handling/04 - Promise Rejections|Promise Rejections]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]
- [[01 - Roadmap|Roadmap]]
