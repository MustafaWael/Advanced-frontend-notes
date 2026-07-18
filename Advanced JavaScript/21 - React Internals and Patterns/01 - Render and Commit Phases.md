---
tags: [react, internals, rendering]
module: "21 - React Internals and Patterns"
priority: must-know
status: not-started
aliases: [Render Phase, Commit Phase]
---

# Render and Commit Phases

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can define what a "render" actually is (calling the function to produce elements), separate it from commit (mutating the DOM), and explain why render functions must be pure.
- Production signal: you stop conflating "re-render" with "DOM update" and can reason about why a component re-rendering isn't automatically a performance problem.
- Dependencies: [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]], [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]

## Source Anchors

- [react.dev - Render and Commit](https://react.dev/learn/render-and-commit)
- [react.dev - Keeping Components Pure](https://react.dev/learn/keeping-components-pure)
- [react.dev - State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [react.dev - Preserving and Resetting State](https://react.dev/learn/preserving-and-resetting-state)

## 1. Concept

A "render" in React is not a screen update. It is **React calling your component function** to get a description of the UI (an element tree). React does this in two separate stages:

1. **Render phase**: call components, build the new element tree, diff it against the previous one ([[21 - React Internals and Patterns/02 - Reconciliation and Keys|reconciliation]]). Pure computation — no DOM touched. Can be paused, aborted, or restarted ([[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber]]).
2. **Commit phase**: apply the computed changes to the actual DOM in one synchronous, uninterruptible burst, then run layout effects and (later) passive effects.

The browser then paints ([[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|render pipeline]]).

> [!warning] "Re-render" ≠ "DOM update"
> A component can re-render (its function runs again) and produce an *identical* element tree — React commits nothing to the DOM. Beginners chase "stop re-renders"; the real cost hierarchy is: cheap render + no commit (fine) < expensive render (fix with memo/derivation) < unnecessary commit (rare). Profile before optimizing renders.

## 2. Why It Matters

- Every React performance and correctness discussion assumes this split. "Why did my component render but the DOM didn't change?" and "why must render be pure?" are the same question from two sides.
- Concurrent features ([[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense/transitions]]) only make sense once you know the render phase is interruptible and the commit phase is not.

## 3. Why Render Must Be Pure

Because the render phase can run multiple times, be thrown away, or run in the background before ever committing, your component function must be a **pure function of its props, state, and context**: same inputs → same JSX, and **no side effects during render**.

```jsx
function Profile({ user }) {
  // ❌ side effect during render — runs on aborted renders too, and in StrictMode twice
  logView(user.id);
  cache[user.id] = user;         // ❌ mutating external state during render
  return <h1>{user.name}</h1>;
}
```

The fix is to move effects out of render: event handlers (user-caused) or `useEffect` (synchronization after commit). React 18+ StrictMode deliberately double-invokes render (and mount effects) in development precisely to surface impure renders — the "why does this run twice?" confusion is StrictMode doing its job.

```jsx
function Profile({ user }) {
  useEffect(() => { logView(user.id); }, [user.id]); // ✅ after commit, deduped by deps
  return <h1>{user.name}</h1>;
}
```

## 4. Mental Model: State as a Snapshot

Each render captures a **snapshot**: props, state, and every value/handler computed from them are frozen for that render ([[03 - Scope and Variables/05 - Closures|closures]] over render-scoped bindings). This is why:

```jsx
function Counter() {
  const [n, setN] = useState(0);
  function handleClick() {
    setN(n + 1);
    setN(n + 1);
    setN(n + 1);   // n is 0 in THIS snapshot → all three compute 1
  }
  return <button onClick={handleClick}>{n}</button>; // increments by 1, not 3
}
```

`n` isn't a live variable; it's the value from the render that created this `handleClick`. The fix — functional updaters `setN(prev => prev + 1)` — is covered in [[21 - React Internals and Patterns/04 - State Batching and Updater Queues|State Batching]].

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — reading "current" DOM state during render:

```jsx
function AutoScroll({ messages }) {
  const listRef = useRef(null);
  // ❌ reading/writing the DOM during render: DOM reflects the PREVIOUS commit,
  // and this runs during aborted/background renders too.
  if (listRef.current) {
    listRef.current.scrollTop = listRef.current.scrollHeight;
  }
  return <div ref={listRef}>{messages.map(m => <p key={m.id}>{m.text}</p>)}</div>;
}
```

Trace: during the render phase the ref points to the DOM from the *last* commit (new messages not applied yet), so it scrolls to the old bottom; under concurrent rendering this render might be discarded entirely, yet it already mutated the DOM.

Production-safe fix — do DOM work in the commit-adjacent phase:

```jsx
function AutoScroll({ messages }) {
  const listRef = useRef(null);
  useLayoutEffect(() => {
    const el = listRef.current;
    el.scrollTop = el.scrollHeight;   // runs AFTER commit, BEFORE paint → no flicker
  }, [messages]);
  return <div ref={listRef}>{messages.map(m => <p key={m.id}>{m.text}</p>)}</div>;
}
```

Tradeoff: `useLayoutEffect` runs synchronously before paint, so heavy work there blocks the frame — it's the right tool for measure/scroll (avoids visible flicker) but the wrong one for non-visual work, which belongs in `useEffect` ([[21 - React Internals and Patterns/07 - useLayoutEffect useInsertionEffect and Effect Timing|Effect Timing]]).

## Real-World Use Cases

### Hydration mismatch from non-deterministic render inputs

A Next.js product page shows "deal ends in 2h 13m" by calling `new Date()` during render. The server renders one time, the client hydrates milliseconds later with a different one — React logs a hydration mismatch and may re-render the subtree.

```jsx
function DealCountdown({ endsAt }) {
  const remaining = endsAt - Date.now();   // ❌ different output per call — render isn't pure
  return <span>ends in {formatDuration(remaining)}</span>;
}

// ✅ deterministic render; the clock lives in an effect, after commit
function DealCountdown({ endsAt }) {
  const [now, setNow] = useState(null);            // null on server AND first client render
  useEffect(() => {
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  return <span>{now ? `ends in ${formatDuration(endsAt - now)}` : "…"}</span>;
}
```

Fails because render must be a pure function of props/state — `Date.now()` makes two runs of the same render disagree, and SSR + hydration is exactly the "render runs twice with the same inputs" case. See [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Issues]].

### Accessible ids: `Math.random()` in render vs `useId`

A form library generates `id`/`htmlFor` pairs to link labels to inputs. Generating them in render breaks under re-runs.

```jsx
function Field({ label }) {
  const id = `field-${Math.random()}`;   // ❌ new id every render → label detaches, hydration mismatch
  const id2 = useId();                   // ✅ stable per component instance, SSR-safe
  return (<><label htmlFor={id2}>{label}</label><input id={id2} /></>);
}
```

Works because `useId` is keyed to the component's position in the tree, so it survives re-renders and matches between server and client — anything computed with side effects or randomness in render does not.

### Profiling a laggy dashboard: expensive render vs unnecessary commit

A trading dashboard re-renders a 5,000-row table on every price tick. The team's first instinct is `React.memo` on everything; the profiler shows the *render* itself takes 180ms — memo doesn't make an expensive render cheap, it only skips renders whose props didn't change (and prices change every tick).

```jsx
// ✅ shrink the render, don't fight the re-render
const visibleRows = useMemo(
  () => sortRows(rows).slice(scrollIndex, scrollIndex + 40),  // derive + window
  [rows, scrollIndex]
);
return <Table rows={visibleRows} />;   // or react-window/react-virtuoso
```

This is the cost hierarchy from section 1 in practice: the problem was an expensive render (big tree, heavy sort), so the fix is derivation + virtualization — not suppressing re-renders that are legitimately needed.

> [!tip]
> Order of investigation in the React Profiler: is the render frequent AND expensive? Cheap frequent renders are usually fine; expensive ones need less work per render (memoized derivation, windowing) before you reach for `memo`.

## 6. Interview Answer

Short answer:

> A render is React calling your component to compute an element tree and diffing it — pure, interruptible, no DOM changes. The commit phase then applies the diff to the real DOM synchronously and runs effects. A component re-rendering doesn't mean the DOM changed; if the output matches, React commits nothing.

Deeper answer:

> Because the render phase can run multiple times, be aborted, or run in the background before committing, component functions must be pure — no side effects, no external mutation during render — which is what StrictMode's double-invoke enforces. State is a per-render snapshot captured by closure, so handlers see the values from the render that created them; that's why batched `setN(n+1)` calls collapse and why DOM reads/writes belong in layout effects after commit, not in render.

## 7. Practice

1. <details><summary>A component re-renders 60 times/second per a profiler, but users report no lag and the DOM is stable. Is this a bug?</summary>Not necessarily. Re-rendering runs the function and diffs; if the output is identical, React commits nothing to the DOM — the cost is just the JS of rendering + diff. If those renders are cheap, it's fine. Investigate only if the render itself is expensive (big lists, heavy computation) or triggers commits. "Reduce re-renders" is not a goal in itself; reduce *expensive* renders and unnecessary commits.</details>

2. <details><summary>Why does StrictMode double-invoke your component in development, and what does a component that breaks under it reveal?</summary>To surface impurity: a pure render produces the same result twice with no observable side effects, so double-invoking is a no-op for correct components. A component that breaks (double-logs, double-increments an external counter, corrupts a cache) is doing side effects *during render* or mutating external state — bugs that also manifest under concurrent rendering/aborted renders in production. StrictMode makes them visible early.</details>

3. <details><summary>Explain, in phase terms, why `useLayoutEffect` prevents a visual flicker that `useEffect` would show.</summary>`useLayoutEffect` fires synchronously after commit but before the browser paints, so DOM measurements/mutations happen while the frame is still being prepared — the user never sees an intermediate state. `useEffect` (passive) fires after paint, so the user sees the pre-effect frame first, then a corrected frame — a flicker. Cost: layout effects block paint, so keep them light.</details>

## Related Notes

- [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]
- [[21 - React Internals and Patterns/04 - State Batching and Updater Queues|State Batching and Updater Queues]]
- [[21 - React Internals and Patterns/07 - useLayoutEffect useInsertionEffect and Effect Timing|Effect Timing]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[01 - Roadmap|Roadmap]]
