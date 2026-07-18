---
tags: [javascript, performance, memory, event-listeners-and-timers-cleanup]
module: "13 - Performance and Memory"
priority: must-know
status: not-started
---

# Event Listeners and Timers Cleanup

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: you can explain why listeners/timers retain callbacks, how cleanup works, and why function identity matters.
- Production signal: effects, listeners, intervals, animation frames, observers, and subscriptions are paired with correct cleanup.
- Dependencies: [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]], [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]], [[08 - Async JavaScript/06 - AbortController|AbortController]]

## Source Anchors

- [MDN addEventListener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener)
- [MDN removeEventListener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/removeEventListener)
- [MDN setInterval](https://developer.mozilla.org/en-US/docs/Web/API/Window/setInterval)
- [MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [React useEffect](https://react.dev/reference/react/useEffect)

## 1. Concept

Listeners and timers are registrations with a host system. The host keeps enough information to call your callback later. That callback may keep its closure alive.

Cleanup ends that ownership.

```tsx
useEffect(() => {
  function onResize() {
    setWidth(window.innerWidth);
  }

  window.addEventListener("resize", onResize);

  return () => {
    window.removeEventListener("resize", onResize);
  };
}, []);
```

## 2. Why It Matters

Leaks and duplicate work often come from missing cleanup:

- old components still respond to events;
- intervals keep running after navigation;
- animation loops continue in hidden screens;
- websocket subscriptions deliver duplicate messages;
- listeners retain DOM nodes or large state through closures.

React effects make setup/cleanup visible, but they do not clean up arbitrary work unless you return the cleanup function.

## 3. Accurate Mechanism

`addEventListener` registers a callback for a target and event type. To remove a listener manually, you must pass the same function reference and compatible listener options, especially capture.

```js
function onScroll() {}

window.addEventListener("scroll", onScroll, { passive: true });
window.removeEventListener("scroll", onScroll);
```

This works because the function reference is the same and capture defaults to `false`.

This does not work:

```js
window.addEventListener("resize", () => console.log("resize"));
window.removeEventListener("resize", () => console.log("resize"));
```

Those are two different functions.

## 4. Mental Model

Every setup line should have a matching teardown line.

| Setup | Cleanup |
| --- | --- |
| `addEventListener` | `removeEventListener` or abort signal |
| `setInterval` | `clearInterval` |
| `setTimeout` | `clearTimeout` if still pending |
| `requestAnimationFrame` | `cancelAnimationFrame` |
| `IntersectionObserver.observe` | `disconnect` or `unobserve` |
| websocket/store subscription | returned unsubscribe |
| `URL.createObjectURL` | `URL.revokeObjectURL` |

## 5. Real Frontend Bug: Anonymous Listener

Problem:

```tsx
function WidthTracker() {
  useEffect(() => {
    window.addEventListener("resize", () => {
      console.log(window.innerWidth);
    });
  }, []);

  return null;
}
```

Bug:

- there is no cleanup;
- the listener cannot be removed because the function reference was not kept;
- repeated mounts add repeated listeners.

Fix:

```tsx
function WidthTracker() {
  useEffect(() => {
    function handleResize() {
      console.log(window.innerWidth);
    }

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, []);

  return null;
}
```

## 6. AbortSignal Cleanup For Listeners

Modern `addEventListener` supports an `AbortSignal`.

```tsx
useEffect(() => {
  const controller = new AbortController();

  window.addEventListener(
    "pointermove",
    handlePointerMove,
    { signal: controller.signal, passive: true }
  );

  return () => {
    controller.abort();
  };
}, []);
```

Benefits:

- one abort can clean up multiple listeners;
- cleanup does not require repeating every target/event pair;
- still keep code readable and scoped.

## 7. Timer Cleanup

Problem:

```tsx
function Clock() {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    setInterval(() => {
      setNow(Date.now());
    }, 1000);
  }, []);

  return <time>{now}</time>;
}
```

> [!warning] Bug
> the interval keeps running after unmount.

Fix:

```tsx
useEffect(() => {
  const id = window.setInterval(() => {
    setNow(Date.now());
  }, 1000);

  return () => {
    window.clearInterval(id);
  };
}, []);
```

For animation loops:

```tsx
useEffect(() => {
  let frame = 0;

  function tick() {
    draw();
    frame = requestAnimationFrame(tick);
  }

  frame = requestAnimationFrame(tick);

  return () => cancelAnimationFrame(frame);
}, []);
```

## 8. Passive and Once Options

Use `passive: true` for scroll/touch listeners that do not call `preventDefault`. This tells the browser the listener will not block scrolling.

```js
window.addEventListener("touchmove", onTouchMove, { passive: true });
```

Use `once: true` when a listener should auto-remove after its first call.

```js
button.addEventListener("click", handleFirstClick, { once: true });
```

These options improve behavior, but they do not replace lifecycle cleanup for long-lived owners.

## 9. Production Tradeoffs

| Pattern | Benefit | Risk |
| --- | --- | --- |
| Named handler + remove | explicit and widely understood | more boilerplate |
| AbortSignal | cleans multiple listeners | requires browser support awareness |
| `once: true` | self-cleaning one-shot listener | not for repeated interactions |
| `passive: true` | smoother scrolling | cannot call `preventDefault` |
| Stable callback | removable and less allocation | may close over stale values if dependencies are wrong |

## Real-World Use Cases

### Dropdown outside-click listener on `document`

A menu closes when the user clicks anywhere outside it. The listener has to live on `document` — an owner that outlives the component — so cleanup is what keeps open/close cycles from stacking handlers.

```tsx
useEffect(() => {
  if (!isOpen) return;

  function onPointerDown(event: PointerEvent) {
    if (!menuRef.current?.contains(event.target as Node)) {
      setOpen(false);
    }
  }

  document.addEventListener("pointerdown", onPointerDown);
  return () => document.removeEventListener("pointerdown", onPointerDown);
}, [isOpen]);
```

Works because the named handler gives `removeEventListener` the same function reference, and gating on `isOpen` means the document only carries the listener while the menu is open. Without cleanup, `document` retains each closure — and through it the ref and setState of unmounted menus. See [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]].

### Debounce timer inside a custom hook

A search box waits 300ms of quiet before filtering. The cleanup function is not just unmount safety — it *is* the debounce.

```tsx
function useDebouncedValue<T>(value: T, delay = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id); // cancels the pending timer on every keystroke
  }, [value, delay]);

  return debounced;
}
```

Works because React runs the previous cleanup before each re-run: every new `value` clears the pending timeout, so only the last one fires — and unmount clears it too, preventing a setState on a dead component. See [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]].

### Zombie WebSocket reconnect timer

A price ticker reconnects 2s after the socket drops. Naive cleanup closes the socket — which fires `onclose`, which schedules a reconnect, which reopens the socket after the user has navigated away.

```tsx
useEffect(() => {
  let socket: WebSocket;
  let reconnectId: number | undefined;
  let closed = false;

  function connect() {
    socket = new WebSocket(PRICE_FEED_URL);
    socket.onmessage = (event) => setQuote(JSON.parse(event.data));
    socket.onclose = () => {
      if (!closed) reconnectId = window.setTimeout(connect, 2000);
    };
  }
  connect();

  return () => {
    closed = true;              // stop the reconnect loop first
    clearTimeout(reconnectId);  // kill any pending reconnect
    socket.close();
  };
}, []);
```

Works because teardown clears *both* registrations the setup created: the pending timer and the socket. The `closed` flag matters because `socket.close()` itself triggers `onclose` — cleanup that re-arms the thing it is cleaning is a classic leak shape. See [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]].

> [!warning]
> React Strict Mode's double setup/cleanup cycle exposes this bug in development: if you see two sockets connect, your cleanup is not symmetrical with your setup.

## 10. Interview Answer

**Short version:** Event targets and timer APIs keep references to callbacks. If the owner goes away, you must remove the listener, clear the timer, cancel the frame, or unsubscribe so the callback and its captured data can be released.

**Strong version:** Adding a listener creates a host registration. The host can retain the function, and the function can retain its lexical environment. Cleanup must use the same function reference for `removeEventListener`, or use an `AbortSignal` where supported. Timers and animation frames similarly need `clearInterval`, `clearTimeout`, or `cancelAnimationFrame`. In React, effect setup should mirror cleanup, and development Strict Mode helps reveal missing cleanup through extra setup/cleanup cycles.

## 11. Common Mistakes

- Removing a listener with a different anonymous function.
- Forgetting the capture option when removing captured listeners.
- Assuming unmount stops intervals automatically.
- Creating animation loops without canceling the last frame.
- Recreating listeners every render without cleanup.
- Using `passive: true` and then calling `preventDefault`.
- Forgetting subscriptions from event buses, stores, and sockets.

## 12. Practice

1. Fix an anonymous resize listener so it can be removed.
2. Use `AbortController` to clean up two listeners in one effect.
3. Add cleanup to a `setInterval` clock.
4. Explain why a listener can retain old component state.
5. Name the cleanup API for timers, animation frames, observers, workers, and object URLs.

## Related Notes

- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[17 - Practical Frontend Scenarios/06 - Cleaning Event Listeners|Cleaning Event Listeners]]
- [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]
- [[01 - Roadmap|Roadmap]]
