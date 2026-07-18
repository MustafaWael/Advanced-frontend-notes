---
tags: [javascript, scope, closure-bugs]
module: "03 - Scope and Variables"
priority: must-know
status: not-started
---

# Closure Bugs

## Maturity Target

- Priority: #must-know
- Study time: 120 minutes
- Interview signal: you can solve classic closure output questions and explain React stale closures without memorized slogans.
- Production signal: you can choose between dependencies, functional updates, refs, argument passing, factories, cancellation, and cleanup.
- Dependencies: [[03 - Scope and Variables/05 - Closures|Closures]], [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]], [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

## Source Anchors

- [MDN - Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [MDN - let TDZ and block scoping](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let)
- [React - useEffect](https://react.dev/reference/react/useEffect)
- [React - Removing Effect Dependencies](https://react.dev/learn/removing-effect-dependencies)
- [React - useCallback](https://react.dev/reference/react/useCallback)

## 1. Concept

A closure bug happens when a callback reads a binding from the wrong lifetime:

- Too shared: every callback reads the same binding.
- Too old: a callback reads from a previous render or earlier state.
- Too long-lived: a callback keeps data or resources alive longer than intended.
- Too implicit: dependencies are hidden instead of passed as arguments.

The debugging question is always:

> When was this function created, and what bindings did it close over?

## 2. Why Closure Bugs Are Tricky

The code often looks correct at the declaration site. The bug appears later when time is involved:

- User clicks after a loop has finished.
- A timer fires after state changed.
- A promise resolves after props changed.
- A debounced function runs after several keystrokes.
- An event listener stays attached after a component has re-rendered.

That time gap is where the closure becomes visible.

## 3. Bug 1: `var` in Loop Handlers

Bug:

```js
const callbacks = [];

for (var i = 0; i < 3; i += 1) {
  callbacks.push(() => i);
}

console.log(callbacks[0]()); // 3
console.log(callbacks[1]()); // 3
console.log(callbacks[2]()); // 3
```

Why it happens:

- `var i` creates one function-scoped binding.
- Every callback closes over that same binding.
- After the loop completes, `i` is `3`.

Fix with `let`:

```js
const callbacks = [];

for (let i = 0; i < 3; i += 1) {
  callbacks.push(() => i); // Fresh i binding per iteration.
}

console.log(callbacks.map((callback) => callback())); // [0, 1, 2]
```

Fix with a factory:

```js
function createCallback(index) {
  return () => index;
}

const callbacks = [];

for (var i = 0; i < 3; i += 1) {
  callbacks.push(createCallback(i));
}

console.log(callbacks.map((callback) => callback())); // [0, 1, 2]
```

> [!tip] Tradeoff
> `let` is simpler in modern code. A factory is still useful when you need to capture a derived value or work inside legacy constraints.

## 4. Bug 2: React Interval Reads Old State

Bug:

```jsx
function Timer() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount(count + 1); // count is from the render that created this effect.
    }, 1000);

    return () => clearInterval(id);
  }, []);

  return <p>{count}</p>;
}
```

> [!warning] Failure mode
> the UI goes to `1` and then stays there.

Why:

- The effect runs after the first render because dependencies are `[]`.
- The interval callback closes over the first render's `count`, which is `0`.
- Every tick calls `setCount(0 + 1)`.

Fix for previous-state updates:

```jsx
function Timer() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      // The updater receives the latest committed state.
      setCount((currentCount) => currentCount + 1);
    }, 1000);

    return () => clearInterval(id);
  }, []);

  return <p>{count}</p>;
}
```

> [!tip] Tradeoff
> this fix is excellent when the next state depends only on previous state. If the timer needs a changing `step`, include `step` as a dependency or store the latest step in a ref intentionally.

## 5. Bug 3: Event Listener Reads Old Props

Bug:

```jsx
function SearchShortcut({ query }) {
  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === "Enter") {
        runSearch(query); // query from the first render only.
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
}
```

Fix when listener should react to query changes:

```jsx
function SearchShortcut({ query }) {
  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === "Enter") {
        runSearch(query);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [query]);
}
```

> [!tip] Tradeoff
> the listener is removed and re-added when `query` changes. That is usually fine. If a subscription is expensive and the listener must be stable, use a ref with clear intent.

Ref pattern:

```jsx
function SearchShortcut({ query }) {
  const latestQueryRef = useRef(query);

  useEffect(() => {
    latestQueryRef.current = query;
  }, [query]);

  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === "Enter") {
        runSearch(latestQueryRef.current);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);
}
```

Use refs intentionally. They bypass reactive dependencies by moving the value into a mutable container.

## 6. Bug 4: Missing `useCallback` Dependencies

Bug:

```jsx
function ProductPage({ productId, referrer }) {
  const handleBuy = useCallback((orderDetails) => {
    return post(`/product/${productId}/buy`, {
      referrer,
      orderDetails
    });
  }, []); // Incorrect: productId and referrer are closed over.

  return <BuyButton onBuy={handleBuy} />;
}
```

Fix:

```jsx
function ProductPage({ productId, referrer }) {
  const handleBuy = useCallback((orderDetails) => {
    return post(`/product/${productId}/buy`, {
      referrer,
      orderDetails
    });
  }, [productId, referrer]);

  return <BuyButton onBuy={handleBuy} />;
}
```

> [!tip] Tradeoff
> `useCallback` is not a correctness tool by itself. It caches a function identity while dependencies are equal. If the callback reads reactive values, list them. If that causes too many re-renders, revisit component boundaries, memoization, and whether the callback actually needs to be passed down.

## 7. Bug 5: Debounced Save Sends Old Text

Bug:

```jsx
function Editor({ documentId }) {
  const [text, setText] = useState("");

  const debouncedSave = useMemo(() => {
    return debounce(() => {
      saveDocument(documentId, text); // text from the memo creation render.
    }, 500);
  }, [documentId]);

  function onChange(event) {
    setText(event.target.value);
    debouncedSave();
  }
}
```

Fix by passing changing data as an argument:

```jsx
function Editor({ documentId }) {
  const [text, setText] = useState("");

  const debouncedSave = useMemo(() => {
    return debounce((nextText) => {
      saveDocument(documentId, nextText);
    }, 500);
  }, [documentId]);

  function onChange(event) {
    const nextText = event.target.value;
    setText(nextText);
    debouncedSave(nextText);
  }
}
```

Why the fix works: `nextText` is supplied at call time, so the debounced function does not need to close over React's `text` binding.

Production checklist:

- Cancel pending debounced work on unmount if the helper supports it.
- Decide whether saving latest text should happen on every change, blur, interval, or explicit Save.
- Handle failed saves and out-of-order responses.

## 8. Bug 6: Async Response Uses Old Assumptions

Bug:

```jsx
function UserPanel({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then((response) => response.json())
      .then((data) => {
        setUser(data); // Can update after userId changed or component unmounted.
      });
  }, [userId]);
}
```

This is partly a closure issue and partly an async lifecycle issue. The callback closes over the effect instance for a specific `userId`, but the response may arrive after a newer request.

Fix with cancellation/ignore flag:

```jsx
function UserPanel({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    let ignore = false;

    fetch(`/api/users/${userId}`)
      .then((response) => response.json())
      .then((data) => {
        if (!ignore) {
          setUser(data);
        }
      });

    return () => {
      ignore = true; // Cleanup mutates the binding captured by this effect.
    };
  }, [userId]);
}
```

Better when supported: abort the request.

```jsx
function UserPanel({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const controller = new AbortController();

    fetch(`/api/users/${userId}`, { signal: controller.signal })
      .then((response) => response.json())
      .then(setUser)
      .catch((error) => {
        if (error.name !== "AbortError") {
          throw error;
        }
      });

    return () => controller.abort();
  }, [userId]);
}
```

Tradeoff: an ignore flag prevents stale state updates; aborting also saves network and server work when supported.

## 9. Bug 7: Retained Memory Through Long-Lived Closure

Bug:

```js
function mountLargeTable(rows) {
  const table = document.querySelector("#table");

  function onExportClick() {
    // rows might contain thousands of objects and stays retained
    // as long as the listener is attached.
    exportRows(rows);
  }

  table.addEventListener("click", onExportClick);

  return function cleanup() {
    table.removeEventListener("click", onExportClick);
  };
}
```

Fix options:

```js
function mountLargeTable(rowStore) {
  const table = document.querySelector("#table");

  function onExportClick() {
    // Read fresh data from a store that owns the data lifecycle.
    exportRows(rowStore.getVisibleRows());
  }

  table.addEventListener("click", onExportClick);

  return function cleanup() {
    table.removeEventListener("click", onExportClick);
  };
}
```

Tradeoff: capturing the array is simpler, but it ties memory lifetime to the listener lifetime. Reading from an owner/store can reduce retention but adds indirection.

## 10. Choosing the Right Fix

| Bug shape | Strong fix |
| --- | --- |
| Loop callbacks all read final index | Use `let` or a factory |
| State update depends on previous state | Functional updater |
| Effect synchronizes with changing prop/state | Include dependency and cleanup |
| Stable listener needs latest value | Ref, with clear ownership |
| Debounced/throttled callback needs latest input | Pass value as argument |
| Async result can become stale | Abort, ignore flag, or request id check |
| Closure retains large data | Capture a smaller value, cleanup listener, or move data to owner |

## 11. Debugging Workflow

1. Put a log where the function is created and where it runs.
2. Log the values the closure reads.
3. In React, log render count or a stable render id.
4. Check dependency arrays for every reactive value used by the callback.
5. Check whether cleanup removes the exact same function identity.
6. For async code, test slow network, fast typing, unmount, and prop changes.
7. For memory issues, check whether the closure retains DOM nodes, large arrays, or request data.

## 12. Interview Answer

Short answer:

> Closure bugs happen when a callback uses a binding from the wrong lifetime. The classic one is `var` in a loop; every callback shares the same binding and sees the final value.

Deeper answer:

> The mechanism is that closures preserve access to bindings from the environment where the function was created. With `var`, all loop callbacks can share one function-scoped binding. With React, each render creates new bindings, so an effect or memoized callback can keep reading values from an old render if dependencies are wrong.

Production answer:

> I fix closure bugs by matching the fix to the ownership model: `let` or factories for loop bindings, functional updaters for previous state, dependency arrays for synchronization, refs for intentionally mutable latest values, argument passing for debounced functions, and abort/cleanup for async work.

## 13. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Just add everything to dependencies." | Correctness first, but sometimes the code should be restructured to remove unnecessary dependencies. |
| "Use refs to avoid dependency arrays." | Refs are mutable escape hatches; use them deliberately. |
| "The linter is optional." | Suppressing dependency warnings often creates stale closure bugs. |
| "Debounce fixes stale data automatically." | A debounced function can preserve stale values unless it receives latest data. |
| "Async bugs are only race conditions." | Many races are also closure/lifetime problems. |

## 14. Practice

1. Predict the output:

```js
const fns = [];

for (var i = 0; i < 3; i += 1) {
  fns.push(() => i);
}

console.log(fns.map((fn) => fn()).join(","));
```

Expected output: `"3,3,3"`.

2. Fix the same code using `let`.
3. Fix the same code using a factory function.
4. Explain why an interval with `[]` dependencies can keep setting state to the same value.
5. Rewrite a debounced save so the latest text is passed as an argument.
6. Add abort handling to an effect that fetches on `userId` change.
7. Explain when a ref is a good stale-closure fix and when it hides a bug.

## Real-World Use Cases

### Map SDK callback registered once, reads state forever

Imperative SDKs (Mapbox, Google Maps, Stripe Elements) take a callback at setup time and never ask again. Registering it in a mount-only effect freezes whatever render it was born in.

```jsx
function StoreLocator({ selectedRegion }) {
  const mapRef = useRef(null);

  useEffect(() => {
    const map = new mapboxgl.Map({ container: mapRef.current });
    map.on("click", (event) => {
      // selectedRegion is from the mount render — filters never apply.
      openNearestStore(event.lngLat, selectedRegion);
    });
    return () => map.remove();
  }, []); // recreating the whole map per region change is not an option

  return <div ref={mapRef} />;
}
```

This is Bug 3's mechanism, but re-running the effect is off the table because map construction is expensive — so the ref pattern from section 5 is the right tool: mirror `selectedRegion` into a ref and read `latestRegionRef.current` inside the callback. The "too old" lifetime is fixed by routing the read through a mutable container instead of the closure.

> [!tip]
> This is the strongest real-world justification for the latest-value ref pattern: a subscription that is expensive to tear down but must see fresh state. See [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]].

### Module-scope closure leaks state across server requests

A Next.js team ports a browser helper that caches "the current user" in module scope. In the browser one user owns the process; on the server every request shares it.

```ts
// lib/currentUser.ts — DANGEROUS on the server
let cachedUser: User | null = null;

export async function getCurrentUser(req: Request) {
  if (cachedUser) return cachedUser;      // may be another request's user!
  cachedUser = await loadUser(req);
  return cachedUser;
}
```

This is the "too shared" lifetime from section 1 at process scale: the module's Environment Record is created once per server process, so every concurrent request's call closes over the same `cachedUser` binding. Fix by scoping the cache to the request (pass it down, use `React.cache`, or `AsyncLocalStorage`) — never module scope for request-owned data ([[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]).

> [!warning]
> This bug ships silently: it passes local testing (one user) and code review (the code "works"), then leaks user A's data to user B under production concurrency.

### Toast auto-dismiss removes the wrong toasts

Each toast schedules its own removal. The timer callback filters the `toasts` array from the render that created it, so dismissing one toast resurrects others added since.

```jsx
function useToasts() {
  const [toasts, setToasts] = useState([]);

  function addToast(toast) {
    setToasts([...toasts, toast]);
    setTimeout(() => {
      setToasts(toasts.filter((t) => t.id !== toast.id)); // stale array!
    }, 4000);
  }

  return { toasts, addToast };
}
```

Both reads of `toasts` are frozen at the render where `addToast` was created — the timeout wipes every toast added afterward. Functional updaters fix both sites, because React supplies the latest committed state at call time instead of the closure supplying an old one:

```jsx
setToasts((current) => [...current, toast]);
setTimeout(() => {
  setToasts((current) => current.filter((t) => t.id !== toast.id));
}, 4000);
```

Same fix family as Bug 2, but the failure looks like a UI glitch ("my toasts vanish early") rather than a stuck counter — which is why it survives longer in real codebases.

## Related Notes

- [[03 - Scope and Variables/01 - Scope Types|Scope Types]]
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/03 - var let const|var let const]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[17 - Practical Frontend Scenarios/01 - Fixing Stale Closure in React|Fixing Stale Closure in React]]
- [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]]
- [[01 - Roadmap|Roadmap]]
