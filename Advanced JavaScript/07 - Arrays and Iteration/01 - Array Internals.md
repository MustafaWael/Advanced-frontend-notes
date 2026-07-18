---
tags: [javascript, arrays, array-internals]
module: "07 - Arrays and Iteration"
priority: must-know
status: not-started
---

# Array Internals

## Maturity Target

- Priority: #must-know
- Study time: 90 minutes
- Interview signal: you can explain arrays as objects with special index and length behavior, including sparse arrays and holes.
- Production signal: you can avoid accidental holes, expensive transformations, state mutation, and wrong assumptions about array-like data.
- Dependencies: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]], [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]

## Source Anchors

- [MDN - Array](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array)
- [MDN - Array length](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/length)
- [MDN - Indexed collections](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Indexed_collections)
- [ECMAScript 2026 - Array exotic objects](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-array-exotic-objects)
- [React - Updating arrays in state](https://react.dev/learn/updating-arrays-in-state)

## 1. Concept

JavaScript arrays are objects optimized for ordered, integer-indexed collections. They are resizable, zero-indexed, and have a special `length` property.

```js
const items = ["a", "b"];

console.log(typeof items); // "object"
console.log(Array.isArray(items)); // true
console.log(items.length); // 2
console.log(items[0]); // "a"
```

Array indexes are property keys that look like non-negative integers. The key is technically a string property, but arrays give those keys special length behavior.

```js
const items = [];

items[0] = "a";
items[2] = "c";

console.log(items.length); // 3
console.log(Object.keys(items)); // ["0", "2"]
```

## 2. Why It Matters

Arrays sit at the center of frontend work:

- Rendering lists in React.
- Transforming API results.
- Filtering/searching/sorting data.
- Managing selections.
- Building lookup maps.
- Handling NodeLists, FormData, URLSearchParams, Sets, and Maps.

> [!warning] Arrays are not simple lists
> Array bugs often come from treating arrays as if they were simple contiguous lists. In JavaScript, arrays can have holes, named properties, shared object references, and mutating methods.

## 3. Official Mechanism

ECMAScript describes arrays as Array exotic objects. They behave like objects but have special rules for array-index properties and the `length` property.

Important rules:

- `length` is one more than the highest array index, not necessarily the count of real elements.
- Setting an index at or beyond the current length updates `length`.
- Reducing `length` deletes elements at indexes beyond the new length.
- Non-index properties do not affect `length`.
- Many array copy operations are shallow.

```js
const arr = ["a", "b"];

arr[5] = "f";
arr.label = "letters";

console.log(arr.length); // 6
console.log(arr.label); // "letters"
console.log(Object.keys(arr)); // ["0", "1", "5", "label"]
```

## 4. Holes vs `undefined`

A hole is a missing index. It is not the same as an index that exists with value `undefined`.

```js
const withHole = ["a", , "c"];
const withUndefined = ["a", undefined, "c"];

console.log(1 in withHole); // false
console.log(1 in withUndefined); // true

console.log(withHole[1]); // undefined
console.log(withUndefined[1]); // undefined
```

Some array methods skip holes, while newer iterator-like behavior may treat them as `undefined`.

```js
const arr = ["a", , "c"];

arr.forEach((value, index) => {
  console.log(index, value);
});

// Output:
// 0 "a"
// 2 "c"

console.log([...arr]); // ["a", undefined, "c"]
```

> [!tip] Avoid sparse arrays in app data
> Production habit: avoid sparse arrays for app data. If a value is unknown, store `null`, `undefined`, or a typed state object intentionally.

## 5. Length Behavior

```js
const items = ["a", "b", "c"];

items.length = 1;

console.log(items); // ["a"]

items.length = 3;

console.log(items); // ["a", empty x 2]
console.log(1 in items); // false
```

Increasing `length` creates holes. Decreasing `length` deletes elements.

## 6. Arrays Are Not Associative Arrays

Do not use arbitrary string keys for list data.

```js
const users = [];

users["active"] = 3;

console.log(users.length); // 0
console.log(users.active); // 3
```

Use an object or `Map` for keyed data:

```js
const usersById = new Map();

usersById.set("u1", { name: "Ava" });

console.log(usersById.get("u1")); // { name: "Ava" }
```

## 7. Shallow Copy Behavior

Array copy operations copy element references, not nested objects.

```js
const original = [{ id: 1, seen: false }];
const copy = [...original];

copy[0].seen = true;

console.log(original[0].seen); // true
console.log(original === copy); // false
console.log(original[0] === copy[0]); // true
```

In React state, copying the array is not enough if you mutate objects inside it. Copy the changed item too.

```js
const next = original.map((item) =>
  item.id === 1 ? { ...item, seen: true } : item
);
```

## 8. Real Frontend Scenario: Sparse Results

> [!example] Tracing an accidental sparse array
> Problem: an API mapper creates holes by assigning by server position.

```js
function buildRows(products) {
  const rows = [];

  for (const product of products) {
    rows[product.position] = product;
  }

  return rows;
}

const rows = buildRows([
  { id: "a", position: 0 },
  { id: "c", position: 2 }
]);

console.log(rows.length); // 3
console.log(1 in rows); // false
```

> [!warning] Holes behave inconsistently downstream
> Bug: downstream code uses `forEach`, which skips the hole, while rendering with spread might expose `undefined`.

Fix with explicit placeholders:

```js
function buildRows(products, size) {
  const rows = Array.from({ length: size }, () => null);

  for (const product of products) {
    rows[product.position] = product;
  }

  return rows;
}

console.log(buildRows([{ id: "a", position: 0 }], 3));
// [{ id: "a", position: 0 }, null, null]
```

Tradeoff: explicit `null` placeholders force the UI to handle empty states intentionally.

## 9. Performance Mental Model

Engines optimize dense arrays with consistent element types better than chaotic arrays.

Helpful habits:

- Prefer dense arrays for list data.
- Avoid mixing list elements with arbitrary named properties.
- Avoid repeated `delete arr[i]`; use `splice`, `filter`, or explicit placeholders.
- Avoid mutating arrays while iterating unless you have tested the exact behavior.
- For very large lists, reduce allocations, memoize derived data, virtualize rendering, or move transformations earlier.

Measure before optimizing. These are design guardrails, not reasons to write cryptic loops by default.

## Real-World Use Cases

### Classic interview trap: `Array(n).map` renders nothing

A loading state should show six skeleton cards while products fetch. The component renders an empty list and nobody sees why.

```jsx
function ProductGridSkeleton() {
  return Array(6).map((_, i) => <SkeletonCard key={i} />);
  // Renders: nothing
}
```

Trace it mechanism by mechanism: `Array(6)` creates an array whose `length` is 6 but with **zero index properties** — six holes, not six `undefined`s. `map` visits only existing indexes (it checks `i in arr` before calling the callback), so the callback never runs and the result is another 6-hole array. React renders holes as nothing.

Fix by materializing real elements first:

```jsx
return Array.from({ length: 6 }, (_, i) => <SkeletonCard key={i} />);
// or: [...Array(6)].map(...) — spread converts holes to undefined
```

Works because `Array.from` writes an actual value at every index, and spread uses the iterator protocol, which reads holes as `undefined`. See [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]] and [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]].

### Converting array-like DOM collections

A pricing page needs the tallest card height to equalize a row. `querySelectorAll` returns a `NodeList` — array-like (indexes plus `length`) but missing `map`, `filter`, and friends.

```js
const cards = document.querySelectorAll(".pricing-card");

const maxHeight = Math.max(
  ...Array.from(cards, (card) => card.getBoundingClientRect().height)
);

cards.forEach((card) => (card.style.minHeight = `${maxHeight}px`));
```

Works because "array" behavior in JavaScript is just indexed properties plus `length` — `Array.from` accepts anything with that shape (or an iterator) and builds a real dense array. The same trick applies to `FormData.entries()`, `arguments`, and `HTMLCollection`.

> [!tip] `Array.from(collection, mapFn)` maps in the same pass
> The second argument avoids allocating an intermediate array compared to `Array.from(cards).map(...)`.

### Flushing a shared buffer with `length = 0`

An analytics module batches events and flushes every 5 seconds. Multiple closures hold a reference to the same buffer, so reassigning it would silently break them.

```js
const pendingEvents = [];

export function track(event) {
  pendingEvents.push(event);
}

setInterval(() => {
  if (pendingEvents.length === 0) return;
  navigator.sendBeacon("/analytics", JSON.stringify(pendingEvents));
  pendingEvents.length = 0; // empties the array every holder can see
}, 5_000);
```

Works because reducing `length` **deletes all elements beyond the new length** on the same array object — every closure that captured `pendingEvents` observes the flush. `pendingEvents = []` would only rebind a local reference (and throws on `const`). See [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]].

> [!warning] This is deliberate shared mutation
> This pattern is correct only for a module-owned buffer with intentional shared state. Never do this to React state or props — see [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]].

## 10. Interview Answer

Short answer:

> JavaScript arrays are objects with special behavior for integer-like indexes and `length`. They are resizable, zero-indexed, and their copy operations are shallow.

Deeper answer:

> Setting an array index can update `length`; reducing `length` deletes elements. Arrays can be sparse, meaning some indexes are holes, and methods differ in how they treat holes. Arbitrary string keys are object properties and do not count as array elements.

Production answer:

> I avoid sparse arrays and named properties on arrays in frontend data. For React state, I treat arrays as immutable and remember that array copies are shallow, so nested item objects must also be copied when changed.

## 11. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "`length` is the number of real elements." | It is based on the highest array index plus one. |
| "A hole and `undefined` are the same." | They read similarly but differ for existence and some methods. |
| "Arrays are good dictionaries." | Use objects or `Map` for keyed data. |
| "Spreading an array deep-copies items." | It copies references shallowly. |
| "`delete arr[i]` removes and shifts items." | It creates a hole; use `splice` or `filter` depending on intent. |

## 12. Practice

1. Predict the output:

```js
const arr = ["a"];

arr[3] = "d";
arr.extra = true;

console.log(arr.length);
console.log(Object.keys(arr));
console.log(1 in arr);
```

Expected output:

```txt
4
["0", "3", "extra"]
false
```

2. Explain why `[...array]` does not deep-copy item objects.
3. Convert a sparse-array builder into one that uses explicit `null` placeholders.
4. Explain why `Array.isArray(value)` is better than `typeof value === "object"` for arrays.
5. Explain why array methods may skip holes.

## Related Notes

- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
- [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]]
- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]
- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[01 - Roadmap|Roadmap]]
