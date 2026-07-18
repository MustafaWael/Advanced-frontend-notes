---
tags: [javascript, react, nextjs, async-effects-and-race-conditions]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# Async Effects and Race Conditions

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: can explain async effect races, cleanup timing, and why `useEffect(async () => ...)` is wrong.
- Production signal: can prevent stale results, loading flicker, unmounted updates, and duplicate request bugs.
- Fast track: sections 3, 5, 6, 8, and practice Q1-Q4.

## Source Anchors

- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [React docs: Synchronizing with Effects](https://react.dev/learn/synchronizing-with-effects)
- [React docs: You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
- [MDN: Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- [MDN: Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)

## 1. Concept

An async effect race happens when multiple async operations are in flight, and an older operation finishes after a newer one and updates state with stale data.

Classic example:

1. User opens profile `a`; fetch A starts.
2. User quickly opens profile `b`; fetch B starts.
3. Fetch B finishes first and shows user B.
4. Fetch A finishes later and overwrites the UI with user A.

The earlier request won the race even though it no longer represents the current UI.

## 2. Why It Matters

Race conditions are production bugs because they depend on real timing:

- slow mobile networks
- rapid route changes
- debounced search
- repeated form submissions
- tab visibility changes
- browser back/forward navigation
- React Strict Mode development checks

They also create bad user trust. A user sees one route, but the data belongs to a previous route.

## 3. Official Mechanism

React effect cleanup is the key mechanism:

- When dependencies change, React runs the previous cleanup before running the next setup.
- When the component unmounts, React runs the latest cleanup.
- Effects run only on the client, after commit.
- The effect callback itself must return `undefined` or a cleanup function, not a Promise.

This is why this is wrong:

```tsx
React.useEffect(async () => {
  const data = await fetch('/api/user').then(r => r.json());
  setUser(data);
}, []);
```

An `async` function always returns a Promise. React expects the return value to be a cleanup function or `undefined`. Put async work inside the effect instead.

```tsx
React.useEffect(() => {
  async function load() {
    const data = await fetch('/api/user').then(r => r.json());
    setUser(data);
  }

  load();
}, []);
```

For production, also add cleanup or cancellation.

## 4. Mental Model

Every effect invocation owns its async work. When that invocation is no longer current, cleanup should stop the work or prevent the result from updating state.

| Problem | Symptom | Fix |
| --- | --- | --- |
| Old request finishes last | UI shows old data | Ignore flag or `AbortController` |
| Component unmounts during request | State update after unmount | Cleanup guard or abort |
| Effect callback is `async` | Cleanup cannot be returned correctly | Inner async function |
| Loading state from old request | Spinner flickers or hides too early | Guard `finally` too |
| Duplicate requests | Extra bandwidth and inconsistent cache | Use data library, stable keys, or server fetching |

## 5. Real Frontend Example

### Problem: product detail race

```tsx
function ProductDetails({ productId }: { productId: string }) {
  const [product, setProduct] = React.useState<Product | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    setLoading(true);

    fetch(`/api/products/${productId}`)
      .then(response => response.json())
      .then(data => {
        setProduct(data);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [productId]);

  if (loading) return <Spinner />;
  return <ProductView product={product} />;
}
```

### Bug

> [!warning] The last-response-wins race
> If `productId` changes quickly, an old request can finish *after* the new one and call `setProduct` with stale data. The old `.finally()` can also flip `loading` to `false` while the newer request is still pending. The bug is ordering, not the fetch itself.

### Fix: ignore flag

```tsx
function ProductDetails({ productId }: { productId: string }) {
  const [product, setProduct] = React.useState<Product | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    let ignore = false;

    async function loadProduct() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/products/${productId}`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = (await response.json()) as Product;

        if (!ignore) {
          setProduct(data);
        }
      } catch (reason) {
        if (!ignore) {
          setError(reason instanceof Error ? reason : new Error(String(reason)));
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadProduct();

    return () => {
      ignore = true;
    };
  }, [productId]);

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <ProductView product={product} />;
}
```

### Why this works

Each effect invocation gets its own `ignore` variable. When `productId` changes, React runs the previous cleanup and sets that old closure's `ignore` to `true`. When the old request resolves, it skips every state update.

## Real-World Use Cases

### Debounce is not a race fix: latest-wins request counter

A flight search debounces input, but the airline fares API has 0.5-6s latency — debouncing spaces out requests, it does not order their responses. A sequence counter accepts only the newest request's result.

```tsx
const requestSeq = React.useRef(0);

React.useEffect(() => {
  const seq = ++requestSeq.current;

  fetchFares(origin, destination).then(fares => {
    if (seq === requestSeq.current) setFares(fares); // only the latest request wins
  });
}, [origin, destination]);
```

Each effect invocation's closure holds its own `seq`, compared against the shared ref at resolve time — the same closure-per-invocation mechanism as the ignore flag, but it also works for callers outside effects.

### Strict Mode exposes a mutation hiding in an effect

An add-to-cart flow runs a POST inside an effect. In development, Strict Mode runs setup twice — and QA files a bug: every product lands in the cart twice.

```tsx
React.useEffect(() => {
  fetch('/api/cart/items', {
    method: 'POST',
    body: JSON.stringify({ productId }),
  });
}, [productId]);
```

Effects are for synchronization and must tolerate re-running; a mutation is an event. The double-invoke did not create the bug, it revealed it — the same duplicate fires on any dependency change or remount. Move the POST into the click handler or a [[22 - Next.js Deep Dive/04 - Server Actions|Server Action]].

> [!tip]
> Litmus test: "if this effect ran twice, would the system end up wrong?" If yes, it is an event handler wearing an effect costume.

### Async setup racing its own cleanup

A support app connects to a chat room per ticket. `connect()` is async — if the agent switches tickets fast, cleanup runs while the connect promise is still pending, `disconnect()` is a no-op, and the resolved connection leaks and keeps receiving messages.

```tsx
React.useEffect(() => {
  let cancelled = false;
  const client = createChatClient(roomId);

  client.connect().then(() => {
    if (cancelled) client.disconnect(); // connect resolved AFTER cleanup ran
  });

  return () => {
    cancelled = true;
    client.disconnect(); // no-op if the connection was not established yet
  };
}, [roomId]);
```

The race here is not between two fetches but between an async setup and its own cleanup. The flag lives in the invocation's closure, so the late-resolving promise can see that its effect is already dead. See [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]].

## 6. AbortController Alternative

The ignore flag prevents stale state updates. `AbortController` also asks the browser to cancel the request.

```tsx
React.useEffect(() => {
  const controller = new AbortController();

  async function loadProduct() {
    try {
      const response = await fetch(`/api/products/${productId}`, {
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      setProduct((await response.json()) as Product);
    } catch (reason) {
      if (controller.signal.aborted) return;
      setError(reason instanceof Error ? reason : new Error(String(reason)));
    }
  }

  loadProduct();

  return () => {
    controller.abort();
  };
}, [productId]);
```

Use `AbortController` when bandwidth, response size, or request cancellation matters. Use the ignore flag for async work that cannot be canceled.

## 7. Data Fetching Architecture

Manual fetch effects are useful for learning and for small custom synchronization. In production apps, consider a framework or data library:

- Next.js Server Components can fetch on the server and keep credentials out of the client bundle.
- Route handlers can centralize server-only logic.
- SWR or TanStack Query can manage cache keys, deduping, retries, stale results, background refetches, and cancellation.
- Server Actions can move mutations to server code in App Router designs.

The point is not "never fetch in effects." The point is to be clear about ownership: cache, cancellation, loading state, errors, retries, and stale data handling.

## 8. Production Checklist

- Does the effect depend on all values used to create the request?
- Can an older request finish after a newer request?
- Are `then`, `catch`, and `finally` guarded?
- Does cleanup cancel or ignore outdated work?
- Are aborts treated as expected cleanup, not user-visible errors?
- Is the loading state tied to the current request only?
- Would a data-fetching library or Server Component remove this client race?
- In development Strict Mode, does setup and cleanup behave correctly when run twice?

## 9. Interview Answer

A race condition in an async effect happens when multiple requests are in flight and an older request resolves after a newer one, then updates state with stale data. React gives us the cleanup mechanism: when dependencies change, the old cleanup runs before the new setup. The common fix is an ignore flag scoped to each effect invocation and checked before every state update. A stronger network-level fix is `AbortController`, which cancels the fetch in cleanup and ignores the expected abort error. I would avoid `useEffect(async () => ...)` because an async effect callback returns a Promise instead of a cleanup function.

## 10. Mistakes to Avoid

| Mistake | Production failure |
| --- | --- |
| Guarding only `.then` but not `.catch` or `.finally` | Old request can still set error or loading state. |
| `useEffect(async () => ...)` | React cannot use the Promise as cleanup. |
| Treating abort as a real error | Users see errors during normal navigation. |
| Empty dependency array for a request using props | Request never updates when props change. |
| Manual fetching everywhere | Duplicated cache, retry, loading, and race logic. |

> [!tip] Guard the whole chain, not just success
> A stale request can still fire `.catch` and `.finally`, so an ignore flag or `AbortController` must cover error and loading updates too — not only `setData`. And never make the effect callback `async`; React needs its return value as the cleanup function.

## 11. Practice

### Q1. What is the bug?

```tsx
React.useEffect(() => {
  fetch(`/api/search?q=${query}`)
    .then(r => r.json())
    .then(setResults);
}, [query]);
```

Old searches can finish after newer searches and overwrite `results`.

### Q2. Add the ignore flag.

```tsx
React.useEffect(() => {
  let ignore = false;

  fetch(`/api/search?q=${encodeURIComponent(query)}`)
    .then(r => r.json())
    .then(data => {
      if (!ignore) setResults(data);
    });

  return () => {
    ignore = true;
  };
}, [query]);
```

### Q3. Why guard `.finally()`?

Because `.finally()` runs after success, failure, and abort. An old request can incorrectly set `loading` to `false` while a newer request is still loading.

### Q4. What should an experienced engineer mention after solving the snippet?

They should mention cancellation, error handling, URL encoding, loading state ownership, cache ownership, and whether the app should use Server Components or a data library instead of manual effect fetching.

## Related Notes

- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
