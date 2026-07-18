---
tags: [javascript, event-loop, event-loop-overview]
module: "09 - Event Loop Advanced"
priority: must-know
status: not-started
---

# Event Loop Overview

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can separate ECMAScript jobs from the browser event loop and explain run-to-completion without folklore.
- Production signal: you can diagnose why a UI freezes, why a callback ran later, and why rendering did not happen when expected.
- Dependencies: [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]], [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]]

## Source Anchors

- [HTML Living Standard: Event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)
- [MDN Microtask guide](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide)
- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [web.dev: Optimize long tasks](https://web.dev/articles/optimize-long-tasks)

## 1. Concept

The event loop is the host scheduling model that coordinates JavaScript execution, tasks, microtasks, and rendering opportunities.

In browser terms, the useful mental order is:

```txt
run one task
drain microtasks
maybe update rendering
pick another task
repeat
```

Important accuracy point: the browser event loop is defined by the HTML Living Standard. ECMAScript defines language execution, agents, and jobs such as promise reactions. The host connects those jobs to its event loop.

## 2. Why It Matters

Frontend bugs often come from timing, not syntax:

- a spinner does not appear before heavy work starts
- a promise callback runs before a timer
- a user click is delayed by a long task
- a stale request updates state after a newer request
- recursive microtasks prevent paint
- a layout read/write loop makes scrolling janky

Strong mid-level frontend developers can connect these bugs to the scheduling model and choose a fix that matches the user's experience.

## 3. Accurate Mechanism

Keep these layers separate:

| Layer | Owns | Examples |
| --- | --- | --- |
| ECMAScript | language execution and jobs | call stack, promises, async functions |
| HTML/browser | event loop, tasks, microtask checkpoints, rendering | timers, events, network callbacks, paint |
| Node.js | its own host event loop implementation | timers, I/O, `process.nextTick` |
| Framework | scheduling on top of the host | React rendering, transitions, effects |
| Application | user intent and data lifetime | "this result is still current" |

> [!tip] Name the host environment
> Browser event loop summaries are useful, but they are not universal across every JavaScript host. Interview answers should name when you are talking about browsers.

## 4. Run-To-Completion

JavaScript runs one piece of script to completion before another task can run on the same event loop.

```js
let count = 0;

button.addEventListener("click", () => {
  count += 1;
  count += 1;
  count += 1;
});
```

> [!warning] Long work blocks everything
> Another click handler will not interrupt this handler halfway through. This reduces shared-memory race complexity inside one task, but it also means long work blocks everything else on the main thread.

## 5. Processing Model

A simplified browser cycle:

```txt
1. Choose and run one task
   Examples: script start, click handler, timer callback

2. Run a microtask checkpoint
   Examples: promise reactions, queueMicrotask, mutation observers
   The microtask queue drains completely, including microtasks added by microtasks.

3. Maybe update rendering
   requestAnimationFrame callbacks, style, layout, paint, composite

4. Repeat
```

> [!warning] Rendering is not guaranteed
> "Maybe update rendering" matters. The browser decides when rendering is needed and possible. It cannot paint while JavaScript is still running.

## 6. Code Output Baseline

```js
console.log("A");

setTimeout(() => console.log("timer"), 0);

Promise.resolve().then(() => console.log("promise"));

queueMicrotask(() => console.log("microtask"));

console.log("B");
```

Expected browser and Node output for this example:

```txt
A
B
promise
microtask
timer
```

Why:

- `A` and `B` are synchronous.
- The promise reaction and `queueMicrotask` callback are microtasks, in enqueue order.
- The timer callback is a later task.

## 7. Real Frontend Bug: Spinner Does Not Paint

### Problem

```js
function handleExportClick() {
  setExporting(true);
  buildHugeCsv(rows);
  setExporting(false);
}
```

### Bug

> [!warning] Spinner never paints
> `buildHugeCsv` blocks the current task. The browser does not get a rendering opportunity between `setExporting(true)` and the heavy work, so the spinner may never visibly appear.

### Fix Options

Yield before non-urgent work:

```js
async function handleExportClick() {
  setExporting(true);

  await new Promise(resolve => setTimeout(resolve, 0));

  try {
    buildHugeCsv(rows);
  } finally {
    setExporting(false);
  }
}
```

Better for very heavy work:

```js
// Move CPU-heavy export generation off the main thread.
const worker = new Worker("/csv-worker.js");
worker.postMessage({ rows });
```

### Tradeoff

> [!tip] Yielding is not speed
> Yielding with a timer gives the browser a chance to handle other work, but it does not make the heavy computation cheaper. For large CPU work, chunking, workers, streaming, or server-side generation can be better.

## 8. Browser vs Node Caution

The browser event loop model and Node.js event loop model overlap, but they are not identical. Browser interview questions usually focus on:

- call stack
- tasks
- microtasks
- timers
- rendering

Node adds phases and APIs such as `process.nextTick`, `setImmediate`, and libuv I/O behavior. Unless the question explicitly says Node, answer for the browser and state that host environments differ.

## 9. Debugging Notes

- Use Chrome DevTools Performance to find long tasks.
- Record with CPU throttling to reproduce user-device delays.
- Look for tasks longer than 50ms when diagnosing responsiveness.
- Add logs around sync work, promise callbacks, timers, and rendering hooks.
- Use Network throttling for request timing bugs, but Performance for main-thread timing bugs.
- If UI does not update before work, check whether JavaScript yielded to the browser.

## 10. Production Tradeoffs

- Microtasks are great for same-turn consistency but can starve rendering if abused.
- Timers create task boundaries, but exact timing is not guaranteed.
- `requestAnimationFrame` aligns visual work with frames, but it is not available in SSR.
- Workers move CPU work off the main thread, but add serialization and architecture cost.
- Framework schedulers help, but they do not make your own long synchronous work disappear.

## 11. Interview Answer

**Short version:** The browser event loop runs one task, drains microtasks, may update rendering, and then repeats. It is a host model from the HTML spec; ECMAScript defines promise jobs and language execution.

**Strong version:** JavaScript in one browser event loop is run-to-completion: a task runs fully before another task starts. After a task, the browser performs a microtask checkpoint, so promise callbacks and `queueMicrotask` callbacks run before timers or the next user event task. Rendering can happen only when the browser gets a rendering opportunity, which JavaScript can delay with long tasks or endless microtasks. In production, this explains why long computations freeze input and paint, why promises beat timers in output questions, and why yielding or moving work to a worker can improve responsiveness.

## 12. Common Mistakes

- Saying the browser event loop is defined by ECMAScript.
- Calling every async callback a microtask.
- Assuming `setTimeout(fn, 0)` runs immediately.
- Forgetting microtasks drain completely before the next task.
- Forgetting rendering cannot happen while JavaScript is running.
- Assuming `async/await` makes CPU work non-blocking.
- Applying Node-specific event loop rules to browser interview questions without saying so.

## 13. Practice

1. Explain the difference between ECMAScript jobs and the browser event loop.
2. Predict the output of the baseline code in this note.
3. Explain why a spinner may not paint before heavy synchronous work.
4. Record a long task in DevTools Performance and identify what blocked input.
5. Explain why a Web Worker can help CPU work but not DOM work.

## Real-World Use Cases

### Long-task monitoring in production

A checkout flow feels fine on dev machines, but users on mid-range phones report dead clicks. Field monitoring with `PerformanceObserver` catches the tasks that block them.

```js
new PerformanceObserver(list => {
  for (const entry of list.getEntries()) {
    if (entry.duration > 100) {
      reportMetric("long-task", {
        duration: entry.duration,
        page: location.pathname,
      });
    }
  }
}).observe({ type: "longtask", buffered: true });
```

This works because of run-to-completion: every task in this report held input, timers, and paint hostage for its whole duration.

> [!tip] Alert on the tail
> Chrome flags tasks over 50ms. Alert on the 95th percentile, not the average — jank lives in the tail. See [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]].

### `await` does not unblock CPU work

A dashboard downloads a large report and the tab freezes after the network finishes. The `await` yields during the fetch, but the parse is one synchronous task.

```ts
async function loadReport() {
  const response = await fetch("/api/report"); // main thread free here
  const text = await response.text();
  const rows = parseCsv(text); // 800ms sync — the freeze is HERE
  setRows(rows);
}
```

`await` yields only at promise boundaries; `parseCsv` runs to completion inside one task, so no input or paint happens until it returns. Chunk it or move it to a worker — see [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]].

### Run-to-completion as a free lock

A cart handler reads, validates, and writes shared state with no locking, and it is safe — no other task can interleave with it.

```js
function addToCart(item) {
  const existing = cart.items.find(entry => entry.sku === item.sku);
  if (existing) existing.quantity += 1; // nothing can run between these lines
  else cart.items.push({ ...item, quantity: 1 });
  persistCart(cart); // state is consistent at this point
}
```

> [!warning] The guarantee ends at `await`
> Run-to-completion holds only within one task. The moment you `await` inside the handler, other tasks can run and mutate `cart` before you resume. See [[08 - Async JavaScript/04 - Async Await|Async Await]].

## Related Notes

- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[09 - Event Loop Advanced/04 - Timers|Timers]]
- [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[01 - Roadmap|Roadmap]]
