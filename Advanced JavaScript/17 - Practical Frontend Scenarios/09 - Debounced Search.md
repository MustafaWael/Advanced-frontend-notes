---
tags: [javascript, scenarios, react, debounced-search]
module: "17 - Practical Frontend Scenarios"
priority: must-know
status: not-started
---

# Debounced Search

## Maturity Target

- Priority: #must-know
- Study time: 70-90 minutes
- Interview signal: can explain debounce, cleanup, cancellation, race conditions, and loading states.
- Production signal: can build search that is responsive, accessible, cancellable, and cache-friendly.
- Fast track: sections 2, 4, 5, and 8.

## Source Anchors

- [MDN: setTimeout](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout)
- [MDN: clearTimeout](https://developer.mozilla.org/en-US/docs/Web/API/Window/clearTimeout)
- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)

## 1. Scenario

A search input sends a request on every keystroke. Typing `react hooks` can fire many requests, waste server work, and show stale results if old responses arrive late.

Debounce solves only part of the problem:

- Debounce reduces how many requests start.
- Cancellation prevents old in-flight requests from winning.
- Minimum query length avoids useless short searches.
- Cache can avoid repeat work for the same query.

## 2. Broken Version

```tsx
function SearchBox() {
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<Result[]>([]);

  function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const nextQuery = event.target.value;
    setQuery(nextQuery);

    // BUG: fires on every keypress.
    // BUG: old responses can overwrite new responses.
    fetch(`/api/search?q=${nextQuery}`)
      .then(response => response.json())
      .then(setResults);
  }

  return <input value={query} onChange={handleChange} />;
}
```

## 3. Root Cause

Controlled inputs should update immediately, but network requests should represent user intent after a pause. If you debounce the input itself, typing feels laggy. Debounce the derived search value or the effect that starts the search.

## 4. `useDebouncedValue`

```tsx
function useDebouncedValue<T>(value: T, delayMs: number) {
  const [debounced, setDebounced] = React.useState(value);

  React.useEffect(() => {
    const id = window.setTimeout(() => {
      setDebounced(value);
    }, delayMs);

    return () => {
      window.clearTimeout(id);
    };
  }, [value, delayMs]);

  return debounced;
}
```

Each value change cancels the previous timer. Only the last value after the pause is committed.

## 5. Full Search With Cancellation

```tsx
function SearchBox() {
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<Result[]>([]);
  const [status, setStatus] = React.useState<'idle' | 'loading' | 'error'>('idle');

  const debouncedQuery = useDebouncedValue(query, 300);

  React.useEffect(() => {
    const trimmed = debouncedQuery.trim();

    if (trimmed.length < 2) {
      setResults([]);
      setStatus('idle');
      return;
    }

    const controller = new AbortController();

    async function search() {
      setStatus('loading');

      try {
        const response = await fetch(
          `/api/search?q=${encodeURIComponent(trimmed)}`,
          { signal: controller.signal }
        );

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = (await response.json()) as Result[];
        setResults(data);
        setStatus('idle');
      } catch (reason) {
        if (controller.signal.aborted) return;
        setStatus('error');
      }
    }

    search();

    return () => {
      controller.abort();
    };
  }, [debouncedQuery]);

  return (
    <section>
      <input
        type="search"
        value={query}
        aria-label="Search"
        onChange={event => setQuery(event.target.value)}
      />

      {status === 'loading' ? <p aria-live="polite">Searching...</p> : null}
      {status === 'error' ? <p role="alert">Search failed</p> : null}
      <ResultList results={results} />
    </section>
  );
}
```

## 6. Debounce Function For Non-React Code

```ts
function debounce<T extends (...args: never[]) => void>(
  fn: T,
  delayMs: number
) {
  let timerId: ReturnType<typeof setTimeout> | undefined;

  return (...args: Parameters<T>) => {
    if (timerId !== undefined) {
      clearTimeout(timerId);
    }

    timerId = setTimeout(() => {
      fn(...args);
    }, delayMs);
  };
}
```

In React, do not create a new debounced function on every render unless you intentionally want to reset it.

## 7. Tradeoffs

- Debounce value, not controlled input updates.
- Use throttle for continuous events like scroll, not search intent.
- Abort old requests when a new debounced query starts.
- Use `encodeURIComponent` for query strings.
- For repeated server-state patterns, prefer a query library with caching and cancellation.
- Keep accessibility: loading text should use `aria-live`, errors should use `role="alert"`.

## 8. Production Checklist

- [ ] Input updates immediately.
- [ ] Search request waits for a pause.
- [ ] Empty and too-short queries do not fetch.
- [ ] Query is URL-encoded.
- [ ] Old request is aborted or ignored.
- [ ] Abort is not shown as an error.
- [ ] Loading and no-results states are distinct.
- [ ] Same query can be cached if useful.

## 9. Interview Angle

Strong answer:

"Debounce delays starting work until the user pauses, but it does not cancel work already in flight. For production search I debounce the query value, then run a cancellable effect using `AbortController`. I also enforce a minimum query length, encode the query, and keep controlled input updates immediate."

## Related Notes

- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions]] — announcing results and loading without spamming
- [[90 - Labs/03 - Accessible Async Search Lab|Accessible Async Search Lab]] — build this scenario end to end
