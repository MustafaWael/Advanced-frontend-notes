---
tags: [javascript, arrays, mutating-vs-non-mutating-methods]
module: "07 - Arrays and Iteration"
priority: must-know
status: not-started
---

# Mutating vs Non Mutating Methods

## Maturity Target

- Priority: #must-know
- Study time: 75-100 minutes
- Interview signal: you can classify array methods, explain reference identity, and predict React state bugs.
- Production signal: you avoid mutating shared arrays unless the ownership is local and intentional.
- Dependencies: [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]], [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]], [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]

## Source Anchors

- [MDN Array](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array)
- [MDN Array.prototype.sort](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort)
- [MDN Array.prototype.toSorted](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/toSorted)
- [React: Updating Arrays in State](https://react.dev/learn/updating-arrays-in-state)
- [ECMAScript Array Objects](https://tc39.es/ecma262/#sec-array-objects)

## 1. Concept

A mutating method changes the same array object. A non-mutating method leaves the original array alone and returns either a new array, a single value, a boolean, a string, an iterator, or another derived result.

> [!tip] Think ownership, not vocabulary
> The important part is not the vocabulary. The important part is ownership. If an array is only a temporary local value, mutation can be simple and fast. If an array is React state, props, cached API data, or shared between components, mutation can create bugs that are hard to connect back to the line that caused them.

## 2. Why It Matters

In frontend applications, arrays commonly represent:

- server results from `fetch`, React Query, SWR, loaders, or server components
- React state such as selected rows, cart items, form sections, or notifications
- derived view models for tables, menus, search results, and dashboards
- cached data reused by several components

The same method can be harmless in one place and dangerous in another:

```js
const local = [3, 1, 2];
local.sort((a, b) => a - b); // acceptable: local array, owned here

setProducts(products.sort((a, b) => a.price - b.price));
// Bug: mutates the existing state/props array before React receives it.
```

## 3. Official Mechanism

Arrays are objects. Mutating methods write properties on the existing object and often update `length`. Non-mutating methods usually allocate a new result, but they do not deep-clone nested objects.

### Common Mutating Methods

| Method | Mutates what? | Returns | Typical risk |
| --- | --- | --- | --- |
| `push(...items)` | appends to same array | new `length` | state reference stays the same |
| `pop()` | removes last item | removed item | accidental destructive read |
| `unshift(...items)` | prepends to same array | new `length` | expensive reindexing on large arrays |
| `shift()` | removes first item | removed item | expensive reindexing on large arrays |
| `splice(start, deleteCount, ...items)` | removes/inserts in same array | removed items | mutates shared order/content |
| `sort(compareFn?)` | reorders same array | same array reference | props/state order changes globally |
| `reverse()` | reverses same array | same array reference | destructive display transformation |
| `fill(value, start?, end?)` | writes same value into slots | same array reference | shared object reference bug |
| `copyWithin(target, start?, end?)` | copies inside same array | same array reference | surprising overwrite |

### Common Non-Mutating Methods

| Method | Returns | Notes |
| --- | --- | --- |
| `map(fn)` | new array | same length as the visited structure; callback result becomes each element |
| `filter(fn)` | new array | only passing elements are included |
| `reduce(fn, initial)` | accumulated value | can return any type |
| `slice(start?, end?)` | new array | shallow copy of a range |
| `concat(...items)` | new array | shallow combination |
| `flat(depth?)` | new array | removes empty slots at flattened levels |
| `flatMap(fn)` | new array | map then flatten one level |
| `find(fn)` | element or `undefined` | short-circuits |
| `some(fn)` / `every(fn)` | boolean | short-circuit existence/all checks |
| `includes(value)` | boolean | uses SameValueZero comparison |
| `entries()` / `keys()` / `values()` | iterator | no array copy until consumed |

### Modern Immutable Counterparts

ES2023 added copy-returning alternatives for historically mutating operations:

| Old mutating pattern | Copy-returning pattern | Use when |
| --- | --- | --- |
| `arr.sort(compare)` | `arr.toSorted(compare)` | sorted display without changing original |
| `arr.reverse()` | `arr.toReversed()` | reversed display without changing original |
| `arr.splice(i, n, ...items)` | `arr.toSpliced(i, n, ...items)` | remove/insert immutably |
| `arr[index] = value` | `arr.with(index, value)` | replace one slot immutably |

Fallback when support or tooling is uncertain:

```js
const sorted = [...items].sort(compareItems);
const reversed = [...items].reverse();
const removed = items.filter(item => item.id !== deletedId);
const replaced = items.map(item => item.id === updated.id ? updated : item);
```

## 4. Mental Model

Think in two layers:

1. Array identity: is this the same array object or a new array object?
2. Item identity: are the objects inside also copied, or are they shared?

```js
const original = [{ id: 1, seen: false }];
const copy = [...original];

console.log(original === copy); // false
console.log(original[0] === copy[0]); // true

copy[0].seen = true;
console.log(original[0].seen); // true
```

The spread copy protected the array container, not the object inside it.

## 5. Real Frontend Bug: Mutating React State

### Problem

> [!example] Tracing a sorted-table state bug
> A table lets the user sort products by price.

```jsx
function ProductTable({ initialProducts }) {
  const [products, setProducts] = useState(initialProducts);

  function sortByPrice() {
    products.sort((a, b) => a.price - b.price);
    setProducts(products);
  }

  return products.map(product => (
    <ProductRow key={product.id} product={product} />
  ));
}
```

### Bug

> [!warning] Same reference, silent reorder
> `sort` mutates `products` in place. `setProducts(products)` passes the same array reference back to React. Even when a render happens for some other reason, any other code that still holds `initialProducts` can now observe the reordered array.

### Fix

```jsx
function ProductTable({ initialProducts }) {
  const [products, setProducts] = useState(initialProducts);

  function sortByPrice() {
    setProducts(prev => prev.toSorted((a, b) => a.price - b.price));
  }

  return products.map(product => (
    <ProductRow key={product.id} product={product} />
  ));
}
```

If `toSorted` is not available in your target environment:

```js
setProducts(prev => [...prev].sort((a, b) => a.price - b.price));
```

### Why The Fix Works

- `prev.toSorted(...)` returns a different array reference.
- React can observe that the state value changed.
- Other consumers of the previous array are not silently reordered.
- The comparator makes numeric order explicit.

## 6. Real Frontend Bug: `fill` With Objects

### Problem

A form builder creates three empty sections.

```js
const sections = Array(3).fill({ fields: [] });
sections[0].fields.push("email");

console.log(sections.map(section => section.fields.length));
// Expected: [1, 0, 0]
// Actual:   [1, 1, 1]
```

### Bug

> [!warning] fill shares one object reference
> `fill` writes the same object reference into every slot. Each section points at the same `fields` array.

### Fix

```js
const sections = Array.from({ length: 3 }, () => ({ fields: [] }));
sections[0].fields.push("email");

console.log(sections.map(section => section.fields.length));
// [1, 0, 0]
```

### Tradeoff

> [!tip] Use a factory for fresh objects
> `Array.from({ length }, factory)` is slightly more verbose, but it creates a fresh object for each item. That clarity is worth it for forms, grids, and dynamic UI builders.

## 7. Method Choice Patterns

### Add An Item

```js
const next = [...items, newItem];
```

### Remove An Item

```js
const next = items.filter(item => item.id !== removedId);
```

### Replace One Item

```js
const next = items.map(item =>
  item.id === updated.id ? { ...item, ...updated } : item
);
```

### Insert At A Specific Index

```js
const next = [
  ...items.slice(0, index),
  inserted,
  ...items.slice(index),
];

// Modern alternative:
const nextModern = items.toSpliced(index, 0, inserted);
```

### Update Nested Data

```js
const next = todos.map(todo =>
  todo.id === id
    ? { ...todo, meta: { ...todo.meta, done: true } }
    : todo
);
```

Copy every level that changes. Reusing unchanged objects is good; mutating changed objects is not.

## 8. Production Tradeoffs

- Local mutation can be fine inside a function when no one else observes the array.
- Public data, state, props, and cache results should be treated as immutable by default.
- Copying a huge array on every keystroke can be expensive; avoid doing expensive derivations inside hot render paths.
- `useMemo` helps only when the inputs are stable and the computation is meaningfully expensive.
- Immutability is not automatically deep. Spread, `slice`, `concat`, `toSorted`, `toSpliced`, and `with` are shallow for object items.
- Prefer clear immutable code first. Reach for specialized structures, virtualization, workers, pagination, or server-side sorting only when data size and interaction cost justify it.

## Real-World Use Cases

### Kanban drag-and-drop reorder

A board library (dnd-kit, @hello-pangea/dnd) reports `from` and `to` indexes on drop. The reorder must produce a new array or React never re-renders the column.

```js
function moveCard(cards, from, to) {
  const moved = cards[from];
  return cards.toSpliced(from, 1).toSpliced(to, 0, moved);
}

function handleDragEnd(result) {
  if (!result.destination) return;
  setCards(prev => moveCard(prev, result.source.index, result.destination.index));
}
```

Works because each `toSpliced` returns a fresh array — the remove and the insert never touch the state array, so React sees a new reference and the drag library's own snapshot of the old order stays intact. The mutating version (`cards.splice(from, 1)` then `splice(to, 0, ...)`) edits state in place mid-drag.

### Mutating a React Query cache entry in place

An optimistic "add product" writes into the cached array directly and nothing updates.

```js
// Bug: getQueryData returns the live cached array, not a copy
const products = queryClient.getQueryData(["products"]);
products.push(optimisticProduct); // silently corrupts the cache

// Fix: hand the cache a new array
queryClient.setQueryData(["products"], old => [...(old ?? []), optimisticProduct]);
```

Works/fails on array identity: React Query (and Redux, Zustand, SWR) detect changes by comparing references. `push` keeps the same reference, so no subscriber re-renders — and worse, the "clean" cache is now polluted before any rollback logic runs.

> [!warning] Cache reads are live references
> Anything returned by `getQueryData`, a Redux selector, or a Zustand store is shared. Treat it as frozen; produce updates with copy-returning methods only.

### Undo history for an editor

A drawing tool keeps snapshots in state. `pop()` looks natural for undo but it is a destructive read on the state array.

```js
function undo() {
  const last = history.at(-1);
  if (!last) return;
  restoreSnapshot(last);
  setHistory(prev => prev.slice(0, -1)); // new array without the last snapshot
}

function commit(snapshot) {
  setHistory(prev => [...prev.slice(-49), snapshot]); // cap at 50, immutably
}
```

Works because `at(-1)` and `slice` are non-mutating: the read and the state update stay separate, so React StrictMode's double-invoked updaters and time-travel devtools both see consistent history. `history.pop()` would mutate state during render logic and return the same reference to `setHistory`.

See [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]] and [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]].

## 9. Interview Answer

**Short version:** Mutating methods change the original array. Non-mutating methods return a new result and leave the original array reference alone.

**Strong version:** In JavaScript, arrays are objects. Methods like `push`, `splice`, `sort`, `reverse`, `fill`, and `copyWithin` write to the same object. Methods like `map`, `filter`, `slice`, and `concat` return new arrays, and methods like `find`, `some`, `every`, and `includes` return a value or boolean. The frontend risk is reference identity: mutating React state or props can prevent predictable rendering and can change data owned by another component. Modern methods such as `toSorted`, `toReversed`, `toSpliced`, and `with` make immutable array updates clearer.

## 10. Common Mistakes

- Calling `sort` directly on props before rendering.
- Using `push` then calling `setState` with the same array reference.
- Copying the array but mutating an object inside the copy.
- Forgetting that `fill({})` stores the same object in every slot.
- Using non-mutating methods but ignoring their returned value.
- Assuming immutable array methods deep-clone nested data.
- Overusing `reduce` when `map`, `filter`, or a loop would express intent better.

## 11. Practice

1. Write the mutating and immutable version of add, remove, replace, insert, sort, and reverse.
2. Explain why `[...arr].sort()` is safer than `arr.sort()` for React props.
3. Predict the output of the `Array(3).fill({ fields: [] })` example.
4. Build a shopping cart reducer without mutating the previous cart array.
5. Explain when local mutation is acceptable in production code.

## Related Notes

- [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]
- [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
- [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]
- [[01 - Roadmap|Roadmap]]
