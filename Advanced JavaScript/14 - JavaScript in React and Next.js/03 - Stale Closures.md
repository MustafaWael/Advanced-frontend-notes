---
tags: [javascript, react, nextjs, stale-closures]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# Stale Closures

## Maturity Target

- Priority: #must-know
- Study time: 80-110 minutes
- Interview signal: can diagnose stale intervals, listeners, async callbacks, and memoized callbacks.
- Production signal: can fix stale data without disabling the hooks linter.
- Fast track: sections 3, 5, 6, 8, and all practice questions.

## Source Anchors

- [MDN: Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [React docs: State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [React docs: Removing Effect Dependencies](https://react.dev/learn/removing-effect-dependencies)
- [React docs: exhaustive-deps lint](https://react.dev/reference/eslint-plugin-react-hooks/lints/exhaustive-deps)

## 1. Concept

A stale closure is a callback that keeps reading values from an old render after the component has rendered with newer values.

The callback is not "wrong" according to JavaScript. It is doing exactly what closures do: it remembers the lexical environment where it was created. The bug is that the callback outlived the assumptions of that render.

Common stale closure locations:

- `setInterval` and `setTimeout`
- DOM or global event listeners
- WebSocket and subscription callbacks
- Promise handlers and async functions
- `useCallback` functions with missing dependencies
- `useMemo` calculations with missing dependencies
- Effects with suppressed dependency warnings

## 2. Why It Matters

Stale closures are one of the most common real React bugs because they often pass basic testing:

- The first render works.
- The first click works.
- Slow network or rapid navigation reveals the bug.
- The UI looks "randomly out of sync."

In interviews, stale closures are a signal topic. A junior answer says, "Add it to the dependency array." A mature answer explains why the closure is stale, what the desired lifetime is, and which fix matches that lifetime.

## 3. Official Mechanism

Each render creates new bindings. A callback created in render 1 keeps render 1's bindings. If that callback is stored somewhere long-lived and React never replaces it, it continues to read render 1.

```tsx
function Counter() {
  const [count, setCount] = React.useState(0);

  React.useEffect(() => {
    const id = window.setInterval(() => {
      console.log(count);
      setCount(count + 1);
    }, 1000);

    return () => window.clearInterval(id);
  }, []);

  return <p>{count}</p>;
}
```

Expected by a beginner: `0, 1, 2, 3...`

Actual behavior: the interval callback captures `count = 0`, so it logs `0` repeatedly and calls `setCount(1)` repeatedly. React may render once to `1`, then skip later identical updates.

## 4. Mental Model

Ask two questions:

1. Should this callback be replaced when a value changes?
2. If not, how should it read current data?

The answer points to a fix:

| Desired behavior | Fix |
| --- | --- |
| Resubscribe when value changes | Put the value in the dependency array |
| Update state from previous state | Use a functional updater |
| Keep one subscription but read latest value | Sync a ref and read `ref.current` |
| Avoid effect entirely | Move logic into an event handler or derive during render |
| Prevent old async result | Use cleanup with ignore flag or `AbortController` |

## 5. Real Frontend Example

### Problem: search listener submits an old query

```tsx
function SearchShortcut({ query }: { query: string }) {
  React.useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
        // BUG: query is from the first render because deps are empty.
        submitSearch(query);
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return null;
}
```

### Bug

> [!warning] Why the query goes stale
> The listener is installed once, so `onKeyDown` is the function from the mount render. If `query` changes as the user types, `submitSearch(query)` can submit the old query.

### Fix 1: resubscribe when the query changes

```tsx
function SearchShortcut({ query }: { query: string }) {
  React.useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
        submitSearch(query);
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [query]);

  return null;
}
```

This is correct if resubscribing is cheap and the listener should always use the matching query from that effect.

### Fix 2: stable listener, latest query

```tsx
function SearchShortcut({ query }: { query: string }) {
  const latestQuery = React.useRef(query);

  React.useEffect(() => {
    latestQuery.current = query;
  }, [query]);

  React.useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') {
        submitSearch(latestQuery.current);
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  return null;
}
```

This is useful when the subscription is expensive or must remain stable, but the handler needs current data.

## Real-World Use Cases

### Debounced search that ignores the active filters

A product search debounces API calls. The debounced wrapper must stay stable — recreating it would reset the timer and drop pending calls — so it is memoized once, and it freezes the mount render's `category`.

```tsx
function ProductSearch({ category }: { category: string }) {
  const [results, setResults] = React.useState<Product[]>([]);

  const runSearch = React.useMemo(
    () =>
      debounce((term: string) => {
        searchProducts(term, category).then(setResults); // category frozen at mount
      }, 300),
    [] // stable timer, stale closure
  );

  return <input onChange={e => runSearch(e.target.value)} />;
}
```

Fails because the debounced function was created once, so its closure keeps the first render's bindings. Either include `category` and cancel the previous debouncer in a `useEffect` cleanup, or read filters from a synced ref (Fix 2 above).

> [!warning]
> If you recreate the debouncer on `category` change, cancel the old one — a pending stale call can still fire after the new debouncer exists.

### Infinite scroll observer stuck on page 1

A feed observes a sentinel `div` to load the next page. The `IntersectionObserver` callback was created at mount, so `page` and `hasMore` never update — it fetches page 2 forever or fetches past the end of the list.

```tsx
React.useEffect(() => {
  const observer = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting && hasMore) {
      loadPage(page + 1); // page and hasMore from the mount render
    }
  });
  observer.observe(sentinelRef.current!);
  return () => observer.disconnect();
}, []);
```

The observer is a long-lived subscription holding one old closure. Fix by keeping the observer stable but moving pagination into state the callback does not read: `setPage(prev => prev + 1)` in the callback, with a separate fetch effect keyed on `page` that also derives `hasMore`. See [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]].

### Reconnect handler with an expired auth token

A trading dashboard keeps one WebSocket alive and reconnects on close. The `onclose` handler captured the token from mount; after a token refresh, every reconnect attempt authenticates with the expired JWT and the server rejects it.

```tsx
React.useEffect(() => {
  const ws = new WebSocket(WS_URL);
  ws.onclose = () => {
    reconnect(authToken); // token from the mount render — refreshed long ago
  };
  return () => ws.close();
}, []);
```

The connection must not be torn down on every token refresh, so adding `authToken` to deps is the wrong lifetime. This is the ref pattern from Fix 2: sync `latestTokenRef.current = authToken` in its own effect and read the ref inside `onclose`. See [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]].

## 6. Fix Patterns by Scenario

### Interval that updates state

```tsx
React.useEffect(() => {
  const id = window.setInterval(() => {
    setCount(prev => prev + 1);
  }, 1000);

  return () => window.clearInterval(id);
}, []);
```

No `count` dependency is needed because the effect does not read `count`; it asks React for the latest state.

### Effect that synchronizes with a prop

```tsx
React.useEffect(() => {
  const connection = createConnection(roomId);
  connection.connect();

  return () => connection.disconnect();
}, [roomId]);
```

`roomId` belongs in dependencies because changing it means the external connection must change.

### Callback passed to a memoized child

```tsx
const onSave = React.useCallback(() => {
  saveDraft(draftId, content);
}, [draftId, content]);
```

If `content` is omitted, the child may call a stable function that submits old content.

### Async result guard

```tsx
React.useEffect(() => {
  let ignore = false;

  fetch(`/api/users/${userId}`)
    .then(r => r.json())
    .then(data => {
      if (!ignore) setUser(data);
    });

  return () => {
    ignore = true;
  };
}, [userId]);
```

The cleanup changes the old closure's `ignore` variable so old results cannot update state.

## 7. Production Tradeoffs

- Adding dependencies can recreate subscriptions. That is correct when the external system depends on those values.
- Refs avoid resubscription but bypass React's dependency tracking. Use them only when the callback needs latest data without reacting.
- Functional updaters are the cleanest fix when the only stale value is the previous state.
- Suppressing `exhaustive-deps` should be rare and documented. Most suppressions hide a bug or a design smell.
- Data fetching libraries can remove many stale closure and race-condition problems by owning cache keys, cancellation, and stale result handling.

## 8. Interview Answer

A stale closure happens when a callback created during one render runs later after the component has rendered with newer state or props. The callback still reads the old lexical bindings. In React this often happens with timers, listeners, async callbacks, and hooks with missing dependencies. The fix depends on intent: add dependencies if the effect or callback should update with those values, use a functional updater if the next state depends on previous state, use a ref if a stable callback must read the latest value, and use cleanup or cancellation for async work so old results cannot win.

## 9. Mistakes to Avoid

| Mistake | Why it is dangerous |
| --- | --- |
| Empty dependency array to "run once" while reading props | It locks the effect to initial props. |
| `// eslint-disable-next-line react-hooks/exhaustive-deps` | It hides the exact class of bug the rule is designed to catch. |
| Recreating an interval on every tick unnecessarily | It works, but a functional updater is often simpler. |
| Ref as a default escape hatch | You lose reactivity and make data flow harder to inspect. |
| Assuming stale closures are performance issues | They are correctness bugs first. |

> [!tip] The mental checkpoint
> Before writing a fix, answer two questions: should this callback be *replaced* when a value changes (then list it as a dependency), or should it *read the latest* value without being replaced (then sync a ref and read `ref.current`)? Choosing the wrong one is how stale closures and effect loops both start.

## 10. Practice

### Q1. Why does this stop at 1?

```tsx
React.useEffect(() => {
  const id = window.setInterval(() => {
    setCount(count + 1);
  }, 1000);

  return () => window.clearInterval(id);
}, []);
```

The interval callback captures the mount render's `count`. If that value is `0`, it repeatedly sets `1`.

### Q2. Fix it without adding `count` to dependencies.

```tsx
React.useEffect(() => {
  const id = window.setInterval(() => {
    setCount(prev => prev + 1);
  }, 1000);

  return () => window.clearInterval(id);
}, []);
```

The effect no longer reads `count`; the updater receives the latest queued state.

### Q3. When would adding dependencies be the better fix?

When the external system itself depends on the changing value, such as a room subscription, document title, analytics event tied to a route, or socket connection.

## Related Notes

- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[17 - Practical Frontend Scenarios/01 - Fixing Stale Closure in React|Fixing Stale Closure in React]]
- [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]]
- [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Deterministic Tests]] — pin the stale-closure fix so a refactor cannot reintroduce it
