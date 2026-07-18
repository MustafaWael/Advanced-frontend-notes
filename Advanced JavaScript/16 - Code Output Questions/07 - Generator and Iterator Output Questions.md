---
tags: [javascript, code-output, interview, generators, iterators]
module: "16 - Code Output Questions"
priority: important
status: not-started
---

# Generator and Iterator Output Questions

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: can trace generator output through suspended execution state and the `next(value)` handshake, not "it pauses."
- Production signal: can reason about lazy iteration, early `return()` cleanup, and why spreading an exhausted iterator yields nothing.
- Fast track: solve Q1-Q4, then explain aloud where the argument to `next()` lands.

## Source Anchors

- [MDN: Iteration protocols](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Iteration_protocols)
- [MDN: function*](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function*)
- [ECMAScript specification — Generator Objects](https://tc39.es/ecma262/#sec-generator-objects)

## Trace Method

For generator questions:

1. Calling a generator function runs **no body code** — it returns a suspended generator object.
2. Each `next()` runs until the *next* `yield`, returns `{ value, done }`, and suspends.
3. The argument to `next(arg)` becomes the value of the `yield` expression **where execution was suspended** — the first `next()`'s argument has no `yield` to land on and is discarded.
4. A `return` in the body produces `{ value, done: true }` once; after that, every `next()` yields `{ value: undefined, done: true }`.
5. `for...of`, spread, and destructuring consume via the iterator protocol and **ignore the `return` value** (they stop at `done: true` without reading its `value`).

## Q1. No Code Runs Until next()

```js
function* gen() {
  console.log("A");
  yield 1;
  console.log("B");
  yield 2;
}
const g = gen();
console.log("start");
console.log(g.next().value);
console.log(g.next().value);
```

### Expected Output

```text
start
A
1
B
2
```

### Why

`gen()` allocates a suspended generator — "A" does not log at call time. The first `next()` runs the body until `yield 1` (logging "A"), the second resumes after the first `yield` and runs to `yield 2` (logging "B"). The footgun this encodes: side effects in a generator body are deferred until consumption.

## Q2. Where next(arg) Lands

```js
function* gen() {
  const a = yield 1;
  const b = yield a + 10;
  yield b + 100;
}
const g = gen();
console.log(g.next(5).value);
console.log(g.next(2).value);
console.log(g.next(3).value);
```

### Expected Output

```text
1
12
103
```

### Why

`next(5)` starts the body; there is no suspended `yield` for 5 to become, so it's discarded — the call runs to `yield 1` and returns 1. `next(2)` resumes at the suspended `yield 1` expression, which now evaluates to 2, so `a = 2` and the body runs to `yield a + 10` → 12. `next(3)` makes that yield evaluate to 3, so `b = 3` → `yield 103`. The handshake is offset by one — the most common generator trace mistake.

## Q3. return Value vs for...of

```js
function* gen() {
  yield 1;
  yield 2;
  return 99;
}
console.log([...gen()]);
console.log(gen().next(), gen().next());
for (const v of gen()) console.log(v);
```

### Expected Output

```text
[1, 2]
{ value: 1, done: false } { value: 1, done: false }
1
2
```

### Why

Spread and `for...of` stop when `done` becomes `true` and discard that result's `value` — 99 never appears. The middle line is a trap within a trap: `gen().next()` twice calls the generator function **twice**, producing two independent generators, each yielding its first value. Iterator state lives on the generator *object*, not the function.

## Q4. Exhausted Iterators Yield Nothing

```js
function* gen() { yield 1; yield 2; yield 3; }
const g = gen();
console.log([...g]);
console.log([...g]);
```

### Expected Output

```text
[1, 2, 3]
[]
```

### Why

A generator object is both iterable and its own iterator (`g[Symbol.iterator]() === g`), so the first spread drives it to `done: true` and the second spread asks the *same exhausted* iterator for values. Contrast with an array, whose `[Symbol.iterator]()` returns a **fresh** iterator per call. Production version of this bug: passing an iterator (not an iterable) to two consumers, the second seeing nothing.

## Q5. Early Termination Runs finally

```js
function* gen() {
  try {
    yield 1;
    yield 2;
  } finally {
    console.log("cleanup");
  }
}
for (const v of gen()) {
  console.log(v);
  break;
}
```

### Expected Output

```text
1
cleanup
```

### Why

`break` (like `throw` or an early `return`) inside `for...of` calls the iterator's `return()` method, which resumes the generator as if a `return` occurred at the suspended `yield` — so the `finally` block runs. This is the mechanism that lets lazy resource readers (file handles, DB cursors) clean up when a consumer stops early; a hand-written iterator without `return()` gets no such signal.

## Q6. Custom Iterable Protocol

```js
const range = {
  from: 1, to: 3,
  [Symbol.iterator]() {
    let cur = this.from;
    const last = this.to;
    return {
      next: () => cur <= last
        ? { value: cur++, done: false }
        : { value: undefined, done: true },
    };
  },
};
console.log([...range]);
console.log([...range]);
console.log(Math.max(...range));
```

### Expected Output

```text
[1, 2, 3]
[1, 2, 3]
3
```

### Why

`range` is an *iterable* whose `[Symbol.iterator]()` builds a fresh iterator object per call (fresh `cur` each time via closure) — so unlike Q4's generator object, it can be consumed repeatedly. Every spread call invokes `[Symbol.iterator]()` again. Swap the implementation to return a shared iterator and the second spread would print `[]` — the Q4 failure, hand-rolled.

## Related Notes

- [[12 - Advanced Language Concepts/00 - Advanced Language Concepts MOC|Advanced Language Concepts MOC]]
- [[07 - Arrays and Iteration/00 - Arrays and Iteration MOC|Arrays and Iteration MOC]]
- [[16 - Code Output Questions/00 - Code Output Questions MOC|Code Output Questions MOC]]
