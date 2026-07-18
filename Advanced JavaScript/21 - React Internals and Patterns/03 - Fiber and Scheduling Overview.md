---
tags: [react, internals, fiber, scheduling]
module: "21 - React Internals and Patterns"
priority: important
status: not-started
aliases: [Fiber, Lanes]
---

# Fiber and Scheduling Overview

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain at overview depth what Fiber enabled (interruptible rendering), what a "lane" is conceptually, and why the render phase can pause but commit can't.
- Production signal: you understand why a transition keeps the UI responsive during heavy renders — because you know rendering is schedulable work, not a blocking call.
- Dependencies: [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]], [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]

## Source Anchors

- [react.dev - Render and Commit](https://react.dev/learn/render-and-commit)
- [react.dev - startTransition](https://react.dev/reference/react/startTransition)
- [react.dev - useTransition](https://react.dev/reference/react/useTransition)
- [MDN - requestIdleCallback](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestIdleCallback) — the API React deliberately does **not** use (section 5)
- [React scheduler source — MessageChannel + 5ms time slice](https://github.com/facebook/react/blob/main/packages/scheduler/src/forks/Scheduler.js)

## 1. Concept

Before React 16, rendering was recursive and synchronous: once React started rendering a big tree, it ran to completion, blocking the main thread — a long task ([[09 - Event Loop Advanced/01 - Event Loop Overview|event loop]]) that froze input. **Fiber** is the reimplementation of React's core that made rendering *incremental and interruptible*.

A **fiber** is a plain JavaScript object — a unit of work — corresponding to a component instance (or DOM node) in the tree. Because the work is a traversable linked structure of these objects (with `child`, `sibling`, `return` links) rather than a call stack, React can:

- do a chunk of rendering work, then **yield to the browser** so input and paint can happen,
- **pause** a render, and later **resume** or **discard** it,
- keep a "work-in-progress" tree separate from the "current" (committed) tree, and swap them atomically at commit.

This is why the render phase is interruptible but commit is not: commit mutates the real DOM, which the user sees, so it must be atomic; render is just building a JS object tree, which is safe to throw away.

## 2. Why It Matters

- It's the substrate for every concurrent feature — transitions, `useDeferredValue`, Suspense streaming ([[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Concurrent Features]]). You can't reason about those without knowing rendering is schedulable.
- Interviewers ask about Fiber to gauge *calibration*: a strong mid/senior gives the overview (interruptible work units, priority lanes, double-buffered trees) and explicitly declines to recite internal field names — reciting `memoizedProps` trivia signals memorization, not understanding.

## 3. Lanes: Priority, Conceptually

Not all updates are equally urgent. Typing in an input must feel instant; re-rendering a huge filtered list off that keystroke can wait a beat. React models this with **lanes** — a priority system (implemented as bitmasks for fast set operations) that tags each update with an urgency:

- **Urgent / discrete** (clicks, typing, `setState` in an event handler by default): render ASAP.
- **Transition** (updates wrapped in `startTransition`): can be interrupted by urgent work and rendered in the background; if new urgent input arrives, the in-progress transition render is thrown away and restarted.

```jsx
const [isPending, startTransition] = useTransition();

function onChange(e) {
  setQuery(e.target.value);                 // urgent: keep the input responsive
  startTransition(() => setResults(filter(all, e.target.value))); // low priority: heavy, interruptible
}
```

Mechanism: React begins rendering the transition, but between fiber work-chunks it checks whether higher-priority work (another keystroke) has arrived; if so, it abandons the partial render and handles the keystroke first. The input never janks even though the list render is expensive.

> [!tip] Transitions don't make work cheaper — they make it interruptible
> `startTransition` doesn't speed up `filter()`; it reprioritizes it so urgent updates preempt it. If the filtering itself is genuinely heavy on the main thread, you still need memoization or a worker ([[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Workers]]). Concurrency is about *responsiveness ordering*, not raw speed.

## 4. Double Buffering

React keeps two trees: **current** (what's on screen) and **work-in-progress** (being built). Rendering populates the WIP tree; commit swaps it to become current in one step. This is what makes an aborted render harmless — the WIP tree is discarded and the current tree (on screen) was never touched. It's the same idea as graphics double-buffering: draw off-screen, flip when ready.

## 5. How React Yields — MessageChannel, Not requestIdleCallback

The browser ships an API that *sounds* purpose-built for this — `requestIdleCallback` — and React deliberately doesn't use it: it fires too infrequently and inconsistently across browsers, is throttled aggressively, and only hands you browser-declared idle time, while React wants to keep working whenever there's a free moment. Instead, React's scheduler posts a macrotask through a **`MessageChannel`** port and slices rendering into **~5ms chunks**: after each fiber unit of work it calls `shouldYield()`; if the slice is used up (or higher-priority work arrived), it stops, posts the next MessageChannel message, and lets the browser process input and paint before resuming. (`setTimeout(0)` wasn't an option either — nested timeouts get clamped to ~4ms, wasting most of each frame; a MessageChannel message fires immediately.)

> [!tip] Interview differentiator
> "React yields with `requestIdleCallback`" is a common wrong answer. Knowing it's a MessageChannel-driven ~5ms time slice with a `shouldYield` check between fiber units — and why rIC and `setTimeout` were rejected — signals you've actually looked at the scheduler rather than repeating folklore. React 19.2's DevTools Performance Tracks ([[21 - React Internals and Patterns/10 - React 19|React 19]]) now let you *watch* these slices and priorities in a profile.

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — heavy derived render on every keystroke:

```jsx
function ProductSearch({ all }) {          // all: 50k items
  const [query, setQuery] = useState("");
  const results = expensiveFilter(all, query);  // runs synchronously each render
  return (
    <>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <List items={results} />
    </>
  );
}
```

Trace: each keystroke → setState (urgent) → synchronous `expensiveFilter` over 50k + rendering thousands of list rows → a long task per character → the input lags behind the user's typing.

Production-safe fix — split urgency with a transition:

```jsx
function ProductSearch({ all }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(all);
  const [isPending, startTransition] = useTransition();

  function onChange(e) {
    const q = e.target.value;
    setQuery(q);                                   // urgent → input updates immediately
    startTransition(() => setResults(expensiveFilter(all, q))); // interruptible
  }
  return (
    <>
      <input value={query} onChange={onChange} />
      {isPending && <Spinner />}
      <List items={results} />
    </>
  );
}
```

Trace of the win: typing "phone" fires five keystrokes; each updates `query` instantly (input stays live) and schedules a transition render; React keeps abandoning the in-progress filter render as new keystrokes arrive, only completing the filter for the final settled value — the browser stays responsive throughout.

Tradeoff: the visible results now *lag* the input by design (stale results shown, with `isPending` feedback) — acceptable for search, wrong for something that must stay perfectly in sync. And if `expensiveFilter` is truly CPU-bound, transitions reduce jank but the work still hogs the thread when it runs; memoize the filter, virtualize the list, or offload to a worker for the real fix. Concurrency composes with those, it doesn't replace them.

## 7. Interview Answer

Short answer:

> Fiber is React's rewrite that turns rendering into interruptible units of work instead of a synchronous recursive call. React can render a chunk, yield to the browser for input and paint, then resume, pause, or discard the render — because the render phase only builds a JS tree. Commit stays synchronous and atomic since it mutates the real DOM.

Deeper answer:

> Updates carry a priority via lanes: urgent work (clicks, typing) preempts transition work (`startTransition`), and React abandons and restarts an in-progress low-priority render when urgent input arrives. It keeps a work-in-progress tree separate from the committed current tree and swaps atomically, so aborted renders are harmless. Crucially, transitions reorder work by responsiveness — they don't make the work cheaper, so heavy computation still needs memoization or a worker.

## 8. Practice

1. <details><summary>Why can React abort a render halfway through with no visible corruption, but never abort a commit?</summary>The render phase writes only to the off-screen work-in-progress fiber tree — a JS data structure the user can't see — so discarding it leaves the on-screen current tree untouched. The commit phase mutates the actual DOM the user is looking at; interrupting it would leave the UI in a half-updated, inconsistent state. Hence render = interruptible, commit = atomic/synchronous.</details>

2. <details><summary>A candidate says "Fiber makes React faster." Refine that.</summary>Fiber doesn't make rendering computationally cheaper — the same components run. It makes rendering *schedulable*: work can be sliced, prioritized, paused, and preempted, so the app stays *responsive* under load even though total work is similar (or slightly more, due to scheduling overhead). The benefit is perceived performance and the ability to keep urgent interactions smooth, not raw throughput.</details>

3. <details><summary>You wrap a state update in `startTransition` but the page still janks hard while it renders. What's the likely cause and fix?</summary>The rendering triggered by that update is genuinely main-thread-heavy (huge synchronous computation or rendering tens of thousands of nodes at once). Transitions make it interruptible but it still runs on the main thread in chunks; a single indivisible heavy computation blocks. Fixes: memoize/precompute the derived data, virtualize the list so only visible rows render, or move the computation to a worker. Then the transition keeps input smooth on top.</details>

## Related Notes

- [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]]
- [[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense and Concurrent Features]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]
- [[01 - Roadmap|Roadmap]]
