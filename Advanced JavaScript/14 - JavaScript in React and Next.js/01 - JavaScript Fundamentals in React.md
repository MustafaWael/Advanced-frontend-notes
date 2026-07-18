---
tags: [javascript, react, nextjs, javascript-fundamentals-in-react]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# JavaScript Fundamentals in React

## Maturity Target

- Priority: #must-know
- Study time: 75-100 minutes
- Interview signal: can explain React behavior as JavaScript plus framework rules, not as magic.
- Production signal: can predict render snapshots, state updates, identity, effects, and server/client execution.
- Fast track: read sections 1, 3, 5, 7, then solve the practice without notes.

## Source Anchors

- [React docs: State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [React docs: Render and Commit](https://react.dev/learn/render-and-commit)
- [React docs: Queueing a Series of State Updates](https://react.dev/learn/queueing-a-series-of-state-updates)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [React docs: Components and Hooks must be pure](https://react.dev/reference/rules/components-and-hooks-must-be-pure)
- [Next.js docs: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)

## 1. Concept

React components are JavaScript functions. A render is React calling those functions to calculate a UI snapshot. During that call, ordinary JavaScript rules apply: local variables are recreated, closures capture lexical bindings, object and function literals get new references, and thrown errors or returned values behave like normal JavaScript.

The important extra layer is React's contract:

- Component render logic should be pure: same props, state, and context should produce the same JSX.
- State does not mutate the current render's variable. A state update requests a future render.
- Effects run after commit on the client; they do not run during server rendering.
- Next.js can execute JavaScript in different places: server, browser, edge runtime, and build/prerender phases.

This module is the bridge between "I know JavaScript" and "I can debug real React and Next.js behavior."

## 2. Why It Matters

Mid-level frontend bugs often look like React bugs, but the root cause is JavaScript:

- A callback reads an old value because it closed over an older render.
- A memoized child re-renders because the parent passes a new object reference every render.
- A state update fails because an array was mutated and returned with the same reference.
- A fetch result overwrites newer data because async work resolved out of order.
- A Next.js page hydrates with different server and client output because render used `Date.now()`, `Math.random()`, `window`, or `localStorage`.

Strong engineers separate layers instead of guessing:

| Layer | What to ask |
| --- | --- |
| ECMAScript | What do variables, closures, equality, promises, and modules do? |
| Browser or Node | What APIs exist here: DOM, Fetch, timers, storage, filesystem, cookies? |
| React | When does render, commit, effect setup, and effect cleanup happen? |
| Next.js | Is this code in a Server Component, Client Component, route handler, Server Action, or bundled client module? |
| Application | What user timing, network latency, or data ownership makes the bug visible? |

## 3. Official Mechanism

React rendering has three practical phases:

1. Trigger: state update, parent render, route change, or store/context update asks React to render.
2. Render: React calls component functions to calculate the next UI tree.
3. Commit: React applies the minimal DOM changes and then runs effects that need to synchronize with external systems.

State is stored by React, not inside your local variable. On each render, React gives your component a snapshot of the state value for that render. The returned JSX includes event handlers created during that render, so handlers read the props and state from the render that created them.

```tsx
function Counter() {
  const [count, setCount] = React.useState(0);

  function logLater() {
    setTimeout(() => {
      // This reads the count from the render that created logLater.
      console.log(count);
    }, 1000);
  }

  return (
    <>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <button onClick={logLater}>Log later</button>
    </>
  );
}
```

> [!warning] Timeout reads the old snapshot
> If the user clicks "Log later" at `count = 0`, then increments to `3`, the timeout still logs `0`. That is not React being stale by accident. It is JavaScript closure behavior plus React's render snapshot model.

## 4. Mental Model

Treat each render like a frozen frame:

- Props and state values are fixed for that render.
- Functions created during that render close over that frame.
- JSX describes the UI for that frame.
- Effects from that frame synchronize after the frame is committed.
- Cleanup from the previous frame runs before the next matching effect setup.

The mature habit is to ask: "What is the lifetime of this value?"

| Value | Lifetime question |
| --- | --- |
| Local variable | Does it reset every render? |
| State | Does changing it require a new reference? |
| Ref | Is it intentionally mutable across renders? |
| Callback | Which render did it close over? |
| Object or array literal | Is this a new reference every render? |
| Effect | What external system does it synchronize with, and how is it cleaned up? |

## 5. Real Frontend Example

### Problem: render-local variables are not state

```tsx
function CartButton() {
  const [items, setItems] = React.useState<string[]>([]);
  let clickCount = 0;

  function addItem() {
    clickCount += 1;
    setItems(prev => [...prev, `item-${clickCount}`]);
  }

  return (
    <button onClick={addItem}>
      Add item ({items.length})
    </button>
  );
}
```

### Bug

> [!warning] Render-local variables reset
> `clickCount` resets to `0` on every render. The first click sets `item-1`, React renders again, then the next render recreates `clickCount` as `0`. You keep adding `item-1`.

### Fix

```tsx
function CartButton() {
  const [items, setItems] = React.useState<string[]>([]);

  function addItem() {
    setItems(prev => {
      const nextNumber = prev.length + 1;
      return [...prev, `item-${nextNumber}`];
    });
  }

  return (
    <button onClick={addItem}>
      Add item ({items.length})
    </button>
  );
}
```

The fixed version derives the next item number from the latest state that React provides to the functional updater. It does not rely on a local variable surviving renders.

### Why this fix works

> [!tip] Functional updaters stay current
> `setItems(prev => ...)` receives the current queued state value at update time. It avoids closing over a possibly old `items` value and works correctly with batched updates.

## Real-World Use Cases

### Undo toast that restores exactly what was deleted

An inbox lets users delete a thread and offers a 5-second "Undo" toast. The snapshot model is the feature here: the handler closes over the exact item that was removed, so undo can restore it verbatim.

```tsx
function handleDelete(thread: EmailThread) {
  setThreads(prev => prev.filter(t => t.id !== thread.id));

  showToast({
    message: `Deleted "${thread.subject}"`,
    // Closes over the removed thread from this render — a snapshot on purpose.
    action: () => setThreads(prev => [thread, ...prev]),
  });
}
```

This works because functions created during a render capture that render's bindings — the same mechanism behind stale-closure bugs, used deliberately. The functional updater ensures the restore applies to whatever the list looks like 5 seconds later. See [[03 - Scope and Variables/05 - Closures|Closures]].

### Impure render caught by Strict Mode double-rendering

An experiment banner tracks exposure by writing to a module-level array during render. It "works" until Strict Mode double-invokes render in development and the server renders it once more — exposures get double-counted or fire on the server where `analytics` does not exist.

```tsx
const seenExperiments: string[] = [];

function ExperimentBanner({ experimentId }: { experimentId: string }) {
  if (!seenExperiments.includes(experimentId)) {
    seenExperiments.push(experimentId); // side effect during render
    analytics.track('exposure', { experimentId });
  }
  return <Banner id={experimentId} />;
}
```

This fails because render must be pure: React is free to call the component function any number of times, on either runtime, before committing. Move the tracking into `useEffect` keyed on `experimentId`.

> [!tip] Strict Mode is a purity fuzzer
> Double-invoked renders do not break pure components. If double-rendering changes behavior, the render has a hidden side effect — fix the code, not the mode.

### Scroll progress bar without a re-render storm

A blog shows a reading-progress bar. Scroll fires dozens of times per frame-budget, so the pending animation-frame ID lives in a ref (mutable, persists across renders, triggers nothing), while only the displayed percentage is state.

```tsx
function ReadingProgress() {
  const frame = React.useRef(0);
  const [percent, setPercent] = React.useState(0);

  React.useEffect(() => {
    function onScroll() {
      cancelAnimationFrame(frame.current);
      frame.current = requestAnimationFrame(() => {
        const max = document.body.scrollHeight - window.innerHeight;
        setPercent(Math.round((window.scrollY / max) * 100));
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return <div className="progress" style={{ width: `${percent}%` }} />;
}
```

This is the "what is the lifetime of this value?" table applied: the frame ID must survive renders but should never cause one (ref); the percentage drives the UI (state). See [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]].

## 6. Common React JavaScript Traps

### Trap 1: expecting state to change immediately

```tsx
function SearchBox() {
  const [query, setQuery] = React.useState('');

  function handleChange(next: string) {
    setQuery(next);
    console.log(query); // Logs the query from the current render, not next.
  }
}
```

`setQuery(next)` schedules a render. It does not rewrite `query` inside the currently running handler.

### Trap 2: side effects during render

```tsx
function ProductPage({ productId }: { productId: string }) {
  // BUG: this runs during render. It can run multiple times and can run on the server.
  analytics.track('view_product', { productId });

  return <ProductDetails id={productId} />;
}
```

Fix it by moving synchronization to an effect in a Client Component, or by logging server-side events in a server-only path where repeated renders are acceptable and deduped.

```tsx
function ProductPageView({ productId }: { productId: string }) {
  React.useEffect(() => {
    analytics.track('view_product', { productId });
  }, [productId]);

  return <ProductDetails id={productId} />;
}
```

### Trap 3: assuming JSX is HTML

> [!warning] JSX is not the DOM
> JSX is syntax that becomes React element objects. Those objects describe what React should render. They are not DOM nodes yet, and reading DOM properties during render is usually a sign that browser-only code belongs in an effect or event handler.

## 7. Production Tradeoffs

- Use state for data that should trigger a render.
- Use refs for mutable values that must persist but should not trigger a render, such as timer IDs, latest callback references, or DOM nodes.
- Keep render pure. Put subscriptions, timers, network synchronization, DOM reads/writes, and analytics in effects or event handlers.
- Do not add `useMemo` or `useCallback` just because something is a function or object. Add them when identity stability matters for an effect dependency, a memoized child, a context value, or an expensive calculation.
- In Next.js, decide early whether code belongs on the server or client. Browser APIs and hooks require a Client Component; data fetching with secrets usually belongs in a Server Component or route handler.

## 8. Interview Answer

React function components are ordinary JavaScript functions, but React calls them under a render/commit model. Each render receives a snapshot of state and props. Functions created during that render close over that snapshot, so event handlers and effects read the values from the render that created them. Calling a state setter schedules a future render; it does not mutate the current variable. Effects run after commit on the client and should synchronize with external systems. In Next.js, you also need to know where the JavaScript runs: Server Components run on the server by default, while Client Components marked with `'use client'` can use hooks and browser APIs and hydrate in the browser.

## 9. Mistakes to Avoid

| Mistake | Better reasoning |
| --- | --- |
| "React variables update immediately after setState" | State setters request a later render. Current render variables stay fixed. |
| "A local variable can store component memory" | Local variables reset when the component function is called again. Use state or refs. |
| "Effects are just lifecycle methods" | Effects synchronize with external systems after commit and have cleanup semantics. |
| "JSX is DOM" | JSX creates React elements. DOM nodes exist after commit. |
| "Client Component means no server work" | In Next.js, Client Components are prerendered into HTML for the first load, then hydrated. |
| "Memoization fixes logic bugs" | Memoization is a performance tool. Fix stale closures, mutation, and ownership first. |

## 10. Practice

### Q1. What is logged?

```tsx
function Demo() {
  const [count, setCount] = React.useState(0);

  function handleClick() {
    setCount(count + 1);
    setCount(count + 1);
    console.log(count);
  }

  return <button onClick={handleClick}>{count}</button>;
}
```

First click logs `0`, and the rendered count becomes `1`, not `2`. Both `setCount(count + 1)` calls use the same closure value, `count = 0`. The fix for queued increments is `setCount(prev => prev + 1)` twice.

### Q2. Where should this code run?

```tsx
const theme = localStorage.getItem('theme');
```

It should not run during server rendering. In a React app with SSR or Next.js, read `localStorage` in a Client Component effect or initialize from a cookie in a Server Component so the server and first client render agree.

### Q3. Why can a component render without the DOM changing?

React can call component functions to calculate the next tree. During commit, it only changes DOM nodes whose rendered output differs. Rendering is calculation; committing is applying changes.

## Related Notes

- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[21 - React Internals and Patterns/14 - Why React Exists|Why React Exists]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
