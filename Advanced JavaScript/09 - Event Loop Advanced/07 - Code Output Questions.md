---
tags: [javascript, event-loop, code-output-questions]
module: "09 - Event Loop Advanced"
priority: must-know
status: not-started
---

# Code Output Questions

## Maturity Target

- Priority: #must-know
- Study time: 120-160 minutes
- Interview signal: you can trace sync code, promise jobs, microtasks, timers, and async function continuations step by step.
- Production signal: you use output questions as small reproductions for real scheduling bugs, not as trivia.
- Dependencies: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]], [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]

## Source Anchors

- [HTML Living Standard: Event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [MDN Microtask guide](https://developer.mozilla.org/en-US/docs/Web/API/HTML_DOM_API/Microtask_guide)
- [MDN Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [MDN setTimeout](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout)

## 1. Concept

Event-loop code output questions test whether you can separate synchronous execution, microtasks, promise jobs, async function continuations, and later tasks.

The point is not memorizing puzzle output. The point is building a reliable trace that also explains real frontend timing bugs.

## 2. How To Trace

For each question, write three lists:

1. synchronous execution
2. microtasks queued and drained
3. tasks queued and executed later

Then walk one callback at a time. Do not jump to "promises before timers" too early; that shortcut fails on nested cases.

## 3. Question 1: Basic Task vs Microtask

```js
console.log("A");

setTimeout(() => console.log("B"), 0);

Promise.resolve().then(() => console.log("C"));

console.log("D");
```

Expected output:

```txt
A
D
C
B
```

Why:

- `A` and `D` are synchronous.
- `C` is a promise reaction microtask.
- `B` is a timer task.

## 4. Question 2: queueMicrotask Order

```js
console.log("start");

queueMicrotask(() => console.log("M1"));

Promise.resolve().then(() => console.log("P1"));

queueMicrotask(() => console.log("M2"));

console.log("end");
```

Expected output:

```txt
start
end
M1
P1
M2
```

Why: `queueMicrotask` and promise reactions share the microtask queue in enqueue order.

## 5. Question 3: Microtask Queued Inside Microtask

```js
console.log("start");

Promise.resolve().then(() => {
  console.log("P1");
  queueMicrotask(() => console.log("M nested"));
});

queueMicrotask(() => console.log("M1"));

Promise.resolve().then(() => console.log("P2"));

console.log("end");
```

Expected output:

```txt
start
end
P1
M1
P2
M nested
```

Why: `M nested` is added to the end of the current microtask queue and runs before the next task.

## 6. Question 4: Promise Chains Interleave

```js
Promise.resolve()
  .then(() => console.log("A1"))
  .then(() => console.log("A2"))
  .then(() => console.log("A3"));

Promise.resolve()
  .then(() => console.log("B1"))
  .then(() => console.log("B2"))
  .then(() => console.log("B3"));
```

Expected output:

```txt
A1
B1
A2
B2
A3
B3
```

Why: each `.then` callback queues the next callback in its own chain after it runs. The chains interleave one job at a time.

## 7. Question 5: Async Await Yields

```js
async function demo() {
  console.log("A");
  await 1;
  console.log("C");
}

demo();

console.log("B");
```

Expected output:

```txt
A
B
C
```

Why: `await` yields the async function continuation even for a non-promise value.

## 8. Question 6: Awaiting A Timer

```js
async function main() {
  console.log("A");

  await new Promise(resolve => setTimeout(resolve, 0));

  console.log("C");
}

main();

Promise.resolve().then(() => console.log("B"));

console.log("D");
```

Expected output:

```txt
A
D
B
C
```

Why:

- `main` starts and logs `A`.
- the awaited promise resolves only after a timer task.
- `D` is synchronous.
- `B` is an already queued promise microtask.
- after the timer resolves, `main` resumes as a microtask and logs `C`.

## 9. Question 7: Promise Executor Timing

```js
const promise = new Promise(resolve => {
  console.log("executor");
  resolve("value");
});

promise.then(value => console.log(value));

console.log("after");
```

Expected output:

```txt
executor
after
value
```

Why: the executor runs synchronously. The `.then` handler runs as a promise job later.

## 10. Question 8: Catch Converts Failure

```js
Promise.reject(new Error("bad"))
  .catch(error => error.message)
  .then(value => console.log(value));
```

Expected output:

```txt
bad
```

Why: the `catch` returned a normal value, so the chain became fulfilled.

## 11. Question 9: Timer Closure With `var`

```js
for (var i = 0; i < 3; i += 1) {
  setTimeout(() => console.log(i), 0);
}
```

Expected output:

```txt
3
3
3
```

Why:

- the loop finishes synchronously before timers run
- `var` creates one function-scoped binding
- all callbacks read the same final `i`

Fix:

```js
for (let i = 0; i < 3; i += 1) {
  setTimeout(() => console.log(i), 0);
}

// 0
// 1
// 2
```

## 12. Question 10: Blocking Delays Timer

```js
console.log("start");

setTimeout(() => console.log("timer"), 0);

const started = Date.now();
while (Date.now() - started < 100) {}

console.log("end");
```

Expected output:

```txt
start
end
timer
```

Why: the timer cannot run while synchronous JavaScript is blocking the stack.

## 13. Question 11: Async forEach

```js
async function run() {
  [1, 2].forEach(async value => {
    await Promise.resolve();
    console.log(value);
  });

  console.log("done");
}

run();
```

Expected output:

```txt
done
1
2
```

Why: `forEach` ignores the promises returned by async callbacks.

## 14. Question 12: Promise.all Order

```js
function wait(ms, value) {
  return new Promise(resolve => {
    setTimeout(() => resolve(value), ms);
  });
}

const values = await Promise.all([
  wait(20, "slow"),
  wait(1, "fast"),
]);

console.log(values);
```

Expected output:

```js
["slow", "fast"]
```

Why: `Promise.all` returns values in input order, not completion order.

## 15. Production Translation

Interview output questions map to real bugs:

| Output lesson | Production bug |
| --- | --- |
| promise before timer | loading cleanup happens before delayed UI |
| microtasks drain fully | recursive microtasks starve paint |
| executor sync, handler async | state read too early after `.then` |
| timer after blocking work | click feedback delayed by long task |
| `var` in timer loop | callbacks share stale/final value |
| async forEach | submit finishes before async work completes |
| `catch` returns value | error path accidentally shows success |
| `queueMicrotask` and `.then` share one queue | init logic assumes one "runs later" than the other and breaks on reorder |
| promise chains interleave | two features' chains observe each other's half-updated shared state |
| `await` on a timer resumes as a microtask | resumed code races user events that arrived while waiting |
| `Promise.all` keeps input order | results zipped to the wrong request when code assumes completion order |

## 16. Interview Answer

**Short version:** Trace synchronous code first, then microtasks in enqueue order, then later tasks such as timers. For async functions, code before the first `await` runs synchronously and code after `await` resumes later.

**Strong version:** I do not memorize outputs directly. I build queues. First I run the current script to completion. While doing that, timers create later tasks, promise reactions and `queueMicrotask` create microtasks, and async functions run until `await`. When the current task ends, the microtask queue drains completely in FIFO order, including microtasks created during the drain. Then the event loop can move to timers or other tasks. This method also explains production bugs such as stale reads, async `forEach`, missing promise returns, and UI work delayed by long tasks.

## 17. Practice

1. Re-run each question and write the queue state before reading the answer.
2. Change one `Promise.resolve().then` into `setTimeout` and retrace.
3. Change one `var` loop into `let` and explain the binding difference.
4. Add a nested `queueMicrotask` to question 2 and predict where it lands.
5. Convert question 11 to a correct sequential `for...of` loop.

## Related Notes

- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
- [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]
- [[09 - Event Loop Advanced/04 - Timers|Timers]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]]
- [[01 - Roadmap|Roadmap]]
