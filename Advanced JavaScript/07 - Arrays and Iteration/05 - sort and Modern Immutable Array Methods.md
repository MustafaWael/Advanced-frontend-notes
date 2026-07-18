---
tags: [javascript, arrays, sort-and-modern-immutable-array-methods]
module: "07 - Arrays and Iteration"
priority: must-know
status: not-started
---

# sort and Modern Immutable Array Methods

## Maturity Target

- Priority: #must-know
- Study time: 80-110 minutes
- Interview signal: you can explain default string sorting, comparator return values, mutation, stability, and ES2023 copy methods.
- Production signal: you sort UI data correctly without mutating state, props, or cache results.
- Dependencies: [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]], [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]

## Source Anchors

- [MDN Array.prototype.sort](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort)
- [MDN Array.prototype.toSorted](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/toSorted)
- [MDN Array.prototype.toReversed](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/toReversed)
- [MDN Array.prototype.toSpliced](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/toSpliced)
- [MDN Array.prototype.with](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/with)
- [React: Updating Arrays in State](https://react.dev/learn/updating-arrays-in-state)

## 1. Concept

`sort` reorders an array in place and returns the same array reference. By default, it compares values as strings. Modern immutable methods such as `toSorted`, `toReversed`, `toSpliced`, and `with` return changed copies instead of mutating the receiver.

This topic combines two common frontend risks:

- correctness: is the order actually what the user expects?
- ownership: did the code mutate data owned by another component, state store, or cache?

## 2. Why It Matters

Sorting appears in product grids, tables, search results, invoices, dashboards, menus, and admin screens. The bug is often subtle because the UI still renders something, just not the right order or not from the right data owner.

```js
const numbers = [1, 10, 2];

console.log(numbers.sort());
// [1, 10, 2]
```

The result is lexicographic string order, not numeric order.

## 3. Official Mechanism

`sort(compareFn?)`:

- mutates the original array
- returns the same array object
- converts elements to strings for default comparison
- calls `compareFn(a, b)` when provided
- expects a negative number when `a` should come before `b`
- expects a positive number when `a` should come after `b`
- treats `0` or `NaN` as equal ordering for those two items
- is stable in modern ECMAScript, so equal items keep their relative order

Comparator shape:

```js
items.sort((a, b) => {
  if (a should come before b) return -1;
  if (a should come after b) return 1;
  return 0;
});
```

Numeric shorthand:

```js
numbers.sort((a, b) => a - b); // ascending
numbers.sort((a, b) => b - a); // descending
```

## 4. Mental Model

Sorting has two contracts:

1. ordering contract: the comparator must consistently describe order
2. ownership contract: the array being sorted must be safe to mutate

If either contract is wrong, the code can look reasonable and still fail in production.

## 5. Numeric Sorting

```js
const values = [10, 2, 1];

console.log([...values].sort());
// [1, 10, 2]

console.log([...values].sort((a, b) => a - b));
// [1, 2, 10]

console.log(values);
// [10, 2, 1]
```

> [!example] Copy plus comparator walkthrough
> The spread copy protects the original array. The comparator fixes numeric order.

## 6. Object Sorting

```js
const products = [
  { id: "p1", name: "Monitor", price: 300 },
  { id: "p2", name: "Cable", price: 10 },
  { id: "p3", name: "Keyboard", price: 100 },
];

const byPrice = products.toSorted((a, b) => a.price - b.price);

console.log(byPrice.map(product => product.id));
// ["p2", "p3", "p1"]
console.log(products.map(product => product.id));
// ["p1", "p2", "p3"]
```

`toSorted` returns a new array. The product objects inside are still shared, so do not mutate them while rendering.

## 7. String Sorting For Real Users

For basic English-like labels:

```js
const names = ["Zoe", "Adam", "Mina"];
const sorted = names.toSorted((a, b) => a.localeCompare(b));

console.log(sorted);
// ["Adam", "Mina", "Zoe"]
```

For repeated sorting with locale and numeric behavior, create an `Intl.Collator` once:

```js
const collator = new Intl.Collator("en", {
  numeric: true,
  sensitivity: "base",
});

const files = ["file2", "file10", "file1"];
console.log(files.toSorted(collator.compare));
// ["file1", "file2", "file10"]
```

> [!tip] Reuse a collator intentionally
> Production tradeoff: `Intl.Collator` is more intentional and can be faster when reused for many comparisons, but it is also a localization decision. Match the product requirements.

## 8. Real Frontend Bug: Sorting Props

### Problem

```jsx
function ProductList({ products }) {
  const sorted = products.sort((a, b) => a.price - b.price);

  return sorted.map(product => (
    <ProductCard key={product.id} product={product} />
  ));
}
```

### Bug

> [!warning] Sorting props mutates parent data
> The child component mutates `products`, which is owned by the parent. Another component using the same array may now render the modified order. In development, React re-renders can make the bug look inconsistent.

### Fix

```jsx
function ProductList({ products }) {
  const sorted = products.toSorted((a, b) => a.price - b.price);

  return sorted.map(product => (
    <ProductCard key={product.id} product={product} />
  ));
}
```

Fallback:

```js
const sorted = [...products].sort((a, b) => a.price - b.price);
```

### Tradeoff

> [!tip] Copy cost is usually worth it
> Copying before sorting costs memory and time proportional to the array size. That is usually correct for props/state. For extremely large data, prefer server-side sorting, pagination, virtualization, or memoizing the sorted result on stable inputs.

## 9. Bad Comparator Patterns

### Boolean Comparator

```js
const values = [3, 1, 2];

console.log(values.toSorted((a, b) => a > b));
// Engine-dependent-looking mistakes can appear because true/false become 1/0.
```

Return negative, positive, or zero numbers instead:

```js
console.log(values.toSorted((a, b) => a - b));
// [1, 2, 3]
```

### Non-Deterministic Comparator

```js
items.sort(() => Math.random() - 0.5);
```

> [!warning] Random sort is not shuffle
> This is not a reliable shuffle. Sorting algorithms assume the comparator is consistent. Use a real shuffle such as Fisher-Yates on a copied array when you need random order.

## 10. Modern Immutable Methods

### `toSorted`

```js
const next = items.toSorted((a, b) => a.rank - b.rank);
```

### `toReversed`

```js
const newestFirst = comments.toReversed();
```

### `toSpliced`

```js
const withoutDeleted = items.toSpliced(index, 1);
const withInserted = items.toSpliced(index, 0, newItem);
```

### `with`

```js
const next = scores.with(2, 99);
```

These methods are copy-returning, not deep-copying:

```js
const original = [{ id: 1, selected: false }];
const next = original.with(0, original[0]);

next[0].selected = true;
console.log(original[0].selected);
// true
```

To update an object item safely:

```js
const next = original.with(0, { ...original[0], selected: true });
```

## 11. Production Checklist

- Sort with a comparator for numbers, dates, prices, priorities, and ranks.
- Use `localeCompare` or `Intl.Collator` for user-facing strings.
- Do not call `sort` or `reverse` directly on props/state/cache arrays.
- Prefer `toSorted` and `toReversed`; use spread-copy fallbacks when needed.
- Keep comparators pure and deterministic.
- Tie-break equal items when stable user-facing order matters.
- Avoid sorting huge lists on every render or keystroke.
- Treat immutable array methods as shallow.

## Real-World Use Cases

### Sorting a feed by date

A blog index sorts posts newest-first. Dates arrive as ISO strings, so the default sort or `a - b` on the raw strings both mislead.

```js
const newestFirst = posts.toSorted(
  (a, b) => new Date(b.publishedAt) - new Date(a.publishedAt)
);
```

Works because subtracting `Date` objects coerces them to millisecond timestamps, giving the numeric comparator `sort` expects — see [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]].

> [!tip] Uniform ISO-8601 UTC strings sort correctly as strings
> If every value looks like `2026-07-16T09:30:00Z`, `(a, b) => b.publishedAt.localeCompare(a.publishedAt)` is correct and skips two `Date` allocations per comparison. It breaks the moment mixed timezones or formats appear — only use it when the API contract guarantees the format.

### Pinned-first conversation list

A chat sidebar shows pinned conversations on top, each group ordered by most recent message. One comparator with a fall-through tie-breaker handles both.

```js
const ordered = conversations.toSorted(
  (a, b) =>
    Number(b.pinned) - Number(a.pinned) ||
    b.lastMessageAt - a.lastMessageAt
);
```

Works because a comparator only needs to return a number: `Number(b.pinned) - Number(a.pinned)` yields `-1/0/1` for the boolean rank, and `||` falls through to the timestamp only when the first key ties (returns `0`). Stable sort guarantees anything still tied keeps its previous relative order.

### Optimistic inline edit with `with`

A reviews list lets the user change a star rating without waiting for the server. `with` replaces one slot immutably; the object itself must also be copied.

```js
setReviews(prev => {
  const index = prev.findIndex(review => review.id === reviewId);
  if (index === -1) return prev;
  return prev.with(index, { ...prev[index], rating: nextRating });
});
```

Works because `with` returns a new array (React sees a new state reference) and the inner spread copies the changed item — copy-returning methods are shallow, so skipping the spread would mutate an object the server cache may still share.

> [!warning] `with(-1, ...)` replaces the last element
> `with` accepts negative indexes counting from the end. If `findIndex` misses and returns `-1`, an unguarded `prev.with(index, ...)` silently overwrites the **last** review instead of throwing. Always guard the `-1` case.

See [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]] and [[07 - Arrays and Iteration/04 - find some every includes|find some every includes]].

## 12. Interview Answer

**Short version:** `sort` mutates the array and defaults to string comparison. Use a comparator for numeric or custom order, and use `toSorted` or a copied array when you must not mutate.

**Strong version:** `sort` returns the same array reference after reordering it in place. Without a comparator, elements are converted to strings, so numeric arrays can sort incorrectly. A comparator should return a negative number, positive number, or zero to describe order, and it should be deterministic. Modern JavaScript provides `toSorted`, `toReversed`, `toSpliced`, and `with` for immutable update patterns, which are especially useful with React state and props. These methods copy the array container but do not deep-clone object items.

## 13. Common Mistakes

- Assuming `[10, 2, 1].sort()` returns `[1, 2, 10]`.
- Sorting props or React state directly.
- Returning `true` or `false` from a comparator.
- Mutating object items after using an immutable array method.
- Sorting on every render without considering list size.
- Forgetting stable sort still needs a tie-breaker when product requirements demand deterministic secondary order.
- Using random sort as a shuffle.

## 14. Practice

1. Predict the output of `[10, 2, 1].sort()`.
2. Write ascending and descending comparators for numbers.
3. Sort products by `inStock` first, then price, then name.
4. Rewrite a mutating `splice` update using `toSpliced`.
5. Explain why `toSorted` fixes array identity but not nested object mutation.

## Related Notes

- [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]
- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[01 - Roadmap|Roadmap]]
