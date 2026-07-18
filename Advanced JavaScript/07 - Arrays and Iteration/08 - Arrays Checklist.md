---
tags: [javascript, arrays, arrays-checklist]
module: "07 - Arrays and Iteration"
priority: must-know
status: not-started
---

# Arrays Checklist

Use this as an active review. A checkbox is complete only when you can explain the idea, predict the output, name the production bug, and write the safer version without looking.

## Fast Track Order

1. [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]
2. [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
3. [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
4. [[07 - Arrays and Iteration/04 - find some every includes|find some every includes]]
5. [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]
6. [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]]
7. [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]]

## Core Understanding

- [ ] I can explain that JavaScript arrays are objects with special index/`length` behavior.
- [ ] I can explain why arrays are not associative arrays and when `Map` or an object lookup is a better shape.
- [ ] I can explain the difference between a hole and an explicit `undefined`.
- [ ] I can name which common methods skip holes and which treat holes like `undefined`.
- [ ] I can explain shallow copy behavior for spread, `slice`, `concat`, `map`, `filter`, and modern immutable methods.
- [ ] I can classify common methods as mutating, non-mutating, or copy-returning modern alternatives.
- [ ] I can explain why `sort`, `reverse`, `splice`, `fill`, and `copyWithin` are dangerous on shared arrays.
- [ ] I can explain why `toSorted`, `toReversed`, `toSpliced`, and `with` help React state updates.
- [ ] I can explain iterable vs iterator, and what `[Symbol.iterator]` does.
- [ ] I can distinguish `for...of`, `for...in`, `Object.entries`, spread, and `Array.from`.

## Method Selection

- [ ] I use `map` when each input item should become one output item.
- [ ] I use `filter` when I need all matching items.
- [ ] I use `reduce` when I need a total, grouping, lookup map, or summary.
- [ ] I use `forEach` only for side effects, not to build arrays.
- [ ] I use `find` when I need the first matching item.
- [ ] I use `findIndex` when I need the first matching position.
- [ ] I use `some` when I need to know whether any item matches.
- [ ] I use `every` when I need to know whether all items match.
- [ ] I use `includes` for primitive membership checks.
- [ ] I use `Set` for repeated primitive membership checks.
- [ ] I build lookup maps for repeated ID lookups instead of calling `find` inside `map`.

## React And Frontend Readiness

- [ ] I never mutate React state arrays directly.
- [ ] I never sort or reverse props directly before rendering.
- [ ] I copy every changed level when updating nested state.
- [ ] I store selected IDs instead of selected object references when data can refetch.
- [ ] I use stable IDs as React keys for reorderable lists.
- [ ] I handle `find` returning `undefined` after refetch, deletion, or permission changes.
- [ ] I understand when `useMemo` helps and when unstable dependencies make it useless.
- [ ] I can explain why render-time transformations must be pure.
- [ ] I can choose between client-side filtering/sorting and server-side filtering/sorting.
- [ ] I can name when virtualization is the right answer for large lists.

## Code Output Drills

### Holes vs `undefined`

```js
const values = ["a", , "c"];
const visited = [];

values.forEach((value, index) => {
  visited.push(index);
});

console.log(1 in values);
console.log(values[1]);
console.log(visited);
console.log([...values]);
```

Expected:

```js
false
undefined
[0, 2]
["a", undefined, "c"]
```

Why: index `1` is a hole, not an own property. `forEach` skips it. Spread uses iteration and materializes it as `undefined`.

### Shallow Copy

```js
const original = [{ id: 1, done: false }];
const copy = [...original];

copy[0].done = true;

console.log(original === copy);
console.log(original[0] === copy[0]);
console.log(original[0].done);
```

Expected:

```js
false
true
true
```

Why: the array container is new, but the object inside is shared.

### `fill` Shared Reference

```js
const rows = Array(2).fill([]);
rows[0].push("x");

console.log(rows[0]);
console.log(rows[1]);
console.log(rows[0] === rows[1]);
```

Expected:

```js
["x"]
["x"]
true
```

Fix:

```js
const rows = Array.from({ length: 2 }, () => []);
```

### Default Sort

```js
const numbers = [10, 2, 1];

console.log([...numbers].sort());
console.log([...numbers].sort((a, b) => a - b));
console.log(numbers);
```

Expected:

```js
[1, 10, 2]
[1, 2, 10]
[10, 2, 1]
```

Why: default sort compares strings; numeric sort needs a comparator. Spread protects the original array.

### `reduce` Without Initial Value

```js
try {
  [].reduce((sum, value) => sum + value);
} catch (error) {
  console.log(error.name);
}

console.log([].reduce((sum, value) => sum + value, 0));
```

Expected:

```js
TypeError
0
```

Why: an empty array has no first existing item to use as the initial accumulator.

### `includes` vs `indexOf` With `NaN`

```js
console.log([NaN].includes(NaN));
console.log([NaN].indexOf(NaN));
```

Expected:

```js
true
-1
```

Why: `includes` uses SameValueZero; `indexOf` does not find `NaN`.

### Empty `some` And `every`

```js
console.log([].some(Boolean));
console.log([].every(Boolean));
```

Expected:

```js
false
true
```

Why: "at least one" is false for empty input; "all items pass" is vacuously true.

### Iterator Exhaustion

```js
const iterator = ["a", "b"][Symbol.iterator]();

console.log([...iterator]);
console.log([...iterator]);
```

Expected:

```js
["a", "b"]
[]
```

Why: the iterator is a stateful cursor and was consumed.

## Production Scenarios To Practice

- [ ] Rewrite a component that mutates `props.items.sort(...)` into a non-mutating version.
- [ ] Replace `filter(...).length > 0` with `some` in a permission check.
- [ ] Build `userById` from a `users` array and use it to render order rows.
- [ ] Group tasks by status without mutating the original tasks.
- [ ] Convert an API object map into rows with `Object.entries`.
- [ ] Fix a selected-row component where `find` can return `undefined`.
- [ ] Add a numeric comparator to a price sort.
- [ ] Replace an async `forEach` with either `for...of` or `Promise.all`.
- [ ] Turn `Array(3).fill({ fields: [] })` into a safe factory version.
- [ ] Decide whether a large list transformation belongs in render, `useMemo`, the server, or virtualization.

## Interview Prompts

1. What is the difference between mutating and non-mutating array methods?
2. Why is `sort` dangerous in React render code?
3. Why does `[10, 2, 1].sort()` not produce numeric order?
4. What is the difference between `map` and `forEach`?
5. Why should `reduce` usually receive an initial value?
6. When would you use `some` instead of `filter`?
7. Why can `includes` find `NaN` while `indexOf` cannot?
8. What is the difference between array spread and object spread?
9. What does it mean for an object to be iterable?
10. How would you optimize rendering a searchable list of 50,000 items?

## Self-Review Rubric

| Level | What you can do |
| --- | --- |
| Junior | Use `map`, `filter`, and `sort` in simple examples. |
| Growing mid-level | Explain mutation, shallow copy, and method selection. |
| Strong mid-level | Predict code output, prevent React identity bugs, and choose data shapes intentionally. |
| Senior signal | Discuss ownership, complexity, memoization limits, server/client boundaries, and user-facing tradeoffs. |

## Related Notes

- [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]
- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
- [[07 - Arrays and Iteration/04 - find some every includes|find some every includes]]
- [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]
- [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]]
- [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[01 - Roadmap|Roadmap]]
