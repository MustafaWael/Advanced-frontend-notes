---
tags: [react, react19, hooks, compiler]
module: "21 - React Internals and Patterns"
priority: must-know
status: not-started
aliases: [React 19, useActionState, useOptimistic, React Compiler]
---

# React 19

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can explain Actions, `useActionState`, `useOptimistic`, `use()`, and what the React Compiler means for manual memoization.
- Production signal: you write form mutations with Actions and optimistic UI declaratively, and you know when `useMemo`/`useCallback` are still worth writing.
- Dependencies: [[21 - React Internals and Patterns/04 - State Batching and Updater Queues|State Batching]], [[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense and Concurrent Features]]

## Source Anchors

- [react.dev - React v19 (blog)](https://react.dev/blog/2024/12/05/react-19)
- [react.dev - useActionState](https://react.dev/reference/react/useActionState)
- [react.dev - useOptimistic](https://react.dev/reference/react/useOptimistic)
- [react.dev - use](https://react.dev/reference/react/use)
- [react.dev - React Compiler 1.0 (blog)](https://react.dev/blog/2025/10/07/react-compiler-1)
- [react.dev - React 19.2 (blog)](https://react.dev/blog/2025/10/01/react-19-2)
- [react.dev - Activity](https://react.dev/reference/react/Activity)
- [react.dev - React Performance Tracks](https://react.dev/reference/dev-tools/react-performance-tracks)
- [react.dev - React Versions](https://react.dev/versions)

> React 19 is stable (released Dec 2024). As verified on 2026-07-11, the current line is **React 19.2.x** and the latest listed patch is **19.2.7**; there is no React 20. React Compiler reached stable **1.0 in October 2025**. Recheck [React Versions](https://react.dev/versions) before repeating a patch-level claim.

## 1. Actions — The Big Idea

An **Action** is, by convention, a function that runs an async transition to perform a mutation. React 19 makes async functions passed to transitions (and to `<form action={…}>`) automatically manage pending state, errors, and optimistic updates — collapsing the boilerplate of `isPending`/`error`/`try-catch` you used to hand-write.

```jsx
// The old way: manual isPending + error + try/catch
// React 19: a form Action does it for you
function ChangeName() {
  const [error, submitAction, isPending] = useActionState(
    async (prevState, formData) => {
      const err = await updateName(formData.get("name"));
      if (err) return err;              // returned value becomes the new state
      redirect("/profile");
      return null;
    },
    null                                // initial state
  );
  return (
    <form action={submitAction}>
      <input name="name" />
      <button disabled={isPending}>Update</button>
      {error && <p>{error}</p>}
    </form>
  );
}
```

`<form action={fn}>` calls `fn` with the [[19 - DOM and Browser APIs/08 - Forms and FormData|FormData]], resets the form on success for uncontrolled inputs, and — with a Server Action — works via native submission before hydration ([[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]], progressive enhancement).

## 2. The New Hooks

**`useActionState(action, initialState)`** → `[state, wrappedAction, isPending]`. Wraps an action; `state` is the action's last return value, `isPending` tracks it. The common case for form mutations. (Renamed from the canary `useFormState`.)

**`useOptimistic(actualValue)`** → `[optimisticValue, setOptimistic]`. Show the expected result *immediately* while the async request runs; React automatically reverts to the real value when the action settles (or errors):

```jsx
const [optimisticLikes, addOptimisticLike] = useOptimistic(likes);
async function like() {
  addOptimisticLike(optimisticLikes + 1);   // UI jumps instantly
  await sendLike();                          // if this throws, React reverts automatically
}
```

**`useFormStatus()`** (from `react-dom`) → reads the parent `<form>`'s pending state without prop drilling — for design-system submit buttons.

**`use(resource)`** → read a promise or context *during render*. Reading a promise suspends until it resolves ([[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense]]); unlike hooks, `use` can be called **conditionally** (after early returns, inside branches). The promise must be cached, not created in render.

```jsx
const theme = use(ThemeContext);        // conditional context read — legal, unlike useContext
const comments = use(commentsPromise);  // suspends until resolved
```

## 3. Quality-of-Life Changes Worth Knowing

- **`ref` as a prop**: function components receive `ref` directly; `forwardRef` is being deprecated ([[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs]]).
- **`<Context>` as provider**: `<ThemeContext value={…}>` instead of `<ThemeContext.Provider>`.
- **ref cleanup functions**: a callback ref may return a cleanup, run on unmount.
- **Document metadata**: `<title>`/`<meta>`/`<link>` rendered anywhere hoist to `<head>` ([[22 - Next.js Deep Dive/07 - Metadata SEO and the head|Metadata]]).
- **Stylesheet/async-script support** with `precedence`, plus resource preload APIs (`preload`, `preinit`, `prefetchDNS`, `preconnect`).
- **Better hydration error messages** with a diff ([[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Issues]]).
- **`useDeferredValue` initial value** argument.

## 4. React 19.1 and 19.2 — What Shipped Since

React stayed on the 19.x line rather than cutting a v20. The 19.2 (Oct 2025) additions worth knowing:

**`<Activity mode="visible|hidden">`** — a third answer to "show/hide UI", alongside conditional rendering (destroys state and DOM) and CSS hiding (keeps effects running and updating):

```jsx
<Activity mode={isActive ? "visible" : "hidden"}>
  <SearchTab />   {/* hidden: state + DOM preserved, effects UNMOUNTED, updates deferred */}
</Activity>
```

`hidden` hides the children, unmounts their effects, and defers their updates until React has nothing more urgent to do (background priority); `visible` remounts effects and processes updates normally. Real-world fits: tab UIs that must keep draft input, back-navigation that should restore scroll/form state, pre-rendering the next likely route in the background so navigation is instant. Contrast: `{isActive && <SearchTab />}` loses all state on toggle; `display: none` keeps subscriptions and timers alive and keeps re-rendering at full priority.

**`useEffectEvent`** — the stable release of the effect-event idea: extract the "event" part of an effect so it always sees fresh props/state without becoming a dependency. Strict rules (effects-only, never in deps, never passed down) in [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]].

**Performance Tracks** — 19.2 adds **Scheduler ⚛** and **Components ⚛** custom tracks to Chrome DevTools performance profiles: you can now *see* lane priorities (blocking vs transition), when React yields or waits for paint, and per-component render/effect timing. The first time [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|lane scheduling]] is directly observable rather than inferred.

**Partial Pre-rendering** — new `react-dom` server APIs: `prerender` a page's static shell ahead of time (serve from CDN), save the `postponed` state, then `resume` rendering the dynamic holes into the same stream on request. This is the React primitive underneath framework-level PPR ([[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]).

**SSR behavior fixes**: streamed Suspense boundary reveals are now briefly batched so server and client reveal behavior match (with a heuristic that stops batching if it would threaten LCP), and Web Streams SSR APIs landed for Node (Node streams still recommended — faster, compression by default). Also: `cacheSignal` for RSC cache-lifetime cleanup, and the `useId` prefix changed to `_r_` for View Transitions compatibility.

> [!tip] View Transitions: experimental, not shipped
> `<ViewTransition>` (animating UI changes via the browser's View Transitions API) is still experimental-channel-only as of mid-2026. Know what it's for; don't claim it's stable in an interview — production apps use the platform's `document.startViewTransition` directly or a library.

## 5. React Compiler and What It Means for Memoization

The **React Compiler** (stable 1.0, Oct 2025) is a build-time tool that auto-memoizes components and hooks — it analyzes your code and inserts the equivalent of `useMemo`/`useCallback`/`React.memo` where safe, so you get referential stability and skipped re-renders *without writing them by hand*. It relies on components following the [[21 - React Internals and Patterns/01 - Render and Commit Phases|Rules of React]] (pure render, no mutation), which is why those rules are now enforced by lint.

What this means practically:

- In a compiler-enabled codebase (opt-in; supported by Next.js, Vite, Expo), most manual `useMemo`/`useCallback` become redundant — the compiler handles the common cases, and hand-memoization becomes noise.
- Manual memoization still matters where: the compiler is *not* enabled; a value must be stable for reasons the compiler can't see (a `useEffect` dependency you want to fire rarely, an external subscription key); or you're memoizing genuinely expensive *computation* (the compiler memoizes to reduce re-renders, but you still reason about heavy work).
- It does not make bad-architecture fast — it reduces re-render overhead, not the cost of, say, filtering 100k rows synchronously ([[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|still your job]]).

> [!tip] The senior framing
> The Compiler shifts memoization from a manual micro-optimization chore to a compiler concern — but it's a *performance* tool, not a correctness one. Understanding *why* referential equality and purity matter ([[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]) is more valuable than ever, because the compiler only works when your components obey those rules. Learn the mechanism; let the compiler do the bookkeeping.

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — hand-rolled optimistic like with manual everything:

```jsx
function LikeButton({ postId, initialLikes }) {
  const [likes, setLikes] = useState(initialLikes);
  const [pending, setPending] = useState(false);
  async function like() {
    setPending(true);
    setLikes(likes + 1);                 // optimistic
    try { await sendLike(postId); }
    catch { setLikes(likes); }           // manual revert — and `likes` is a stale snapshot!
    finally { setPending(false); }
  }
  return <button onClick={like} disabled={pending}>♥ {likes}</button>;
}
```

Bugs: the revert uses the stale `likes` snapshot ([[21 - React Internals and Patterns/04 - State Batching and Updater Queues|snapshot rule]]); rapid clicks race; pending/error handling is manual and easy to get wrong.

Production-safe fix — Actions + `useOptimistic`:

```jsx
function LikeButton({ postId, likes }) {
  const [optimisticLikes, addOptimistic] = useOptimistic(likes);
  const [, likeAction, isPending] = useActionState(async () => {
    addOptimistic(optimisticLikes + 1);   // instant UI
    await sendLike(postId);               // React reverts optimistic value automatically on error
  }, null);
  return (
    <form action={likeAction}>
      <button disabled={isPending}>♥ {optimisticLikes}</button>
    </form>
  );
}
```

Tradeoffs: Actions/`useOptimistic` shine for the mutation-with-feedback pattern, but they're transition-based, so they assume you're on React 19 and (for the server variant) a framework with Server Actions. For non-form imperative flows they can feel forced — a plain handler with a data library's mutation (React Query `useMutation`, which also does optimistic updates + rollback) is often clearer and more portable. And optimistic UI is a UX decision: it's wrong when the operation frequently fails or when showing an unconfirmed state misleads (payments) — there, wait for confirmation.

## Real-World Use Cases

### Design-system `SubmitButton` with `useFormStatus`

A component library ships one submit button used by every form in the app. Pre-19 it needed an `isPending` prop drilled from each form's mutation state; `useFormStatus` reads the nearest parent `<form>`'s pending state directly.

```jsx
import { useFormStatus } from "react-dom";

function SubmitButton({ children }) {
  const { pending } = useFormStatus();       // reads the parent <form action> status
  return (
    <button type="submit" disabled={pending} aria-busy={pending}>
      {pending ? <Spinner /> : children}
    </button>
  );
}
// any form in the app: <form action={saveAction}><SubmitButton>Save</SubmitButton></form>
```

Works because form Actions put pending state *on the form itself*, so a child can subscribe without prop drilling — the button component stays generic across every mutation in the codebase.

> [!warning]
> `useFormStatus` only reads a **parent** `<form>` — it returns `pending: false` if called in the same component that renders the form. It must be in a child.

### Newsletter signup that works before hydration

A content-heavy landing page ships a signup form. With a Server Action bound to `<form action>`, the browser can submit via native form POST even if the user acts before the JS bundle loads — no dead click, no lost signup.

```jsx
// app/signup-form.tsx
import { subscribe } from "./actions";   // "use server" function

export function SignupForm() {
  return (
    <form action={subscribe}>            {/* native submission pre-hydration, Action post-hydration */}
      <input type="email" name="email" required />
      <SubmitButton>Subscribe</SubmitButton>
    </form>
  );
}
```

This is the progressive-enhancement path from section 1: React wires the Action through real form semantics (`FormData`, POST) instead of a JS-only `onSubmit`, so the same code degrades to a plain HTML form ([[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]], [[19 - DOM and Browser APIs/08 - Forms and FormData|FormData]]).

### Conditional context read with `use()` in a reusable component

A `<Tooltip>` from your design system optionally integrates with an app-level `PopoverManagerContext` — but must also work standalone. With `useContext`, the hook runs unconditionally and you branch on the result; with `use`, you can skip the read entirely when a prop opts out.

```jsx
function Tooltip({ standalone = false, children }) {
  if (standalone) return <BasicTooltip>{children}</BasicTooltip>;  // early return...
  const manager = use(PopoverManagerContext);                      // ...then a legal context read
  return <ManagedTooltip manager={manager}>{children}</ManagedTooltip>;
}
```

Legal because `use` doesn't rely on positional hook state (section 2) — the one hook-order rule it's exempt from. Same shape works for promises: `use(commentsPromise)` inside a branch suspends only when that branch renders, letting one component serve both eager and lazy data paths ([[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense]]).

## 7. Interview Answer

Short answer:

> React 19's headline is Actions: async functions in transitions (and `<form action>`) that auto-manage pending, error, and optimistic state. `useActionState` wraps a mutation and gives you `[state, action, isPending]`; `useOptimistic` shows the expected result immediately and auto-reverts on failure; `use()` reads a promise (suspending) or context during render, and can be called conditionally. Plus `ref` as a prop, `<Context>` as provider, and native metadata/stylesheet support.

Deeper answer:

> The React Compiler (stable 1.0, Oct 2025) auto-inserts memoization at build time, so in compiler-enabled apps most manual `useMemo`/`useCallback` become unnecessary — but it's a performance tool that only works when components follow the Rules of React (pure render, no mutation), which is why understanding referential equality and purity matters more, not less. Manual memoization survives for non-compiler codebases, effect-dependency stability the compiler can't infer, and reasoning about genuinely expensive computation, which the compiler doesn't make cheaper.

## 8. Practice

1. <details><summary>What three things does an Action manage automatically that you used to write by hand?</summary>Pending state (auto true at start, resets when the final update commits), error handling (errors surface to Error Boundaries and optimistic values auto-revert), and — with `<form action>` — form submission wiring including resetting uncontrolled inputs on success. `useActionState` also threads the action's return value as state and gives `isPending`, replacing the manual `useState` trio.</details>

2. <details><summary>Why can `use()` be called conditionally when `useContext` cannot?</summary>Regular hooks must be called unconditionally in the same order every render because React tracks them by call order. `use` is special-cased in the renderer to not rely on positional hook state, so it's legal after early returns or inside branches — e.g., reading context only when a prop is non-null. It still must be called during render (like hooks), just without the ordering constraint.</details>

3. <details><summary>In a React Compiler-enabled project, a teammate removes all `useMemo`/`useCallback`. When is that safe and when will it bite?</summary>Safe: for memoization whose only purpose was re-render avoidance / referential stability of props to children — the compiler reinserts equivalent memoization. Bites when: the project isn't fully compiler-covered (opt-outs, unsupported files); a value's stability was relied on by a `useEffect` dependency to control *effect* firing (the compiler optimizes rendering, not your effect semantics); or a `useMemo` guarded a genuinely expensive computation whose cost you still need to reason about. Verify the compiler is enabled and the components follow the rules before stripping.</details>

4. <details><summary>When is `useOptimistic` the wrong choice?</summary>When the operation fails often (users see flicker/revert churn), when showing an unconfirmed state is misleading or unsafe (payment succeeded, order placed, irreversible actions), or when there's no meaningful "expected" intermediate value. Optimistic UI trades correctness-of-the-moment for perceived speed; for high-stakes or failure-prone mutations, show a pending state and wait for server confirmation instead.</details>

## Related Notes

- [[21 - React Internals and Patterns/04 - State Batching and Updater Queues|State Batching and Updater Queues]]
- [[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense and Concurrent Features]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]
- [[01 - Roadmap|Roadmap]]
