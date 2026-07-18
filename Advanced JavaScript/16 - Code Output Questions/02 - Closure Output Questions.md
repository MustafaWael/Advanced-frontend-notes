---
tags: [javascript, code-output, interview, closure-output-questions]
module: "16 - Code Output Questions"
priority: must-know
status: not-started
---

# Closure Output Questions

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: can explain closure output through bindings and lexical environments, not "it remembers values."
- Production signal: can connect closure traces to stale React callbacks, timers, listeners, and memory retention.
- Fast track: solve Q1-Q7, then explain the difference between Q1 and Q2 aloud.

## Source Anchors

- [MDN: Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [ECMAScript specification](https://tc39.es/ecma262/)
- [React docs: State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)

## Trace Method

For closure questions:

1. Ask which lexical environment the function was created in.
2. Ask whether closures share the same binding or separate bindings.
3. Ask when the callback runs relative to mutations.
4. Remember: closures capture bindings, not frozen primitive values.

## Q1. Classic `var` Loop Timer

```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
```

### Expected Output

```text
3
3
3
```

### Why

`var i` creates one shared binding in the enclosing scope. Each timeout callback closes over that same binding. Timers run after the loop finishes, and the loop exits when `i` becomes `3`.

### Common Wrong Answer

`0, 1, 2`.

That would require separate bindings per iteration. `var` does not create them.

Related: [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]

## Q2. Fixed With `let`

```js
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
```

### Expected Output

```text
0
1
2
```

### Why

`let` in a `for` loop creates a fresh per-iteration binding. Each callback closes over a different `i`.

### Interview Line

`let` fixes this because it changes the binding lifetime, not because timers behave differently.

Related: [[03 - Scope and Variables/03 - var let const|var let const]]

## Q3. Closure Captures Binding, Not Value

```js
let value = 1;

const readValue = () => value;

value = 2;

console.log(readValue());
```

### Expected Output

```text
2
```

### Why

The closure captures the `value` binding. When `value = 2` runs, it updates the same binding. Later, `readValue` reads the current value of that binding.

### Common Wrong Answer

`1`.

That would be true if closures copied primitive values at creation time. They do not.

Related: [[03 - Scope and Variables/05 - Closures|Closures]]

## Q4. Counter Factory

```js
function makeCounter() {
  let count = 0;

  return {
    increment: () => ++count,
    getCount: () => count,
  };
}

const counter = makeCounter();

counter.increment();
counter.increment();

console.log(counter.getCount());
```

### Expected Output

```text
2
```

### Why

`increment` and `getCount` are created inside the same call to `makeCounter`, so both close over the same `count` binding. `count` stays reachable because the returned functions are reachable.

### Production Angle

This pattern is useful for private state, but long-lived closures can also retain memory.

Related: [[13 - Performance and Memory/04 - Closures and Retained Memory|Closures and Retained Memory]]

## Q5. Separate Closures

```js
function multiplier(factor) {
  return number => number * factor;
}

const double = multiplier(2);
const triple = multiplier(3);

console.log(double(5), triple(5));
```

### Expected Output

```text
10 15
```

### Why

Each call to `multiplier` creates a new lexical environment with its own `factor` binding. `double` closes over `factor = 2`; `triple` closes over `factor = 3`.

### Interview Line

Same function body, different closure environments.

Related: [[04 - Functions Deep Dive/06 - Currying and Partial Application|Currying and Partial Application]]

## Q6. Shared Closure In Array

```js
const funcs = [];

for (var i = 0; i < 3; i++) {
  funcs.push(() => i);
}

console.log(funcs[0](), funcs[1](), funcs[2]());
```

### Expected Output

```text
3 3 3
```

### Why

All functions close over the same `var i` binding. By the time the functions are called, the loop has finished and `i` is `3`.

### Fix

```js
const funcs = [];

for (let i = 0; i < 3; i++) {
  funcs.push(() => i);
}

console.log(funcs[0](), funcs[1](), funcs[2]()); // 0 1 2
```

Related: [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]]

## Q7. IIFE Snapshot Pattern

```js
const funcs = [];

for (var i = 0; i < 3; i++) {
  funcs.push(((j) => () => j)(i));
}

console.log(funcs[0](), funcs[1](), funcs[2]());
```

### Expected Output

```text
0 1 2
```

### Why

The immediately invoked function receives the current `i` as `j`. Each invocation creates a new `j` parameter binding. The returned function closes over that separate `j`.

### Interview Line

The IIFE creates a new scope per iteration, similar to what `let` does more cleanly today.

Related: [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions and IIFE]]

## Q8. Module Pattern Reset

```js
const counter = (() => {
  let n = 0;

  return {
    inc: () => ++n,
    reset: () => {
      n = 0;
    },
  };
})();

counter.inc();
counter.inc();
counter.reset();

console.log(counter.inc());
```

### Expected Output

```text
1
```

### Why

The IIFE runs once and creates one `n` binding. `inc` and `reset` share that binding. After two increments, `n` is `2`; `reset` sets it to `0`; the final `inc` increments to `1`.

Related: [[03 - Scope and Variables/05 - Closures|Closures]]

## Q9. Stale Message

```js
function createLogger() {
  let count = 0;
  const message = `Count is ${count}`;

  return {
    increment() {
      count += 1;
    },
    log() {
      console.log(message);
    },
  };
}

const logger = createLogger();
logger.increment();
logger.increment();
logger.log();
```

### Expected Output

```text
Count is 0
```

### Why

`message` is computed once when `createLogger` runs. `increment` updates `count`, but `message` is just a string value that is not recomputed. `log` closes over the `message` binding, whose value remains `"Count is 0"`.

### Fix

```js
log() {
  console.log(`Count is ${count}`);
}
```

Now the message is computed at call time from the current `count` binding.

### React Angle

This is the plain JavaScript shape behind stale derived values in callbacks.

Related: [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

## Q10. Closure And Async Timing

```js
let value = 'initial';

function scheduleLog() {
  setTimeout(() => console.log(value), 0);
}

scheduleLog();
value = 'updated';
```

### Expected Output

```text
updated
```

### Why

The timeout callback closes over the `value` binding, not the string value at scheduling time. The binding is updated before the timer task runs, so the callback logs `"updated"`.

### Common Wrong Answer

`initial`.

That would require capturing the value separately, such as `const snapshot = value`.

Related: [[09 - Event Loop Advanced/04 - Timers|Timers]]

## Review Loop

- [ ] I can distinguish shared binding from separate binding.
- [ ] I can explain why `let` in loops creates per-iteration bindings.
- [ ] I can explain why closures can retain memory.
- [ ] I can connect at least one question to React stale closures.

## Related Notes

- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]]
- [[16 - Code Output Questions/03 - this Output Questions|this Output Questions]]
