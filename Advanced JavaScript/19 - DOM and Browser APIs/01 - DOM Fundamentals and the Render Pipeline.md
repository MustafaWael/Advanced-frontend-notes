---
tags: [javascript, dom, rendering, performance]
module: "19 - DOM and Browser APIs"
priority: must-know
status: not-started
aliases: [Render Pipeline, Reflow, Layout Thrashing]
---

# DOM Fundamentals and the Render Pipeline

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can explain DOM vs CSSOM vs render tree, define reflow vs repaint precisely, and diagnose layout thrashing from code.
- Production signal: you can find and fix a forced synchronous layout in a real component instead of guessing at "performance tips".
- Dependencies: [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]], [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]

## Source Anchors

- [MDN - Document Object Model](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model)
- [web.dev - Rendering performance](https://web.dev/articles/rendering-performance)
- [web.dev - Avoid large, complex layouts and layout thrashing](https://web.dev/articles/avoid-large-complex-layouts-and-layout-thrashing)
- [HTML Living Standard - Event loop processing model](https://html.spec.whatwg.org/multipage/webappapis.html#event-loop-processing-model)
- [CSSOM View Module](https://www.w3.org/TR/cssom-view-1/)

## 1. Concept

The DOM is a live, in-memory tree of node objects that the browser builds from HTML and exposes to JavaScript. It is not the HTML text, and it is not what you see on screen. What you see is the result of a pipeline:

1. Parse HTML → DOM tree.
2. Parse CSS → CSSOM.
3. DOM + CSSOM → render tree (only visible boxes; `display: none` nodes are absent).
4. Layout (a.k.a. reflow): compute geometry — position and size of every box.
5. Paint: fill in pixels for each box (text, colors, borders, shadows) into layers.
6. Composite: draw the layers to the screen in order, on the GPU where possible.

JavaScript sits before this pipeline: it mutates the DOM/CSSOM, and the browser later runs the affected pipeline stages during the rendering step of the event loop.

### Your JavaScript never becomes the styling

Worth being precise about, because it removes the last bit of magic from "how does JS change the page":

```js
el.style.marginLeft = '10px';
```

1. That assignment compiles to a `StaNamedProperty` bytecode like any other property write ([[02 - JavaScript Runtime Foundations/09 - Bytecode Dispatch and Tier-Up|Bytecode Dispatch and Tier-Up]]).
2. `style` is not a plain object. Looking `marginLeft` up on its hidden class finds not a data field but an **accessor** — a struct holding a raw C++ function pointer.
3. That pointer targets Blink code generated from `CSSStyleDeclaration.idl` **at Chrome build time** and compiled by Clang, months before you typed the line. V8 sets up registers per the platform calling convention and issues an ordinary `call`.
4. The C++ parses `"10px"` into a `CSSPrimitiveValue`, stores it in the element's inline style, and sets a dirty bit. Everything after that is stages 3–6 above, all in C++.

> [!tip] The JS→browser boundary is not a special mechanism
> It is an ordinary function call across a code-generated glue layer. The same is true of every DOM API, `fetch`, and `console.log`. This is also why `MutationObserver` isn't "watching" anything: inside the C++ function that removes a child node there is a literal branch — *if this document has observers registered, append a record to their queue*. The bookkeeping is hand-written into the mutation code. Nothing observes; things announce. See [[19 - DOM and Browser APIs/06 - Observers|Observers]].

## 2. Why It Matters

- Almost every frontend performance problem that isn't network-related lives in this pipeline.
- React, Vue, and friends are abstractions *over* the DOM — their performance stories (batched updates, virtual DOM diffing) only make sense if you know what raw DOM mutation costs.
- "Reflow vs repaint" and "layout thrashing" are standard senior interview probes because they separate people who have profiled real UIs from people who memorized listicles.

## 3. Accurate Mechanism: Reflow vs Repaint vs Composite

Different mutations dirty different pipeline stages:

| You change | Pipeline stages that rerun | Cost |
| --- | --- | --- |
| Geometry (`width`, `font-size`, adding nodes, `display`) | Layout → Paint → Composite | Highest |
| Visuals only (`color`, `background`, `box-shadow`, `visibility`) | Paint → Composite | Medium |
| Compositor-only (`transform`, `opacity`) | Composite | Lowest |

Key mechanism details:

- Layout is not per-element in the worst case: changing one element's size can invalidate ancestors and siblings, so the browser may recompute large subtrees.
- The browser is lazy. Style and layout invalidations are queued and normally resolved once, during the rendering opportunity after your task and its microtasks finish. Mutating the DOM 100 times in one task usually costs one layout, not 100.
- That laziness breaks when you *read* a layout-dependent property (`offsetHeight`, `getBoundingClientRect()`, `scrollTop`, `getComputedStyle(...)` for geometry) while layout is dirty. The browser must answer accurately, so it runs layout synchronously, inside your JavaScript. This is a **forced synchronous layout**.

> [!warning] Layout thrashing
> Alternating write → read → write → read in a loop forces a fresh synchronous layout on every iteration. This is the single most common DOM performance bug and it hides easily inside helper functions that "just measure something".

## 4. Mental Model

Think of the browser as an accountant who batches paperwork: you can drop as many change requests as you want in the inbox and they get processed once at the end of the day. But every time you ask "what's the current balance?", the accountant has to stop and process the whole inbox immediately to answer correctly. Interleave questions with change requests and you make the accountant process the inbox over and over.

## 5. Real Frontend Example: Layout Thrashing, Traced

Buggy version — equalize card heights in a grid:

```js
function equalizeCardHeights(cards) {
  cards.forEach((card) => {
    const height = card.offsetHeight;      // READ  (forces layout if dirty)
    card.style.height = `${height + 16}px`; // WRITE (dirties layout)
  });
}
```

Trace with 50 cards:

1. Iteration 1: layout is clean, `offsetHeight` is cheap. Write dirties layout.
2. Iteration 2: `offsetHeight` finds layout dirty → browser runs synchronous layout for the document. Write dirties it again.
3. Iterations 3–50: same. Result: ~49 forced synchronous layouts in one task. On a large page each layout can take several milliseconds — this loop alone can blow the frame budget many times over.

Production-safe fix — batch reads, then batch writes:

```js
function equalizeCardHeights(cards) {
  // Phase 1: all reads. Layout runs at most once.
  const heights = cards.map((card) => card.offsetHeight);

  // Phase 2: all writes. Layout is dirtied but resolved once, before next paint.
  cards.forEach((card, i) => {
    card.style.height = `${heights[i] + 16}px`;
  });
}
```

Tradeoff: read/write separation makes code less "locally obvious" — the measurement and the mutation are no longer adjacent, and you hold intermediate arrays. In larger apps this batching discipline is why libraries like FastDOM, and frameworks that schedule DOM work internally, exist. Often the better fix is *removing the need to measure*: this particular problem is solved in pure CSS with grid/flexbox (`align-items: stretch`), which is both faster and simpler.

> [!tip] Prefer compositor-only animation
> Animate `transform` and `opacity` instead of `top/left/width/height`. Compositor-only changes skip layout and paint entirely, so they stay smooth even while the main thread is busy. This is why `transform: translateX(...)` beats animating `left`.

## 6. How This Connects to React

React does not save you from this pipeline; it schedules around it.

- React batches state updates and commits DOM mutations together, which naturally groups writes.
- But any `useLayoutEffect` that reads geometry runs synchronously after DOM mutation and before paint — a measurement there can force layout, which is sometimes exactly what you want (tooltip positioning) and sometimes a hidden cost.
- A `ResizeObserver` or [[19 - DOM and Browser APIs/06 - Observers|IntersectionObserver]] is often the production-grade alternative to manual measurement loops.

## 7. Common Bugs and Edge Cases

- Reading `getBoundingClientRect()` inside a `scroll` handler on every event: scroll handlers fire at high frequency; combine with a write and you thrash on every scroll tick. Use `IntersectionObserver` or throttle with `requestAnimationFrame`.
- `getComputedStyle(el).height` forces layout just like `offsetHeight` when layout is dirty — "it's just reading a style" is false for geometry-dependent properties.
- `display: none` removes an element from the render tree (no box, no layout cost), while `visibility: hidden` keeps its box (participates in layout, skips paint). Toggling `display` is a layout change; toggling `visibility` is paint-only.
- Appending nodes in a loop directly into the live DOM is fine *if* you don't read layout between appends; the browser batches. `DocumentFragment` helps most when code you don't control might read in between.

## Real-World Use Cases

### FLIP animation for kanban card reordering

A board reorders cards when one is dragged. Animating `top`/`margin` reruns layout every frame; the FLIP technique measures **F**irst and **L**ast positions, then animates only the inverted `transform`.

```js
function flipMove(cards, reorderDOM) {
  const first = new Map(cards.map((c) => [c, c.getBoundingClientRect()])); // batched reads
  reorderDOM();                                                            // batched writes
  cards.forEach((card) => {
    const f = first.get(card);
    const l = card.getBoundingClientRect(); // one layout for all reads here
    card.animate(
      [{ transform: `translate(${f.x - l.x}px, ${f.y - l.y}px)` }, { transform: "none" }],
      { duration: 200, easing: "ease-out" }
    );
  });
}
```

Works because reads and writes stay in separate phases (two layouts total, not one per card), and the animation itself is `transform` — compositor-only, no layout or paint per frame.

### Tooltip positioning in `useLayoutEffect`

A design-system tooltip must measure its trigger and flip above/below depending on viewport space — *before* the user sees a wrongly-placed frame.

```jsx
useLayoutEffect(() => {
  const trigger = triggerRef.current.getBoundingClientRect(); // forced layout — intentional
  const tip = tipRef.current.getBoundingClientRect();
  const flip = trigger.bottom + tip.height > window.innerHeight;
  tipRef.current.style.transform =
    `translateY(${flip ? -tip.height - 8 : trigger.height + 8}px)`;
}, [open]);
```

This is the *legitimate* forced synchronous layout: `useLayoutEffect` runs after DOM mutation and before paint, so measuring here is exactly the mechanism's purpose — just keep all reads grouped before the write.

> [!tip]
> If the tooltip only needs to react to size changes over time, a `ResizeObserver` ([[19 - DOM and Browser APIs/06 - Observers|Observers]]) replaces repeated manual measurement.

### Reading-progress bar without scroll jank

A blog shows a top progress bar tracking scroll position. The naive version writes `bar.style.width` on every scroll event — a geometry write on the hottest input path.

```js
let ticking = false;
window.addEventListener("scroll", () => {
  if (ticking) return;
  ticking = true;
  requestAnimationFrame(() => {
    const progress = window.scrollY / (document.documentElement.scrollHeight - innerHeight);
    bar.style.transform = `scaleX(${progress})`; // compositor-only write
    ticking = false;
  });
}, { passive: true });
```

`width` writes dirty layout dozens of times per second; `transform: scaleX()` skips layout *and* paint, and the `requestAnimationFrame` gate aligns the write with the rendering opportunity ([[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]).

## 8. Interview Answer

Short answer:

> The browser turns DOM and CSSOM into a render tree, then runs layout (geometry), paint (pixels), and compositing. Reflow means layout reruns — that's geometry changes. Repaint means only paint reruns — visual-only changes. `transform` and `opacity` can skip both and run on the compositor.

Deeper answer:

> The browser batches style and layout invalidations and resolves them once per rendering opportunity. But layout-dependent reads like `offsetHeight` or `getBoundingClientRect` on a dirty layout force a synchronous layout inside JavaScript. Interleaving reads and writes in a loop — layout thrashing — forces layout per iteration. The fix is separating read and write phases, or eliminating measurement via CSS or observers.

## 9. Practice

1. <details><summary>A dropdown animates its `top` property and stutters while a table renders. Why, and what's the fix?</summary>Animating `top` dirties layout every frame, and layout runs on the main thread, which is busy rendering the table. Switch to `transform: translateY(...)` — compositor-only, so it can stay smooth off the main thread. If the element needs `position` for stacking, keep `top: 0` static and move it entirely with transforms.</details>

2. <details><summary>Predict the number of layouts: a loop over 20 elements does `el.style.width = el.parentElement.offsetWidth / 2 + "px"`.</summary>Roughly 20 forced synchronous layouts. Each iteration reads `offsetWidth` (forcing layout because the previous iteration's write dirtied it), then writes. First iteration's read may be free if layout was clean. Fix: read the parent width(s) first into an array, then write all widths.</details>

3. <details><summary>Why is `visibility: hidden` sometimes preferred over `display: none` for elements that toggle frequently?</summary>`display: none` removes the box from the render tree, so toggling it back triggers layout for the affected subtree (and possibly ancestors). `visibility: hidden` keeps the box in layout, so toggling only requires paint/composite work. Tradeoff: the hidden element still occupies space and participates in layout cost while hidden.</details>

4. <details><summary>Where does the browser actually run layout relative to your event handler code?</summary>Normally after the task and its microtasks complete, during the "update the rendering" step of the event loop — at most once per rendering opportunity (~per frame). Exception: a forced synchronous layout runs immediately, inside your handler, when you read geometry while layout is dirty.</details>

## Related Notes

- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
- [[19 - DOM and Browser APIs/06 - Observers|Observers]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[01 - Roadmap|Roadmap]]
