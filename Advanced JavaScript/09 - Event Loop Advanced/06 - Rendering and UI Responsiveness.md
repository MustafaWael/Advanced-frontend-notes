---
tags: [javascript, event-loop, rendering-and-ui-responsiveness]
module: "09 - Event Loop Advanced"
priority: must-know
status: not-started
---

# Rendering and UI Responsiveness

## Maturity Target

- Priority: #must-know
- Study time: 110-150 minutes
- Interview signal: you can connect event-loop scheduling to paint, input delay, long tasks, layout, and INP.
- Production signal: you know how to reduce jank with measurement, chunking, virtualization, workers, and render-aware scheduling.
- Dependencies: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]], [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]

## Source Anchors

- [web.dev: Optimize long tasks](https://web.dev/articles/optimize-long-tasks)
- [web.dev: Interaction to Next Paint](https://web.dev/articles/inp)
- [MDN PerformanceLongTaskTiming](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceLongTaskTiming)
- [MDN requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)
- [MDN Web Workers API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API)
- [HTML Living Standard: Event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)

## 1. Concept

UI responsiveness means the browser can respond to input and present the next visual update quickly.

The main thread often has to coordinate:

- event handlers
- JavaScript execution
- style recalculation
- layout
- paint
- compositing
- framework rendering

If JavaScript occupies the main thread for too long, input and paint wait.

## 2. Why It Matters

Users experience event-loop problems as:

- typing lag
- delayed click feedback
- spinner not appearing
- scroll jank
- frozen page
- delayed route transition
- animation stutter
- slow autocomplete

These are not abstract interview puzzles. They directly affect Core Web Vitals such as Interaction to Next Paint (INP).

## 3. Accurate Mechanism

Rendering cannot happen while JavaScript is running on the main thread. After a task finishes and microtasks drain, the browser may update rendering if needed.

Long tasks matter because a task that runs too long blocks:

- input event handling
- timer callbacks
- promise microtask completion after that task
- rendering opportunities
- visible feedback from state changes

web.dev and Chrome tooling commonly treat tasks over 50ms as long tasks for responsiveness analysis.

## 4. Mental Model

Responsive apps give the browser frequent chances to:

```txt
handle input
run high-priority work
calculate layout
paint
```

The goal is not "never do heavy work." The goal is to place heavy work at the right time, reduce it, split it, cache it, or move it away from the main thread.

## 5. Real Frontend Bug: Large Filter On Every Keypress

### Problem

```jsx
function ProductSearch({ products }) {
  const [query, setQuery] = useState("");

  const visibleProducts = products
    .filter(product => {
      return product.name.toLowerCase().includes(query.toLowerCase());
    })
    .sort((a, b) => a.price - b.price);

  return (
    <>
      <input value={query} onChange={event => setQuery(event.target.value)} />
      <ProductList products={visibleProducts} />
    </>
  );
}
```

### Bugs

- filtering and sorting run on every render
- `sort` mutates `products`
- large lists make typing lag
- rendering every row compounds the cost

### Fix

```jsx
function ProductSearch({ products }) {
  const [query, setQuery] = useState("");
  const deferredQuery = useDeferredValue(query);

  const visibleProducts = useMemo(() => {
    const normalized = deferredQuery.trim().toLowerCase();

    return products
      .filter(product => {
        return product.name.toLowerCase().includes(normalized);
      })
      .toSorted((a, b) => a.price - b.price);
  }, [products, deferredQuery]);

  return (
    <>
      <input value={query} onChange={event => setQuery(event.target.value)} />
      <VirtualizedProductList products={visibleProducts} />
    </>
  );
}
```

### Tradeoff

`useMemo` helps only when inputs are stable and the computation is expensive enough to matter. For very large datasets, also consider server-side search, indexing, pagination, workers, or virtualization.

## 6. Spinner Not Appearing

```js
setLoading(true);
doExpensiveWork();
setLoading(false);
```

The browser cannot paint the loading state while `doExpensiveWork` is running.

Possible fixes:

```js
setLoading(true);

setTimeout(() => {
  doExpensiveWork();
  setLoading(false);
}, 0);
```

Or:

```js
setLoading(true);

requestAnimationFrame(() => {
  doExpensiveWork();
  setLoading(false);
});
```

Better for truly heavy work:

```js
worker.postMessage({ type: "start", payload });
```

Choose based on whether the work is small enough to delay, chunk, or move.

## 7. Layout Thrashing

### Problem

```js
for (const card of cards) {
  card.style.width = "200px";
  console.log(card.offsetHeight);
}
```

### Bug

The code alternates DOM writes and layout reads. The browser may be forced to recalculate layout repeatedly.

### Fix

Batch writes and reads:

```js
for (const card of cards) {
  card.style.width = "200px";
}

requestAnimationFrame(() => {
  const heights = cards.map(card => card.offsetHeight);
  console.log(heights);
});
```

Even better: use CSS layout, ResizeObserver, or fewer manual measurements where possible.

## 8. Chunking Work

```js
async function processInChunks(items, processItem) {
  let index = 0;

  while (index < items.length) {
    const deadline = performance.now() + 8;

    while (index < items.length && performance.now() < deadline) {
      processItem(items[index]);
      index += 1;
    }

    await new Promise(resolve => setTimeout(resolve, 0));
  }
}
```

This gives the event loop chances to handle other work between chunks. It is a pragmatic browser pattern, not a substitute for reducing total work.

## 9. Web Worker Boundary

Use a worker when:

- the work is CPU-heavy
- it does not need direct DOM access
- serialization cost is acceptable
- the user benefits from keeping the main thread responsive

```js
const worker = new Worker("/search-worker.js");

worker.postMessage({
  type: "filter",
  query,
  products,
});

worker.addEventListener("message", event => {
  setResults(event.data.results);
});
```

> [!tip] Tradeoff
> workers add architecture, data transfer cost, and debugging complexity. They are powerful when the main-thread cost is the real bottleneck.

## 10. DevTools Workflow

1. Record the slow interaction in Performance.
2. Look for long tasks and red long-task indicators.
3. Expand the main thread flame chart.
4. Identify whether time is JavaScript, style, layout, paint, or rendering framework work.
5. Reproduce with CPU throttling.
6. Apply one fix at a time.
7. Re-record and compare.

Do not guess whether memoization, chunking, workers, or virtualization helped. Verify.

## 11. Production Fix Menu

| Problem | Candidate fix |
| --- | --- |
| huge render list | virtualization, pagination |
| expensive filtering | memoization, debounce, server search, worker |
| long CPU loop | chunking, worker, reduce algorithmic cost |
| slow click feedback | yield before non-urgent work, reduce handler work |
| animation jank | `requestAnimationFrame`, CSS transforms, less layout |
| layout thrashing | batch DOM reads/writes, use CSS, avoid forced layout |
| stale background work | cancellation, request ids |
| too much JS on startup | code split, defer non-critical scripts |

## 12. Interview Answer

**Short version:** Rendering and input share the browser main thread with JavaScript. Long tasks and endless microtasks delay input and paint, so responsive apps reduce, split, schedule, or move work.

**Strong version:** The browser can update rendering only when JavaScript yields and microtasks drain. If one event handler or render calculation runs for hundreds of milliseconds, user input and paint wait. This affects metrics like INP. In production, I would measure in DevTools, identify whether the cost is JavaScript, layout, paint, or framework rendering, then choose the right fix: reduce work, memoize, debounce, virtualize, chunk with task boundaries, align visual work with `requestAnimationFrame`, or move CPU work to a worker.

## 13. Common Mistakes

- Adding `async` to heavy CPU code and expecting responsiveness to improve.
- Using `queueMicrotask` to yield before paint.
- Rendering thousands of rows without virtualization.
- Sorting or filtering large arrays on every keypress without measurement.
- Alternating DOM reads and writes in a loop.
- Using `useMemo` as a cure-all without stable inputs.
- Moving work to a worker when serialization cost is larger than the work.
- Optimizing without a Performance recording.

## 14. Practice

1. Record a slow input interaction and identify the long task.
2. Refactor a 20,000-row render to use virtualization or pagination.
3. Split a CPU loop into chunks.
4. Move a pure computation to a Web Worker.
5. Fix a DOM read/write loop that causes forced layout.
6. Explain how INP relates to the event loop.

## Real-World Use Cases

### Attributing a bad INP score to the guilty handler

Field data says INP is 480ms on the orders page, but every interaction feels fine on your machine. The `web-vitals` attribution build names the element and the phase that ate the time.

```js
import { onINP } from "web-vitals/attribution";

onINP(({ value, attribution }) => {
  reportMetric("inp", {
    value,
    element: attribution.interactionTarget, // e.g. "#bulk-approve-button"
    inputDelay: attribution.inputDelay,     // main thread busy BEFORE handler
    processing: attribution.processingDuration, // your handler's cost
    presentationDelay: attribution.presentationDelay, // render/paint after
  });
});
```

The three phases map directly onto the event loop: input delay is a long task ahead of yours, processing is your task, presentation delay is the rendering step waiting for the checkpoint to end. See [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]].

> [!tip] The phase tells you the fix
> High input delay: someone else's long task (third-party scripts, hydration). High processing: your handler. High presentation delay: too much DOM/render work after the state change. Measure before choosing.

### Yielding to input while building a search index

Opening the command palette builds a fuzzy-search index over 30,000 records. Done in one loop, the palette's own opening animation and the user's first keystrokes freeze.

```ts
async function buildIndex(records: Record[]) {
  const index = new FuzzyIndex();

  for (const [i, record] of records.entries()) {
    index.add(record);

    if (i % 500 === 0) {
      if ("scheduler" in window && scheduler.yield) {
        await scheduler.yield(); // continuation is prioritized over other tasks
      } else {
        await new Promise(resolve => setTimeout(resolve, 0));
      }
    }
  }
  return index;
}
```

Each `await` ends the current task, letting the browser run pending input tasks and paint before the loop resumes. `scheduler.yield()` improves on the `setTimeout` fallback by putting the continuation at the *front* of the task queue instead of the back.

### Spinners that survive main-thread jank

A JS-driven spinner (advancing rotation in `requestAnimationFrame`) freezes exactly when you need it — during the long task it is supposed to mask. A CSS transform animation keeps running because the compositor thread animates it without the main thread.

```css
.spinner {
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); } /* transform + opacity: compositor-friendly */
}
```

`requestAnimationFrame` callbacks are part of the rendering step, which the event loop cannot reach while a task runs — but compositor-driven `transform`/`opacity` animations live outside that loop entirely. Same reason animating `height` or `top` janks: those need main-thread layout every frame.

> [!warning] This hides jank, it does not fix it
> A spinning spinner over a frozen page still drops the user's clicks. Use it as honest feedback while you also chunk or offload the work — see [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]].

## Related Notes

- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]
- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[09 - Event Loop Advanced/09 - Node.js Event Loop vs Browser|Node.js Event Loop vs Browser]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[01 - Roadmap|Roadmap]]
- [[90 - Labs/01 - Event Loop and Rendering Profiler Lab|Event Loop and Rendering Profiler Lab]] — make these mechanics visible by building the profiler
