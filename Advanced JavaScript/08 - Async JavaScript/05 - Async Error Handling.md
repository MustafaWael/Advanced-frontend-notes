---
tags: [javascript, async, async-error-handling]
module: "08 - Async JavaScript"
priority: must-know
status: not-started
---

# Async Error Handling

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: you can explain rejected promises, async throws, propagation, unhandled rejections, and fetch HTTP handling.
- Production signal: you design user recovery, telemetry, retry policy, cancellation handling, and useful error types.
- Dependencies: [[08 - Async JavaScript/02 - Promises|Promises]], [[08 - Async JavaScript/04 - Async Await|Async Await]]

## Source Anchors

- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [MDN Window unhandledrejection event](https://developer.mozilla.org/en-US/docs/Web/API/Window/unhandledrejection_event)
- [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [MDN Response.ok](https://developer.mozilla.org/en-US/docs/Web/API/Response/ok)
- [HTML Living Standard: Unhandled promise rejections](https://html.spec.whatwg.org/multipage/webappapis.html#unhandled-promise-rejections)

## 1. Concept

Async error handling is about where promise rejections are created, where they are caught, and what recovery decision is made.

In `async/await`:

- a rejected awaited promise throws at the `await` line
- throwing inside an async function rejects the returned promise
- a `try/catch` catches awaited rejections only inside its control flow

```js
async function load() {
  throw new Error("failed");
}

try {
  await load();
} catch (error) {
  console.log(error.message);
}

// failed
```

## 2. Why It Matters

Async failures are user-facing:

- network offline
- expired auth token
- 404 item deleted by another user
- 409 conflict during form submit
- 422 server validation error
- 500 server outage
- invalid JSON
- aborted or timed out requests
- stale result ignored because a newer request won

Mature frontend code does not treat all errors as "Something went wrong." It decides which errors should be retried, which should show field messages, which should be ignored, and which should be reported.

## 3. Official Mechanism

Key rules:

- `throw` inside an async function rejects that async function's returned promise.
- `await rejectedPromise` throws the rejection reason inside the async function.
- `.catch(handler)` handles a rejected chain.
- If a `catch` returns normally, the chain becomes fulfilled with the returned value.
- If a `catch` rethrows, the chain remains rejected.
- Browsers expose unhandled promise rejections through the `unhandledrejection` event.
- Rejection reasons can be any JavaScript value, but production code should prefer `Error` objects or subclasses for stack traces and metadata.

## 4. Mental Model

Synchronous errors travel through the current call stack.

Async errors travel with the promise.

```js
try {
  Promise.reject(new Error("bad"));
} catch (error) {
  console.log("caught");
}

// The catch block does not run.
// The promise was rejected, but it was not awaited or returned.
```

Correct:

```js
try {
  await Promise.reject(new Error("bad"));
} catch (error) {
  console.log("caught");
}

// caught
```

## 5. Fetch Error Reality

`fetch` rejects for network-level failures and aborts. It does not reject just because the server returned HTTP 404 or 500.

```js
async function fetchJson(url) {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
```

Without the `response.ok` check, a 500 response may still flow into your success path and fail later in a less useful place.

## 6. Custom Error Types

```ts
class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);

  if (!response.ok) {
    let body: unknown;

    try {
      body = await response.json();
    } catch {
      body = undefined;
    }

    throw new ApiError(`HTTP ${response.status}`, response.status, body);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
```

Why this helps:

- UI can distinguish 401, 403, 404, 409, and 422.
- Telemetry can group errors by type/status.
- retry policy can avoid retrying validation/auth failures.
- components do not each invent HTTP parsing rules.

## 7. Real Frontend Bug: `try/catch` Without `await`

### Problem

```js
async function handleClick() {
  try {
    saveProfile();
    showToast("Saved");
  } catch (error) {
    showToast("Could not save");
  }
}
```

### Bug

If `saveProfile` returns a rejected promise, the `catch` does not catch it because the promise was not awaited or returned. The success toast can show before the save completes.

### Fix

```js
async function handleClick() {
  try {
    await saveProfile();
    showToast("Saved");
  } catch (error) {
    showToast("Could not save");
    reportError(error);
  }
}
```

## 8. Real Frontend Bug: Catching Too Low

### Problem

```ts
async function fetchUser(id: string) {
  try {
    return await apiFetch<User>(`/users/${id}`);
  } catch (error) {
    return null;
  }
}
```

### Bug

The low-level utility hides every failure. The caller cannot tell the difference between "user not found", "offline", "unauthorized", and "server down."

### Better Pattern

```ts
async function fetchUser(id: string) {
  try {
    return await apiFetch<User>(`/users/${id}`);
  } catch (error) {
    throw new Error(`Failed to fetch user ${id}`, {
      cause: error,
    });
  }
}
```

Then decide recovery at the UI/query boundary:

```ts
async function loadUserScreen(id: string) {
  try {
    return await fetchUser(id);
  } catch (error) {
    reportError(error);
    throw error;
  }
}
```

## 9. Error Policy By Category

| Error type | Usually show user? | Usually retry? | Notes |
| --- | --- | --- | --- |
| abort from obsolete request | no | no | expected cleanup |
| timeout | yes | maybe | offer retry or background refresh |
| offline/network failure | yes | yes | detect when useful |
| 401 unauthenticated | yes | no | redirect/login refresh |
| 403 forbidden | yes | no | permission UI |
| 404 missing resource | yes | no | not found or stale link |
| 409 conflict | yes | maybe | user must resolve conflict |
| 422 validation | yes | no | map to fields |
| 500 server error | yes | yes with backoff | report telemetry |
| invalid JSON/schema mismatch | yes in UI, high telemetry | no | contract issue |

These are product decisions, not just language mechanics.

## 10. Retry With Backoff

```ts
function wait(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function retry<T>(
  operation: () => Promise<T>,
  shouldRetry: (error: unknown, attempt: number) => boolean,
  maxAttempts = 3
): Promise<T> {
  let attempt = 0;

  while (true) {
    try {
      return await operation();
    } catch (error) {
      attempt += 1;

      if (attempt >= maxAttempts || !shouldRetry(error, attempt)) {
        throw error;
      }

      await wait(2 ** attempt * 100);
    }
  }
}
```

Use retries for transient failures. Do not blindly retry non-idempotent mutations such as payments or order creation unless the server supports idempotency keys.

## 11. Result Tuple Pattern

Some teams prefer explicit data/error tuples for local flow control:

```ts
type Result<T> = [data: T, error: null] | [data: null, error: Error];

async function toResult<T>(promise: Promise<T>): Promise<Result<T>> {
  try {
    return [await promise, null];
  } catch (error) {
    return [
      null,
      error instanceof Error ? error : new Error(String(error)),
    ];
  }
}

const [user, error] = await toResult(fetchUser("u1"));

if (error) {
  showToast(error.message);
} else {
  renderUser(user);
}
```

> [!tip] Tradeoff
> this avoids nested `try/catch`, but it can also make errors easier to ignore. Use it intentionally.

## 12. React Notes

React error boundaries handle render-time errors. They do not automatically catch every asynchronous error from event handlers, timers, or promises. For async UI work:

- store error state when the component can recover locally
- use query libraries that model `isError`, `error`, retry, and reset state
- throw during render only when a framework boundary is designed to handle it
- report unexpected errors to telemetry

```jsx
function ProfileForm() {
  const [error, setError] = useState(null);

  async function handleSubmit(values) {
    setError(null);

    try {
      await saveProfile(values);
    } catch (error) {
      setError(error);
      reportError(error);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {error ? <ErrorMessage error={error} /> : null}
      <button>Save</button>
    </form>
  );
}
```

## 13. Unhandled Rejection Debugging

Browser example:

```js
window.addEventListener("unhandledrejection", event => {
  console.error("Unhandled promise rejection", event.reason);
});
```

Use this for diagnostics and telemetry, not as a substitute for local error handling. The best place to handle an error is where the code can decide what the user should see or what retry/recovery should happen.

## 14. Production Checklist

- Check `response.ok` for fetch.
- Convert unknown rejection reasons into `Error` objects at boundaries.
- Preserve original causes when wrapping errors.
- Catch errors where recovery is possible.
- Rethrow when the caller still needs to know the operation failed.
- Treat aborts from cleanup as expected, not user-facing failures.
- Do not retry all errors blindly.
- Do not swallow errors in shared data utilities.
- Report unexpected failures with useful context.
- Test offline, timeout, 401, 404, 409, 422, 500, invalid JSON, and abort paths.

## Real-World Use Cases

### Classic interview trap: `return` vs `return await` in `try/catch`

A report screen has a fallback for failed loads — and the fallback never fires. This is the `return`-statement variant of the missing-`await` bug in section 7, and interviewers love it because it looks awaited.

```ts
async function loadReport() {
  try {
    return fetchJson("/api/report"); // rejection escapes the catch
  } catch {
    return FALLBACK_REPORT; // never reached for fetch failures
  }
}
```

Trace: `return fetchJson(...)` hands the still-pending promise to the caller and *exits the function* — the `try` block is already finished by the time the promise rejects, so there is no active `catch` to receive the throw. Async errors travel with the promise (section 4), and this promise left the function before failing.

```ts
async function loadReport() {
  try {
    return await fetchJson("/api/report"); // rejection throws here, inside try
  } catch {
    return FALLBACK_REPORT;
  }
}
```

> [!tip]
> Outside a `try/catch` (or `finally`), plain `return promise` is fine and saves a microtask. The rule is narrow: inside a `try` where you want the `catch` to see the failure, always `return await`.

### Mapping a 422 response to form fields

A profile form should highlight the exact invalid fields, not show a generic toast. The `ApiError` from section 6 carries the parsed body, so the submit handler can branch by status and feed a form library.

```ts
async function onSubmit(values: ProfileValues) {
  try {
    await usersApi.update(userId, values);
  } catch (error) {
    if (error instanceof ApiError && error.status === 422) {
      const fieldErrors = (error.body as { errors: Record<string, string> }).errors;
      for (const [field, message] of Object.entries(fieldErrors)) {
        setError(field, { message }); // react-hook-form style
      }
      return; // handled: no toast, no telemetry noise
    }
    throw error; // everything else escalates to the screen boundary
  }
}
```

Works because the typed error preserves status and body across the promise chain — the policy table in section 9 ("422: map to fields, don't retry") becomes executable. See [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]].

### Start-early promises and unhandled rejections

The "start promises early, await later" parallelization trick from [[08 - Async JavaScript/04 - Async Await|Async Await]] has an error-handling edge: a rejection can go unhandled while you are awaiting something else.

```ts
const settingsPromise = fetchSettings(); // starts now, no handler attached yet
const user = await fetchUser(userId);    // suppose THIS throws first...

const settings = await settingsPromise;  // never reached
```

If `fetchUser` rejects, the function exits before any handler attaches to `settingsPromise`. When it later rejects too, that rejection has no handler — an `unhandledrejection` in the browser, a process crash in default Node.

```ts
const [user, settings] = await Promise.all([
  fetchUser(userId),
  fetchSettings(),
]);
```

Works because `Promise.all` attaches handlers to every input immediately, so a second rejection is observed (and ignored) instead of orphaned.

> [!warning]
> If you must await separately (mixed dependencies), attach a no-op catch to the early promise or your telemetry from section 13 will fill with ghost rejections.

## 15. Interview Answer

**Short version:** In async code, rejected promises are handled by `await` with `try/catch` or by `.catch`. Throwing inside an async function rejects its returned promise.

**Strong version:** Async errors travel through promises. `await` turns a rejection into a throw at that line, so `try/catch` works only for promises that are awaited inside the block. A `catch` that returns normally converts the chain back to fulfillment; rethrowing preserves failure. In frontend code, I check `response.ok`, use typed error classes for HTTP failures, ignore expected aborts, design retry policy by error category, and avoid swallowing errors in shared utilities because callers need recovery context.

## 16. Common Mistakes

- Wrapping a promise-starting call in `try/catch` without `await`.
- Forgetting that `fetch` does not reject on HTTP 404/500.
- Catching too low and returning `null` for every failure.
- Catching and not rethrowing when the caller still needs the failure.
- Showing abort cleanup as a user-facing error.
- Retrying validation, auth, or conflict errors blindly.
- Rejecting with strings instead of `Error` objects.
- Assuming React error boundaries catch every async error.

## 17. Practice

1. Write `apiFetch` that throws `ApiError` for non-2xx responses.
2. Fix a `try/catch` that forgot to `await`.
3. Show how a `.catch` can accidentally turn failure into success.
4. Add retry with backoff only for retryable errors.
5. Decide UI behavior for 401, 403, 404, 409, 422, 500, timeout, and abort.

## Related Notes

- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]
- [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
