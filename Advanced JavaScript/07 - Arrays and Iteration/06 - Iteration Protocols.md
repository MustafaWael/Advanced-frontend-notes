---
tags: [javascript, arrays, iteration-protocols]
module: "07 - Arrays and Iteration"
priority: important
status: not-started
---

# Iteration Protocols

## Maturity Target

- Priority: #important
- Study time: 75-100 minutes
- Interview signal: you can explain iterable vs iterator, `Symbol.iterator`, `for...of`, spread, and iterator exhaustion.
- Production signal: you convert DOM/API collections correctly and avoid confusing object enumeration with value iteration.
- Dependencies: [[12 - Advanced Language Concepts/07 - Symbols|Symbols]], [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]

## Source Anchors

- [MDN Iteration protocols](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Iteration_protocols)
- [MDN for...of](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/for...of)
- [MDN Symbol.iterator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/iterator)
- [MDN Array.from](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/from)
- [ECMAScript Iterator Interface](https://tc39.es/ecma262/#sec-iterator-interface)

## 1. Concept

Iteration protocols are the rules that let JavaScript pull values from an object one at a time.

Two related ideas matter:

- Iterable: an object with a `[Symbol.iterator]()` method that returns an iterator.
- Iterator: an object with a `next()` method that returns `{ value, done }`.

```js
const values = ["a", "b"];
const iterator = values[Symbol.iterator]();

console.log(iterator.next());
// { value: "a", done: false }

console.log(iterator.next());
// { value: "b", done: false }

console.log(iterator.next());
// { value: undefined, done: true }
```

## 2. Why It Matters

These protocols power more syntax than many developers realize:

- `for...of`
- array spread: `[...iterable]`
- function call spread: `fn(...iterable)`
- destructuring: `const [first] = iterable`
- `Array.from(iterable)`
- `Map`, `Set`, strings, generators, and many DOM collections

When you understand the protocol, errors like "object is not iterable" become straightforward instead of mysterious.

## 3. Official Mechanism

An object is iterable when JavaScript can call:

```js
object[Symbol.iterator]()
```

That call must return an iterator. Each call to `iterator.next()` returns an object shaped like:

```js
{ value: nextValue, done: false }
```

When iteration finishes:

```js
{ value: undefined, done: true }
```

Some objects are iterable and also their own iterator. Array iterators behave this way:

```js
const iterator = ["x"][Symbol.iterator]();

console.log(iterator[Symbol.iterator]() === iterator);
// true
```

## 4. Mental Model

Iterable means "JavaScript knows how to ask this object for values."

Iterator means "this is the live cursor currently walking through those values."

An iterable can usually create a fresh iterator each time. A single iterator itself is stateful and can be exhausted.

## 5. `for...of` vs `for...in`

`for...of` reads iterable values:

```js
const items = ["first", "second"];

for (const value of items) {
  console.log(value);
}

// first
// second
```

`for...in` reads enumerable property keys:

```js
const items = ["first", "second"];

for (const key in items) {
  console.log(key);
}

// "0"
// "1"
```

For arrays, use `for...of` when you want values. Use `for...in` mainly for object property enumeration, and even then prefer `Object.keys`, `Object.values`, or `Object.entries` when that is clearer.

## 6. Plain Objects Are Not Iterable By Default

```js
const user = { id: 1, name: "Mina" };

try {
  console.log([...user]);
} catch (error) {
  console.log(error.name);
  // TypeError
}
```

Object spread is different:

```js
const copy = { ...user };
console.log(copy);
// { id: 1, name: "Mina" }
```

Array spread needs an iterable. Object spread copies enumerable own properties.

To iterate object data, choose the shape explicitly:

```js
console.log(Object.keys(user));
// ["id", "name"]

console.log(Object.values(user));
// [1, "Mina"]

console.log(Object.entries(user));
// [["id", 1], ["name", "Mina"]]
```

## 7. Array-Like vs Iterable

Array-like means an object has indexed properties and `length`. Iterable means it has `[Symbol.iterator]`.

```js
const arrayLike = {
  0: "a",
  1: "b",
  length: 2,
};

console.log(Array.from(arrayLike));
// ["a", "b"]

try {
  console.log([...arrayLike]);
} catch (error) {
  console.log(error.name);
  // TypeError
}
```

`Array.from` can handle both iterable and array-like objects. Spread requires iterable.

### DOM Example

```js
const buttons = document.querySelectorAll("button");

// NodeList is iterable in modern browsers, so this usually works:
const asArray = [...buttons];

// Array.from is explicit and also supports array-like conversion:
const labels = Array.from(buttons, button => button.textContent?.trim() ?? "");
```

Use conversion when you need array methods such as `map`, `filter`, `toSorted`, or `reduce`.

## 8. Iterator Exhaustion

```js
const iterator = ["a", "b"][Symbol.iterator]();

console.log([...iterator]);
// ["a", "b"]

console.log([...iterator]);
// []
```

The iterator was consumed the first time. If you need to iterate again, keep the original iterable and create a new iterator:

```js
const values = ["a", "b"];

console.log([...values]);
// ["a", "b"]

console.log([...values]);
// ["a", "b"]
```

## 9. Custom Iterable

```js
const pageRange = {
  start: 1,
  end: 3,

  [Symbol.iterator]() {
    let current = this.start;
    const end = this.end;

    return {
      next() {
        if (current <= end) {
          return { value: current++, done: false };
        }

        return { value: undefined, done: true };
      },
    };
  },
};

console.log([...pageRange]);
// [1, 2, 3]
```

This is not common in everyday UI work, but it explains how generators, lazy ranges, custom data structures, and library abstractions integrate with JavaScript syntax.

Generator equivalent:

```js
function* range(start, end) {
  for (let value = start; value <= end; value += 1) {
    yield value;
  }
}

console.log([...range(1, 3)]);
// [1, 2, 3]
```

## 10. Real Frontend Bug: Converting API Maps

### Problem

An API returns an object keyed by ID:

```js
const usersById = {
  u1: { id: "u1", name: "Mina" },
  u2: { id: "u2", name: "Sara" },
};

const names = [...usersById].map(user => user.name);
```

### Bug

> [!warning] Plain objects aren't iterable
> Array spread (`[...obj]`), `for...of`, and destructuring iteration need the iterable protocol, which plain objects don't implement — so they throw. Convert first with `Object.entries`/`keys`/`values`, or use a `Map` when you need an iterable keyed collection.

### Fix

```js
const names = Object.values(usersById).map(user => user.name);

console.log(names);
// ["Mina", "Sara"]
```

If you need IDs too:

```js
const rows = Object.entries(usersById).map(([id, user]) => ({
  id,
  label: user.name,
}));

console.log(rows);
// [{ id: "u1", label: "Mina" }, { id: "u2", label: "Sara" }]
```

### Tradeoff

Objects are good for JSON and simple lookup. `Map` is better when keys are not strings, insertion order matters as a first-class behavior, or you need frequent additions/removals with collection semantics.

## 11. Production Checklist

- Use `for...of` for iterable values.
- Use `for...in` cautiously for object keys.
- Convert object maps with `Object.values` or `Object.entries`.
- Convert array-like values with `Array.from`.
- Remember that iterators are stateful and can be exhausted.
- Do not assume any object can be array-spread.
- Use `Map` or `Set` when the collection semantics are part of the domain.
- Use generators when lazy value production improves clarity or memory use.

## 12. Interview Answer

**Short version:** An iterable has `[Symbol.iterator]()`; an iterator has `next()` returning `{ value, done }`. Syntax like `for...of`, spread, destructuring, and `Array.from` uses this protocol.

**Strong version:** Iterable and iterator are separate concepts. An iterable can produce an iterator, while an iterator is the cursor that advances through values. Arrays, strings, maps, sets, and generators are iterable. Plain objects are not iterable by default, so `[...]` on a plain object throws; use `Object.values`, `Object.entries`, or define `[Symbol.iterator]` intentionally. In production frontend work, this matters when converting API objects, DOM collections, maps, and sets into UI-ready arrays.

## 13. Common Mistakes

- Confusing `for...in` keys with `for...of` values.
- Trying to spread a plain object into an array.
- Assuming object spread and array spread use the same mechanism.
- Reusing an exhausted iterator.
- Assuming array-like always means iterable.
- Converting a collection to an array too early when lazy iteration would be enough.
- Using a custom iterable where a simple array or object would be clearer.

## 14. Practice

1. Implement a custom iterable that yields page numbers from 1 to 5.
2. Explain why `[...{ a: 1 }]` throws.
3. Convert an object map into rows using `Object.entries`.
4. Show the difference between `for...in` and `for...of` on an array.
5. Consume the same iterator twice and explain the output.

## Related Notes

- [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]
- [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
- [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]
- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[01 - Roadmap|Roadmap]]
