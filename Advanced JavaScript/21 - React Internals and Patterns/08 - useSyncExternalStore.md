---
tags: [react, internals, state, stores]
module: "21 - React Internals and Patterns"
priority: important
status: not-started
aliases: [useSyncExternalStore, Tearing]
---

# useSyncExternalStore

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain tearing, why external stores need a dedicated hook in concurrent React, and the subscribe/getSnapshot contract.
- Production signal: you can bind a non-React data source (browser API, Zustand/Redux-style store) to React correctly, including SSR.
- Dependencies: [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling Overview]], [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]]

## Source Anchors

- [react.dev - useSyncExternalStore](https://react.dev/reference/react/useSyncExternalStore)
- [react.dev - You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
- [React 18 Working Group - Concurrent React for Library Maintainers](https://github.com/reactwg/react-18/discussions/70)

## 1. Concept

`useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot?)` is the official way to subscribe a React component to a store that lives **outside** React — Redux, Zustand, a browser API (`navigator.onLine`, `matchMedia`), a custom `EventTarget`, anything React doesn't own.

```jsx
function useOnlineStatus() {
  return useSyncExternalStore(
    (callback) => {                     // subscribe: register, return unsubscribe
      window.addEventListener("online", callback);
      window.addEventListener("offline", callback);
      return () => {
        window.removeEventListener("online", callback);
        window.removeEventListener("offline", callback);
      };
    },
    () => navigator.onLine,             // getSnapshot: read current value (client)
    () => true                          // getServerSnapshot: value during SSR
  );
}
```

The contract: `subscribe` registers a listener and returns an unsubscribe; `getSnapshot` returns the current value and **must return a referentially-stable value when nothing changed** (or React re-renders forever). React calls `getSnapshot` to detect changes via `Object.is`.

## 2. Why It Matters — Tearing

Before this hook, external stores were bound with `useEffect` + `useState`. Concurrent React broke that subtly. Because the render phase is [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|interruptible]], React can pause mid-render, and an external store can *change during the pause*. Then different components in the same render read different values — the UI shows **inconsistent state within one frame**: this is **tearing**.

Example: a store holds `count = 1`. React renders `<A>` (reads 1), yields, the store updates to `2`, React resumes and renders `<B>` (reads 2). One paint shows "A: 1" and "B: 2" — torn. Plain `useState`/`useContext` are safe because React controls those values; an *external* mutable source isn't under React's consistency guarantees.

`useSyncExternalStore` fixes this: it forces updates from external stores to be synchronous/consistent, and React re-checks the snapshot to detect changes that happened during rendering, re-rendering if the store moved — so every component in a committed frame reads the same value.

> [!tip] You usually consume this hook, you rarely write it
> Modern react-redux, Zustand, Jotai, and Valtio all use `useSyncExternalStore` internally. You write it directly mainly to bind *browser* APIs (online status, media queries, viewport size, storage events) or a small custom store. Knowing the hook explains *how your state library stays consistent under concurrent rendering*.

## 3. The getSnapshot Stability Trap

`getSnapshot` must not return a fresh object each call, or React sees a "new" value every check and loops:

```jsx
// ❌ new array every call → infinite re-render
useSyncExternalStore(subscribe, () => store.items.filter(x => x.active));

// ✅ return a stable reference; derive/memoize outside, or select a stable slice
useSyncExternalStore(subscribe, () => store.activeItems);  // store maintains this reference
```

This mirrors the [[14 - JavaScript in React and Next.js/05 - Referential Equality|referential equality]] rule everywhere in React: derived objects need stable identity. For selecting/deriving with memoization, `useSyncExternalStoreWithSelector` (from `use-sync-external-store/shim/with-selector`) adds an equality function.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — binding a media query with effect + state:

```jsx
function useMediaQuery(query) {
  const [matches, setMatches] = useState(false);   // ❌ starts false even if it matches
  useEffect(() => {
    const mql = window.matchMedia(query);
    setMatches(mql.matches);                        // corrected AFTER first paint → flicker
    const handler = (e) => setMatches(e.matches);
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [query]);
  return matches;
}
```

Trace: first render returns `false` regardless of the real match; after paint the effect runs and corrects it → a visible flash of the wrong layout (e.g., desktop nav flashing on mobile). Also under concurrent rendering, two components using this hook can momentarily disagree (tearing).

Production-safe fix:

```jsx
function useMediaQuery(query) {
  return useSyncExternalStore(
    (cb) => {
      const mql = window.matchMedia(query);
      mql.addEventListener("change", cb);
      return () => mql.removeEventListener("change", cb);
    },
    () => window.matchMedia(query).matches,   // read synchronously during render → correct first frame
    () => false                                // SSR default (server has no viewport)
  );
}
```

Now the first render reads the real match synchronously (no post-paint correction, no flicker), all consumers stay consistent, and SSR has a defined value.

Tradeoffs: `getServerSnapshot` must return something sensible for the server (which has no `window`) — and if the server guess differs from the client's real value, you get a hydration mismatch for that subtree ([[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Issues]]); media queries genuinely can't be known server-side, so a one-frame client correction or a mismatch is sometimes unavoidable — pick the least-bad default. Calling `matchMedia` inside `getSnapshot` on every render is also slightly wasteful; a small memo/cache per query is a reasonable optimization.

## 5. Interview Answer

Short answer:

> `useSyncExternalStore` subscribes a component to a store outside React with a `subscribe` function and a `getSnapshot` that returns the current value. It exists because concurrent rendering can pause mid-render while an external store changes, letting different components read different values — tearing. The hook forces consistent, synchronous reads so every component in a committed frame sees the same value.

Deeper answer:

> `getSnapshot` must return a referentially stable value when unchanged or React loops; deriving objects needs the with-selector variant plus an equality function. `getServerSnapshot` provides the SSR value and, if it disagrees with the client, causes a hydration mismatch — unavoidable for truly client-only signals like viewport. In practice Redux, Zustand, and friends use this hook internally; you write it directly mainly to bind browser APIs, and knowing it explains how those libraries stay tear-free under concurrent React while plain useEffect+useState binding doesn't.

## 6. Practice

1. <details><summary>Define tearing and explain why `useState` isn't vulnerable but an external store is.</summary>Tearing is when a single committed frame shows inconsistent values because components read a data source at different points while React paused and resumed rendering. `useState`/`useContext` values are owned and versioned by React, so it guarantees consistency across a render. An external mutable store isn't under React's control — it can change during an interruptible render, so two components reading it directly can capture different values. `useSyncExternalStore` restores consistency.</details>

2. <details><summary>Why does `getSnapshot: () => ({ x: store.x })` cause an infinite loop?</summary>It returns a new object every call, so React's `Object.is` comparison against the previous snapshot is always false → React thinks the store changed → re-renders → calls getSnapshot again → new object → loops. getSnapshot must return a stable reference (a primitive, or the same object identity while unchanged). To derive shape, keep the derived value stable in the store or use useSyncExternalStoreWithSelector with an equality fn.</details>

3. <details><summary>You bind `window.scrollY` with this hook and performance tanks. What went wrong conceptually?</summary>Scroll fires at very high frequency, and each change calls the subscriber → re-render. Binding a rapidly-changing value directly means re-rendering on every scroll tick — the hook faithfully propagates every change. Fix: don't route high-frequency values through render at all (use a ref/direct DOM for scroll-driven effects), or throttle/coalesce updates before notifying subscribers. The hook is for *state* consistency, not a license to render on every micro-change.</details>

4. <details><summary>What's the purpose of the third argument, and what breaks without it in an SSR app?</summary>`getServerSnapshot` supplies the value used during server rendering, where `subscribe`/client `getSnapshot` (which may touch `window`) can't run. Without it, SSR either throws (accessing `window`) or React can't produce server HTML for the hook. With it, the server renders a defined value; if that value differs from the client's real one, you get a hydration mismatch for that subtree — sometimes unavoidable for client-only signals, so you choose the safest default.</details>

## Related Notes

- [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling Overview]]
- [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]
- [[31 - Low Level Design/04 - Design Patterns|Design Patterns]] — this hook is the Observer pattern
- [[01 - Roadmap|Roadmap]]
