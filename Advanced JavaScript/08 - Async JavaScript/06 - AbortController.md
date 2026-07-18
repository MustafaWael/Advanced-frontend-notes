---
tags: [javascript, async, abortcontroller]
module: "08 - Async JavaScript"
priority: must-know
status: not-started
aliases: [Request Cancellation API]
---

# AbortController

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: you can explain controller vs signal, cooperative cancellation, abort errors, timeouts, and React cleanup.
- Production signal: you cancel obsolete reads, avoid stale writes, and do not confuse client abort with server rollback.
- Dependencies: [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]], [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]

## Source Anchors

- [MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [MDN AbortSignal](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal)
- [MDN AbortSignal.timeout](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static)
- [MDN AbortSignal.any](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/any_static)
- [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [React useEffect](https://react.dev/reference/react/useEffect)

## 1. Concept

`AbortController` creates an `AbortSignal`. You pass the signal to an async operation that supports cancellation, and call `controller.abort()` when the work is no longer wanted.

```js
const controller = new AbortController();

fetch("/api/users", {
  signal: controller.signal,
});

controller.abort();
```

The controller is the trigger. The signal is the observable object passed to work.

## 2. Why It Matters

Frontend apps often start async work that becomes obsolete:

- user changes search query
- route changes
- component unmounts
- user closes a modal
- user clicks cancel
- request exceeds a timeout
- a query library cancels stale work

Without cancellation or stale-result protection, old responses can overwrite current UI, waste bandwidth, and make debugging confusing.

## 3. Official Mechanism

`AbortController` and `AbortSignal` are Web APIs, not ECMAScript promise features.

Important pieces:

- `new AbortController()` creates a controller.
- `controller.signal` returns the associated `AbortSignal`.
- `controller.abort(reason?)` marks the signal aborted and dispatches the abort event.
- `signal.aborted` tells you whether it has been aborted.
- `signal.reason` stores the abort reason when available.
- `signal.throwIfAborted()` throws if already aborted.
- `AbortSignal.timeout(ms)` returns a signal that aborts after active time.
- `AbortSignal.any([...signals])` returns a signal that aborts when any input signal aborts.
- `fetch(url, { signal })` observes the signal and rejects when aborted.

Cancellation is cooperative. The async operation must support the signal.

## 4. Mental Model

Abort means "this caller is no longer interested."

It does not automatically mean:

- the server did not receive the request
- a database write was rolled back
- a payment was canceled
- all nested custom work stopped

For reads such as search/autocomplete, aborting obsolete requests is excellent. For critical mutations, use server-side idempotency, transaction design, and explicit cancel APIs.

## 5. Basic Fetch Pattern

```js
async function loadUser(userId, signal) {
  const response = await fetch(`/api/users/${userId}`, { signal });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

const controller = new AbortController();

loadUser("u1", controller.signal).catch(error => {
  if (error instanceof DOMException && error.name === "AbortError") {
    console.log("request aborted");
    return;
  }

  throw error;
});

controller.abort();
```

If you pass a custom abort reason, the rejection shape can differ. In shared utilities, prefer checking `signal.aborted`, `error.name`, and your own known error policy.

## 6. React `useEffect` Cleanup

```jsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/users/${userId}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        setUser(await response.json());
      } catch (error) {
        if (controller.signal.aborted) return;
        setError(error);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      controller.abort();
    };
  }, [userId]);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Could not load user.</p>;
  return <p>{user?.name}</p>;
}
```

Why this works:

- each effect run owns one controller
- cleanup aborts the request when `userId` changes or the component unmounts
- aborted requests do not show user-facing errors
- stale responses are less likely to write state after the latest render

## 7. Search Autocomplete

```js
let currentController;

async function search(query) {
  currentController?.abort();

  const controller = new AbortController();
  currentController = controller;

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (controller.signal.aborted) {
      return [];
    }

    throw error;
  }
}
```

This is useful for obsolete reads. Also consider debouncing so you start fewer requests in the first place.

## 8. Timeout With `AbortSignal.timeout`

```js
async function fetchJsonWithTimeout(url, timeoutMs = 5000) {
  const response = await fetch(url, {
    signal: AbortSignal.timeout(timeoutMs),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
```

Timeout handling:

```js
try {
  await fetchJsonWithTimeout("/api/report", 3000);
} catch (error) {
  if (error instanceof DOMException && error.name === "TimeoutError") {
    showToast("The request timed out.");
  } else if (error instanceof DOMException && error.name === "AbortError") {
    // User/browser abort. Often not a user-facing error.
  } else {
    throw error;
  }
}
```

Browser support for newer static helpers can matter. If you support older environments, use a controller plus `setTimeout`.

## 9. Combining Signals

Use `AbortSignal.any` when more than one reason should cancel the work.

```js
async function loadReport(parentSignal) {
  const timeoutSignal = AbortSignal.timeout(5000);
  const signal = AbortSignal.any([parentSignal, timeoutSignal]);

  const response = await fetch("/api/report", { signal });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
```

Example reasons:

- user navigated away
- component unmounted
- timeout reached
- route-level loader was canceled

## 10. Custom Abortable Work

Promises do not cancel themselves, but your own async functions can observe a signal.

```js
function wait(ms, signal) {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(signal.reason);
      return;
    }

    const timeoutId = setTimeout(resolve, ms);

    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timeoutId);
        reject(signal.reason);
      },
      { once: true }
    );
  });
}
```

Use this pattern for custom timers, polling, streaming loops, and multi-step workflows.

## 11. Real Frontend Bug: Aborting A Payment

### Problem

```js
const controller = new AbortController();

submitPayment(formValues, controller.signal);

controller.abort();
showToast("Payment canceled");
```

### Bug

> [!warning] Abort cancels the client wait, not the server work
> Aborting only stops the client from listening; the request may already have reached the server and completed. For non-idempotent actions like payments, abort is not a safety mechanism — disable duplicate submissions and use server-side idempotency keys instead.

### Better Pattern

- Disable duplicate submissions immediately.
- Send an idempotency key with the mutation.
- Let the server return the definitive transaction state.
- Provide an explicit cancel/refund workflow if the domain supports it.
- Use `AbortController` to stop waiting for obsolete UI reads, not as proof of mutation rollback.

## 12. Production Checklist

- Create a fresh controller per request/effect run.
- Pass the signal to every API that supports it.
- Abort in React effect cleanup.
- Ignore expected abort errors in UI.
- Distinguish timeout from manual abort when the UI needs different copy.
- Combine signals when route, user, and timeout cancellation can all apply.
- Do not reuse a controller after it has been aborted.
- Do not assume abort rolls back server work.
- Remove custom abort listeners or use `{ once: true }`.
- Pair cancellation with request IDs when a library/API does not support signals.

## Real-World Use Cases

### "Stop generating" for a streamed AI response

A chat UI streams tokens from the server and needs a Stop button. The same signal that aborts the connection also cancels mid-stream body reads.

```js
const controller = new AbortController();

async function streamCompletion(prompt) {
  const response = await fetch("/api/chat", {
    method: "POST",
    body: JSON.stringify({ prompt }),
    signal: controller.signal,
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read(); // abort rejects here too
    if (done) break;
    appendToken(decoder.decode(value, { stream: true }));
  }
}

// Stop button handler
stopButton.onclick = () => controller.abort();
```

Works because the fetch signal covers the whole response lifecycle: after headers arrive, aborting rejects the pending `reader.read()`, so a stream that is minutes long stops immediately. Treat the resulting `AbortError` as expected, per section 5. See [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]].

### Bulk event-listener cleanup with one signal

A drag-and-drop interaction registers listeners on `window` and `document`. Instead of keeping references to remove each one, `addEventListener` accepts the same `signal` option — one abort removes them all.

```jsx
useEffect(() => {
  const controller = new AbortController();
  const { signal } = controller;

  window.addEventListener("resize", updateBounds, { signal });
  window.addEventListener("keydown", onEscapeCancel, { signal });
  document.addEventListener("pointermove", onDrag, { signal });
  document.addEventListener("pointerup", onDrop, { signal });

  return () => controller.abort(); // removes all four
}, []);
```

Works because `AbortSignal` is a general cancellation primitive, not a fetch feature — any API that accepts a signal (listeners, `fetch`, custom work) unsubscribes on the same abort event.

> [!tip]
> This also fixes the classic "removeEventListener with a different function reference" bug: no references needed, so there is nothing to mismatch. See [[19 - DOM and Browser APIs/04 - Custom Events and EventTarget|Custom Events and EventTarget]].

### Cancelable job-status polling

After starting a video-transcode job, the UI polls `/jobs/:id` every 2 seconds until it finishes. The loop composes `throwIfAborted`, the abortable fetch, and the abortable `wait` from section 10 — abort at any point exits the whole loop.

```js
async function pollJob(jobId, signal) {
  while (true) {
    signal.throwIfAborted(); // cheap exit between iterations

    const job = await apiFetch(`/jobs/${jobId}`, { signal });
    if (job.status !== "pending") return job;

    await wait(2_000, signal); // the abortable wait from section 10
  }
}
```

Works because cancellation is cooperative: each awaited step observes the same signal, so aborting settles whichever step is currently pending and the rejection unwinds the loop. Combine with `AbortSignal.any` (section 9) to add a route-change or timeout reason.

## 13. Interview Answer

**Short version:** `AbortController` creates a signal. You pass the signal to work like `fetch`, and calling `abort()` notifies that work to stop if it supports cancellation.

**Strong version:** `AbortController` and `AbortSignal` are Web APIs. The controller owns the abort action; the signal is passed to `fetch` or custom async work. Aborting marks the signal aborted and participating APIs reject or stop according to their contract. Cancellation is cooperative, and promises themselves do not cancel. In React, create a controller inside an effect and abort it in cleanup to avoid obsolete requests and stale writes. For critical mutations, aborting the client request is not enough; use server-side idempotency and explicit domain guarantees.

## 14. Common Mistakes

- Reusing one controller for multiple unrelated requests.
- Treating abort errors as user-facing failures.
- Forgetting to abort on effect cleanup.
- Assuming abort cancels server work that already started.
- Using `Promise.race` for timeout but leaving the fetch running.
- Forgetting that a signal stays aborted forever.
- Ignoring browser/runtime support for `AbortSignal.timeout` and `AbortSignal.any`.
- Building custom abortable work without removing abort listeners.

## 15. Practice

1. Write a React effect that fetches with cleanup.
2. Add timeout cancellation to a fetch call.
3. Combine a parent signal with a timeout signal.
4. Implement an abortable `wait(ms, signal)`.
5. Explain why aborting a POST is not the same as rolling back server state.

## Related Notes

- [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
- [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]
- [[19 - DOM and Browser APIs/04 - Custom Events and EventTarget|Custom Events and EventTarget]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
- [[01 - Roadmap|Roadmap]]
- [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Timers, Races, Cancellation and Deterministic Tests]] — how to prove cancellation with a test
