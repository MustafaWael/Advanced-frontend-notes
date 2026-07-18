---
tags: [javascript, scenarios, react, fixing-stale-closure-in-react]
module: "17 - Practical Frontend Scenarios"
priority: must-know
status: not-started
---

# Fixing Stale Closure in React

## Maturity Target

- Priority: #must-know
- Study time: 70-90 minutes
- Interview signal: can explain why the callback sees old state and choose between deps, refs, and functional updates.
- Production signal: can fix timers, listeners, and async callbacks without disabling the hooks linter.
- Fast track: read the broken interval, then explain all three fixes aloud.

## Source Anchors

- [React docs: State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [React docs: Removing Effect Dependencies](https://react.dev/learn/removing-effect-dependencies)
- [MDN: Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)

## 1. Scenario

A component displays the current count correctly, but a timer, event listener, or delayed callback keeps reading the first value.

User symptom:

- The UI says `5`.
- The console, analytics event, autosave, or listener still sends `0`.
- The bug appears only after time passes or after a callback runs later.

This is a stale closure: a callback created during an old render runs later and reads old render bindings.

## 2. Broken Version

```tsx
function CounterLogger() {
  const [count, setCount] = React.useState(0);

  React.useEffect(() => {
    const id = window.setInterval(() => {
      // BUG: this callback was created during the first render.
      // It keeps reading count from that render.
      console.log('count:', count);
    }, 1000);

    return () => window.clearInterval(id);
  }, []);

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

## 3. Root Cause

React renders are snapshots. The effect runs after the first commit and creates an interval callback. That callback closes over the first render's `count`. Because the dependency array is empty, React never replaces the interval with a callback from later renders.

Important distinction:

- The UI updates because state changes trigger new renders.
- The interval callback does not update because it is the old function registered with `setInterval`.

## 4. Fix 1: Functional Update

Use this when the callback updates state based on previous state.

```tsx
function AutoCounter() {
  const [count, setCount] = React.useState(0);

  React.useEffect(() => {
    const id = window.setInterval(() => {
      // React supplies the latest queued state.
      // This does not read count from the closure.
      setCount(current => current + 1);
    }, 1000);

    return () => window.clearInterval(id);
  }, []);

  return <p>{count}</p>;
}
```

Why it works:

- The interval no longer reads `count`.
- The updater receives the latest state from React.
- The interval does not need to restart on every count change.

## 5. Fix 2: Include Dependencies

Use this when the external system should be recreated when the value changes.

```tsx
function CountLogger() {
  const [count, setCount] = React.useState(0);

  React.useEffect(() => {
    const id = window.setInterval(() => {
      console.log('fresh count:', count);
    }, 1000);

    // Cleanup removes the old interval before the new one is created.
    return () => window.clearInterval(id);
  }, [count]);

  return <button onClick={() => setCount(c => c + 1)}>+</button>;
}
```

Tradeoff:

- The value is fresh.
- The interval restarts every time `count` changes.
- That is fine for logging, but not fine if the timer cadence must remain stable.

## 6. Fix 3: Ref For Latest Value

Use this when the subscription/timer should stay stable but needs latest data.

```tsx
function StableLogger() {
  const [count, setCount] = React.useState(0);
  const latestCount = React.useRef(count);

  React.useEffect(() => {
    latestCount.current = count;
  }, [count]);

  React.useEffect(() => {
    const id = window.setInterval(() => {
      // The closure captures the stable ref object.
      // The current property is updated after each render.
      console.log('latest count:', latestCount.current);
    }, 1000);

    return () => window.clearInterval(id);
  }, []);

  return <button onClick={() => setCount(c => c + 1)}>+</button>;
}
```

Tradeoff:

- Stable timer, latest value.
- More mutable code.
- Do not use refs to hide dependencies when the effect truly should resubscribe.

## 7. Production Checklist

- [ ] Did I identify which render created the callback?
- [ ] Does the callback need latest value, or should the external subscription restart?
- [ ] Can a functional update remove the state dependency?
- [ ] If using a ref, is it synced whenever the value changes?
- [ ] Did I keep cleanup for timers and listeners?
- [ ] Did I keep the hooks linter enabled?

## 8. Interview Angle

Strong answer:

"A stale closure happens because every React render creates new bindings. The interval or listener was created in an older render, so it reads values from that render. I would choose the fix based on intent: functional update if I only need previous state, dependency array if the external system should be recreated, or a ref if the callback must stay stable but read the latest value."

## 9. Practice

1. Rewrite the broken interval using all three fixes.
2. Explain why `setCount(count + 1)` inside an interval often gets stuck.
3. Build a keyboard shortcut that always submits the latest query without re-registering the listener.
4. Explain why suppressing `exhaustive-deps` is risky here.

## Related Notes

- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]]
