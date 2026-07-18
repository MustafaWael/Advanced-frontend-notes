---
tags: [javascript, event-loop, tasks-vs-microtasks]
module: "09 - Event Loop Advanced"
priority: must-know
status: not-started
aliases: [Microtasks, Macrotasks]
---

# Tasks vs Microtasks

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can classify common callbacks and explain why microtasks run before timers.
- Production signal: you know when microtasks help consistency and when they harm rendering responsiveness.
- Dependencies: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]], [[08 - Async JavaScript/02 - Promises|Promises]]

## Source Anchors

- [HTML Living Standard: Event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [MDN Microtask guide](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide)
- [MDN queueMicrotask](https://developer.mozilla.org/en-US/docs/Web/API/Window/queueMicrotask)
- [MDN setTimeout](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout)
- [MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)

## 1. Concept

A task is a unit of work the host schedules for the event loop. A microtask is a higher-priority continuation that runs after the current task finishes and before the browser moves to another task or rendering opportunity.

Common browser tasks:

- initial script execution
- timer callbacks
- user event callbacks
- network event callbacks
- message events

Common browser microtasks:

- promise reactions
- `queueMicrotask` callbacks
- mutation observer callbacks

## 2. Why It Matters

This is the core of many event-loop questions:

```js
setTimeout(() => console.log("task"), 0);
Promise.resolve().then(() => console.log("microtask"));
console.log("sync");

// sync
// microtask
// task
```

This is the classic interview ordering question. Tick-by-tick:

1. **Task: run the script to completion.** `setTimeout` hands its callback to the host, which queues a **task**. `.then` registers a reaction on an already-fulfilled promise, which queues a **microtask** — a [[09 - Event Loop Advanced/03 - Promise Jobs|promise job]]. `"sync"` logs.
2. **Microtask checkpoint.** The queue drains: `"microtask"` logs.
3. **Next task.** The event loop picks the timer callback: `"task"` logs. Even at a `0` delay it can never beat the checkpoint, because the checkpoint runs before the loop selects another task — see [[09 - Event Loop Advanced/04 - Timers|Timers]].

In production, the same rule affects whether rendering, user input, and timers get a chance to run.

## 3. Accurate Mechanism

After a task completes, the browser runs a microtask checkpoint. That checkpoint drains the microtask queue completely. If a microtask queues another microtask, the new microtask runs in the same checkpoint before the browser moves on.

This means microtasks can starve tasks and rendering:

```js
function spin() {
  queueMicrotask(spin);
}

spin();
```

> [!warning] Recursive microtasks freeze pages
> Do not run that in a real page. It keeps adding microtasks, so the browser cannot proceed to timers, input tasks, or rendering.

## 4. Mental Model

Tasks are "come back later."

Microtasks are "finish this turn's follow-up before anything else."

> [!tip] Pick the right boundary
> Use a microtask when you need to restore internal consistency after current synchronous code. Use a task boundary when the browser needs a chance to process input or paint.

## 5. Code Output: Enqueue Order

```js
console.log("start");

Promise.resolve().then(() => {
  console.log("promise 1");
  queueMicrotask(() => console.log("nested microtask"));
});

queueMicrotask(() => console.log("microtask 1"));

Promise.resolve().then(() => console.log("promise 2"));

setTimeout(() => console.log("timer"), 0);

console.log("end");
```

Expected output:

```txt
start
end
promise 1
microtask 1
promise 2
nested microtask
timer
```

Why:

- the first three microtasks are queued in order
- `nested microtask` is added to the end while microtasks are draining
- the timer waits for the microtask checkpoint to finish

## 6. Same-Turn Consistency Example

> [!example] Batched store notifications
> Frameworks and libraries sometimes use microtasks to batch notifications after synchronous changes finish.

```js
class Store {
  listeners = new Set();
  value = 0;
  flushQueued = false;

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  setValue(nextValue) {
    this.value = nextValue;

    if (!this.flushQueued) {
      this.flushQueued = true;

      queueMicrotask(() => {
        this.flushQueued = false;

        for (const listener of this.listeners) {
          listener(this.value);
        }
      });
    }
  }
}

const store = new Store();
store.subscribe(value => console.log(value));

store.setValue(1);
store.setValue(2);
store.setValue(3);

// 3
```

The listener runs once after the current synchronous turn and sees the final value.

## 7. Real Frontend Bug: Microtask Starvation

### Problem

```js
function processQueue(items) {
  const item = items.shift();

  if (!item) return;

  processItem(item);

  queueMicrotask(() => processQueue(items));
}
```

### Bug

> [!warning] Checkpoint holds everything hostage
> For a large queue, this can keep the browser inside the microtask checkpoint for too long. Timers, input events, and rendering wait.

### Fix

Use task boundaries or frame boundaries for large work:

```js
function processQueue(items) {
  const deadline = performance.now() + 8;

  while (items.length > 0 && performance.now() < deadline) {
    processItem(items.shift());
  }

  if (items.length > 0) {
    setTimeout(() => processQueue(items), 0);
  }
}
```

For visual work:

```js
function processNextFrame(items) {
  requestAnimationFrame(() => {
    for (let count = 0; count < 100 && items.length > 0; count += 1) {
      processItem(items.shift());
    }

    if (items.length > 0) {
      processNextFrame(items);
    }
  });
}
```

## 8. Production Decision Points

Use microtasks for:

- post-sync cleanup
- batching internal notifications
- promise continuations
- keeping a state invariant before the next event

Use tasks or frames for:

- long loops
- work that should not block paint
- yielding to input
- chunked processing
- visual updates

## 9. Browser vs Node Caution

Browser microtasks and Node microtasks are similar for promises and `queueMicrotask`, but Node also has `process.nextTick`, which has its own priority behavior. Browser-focused interview answers should avoid bringing in `process.nextTick` unless asked.

## 10. Interview Answer

**Short version:** A task is host-scheduled work like a timer or event callback. A microtask is a continuation like a promise reaction that runs after the current task and before the next task.

**Strong version:** In the browser, the event loop runs one task to completion, then performs a microtask checkpoint. Promise reactions and `queueMicrotask` callbacks run in that checkpoint, and the queue drains completely, including microtasks queued by other microtasks. Only after that can the browser move on to another task or rendering opportunity. This is why promises run before `setTimeout(..., 0)`. The production risk is microtask starvation: if you recursively queue microtasks for too long, the browser cannot handle input or paint.

## 11. Common Mistakes

- Calling `setTimeout` a microtask.
- Thinking `queueMicrotask` and `Promise.then` have different priority.
- Forgetting microtasks queued by microtasks run in the same checkpoint.
- Using microtasks to process large queues.
- Assuming microtasks give the browser a chance to paint.
- Applying Node `process.nextTick` behavior to browser questions.

## 12. Practice

1. Predict the output of the enqueue order example.
2. Explain why recursive `queueMicrotask` can freeze a page.
3. Write a batching example that uses one microtask.
4. Rewrite a microtask loop into chunked `setTimeout` work.
5. Explain when `requestAnimationFrame` is better than `queueMicrotask`.

## Real-World Use Cases

### MutationObserver batching in a rich text editor

An editor plugin needs to react to DOM changes — but a single paste can produce hundreds of mutations. `MutationObserver` callbacks are microtasks, so the browser hands you all mutations from the current task in one call, after the synchronous work finishes.

```js
const observer = new MutationObserver(mutations => {
  // one callback per turn, not per mutation
  recalculateOutline(editorRoot);
  markDocumentDirty();
});

observer.observe(editorRoot, { childList: true, subtree: true, characterData: true });
```

This is the "same-turn follow-up" property of microtasks used deliberately: the callback sees the final DOM state of the turn, never a half-applied edit. See [[19 - DOM and Browser APIs/06 - Observers|Observers]].

### Flushing microtasks in unit tests

A test triggers a promise-based mock, then asserts immediately — and fails, because the `.then` reaction has not run yet. The assertion executes in the same synchronous turn that queued the microtask.

```ts
test("shows the username after load", async () => {
  render(<Profile />);
  fireEvent.click(screen.getByText("Load"));

  // expect(...) here fails: the mock's .then has not run

  await Promise.resolve(); // yield once — pending microtasks drain first
  expect(screen.getByText("mustafa")).toBeInTheDocument();
});
```

`await Promise.resolve()` works because the test's continuation is queued *behind* the already-pending reactions in the same FIFO microtask queue.

> [!warning] One flush is not always enough
> Each `await` yields once. A chain of three `.then`s needs three flushes — or one real task boundary (`await new Promise(r => setTimeout(r, 0))`), which drains every checkpoint in between. See [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]] for why chains interleave.

### Microtasks run between DOM event listeners

Two listeners on the same button: the first updates state through a promise, the second reports analytics. For a real user click, each listener is invoked as its own callback, so the microtask checkpoint runs **between** them — the analytics listener sees the updated state. For a programmatic `button.click()`, dispatch is synchronous inside the current task, so no checkpoint runs until both listeners finish.

```js
button.addEventListener("click", () => {
  Promise.resolve().then(() => (state.submitted = true));
});

button.addEventListener("click", () => {
  trackClick({ submitted: state.submitted });
  // real click: true — programmatic click(): false
});
```

> [!warning] Tests lie about ordering here
> `element.click()` in a test keeps the stack non-empty across both listeners, so microtasks stay queued. Code that "works in the browser" can order differently under test for exactly this reason.

## Related Notes

- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[09 - Event Loop Advanced/04 - Timers|Timers]]
- [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[01 - Roadmap|Roadmap]]
