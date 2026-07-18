---
tags: [javascript, react, nextjs, closures-in-hooks]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# Closures in Hooks

## Maturity Target

- Priority: #must-know
- Study time: 75-100 minutes
- Interview signal: can connect closures to `useEffect`, `useMemo`, `useCallback`, event handlers, and batched state updates.
- Production signal: can decide when to use dependencies, functional updates, or refs.
- Fast track: study sections 3, 5, 6, 8, then explain the practice answers aloud.

## Source Anchors

- [MDN: Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [React docs: State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [React docs: Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [React docs: useCallback](https://react.dev/reference/react/useCallback)
- [React docs: useMemo](https://react.dev/reference/react/useMemo)

## 1. Concept

A closure is a function plus the lexical environment it was created in. In React, every component render creates a new lexical environment. Hook callbacks, event handlers, timers, promise callbacks, and memoized functions close over the props, state, and local variables from the render that created them.

That is the root of many hook behaviors:

- `useEffect` setup closes over the render that scheduled it.
- `useMemo` closes over values used by the calculation.
- `useCallback` returns a function that closes over values from the render when it was last created.
- Event handlers close over the render that produced the JSX.
- Functional state updates can avoid needing a closed-over state value.

## 2. Why It Matters

Hooks make closures visible. In class components, `this.state` pointed at mutable instance state. In function components, each render has its own fixed state values. This is usually easier to reason about, but it punishes vague dependency arrays and long-lived callbacks.

Production symptoms include:

- A timer keeps using the initial state.
- An event listener reads an old prop after navigation.
- A memoized callback submits old form data.
- Batched state updates only increment once.
- A fetch effect resolves with data for an old ID.

## 3. Official Mechanism

When React calls your component:

1. React reads the current hook state.
2. Your component function runs with fresh local bindings.
3. Any functions created during that run capture those bindings.
4. React commits the UI.
5. Effects from that render run later, still holding their captured bindings.

This means "latest value" and "captured value" are different ideas.

```tsx
function renderCounter(count: number) {
  return function log() {
    console.log(count);
  };
}

const logZero = renderCounter(0);
const logOne = renderCounter(1);

logZero(); // 0
logOne(); // 1
```

React components follow the same JavaScript rule. The difference is that React calls your component many times over the lifetime of the UI.

## 4. Mental Model

Think of hooks as render snapshot tools:

| Hook or callback | What it captures |
| --- | --- |
| Event handler | Values from the render that created the JSX handler |
| `useEffect` setup | Values from the render whose dependencies triggered the effect |
| Effect cleanup | Values from the previous effect setup's closure |
| `useMemo` calculation | Values used while calculating the memoized value |
| `useCallback` function | Values from the render when the callback was created |
| Functional updater | Receives latest queued state from React instead of relying on closure state |

> [!tip] Dependencies declare, not schedule
> The dependency array is not "when I want it to run." It is a declaration of which reactive values the closure depends on.

## 5. Real Frontend Example

### Problem: batched updates with closed-over state

```tsx
function QuantityPicker() {
  const [quantity, setQuantity] = React.useState(0);

  function addThreeBroken() {
    setQuantity(quantity + 1);
    setQuantity(quantity + 1);
    setQuantity(quantity + 1);
  }

  return <button onClick={addThreeBroken}>{quantity}</button>;
}
```

### Bug

> [!warning] Batched updates share one closure
> If `quantity` is `0`, all three updates enqueue `1`. The handler closes over `quantity = 0`, so each call calculates the same next value. The UI becomes `1`, not `3`.

### Fix

```tsx
function QuantityPicker() {
  const [quantity, setQuantity] = React.useState(0);

  function addThree() {
    setQuantity(prev => prev + 1);
    setQuantity(prev => prev + 1);
    setQuantity(prev => prev + 1);
  }

  return <button onClick={addThree}>{quantity}</button>;
}
```

The updater function does not need the render's `quantity`. React passes the latest queued state into each updater in order.

Expected result after one click from `0`: `3`.

## Real-World Use Cases

### Drag-to-reorder that captures the grabbed card

A board lets users drag cards to reorder them. The `pointerdown` handler installs `pointermove`/`pointerup` listeners that close over the grabbed card and the start position — here the creation-time snapshot is exactly what the gesture needs.

```tsx
function onPointerDown(card: Card, event: React.PointerEvent) {
  const startY = event.clientY;

  function onMove(e: PointerEvent) {
    previewReorder(card.id, e.clientY - startY); // closes over drag-start values
  }
  function onUp(e: PointerEvent) {
    commitReorder(card.id, e.clientY - startY);
    window.removeEventListener('pointermove', onMove);
    window.removeEventListener('pointerup', onUp);
  }

  window.addEventListener('pointermove', onMove);
  window.addEventListener('pointerup', onUp);
}
```

This works because the listeners capture the bindings of the `onPointerDown` call that created them — a drag gesture *wants* values frozen at drag start, so the closure is correct by design. See [[03 - Scope and Variables/05 - Closures|Closures]].

### Analytics payload after `setState` in the same handler

A checkout tracks the pre-discount total when a coupon is applied. The handler still reads this render's snapshot even after calling the setter — useful here, a trap if you expected the new value.

```tsx
function applyCoupon(coupon: Coupon) {
  setTotalCents(totalCents - coupon.discountCents);
  analytics.track('coupon_applied', {
    code: coupon.code,
    totalBefore: totalCents, // still the render snapshot — deliberately pre-discount
  });
}
```

> [!warning]
> If you need the *post*-discount value in the same handler, compute it in a local variable (`const next = totalCents - coupon.discountCents`). State never changes mid-handler; the setter only schedules a render.

### Retry button that resends the exact failed upload

A chat composer uploads attachments. When an upload fails, the retry action closes over the `File` object from the send attempt, so retry works even after the composer input was cleared.

```tsx
async function sendAttachment(file: File) {
  try {
    await uploadAttachment(conversationId, file);
  } catch {
    setFailed(prev => [
      ...prev,
      { id: crypto.randomUUID(), name: file.name, retry: () => sendAttachment(file) },
    ]);
  }
}
```

The `retry` closure preserves `file` because closures capture the creation-time environment — the same mechanism behind stale-closure bugs, used deliberately.

> [!warning]
> The closure also freezes `conversationId`. If the user can switch conversations before retrying, read the current conversation from a ref or store instead — see [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]].

## 6. Hook Closure Patterns

### Pattern A: include dependencies when the closure should react

```tsx
function UserPresence({ userId }: { userId: string }) {
  React.useEffect(() => {
    const unsubscribe = presence.subscribe(userId);

    return () => {
      unsubscribe();
    };
  }, [userId]);

  return null;
}
```

`userId` is a reactive value used by the effect. Including it means React cleans up the old subscription and creates a new one when `userId` changes.

### Pattern B: use functional updates when the next state depends on previous state

```tsx
function Notifications() {
  const [unread, setUnread] = React.useState(0);

  React.useEffect(() => {
    const unsubscribe = socket.on('notification', () => {
      // No dependency on unread is needed because React supplies the latest value.
      setUnread(prev => prev + 1);
    });

    return unsubscribe;
  }, []);

  return <span>{unread}</span>;
}
```

### Pattern C: use refs when a long-lived callback needs the latest value without resubscribing

```tsx
function AutosaveStatus({ draft }: { draft: Draft }) {
  const latestDraftRef = React.useRef(draft);

  React.useEffect(() => {
    latestDraftRef.current = draft;
  }, [draft]);

  React.useEffect(() => {
    const id = window.setInterval(() => {
      // Reads the latest draft intentionally.
      saveDraft(latestDraftRef.current);
    }, 5000);

    return () => window.clearInterval(id);
  }, []);

  return null;
}
```

> [!tip] Latest-value ref, used deliberately
> This pattern is appropriate when the subscription or timer should stay stable, but the callback needs current data. Use it deliberately; do not use refs to hide real dependencies.

## 7. Production Tradeoffs

- Dependencies are the default. If a closure reads a reactive value and should rerun when it changes, include it.
- Functional updates are best for state transitions based only on previous state.
- Refs are best for mutable latest values, timer IDs, DOM nodes, and imperative handles.
- `useCallback` preserves function identity, but the returned function can still be stale if its dependency list is wrong.
- `useMemo` caches a calculated value, but stale dependencies produce stale calculations.
- Avoid "one-time effect" thinking unless the effect truly does not depend on reactive values.

## 8. Interview Answer

Every render of a React function component creates a new closure. Hook callbacks and event handlers capture the props and state from the render that created them. This is why a timeout or interval can read an old value: the callback is not reading a live variable; it is reading the binding from an old render. The normal fixes are to include real dependencies so React creates a new closure, use a functional state update when the next state depends on previous state, or use a ref when a long-lived callback intentionally needs the latest value without recreating the subscription.

## 9. Mistakes to Avoid

| Mistake | Why it fails |
| --- | --- |
| `useCallback(fn, [])` while `fn` reads state | The callback keeps the initial state forever. |
| Omitting dependencies to stop rerenders | This hides a stale closure bug. Restructure instead. |
| Reading state after `setState` in the same handler | The handler still sees the current render snapshot. |
| Using refs for everything | Refs avoid rendering and dependency tracking; they can make UI state invisible. |
| Treating linter warnings as optional style | The hooks linter catches real closure bugs. |

## 10. Practice

### Q1. What is logged?

```tsx
function Demo() {
  const [count, setCount] = React.useState(0);

  React.useEffect(() => {
    const id = window.setTimeout(() => {
      console.log(count);
    }, 1000);

    return () => window.clearTimeout(id);
  }, []);

  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

If the user clicks three times before the timeout fires, it still logs `0`. The effect ran once on mount, and the timeout callback captured the mount render's `count`.

### Q2. Why is this dependency array valid?

```tsx
const increment = React.useCallback(() => {
  setCount(prev => prev + 1);
}, []);
```

It does not read `count`. It reads only `setCount`, and React state setters are stable. The functional updater receives the latest state.

### Q3. Which fix would you choose?

For a WebSocket subscription that should reconnect when `roomId` changes, include `roomId` in dependencies. For a stable interval that should always save the latest draft, use a ref to hold the latest draft and keep the interval stable.

## Related Notes

- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
