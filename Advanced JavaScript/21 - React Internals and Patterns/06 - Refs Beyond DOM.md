---
tags: [react, internals, refs, hooks]
module: "21 - React Internals and Patterns"
priority: important
status: not-started
aliases: [useRef, forwardRef, Callback Refs]
---

# Refs Beyond DOM

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain `useRef` as a mutable instance variable that doesn't trigger renders, when to use callback refs, and how `ref` works as a prop in React 19.
- Production signal: you store non-rendered mutable values (timers, latest-value, previous-value, instances) in refs instead of forcing re-renders or stale closures.
- Dependencies: [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]], [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

## Source Anchors

- [react.dev - useRef](https://react.dev/reference/react/useRef)
- [react.dev - Referencing Values with Refs](https://react.dev/learn/referencing-values-with-refs)
- [react.dev - Manipulating the DOM with Refs](https://react.dev/learn/manipulating-the-dom-with-refs)
- [react.dev - useImperativeHandle](https://react.dev/reference/react/useImperativeHandle)
- [react.dev - useEffectEvent](https://react.dev/reference/react/useEffectEvent)

## 1. Concept

`useRef(initial)` returns a stable object `{ current: initial }` that:

- **persists across renders** (same object every render — stable identity),
- is **mutable** — you can write `ref.current = x` any time,
- and, critically, **does not trigger a re-render** when you change it.

That last property is the whole point. State is for values the UI renders *from*; refs are for values the component needs to *remember* but that don't belong in the render output.

```jsx
const timerRef = useRef(null);       // holds a timer id — not rendered
timerRef.current = setTimeout(...);  // mutate freely, no re-render
```

The DOM use (`<input ref={inputRef} />` → `inputRef.current` is the node) is just the most visible special case of "a stable mutable box React fills in."

## 2. Why It Matters

- Refs are the escape hatch from React's render model for values that are *imperative* by nature: DOM nodes, timer/interval ids, subscription handles, third-party library instances, the "latest" value for a callback, the previous value for comparison.
- Confusing "should this be state or a ref?" produces two classic bugs: putting render-relevant data in a ref (UI doesn't update) or putting imperative data in state (needless re-renders, sometimes infinite loops).

## 3. Refs as Instance Variables

Before hooks, class components stored per-instance mutable data as `this.x`. `useRef` is the function-component equivalent — one box per component instance, surviving renders.

```jsx
function Stopwatch() {
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef(null);          // instance variable: the interval id
  const startedAtRef = useRef(null);

  function start() {
    startedAtRef.current = Date.now();
    intervalRef.current = setInterval(() => {
      setElapsed(Date.now() - startedAtRef.current);  // state drives the UI
    }, 50);
  }
  function stop() { clearInterval(intervalRef.current); }  // need the id later → ref
  // ...
}
```

`elapsed` is state (rendered). The interval id and start time are refs (needed imperatively, never rendered). Storing the interval id in state would be wrong — updating it would re-render for no visual reason, and reading it in `stop` might read a stale snapshot.

> [!warning] Don't read or write refs during render
> Mutating a ref during render is a side effect ([[21 - React Internals and Patterns/01 - Render and Commit Phases|render must be pure]]) and reading one during render can return values from a different commit under concurrent rendering. Read/write refs in event handlers, effects, or callbacks — not in the render body. (Lazy one-time init like `if (!ref.current) ref.current = createThing()` is the tolerated exception.)

## 4. The "Latest Value" Ref Pattern

A ref bridges the [[14 - JavaScript in React and Next.js/03 - Stale Closures|stale-closure]] gap: keep a ref updated with the newest value so long-lived callbacks read *current* data without needing to be recreated.

```jsx
function useEventCallback(fn) {
  const ref = useRef(fn);
  useLayoutEffect(() => { ref.current = fn; });   // keep latest fn
  return useCallback((...args) => ref.current(...args), []); // stable identity, always-fresh fn
}
```

This gives a stable function identity (good for memoized children / effect deps) that never goes stale. React shipped the official version of this idea as **`useEffectEvent`**, stable since React 19.2 (Oct 2025) — but it is *narrower* than the ref pattern, not a drop-in replacement. The rules (enforced by `eslint-plugin-react-hooks` v6):

- An Effect Event may only be called **from inside effects** (`useEffect`, `useLayoutEffect`, `useInsertionEffect`) or other Effect Events — never during render, never from event handlers.
- It must **never appear in a dependency array**, and must not be passed to other components or hooks.
- Its identity is **deliberately unstable** — it changes every render as a runtime assertion against misuse. That's the opposite of the ref pattern above, which exists precisely to give you a *stable* identity you can hand to memoized children.

So the decision is: latest-value logic *inside an effect* → `useEffectEvent` (React 19.2+); a stable, never-stale callback you need to *pass around* (memoized children, event handler props, pre-19.2 codebases, portable library code) → the `useEventCallback` ref pattern. Use either deliberately: both opt a value *out* of reactivity, which is sometimes exactly right (analytics callback) and sometimes hides a real dependency.

> [!warning] Don't use `useEffectEvent` to silence the deps linter
> If a value changing *should* re-run the effect (a `roomId`, a query), it's a dependency — wrapping it hides real bugs. react.dev's own counter-example: `logVisit(pageUrl)` wrapped in an Effect Event inside an empty-deps effect silently stops logging page changes. Reserve Effect Events for logic that is conceptually an *event* that happens to fire from an effect ("show a notification when connected, with the current theme") — not for reactive inputs.

## 5. Callback Refs and forwardRef / React 19

**Callback refs**: pass a function instead of a ref object; React calls it with the node on mount and `null` on unmount (React 19 also supports returning a cleanup function). Use when you need to *run code* when the node attaches, or attach to a dynamic list of nodes:

```jsx
<div ref={(node) => {
  if (node) observer.observe(node);          // measure/observe on attach
  return () => observer.unobserve(node);      // React 19 cleanup form
}} />
```

**Passing refs to components**: a component is a function — `<MyInput ref={r} />` needs the ref forwarded to a real DOM node inside.

- **Pre-React 19**: wrap with `forwardRef((props, ref) => ...)`.
- **React 19+**: `ref` is just a regular prop — `function MyInput({ ref }) { return <input ref={ref} /> }`. `forwardRef` is being deprecated (a codemod exists).

**`useImperativeHandle`**: when a parent needs to call *methods* on a child (`focus()`, `scrollToTop()`, `play()`) rather than touch its DOM, expose a curated imperative API:

```jsx
function VideoPlayer({ ref }) {           // React 19 ref-as-prop
  const videoRef = useRef(null);
  useImperativeHandle(ref, () => ({
    play: () => videoRef.current.play(),
    seek: (t) => { videoRef.current.currentTime = t; },
  }), []);
  return <video ref={videoRef} />;
}
```

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — previous-value comparison via state:

```jsx
function PriceAlert({ price }) {
  const [prevPrice, setPrevPrice] = useState(price);
  useEffect(() => {
    if (price > prevPrice) notify("Price rose!");
    setPrevPrice(price);         // ❌ setState in effect → extra render every price change
  }, [price, prevPrice]);        // prevPrice in deps → effect re-runs on its own update
  // ...
}
```

Trace: each price change runs the effect, calls `setPrevPrice` → another render → effect sees `prevPrice` changed → potential double-processing and an avoidable render per update.

Production-safe fix — previous value in a ref:

```jsx
function PriceAlert({ price }) {
  const prevPriceRef = useRef(price);
  useEffect(() => {
    if (price > prevPriceRef.current) notify("Price rose!");
    prevPriceRef.current = price;   // ✅ mutate ref: no re-render, no self-triggering dep
  }, [price]);
  // ...
}
```

Tradeoffs: the ref approach is correct and cheaper, but "previous value" is inherently imperative — the ref is *not* part of render, so you can't render "previous price" directly from it without also keeping it in state when the UI needs to *show* it. Rule: if the UI displays it → state; if it's only for comparison/bookkeeping → ref. Mixing them (render from a ref) leads to "the screen didn't update" bugs because ref writes don't re-render.

## 7. Interview Answer

Short answer:

> `useRef` is a stable, mutable box that persists across renders and — crucially — doesn't trigger a re-render when you change `.current`. It's the function-component instance variable: for DOM nodes, timer ids, subscriptions, library instances, and "latest/previous value" bookkeeping. State is for what the UI renders from; refs are for what the component must remember but doesn't render.

Deeper answer:

> Callback refs run code on attach/detach (with a cleanup return in React 19) and handle dynamic node sets. Passing a ref into a component needed `forwardRef` before React 19, where `ref` is now an ordinary prop and `forwardRef` is being deprecated. `useImperativeHandle` exposes a curated method API instead of a raw node. The key discipline is not reading or writing refs during render — that's a side effect and unsafe under concurrent rendering — and choosing ref vs state by whether the value appears in the render output.

## 8. Practice

1. <details><summary>You store a WebSocket instance in `useState`. Symptoms and correct fix?</summary>Every place that recreates or replaces the socket triggers a re-render, and reading it in async callbacks may hit a stale snapshot; you may also get render loops if creation happens in render. A socket is imperative, non-rendered infrastructure → store it in a `useRef` (create it in an effect, close it in the effect's cleanup). Use state only for *derived, rendered* status like `isConnected`.</details>

2. <details><summary>Why doesn't `ref.current = x` update the screen, and when is that a feature vs a bug?</summary>Ref writes deliberately bypass React's update mechanism — no subscription, no re-render. Feature: for values the UI doesn't display (timer ids, latest-value bridges, measurements-in-progress), you avoid wasteful renders. Bug: if the UI is supposed to reflect that value, the screen goes stale because nothing told React to re-render — that data belonged in state.</details>

3. <details><summary>Contrast a callback ref with a ref object for attaching an IntersectionObserver to list items.</summary>A ref object holds one node; a list of dynamic items would need an array of refs and effect coordination. A callback ref runs per node as it mounts/unmounts — `ref={node => { if (node) io.observe(node); }}` (with a cleanup return in React 19) — so each item wires itself up on attach and tears down on removal without index bookkeeping. Callback refs shine exactly when you must run logic at attach time or manage a variable set of nodes.</details>

4. <details><summary>In React 19, how do you let a parent call `focus()` on a custom `<SearchInput>`? Sketch it.</summary>Accept `ref` as a prop and expose an imperative handle: `function SearchInput({ ref }) { const inputRef = useRef(null); useImperativeHandle(ref, () => ({ focus: () => inputRef.current.focus() }), []); return <input ref={inputRef} />; }`. Parent: `const r = useRef(null); <SearchInput ref={r} />; r.current.focus();`. No `forwardRef` needed in React 19 — `ref` is a normal prop.</details>

## Related Notes

- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[21 - React Internals and Patterns/07 - useLayoutEffect useInsertionEffect and Effect Timing|Effect Timing]]
- [[21 - React Internals and Patterns/11 - Custom Hook Design Patterns|Custom Hook Design Patterns]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[01 - Roadmap|Roadmap]]
