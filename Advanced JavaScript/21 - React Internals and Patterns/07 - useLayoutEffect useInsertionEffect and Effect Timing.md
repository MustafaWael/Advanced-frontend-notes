---
tags: [react, internals, effects, timing]
module: "21 - React Internals and Patterns"
priority: important
status: not-started
aliases: [Effect Timing, useLayoutEffect, useInsertionEffect]
---

# useLayoutEffect, useInsertionEffect and Effect Timing

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can lay out the full timeline — render → commit/mutation → layout effects → paint → passive effects — and place each hook on it.
- Production signal: you pick `useEffect` vs `useLayoutEffect` deliberately (flicker vs blocking) instead of switching hooks until the warning disappears.
- Dependencies: [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]], [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]

## Source Anchors

- [react.dev - useEffect](https://react.dev/reference/react/useEffect)
- [react.dev - useLayoutEffect](https://react.dev/reference/react/useLayoutEffect)
- [react.dev - useInsertionEffect](https://react.dev/reference/react/useInsertionEffect)
- [react.dev - You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)

## 1. The Timeline

For a single update, React and the browser proceed in this fixed order:

1. **Render phase** — call components, diff. Pure, interruptible. (No DOM, no effects.)
2. **Commit — mutation** — React mutates the DOM to match the new tree. **`useInsertionEffect`** fires around this point: its only *guaranteed* ordering is **before any layout effect** — refs are not attached yet, and per the docs it may run before *or* after the DOM update, so never rely on the DOM's state inside it. It exists for CSS-in-JS libraries to inject `<style>` rules before layout is read.
3. **`useLayoutEffect`** fires — DOM is mutated but **not yet painted**; you can measure layout and synchronously mutate again with no visible flicker. Blocks paint.
4. **Browser paints** — the user finally sees the frame.
5. **`useEffect`** (passive) fires — *after* paint, asynchronously.

Cleanup functions run in the mirror order before the next run/unmount. The single most important fact: **`useLayoutEffect` runs before paint (can block it); `useEffect` runs after paint (never blocks it).**

## 2. Why It Matters

- The choice between the two is a real UX/perf tradeoff, and "just use useLayoutEffect to fix the flicker" without understanding the paint-blocking cost is a junior move.
- SSR interacts with this: `useLayoutEffect` doesn't run on the server and warns during hydration if used for layout that affects first paint — a common Next.js console warning.

## 3. useEffect vs useLayoutEffect — The Decision

Use **`useEffect`** (the default, 95% of cases): data fetching, subscriptions, logging, timers, syncing to non-visual external systems. It runs after paint, so it never delays what the user sees. If your effect updates state that changes layout, the user *might* see a one-frame intermediate state — usually invisible.

Use **`useLayoutEffect`** only when you must **read layout and change it before the user sees the first frame**: measuring an element to position a tooltip/popover, reading scroll position, measuring text to size a container, preventing a visible jump. It's synchronous and blocks paint, so heavy work here directly costs frame time.

```jsx
// Tooltip that must appear correctly positioned on the FIRST painted frame
useLayoutEffect(() => {
  const { top, left } = anchorRef.current.getBoundingClientRect();
  setPos(flipIfOffscreen(top, left));   // measured + repositioned before paint → no flash
}, [open]);
```

> [!warning] useLayoutEffect + SSR
> `useLayoutEffect` never runs during server rendering, so layout it would perform is absent from the server HTML — React warns during hydration. If the measurement only matters on the client, either guard it, use `useEffect` and accept a possible one-frame adjustment, or use the `useIsomorphicLayoutEffect` pattern (layout on client, effect on server). Don't silence the warning by ignoring it — decide whether first-paint correctness actually matters here.

## 4. useInsertionEffect — Narrow and Special

`useInsertionEffect` fires *before* layout effects, specifically so CSS-in-JS libraries (Emotion, styled-components internals) can inject styles before React reads layout — otherwise a layout effect measuring an element could read pre-styled dimensions. Its other documented quirks: you can't update state from it, refs aren't attached yet, its ordering relative to the DOM mutation is unspecified, and cleanup/setup interleave per component instead of running in two waves. You almost never write it in app code; it exists for library authors. Knowing *why* it exists (style injection must precede layout reads) is the interview-relevant part.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a dropdown menu that should open upward when there's no room below.

Buggy version with `useEffect`:

```jsx
function Dropdown({ open }) {
  const menuRef = useRef(null);
  const [dropUp, setDropUp] = useState(false);
  useEffect(() => {                       // runs AFTER paint
    if (!open) return;
    const rect = menuRef.current.getBoundingClientRect();
    setDropUp(rect.bottom > window.innerHeight);
  }, [open]);
  return open ? <ul ref={menuRef} className={dropUp ? "up" : "down"}>…</ul> : null;
}
```

Trace the flicker: on open, React paints the menu *downward* (initial `dropUp=false`) → user sees it appear below, possibly clipped by the viewport → then `useEffect` measures, sets `dropUp=true` → re-render → menu jumps upward. A visible flash-and-jump.

Production-safe fix — measure before paint:

```jsx
useLayoutEffect(() => {                    // runs BEFORE paint
  if (!open) return;
  const rect = menuRef.current.getBoundingClientRect();
  setDropUp(rect.bottom > window.innerHeight);
}, [open]);
```

Now the measurement and the corrective re-render happen before the browser paints, so the user only ever sees the menu in its final position.

Tradeoffs: `useLayoutEffect` blocks paint while it (and its triggered synchronous re-render) runs — fine for a quick `getBoundingClientRect`, costly if the effect does heavy work or triggers a large re-render. It also doesn't run on the server, so SSR emits the un-flipped markup (acceptable here since the menu is client-interactive and closed initially). The deeper fix that avoids JS measurement entirely is CSS anchor positioning / `position-try` where supported — no effect, no flicker, no paint-block — a good "know the platform" follow-up.

## 6. Interview Answer

Short answer:

> The reliable order is: render, commit, `useLayoutEffect`, paint, then `useEffect`. `useInsertionEffect` runs before layout effects for CSS-in-JS, but React explicitly does **not** guarantee whether it runs before or after the DOM mutation, so never place it at a fixed DOM-timing step. `useLayoutEffect` blocks paint and is for measurements that must be correct on the first frame; `useEffect` runs after paint and is the default for everything non-visual.

Deeper answer:

> Because `useLayoutEffect` runs before paint, it prevents flicker when you must read layout and re-render (tooltips, drop-direction, scroll restoration) — at the cost of blocking the frame, so heavy work there hurts. It doesn't run during SSR and warns on hydration, so client-only measurement needs guarding or the isomorphic-layout-effect pattern. `useInsertionEffect` exists one step earlier for CSS-in-JS to inject styles before layout is read, so measurements aren't taken against unstyled elements — library territory, not app code.

## 7. Practice

1. <details><summary>Place these on the timeline: DOM mutation, paint, useEffect, useLayoutEffect, useInsertionEffect.</summary>Commit mutates the DOM → useLayoutEffect (post-mutation, pre-paint) → paint → useEffect (async, after paint). useInsertionEffect's only guaranteed position is *before any layout effect* — the docs explicitly say it may run before or after the DOM update and refs aren't attached yet, so place it as "before layout effects, DOM-update order unspecified" rather than at a fixed step. Bonus signal: knowing that nuance is exactly what separates reciting a diagram from having read the contract.</details>

2. <details><summary>A measurement effect works locally but throws "useLayoutEffect does nothing on the server" in Next.js. Why, and options?</summary>SSR renders to a string with no DOM/layout, so React can't run layout effects server-side and warns. Options: (1) if first-paint correctness is needed only client-side, use the `useIsomorphicLayoutEffect` pattern (useLayoutEffect in browser, useEffect on server); (2) switch to `useEffect` and accept a possible one-frame adjustment if the visual jump is tolerable; (3) render a stable placeholder server-side and measure on the client. Choose based on whether the un-measured first frame is acceptable.</details>

3. <details><summary>When would moving code from useEffect to useLayoutEffect be a mistake?</summary>When the work is non-visual or heavy: data fetching, logging, subscriptions, or expensive computation. Putting these in useLayoutEffect blocks paint for no visual benefit, making the UI feel slower — the user waits on work they'd never have seen anyway. useLayoutEffect is justified only when the effect must read/adjust layout before the first painted frame to avoid a visible flicker or jump.</details>

## Related Notes

- [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]]
- [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[01 - Roadmap|Roadmap]]
