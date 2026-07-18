---
tags: [javascript, event-loop, timers]
module: "09 - Event Loop Advanced"
priority: must-know
status: not-started
---

# Timers

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can explain minimum delay, task scheduling, timer drift, interval cleanup, and `this` loss in timer callbacks.
- Production signal: you use timers safely for debounce, polling, delayed UI, and chunking without leaks or overlapping async work.
- Dependencies: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]], [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]

## Source Anchors

- [MDN setTimeout](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout)
- [MDN setInterval](https://developer.mozilla.org/en-US/docs/Web/API/Window/setInterval)
- [MDN clearTimeout](https://developer.mozilla.org/en-US/docs/Web/API/Window/clearTimeout)
- [HTML Living Standard: Timers](https://html.spec.whatwg.org/multipage/timers-and-user-prompts.html#timers)
- [web.dev: Optimize long tasks](https://web.dev/articles/optimize-long-tasks)
- [React useEffect](https://react.dev/reference/react/useEffect)

## 1. Concept

Timers are host APIs that schedule callbacks for later tasks.

```js
setTimeout(callback, delay);
setInterval(callback, interval);
```

The delay is a minimum delay, not a guaranteed exact execution time. The callback can run only when the event loop is able to pick the timer task.

## 2. Why It Matters

Timers power:

- debounce and throttle utilities
- polling
- delayed UI feedback
- retry backoff
- chunking long work
- test delays
- temporary notifications

They also cause bugs:

- interval keeps running after unmount
- async interval overlaps requests
- timer callback loses `this`
- `setTimeout(fn, 0)` is treated as immediate
- background tab throttling changes timing
- stale closure reads old state

## 3. Official Mechanism

Timers are browser/host APIs, not ECMAScript language features.

Important rules:

- `setTimeout` schedules one callback.
- `setInterval` schedules repeated callbacks until cleared.
- Both return an id/handle.
- `clearTimeout` cancels a timeout handle.
- `clearInterval` cancels an interval handle.
- A delay of `0` means "as soon as eligible in a later task", not "right now."
- Browser policies can clamp or throttle timer delays, especially nested timers and background tabs.
- The actual run time can be delayed by synchronous code, microtasks, rendering, and host scheduling.

## 4. Mental Model

A timer says:

```txt
run no earlier than this delay, when the event loop can run another task
```

It does not say:

```txt
interrupt current JavaScript exactly at this time
```

## 5. Code Output: Timer After Sync And Microtasks

```js
console.log("A");

setTimeout(() => console.log("D"), 0);

Promise.resolve().then(() => console.log("C"));

console.log("B");
```

Expected:

```txt
A
B
C
D
```

The timer callback runs as a later task after synchronous code and microtasks.

## 6. Blocking Delays Timers

```js
console.log("start");

setTimeout(() => console.log("timer"), 0);

const started = Date.now();
while (Date.now() - started < 200) {
  // Simulate blocking work.
}

console.log("end");
```

Expected:

```txt
start
end
timer
```

The timer could not run during the blocking loop.

## 7. `setInterval` With Async Work

### Problem

```js
setInterval(async () => {
  await fetchLatestStatus();
}, 1000);
```

### Bug

> [!warning] setInterval ignores async duration
> `setInterval` fires on a fixed schedule regardless of whether the previous async callback finished. If `fetchLatestStatus` takes 3 seconds, new requests pile up while older ones are still in flight. A self-scheduling `setTimeout` (fire the next only after the current completes) avoids the overlap.

### Fix: Recursive `setTimeout`

```js
let stopped = false;

async function poll() {
  if (stopped) return;

  try {
    await fetchLatestStatus();
  } finally {
    if (!stopped) {
      setTimeout(poll, 1000);
    }
  }
}

poll();

function stopPolling() {
  stopped = true;
}
```

This schedules the next poll after the previous one finishes.

## 8. React Timer Cleanup

```jsx
function Countdown({ seconds }) {
  const [remaining, setRemaining] = useState(seconds);

  useEffect(() => {
    const id = setInterval(() => {
      setRemaining(value => Math.max(0, value - 1));
    }, 1000);

    return () => clearInterval(id);
  }, []);

  return <span>{remaining}</span>;
}
```

Why this works:

- the interval is created when the effect runs
- cleanup clears it on unmount
- functional state update avoids stale `remaining`

Common bug:

```jsx
useEffect(() => {
  const id = setInterval(() => {
    setRemaining(remaining - 1);
  }, 1000);

  return () => clearInterval(id);
}, []);
```

The callback closes over the initial `remaining` value.

## 9. Debounce Pattern

```jsx
function SearchBox({ onSearch }) {
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (!query.trim()) return;

    const id = setTimeout(() => {
      onSearch(query);
    }, 300);

    return () => clearTimeout(id);
  }, [query, onSearch]);

  return (
    <input
      value={query}
      onChange={event => setQuery(event.target.value)}
    />
  );
}
```

Every query change clears the previous timeout. Only the latest value after 300ms triggers search.

## 10. Chunking Long Work

```js
function processItems(items) {
  let index = 0;

  function processChunk() {
    const deadline = performance.now() + 8;

    while (index < items.length && performance.now() < deadline) {
      processItem(items[index]);
      index += 1;
    }

    if (index < items.length) {
      setTimeout(processChunk, 0);
    }
  }

  processChunk();
}
```

This yields between chunks so the browser can process other work. It is not as powerful as a worker, but it can prevent one large task from blocking the main thread for too long.

## 11. `this` Loss In Timer Callbacks

```js
const counter = {
  count: 0,
  increment() {
    this.count += 1;
  },
};

setTimeout(counter.increment, 0);
```

The method is passed as a plain function. Its `this` binding is lost.

Fix:

```js
setTimeout(() => counter.increment(), 0);
```

Or bind explicitly:

```js
setTimeout(counter.increment.bind(counter), 0);
```

## 12. Production Checklist

- Clear timers in React cleanup.
- Use functional state updates inside timer callbacks when reading prior state.
- Treat timer delay as minimum delay.
- Avoid `setInterval` for async polling unless overlapping is safe.
- Use recursive `setTimeout` when the next run depends on the previous run finishing.
- Debounce user input with timeout cleanup.
- Use `requestAnimationFrame` for visual frame work, not `setTimeout(fn, 16)`.
- Do not use timer strings; pass functions.
- Account for background-tab throttling in analytics, polling, and timers.
- Use `ReturnType<typeof setTimeout>` for cross-environment TypeScript timer handles.

## 13. Interview Answer

**Short version:** `setTimeout` schedules one future task and `setInterval` schedules repeated future tasks. The delay is a minimum; callbacks run only when the event loop can pick them.

**Strong version:** Timers are host APIs defined by the web platform, not ECMAScript. A zero-delay timer runs in a later task after the current task and microtasks finish. Actual timing can be delayed by long synchronous work, microtasks, browser throttling, and rendering. In production, timers need cleanup, especially in React effects. For async polling, `setInterval` can overlap requests because it does not await the callback, so recursive `setTimeout` is often safer.

## 14. Common Mistakes

- Expecting `setTimeout(fn, 0)` to run immediately.
- Not clearing intervals on unmount.
- Using `setInterval` with async work that can overlap.
- Capturing stale state in timer callbacks.
- Passing object methods to timers and losing `this`.
- Using timers for animation instead of `requestAnimationFrame`.
- Assuming timer behavior is identical in visible tabs, background tabs, workers, and Node.

## 15. Practice

1. Predict the output of the timer/microtask example.
2. Fix a leaking interval in a React effect.
3. Rewrite async `setInterval` polling with recursive `setTimeout`.
4. Implement a debounced search input.
5. Explain why a timer callback can be delayed by blocking JavaScript.

## Real-World Use Cases

### Retry with exponential backoff and jitter

A flaky mobile network fails the first request to `/api/orders`. Retrying immediately hammers a struggling server; a timer-based backoff spaces the attempts out.

```ts
async function fetchWithRetry(url: string, attempts = 4) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await fetch(url).then(assertOk);
    } catch (error) {
      if (attempt === attempts - 1) throw error;
      const delay = 2 ** attempt * 500 + Math.random() * 250; // jitter
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

The `setTimeout`-wrapped promise creates a task boundary between attempts, so the main thread stays free for input and paint while waiting.

> [!tip] Jitter prevents retry stampedes
> Without the random component, every client that failed at the same moment retries at the same moment. Pair this with [[08 - Async JavaScript/06 - AbortController|AbortController]] so an unmounted component stops the retry loop.

### Show the spinner only if loading is slow

Navigation usually resolves in 80ms. Showing a spinner for every request means a distracting flash on fast loads. Delay the indicator, and cancel it if data wins the race.

```tsx
function useDelayedPending(isPending: boolean, delayMs = 300) {
  const [showSpinner, setShowSpinner] = useState(false);

  useEffect(() => {
    if (!isPending) return setShowSpinner(false);
    const id = setTimeout(() => setShowSpinner(true), delayMs);
    return () => clearTimeout(id); // fast response: spinner never appears
  }, [isPending, delayMs]);

  return showSpinner;
}
```

This inverts the usual debounce: the timer schedules *UI feedback*, and clearing it on early completion is what makes the pattern work — the same schedule/cancel pair as [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]].

### Background-tab throttling breaks a session countdown

A banking app shows "logged out in 5:00" by decrementing state every second. The user switches tabs; the browser clamps background timers to once per minute (or less), and the countdown returns wildly wrong.

```js
// Bug: counts ticks — assumes the interval actually fires every 1000ms
setInterval(() => setSecondsLeft(seconds => seconds - 1), 1000);

// Fix: derive from wall-clock time; ticks only refresh the display
const expiresAt = Date.now() + 5 * 60_000;
setInterval(() => {
  setSecondsLeft(Math.max(0, Math.round((expiresAt - Date.now()) / 1000)));
}, 1000);

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) forceRefresh(); // resync the moment the tab returns
});
```

The mechanism: a timer's delay is a *minimum*, and host throttling can stretch it arbitrarily — so ticks are a rendering hint, never a clock.

> [!warning] Never enforce deadlines client-side by counting ticks
> Session expiry, auction ends, and OTP windows must compare against a timestamp (ideally server-issued). Throttled tabs, sleep/wake, and clock drift all lie to tick counters.

## Related Notes

- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]
- [[01 - Roadmap|Roadmap]]
