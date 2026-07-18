---
tags: [javascript, react, nextjs, abortcontroller-in-effects]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# AbortController in Effects

## Maturity Target

- Priority: #must-know
- Study time: 75-100 minutes
- Interview signal: can explain `AbortController`, `AbortSignal`, cleanup, and abort error handling.
- Production signal: can cancel fetches safely in React effects without false error states or stale loading states.
- Fast track: sections 3, 5, 6, 8, and practice Q1-Q3.

## Source Anchors

- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [MDN: AbortController.abort](https://developer.mozilla.org/en-US/docs/Web/API/AbortController/abort)
- [MDN: AbortSignal](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal)
- [MDN: Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)

## 1. Concept

`AbortController` is a browser API for canceling async operations that accept an `AbortSignal`, especially `fetch`. In a React effect, the standard pattern is:

1. Create one controller inside the effect.
2. Pass `controller.signal` to `fetch`.
3. Return cleanup that calls `controller.abort()`.
4. Treat abort as expected cleanup, not as a user-visible failure.

```tsx
React.useEffect(() => {
  const controller = new AbortController();

  fetch('/api/data', { signal: controller.signal });

  return () => {
    controller.abort();
  };
}, []);
```

## 2. Why It Matters

Ignoring stale results prevents bad state updates, but the request still consumes network and CPU. `AbortController` cancels the request earlier:

- The browser can stop downloading a response that is no longer needed.
- JSON parsing can be avoided.
- Slow route changes do not keep unnecessary work alive.
- Race conditions become easier to reason about.
- Strict Mode cleanup checks reveal missing cancellation sooner.

## 3. Official Mechanism

`AbortController` has a `signal`. The signal can be passed to APIs that support cancellation. Calling `controller.abort()` marks the signal as aborted and notifies consumers.

For `fetch`, aborting causes the fetch promise to reject. In many browser cases, the rejection is a `DOMException` named `AbortError`. Newer APIs also support `signal.reason`, `AbortSignal.timeout(ms)`, and `AbortSignal.any([...signals])`.

Important rules:

- A controller cannot be reset after aborting.
- Create a fresh controller for each operation.
- Do not share one controller across component instances.
- Catch abort errors intentionally.

## 4. Mental Model

The effect owns the request.

```text
effect setup
  create controller
  start fetch with signal

dependency changes or component unmounts
  cleanup calls abort
  signal becomes aborted
  fetch rejects
  catch handler ignores expected abort
```

The controller's lifetime should match the effect invocation's lifetime.

## 5. Real Frontend Example

### Problem: route changes while a request is in flight

```tsx
function useInvoice(invoiceId: string) {
  const [invoice, setInvoice] = React.useState<Invoice | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const controller = new AbortController();

    async function loadInvoice() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/invoices/${invoiceId}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = (await response.json()) as Invoice;
        setInvoice(data);
      } catch (reason) {
        if (controller.signal.aborted) return;

        setError(reason instanceof Error ? reason : new Error(String(reason)));
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadInvoice();

    return () => {
      controller.abort();
    };
  }, [invoiceId]);

  return { invoice, loading, error };
}
```

### Why this works

When `invoiceId` changes, React runs cleanup for the old effect. The cleanup aborts the old request. If the old request rejects because of the abort, the catch handler returns without setting error state. The `finally` block also checks the signal so old requests do not change loading state.

## Real-World Use Cases

### Cancel the previous keystroke's request from an event handler

A user directory searches as you type. The requests are triggered by an event handler, not an effect, so the in-flight controller lives in a ref and each keystroke aborts its predecessor.

```tsx
const inflight = React.useRef<AbortController | null>(null);

async function onQueryChange(term: string) {
  inflight.current?.abort();
  inflight.current = new AbortController();

  try {
    const people = await searchDirectory(term, { signal: inflight.current.signal });
    setResults(people);
  } catch (reason) {
    if (reason instanceof DOMException && reason.name === 'AbortError') return;
    setError(reason as Error);
  }
}
```

Same rule as in effects — one fresh controller per request, whoever owns the request calls `abort()` — just with the handler as the owner.

> [!warning]
> Handler-owned requests outlive unmount. Add a small effect whose cleanup runs `inflight.current?.abort()` so navigation cancels the last request too.

### One signal to remove a batch of listeners

`addEventListener` accepts a `signal` option. A media player registers several window and document listeners; a single `abort()` in cleanup unregisters all of them — no risk of a mismatched `removeEventListener` with a different function reference.

```tsx
React.useEffect(() => {
  const controller = new AbortController();
  const { signal } = controller;

  window.addEventListener('resize', updateLayout, { signal });
  window.addEventListener('scroll', updateProgress, { signal, passive: true });
  document.addEventListener('keydown', handleShortcuts, { signal });

  return () => controller.abort(); // removes all three
}, []);
```

`AbortSignal` is a general cancellation primitive, not a fetch feature — anything that accepts a signal ties its lifetime to the effect. See [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]].

> [!tip]
> This also fixes the classic "listener never removed because the cleanup passed a different function reference" bug — the signal identifies the registration, not the callback.

### Forwarding the client's abort through a route handler

A Next.js route handler proxies a slow search API. The incoming `Request` has its own signal that aborts when the user navigates away — forwarding it cancels the upstream call instead of finishing work nobody will read.

```ts
// app/api/search/route.ts
export async function GET(request: Request) {
  const term = new URL(request.url).searchParams.get('q') ?? '';

  const upstream = await fetch(`${SEARCH_API}?q=${encodeURIComponent(term)}`, {
    signal: request.signal, // browser aborted -> upstream fetch cancelled too
  });

  return Response.json(await upstream.json());
}
```

Signals compose across layers: the browser's abort propagates client → route handler → upstream API, cancelling the whole chain. See [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]].

## 6. Error Handling Details

### Check the signal when possible

```tsx
catch (reason) {
  if (controller.signal.aborted) return;
  setError(reason instanceof Error ? reason : new Error(String(reason)));
}
```

This directly answers: "Was this request intentionally aborted?"

### Check `AbortError` when you do not have the controller in scope

```tsx
catch (reason) {
  if (reason instanceof DOMException && reason.name === 'AbortError') return;
  reportError(reason);
}
```

Avoid checking browser-specific message strings. Error messages vary.

### Timeout

```tsx
async function fetchWithTimeout(url: string, timeoutMs: number) {
  const signal = AbortSignal.timeout(timeoutMs);
  const response = await fetch(url, { signal });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
```

`AbortSignal.timeout(ms)` cancels after a duration. If you also need unmount cancellation, combine it with an effect-owned controller.

### Timeout plus cleanup

```tsx
React.useEffect(() => {
  const controller = new AbortController();
  const timeoutSignal = AbortSignal.timeout(8000);
  const signal = AbortSignal.any([controller.signal, timeoutSignal]);

  fetch(url, { signal }).catch(reason => {
    if (signal.aborted) return;
    reportError(reason);
  });

  return () => {
    controller.abort();
  };
}, [url]);
```

Use this only when your browser support target allows it or when you have a fallback.

## 7. Production Tradeoffs

| Choice | Use when | Tradeoff |
| --- | --- | --- |
| Ignore flag | Async work cannot be canceled or simplicity matters | Network still completes |
| `AbortController` | Fetch or signal-aware API | Must handle expected abort rejection |
| Data library | App has repeated server-state needs | Adds dependency and conventions |
| Server Component fetch | Data can be loaded on server in Next.js | Not interactive client state |
| Timeout signal | Request has strict latency budget | Browser support and UX need thought |

For large applications, prefer a server-state library or framework fetching convention. Manual `AbortController` is still valuable inside custom hooks and browser-only integrations.

## 8. Common Bugs

> [!tip] The effect owns the request
> Create the `AbortController` inside the effect and call `abort()` in its cleanup. One controller per effect run means a dependency change or unmount cancels exactly the request that run started — no shared state, no leaks.

### Bug: module-level controller

```tsx
const controller = new AbortController();

function UserPanel() {
  React.useEffect(() => {
    fetch('/api/user', { signal: controller.signal });
    return () => controller.abort();
  }, []);
}
```

Once this controller is aborted, it stays aborted forever. Future component instances will immediately fail. Create the controller inside the effect.

### Bug: false error UI on navigation

```tsx
catch (reason) {
  setError(reason as Error);
}
```

If navigation aborts the fetch, this shows an error for a normal cleanup. Filter aborts first.

### Bug: `finally` changes loading after abort

```tsx
finally {
  setLoading(false);
}
```

`finally` runs after abort too. Check `signal.aborted` or pair abort with an ignore flag.

## 9. Interview Answer

`AbortController` lets me cancel a fetch by passing its `signal` into `fetch` and calling `abort()` in the effect cleanup. In React, I create one controller per effect invocation so its lifetime matches the request. When the component unmounts or dependencies change, cleanup aborts the old request. The fetch rejects, so I catch the error and ignore it if the signal was aborted or if the error is an `AbortError`. I also guard loading and error state so an aborted request does not update UI after it is no longer current.

## 10. Mistakes to Avoid

| Mistake | Better pattern |
| --- | --- |
| Reusing a controller after abort | Create a new controller per request |
| Showing abort as error | Filter aborts in `catch` |
| Setting loading in unguarded `finally` | Check `!signal.aborted` |
| Thinking abort is only for React | It is a browser cancellation primitive |
| Using timeout without cleanup | Combine timeout with effect cleanup if unmount must cancel too |

## 11. Practice

### Q1. What is logged if cleanup runs before fetch completes?

```tsx
React.useEffect(() => {
  const controller = new AbortController();

  fetch('/api/data', { signal: controller.signal })
    .catch(reason => console.log(reason.name));

  return () => controller.abort();
}, []);
```

Usually `AbortError` is logged. In production code, catch and ignore that expected cancellation.

### Q2. Why is this broken?

```tsx
const controller = new AbortController();

function useData() {
  React.useEffect(() => {
    fetch('/api/data', { signal: controller.signal });
    return () => controller.abort();
  }, []);
}
```

The controller is shared and permanent. After the first cleanup, its signal remains aborted, so future requests using it immediately reject.

### Q3. What is the difference between ignore flag and abort?

An ignore flag prevents state updates after stale async work completes. `AbortController` asks the underlying API to stop the work. You may still combine both when you need very defensive loading and error handling.

## Related Notes

- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Deterministic Tests]] — assert that unmount aborts the in-flight request
