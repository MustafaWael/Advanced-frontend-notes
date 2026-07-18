---
tags: [javascript, react, nextjs, react-and-next-checklist]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# React and Next Checklist

Use this file as an active review. Do not mark an item complete because the words feel familiar. Mark it complete when you can explain the mechanism, write the bug, fix it, and name the production tradeoff.

## Source Anchors

- [React docs: State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [React docs: Removing Effect Dependencies](https://react.dev/learn/removing-effect-dependencies)
- [React docs: memo](https://react.dev/reference/react/memo)
- [Next.js docs: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [Next.js docs: Hydration error](https://nextjs.org/docs/messages/react-hydration-error)
- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)

## Module Outcome

By the end of this module, you should be able to answer React and Next.js JavaScript questions at a strong mid-level standard:

- Explain render snapshots, closures, dependencies, identity, immutability, async races, aborting, server/client boundaries, and hydration.
- Debug real UI bugs caused by stale values, wrong references, mutation, or mismatched server/client output.
- Choose a practical fix and explain the tradeoff instead of applying a memorized rule.

## Dependency Order

Study in this order:

1. [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]
2. [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
3. [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
4. [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
5. [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
6. [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
7. [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
8. [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
9. [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
10. [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]

## Fast Track

If you have only one hour:

1. Read sections 1, 3, 5, and Interview Answer in each note.
2. Write the stale interval fix from memory.
3. Write the async race ignore-flag fix from memory.
4. Explain why an inline object breaks a dependency array.
5. Explain when code belongs in a Next.js Client Component.
6. Fix one hydration mismatch involving `localStorage`.

If you have one day:

1. Read all notes.
2. Run every practice snippet mentally.
3. Build a tiny Next.js page with one Server Component, one Client Component, one fetch, one aborting effect, and one hydration-safe browser read.
4. Record yourself answering the interview prompts below in under two minutes each.

## Must-Know Checklist

- [ ] I can explain that React components are JavaScript functions called during render.
- [ ] I can define render, commit, effect setup, and effect cleanup.
- [ ] I can explain state as a snapshot, not a mutable local variable.
- [ ] I can explain why reading state immediately after `setState` reads the current render's value.
- [ ] I can explain why every render creates new closures.
- [ ] I can identify a stale closure in a timer, listener, promise callback, effect, memo, or callback.
- [ ] I can fix stale closures with dependencies, functional updates, or refs depending on intent.
- [ ] I can explain what dependency arrays declare.
- [ ] I can explain how React compares dependencies with `Object.is`.
- [ ] I can remove dependencies by restructuring code, not by deleting them.
- [ ] I can explain why object, array, and function literals are new references every render.
- [ ] I can explain why `React.memo` fails when props are always new references.
- [ ] I can update arrays immutably: add, remove, replace, sort, reverse, and move.
- [ ] I can update nested objects immutably by copying each changed level.
- [ ] I can explain why mutating state can prevent rerenders.
- [ ] I can describe an async effect race and reproduce it with a slow request.
- [ ] I can write an ignore-flag fix and guard success, error, and loading updates.
- [ ] I can write an `AbortController` effect and ignore expected aborts.
- [ ] I can explain why `useEffect(async () => ...)` is wrong.
- [ ] I can explain Server Components and Client Components in Next.js App Router.
- [ ] I can explain what `'use client'` does to a module graph.
- [ ] I can explain serializable props across the server/client boundary.
- [ ] I can explain hydration and common mismatch causes.
- [ ] I can fix browser-only render reads using `useEffect`, cookies, or dynamic import.

## Important Checklist

- [ ] I can decide between `useMemo`, `useCallback`, moving values inside effects, and module-level constants.
- [ ] I can explain when refs are appropriate and when they hide data flow.
- [ ] I can explain why context provider values often need stable identity.
- [ ] I can avoid showing abort errors as user-facing failures.
- [ ] I can explain why `finally` must be guarded in async effects.
- [ ] I can describe how Strict Mode exposes missing cleanup in development.
- [ ] I can choose Server Component fetching vs Client Component fetching vs a data library.
- [ ] I can keep `'use client'` boundaries low to reduce bundle size.
- [ ] I can explain why invalid HTML nesting can cause hydration errors.
- [ ] I can use cookies for server-known user preferences like theme or locale.

## Deep-Dive Checklist

- [ ] I can compare ignore flag vs `AbortController`.
- [ ] I can compare state vs ref vs module variable.
- [ ] I can explain how closure lifetimes relate to memory retention.
- [ ] I can debug a rerender caused by unstable object identity.
- [ ] I can describe when custom `React.memo` comparison is risky.
- [ ] I can explain why deep equality is not React's default comparison strategy.
- [ ] I can describe how Next.js module graphs separate server and client code.
- [ ] I can explain why a Client Component can still be prerendered and hydrated on first load.
- [ ] I can identify when `dynamic(..., { ssr: false })` is appropriate.

## Glossary

| Term | Plain meaning | Technical meaning | Why it matters |
| --- | --- | --- | --- |
| Render snapshot | Values for one UI calculation | Props, state, and local bindings from one component invocation | Handlers and effects read from the render that created them |
| Closure per render | Function remembers one render | Callback closes over that render's lexical environment | Explains stale timers, listeners, and callbacks |
| Stale closure | Old callback reads old data | Long-lived function uses bindings from an old render | Causes wrong submissions, old IDs, and stuck intervals |
| Dependency array | Values a hook depends on | React compares each element using `Object.is` | Controls effect cleanup/setup and memo recalculation |
| Referential equality | Same object identity | Objects/functions equal only when same reference | Explains memoization and effect loops |
| Structural sharing | Copy changed path only | New references for changed containers, reused unchanged branches | Enables immutable updates efficiently |
| Functional update | State update from previous state | `setState(prev => next)` receives latest queued state | Avoids stale closure for state transitions |
| Ref | Persistent mutable box | Stable object with mutable `.current` | Stores DOM nodes, timer IDs, latest values without rerender |
| Race condition | Timing decides wrong winner | Older async result updates after newer result | Shows stale data in real networks |
| AbortController | Cancellation controller | Provides signal and aborts signal-aware APIs | Cancels fetches during cleanup |
| AbortSignal | Cancellation signal | Passed to `fetch` or signal-aware API | Fetch rejects when aborted |
| Server Component | Server-rendered component | Default App Router component running on server | Keeps data fetching and secrets off client |
| Client Component | Interactive component | Module marked with `'use client'` | Enables hooks, events, browser APIs |
| Hydration | Browser takes over server HTML | React attaches event handlers to existing HTML | Initial client output must match server output |
| Hydration mismatch | Server/client output differs | Client first render does not match server HTML | Causes warnings, flashes, and client fallback |

## Code Drills

### Drill 1: Stale interval

```tsx
// Problem: count is captured from the first render.
React.useEffect(() => {
  const id = window.setInterval(() => {
    setCount(count + 1);
  }, 1000);

  return () => window.clearInterval(id);
}, []);
```

Fix:

```tsx
React.useEffect(() => {
  const id = window.setInterval(() => {
    setCount(prev => prev + 1);
  }, 1000);

  return () => window.clearInterval(id);
}, []);
```

Interview angle: The fixed version no longer reads `count`, so it does not need `count` in dependencies.

### Drill 2: Dependency object loop

```tsx
const options = { retry: 2 };

React.useEffect(() => {
  loadUser(userId, options);
}, [userId, options]);
```

Fix:

```tsx
React.useEffect(() => {
  const options = { retry: 2 };
  loadUser(userId, options);
}, [userId]);
```

Interview angle: The object is only needed by the effect, so moving it inside removes an unstable render-time dependency.

### Drill 3: Immutable update

```tsx
// Problem: mutates array and object inside state.
task.done = true;
setTasks(tasks);
```

Fix:

```tsx
setTasks(prev =>
  prev.map(task =>
    task.id === id ? { ...task, done: true } : task
  )
);
```

Interview angle: New array, new changed task object, unchanged tasks reused.

### Drill 4: Async race

```tsx
React.useEffect(() => {
  fetch(`/api/users/${userId}`)
    .then(r => r.json())
    .then(setUser);
}, [userId]);
```

Fix:

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

Interview angle: Cleanup marks the old effect invocation as stale before the next one runs.

### Drill 5: AbortController

```tsx
React.useEffect(() => {
  const controller = new AbortController();

  fetch(`/api/users/${userId}`, { signal: controller.signal })
    .then(r => r.json())
    .then(setUser)
    .catch(reason => {
      if (controller.signal.aborted) return;
      setError(reason instanceof Error ? reason : new Error(String(reason)));
    });

  return () => controller.abort();
}, [userId]);
```

Interview angle: One controller per effect invocation; abort is expected cleanup.

### Drill 6: Hydration mismatch

```tsx
// Problem: localStorage is browser-only and can differ from server output.
const theme = localStorage.getItem('theme') ?? 'light';
```

Fix:

```tsx
const [theme, setTheme] = React.useState<'light' | 'dark'>('light');

React.useEffect(() => {
  const saved = localStorage.getItem('theme');
  if (saved === 'light' || saved === 'dark') {
    setTheme(saved);
  }
}, []);
```

Interview angle: Server and first client render agree; browser-only value updates after hydration.

## Interview Prompts

### 1. What does "state is a snapshot" mean?

Strong answer: It means a render receives fixed state values. Calling a setter does not mutate the current variable; it schedules another render. Handlers and effects created during a render close over that render's values.

### 2. What is a stale closure?

Strong answer: A callback created in an old render runs later and reads old props or state from its closure. It happens in timers, listeners, promises, effects, and memoized callbacks. Fix by adding dependencies, using a functional updater, or using a ref when a stable callback needs latest data.

### 3. How do dependency arrays work?

Strong answer: They list reactive values used by the hook callback or calculation. React compares each dependency with the previous one using `Object.is`. For effects, changed dependencies trigger old cleanup and new setup.

### 4. Why does mutating state break React?

Strong answer: Mutation keeps the same reference. React uses reference equality to detect state changes, so passing the same mutated object can bail out. It also breaks the snapshot model and memoization assumptions.

### 5. What is a race condition in an async effect?

Strong answer: Multiple requests are in flight, and an older one finishes after a newer one and updates state with stale data. Fix with cleanup: ignore outdated results or abort the old request.

### 6. What does `'use client'` do?

Strong answer: It marks a module as a Client Component boundary. That module and its imports become part of the client graph, enabling hooks and browser APIs. It should be placed as low as practical to avoid shipping static/server code to the browser.

### 7. What causes hydration mismatch?

Strong answer: The first client render produces different output than the server HTML. Common causes are time, randomness, browser-only APIs, localStorage, invalid HTML, or different locale data. Fix by making initial output deterministic or moving the value to the server through cookies.

## Practical Scenarios

### Scenario 1: Debounced search shows old results

Likely causes:

- stale closure in the debounced callback
- async race between searches
- missing cleanup for timeout or request

Good fix:

- clear the debounce timer
- include real dependencies
- abort or ignore outdated requests

### Scenario 2: Memoized table still rerenders

Likely causes:

- inline columns array
- inline row action callback
- context value recreated every render

Good fix:

- move constants outside the component
- use `useMemo` for derived columns
- use `useCallback` for handlers only if identity matters

### Scenario 3: Theme flashes from light to dark

Likely causes:

- localStorage read after hydration
- server does not know the saved theme

Good fix:

- store theme in a cookie and read it on the server
- fallback to client effect only when server cannot know the value

## Final Self-Test

Before moving to the next module, answer without notes:

1. Why does `setCount(count + 1)` three times often produce `1`, not `3`?
2. What does `Object.is({}, {})` return, and why does React care?
3. Why is `useEffect(async () => {}, [])` wrong?
4. How does an ignore flag prevent stale async updates?
5. When should you use `AbortController` instead of only an ignore flag?
6. Why should `'use client'` be placed low in the tree?
7. What exact mismatch happens when render reads `localStorage`?
8. Which fix would you choose for a browser-only chart library in Next.js?

## Related Notes

- [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]
- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]
- [[15 - Interview Preparation/03 - Strong Mid Level Questions|Strong Mid Level Questions]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
