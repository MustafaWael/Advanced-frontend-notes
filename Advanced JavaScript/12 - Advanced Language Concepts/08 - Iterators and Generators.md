---
tags: [javascript, language-concepts, iterators-and-generators]
module: "12 - Advanced Language Concepts"
priority: important
status: not-started
---

# Iterators and Generators

## Maturity Target

- Priority: #important
- Study time: 110-150 minutes
- Interview signal: you can explain iterator vs iterable, `Symbol.iterator`, generator state, `yield`, `yield*`, and async iteration.
- Production signal: you understand the protocols behind spread, destructuring, `for...of`, `Map`, `Set`, pagination, streaming, and lazy processing.
- Dependencies: [[12 - Advanced Language Concepts/07 - Symbols|Symbols]], [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]], [[08 - Async JavaScript/04 - Async Await|Async Await]]

## Source Anchors

- [MDN Iteration protocols](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Iteration_protocols)
- [MDN function*](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/function*)
- [MDN yield](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/yield)
- [MDN for...of](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for...of)
- [MDN for await...of](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for-await...of)

## 1. Concept

An iterator is an object with a `next()` method that returns `{ value, done }`.

An iterable is an object with `[Symbol.iterator]()` that returns an iterator.

A generator function (`function*`) creates a generator object that is both iterable and an iterator.

```js
function* numbers() {
  yield 1;
  yield 2;
}

console.log([...numbers()]); // [1, 2]
```

## 2. Why It Matters

The iteration protocol powers many everyday features:

- `for...of`;
- array spread: `[...items]`;
- destructuring: `const [first] = items`;
- `Array.from`;
- `new Map(iterable)`;
- `new Set(iterable)`;
- `Promise.all(iterable)`;
- strings, arrays, maps, sets, typed arrays, generators.

Knowing the protocol turns "syntax magic" into a predictable contract.

## 3. Accurate Mechanism

Iterator:

```js
const iterator = {
  current: 0,
  next() {
    this.current += 1;

    if (this.current <= 3) {
      return { value: this.current, done: false };
    }

    return { value: undefined, done: true };
  }
};
```

Iterable:

```js
const range = {
  from: 1,
  to: 3,
  [Symbol.iterator]() {
    let current = this.from;
    const to = this.to;

    return {
      next() {
        return current <= to
          ? { value: current++, done: false }
          : { value: undefined, done: true };
      }
    };
  }
};

console.log([...range]); // [1, 2, 3]
```

## 4. Generator Mechanism

Calling a generator function does not run its body immediately. It returns a generator object. The body runs when `.next()` is called and pauses at each `yield`.

```js
function* demo() {
  console.log("start");
  const input = yield "first";
  yield `received ${input}`;
  return "done";
}

const gen = demo();

console.log(gen.next());
console.log(gen.next("value"));
console.log(gen.next());
```

Expected output:

```txt
start
{ value: "first", done: false }
{ value: "received value", done: false }
{ value: "done", done: true }
```

`for...of` consumes yielded values where `done` is `false`. It does not include the final return value.

## 5. Mental Model

An iterable is a factory for iterators.

A generator is a paused function with memory.

Use them when values can be produced lazily instead of all at once.

## 6. Real Frontend Example: Chunk Large Work

```ts
function* chunks<T>(items: T[], size: number): Generator<T[]> {
  for (let index = 0; index < items.length; index += size) {
    yield items.slice(index, index + size);
  }
}

for (const batch of chunks(largeList, 100)) {
  processBatch(batch);
}
```

Why it helps:

- chunking keeps memory and UI work easier to reason about;
- the generator produces one batch at a time;
- callers can stop early with `break`.

If processing is expensive enough to block rendering, combine chunking with scheduling tools from [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]].

## 7. Async Generators for Pagination

```ts
async function* fetchPages(endpoint: string): AsyncGenerator<User[]> {
  let page = 1;

  while (true) {
    const response = await fetch(`${endpoint}?page=${page}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = (await response.json()) as { items: User[] };
    if (data.items.length === 0) return;

    yield data.items;
    page += 1;
  }
}

for await (const users of fetchPages("/api/users")) {
  appendUsers(users);
}
```

> [!info] Same primitive as `async/await`
> A generator is a suspendable call-stack frame you resume with `.next()`. `async/await` is that identical suspend/resume machinery wired to a promise scheduler instead — which is why an async function runs synchronously until the first `await`, then resumes later as a microtask. See the internals deep dive in [[08 - Async JavaScript/04 - Async Await|Async Await]] and [[09 - Event Loop Advanced/03 - Promise Jobs|Promise Jobs]].

> [!tip] Tradeoff
> this is elegant for streaming/pagination, but UI code still needs cancellation, loading state, and error handling.

## 8. `yield*` Delegation

```js
function* combined() {
  yield* [1, 2];
  yield* new Set([3, 4]);
  yield 5;
}

console.log([...combined()]); // [1, 2, 3, 4, 5]
```

Without `yield*`, you yield the iterable itself as one value.

```js
function* wrong() {
  yield [1, 2];
}

console.log([...wrong()]); // [ [1, 2] ]
```

## 9. Production Bugs

### Bug: Consuming a generator twice

```js
const values = numbers();

console.log([...values]); // [1, 2]
console.log([...values]); // []
```

Fix: call the generator function again.

```js
console.log([...numbers()]);
console.log([...numbers()]);
```

### Bug: Spreading an infinite generator

```js
function* ids() {
  let id = 1;
  while (true) yield id++;
}

// [...ids()] would never finish.
```

Fix:

```js
function take<T>(count: number, iterable: Iterable<T>) {
  const result: T[] = [];

  for (const item of iterable) {
    result.push(item);
    if (result.length === count) break;
  }

  return result;
}

console.log(take(3, ids())); // [1, 2, 3]
```

## 10. Production Tradeoffs

| Pattern | Benefit | Risk |
| --- | --- | --- |
| Custom iterable | integrates with JS syntax | may surprise team if simple array works |
| Generator | lazy sequence, clear state | single-use iterator can confuse |
| Async generator | natural pagination/streams | cancellation and errors still need design |
| `yield*` | composition | easy to confuse with yielding the iterable |
| `for...of` | protocol-based iteration | not available for plain objects unless iterable |

## 11. Interview Answer

**Short version:** An iterator has `next()` returning `{ value, done }`. An iterable has `[Symbol.iterator]()` returning an iterator. Generators are functions that pause at `yield` and return generator objects implementing these protocols.

**Strong version:** JavaScript's iterable protocol is the shared contract behind `for...of`, spread, destructuring, `Array.from`, maps, sets, and promise combinators. A generator preserves its execution state between `.next()` calls, so it can produce lazy sequences and receive values back through `next(value)`. `yield*` delegates to another iterable. Async generators extend the model to values that arrive over time, such as paginated API data. In production I use iterators when laziness or protocol integration matters, and I avoid overengineering simple arrays.

## 12. Common Mistakes

- Calling a generator function and expecting the body to run immediately.
- Iterating the same generator object twice.
- Forgetting `for...of` skips the generator return value.
- Using `yield [1,2]` when `yield* [1,2]` was intended.
- Spreading infinite iterables.
- Assuming plain objects are iterable.
- Ignoring cancellation/error handling in async generators.

## 13. Practice

1. Implement `range(start, end, step)`.
2. Explain why `[...new Set([1, 1, 2])]` works.
3. Predict each `.next()` result in a generator that receives `next(value)`.
4. Write `take(n, iterable)`.
5. Build an async generator for paginated fetch and explain where errors propagate.

## Related Notes

- [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]
- [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[01 - Roadmap|Roadmap]]
