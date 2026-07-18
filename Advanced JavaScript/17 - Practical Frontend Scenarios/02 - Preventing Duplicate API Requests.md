---
tags: [javascript, scenarios, react, preventing-duplicate-api-requests]
module: "17 - Practical Frontend Scenarios"
priority: must-know
status: not-started
---

# Preventing Duplicate API Requests

## Maturity Target

- Priority: #must-know
- Study time: 60-80 minutes
- Interview signal: can distinguish duplicate reads, duplicate mutations, debounce, cancellation, and idempotency.
- Production signal: can prevent double submits and request storms without relying only on frontend luck.
- Fast track: focus on sections 2, 4, 5, and 8.

## Source Anchors

- [MDN: Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)

## 1. Scenario

A user clicks "Submit" twice before the first request finishes. Or multiple components mount and fetch the same resource. Or a search box fires a request on every keypress.

These are different duplicate-request problems:

| Problem | Example | Main fix |
| --- | --- | --- |
| Duplicate mutation | double form submit | disable, guard, idempotency key |
| Duplicate read | same query from many components | cache/dedupe by key |
| Request storm | search on every keypress | debounce plus cancellation |
| Stale completion | old request finishes last | ignore flag or abort |

## 2. Broken Version

```tsx
function CheckoutButton({ cartId }: { cartId: string }) {
  async function handleClick() {
    // BUG: every click sends a new POST.
    // If the server processes both, the user may be charged twice.
    await fetch(`/api/checkout/${cartId}`, { method: 'POST' });
  }

  return <button onClick={handleClick}>Pay</button>;
}
```

## 3. Root Cause

`fetch` starts network work and returns a Promise. It does not block later clicks. React does not automatically know this mutation is already in flight. If the handler can run twice, two independent server operations can start.

For critical mutations, frontend prevention is not enough. The server should also protect the operation with idempotency.

## 4. Frontend Fix: Pending Guard

```tsx
function CheckoutButton({ cartId }: { cartId: string }) {
  const [pending, setPending] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  async function handleClick() {
    if (pending) return;

    setPending(true);
    setError(null);

    try {
      const response = await fetch(`/api/checkout/${cartId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // The server should treat this key as "run this mutation once".
          idempotencyKey: crypto.randomUUID(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason : new Error(String(reason)));
    } finally {
      // finally prevents a permanently disabled button after errors.
      setPending(false);
    }
  }

  return (
    <>
      <button disabled={pending} onClick={handleClick}>
        {pending ? 'Paying...' : 'Pay'}
      </button>
      {error ? <p role="alert">{error.message}</p> : null}
    </>
  );
}
```

## 5. Race Detail: State Guard Timing

For very rapid events in the same tick, state can lag behind because `setPending(true)` schedules a render. A ref can provide an immediate synchronous guard.

```tsx
function useSingleFlight<T extends unknown[]>(
  fn: (...args: T) => Promise<void>
) {
  const inFlight = React.useRef(false);

  return React.useCallback(async (...args: T) => {
    if (inFlight.current) return;

    inFlight.current = true;

    try {
      await fn(...args);
    } finally {
      inFlight.current = false;
    }
  }, [fn]);
}
```

Use state for UI display. Use a ref when you also need an immediate imperative guard.

## 6. Read Requests: Dedupe By Key

```tsx
const requestCache = new Map<string, Promise<User>>();

function fetchUserOnce(userId: string) {
  const key = `user:${userId}`;
  const cached = requestCache.get(key);

  if (cached) return cached;

  const request = fetch(`/api/users/${userId}`)
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json() as Promise<User>;
    })
    .finally(() => {
      // Remove if you want only in-flight dedupe.
      // Keep it if you want a longer-lived cache.
      requestCache.delete(key);
    });

  requestCache.set(key, request);
  return request;
}
```

Production apps usually use a library for this because cache invalidation, retries, and stale data get complex quickly.

## 7. Tradeoffs

- Disable buttons for mutations, but also make server mutations idempotent.
- Debounce reduces starts; it does not cancel already-started requests.
- Abort is right for superseded reads; it does not roll back a mutation that reached the server.
- Cache/dedupe reads by key; avoid deduping unlike requests accidentally.
- Always reset pending state in `finally`.

## 8. Production Checklist

- [ ] Is this a read or mutation?
- [ ] Can the handler run twice before state updates?
- [ ] Is the trigger disabled while pending?
- [ ] Is there a ref or single-flight guard for critical actions?
- [ ] Does the server support idempotency for dangerous mutations?
- [ ] Are duplicate reads deduped by a stable key?
- [ ] Are errors and aborts handled without stuck loading state?
- [ ] Did I check the Network panel under rapid clicks?

## 9. Interview Angle

Strong answer:

"For duplicate POSTs, I disable the trigger and guard the handler, but for payment or booking I also require server idempotency because the frontend can be bypassed. For duplicate GETs, I dedupe by cache key or use a data library. Debounce helps request storms, but it does not solve in-flight race conditions by itself."

## Related Notes

- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
