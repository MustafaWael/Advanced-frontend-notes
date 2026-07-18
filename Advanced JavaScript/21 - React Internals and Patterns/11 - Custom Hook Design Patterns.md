---
tags: [react, hooks, patterns, architecture]
module: "21 - React Internals and Patterns"
priority: important
status: not-started
aliases: [Custom Hooks]
---

# Custom Hook Design Patterns

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain what a custom hook actually is (a function calling hooks — sharing logic, not state), and design a clean hook API with correct dependencies and cleanup.
- Production signal: your hooks have stable return identities, honest dependency arrays, and cleanup — reusable without surprising the caller.
- Dependencies: [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]], [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]

## Source Anchors

- [react.dev - Reusing Logic with Custom Hooks](https://react.dev/learn/reusing-logic-with-custom-hooks)
- [react.dev - Rules of Hooks](https://react.dev/reference/rules/rules-of-hooks)
- [react.dev - useCallback](https://react.dev/reference/react/useCallback)
- [react.dev - You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)

## 1. Concept

A custom hook is just a function whose name starts with `use` and that calls other hooks. It exists to **share stateful logic**, not state itself: two components using `useCounter()` get two independent counters. The hook packages the wiring (state + effects + handlers); each call site gets its own instance of that wiring.

```jsx
function useToggle(initial = false) {
  const [on, setOn] = useState(initial);
  const toggle = useCallback(() => setOn(o => !o), []);   // stable identity
  return [on, toggle];
}
```

The Rules of Hooks apply: call hooks unconditionally, at the top level, only from components or other hooks — because React tracks hook state by call order ([[14 - JavaScript in React and Next.js/04 - Dependency Arrays|why order matters]]).

The mechanism behind that rule: hook state lives on the component's fiber ([[21 - React Internals and Patterns/15 - Elements JSX and Component Identity|element vs component vs fiber]]) as a **linked list of hook slots**, consumed *positionally* — first `useState` call reads slot 1, second reads slot 2, and so on. There are no names; position is identity. Make a call conditional and every subsequent hook shifts one slot, reading a stranger's state:

```jsx
if (isEditing) useState("");     // ❌ slot 1 exists only sometimes
const [name] = useState("Ada");  // reads slot 1 or slot 2 depending on isEditing → corrupted state
```

React detects the count mismatch and throws ("Rendered fewer hooks than expected"), but the rule exists to prevent the silent version of this corruption.

## 2. Why It Matters

- Custom hooks are the primary React code-reuse mechanism; a badly designed one leaks re-renders, stale closures, or missing cleanup into every consumer.
- "What is a custom hook and what does it share?" plus "design a `useDebouncedValue`/`useFetch`" are extremely common interview tasks that reveal whether you understand hooks or just use them.

## 3. Design Principles

**Return stable identities.** Functions and objects a hook returns should be memoized (`useCallback`/`useMemo`) so consumers can safely put them in dependency arrays or pass them to memoized children without churn ([[14 - JavaScript in React and Next.js/05 - Referential Equality|referential equality]]). (In a React Compiler codebase this is handled for you — [[21 - React Internals and Patterns/10 - React 19|React 19]].)

**Choose a return shape deliberately.** Array (`[value, setter]`) when callers rename freely and there are ≤3 values; object (`{ data, error, isLoading }`) when there are many, or callers want to pick a subset by name. Match the ergonomics to the API.

**Own your cleanup.** Any subscription, timer, or listener the hook creates must be torn down in the effect's cleanup — the consumer can't clean up what they can't see ([[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|cleanup]]).

**Keep dependencies honest.** Don't lie to the linter to silence it; if a value is genuinely non-reactive (a callback you want latest but not reactive), use the latest-ref pattern ([[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs]]) rather than omitting deps.

## 4. Common Patterns

```jsx
// Latest-value ref: stable callback that never goes stale
function useEvent(fn) {
  const ref = useRef(fn);
  useLayoutEffect(() => { ref.current = fn; });
  return useCallback((...a) => ref.current(...a), []);
}

// Debounced value
function useDebouncedValue(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);          // cleanup cancels the pending update
  }, [value, delay]);
  return debounced;
}

// Subscription via useSyncExternalStore (tear-free) — see that note
function useOnline() { /* useSyncExternalStore(...) */ }
```

The `useEvent` pattern deserves emphasis: it lets a hook expose a callback that always sees the latest props/state but keeps a stable identity, breaking the "add it to deps → effect re-runs too often" bind. React shipped this idea officially as **`useEffectEvent`** (stable since React 19.2) — with stricter rules: callable only from inside effects, never listed in deps, never passed to children, and *deliberately unstable* identity. Full rules and the "which one when" decision in [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]]. The docs' flagship `useEffectEvent` example is literally a custom `useInterval` hook whose callback stays fresh without restarting the timer.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — a `useFetch` that races and leaks:

```jsx
function useFetch(url) {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch(url).then(r => r.json()).then(setData);   // no cleanup, no abort, no error state
  }, [url]);
  return data;
}
```

Trace the problems: rapidly changing `url` (A→B) fires two requests; if A resolves after B, `setData` overwrites B's data with A's — a [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|race condition]]; unmounting mid-flight still calls `setData` (works in React 18 without warning, but the request and its work are wasted); no error or loading state; a 404 sets `data` to an error body silently ([[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch resolves on 404]]).

Production-safe fix:

```jsx
function useFetch(url) {
  const [state, setState] = useState({ data: null, error: null, isLoading: true });
  useEffect(() => {
    const ac = new AbortController();
    setState(s => ({ ...s, isLoading: true }));
    fetch(url, { signal: ac.signal })
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(data => setState({ data, error: null, isLoading: false }))
      .catch(err => { if (err.name !== "AbortError") setState({ data: null, error: err, isLoading: false }); });
    return () => ac.abort();     // cancel on url change / unmount → kills the race
  }, [url]);
  return state;                  // object shape: many values, callers pick what they need
}
```

Tradeoffs: this is a *teaching* implementation — production apps should adopt React Query / SWR, which add caching, dedup, retries, revalidation, and Suspense integration you'd otherwise re-derive (badly). The object return shape suits `{ data, error, isLoading }`; abort-on-change fixes races but means an in-flight request is discarded on every keystroke (pair with debounced url). And the hook still re-runs the effect per `url` change — correct, but a caller passing a *new* url string identity each render (e.g., a template literal recomputed differently) would thrash; document that `url` should be stable.

## 6. Interview Answer

Short answer:

> A custom hook is a `use`-prefixed function that calls other hooks to share *logic*, not state — each call site gets its own independent state. Good hooks return stable identities (memoized functions/objects), pick an array or object shape to match ergonomics, own their cleanup for any subscription/timer/listener, and keep dependency arrays honest rather than lying to the linter.

Deeper answer:

> The Rules of Hooks (unconditional, top-level calls) exist because React tracks hook state positionally. Key patterns: the latest-value ref (`useEvent`/`useEffectEvent`) for a stable callback that never goes stale, so it doesn't force effects to re-run; `useSyncExternalStore` for tear-free external subscriptions; and abort-on-change for fetch hooks to kill races. A realistic `useFetch` handles races (AbortController), errors (`res.ok`), and loading — but the honest senior answer is that caching/dedup/retry belong in React Query or SWR rather than a hand-rolled hook.

## 7. Practice

1. <details><summary>Two components call `useCounter()`. Do they share the counter value? Explain what custom hooks actually share.</summary>No — each gets an independent counter. Custom hooks share *logic* (the wiring: which hooks are called, how state updates, effects), not state. Every call to the hook creates fresh state via the `useState`/`useRef` inside it, scoped to that component instance. To share state, you need a lifted state, context, or an external store — the hook alone gives each caller its own.</details>

2. <details><summary>Why should a custom hook memoize the functions it returns?</summary>So consumers can rely on stable identity: put the function in a `useEffect`/`useCallback` dependency array without causing re-runs every render, or pass it to a `React.memo` child without breaking the memo. An unmemoized returned function is a new reference each render, silently defeating downstream memoization and effect stability. (React Compiler automates this, but without it you memoize by hand.)</details>

3. <details><summary>Your `useInterval(callback, delay)` calls a stale callback. Fix it without re-creating the interval on every render.</summary>Store the callback in a ref updated each render (latest-value pattern), and read `ref.current` inside the interval; keep the interval effect keyed only on `delay`: `const cb = useRef(callback); useLayoutEffect(() => { cb.current = callback; }); useEffect(() => { const id = setInterval(() => cb.current(), delay); return () => clearInterval(id); }, [delay]);`. This decouples "always call the latest callback" from "don't restart the timer", the classic Dan Abramov useInterval. In React 19.2+ the official form is `const onTick = useEffectEvent(callback)` called inside the interval — same idea, linter-enforced rules.</details>

4. <details><summary>Array vs object return shape — when each?</summary>Array `[value, setValue]` when there are few values (≤3) and callers benefit from renaming freely (`const [open, setOpen] = useToggle()`), mirroring `useState`. Object `{ data, error, isLoading, refetch }` when there are many values, some optional, or callers want to destructure only a subset by stable name without caring about order. Objects are more self-documenting and extensible (adding a field doesn't shift positions); arrays are terser for the small, positional case.</details>

## Related Notes

- [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]]
- [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[01 - Roadmap|Roadmap]]
