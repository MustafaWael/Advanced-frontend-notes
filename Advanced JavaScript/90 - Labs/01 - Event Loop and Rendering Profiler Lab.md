---
tags: [labs, event-loop, performance, rendering]
module: "90 - Labs"
priority: important
status: not-started
aliases: [profiler lab]
---

# Lab 01 — Event Loop and Rendering Profiler

Build a single-page playground that makes scheduling *visible*: you trigger tasks, microtasks, timers, rAF callbacks, and long blocking work — and the page itself shows you what that did to frame timing. Then you profile and fix the jank you created.

## Prerequisites

- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]] · [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and rAF]] · [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|Render Pipeline]] · [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]

## Build Brief

Plain Vite + TypeScript, no framework required (React optional). One page, three parts:

1. **A frame monitor.** A rAF loop tracking time between frames; render a rolling chart (a `<canvas>` bar per frame, red when > 50ms) plus a "longest frame in the last 5s" readout. Add a `PerformanceObserver` for `longtask` entries and log them to an on-page list with their durations.
2. **A control panel of schedulers.** Buttons that each enqueue work with a distinct mechanism, each appending a timestamped line to an on-page log: `setTimeout(0)`, `queueMicrotask`, `Promise.resolve().then`, `requestAnimationFrame`, `setInterval` spam (start/stop), a synchronous 200ms busy-loop, a "microtask storm" (a promise chain that re-queues itself 10,000 times), and a "chunked" version of the busy-loop that yields between slices (`setTimeout`/`scheduler.yield` where available).
3. **An animation victim.** A CSS-animated spinner *and* a JS-animated (rAF) progress bar, so you can see which schedulers freeze which animation.

## Acceptance Criteria

- [ ] Clicking "sync 200ms" visibly freezes the rAF progress bar and logs a long task ≈200ms; the CSS spinner behavior is observed and explained (compositor vs main thread).
- [ ] The log demonstrates ordering: sync line → microtask lines → task lines, matching your written prediction for at least three mixed sequences you design.
- [ ] The microtask storm freezes rendering *without* a single long `setTimeout` task — and you can explain why the frame monitor shows one giant frame ([[09 - Event Loop Advanced/02 - Tasks vs Microtasks|microtask checkpoint]]).
- [ ] The chunked busy-loop keeps every frame under ~50ms while completing the same total work, and the monitor proves it.
- [ ] The `longtask` observer catches everything the frame monitor flags as red, and you can articulate what each tool measures differently.

## Debugging Tasks (create, observe, fix)

1. **Interval leak**: start the `setInterval` spam, remove the stop button's handler (simulate the missing cleanup), reload — then instrument and prove the leak with DevTools ([[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|cleanup]]). Fix with proper teardown.
2. **Layout thrash**: make the frame monitor's chart update read `offsetWidth` and then write styles per bar in a loop; observe forced synchronous layout in the Performance panel ([[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|pipeline]]); fix by batching reads before writes.
3. **The 60fps lie**: throttle CPU 6× in DevTools and find what breaks first; fix the most expensive path.

## Testing Expectations

- Unit-test the chunking utility (given total work and slice budget, it yields ≥ expected times — inject a fake `now`) ([[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|fake timers]]).
- Unit-test the frame-stats reducer (rolling window, max tracking) as pure logic ([[24 - Testing and Quality/02 - Pure JavaScript Unit Tests|unit tests]]).

## Accessibility Expectations

- All controls are real `<button>`s with names; the log is a labeled region; frame-monitor colors are paired with text values ([[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|not color-only]]).
- The spinner/progress animations respect `prefers-reduced-motion` (the *monitoring* still works; the decorative motion stops).

## Performance and Security Considerations

- The monitor itself must be cheap: canvas drawing batched per frame, log capped (virtualize or trim old entries), no per-frame DOM churn — measure your measurer.
- `performance.now()` precision and `longtask` availability vary; feature-detect and degrade.

## Interview Questions (answer out loud after building)

1. Why did the microtask storm freeze the page when each individual microtask was fast? Which queue drains to exhaustion before rendering, and where do tasks differ?
2. Your chunked loop used `setTimeout(0)` — what latency does that add per slice and why? What does `scheduler.yield()` improve?
3. The CSS spinner kept animating during the busy-loop (or didn't — depending on properties). Which animations can the compositor run without the main thread, and what property choices does that dictate?
4. A PM says "the app feels laggy on scroll." Walk your measurement plan before naming any fix.

## Retrospective

Write one using [[98 - Vault Operations/Templates/Lab Retrospective Template|the template]]: what you predicted wrong, which mechanism names you reached for, what you'd now explain differently in [[09 - Event Loop Advanced/07 - Code Output Questions|code-output questions]].

## Related Notes

- [[09 - Event Loop Advanced/00 - Event Loop Advanced MOC|Event Loop Advanced MOC]]
- [[13 - Performance and Memory/00 - Performance and Memory MOC|Performance and Memory MOC]]
- [[90 - Labs/00 - Labs MOC|Labs MOC]]
