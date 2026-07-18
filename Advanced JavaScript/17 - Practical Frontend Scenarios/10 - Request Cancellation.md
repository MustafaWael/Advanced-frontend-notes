---
tags: [javascript, scenarios, react, request-cancellation]
module: "17 - Practical Frontend Scenarios"
priority: must-know
status: not-started
---

# Request Cancellation

## Maturity Target

- Priority: #must-know
- Study time: 70-100 minutes
- Interview signal: can explain `AbortController`, abort errors, cleanup timing, and request ownership.
- Production signal: can cancel obsolete reads without confusing cancellation with real failures.
- Fast track: sections 2, 4, 5, and 8.

## Source Anchors

- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [MDN: AbortSignal](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal)
- [MDN: Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)

## 1. Scenario

A user changes route while a request is pending. Or a search query changes while the old query is still loading. The old request is no longer useful.

Request cancellation solves:

- wasted bandwidth
- stale UI updates
- false errors after navigation
- unnecessary JSON parsing
- work continuing after unmount

## 2. Broken Version

```tsx
function PostDetail({ postId }: { postId: string }) {
  const [post, setPost] = React.useState<Post | null>(null);

  React.useEffect(() => {
    fetch(`/api/posts/${postId}`)
      .then(response => response.json())
      .then(setPost);
  }, [postId]);

  return <PostView post={post} />;
}
```

Bug:

- If `postId` changes quickly, old data can overwrite new data.
- If the component unmounts, the old response can still run its callbacks.

## 3. Root Cause

`fetch` accepts an `AbortSignal`, but it will not cancel by itself. React effect cleanup is the natural ownership boundary: the request started by this effect should be canceled when this effect is no longer current.

## 4. Production Fix

```tsx
function PostDetail({ postId }: { postId: string }) {
  const [post, setPost] = React.useState<Post | null>(null);
  const [error, setError] = React.useState<Error | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    const controller = new AbortController();

    async function loadPost() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/posts/${postId}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = (await response.json()) as Post;
        setPost(data);
      } catch (reason) {
        if (controller.signal.aborted) return;

        setError(reason instanceof Error ? reason : new Error(String(reason)));
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadPost();

    return () => {
      controller.abort();
    };
  }, [postId]);

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <PostView post={post} />;
}
```

## 5. Why This Works

- One controller is created per effect invocation.
- The signal is passed to the matching fetch.
- Cleanup aborts the request when `postId` changes or the component unmounts.
- Abort is treated as expected cleanup, not user-visible error.
- `finally` does not reset loading for an aborted old request.

## 6. Timeout Pattern

```ts
async function fetchWithTimeout(url: string, timeoutMs: number) {
  const response = await fetch(url, {
    signal: AbortSignal.timeout(timeoutMs),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}
```

If you also need component cleanup, combine a manual controller with timeout where runtime support allows:

```tsx
React.useEffect(() => {
  const controller = new AbortController();
  const timeoutSignal = AbortSignal.timeout(8000);
  const signal = AbortSignal.any([controller.signal, timeoutSignal]);

  fetch(url, { signal }).catch(reason => {
    if (signal.aborted) return;
    reportError(reason);
  });

  return () => controller.abort();
}, [url]);
```

## 7. Tradeoffs

- Abort is excellent for superseded reads.
- Abort does not undo mutations that reached the server.
- Ignore flags work for non-cancelable async APIs.
- Query libraries often pass an AbortSignal automatically.
- Abort errors still go through Promise rejection handling, so catch them.

## 8. Production Checklist

- [ ] Is there one controller per request/effect?
- [ ] Is `controller.signal` passed to fetch?
- [ ] Does cleanup call `controller.abort()`?
- [ ] Is abort filtered before setting error state?
- [ ] Is `finally` guarded against stale loading updates?
- [ ] Are mutations protected by idempotency instead of assuming abort rolls them back?
- [ ] Are browser/runtime support requirements acceptable for `AbortSignal.timeout` or `AbortSignal.any`?

## 9. Interview Angle

Strong answer:

"I create an `AbortController` inside the effect that owns the request, pass its signal to fetch, and abort in cleanup. When abort happens, fetch rejects, so I catch it and ignore expected cancellation. I still handle real network or HTTP errors. I do not treat abort as rollback for mutations."

## 10. Practice

1. Convert an ignore-flag search effect to `AbortController`.
2. Explain why a module-level `AbortController` is broken.
3. Show why aborting a POST request does not guarantee the server did not process it.
4. Add a timeout to a fetch and handle timeout separately from manual abort.

## Related Notes

- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
