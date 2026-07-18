---
tags: [javascript, interview, senior-style-thinking-questions]
module: "15 - Interview Preparation"
priority: important
status: not-started
---

# Senior Style Thinking Questions

## Maturity Target

- Priority: #important
- Study time: 120-180 minutes
- Interview signal: can reason about tradeoffs, architecture, and debugging strategy without pretending there is only one answer.
- Production signal: can choose tools and patterns based on ownership, scale, runtime, and failure modes.
- Fast track: practice Q1, Q2, Q4, Q5, Q7, and Q9 aloud.

## Source Anchors

- [React docs: You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [Next.js docs: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [web.dev: Optimize long tasks](https://web.dev/articles/optimize-long-tasks)
- [Chrome DevTools: Memory problems](https://developer.chrome.com/docs/devtools/memory-problems)
- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)

## How To Answer Senior-Style Questions

Use this pattern:

1. Classify the problem.
2. Name the likely failure modes.
3. Pick a default approach.
4. Name alternatives and tradeoffs.
5. Explain how you would verify the decision.

A senior-style answer is not longer by default. It is better organized.

## Q1. Context, Zustand, Or TanStack Query?

### Model Answer

I would first classify the state.

- Server state belongs in a server-state tool or framework data layer. It is remote, cached, shared, can go stale, and needs refetching, retries, invalidation, and race handling. TanStack Query or framework server fetching is a good fit.
- Global client UI state can belong in Zustand when it changes often or many components need focused subscriptions, such as modals, selected rows, toasts, or wizard state.
- Context is best for low-frequency, subtree-wide values such as theme, locale, auth session summary, or feature flags.
- Local `useState` is best for state owned by one component or a small subtree.

### Real Bug

Putting a large frequently-changing object in Context can rerender every consumer on each update. A notification count changing every second should not rerender the entire application shell.

### Tradeoff

Context is built into React and simple. Zustand adds dependency and conventions but can reduce rerender blast radius. TanStack Query is excellent for server state but should not be used for purely local UI toggles.

### Verification

Use React Profiler to see rerender scope. Use network and cache tooling for server-state behavior.

Related: [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]], [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]

## Q2. How Would You Debug A Memory Leak?

### Model Answer

I would reproduce the growth first, then use Chrome DevTools Memory.

1. Find the action: route navigation, opening a modal, search, upload, or chart page.
2. Take a baseline heap snapshot.
3. Repeat the action several times.
4. Force garbage collection.
5. Take another snapshot and compare.
6. Inspect retainer paths for objects that should have been collected.

Common suspects:

- listeners without cleanup
- intervals without cleanup
- observers without disconnect
- large closures retained by callbacks
- unbounded Maps or arrays used as caches
- refs or globals keeping detached DOM nodes reachable

### Real Bug

A route adds `window.addEventListener('resize', handler)` in an effect without cleanup. After 20 navigations, 20 handlers remain. Each handler closes over page state, so memory and duplicate work grow.

### Fix

```tsx
React.useEffect(() => {
  function onResize() {
    setWidth(window.innerWidth);
  }

  window.addEventListener('resize', onResize);
  return () => window.removeEventListener('resize', onResize);
}, []);
```

### Verification

Repeat the heap snapshot workflow and confirm retained listener closures stop growing.

Related: [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]], [[13 - Performance and Memory/08 - Chrome DevTools Memory Profiling|Chrome DevTools Memory Profiling]]

## Q3. Bundle Grew 300 Percent. What Do You Do?

### Model Answer

I would avoid guessing and inspect the bundle.

1. Run a bundle analyzer for the current build.
2. Compare to the last known good build.
3. Check new dependencies and import paths.
4. Look for duplicate versions.
5. Look for CJS dependencies or side-effectful modules blocking tree shaking.
6. Check whether a new `'use client'` boundary pulled server/static code into the client graph.
7. Decide whether to replace, lazy-load, split, or move code server-side.

### Real Bug

A chart library imported in `app/layout.tsx` after `'use client'` can put a large chart bundle on every route, even if the chart appears on one page.

### Fix Options

- Move the interactive component lower.
- Use dynamic import for route-specific heavy UI.
- Replace the dependency.
- Import only needed submodules.
- Add bundle size checks to CI.

Related: [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]], [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]

## Q4. A `useEffect` Runs Too Often. Diagnose It.

### Model Answer

I would first identify which dependency changes. Effects run after render when dependencies compare different by `Object.is`. If an effect runs too often, one dependency is changing identity or the effect is doing work that should not be an effect.

Diagnostic checklist:

- Log each dependency and compare identity.
- Check inline objects, arrays, and functions.
- Check parent props recreated every render.
- Check whether the effect sets state and triggers its own dependency change.
- Check whether the logic can be derived during render or moved to an event handler.

### Real Bug

```tsx
const options = { includeDrafts: false };

React.useEffect(() => {
  loadPosts(options);
}, [options]);
```

`options` is a new object every render. Move it inside the effect or memoize it only if another consumer needs stable identity.

### Mature Fix

```tsx
React.useEffect(() => {
  loadPosts({ includeDrafts: false });
}, []);
```

Related: [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]

## Q5. Server Components Or Client Components?

### Model Answer

Default to Server Components for data loading, static UI, layout, markdown, and anything that does not need browser interactivity. Use Client Components for state, effects, refs, event handlers, browser APIs, and interactive islands.

### Tradeoffs

| Concern | Server Component | Client Component |
| --- | --- | --- |
| Client bundle | Does not ship component implementation | Ships module graph |
| Interactivity | No event handlers/hooks | Full React client behavior |
| Data access | Can access server resources | Must call API or receive props |
| Hydration | No hydration for that component | Hydration needed |
| Secrets | Safe server-side | Must not include secrets |

### Real Bug

Putting `'use client'` in a root layout for a dropdown can pull the whole shell into the browser bundle. Move the dropdown into a small Client Component.

Related: [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]

## Q6. Design A Type-Safe API Layer

### Model Answer

TypeScript alone does not validate runtime data. I would combine typed request functions with runtime validation at boundaries.

```ts
type User = {
  id: string;
  name: string;
  email: string;
};

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchJson<T>(
  url: string,
  validate: (value: unknown) => T,
  signal?: AbortSignal
): Promise<T> {
  const response = await fetch(url, { signal });

  if (!response.ok) {
    throw new ApiError(response.status, `HTTP ${response.status}`);
  }

  return validate(await response.json());
}
```

### Tradeoff

Runtime validation adds code and CPU cost, but catches API contract drift that TypeScript cannot see at runtime. For critical boundaries, it is worth it.

### Verification

Test success, HTTP failure, invalid payload, abort, timeout, and retry behavior.

Related: [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]

## Q7. Multiple Effects Have Race Conditions. Systemic Fix?

### Model Answer

I would audit every effect that starts async work. For each one:

- Does it depend on props or state that can change before resolution?
- Can the work be canceled?
- Does it guard success, error, and loading state?
- Is this really server state that should be owned by a data library or Server Component?

### Default Patterns

Use `AbortController` for fetch:

```tsx
React.useEffect(() => {
  const controller = new AbortController();

  fetch(url, { signal: controller.signal })
    .then(r => r.json())
    .then(data => {
      if (!controller.signal.aborted) setData(data);
    })
    .catch(error => {
      if (controller.signal.aborted) return;
      setError(error instanceof Error ? error : new Error(String(error)));
    });

  return () => controller.abort();
}, [url]);
```

Use an ignore flag for non-cancelable async work. Prefer a server-state library when the pattern repeats across the app.

Related: [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]], [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]

## Q8. How Would You Teach The Event Loop?

### Model Answer

I would start with constraints: JavaScript code runs one piece at a time. The browser handles timers, I/O, user events, and rendering as the host environment. When synchronous code finishes, microtasks run before the next task.

```js
console.log('sync 1');

setTimeout(() => console.log('task'), 0);

Promise.resolve().then(() => console.log('microtask'));

console.log('sync 2');

// sync 1, sync 2, microtask, task
```

### Misconceptions To Correct

- `setTimeout(fn, 0)` does not mean immediate.
- Promises do not create parallel JavaScript execution.
- Microtasks can starve rendering if you keep adding more.
- Browser rendering is part of the host event loop, not ECMAScript alone.

Related: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]

## Q9. Build Debounced, Cancellable Search

### Model Answer

A robust search needs both input debouncing and request cancellation.

```tsx
function useDebouncedValue<T>(value: T, delay: number) {
  const [debounced, setDebounced] = React.useState(value);

  React.useEffect(() => {
    const id = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(id);
  }, [value, delay]);

  return debounced;
}

function useSearch(query: string) {
  const debouncedQuery = useDebouncedValue(query, 300);
  const [results, setResults] = React.useState<Result[]>([]);

  React.useEffect(() => {
    if (debouncedQuery.length < 2) {
      setResults([]);
      return;
    }

    const controller = new AbortController();

    fetch(`/api/search?q=${encodeURIComponent(debouncedQuery)}`, {
      signal: controller.signal,
    })
      .then(r => r.json())
      .then(data => {
        if (!controller.signal.aborted) setResults(data);
      })
      .catch(error => {
        if (controller.signal.aborted) return;
        reportError(error);
      });

    return () => controller.abort();
  }, [debouncedQuery]);

  return results;
}
```

### Tradeoff

Manual hooks are fine for small apps. Repeated server-state patterns should move to a query library with cancellation, caching, deduping, and stale result handling.

Related: [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]

## Q10. What Performance Optimizations Have You Applied?

### Model Answer Shape

Do not list random APIs. Tell a measured story:

```text
Problem: route was slow after adding a chart dashboard.
Measurement: bundle analyzer showed the chart library in the initial bundle.
Change: moved chart into a route-level dynamic import and kept the page shell server-rendered.
Result: initial JavaScript dropped and the route became interactive sooner.
Tradeoff: chart now has its own loading state.
```

### Strong Examples

- Virtualized long lists instead of rendering thousands of rows.
- Memoized expensive transforms only after measuring.
- Split heavy editor/chart/map bundles.
- Moved server data fetching out of client effects.
- Replaced high-frequency Context state with selector-based store.
- Fixed event listener or timer leaks.
- Debounced or throttled user-driven API calls.

Related: [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]]

## Practice Routine

- [ ] For each question, answer with classification, default, tradeoff, verification.
- [ ] Add one example from your own project experience where possible.
- [ ] Practice saying "I would measure first" without sounding evasive.
- [ ] Turn Q1, Q3, Q5, and Q9 into 5-minute architecture answers.

## Related Notes

- [[15 - Interview Preparation/03 - Strong Mid Level Questions|Strong Mid Level Questions]]
- [[15 - Interview Preparation/06 - Mock Interview Guide|Mock Interview Guide]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[17 - Practical Frontend Scenarios/08 - Preventing Memory Leaks|Preventing Memory Leaks]]
- [[18 - Revision Plans/06 - 10 Practical Frontend Scenarios|10 Practical Frontend Scenarios]]
