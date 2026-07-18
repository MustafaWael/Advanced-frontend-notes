---
tags: [javascript, scope, closures]
module: "03 - Scope and Variables"
priority: must-know
status: not-started
aliases: [Closure]
---

# Closures

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can explain closures as functions plus lexical environment access, then solve loop and async output questions.
- Production signal: you can choose between closure state, object state, React state, refs, memoization, and module scope intentionally.
- Dependencies: [[03 - Scope and Variables/01 - Scope Types|Scope Types]], [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]], [[03 - Scope and Variables/03 - var let const|var let const]]

## Source Anchors

- [MDN - Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [ECMAScript 2026 - Function Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-function-environment-records)
- [ECMAScript 2026 - NewFunctionEnvironment](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-newfunctionenvironment)
- [React - useCallback](https://react.dev/reference/react/useCallback)
- [React - useEffect](https://react.dev/reference/react/useEffect)

## 1. Concept

A closure is a function with access to the lexical environment where it was created. Every JavaScript function is created with a reference to its surrounding lexical environment; the closure becomes visible when the function runs later or outside the scope where it was created.

The important phrase is access to bindings, not copies of values.

```js
function createCounter() {
  let count = 0;

  return function increment() {
    count += 1;
    return count;
  };
}

const next = createCounter();
console.log(next()); // 1
console.log(next()); // 2
console.log(next()); // 3
```

`count` did not disappear after `createCounter()` returned because the returned function still needs its environment.

## 2. Why Closures Exist

Closures let JavaScript functions carry behavior together with the data they need. That powers:

- Event handlers that remember configuration.
- Callback APIs.
- Function factories.
- Encapsulation/private state.
- Memoization.
- Debounce and throttle helpers.
- React hook callbacks.
- Async continuations after timers, promises, and network responses.

Without closures, frontend code would need much more global state or object plumbing.

## 3. Official Mechanism

When a function object is created, it has an internal environment reference. When it is later called, the function's environment becomes part of the new function environment's outer chain. That is why identifier lookup can reach variables from the function's creation scope.

Step-by-step:

1. `createCounter()` is called.
2. A function environment is created for that call.
3. The `count` binding is created and initialized to `0`.
4. `increment` is created with access to that environment.
5. `createCounter()` returns `increment`.
6. The returned function is still reachable, so the environment containing `count` remains reachable.
7. Each call to `next()` resolves `count` through that environment and updates the same binding.

## 4. Mental Model

Closure = function + backpack of outer binding boxes.

The backpack stores references to bindings the function can reach. If a binding changes, the closure sees the new value.

```js
function makeReaders() {
  let value = "initial";

  function read() {
    return value;
  }

  function write(nextValue) {
    value = nextValue;
  }

  return { read, write };
}

const store = makeReaders();
console.log(store.read()); // "initial"
store.write("updated");
console.log(store.read()); // "updated"
```

## 5. Closures Capture Bindings, Not Snapshots

This is the core interview distinction.

```js
let message = "first";

function logMessage() {
  console.log(message);
}

message = "second";
logMessage(); // "second"
```

The closure reads the current contents of the `message` binding.

But if each function call creates a new binding, closures can preserve different environments:

```js
function makeAdder(amount) {
  return function add(value) {
    return value + amount;
  };
}

const addTen = makeAdder(10);
const addFive = makeAdder(5);

console.log(addTen(2));  // 12
console.log(addFive(2)); // 7
```

Each `makeAdder` call creates a separate `amount` binding.

## 6. Real Frontend Example: Event Handlers

Closures are excellent for attaching context to callbacks.

```js
function createAnalyticsHandler(productId) {
  return function handleClick(event) {
    // The handler keeps access to productId without reading from the DOM.
    track("product_clicked", {
      productId,
      buttonText: event.currentTarget.textContent
    });
  };
}

document
  .querySelector("[data-product='p42']")
  .addEventListener("click", createAnalyticsHandler("p42"));
```

Why this is useful:

- The handler does not rely on a global current product.
- The product id is passed once at setup time.
- The function can be removed later if you keep the exact handler reference.

Cleanup matters:

```js
const button = document.querySelector("[data-product='p42']");
const handler = createAnalyticsHandler("p42");

button.addEventListener("click", handler);

// Later, during teardown:
button.removeEventListener("click", handler);
```

If you create a new function in `removeEventListener`, it will not remove the old listener because the identity is different.

## 7. Private State and Encapsulation

Closures can hide implementation details.

```js
function createTokenStore() {
  let token = null;

  return {
    set(nextToken) {
      token = nextToken;
    },
    readAuthorizationHeader() {
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    clear() {
      token = null;
    }
  };
}

const tokenStore = createTokenStore();
tokenStore.set("abc");
console.log(tokenStore.readAuthorizationHeader());
// { Authorization: "Bearer abc" }
```

> [!tip] Tradeoff
> closure state is simple and private, but it can be hard to inspect, reset, or share across tests if you export a singleton. Prefer factory functions when you need one independent instance per test, user, request, or widget.

## 8. Memoization with Closure

```js
function memoizeById(loadById) {
  const cache = new Map();

  return async function load(id) {
    if (cache.has(id)) {
      return cache.get(id);
    }

    const promise = loadById(id);
    cache.set(id, promise);

    try {
      return await promise;
    } catch (error) {
      // Do not cache failed requests forever unless that is intentional.
      cache.delete(id);
      throw error;
    }
  };
}
```

Why the closure works:

- `cache` is private to the memoized loader.
- Every call to the returned `load` function uses the same `cache`.
- Failed requests are removed so retries can happen.

> [!tip] Tradeoff
> caching promises prevents duplicate work, but cache lifetime and invalidation must be explicit. In frontend code, add size limits, time limits, or invalidation when data can become stale.

## 9. React Closures

React makes closure mechanics visible because each render creates new bindings.

```jsx
function SaveButton({ documentId }) {
  const [draft, setDraft] = useState("");

  const handleSave = useCallback(() => {
    // This callback closes over documentId and draft from the render
    // where React created this function.
    return saveDocument(documentId, draft);
  }, [documentId, draft]);

  return <button onClick={handleSave}>Save</button>;
}
```

If `draft` is missing from the dependency list, the callback can save an old draft. If `handleSave` is passed to a memoized child, `useCallback` can be useful for identity stability, but correctness comes first: dependencies must match the closed-over reactive values.

## 10. Closures and Memory

A closure can keep large data alive if the returned function still references it.

```js
function createExporter(rows) {
  const metadata = {
    createdAt: Date.now(),
    rowCount: rows.length
  };

  return function exportSummary() {
    // Good: this closure needs metadata only.
    return metadata;
  };
}
```

Avoid accidentally capturing large values:

```js
function createExporter(rows) {
  return function exportSummary() {
    // Bug: the closure retains rows for as long as exportSummary exists.
    return { rowCount: rows.length };
  };
}
```

Fix:

```js
function createExporter(rows) {
  const rowCount = rows.length;

  return function exportSummary() {
    return { rowCount };
  };
}
```

> [!tip] Tradeoff
> do not prematurely avoid closures. They are normal JavaScript. Worry when a long-lived callback retains large DOM nodes, large arrays, request objects, or component resources.

## 11. Bug -> Fix -> Checklist

Bug: a debounced save closes over the wrong value.

```jsx
function Editor({ documentId }) {
  const [text, setText] = useState("");

  const debouncedSave = useMemo(
    () => debounce(() => saveDocument(documentId, text), 500),
    [documentId]
  );

  function onChange(event) {
    setText(event.target.value);
    debouncedSave();
  }
}
```

> [!warning] Failure mode
> `text` in the debounced function is from the render where `debouncedSave` was created.

Fix by passing the changing value as an argument:

```jsx
function Editor({ documentId }) {
  const [text, setText] = useState("");

  const debouncedSave = useMemo(
    () => debounce((nextText) => saveDocument(documentId, nextText), 500),
    [documentId]
  );

  function onChange(event) {
    const nextText = event.target.value;
    setText(nextText);
    debouncedSave(nextText);
  }
}
```

Checklist:

- When was the function created?
- When does it run?
- Which outer bindings does it read?
- Are those bindings stable, mutable, render-owned, request-owned, or module-owned?
- Does the closure need cleanup?
- Could a large captured value stay in memory too long?

## 12. Interview Answer

Short answer:

> A closure is a function that can access variables from the scope where it was created, even after that outer function has finished.

Deeper answer:

> JavaScript functions are created with an internal environment reference. When the function runs later, identifier lookup can follow that reference to outer Environment Records. Closures preserve access to bindings, not snapshots of primitive values. That is why multiple closures can share one binding, while separate function calls can create separate bindings.

Production answer:

> Closures are how callbacks remember context. They are useful for event handlers, memoization, debounce, and encapsulation. The risk is using a callback after the application state has moved on, as in React stale closures, or retaining large values in long-lived callbacks.

## 13. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Closures happen only when returning a function." | Returning a function makes them visible, but functions close over their creation environment generally. |
| "Closures copy primitive values." | They preserve access to bindings. |
| "Closures are bad for memory." | Closures are normal; leaks happen when long-lived closures retain unnecessary large objects or DOM nodes. |
| "React stale closures are a React-only concept." | React exposes ordinary JavaScript closures through repeated renders. |
| "Memoization is always good." | A cache has lifetime, invalidation, and memory tradeoffs. |

## 14. Practice

1. Predict the output:

```js
function makeLogger() {
  let value = 0;
  return {
    inc() {
      value += 1;
    },
    log() {
      console.log(value);
    }
  };
}

const logger = makeLogger();
logger.inc();
logger.inc();
logger.log();
```

Expected output: `2`.

2. Explain why `addTen` and `addFive` do not share the same `amount` binding.
3. Write a memoizer with a `Map`, then add behavior for failed requests.
4. Fix a debounced React callback that reads stale state.
5. Create a closure that accidentally retains a large array, then refactor it to retain only a primitive summary.

## Real-World Use Cases

### Classic interview trap: `setTimeout` inside a `var` loop

The single most-asked closure question. You will get some version of this snippet and be asked for the output.

```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
```

Wrong guess: `0, 1, 2`. Actual output: `3, 3, 3`.

Tick-by-tick trace:

1. Declaration instantiation hoists `var i` into the surrounding function/script scope — **one binding** for the whole loop ([[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]).
2. The loop runs synchronously to completion. Each iteration creates a new arrow function closing over that one shared `i` binding and hands it to `setTimeout`, which schedules a timer task.
3. The loop exits when `i === 3` and the call stack empties. Nothing has logged yet.
4. After ~100ms the event loop dequeues the three timer callbacks as macrotasks ([[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]). Each callback resolves `i` through its closure — same binding box, current contents: `3`.

The fix is one keyword:

```js
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100); // 0, 1, 2
}
```

`let` in a `for` head creates a **fresh per-iteration binding** ([[03 - Scope and Variables/03 - var let const|var let const]]), so each callback closes over its own `i`. This works because closures capture bindings, not values — with `var` there was only one binding to capture. More variations in [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]].

> [!tip] Interview follow-up
> Interviewers often push: "fix it without `let`." Answers: an IIFE/factory that takes `i` as a parameter, or `setTimeout(console.log, 100, i)` — extra arguments are passed to the callback, so nothing is closed over.

### WebSocket reconnect with exponential backoff

A live-prices widget must reconnect when the socket drops, backing off on repeated failures. The retry counter and pending timer live in the closure — no class, no global.

```js
function connectPrices(url, onMessage) {
  let attempt = 0;
  let socket;

  function open() {
    socket = new WebSocket(url);
    socket.onmessage = onMessage;
    socket.onopen = () => { attempt = 0; };
    socket.onclose = () => {
      attempt += 1;
      setTimeout(open, Math.min(1000 * 2 ** attempt, 30_000));
    };
  }

  open();
  return () => socket.close();
}
```

Every handler resolves `attempt` and `socket` through the same creation-time environment, so state survives across reconnects without any external store.

> [!warning]
> The returned cleanup closes the *current* socket, but the pending `setTimeout(open, ...)` will still fire and reopen it. Track the timer id in the closure and clear it during teardown — see [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]] for the lifetime checklist.

### One-time SDK initialization guard

Several routes can trigger analytics, but the third-party SDK must be initialized exactly once. A `once` wrapper hides the "already ran" flag in a closure instead of a module-level boolean anyone can flip.

```ts
function once<T extends (...args: any[]) => any>(fn: T) {
  let called = false;
  let result: ReturnType<T>;

  return (...args: Parameters<T>) => {
    if (!called) {
      called = true;
      result = fn(...args);
    }
    return result;
  };
}

export const initAnalytics = once((writeKey: string) => analytics.load(writeKey));
```

`called` and `result` are unreachable from outside — the closure is the privacy boundary, the same mechanism as the token store above but packaged as a reusable combinator like [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]].

## Related Notes

- [[03 - Scope and Variables/01 - Scope Types|Scope Types]]
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/03 - var let const|var let const]]
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]
- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]]
- [[01 - Roadmap|Roadmap]]
