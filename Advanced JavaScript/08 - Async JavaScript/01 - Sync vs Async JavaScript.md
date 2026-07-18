---
tags: [javascript, async, sync-vs-async-javascript]
module: "08 - Async JavaScript"
priority: must-know
status: not-started
---

# Sync vs Async JavaScript

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can explain run-to-completion, host APIs, tasks, microtasks, and why async code does not block the main stack.
- Production signal: you can reason about loading states, stale results, UI responsiveness, and CPU work without hand-waving.
- Dependencies: [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]], [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]

## Source Anchors

- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [MDN Microtask guide](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide)
- [HTML Living Standard: Event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [MDN Worker](https://developer.mozilla.org/en-US/docs/Web/API/Worker)

## 1. Concept

Synchronous JavaScript runs now on the current call stack. Each step must finish before the next step can run.

Asynchronous JavaScript starts work whose result will be handled later. The current call stack continues, and the continuation runs later through a promise job, task, callback, or host API.

```js
console.log("A");

setTimeout(() => console.log("D"), 0);

Promise.resolve().then(() => console.log("C"));

console.log("B");

// A
// B
// C
// D
```

The important point: async changes *when* code resumes. It does not mean two normal JavaScript call stacks are executing at the same time in the same agent.

## 2. Why It Matters

Frontend applications are full of work that cannot finish instantly:

- network requests
- timers
- user input
- DOM events
- animations
- file reads
- image/video loading
- background data refresh
- server actions and route transitions

If all of this blocked the main JavaScript stack, the browser could not respond to clicks, type input, or paint updates while waiting. Async control flow keeps the UI responsive by letting slow host work complete later.

Async code also creates new production risks:

- stale responses can overwrite fresh state
- a loading flag can be set too late
- errors can become unhandled promise rejections
- CPU-heavy work can still freeze the UI even if wrapped in an `async` function
- promises can continue after a component unmounts unless you cancel or ignore obsolete work

## 3. Accurate Mechanism

Keep the layers separate:

| Layer | What it owns | Examples |
| --- | --- | --- |
| ECMAScript | language execution, promises, jobs, async functions | `Promise`, `await`, run-to-completion |
| Browser/host | web APIs, event loop integration, networking, timers | `fetch`, `setTimeout`, DOM events |
| Framework | rendering and lifecycle rules | React effects, Next.js server/client boundaries |
| Application | user intent and data lifetime | "this search result is still current" |

Key rules:

- JavaScript execution is run-to-completion: once a stack starts running, another callback does not interrupt it halfway.
- Promise reactions run as jobs/microtasks after the current synchronous work finishes.
- Browser tasks include timers, events, and other host callbacks.
- Microtasks are drained before the browser moves to the next task.
- Rendering is controlled by the browser and can be delayed by long JavaScript work.

## 4. Mental Model

Think of async JavaScript as "start now, continue later":

```txt
sync code starts
  start fetch / timer / promise continuation
sync code finishes
  microtasks run
  browser may render
  next task runs
```

`await` does not block the whole thread. It pauses the current async function and returns control to the caller. The rest of that async function becomes a continuation.

## 5. Code Output: Tasks And Microtasks

```js
console.log("start");

setTimeout(() => console.log("timeout"), 0);

Promise.resolve()
  .then(() => {
    console.log("promise 1");
  })
  .then(() => {
    console.log("promise 2");
  });

queueMicrotask(() => console.log("microtask"));

console.log("end");
```

Expected output:

```txt
start
end
promise 1
microtask
promise 2
timeout
```

Why:

- `start` and `end` are synchronous.
- The first promise handler and `queueMicrotask` are queued as microtasks.
- The second promise handler is queued after the first promise handler runs.
- `setTimeout` is a later task.

## 6. Async Does Not Mean Parallel CPU Work

```js
async function freezeUi() {
  const started = performance.now();

  while (performance.now() - started < 2000) {
    // Busy loop for 2 seconds.
  }

  return "done";
}

freezeUi();
console.log("scheduled");
```

> [!warning] Async does not unblock CPU work
> The function is `async`, but the loop still runs synchronously until it completes or reaches an `await`. The UI can freeze during the loop.

For CPU-heavy work, consider:

- smaller chunks with yielding
- `requestIdleCallback` for low-priority work where supported
- Web Workers for real off-main-thread computation
- server-side processing when appropriate

## 7. Real Frontend Bug: Loading State Set Too Late

### Problem

```jsx
function SaveButton({ save }) {
  const [saving, setSaving] = useState(false);

  async function handleClick() {
    await save();
    setSaving(true);
    setSaving(false);
  }

  return (
    <button disabled={saving} onClick={handleClick}>
      Save
    </button>
  );
}
```

### Bug

> [!warning] Loading state set after the work
> The async operation starts before the UI enters the saving state. A user can click again while the first request is already in flight. The code also sets `saving` to `true` after the request has finished, which is backwards.

### Fix

```jsx
function SaveButton({ save }) {
  const [saving, setSaving] = useState(false);

  async function handleClick() {
    if (saving) return;

    setSaving(true);

    try {
      await save();
    } finally {
      setSaving(false);
    }
  }

  return (
    <button disabled={saving} onClick={handleClick}>
      {saving ? "Saving..." : "Save"}
    </button>
  );
}
```

### Tradeoff

> [!tip] State guards have limits
> For very fast repeated clicks in the same render frame, a state variable may not update quickly enough to guard every duplicate event. Critical mutations should also use server-side idempotency, request deduplication, or a local ref guard.

## 8. Real Frontend Bug: Stale Search Results

### Problem

```js
async function onQueryChange(query) {
  const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
  const results = await response.json();
  setResults(results);
}
```

### Bug

> [!warning] Old response can win the race
> If the user types "r", then "re", then "rea", the request for "r" might finish last and overwrite the newer "rea" results.

### Fix Options

Use `AbortController` to cancel obsolete reads:

```js
let currentController;

async function onQueryChange(query) {
  currentController?.abort();

  const controller = new AbortController();
  currentController = controller;

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
      signal: controller.signal,
    });
    const results = await response.json();
    setResults(results);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") return;
    setError(error);
  }
}
```

Or ignore obsolete results by tracking the latest request id:

```js
let latestRequestId = 0;

async function onQueryChange(query) {
  const requestId = ++latestRequestId;
  const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
  const results = await response.json();

  if (requestId !== latestRequestId) return;
  setResults(results);
}
```

## 9. Debugging Notes

- Add logs before and after `await` to see where control yields.
- Use DevTools Network throttling to reproduce race conditions.
- Use the Performance panel to identify long tasks that block input and paint.
- Watch for unhandled promise rejection messages in the console.
- Put request identifiers in logs for search, autocomplete, and route changes.
- Separate "request started", "response received", "state applied", and "request ignored/aborted" in logs.

## 10. Production Tradeoffs

- Async keeps I/O from blocking the main stack, but CPU-heavy JS still blocks.
- `setTimeout(fn, 0)` means "run in a later task", not "run immediately."
- Promises do not provide cancellation by themselves.
- React effects need cleanup when async work can outlive the current render.
- Use server-side or cache-level deduplication for critical duplicate prevention.
- Keep async boundaries explicit: the caller should know whether a function returns a promise.

## Real-World Use Cases

### CSV import parsing in a Web Worker

An admin panel lets users import a 50MB CSV of products. Parsing it in an `async` function still freezes scrolling and typing for seconds, because parsing is CPU work on the main stack.

```js
// main thread
const worker = new Worker(new URL("./csv-parser.worker.js", import.meta.url));

worker.postMessage(file);
worker.onmessage = event => setRows(event.data.rows);

// csv-parser.worker.js
onmessage = async event => {
  const text = await event.data.text();
  postMessage({ rows: parseCsv(text) }); // heavy loop runs off the main thread
};
```

Works because async scheduling only changes *when* continuations run on the main stack — a Worker is the only way to get CPU work onto a genuinely different thread (see section 6).

### Chunked filtering to keep typing responsive

A data table filters 100k client-side rows as the user types. Filtering everything in one pass is a long task: the browser cannot paint or handle keystrokes until it finishes, because of run-to-completion.

```js
async function filterRows(rows, predicate) {
  const matches = [];

  for (let start = 0; start < rows.length; start += 5_000) {
    for (const row of rows.slice(start, start + 5_000)) {
      if (predicate(row)) matches.push(row);
    }

    await new Promise(resolve => setTimeout(resolve)); // yield: next chunk is a new task
  }

  return matches;
}
```

> [!warning]
> Yielding with a microtask (`await Promise.resolve()`) does NOT let the browser render — microtasks drain before the next task. You must yield with a task (`setTimeout`) or `scheduler.yield()` where supported. See [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]] and [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]].

### Optimistic like button

A social feed flips the heart icon instantly and syncs the server later. The UI update is synchronous "now" work; the network call is "later" work the user should not wait for.

```jsx
async function handleLike(postId) {
  setLiked(true); // sync: paint this frame

  try {
    await likesApi.add(postId); // async: reconcile later
  } catch {
    setLiked(false); // roll back on failure
  }
}
```

Works because the sync state update finishes on the current stack before the fetch continuation ever runs — "start now, continue later" is exactly the product requirement here.

## 11. Interview Answer

**Short version:** Synchronous code runs on the current call stack until it finishes. Asynchronous code starts work and schedules a continuation for later, usually through a promise job or host callback.

**Strong version:** JavaScript is run-to-completion in an agent, so ordinary callbacks do not interrupt each other halfway. ECMAScript defines promises and async functions, while the host provides APIs like `fetch`, timers, DOM events, and the event loop integration. Promise callbacks run as microtasks after the current stack finishes, and timers/events run as tasks. Async code does not make CPU work parallel; it only changes when continuations run. In production, the hard part is not syntax. It is handling loading state, stale results, errors, cancellation, and UI responsiveness.

## 12. Common Mistakes

- Thinking `setTimeout(fn, 0)` runs immediately.
- Thinking `await` blocks the entire JavaScript thread.
- Thinking `async function` makes CPU-heavy work non-blocking.
- Forgetting that promise handlers run after the current sync code.
- Starting async work before setting duplicate-click guards.
- Not handling stale responses when user input changes quickly.
- Mixing ECMAScript promises with browser APIs without naming which layer owns the behavior.

## 13. Practice

1. Predict the output of the task/microtask example in this note.
2. Explain why `await 42` still yields before the next line inside the async function runs.
3. Build a small search handler that ignores stale responses.
4. Reproduce a slow request race with DevTools Network throttling.
5. Explain when a Web Worker is more appropriate than `async/await`.

## Related Notes

- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[01 - Roadmap|Roadmap]]
