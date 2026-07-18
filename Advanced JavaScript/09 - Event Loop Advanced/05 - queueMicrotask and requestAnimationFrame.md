---
tags: [javascript, event-loop, queuemicrotask-and-requestanimationframe]
module: "09 - Event Loop Advanced"
priority: important
status: not-started
---

# queueMicrotask and requestAnimationFrame

## Maturity Target

- Priority: #important
- Study time: 90-120 minutes
- Interview signal: you can explain why microtasks and animation frames are different scheduling tools.
- Production signal: you use microtasks for same-turn consistency and animation frames for visual work before paint.
- Dependencies: [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]], [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]

## Source Anchors

- [MDN queueMicrotask](https://developer.mozilla.org/en-US/docs/Web/API/Window/queueMicrotask)
- [MDN Microtask guide](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide)
- [MDN requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestAnimationFrame)
- [MDN cancelAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/Window/cancelAnimationFrame)
- [HTML Living Standard: Animation frames](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#animation-frames)
- [web.dev: Optimize long tasks](https://web.dev/articles/optimize-long-tasks)

## 1. Concept

`queueMicrotask(callback)` schedules a microtask.

`requestAnimationFrame(callback)` schedules a callback for the browser's rendering cycle before the next paint.

They are not interchangeable:

```txt
queueMicrotask        same event-loop turn, before rendering
requestAnimationFrame rendering opportunity, before paint
setTimeout           later task
```

## 2. Why It Matters

Frontend work often needs a specific timing boundary:

- "finish this internal state update before the next event" -> microtask
- "measure/write DOM before the next paint" -> `requestAnimationFrame`
- "let input and paint happen before more work" -> task/frame boundary
- "run animation work every frame" -> `requestAnimationFrame`

Using the wrong boundary creates flaky measurements, janky animations, or starved rendering.

## 3. Official Mechanism

`queueMicrotask`:

- queues a callback in the microtask queue
- runs after the current task
- runs before the next task
- runs before the browser gets to render
- shares the same queue ordering behavior as promise reactions

`requestAnimationFrame`:

- queues a callback for the next rendering opportunity
- runs before paint
- passes a high-resolution timestamp
- can be canceled with `cancelAnimationFrame`
- typically pauses or slows when the page is not visible, depending on browser policy
- does not exist in server-side JavaScript environments

## 4. Mental Model

Microtask:

```txt
make state consistent before anything else happens
```

Animation frame:

```txt
do visual work at the moment the browser is preparing a frame
```

Task:

```txt
come back later and let the browser breathe
```

## 5. Code Output: Same Microtask Queue

```js
console.log("start");

queueMicrotask(() => console.log("microtask 1"));

Promise.resolve().then(() => console.log("promise"));

queueMicrotask(() => console.log("microtask 2"));

console.log("end");
```

Expected:

```txt
start
end
microtask 1
promise
microtask 2
```

`queueMicrotask` and promise reactions share the microtask queue in enqueue order.

## 6. Microtask Use Case: Batched Notifications

```js
class BatchedEmitter {
  listeners = new Set();
  queued = false;
  latestValue = null;

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  emit(value) {
    this.latestValue = value;

    if (this.queued) return;

    this.queued = true;

    queueMicrotask(() => {
      this.queued = false;

      for (const listener of this.listeners) {
        listener(this.latestValue);
      }
    });
  }
}
```

This avoids notifying subscribers for every intermediate synchronous write.

## 7. Microtask Bug: No Paint Opportunity

### Problem

```js
setLoading(true);

queueMicrotask(() => {
  runExpensiveWork();
  setLoading(false);
});
```

### Bug

> [!warning] Microtasks run before paint
> The microtask queue drains before the browser gets a rendering opportunity, so scheduling heavy work with `queueMicrotask` (or a resolved promise) still blocks the paint of a loading state. Use a task (`setTimeout`) or a frame (`requestAnimationFrame`) boundary when you need the UI to paint first.

### Fix

Use a task or frame boundary before heavy visual work:

```js
setLoading(true);

setTimeout(() => {
  runExpensiveWork();
  setLoading(false);
}, 0);
```

For heavy CPU work, prefer chunking or a worker.

## 8. requestAnimationFrame For Visual Work

```js
let handle = 0;
let x = 0;

function animate(timestamp) {
  x += 2;
  box.style.transform = `translateX(${x}px)`;

  if (x < 300) {
    handle = requestAnimationFrame(animate);
  }
}

handle = requestAnimationFrame(animate);

function stop() {
  cancelAnimationFrame(handle);
}
```

Why rAF:

- browser chooses a frame-aligned time
- callback receives a frame timestamp
- animation can pause when the page is hidden
- work is aligned with paint

## 9. DOM Measurement Timing

Use rAF when a DOM read/write should align with the next frame:

```js
function scrollToNewItem(item) {
  item.classList.add("is-new");

  requestAnimationFrame(() => {
    const rect = item.getBoundingClientRect();

    if (rect.top < 0 || rect.bottom > window.innerHeight) {
      item.scrollIntoView({ block: "nearest" });
    }
  });
}
```

Avoid mixing many writes and reads in a loop:

```js
for (const item of items) {
  item.style.width = "200px";
  console.log(item.offsetWidth);
}
```

This can force repeated layout work. Batch writes, then reads, or use rAF boundaries.

## 10. React Cleanup For rAF

```jsx
function ProgressBar({ target }) {
  const ref = useRef(null);

  useEffect(() => {
    let frameId = 0;
    let current = 0;

    function tick() {
      current += (target - current) * 0.15;

      if (ref.current) {
        ref.current.style.transform = `scaleX(${current})`;
      }

      if (Math.abs(target - current) > 0.001) {
        frameId = requestAnimationFrame(tick);
      }
    }

    frameId = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(frameId);
  }, [target]);

  return <div ref={ref} />;
}
```

Always cancel loops on unmount or dependency change.

## 11. Server-Side Rendering Guard

`requestAnimationFrame` is a browser API.

```js
if (typeof window !== "undefined") {
  requestAnimationFrame(() => {
    // browser-only visual work
  });
}
```

In React, browser-only rAF code usually belongs in `useEffect` or `useLayoutEffect`, not during server render.

## 12. Production Decision Table

| Need | Better tool | Why |
| --- | --- | --- |
| run after current sync code, before next task | `queueMicrotask` | same-turn consistency |
| handle promise continuation | promise / `await` | built-in promise jobs |
| run after browser gets another task turn | `setTimeout` | yields to event loop |
| animate or measure before paint | `requestAnimationFrame` | frame-aligned |
| run low-priority work when browser has spare time | `requestIdleCallback` if supported | idle scheduling |
| heavy CPU work | Web Worker | off main thread |

## 13. Interview Answer

**Short version:** `queueMicrotask` runs a callback in the microtask queue before the next task and before paint. `requestAnimationFrame` runs before the next paint opportunity and is for visual frame work.

**Strong version:** `queueMicrotask` is for same-turn follow-up work. It shares ordering with promise reactions and drains before timers or rendering, so it can starve the page if abused. `requestAnimationFrame` is not a task or microtask in the usual interview model; it is part of the browser rendering cycle and runs before paint with a frame timestamp. Use microtasks for consistency, rAF for animations and DOM reads/writes aligned with paint, and task boundaries or workers when work should not block input and rendering.

## 14. Common Mistakes

- Using microtasks to make a spinner paint.
- Recursively scheduling microtasks and starving the event loop.
- Using `setTimeout(fn, 16)` for animation instead of rAF.
- Forgetting to cancel rAF loops on unmount.
- Running rAF code during SSR.
- Assuming rAF runs while a tab is hidden the same way it runs when visible.
- Treating rAF as a promise microtask.

## 15. Practice

1. Predict the output of the same-queue example.
2. Explain why a microtask can prevent a spinner from painting.
3. Build a tiny rAF animation loop with cleanup.
4. Explain when DOM measurement belongs in rAF.
5. Decide whether each case needs microtask, timer, rAF, idle callback, or worker.

## Related Notes

- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/04 - Timers|Timers]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]
- [[01 - Roadmap|Roadmap]]
