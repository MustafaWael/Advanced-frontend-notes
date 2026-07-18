---
tags: [javascript, scenarios, react, handling-race-conditions]
module: "17 - Practical Frontend Scenarios"
priority: must-know
status: not-started
---

# Handling Race Conditions

## Maturity Target

- Priority: #must-know
- Study time: 70-90 minutes
- Interview signal: can explain out-of-order async completion and write both ignore-flag and abort fixes.
- Production signal: can protect search, profile pages, route transitions, and dependent requests from stale data.
- Fast track: study the timeline, then implement sections 4 and 5 from memory.

## Source Anchors

- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [MDN: Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [MDN: Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)

## 1. Scenario

A search input shows results for `re` while the input says `react`. Or a profile route says `/users/2`, but the page displays data for user 1.

Timeline:

```text
t=0    query = "r"      request A starts
t=80   query = "re"     request B starts
t=160  query = "react"  request C starts
t=250  C resolves       correct UI
t=400  A resolves       stale UI overwrites correct UI
```

The bug is not that promises are broken. The bug is that every Promise callback updates shared state unconditionally.

## 2. Broken Version

```tsx
function SearchResults({ query }: { query: string }) {
  const [results, setResults] = React.useState<Result[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    setLoading(true);

    fetch(`/api/search?q=${encodeURIComponent(query)}`)
      .then(response => response.json())
      .then(data => {
        // BUG: an old request can still update current UI.
        setResults(data);
        setLoading(false);
      });
  }, [query]);

  return loading ? <Spinner /> : <ResultList results={results} />;
}
```

## 3. Root Cause

Each effect invocation starts independent async work. React runs cleanup when dependencies change, but the browser request from the old effect continues unless you cancel it. When the old Promise resolves, its callback still has access to `setResults`.

The UI needs a rule: only the current request can update current state.

## 4. Fix 1: Ignore Flag

```tsx
function SearchResults({ query }: { query: string }) {
  const [results, setResults] = React.useState<Result[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    let ignore = false;

    async function load() {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = (await response.json()) as Result[];

        if (!ignore) {
          setResults(data);
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

    load();

    return () => {
      ignore = true;
    };
  }, [query]);

  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <ResultList results={results} />;
}
```

Why it works:

- Each effect has its own `ignore` binding.
- Cleanup sets the old effect's `ignore` to `true`.
- Old success, error, and loading updates are skipped.

## 5. Fix 2: AbortController

```tsx
React.useEffect(() => {
  const controller = new AbortController();

  async function load() {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
        signal: controller.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      setResults((await response.json()) as Result[]);
    } catch (reason) {
      if (controller.signal.aborted) return;

      setError(reason instanceof Error ? reason : new Error(String(reason)));
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
}, [query]);
```

Why it works:

- Cleanup aborts the old request.
- The old fetch rejects as expected cancellation.
- The catch/finally branches avoid stale state updates after abort.

## 6. Tradeoffs

| Pattern | Best for | Tradeoff |
| --- | --- | --- |
| Ignore flag | non-cancelable async work | still uses network/CPU |
| AbortController | fetch and signal-aware APIs | must handle expected abort |
| Data library | repeated server-state needs | adds conventions and dependency |
| Server Component fetch | server-rendered route data | not for client-only live interactions |

## 7. Production Checklist

- [ ] Can multiple requests be in flight for the same UI slot?
- [ ] Can an older request finish after a newer one?
- [ ] Are success, catch, and finally guarded?
- [ ] Is abort handled as expected cleanup?
- [ ] Is loading state tied to the current request only?
- [ ] Would a data library own this better?
- [ ] Did I test with artificial slow responses and rapid input?

## 8. Interview Angle

Strong answer:

"A race condition happens when async operations complete in a different order than they started and update the same state. In React effects, cleanup is the hook point. I can either mark the old effect as ignored or abort the old request. The key detail is guarding not only success, but also error and loading state."

## 9. Practice

1. Add a random artificial delay to a search API and reproduce stale results.
2. Implement the ignore-flag fix without looking.
3. Implement the abort fix and confirm abort does not show an error.
4. Explain why debouncing reduces races but does not fully solve them.

## Related Notes

- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Deterministic Tests]] — force the bad interleaving in a repeatable test
- [[31 - Low Level Design/05 - Concurrency Foundations|Concurrency Foundations]] — the same contention idea at thread scale, and why JS races differ
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]] — Dealing with Contention, the distributed scale
