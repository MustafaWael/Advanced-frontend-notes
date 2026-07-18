---
tags: [javascript, event-loop, event-loop-checklist]
module: "09 - Event Loop Advanced"
priority: must-know
status: not-started
---

# Event Loop Checklist

Use this as an active review. A checkbox is complete only when you can explain the idea, predict code output, connect it to a production bug, and choose a safer pattern without looking.

## Fast Track Order

1. [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
2. [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
3. [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
4. [[09 - Event Loop Advanced/04 - Timers|Timers]]
5. [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
6. [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
7. [[09 - Event Loop Advanced/07 - Code Output Questions|Code Output Questions]]

## Core Understanding

- [ ] I can explain that the browser event loop is a host model, not an ECMAScript-only feature.
- [ ] I can explain what ECMAScript promise jobs are.
- [ ] I can separate browser event-loop behavior from Node-specific behavior.
- [ ] I can explain run-to-completion.
- [ ] I can classify common callbacks as synchronous work, microtasks, tasks, or rendering callbacks.
- [ ] I can explain why promise reactions run before timers.
- [ ] I can explain why microtasks can starve rendering.
- [ ] I can explain why `setTimeout(fn, 0)` does not mean immediate.
- [ ] I can explain why rendering cannot happen while JavaScript is running.
- [ ] I can explain how long tasks affect user input and INP.

## Tasks And Microtasks

- [ ] I know examples of browser tasks: script start, click handlers, timer callbacks, message events.
- [ ] I know examples of microtasks: promise reactions, `queueMicrotask`, mutation observers.
- [ ] I know that microtasks drain completely after the current task.
- [ ] I know that microtasks queued by microtasks run in the same checkpoint.
- [ ] I know when a microtask is useful for same-turn consistency.
- [ ] I know when a task boundary is better for yielding.
- [ ] I can explain why recursive `queueMicrotask` can freeze a page.

## Promise Jobs

- [ ] I know the Promise executor runs synchronously.
- [ ] I know `.then` handlers run asynchronously.
- [ ] I know each `.then` returns a new promise.
- [ ] I can explain promise-chain interleaving.
- [ ] I can explain `await` resumption as promise-job scheduling.
- [ ] I can explain why a `catch` that returns normally converts failure into success.
- [ ] I can connect promise-job ordering to stale reads in app code.

## Timers

- [ ] I know timers are host APIs.
- [ ] I know timer delay is a minimum delay.
- [ ] I know sync work and microtasks can delay timer callbacks.
- [ ] I can clean up timers in React effects.
- [ ] I can avoid stale state inside timer callbacks.
- [ ] I can explain why async `setInterval` can overlap work.
- [ ] I can rewrite async polling with recursive `setTimeout`.
- [ ] I can implement debounce with timeout cleanup.
- [ ] I know timer callbacks can lose `this`.

## Rendering And Responsiveness

- [ ] I know `queueMicrotask` runs before paint.
- [ ] I know `requestAnimationFrame` runs before a paint opportunity.
- [ ] I can choose between `queueMicrotask`, `setTimeout`, `requestAnimationFrame`, idle callbacks, and workers.
- [ ] I can explain why a spinner may not appear before heavy work.
- [ ] I can identify layout thrashing from alternating DOM writes and reads.
- [ ] I can chunk long work.
- [ ] I can explain when a Web Worker is appropriate.
- [ ] I can use DevTools Performance to find long tasks.
- [ ] I know optimization should be verified with measurement.

## Code Output Drills

### Basic Ordering

```js
console.log("A");
setTimeout(() => console.log("B"), 0);
Promise.resolve().then(() => console.log("C"));
console.log("D");
```

Expected:

```txt
A
D
C
B
```

### Microtask Enqueue Order

```js
queueMicrotask(() => console.log("M1"));
Promise.resolve().then(() => console.log("P1"));
queueMicrotask(() => console.log("M2"));
```

Expected:

```txt
M1
P1
M2
```

### Promise Chain Interleaving

```js
Promise.resolve().then(() => console.log("A1")).then(() => console.log("A2"));
Promise.resolve().then(() => console.log("B1")).then(() => console.log("B2"));
```

Expected:

```txt
A1
B1
A2
B2
```

### Await Yields

```js
async function demo() {
  console.log("A");
  await 1;
  console.log("C");
}

demo();
console.log("B");
```

Expected:

```txt
A
B
C
```

### Timer Closure

```js
for (var i = 0; i < 3; i += 1) {
  setTimeout(() => console.log(i), 0);
}
```

Expected:

```txt
3
3
3
```

## Production Scenarios To Practice

- [ ] Fix a spinner that does not paint before heavy work.
- [ ] Refactor a recursive microtask queue into chunked tasks.
- [ ] Fix a leaking interval in a React component.
- [ ] Rewrite async polling to prevent overlapping requests.
- [ ] Replace timer-based animation with `requestAnimationFrame`.
- [ ] Batch DOM writes and reads to avoid layout thrashing.
- [ ] Use DevTools Performance to identify a long task.
- [ ] Decide whether to use memoization, virtualization, chunking, or a worker for a large list.
- [ ] Explain why code works in a tiny demo but feels slow with real data.

## Interview Prompts

1. Is the event loop defined by ECMAScript or the browser host?
2. What is run-to-completion?
3. What is the difference between a task and a microtask?
4. Why do promises run before timers?
5. Can microtasks block rendering?
6. Why does `setTimeout(fn, 0)` not run immediately?
7. What is the difference between `queueMicrotask` and `requestAnimationFrame`?
8. Why can `setInterval(async () => {}, 1000)` cause overlapping work?
9. Why might a loading spinner not appear before expensive JavaScript?
10. How would you debug a janky input field?

## Self-Review Rubric

| Level | What you can do |
| --- | --- |
| Junior | Predict simple promise vs timer output. |
| Growing mid-level | Trace nested microtasks, promise chains, timers, and async/await. |
| Strong mid-level | Connect scheduling to React effects, UI responsiveness, stale reads, and cleanup. |
| Senior signal | Diagnose long tasks, layout thrashing, rendering delays, worker boundaries, and host differences. |

## Related Notes

- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[09 - Event Loop Advanced/04 - Timers|Timers]]
- [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[09 - Event Loop Advanced/07 - Code Output Questions|Code Output Questions]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[01 - Roadmap|Roadmap]]
