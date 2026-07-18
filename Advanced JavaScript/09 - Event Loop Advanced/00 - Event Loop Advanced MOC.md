---
tags: [javascript, moc, event-loop]
module: "09 - Event Loop Advanced"
priority: must-know
status: not-started
---

# Event Loop Advanced MOC

This module teaches the browser scheduling model: run-to-completion tasks, microtask checkpoints, timers, and rendering opportunities, plus how ECMAScript promise jobs plug into the host event loop. It unlocks the output-order questions interviewers love (tasks vs microtasks, promise chains, `await` resumption) and the production bugs behind them: spinners that never paint, timer drift, overlapping intervals, and microtask starvation that freezes rendering. Finish it and you can both predict console output and choose the right scheduling boundary for real UI work.

## Prerequisites

- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]
- [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]
- [[08 - Async JavaScript/01 - Sync vs Async JavaScript|Sync vs Async JavaScript]]
- [[08 - Async JavaScript/02 - Promises|Promises]]

## Reading Order

1. [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]] — the task/microtask/render cycle and run-to-completion, the frame everything else hangs on.
2. [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]] — the ordering rule behind almost every output question.
3. [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]] — why `.then` never runs synchronously and how chains interleave.
4. [[09 - Event Loop Advanced/04 - Timers|Timers]] — minimum delays, drift, cleanup, and the async `setInterval` overlap trap.
5. [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]] — picking the right scheduling boundary for consistency vs visual work.
6. [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]] — long tasks, layout thrashing, INP, and the fix menu for jank.
7. [[09 - Event Loop Advanced/07 - Code Output Questions|Code Output Questions]] — drills that pressure-test your tracing under interview conditions.
8. [[09 - Event Loop Advanced/08 - Event Loop Checklist|Event Loop Checklist]] — the active-review gate before you call this module done.
9. [[09 - Event Loop Advanced/09 - Node.js Event Loop vs Browser|Node.js Event Loop vs Browser]] — libuv phases, `setImmediate`/`process.nextTick`, and why SSR timing differs (extension topic).

## You're Done When

- [ ] I can explain the browser cycle — run one task, drain microtasks completely, maybe render — and why run-to-completion means long work blocks input and paint.
- [ ] I can classify common callbacks (timers, events, promise reactions, `queueMicrotask`, rAF) and predict output order for mixed sync/microtask/timer code, including nested microtasks and chain interleaving.
- [ ] I can trace promise jobs: executor runs synchronously, handlers run as microtasks, each `.then` returns a new promise, and a `catch` that returns normally converts failure into success.
- [ ] I can use timers safely: treat delay as a minimum, clean up in React effects, avoid stale closures and lost `this`, and rewrite async polling with recursive `setTimeout`.
- [ ] I can choose the right boundary — microtask for same-turn consistency, task to yield, `requestAnimationFrame` for frame-aligned visual work, worker for heavy CPU.
- [ ] I can diagnose responsiveness bugs (unpainted spinner, microtask starvation, layout thrashing, long tasks) with DevTools Performance and verify fixes by measuring.
- [ ] I can state clearly which behavior is browser host model vs ECMAScript vs Node-specific in an interview answer.

## Related Notes

- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/08 - Event Loop Checklist|Event Loop Checklist]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[01 - Roadmap|Roadmap]]
