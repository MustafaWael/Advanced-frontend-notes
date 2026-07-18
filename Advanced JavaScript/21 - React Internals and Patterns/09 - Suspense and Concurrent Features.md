---
tags: [react, internals, suspense, concurrent]
module: "21 - React Internals and Patterns"
priority: important
status: not-started
aliases: [Suspense, useDeferredValue, Transitions]
---

# Suspense and Concurrent Features

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: you can explain what Suspense actually does (catch a thrown promise, show fallback), how transitions and `useDeferredValue` keep UIs responsive, and the streaming SSR relationship.
- Production signal: you use Suspense boundaries and transitions to shape loading/urgency deliberately rather than scattering `isLoading` flags.
- Dependencies: [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling Overview]], [[08 - Async JavaScript/02 - Promises|Promises]]

## Source Anchors

- [react.dev - Suspense](https://react.dev/reference/react/Suspense)
- [react.dev - useTransition](https://react.dev/reference/react/useTransition)
- [react.dev - useDeferredValue](https://react.dev/reference/react/useDeferredValue)
- [react.dev - use](https://react.dev/reference/react/use)

## 1. Concept

Two related capabilities the concurrent renderer unlocked:

**Suspense** lets a component "suspend" — signal that it isn't ready to render because it's waiting on something (data, code, an image). Mechanically, a suspending component *throws a promise*; the nearest `<Suspense fallback={…}>` boundary catches it, shows the fallback, and retries the subtree when the promise resolves.

```jsx
<Suspense fallback={<Skeleton />}>
  <Comments commentsPromise={promise} />   {/* uses `use(promise)` → suspends until resolved */}
</Suspense>
```

**Concurrent features** — transitions and deferred values — let you mark some updates as low-priority so urgent interactions stay responsive ([[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|lanes/scheduling]]).

## 2. Why It Matters

- Suspense unifies loading states declaratively: instead of every data component owning an `isLoading` branch, you declare *where* fallbacks appear in the tree. It's the model Next.js App Router, React Query, and RSC build on.
- Transitions/`useDeferredValue` are the standard answers to "how do you keep a search input responsive while filtering a huge list" — a very common senior interview scenario.

## 3. How Suspense Works, Precisely

1. A component reads a not-yet-ready resource (via `use(promise)`, a Suspense-enabled data library, or `React.lazy` for code).
2. It throws the promise. React unwinds to the nearest Suspense boundary and renders its `fallback`.
3. When the promise resolves, React retries rendering the subtree with the now-ready data.
4. Boundaries nest: an inner boundary catches first, so you can show granular skeletons; an outer boundary catches anything uncaught below it.

Important constraint ([[21 - React Internals and Patterns/10 - React 19|React 19]] `use`): the promise must be *cached/stable* — a promise created fresh in render each time would re-suspend forever. In practice the promise comes from a framework/data layer that caches it (RSC, React Query), not from `fetch()` called inline in render.

`React.lazy` is Suspense for *code*: the dynamic import returns a promise; the boundary shows a fallback until the chunk loads — this is how route-based code splitting shows a spinner ([[10 - Modules/07 - Tree Shaking and Code Splitting|code splitting]]).

## 4. Transitions and Deferred Values

**`useTransition`** marks a state update as non-urgent, giving you an `isPending` flag and keeping the app interactive while the heavy render happens in the background (full mechanism and search example in [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling]]).

**`useDeferredValue`** is the "I don't own the setState" cousin: you pass it a value and it returns a version that *lags* during urgent updates, so expensive children re-render off the deferred (stale-but-catching-up) value.

```jsx
function Search({ query }) {
  const deferredQuery = useDeferredValue(query);      // lags behind `query` under load
  const results = useMemo(() => filter(all, deferredQuery), [deferredQuery]);
  const stale = query !== deferredQuery;              // show dimmed while catching up
  return <div style={{ opacity: stale ? 0.6 : 1 }}><List items={results} /></div>;
}
```

Difference to state clearly: use `useTransition` when *you* trigger the state update (you can wrap the setter); use `useDeferredValue` when the value comes *in as a prop* and you can't wrap its source. Both reduce jank by deprioritizing, not by speeding up work.

**Suspense + transitions interplay**: wrapping a navigation in `startTransition` tells React "don't show the Suspense fallback again, keep the old UI visible until the new content is ready" — this avoids a jarring flash back to a skeleton when navigating between already-loaded routes.

Two adjacent tools to know: **`<Activity mode="hidden">`** (stable in React 19.2 — [[21 - React Internals and Patterns/10 - React 19|React 19]]) preserves a subtree's state while hiding it and deferring its updates — the state-keeping alternative to unmounting for tabs and back-navigation. And **`<ViewTransition>`** (still experimental as of mid-2026) aims to animate these transitions via the browser's View Transitions API — know it exists, don't rely on it yet.

## 5. Streaming SSR Relationship

Suspense is also the unit of **streaming server rendering**. The server sends HTML for the ready parts immediately and *streams in* the suspended parts as their data resolves:

1. Server renders the shell, sending a fallback placeholder for each `<Suspense>` whose data isn't ready.
2. As each boundary's data resolves, the server streams the real HTML plus a tiny script that swaps it into place.
3. **Selective hydration**: React can hydrate ready boundaries independently, and prioritize hydrating whatever the user interacts with first.

This is why a Suspense boundary in Next.js lets a slow widget (a recommendations panel hitting a slow API) stream in later without blocking the page's first paint — the same boundary shapes both client loading fallbacks and server streaming chunks ([[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]).

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — imperative loading flags and a janky filter:

```jsx
function ProductPage({ query }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    fetchProducts(query).then(r => { setResults(r); setLoading(false); });
  }, [query]);
  // Filtering the huge list below also janks the input on each keystroke.
  return loading ? <Spinner /> : <BigList items={results} />;
}
```

Issues: manual loading state per component (repeated everywhere, race-prone — [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|races]]), and heavy re-renders freeze the input.

Production-safe shape — Suspense for loading, deferred value for responsiveness:

```jsx
function ProductPage() {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);
  return (
    <>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />  {/* stays responsive */}
      <Suspense fallback={<ListSkeleton />}>
        <Results query={deferredQuery} />   {/* suspends on data via the data layer */}
      </Suspense>
    </>
  );
}
```

Tradeoffs: Suspense-based data needs a data layer that *throws stable promises* (RSC, React Query, Relay) — you can't just call `fetch` in render, so this pattern is only clean inside a framework that provides it. `useDeferredValue` intentionally shows stale results briefly (dim them so users understand). And Suspense doesn't handle *errors* — a rejected data fetch needs an Error Boundary ([[11 - Error Handling/05 - React Error Boundaries|Error Boundaries]]) alongside; the two boundaries are complementary (loading vs failure). Over-splitting boundaries also creates a "popcorn" effect of many independent skeletons resolving at different times — group them thoughtfully.

## 7. Interview Answer

Short answer:

> Suspense lets a component suspend by throwing a promise; the nearest boundary shows a fallback and retries when it resolves — declarative loading states instead of per-component isLoading flags. Transitions (`useTransition`) and `useDeferredValue` mark updates as low-priority so urgent input stays responsive while heavy renders happen in the background. Suspense is also the streaming SSR unit: the server sends ready HTML first and streams suspended parts as their data resolves, with selective hydration.

Deeper answer:

> The suspended promise must be cached/stable or the component re-suspends forever, so Suspense data comes from a framework data layer, not inline fetch. `useTransition` wraps a state update you control; `useDeferredValue` lags a value you receive as a prop — both deprioritize rather than speed up, so heavy work still needs memoization or workers. Wrapping navigation in a transition keeps the previous UI visible instead of flashing a fallback. Suspense pairs with Error Boundaries — one for loading, one for failure — since Suspense itself doesn't catch errors.

## 8. Practice

1. <details><summary>Mechanically, what does a component "suspending" mean, and what catches it?</summary>The component throws a promise (rather than returning JSX) to signal it isn't ready. React unwinds to the nearest `<Suspense>` boundary above it, renders that boundary's `fallback`, and subscribes to the promise; when it resolves, React retries rendering the suspended subtree with the ready data. It's conceptually try/catch for "not ready yet", with the promise as the signal.</details>

2. <details><summary>useTransition vs useDeferredValue — when each?</summary>Use `useTransition` when you own the state update and can wrap the setter in `startTransition` (e.g., your onChange sets results). Use `useDeferredValue` when the expensive input arrives as a prop/value you don't control the setter for — you defer the value locally. Both keep urgent updates (typing) responsive by rendering the heavy work at lower priority; neither makes the heavy work itself faster.</details>

3. <details><summary>Why can't you pass `use(fetch("/api"))` created inline in render to Suspense?</summary>Each render calls `fetch` again, creating a *new* promise; `use` suspends on it, React retries, render runs again, new promise — it never settles into a resolved cached value, so it re-suspends forever (React warns about uncached promises). The promise must be created outside render or memoized/cached by a Suspense-aware data layer (RSC, React Query) so the same resolved promise is returned across retries.</details>

4. <details><summary>Explain how one Suspense boundary shapes both a client loading skeleton and server streaming.</summary>On the client, if the boundary's subtree suspends (data/code not ready), React shows the fallback until it resolves. On the server with streaming SSR, that same boundary lets the server send the shell + fallback immediately and stream the real HTML for the subtree once its data resolves, swapping it in via an inline script, with selective hydration prioritizing user-interacted boundaries. So the boundary is a single declaration of "this part may not be ready yet" that both render environments honor.</details>

## Related Notes

- [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling Overview]]
- [[21 - React Internals and Patterns/10 - React 19|React 19]]
- [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]]
- [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]
- [[01 - Roadmap|Roadmap]]
