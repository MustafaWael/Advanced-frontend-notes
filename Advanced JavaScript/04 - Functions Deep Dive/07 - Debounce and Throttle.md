---
tags: [javascript, functions, debounce-and-throttle]
module: "04 - Functions Deep Dive"
priority: must-know
status: not-started
aliases: [Debounce, Throttle]
---

# Debounce and Throttle

## Maturity Target

- Priority: #must-know
- Study time: 100-120 minutes
- Interview signal: you can explain debounce vs throttle, leading/trailing edges, closure state, and timer cleanup.
- Production signal: you can implement rate limiting without losing arguments, `this`, cancellation, or async correctness.
- Dependencies: [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]], [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]], [[09 - Event Loop Advanced/04 - Timers|Timers]]

## Source Anchors

- [MDN Glossary - Debounce](https://developer.mozilla.org/en-US/docs/Glossary/Debounce)
- [MDN Glossary - Throttle](https://developer.mozilla.org/en-US/docs/Glossary/Throttle)
- [MDN - setTimeout](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout)
- [MDN - requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)
- [React - useEffect](https://react.dev/reference/react/useEffect)

## 1. Concept

Debounce waits until calls stop for a delay, then runs once. It is for final intent.

Throttle runs at most once per time window. It is for steady rate limiting.

```txt
Typing search query: debounce
Scrolling position: throttle or requestAnimationFrame
Window resize final layout calculation: debounce
Drag position updates: throttle or requestAnimationFrame
```

Both are higher-order functions. They wrap another function and use closure state to remember timer ids, timestamps, and last arguments.

## 2. Why It Matters

Frontend events can fire many times per second:

- `input`
- `scroll`
- `resize`
- `mousemove`
- `pointermove`
- `keydown`

Calling expensive code on every event can cause jank, unnecessary renders, duplicate network requests, and server load. Rate limiting improves responsiveness, but it can also create stale data or cleanup bugs if implemented casually.

## 3. Debounce Mental Model

Debounce groups noisy calls into one final call.

```txt
call A ---- call B ---- call C ---------------- run C
       timer reset timer reset      delay passes
```

Use debounce when you care about the last value after the user pauses:

- Search suggestions after typing stops.
- Save draft after editing pauses.
- Recalculate layout after resizing stops.

## 4. Throttle Mental Model

Throttle limits execution to one call per interval.

```txt
call A run ---- call B skipped ---- call C skipped ---- call D run
```

Use throttle when you need regular updates without running on every event:

- Scroll progress.
- Drag updates.
- Mouse position sampling.
- Infinite scroll checks.

For visual updates tied to paint, `requestAnimationFrame` is often a better fit than a millisecond throttle.

## 5. Debounce Implementation

```js
function debounce(fn, delayMs) {
  let timeoutId = null;

  function debounced(...args) {
    const context = this;

    clearTimeout(timeoutId);

    timeoutId = setTimeout(() => {
      timeoutId = null;
      fn.apply(context, args);
    }, delayMs);
  }

  debounced.cancel = function cancel() {
    clearTimeout(timeoutId);
    timeoutId = null;
  };

  return debounced;
}
```

Why this implementation is production-aware:

- It preserves arguments with `...args`.
- It preserves dynamic `this` with `fn.apply(context, args)`.
- It exposes `cancel` for cleanup.
- The timer id lives in a closure.

Example:

```js
const logSearch = debounce((query) => {
  console.log(`search:${query}`);
}, 300);

logSearch("r");
logSearch("re");
logSearch("rea");

// After 300ms of no more calls:
// search:rea
```

## 6. Leading and Trailing Debounce

Sometimes you want the first call immediately and then ignore the rest until the user stops.

```js
function debounceLeading(fn, delayMs) {
  let timeoutId = null;

  return function debounced(...args) {
    const context = this;
    const shouldCallNow = timeoutId === null;

    clearTimeout(timeoutId);

    timeoutId = setTimeout(() => {
      timeoutId = null;
    }, delayMs);

    if (shouldCallNow) {
      fn.apply(context, args);
    }
  };
}
```

Use leading debounce for things like "submit once when clicked rapidly." Use trailing debounce for "process the final text after typing."

## 7. Throttle Implementation

Simple leading throttle:

```js
function throttle(fn, intervalMs) {
  let lastRun = 0;

  return function throttled(...args) {
    const now = Date.now();

    if (now - lastRun < intervalMs) {
      return;
    }

    lastRun = now;
    return fn.apply(this, args);
  };
}
```

Leading + trailing throttle:

```js
function throttleTrailing(fn, intervalMs) {
  let lastRun = 0;
  let timeoutId = null;
  let lastArgs;
  let lastContext;

  function run() {
    lastRun = Date.now();
    timeoutId = null;
    fn.apply(lastContext, lastArgs);
    lastArgs = undefined;
    lastContext = undefined;
  }

  function throttled(...args) {
    const remaining = intervalMs - (Date.now() - lastRun);
    lastArgs = args;
    lastContext = this;

    if (remaining <= 0) {
      clearTimeout(timeoutId);
      run();
      return;
    }

    if (timeoutId === null) {
      timeoutId = setTimeout(run, remaining);
    }
  }

  throttled.cancel = function cancel() {
    clearTimeout(timeoutId);
    timeoutId = null;
    lastArgs = undefined;
    lastContext = undefined;
  };

  return throttled;
}
```

> [!tip] Tradeoff
> simple throttle is easy to reason about but can drop the final user intent. Trailing throttle is more complete but has more state.

## 8. `requestAnimationFrame` for UI Updates

For scroll or pointer movement that updates the DOM, align work with the browser paint cycle.

```js
function rafThrottle(fn) {
  let frameId = null;
  let lastArgs;
  let lastContext;

  function run() {
    frameId = null;
    fn.apply(lastContext, lastArgs);
  }

  return function throttled(...args) {
    lastArgs = args;
    lastContext = this;

    if (frameId === null) {
      frameId = requestAnimationFrame(run);
    }
  };
}
```

Use this for visual work like scroll position indicators. Use time-based throttle for rate limits that are not tied to painting.

## 9. Real Frontend Scenario: Debounced Search

Bug: debounce reduces requests, but older async responses can still overwrite newer results.

```jsx
function SearchBox() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  const search = useMemo(() => {
    return debounce(async (nextQuery) => {
      const response = await fetch(`/api/search?q=${encodeURIComponent(nextQuery)}`);
      setResults(await response.json());
    }, 300);
  }, []);

  function onChange(event) {
    const nextQuery = event.target.value;
    setQuery(nextQuery);
    search(nextQuery);
  }
}
```

> [!warning] Failure mode
> a slow response for `"rea"` can arrive after a faster response for `"react"` and overwrite newer results.

Fix with `AbortController`:

```jsx
function SearchBox() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const controllerRef = useRef(null);

  const search = useMemo(() => {
    return debounce(async (nextQuery) => {
      controllerRef.current?.abort();

      const controller = new AbortController();
      controllerRef.current = controller;

      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(nextQuery)}`, {
          signal: controller.signal
        });
        setResults(await response.json());
      } catch (error) {
        if (error.name !== "AbortError") {
          throw error;
        }
      }
    }, 300);
  }, []);

  useEffect(() => {
    return () => {
      search.cancel();
      controllerRef.current?.abort();
    };
  }, [search]);

  function onChange(event) {
    const nextQuery = event.target.value;
    setQuery(nextQuery);
    search(nextQuery);
  }
}
```

> [!tip] Tradeoff
> debounce solves input noise. Abort/cancellation solves stale network results. You often need both.

## 10. React Hook Pattern

Debounced value:

```jsx
function useDebouncedValue(value, delayMs) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const id = setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);

    return () => clearTimeout(id);
  }, [value, delayMs]);

  return debouncedValue;
}
```

Usage:

```jsx
function SearchBox() {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 300);

  useEffect(() => {
    if (debouncedQuery === "") {
      return;
    }

    // Fetch based on debouncedQuery here.
  }, [debouncedQuery]);
}
```

This pattern is often easier to reason about than memoizing a debounced function.

## 11. Common Bugs

| Bug | Why it happens | Fix |
| --- | --- | --- |
| Losing arguments | Wrapper calls `fn()` instead of `fn(...args)` | Forward rest args |
| Losing `this` | Wrapper calls `fn(...args)` when dynamic receiver matters | Use `fn.apply(this, args)` |
| Stale React state | Debounced function closes over old render values | Pass values as args or update dependencies |
| Timer fires after unmount | No cleanup/cancel | Clear timeout/cancel wrapper |
| Old response overwrites new | Debounce does not cancel network | Abort or request id |
| Scroll still janks | Throttled work is too heavy | Reduce work, use rAF, virtualize, move work off main path |

## Real-World Use Cases

The note's core scenario is debounced search (section 9). These are the other places rate limiting earns its keep in a product codebase.

### Autosave editor: debounce with `flush`, not `cancel`

A notes editor autosaves 800ms after typing pauses. On unmount you must not `cancel()` — that throws away the user's last keystrokes. You need the opposite: run the pending call *now*.

```js
function debounceWithFlush(fn, delayMs) {
  let timeoutId = null;
  let pending = null;

  function debounced(...args) {
    pending = args;
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => { timeoutId = null; fn(...pending); pending = null; }, delayMs);
  }

  debounced.flush = () => {
    if (timeoutId === null) return;
    clearTimeout(timeoutId);
    timeoutId = null;
    fn(...pending);            // fire the trailing call immediately
    pending = null;
  };

  return debounced;
}
```

In the component: `useEffect(() => () => saveDraft.flush(), [])`. The closure holding `pending` args is what makes flush possible — the wrapper remembers the last intent, so it can either drop it (cancel) or honor it early (flush).

> [!warning]
> `cancel` on unmount is correct for *reads* (search requests) and data loss for *writes* (drafts, form autosave). Decide per call site which one the product needs.

### Throttled scroll-depth analytics

Marketing wants scroll-depth events on articles. `scroll` fires continuously; sending an event per tick would flood the analytics endpoint and jank the page.

```js
const trackScrollDepth = throttleTrailing(() => {
  const depth = Math.round(
    (window.scrollY + window.innerHeight) / document.body.scrollHeight * 100
  );
  analytics.track("scroll_depth", { depth });
}, 2_000);

window.addEventListener("scroll", trackScrollDepth, { passive: true });
```

Trailing behavior matters here: a plain leading throttle drops the *final* position — exactly the number marketing cares about. The closure's `lastArgs`/timer state is what lets the trailing call report where the user actually stopped.

> [!tip]
> `{ passive: true }` tells the browser the handler never calls `preventDefault()`, so scrolling is not blocked waiting on your JavaScript at all.

### Infinite scroll trigger: throttle vs `IntersectionObserver`

A product-feed page loads the next page when the user nears the bottom. The throttled-scroll version works but still wakes JavaScript on every interval:

```js
const maybeLoadMore = throttle(() => {
  const nearBottom =
    window.innerHeight + window.scrollY >= document.body.offsetHeight - 800;
  if (nearBottom && !isLoading) loadNextPage();
}, 250);

window.addEventListener("scroll", maybeLoadMore);
```

The modern default deletes the rate-limiting problem instead of managing it:

```js
const sentinel = document.querySelector("#feed-end");
new IntersectionObserver(
  entries => { if (entries[0].isIntersecting && !isLoading) loadNextPage(); },
  { rootMargin: "800px" }
).observe(sentinel);
```

Throttle exists because `scroll` calls *you* too often; `IntersectionObserver` inverts it so the browser calls you only when the answer changes. Knowing when the right fix is "no throttle at all" is the senior version of this topic. Note `isLoading` here plays the same role as the timer id in debounce — closure state guarding duplicate calls.

See [[19 - DOM and Browser APIs/06 - Observers|Observers]] and [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]].

## 12. Interview Answer

Short answer:

> Debounce waits until calls stop, then runs once. Throttle runs at most once per interval.

Deeper answer:

> Both are higher-order functions implemented with closures and timers. Debounce stores a timer id and resets it on each call. Throttle stores last-run state and skips or delays calls during the interval. Production implementations need to preserve arguments and `this`, expose cancellation, and consider leading/trailing behavior.

Production answer:

> I use debounce for final intent like search after typing pauses, throttle for steady updates like scroll progress, and `requestAnimationFrame` for visual updates tied to paint. For async search, debounce is not enough; I also need cancellation or stale-response protection.

## 13. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Debounce prevents race conditions." | It reduces calls, but old requests can still finish late. |
| "Throttle and debounce are interchangeable." | Debounce waits for quiet; throttle samples over time. |
| "A wrapper can call `fn()` directly." | It may drop arguments and `this`. |
| "Cleanup is optional." | Timers and pending requests can fire after unmount. |
| "Scroll handlers only need throttling." | Work size matters; visual work often belongs in rAF. |

## 14. Practice

1. Implement `debounce(fn, delay)` that preserves arguments and supports `cancel`.
2. Implement leading throttle and explain what happens to skipped calls.
3. Add trailing behavior to a throttle.
4. Fix a debounced React search that closes over stale `query`.
5. Explain why debounce does not replace `AbortController`.
6. Decide between debounce, throttle, and rAF for: search input, resize final calculation, scroll progress, drag preview.

## Related Notes

- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[04 - Functions Deep Dive/06 - Currying and Partial Application|Currying and Partial Application]]
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[09 - Event Loop Advanced/04 - Timers|Timers]]
- [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
- [[01 - Roadmap|Roadmap]]
