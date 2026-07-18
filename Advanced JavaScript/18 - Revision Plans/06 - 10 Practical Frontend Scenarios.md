---
tags: [javascript, revision, interview, 10-practical-frontend-scenarios]
module: "18 - Revision Plans"
priority: must-know
status: not-started
---

# 10 Practical Frontend Scenarios

Use these scenarios to prove the vault is not just interview trivia. For each scenario, write:

- Problem: what the user or team sees.
- Bug: the exact JavaScript or React mechanism.
- Fix: code with comments.
- Tradeoff: what the fix costs or changes.
- Checklist: how to avoid repeating it.
- Interview angle: the concise answer you would give.

## 1. Fixing a Stale Closure in React

Related note: [[17 - Practical Frontend Scenarios/01 - Fixing Stale Closure in React|Fixing Stale Closure in React]]

Problem:

A counter increments once and then stops because an interval callback keeps reading the first render's `count`.

Bug:

The interval callback closes over the `count` binding from the render that created the effect. If the effect has an empty dependency array, that callback never gets recreated with newer render values.

Failing version:

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount(count + 1); // Bug: count is always the value from this render.
    }, 1000);

    return () => clearInterval(id);
  }, []);

  return <span>{count}</span>;
}
```

Production fix:

```jsx
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      // Functional update reads the latest queued state value.
      setCount((current) => current + 1);
    }, 1000);

    return () => clearInterval(id);
  }, []);

  return <span>{count}</span>;
}
```

Tradeoff:

Functional updates are excellent when the next state depends on the previous state. If the interval also depends on props or external values, include those dependencies or move the logic.

Checklist:

- [ ] Does the callback read render values?
- [ ] Should the effect rerun when those values change?
- [ ] Can a functional update remove the dependency?
- [ ] Does cleanup clear timers or subscriptions?

Interview angle:

Stale closures happen because each render has its own values. I fix them by making dependencies honest, using functional updates for previous-state changes, or using refs when I need a mutable latest value that should not trigger rerenders.

## 2. Preventing Duplicate API Requests

Related note: [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]

Problem:

A user double-clicks "Pay" or "Save" and sends two requests. The backend might create duplicate records.

Bug:

The UI allows repeated submission while the first request is still in flight. JavaScript executes both event handlers, and both async operations continue independently.

Failing version:

```jsx
function SaveButton() {
  async function handleSave() {
    await fetch("/api/save", { method: "POST" });
  }

  return <button onClick={handleSave}>Save</button>;
}
```

Production fix:

```jsx
function SaveButton() {
  const [isSaving, setIsSaving] = useState(false);
  const inFlightRef = useRef(false);

  async function handleSave() {
    if (inFlightRef.current) return; // Guard same-tick double clicks.

    inFlightRef.current = true;
    setIsSaving(true);

    try {
      const response = await fetch("/api/save", { method: "POST" });

      if (!response.ok) {
        throw new Error(`Save failed: ${response.status}`);
      }
    } finally {
      inFlightRef.current = false;
      setIsSaving(false);
    }
  }

  return (
    <button disabled={isSaving} onClick={handleSave}>
      {isSaving ? "Saving..." : "Save"}
    </button>
  );
}
```

Tradeoff:

Client guards improve UX but are not enough for payments or critical writes. The server should still support idempotency keys or duplicate protection.

Checklist:

- [ ] Disable or guard while the request is in flight.
- [ ] Use `finally` so the guard resets on success or failure.
- [ ] Handle HTTP non-2xx responses.
- [ ] Use server-side idempotency for critical writes.

Interview angle:

I prevent duplicate requests with a UI disabled state, an immediate in-flight guard for fast repeated events, and server idempotency for operations where duplicates are harmful.

## 3. Handling Request Race Conditions

Related note: [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]

Problem:

A search page displays results for an older query because the older request resolves after the newer request.

Bug:

Promises resolve independently. Without a "latest request wins" rule, any response can update state, even if it no longer matches the current input.

Failing version:

```jsx
useEffect(() => {
  fetch(`/api/search?q=${query}`)
    .then((response) => response.json())
    .then(setResults); // Bug: older requests can overwrite newer results.
}, [query]);
```

Production fix:

```jsx
function SearchResults({ query }) {
  const [results, setResults] = useState([]);
  const requestIdRef = useRef(0);

  useEffect(() => {
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;

    async function load() {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`);
      }

      const data = await response.json();

      // Only the latest request is allowed to update visible results.
      if (requestIdRef.current === requestId) {
        setResults(data);
      }
    }

    load().catch((error) => {
      if (requestIdRef.current === requestId) {
        console.error(error);
      }
    });
  }, [query]);

  return <ResultsList results={results} />;
}
```

Tradeoff:

Request-id guards prevent stale UI updates, but they do not stop network work. Combine with `AbortController` when the request supports cancellation.

Checklist:

- [ ] Can older work resolve after newer work?
- [ ] Does the response still match the current query, route, or form?
- [ ] Should stale work be ignored, canceled, or both?
- [ ] Are errors also guarded so old failures do not replace new UI state?

Interview angle:

Race conditions happen when completion order differs from start order. I usually use abort for resource cleanup and a request id or stale flag for correctness.

## 4. Optimizing Large List Transformations

Related note: [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]

Problem:

Typing in a filter input feels slow because each keystroke filters, sorts, groups, and renders thousands of rows.

Bug:

The UI performs expensive synchronous work on every render. JavaScript blocks the main thread, so the browser cannot respond and paint smoothly.

Failing version:

```jsx
function ProductTable({ products, query }) {
  const visibleProducts = products
    .filter((product) => product.name.includes(query))
    .sort((a, b) => a.price - b.price); // Bug: mutates the filtered array safely, but work repeats every render.

  return <Table rows={visibleProducts} />;
}
```

Production fix:

```jsx
function ProductTable({ products, query }) {
  const normalizedQuery = query.trim().toLowerCase();

  const visibleProducts = useMemo(() => {
    // Keep the transform pure and derived from explicit dependencies.
    return products
      .filter((product) =>
        product.name.toLowerCase().includes(normalizedQuery)
      )
      .toSorted((a, b) => a.price - b.price);
  }, [products, normalizedQuery]);

  return <VirtualizedTable rows={visibleProducts} />;
}
```

Tradeoff:

`useMemo` helps only if dependencies are stable and the calculation is expensive enough. For very large lists, use server-side filtering, indexing, pagination, workers, or virtualization.

Checklist:

- [ ] Measure before optimizing.
- [ ] Keep transforms pure and non-mutating.
- [ ] Stabilize dependencies intentionally.
- [ ] Virtualize or paginate large rendered lists.
- [ ] Consider moving heavy work off the main thread.

Interview angle:

I first identify whether the problem is computation, rendering, network, or memory. For large lists, I combine pure transforms, memoization when useful, and virtualization or server-side filtering when the render cost dominates.

## 5. Avoiding Mutation in State

Related note: [[17 - Practical Frontend Scenarios/05 - Avoiding Mutation in State|Avoiding Mutation in State]]

Problem:

A todo checkbox changes data, but React does not rerender reliably or memoized child components show stale values.

Bug:

The code mutates existing objects or arrays and may reuse the same reference. React and memoization rely heavily on identity comparisons.

Failing version:

```jsx
function toggleTodo(id) {
  const todo = todos.find((item) => item.id === id);
  todo.done = !todo.done; // Bug: mutates existing state.
  setTodos(todos); // Same array reference.
}
```

Production fix:

```jsx
function toggleTodo(id) {
  setTodos((currentTodos) =>
    currentTodos.map((todo) => {
      if (todo.id !== id) return todo; // Keep unchanged objects stable.

      return {
        ...todo,
        done: !todo.done, // Changed item gets a new object reference.
      };
    })
  );
}
```

Tradeoff:

Immutable updates create new objects, so very deep structures can become noisy. Normalize complex state or use a helper library when nested updates dominate the code.

Checklist:

- [ ] Never mutate props or state directly.
- [ ] Copy every level that changes.
- [ ] Preserve unchanged references when possible.
- [ ] Watch for shallow-copy nested-reference bugs.

Interview angle:

Immutability is not just style. It gives React and memoized code reliable identity signals and prevents shared data from being accidentally changed elsewhere.

## 6. Cleaning Event Listeners

Related note: [[17 - Practical Frontend Scenarios/06 - Cleaning Event Listeners|Cleaning Event Listeners]]

Problem:

After navigating around a page, one resize event runs the same handler many times.

Bug:

The component adds listeners repeatedly and either never removes them or removes a different function reference than the one it added.

Failing version:

```jsx
useEffect(() => {
  window.addEventListener("resize", () => {
    setWidth(window.innerWidth);
  });

  // Bug: no cleanup, and the anonymous function cannot be removed later.
}, []);
```

Production fix:

```jsx
useEffect(() => {
  function handleResize() {
    setWidth(window.innerWidth);
  }

  handleResize(); // Initialize from the current browser value.
  window.addEventListener("resize", handleResize);

  return () => {
    window.removeEventListener("resize", handleResize);
  };
}, []);
```

Tradeoff:

Stable listener identity matters. If the handler depends on changing values, either include dependencies and clean up on change, or read latest values from a ref.

Checklist:

- [ ] Keep the same function reference for add/remove.
- [ ] Return cleanup from effects.
- [ ] Include dependencies honestly.
- [ ] Avoid browser APIs in server components or during server render.

Interview angle:

Listener cleanup is about lifetime and identity. The same callback reference that was added must be removed, and the effect cleanup should match the subscription lifetime.

## 7. Async Form Submission

Related note: [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]

Problem:

A form shows success even when the server returns validation errors, or it gets stuck loading after a thrown error.

Bug:

The code treats every resolved `fetch` as success and does not reset loading state in all paths.

Failing version:

```jsx
async function submit(values) {
  setStatus("saving");

  const response = await fetch("/api/profile", {
    method: "POST",
    body: JSON.stringify(values),
  });

  setStatus("saved"); // Bug: fetch resolves for HTTP 400/500 responses.
}
```

Production fix:

```jsx
async function submit(values) {
  setStatus("saving");
  setError(null);

  try {
    const response = await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      // Preserve useful status while showing a user-safe message.
      throw new Error(data?.message ?? `Request failed: ${response.status}`);
    }

    setStatus("saved");
  } catch (error) {
    setStatus("error");
    setError(error.message);
  }
}
```

Tradeoff:

Real forms often need field-level validation, retry rules, auth handling, and abort behavior. Keep domain errors separate from unexpected exceptions.

Checklist:

- [ ] Check `response.ok`.
- [ ] Parse response safely.
- [ ] Reset loading state in success and failure paths.
- [ ] Disable or guard duplicate submits.
- [ ] Surface useful validation messages.

Interview angle:

`fetch` rejects for network-level failures, not ordinary HTTP error statuses. Production form code must check status, parse validation data, manage loading, and recover cleanly.

## 8. Preventing Memory Leaks

Related note: [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]

Problem:

Memory usage grows after repeated navigation to and from a screen.

Bug:

Something still reaches data from the old screen: timer, listener, subscription, cache, closure, pending request, or detached DOM reference.

Failing version:

```jsx
useEffect(() => {
  const id = setInterval(() => {
    pollExpensiveData(); // Bug: continues after the component unmounts.
  }, 5000);
}, []);
```

Production fix:

```jsx
useEffect(() => {
  const id = setInterval(() => {
    pollExpensiveData();
  }, 5000);

  return () => {
    clearInterval(id); // Releases the timer and its retained closure.
  };
}, []);
```

Tradeoff:

Cleanup prevents leaks, but polling may still be the wrong architecture. Consider visibility checks, server push, cache invalidation, or stale-while-revalidate patterns.

Checklist:

- [ ] Clean timers and intervals.
- [ ] Remove listeners.
- [ ] Unsubscribe from external stores or sockets.
- [ ] Abort or ignore stale requests.
- [ ] Limit cache growth.
- [ ] Verify with repeated navigation and heap snapshots.

Interview angle:

A leak is about reachability. I look for anything that keeps old component data reachable after the screen should be gone.

## 9. Debounced Search

Related note: [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]

Problem:

Search sends too many requests and sometimes displays results for the wrong query.

Bug:

The code starts a request for every keystroke and may allow old timers or requests to survive after the query changes.

Production fix:

```jsx
function SearchBox() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(async () => {
      try {
        const response = await fetch(
          `/api/search?q=${encodeURIComponent(query)}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`Search failed: ${response.status}`);
        }

        setResults(await response.json());
      } catch (error) {
        if (error.name !== "AbortError") {
          console.error(error);
        }
      }
    }, 300);

    return () => {
      clearTimeout(timeoutId); // Cancel the old scheduled search.
      controller.abort(); // Cancel the old request if it started.
    };
  }, [query]);

  return <SearchInput value={query} onChange={setQuery} results={results} />;
}
```

Tradeoff:

Debounce improves network and UI calmness, but it delays feedback. Use shorter delays, optimistic UI, cached results, or immediate local filtering when the experience needs it.

Checklist:

- [ ] Clear old timers.
- [ ] Abort old requests.
- [ ] Encode query parameters.
- [ ] Handle empty input.
- [ ] Handle errors without replacing current results with stale failures.

Interview angle:

Debounced search combines closure lifetime, timer cleanup, request cancellation, and race-condition prevention. The fix is not only "use debounce"; it is managing every async lifetime.

## 10. Request Cancellation

Related note: [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]

Problem:

A route changes while a request is in flight. The old request still finishes and tries to update state.

Bug:

Async work outlives the UI that started it. Without cancellation or stale guards, old results can update the wrong screen.

Production fix:

```jsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const controller = new AbortController();
    let isCurrent = true;

    async function loadUser() {
      try {
        const response = await fetch(`/api/users/${userId}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`User request failed: ${response.status}`);
        }

        const data = await response.json();

        if (isCurrent) {
          setUser(data);
        }
      } catch (error) {
        if (error.name === "AbortError") return;

        if (isCurrent) {
          setError(error);
        }
      }
    }

    loadUser();

    return () => {
      isCurrent = false; // Guards state updates even if abort is not enough.
      controller.abort();
    };
  }, [userId]);

  if (error) return <ErrorMessage error={error} />;
  if (!user) return <Spinner />;
  return <Profile user={user} />;
}
```

Tradeoff:

Abort support depends on the API. A stale guard is still useful because not all async work is cancelable and some work may finish between cleanup and rejection handling.

Checklist:

- [ ] Create the controller inside the effect/request lifetime.
- [ ] Pass `signal` to supported APIs.
- [ ] Treat `AbortError` separately.
- [ ] Guard state updates for non-cancelable work.
- [ ] Clean up when dependencies change or the component unmounts.

Interview angle:

Cancellation is about resource cleanup, while stale guards are about UI correctness. Mature code often uses both.

## Final Scenario Review

After practicing all ten:

- [ ] Pick 3 scenarios and rewrite the failing version from memory.
- [ ] Explain the bug using JavaScript mechanisms, not only React terms.
- [ ] Add one verification step for each fix.
- [ ] Name one tradeoff or alternative for each fix.
- [ ] Connect each scenario to one official source or vault note.

## Sources

- ECMAScript Language Specification: https://tc39.es/ecma262/
- HTML Living Standard event loops and task processing: https://html.spec.whatwg.org/multipage/webappapis.html#event-loops
- MDN Promise reference: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise
- MDN AbortController reference: https://developer.mozilla.org/en-US/docs/Web/API/AbortController
- React `useEffect` reference: https://react.dev/reference/react/useEffect
- Next.js Server and Client Components docs: https://nextjs.org/docs/app/getting-started/server-and-client-components
- web.dev RAIL performance model: https://web.dev/articles/rail

## Related Notes

- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
- [[18 - Revision Plans/02 - 7 Day Revision Plan|7 Day Revision Plan]]
- [[18 - Revision Plans/03 - 14 Day Deep Study Plan|14 Day Deep Study Plan]]
- [[18 - Revision Plans/04 - 30 Interview Questions|30 Interview Questions]]
- [[18 - Revision Plans/05 - 20 Code Output Questions|20 Code Output Questions]]
- [[01 - Roadmap|Roadmap]]
