---
tags: [javascript, code-output, interview, async-and-event-loop-output-questions]
module: "16 - Code Output Questions"
priority: must-know
status: not-started
---

# Async and Event Loop Output Questions

## Maturity Target

- Priority: #must-know
- Study time: 120-150 minutes
- Interview signal: can trace sync code, Promise microtasks, `await` continuations, timers, and nested queues.
- Production signal: can explain UI blocking, race conditions, waterfalls, and why async code still runs on one JS thread.
- Fast track: solve Q1-Q8, then run them in Node or a browser console.

## Source Anchors

- [HTML Living Standard: event loops](https://html.spec.whatwg.org/multipage/webappapis.html#event-loops)
- [MDN: Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [MDN: async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
- [MDN: queueMicrotask](https://developer.mozilla.org/en-US/docs/Web/API/queueMicrotask)

## Trace Method

For async output:

1. Run synchronous code first.
2. Promise reactions and `await` continuations are microtasks.
3. `queueMicrotask` adds to the same microtask queue.
4. Timers run in later tasks.
5. The microtask queue drains fully before the next task.
6. When a `.then` returns, the next `.then` is queued later, not immediately at chain creation.

## Q1. Promise Before Timer

```js
console.log('A');

setTimeout(() => console.log('B'), 0);

Promise.resolve().then(() => console.log('C'));

console.log('D');
```

### Expected Output

```text
A
D
C
B
```

### Why

`A` and `D` are synchronous. The Promise reaction is a microtask. The timer callback is a later task. Microtasks run before the next task.

Related: [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## Q2. Chained Promises Interleave

```js
Promise.resolve()
  .then(() => console.log('A'))
  .then(() => console.log('B'));

Promise.resolve()
  .then(() => console.log('C'))
  .then(() => console.log('D'));
```

### Expected Output

```text
A
C
B
D
```

### Why

The first `.then` handlers are queued immediately: `A`, then `C`. When `A` runs, it fulfills the Promise returned by that `.then`, which queues `B` at the end. The queue becomes `C`, `B`. Then `C` queues `D`.

### Common Wrong Answer

`A, B, C, D`.

That ignores FIFO ordering across Promise chains.

Related: [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]]

## Q3. `await` Continuation

```js
async function run() {
  console.log(1);
  await null;
  console.log(2);
}

run();
console.log(3);
```

### Expected Output

```text
1
3
2
```

### Why

The async function runs synchronously until `await`. `await null` still yields; the continuation after `await` is scheduled as a microtask. The global `console.log(3)` runs before that microtask.

Related: [[08 - Async JavaScript/04 - Async Await|Async Await]]

## Q4. Promise Constructor Is Synchronous

```js
new Promise(resolve => {
  console.log('A');
  resolve();
}).then(() => {
  console.log('C');
});

console.log('B');
```

### Expected Output

```text
A
B
C
```

### Why

The Promise executor runs synchronously. Calling `resolve` settles the Promise and queues the `.then` callback as a microtask. `B` logs before microtasks drain.

Related: [[08 - Async JavaScript/02 - Promises|Promises]]

## Q5. `queueMicrotask` Ordering

```js
queueMicrotask(() => console.log('A'));

Promise.resolve().then(() => console.log('B'));

queueMicrotask(() => console.log('C'));

console.log('D');
```

### Expected Output

```text
D
A
B
C
```

### Why

`queueMicrotask` and Promise reactions use the microtask queue. They are processed FIFO after synchronous code completes.

Related: [[09 - Event Loop Advanced/05 - queueMicrotask and requestAnimationFrame|queueMicrotask and requestAnimationFrame]]

## Q6. Nested Microtask

```js
Promise.resolve().then(() => {
  console.log('A');
  queueMicrotask(() => console.log('B'));
});

setTimeout(() => console.log('C'), 0);

console.log('D');
```

### Expected Output

```text
D
A
B
C
```

### Why

`D` is synchronous. The Promise microtask logs `A` and queues another microtask for `B`. The microtask queue must drain completely, including nested microtasks, before the timer task logs `C`.

Related: [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## Q7. Async Function Return Value

```js
async function getValue() {
  return 42;
}

const result = getValue();

console.log(result instanceof Promise);

result.then(value => console.log(value));

console.log('after');
```

### Expected Output

```text
true
after
42
```

### Why

An async function always returns a Promise. The returned value `42` becomes the fulfillment value. The `.then` handler runs as a microtask after synchronous `after`.

Related: [[08 - Async JavaScript/04 - Async Await|Async Await]]

## Q8. Sequential Await In A Loop

```js
async function main() {
  for (const n of [1, 2, 3]) {
    await Promise.resolve();
    console.log(n);
  }
}

main();
console.log('outside');
```

### Expected Output

```text
outside
1
2
3
```

### Why

The first `await` suspends `main`, so `outside` logs before the first loop body continuation. Each iteration waits for the previous awaited continuation before starting the next iteration.

### Production Angle

This is serial. Use `Promise.all` when independent async work should start concurrently.

Related: [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]

## Q9. `Promise.all` Result Order

```js
async function main() {
  const slow = new Promise(resolve => {
    setTimeout(() => resolve('slow'), 10);
  });

  const fast = Promise.resolve('fast');

  const results = await Promise.all([slow, fast]);
  console.log(results);
}

main();
```

### Expected Output

```text
[ 'slow', 'fast' ]
```

### Why

`Promise.all` preserves input order, not resolution order. Even though `fast` resolves earlier, its result stays at index 1 because it was the second input.

Related: [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]]

## Q10. Timer Resolves A Promise

```js
new Promise(resolve => {
  setTimeout(resolve, 0);
}).then(() => console.log('promise'));

console.log('sync');

setTimeout(() => console.log('timer'), 0);
```

### Expected Output

```text
sync
promise
timer
```

### Why

The first timer is registered before the second timer. When the first timer task runs, it resolves the Promise and queues the `.then` callback as a microtask. That microtask runs before the event loop picks the second timer task.

### Host Note

Timer ordering can have host details, but for timers registered in this order with zero delay, this is the expected browser/Node behavior.

Related: [[09 - Event Loop Advanced/04 - Timers|Timers]]

## Q11. Mixed Timer In Promise

```js
console.log('1');

setTimeout(() => console.log('2'), 0);

Promise.resolve()
  .then(() => {
    console.log('3');
    setTimeout(() => console.log('4'), 0);
  })
  .then(() => console.log('5'));

console.log('6');
```

### Expected Output

```text
1
6
3
5
2
4
```

### Why

`1` and `6` are sync. The first Promise handler logs `3` and registers a new timer for `4`. Its returned Promise then queues the next `.then`, which logs `5` in the same microtask drain. Timers run after microtasks. Timer `2` was registered before timer `4`, so `2` runs first.

Related: [[09 - Event Loop Advanced/07 - Code Output Questions|Code Output Questions]]

## Q12. Awaiting Another Async Function

```js
async function inner() {
  console.log('inner start');
  await Promise.resolve();
  console.log('inner end');
}

async function outer() {
  console.log('outer start');
  await inner();
  console.log('outer end');
}

outer();
console.log('global');
```

### Expected Output

```text
outer start
inner start
global
inner end
outer end
```

### Why

`outer` starts and calls `inner`. `inner` logs before its first `await`, then suspends. `outer` awaits `inner`, so it also suspends. Global code logs `global`. The `inner` continuation logs `inner end`, fulfilling `inner`'s Promise, which queues and later runs `outer`'s continuation.

Related: [[08 - Async JavaScript/04 - Async Await|Async Await]]

## Review Loop

- [ ] I separated sync, microtasks, and tasks.
- [ ] I can explain why `.then` chains interleave.
- [ ] I can explain why `await null` still yields.
- [ ] I can explain which examples are serial and which start concurrent work.

## Related Notes

- [[08 - Async JavaScript/08 - Async Checklist|Async Checklist]]
- [[09 - Event Loop Advanced/08 - Event Loop Checklist|Event Loop Checklist]]
- [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]]
- [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]]
