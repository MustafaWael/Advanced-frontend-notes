---
tags: [javascript, scenarios, react, preventing-memory-leaks]
module: "17 - Practical Frontend Scenarios"
priority: important
status: not-started
---

# Preventing Memory Leaks

## Maturity Target

- Priority: #important
- Study time: 70-100 minutes
- Interview signal: can explain leaks through reachability, closures, and missing cleanup.
- Production signal: can prevent and verify leaks in React apps with DevTools.
- Fast track: sections 2, 4, 6, and 8.

## Source Anchors

- [MDN: Memory management](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Memory_management)
- [Chrome DevTools: Fix memory problems](https://developer.chrome.com/docs/devtools/memory-problems)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)

## 1. Scenario

After navigating around the app for 20 minutes, the tab slows down. Memory keeps increasing after returning to the same page. A callback fires twice, then five times, then ten times.

Leaks happen when objects are no longer needed but remain reachable from roots such as `window`, timers, event listener lists, pending promises, observers, or module-level caches.

## 2. Common Broken Patterns

### Timer Without Cleanup

```tsx
function Clock() {
  const [time, setTime] = React.useState(new Date());

  React.useEffect(() => {
    // BUG: interval keeps running after unmount.
    window.setInterval(() => setTime(new Date()), 1000);
  }, []);

  return <time>{time.toLocaleTimeString()}</time>;
}
```

### Listener Without Cleanup

```tsx
React.useEffect(() => {
  window.addEventListener('resize', () => {
    setWidth(window.innerWidth);
  });
}, []);
```

### Fetch After Unmount

```tsx
React.useEffect(() => {
  fetch('/api/user')
    .then(r => r.json())
    .then(setUser);
}, []);
```

## 3. Root Cause

The garbage collector can only collect unreachable objects. A timer or event listener registered with the browser keeps its callback reachable. The callback can keep a closure reachable. That closure can retain component state, props, DOM nodes, and large data.

React unmounting a component does not automatically remove resources you registered with external systems.

## 4. Fix Timers And Listeners

```tsx
function Clock() {
  const [time, setTime] = React.useState(new Date());

  React.useEffect(() => {
    const id = window.setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => {
      window.clearInterval(id);
    };
  }, []);

  return <time>{time.toLocaleTimeString()}</time>;
}
```

```tsx
function WindowWidth() {
  const [width, setWidth] = React.useState(0);

  React.useEffect(() => {
    function updateWidth() {
      setWidth(window.innerWidth);
    }

    updateWidth();
    window.addEventListener('resize', updateWidth);

    return () => {
      window.removeEventListener('resize', updateWidth);
    };
  }, []);

  return <span>{width}</span>;
}
```

## 5. Fix Async Work

```tsx
function UserPanel({ userId }: { userId: string }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [error, setError] = React.useState<Error | null>(null);

  React.useEffect(() => {
    const controller = new AbortController();

    fetch(`/api/users/${userId}`, { signal: controller.signal })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json() as Promise<User>;
      })
      .then(setUser)
      .catch(reason => {
        if (controller.signal.aborted) return;
        setError(reason instanceof Error ? reason : new Error(String(reason)));
      });

    return () => {
      controller.abort();
    };
  }, [userId]);

  if (error) return <ErrorMessage error={error} />;
  return <UserView user={user} />;
}
```

## 6. Avoid Retaining Large Objects

```tsx
function Dashboard({ rows }: { rows: Row[] }) {
  React.useEffect(() => {
    const expensiveSummary = buildSummary(rows);
    const count = expensiveSummary.count;

    const id = window.setInterval(() => {
      // Capture only the primitive needed by the interval.
      console.log('row count:', count);
    }, 5000);

    return () => window.clearInterval(id);
  }, [rows]);

  return null;
}
```

If the interval captured `expensiveSummary`, that entire object would remain reachable as long as the interval did.

## 7. DevTools Verification

Use Chrome DevTools Memory:

1. Take a heap snapshot.
2. Perform the suspected leak action several times.
3. Force garbage collection.
4. Take another heap snapshot.
5. Compare snapshots.
6. Inspect retained objects and retainer paths.
7. Verify the reference chain points to a listener, timer, cache, closure, or detached DOM node.

## 8. Production Checklist

- [ ] Every effect that subscribes also unsubscribes.
- [ ] Every timer is cleared.
- [ ] Every observer is disconnected.
- [ ] Fetches are aborted or ignored on cleanup.
- [ ] Listener cleanup uses the same function reference.
- [ ] Refs to detached DOM nodes are nulled if manually managed.
- [ ] Caches have eviction or use `WeakMap` when appropriate.
- [ ] DevTools snapshot comparison verifies the fix.

## 9. Interview Angle

Strong answer:

"A memory leak means something logically dead is still reachable. In React, common roots are timers, listeners, observers, pending async callbacks, and global caches. The fix is to treat effects as acquire/release: whatever I register in setup, I release in cleanup. I verify with heap snapshots and retainer paths."

## Related Notes

- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[17 - Practical Frontend Scenarios/06 - Cleaning Event Listeners|Cleaning Event Listeners]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
