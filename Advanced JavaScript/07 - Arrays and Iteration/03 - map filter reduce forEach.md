---
tags: [javascript, arrays, map-filter-reduce-foreach]
module: "07 - Arrays and Iteration"
priority: must-know
status: not-started
---

# map filter reduce forEach

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you choose the method that matches the result shape and explain callback order/output.
- Production signal: you write readable data transformations without accidental mutation, hidden async bugs, or expensive render work.
- Dependencies: [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]], [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]], [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]

## Source Anchors

- [MDN Array.prototype.map](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/map)
- [MDN Array.prototype.filter](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/filter)
- [MDN Array.prototype.reduce](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/reduce)
- [MDN Array.prototype.forEach](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/forEach)
- [React: Rendering Lists](https://react.dev/learn/rendering-lists)

## 1. Concept

These are higher-order array methods. They receive a callback and run it over array elements, but each one answers a different question:

| Method | Question | Return value |
| --- | --- | --- |
| `map` | What should each item become? | new array |
| `filter` | Which items should remain? | new array |
| `reduce` | What single accumulated value should this array become? | any value |
| `forEach` | What side effect should run for each item? | `undefined` |

The callback shape is usually:

```js
array.map((value, index, array) => {
  return nextValue;
});
```

## 2. Why It Matters

These methods are everywhere in frontend work:

- `map` renders React lists and transforms API data into UI props.
- `filter` powers search, permission filtering, and hidden/visible state.
- `reduce` builds totals, grouped data, lookup maps, and derived summaries.
- `forEach` is useful for side effects such as logging, registering listeners, or calling imperative APIs.

Mid-level strength is choosing the clearest method, not forcing every problem into one favorite method.

## 3. Official Mechanism

Array iterative methods generally use the array length and numeric indices. Important details:

- `map`, `filter`, `reduce`, and `forEach` call the callback in increasing index order.
- `map`, `filter`, and `forEach` skip empty slots in sparse arrays.
- `reduce` also skips holes, and without an `initialValue` it uses the first existing element as the initial accumulator.
- The callback can receive `(element, index, array)`.
- These methods do not mutate the original array by themselves, but your callback can still mutate objects or external state.
- `map` creates a new array; calling `map` and ignoring its return value is usually a code smell.

## 4. Mental Model

Choose based on the shape you need:

```txt
array -> array of same conceptual size       map
array -> smaller array                       filter
array -> number/string/object/map/summary    reduce
array -> side effects only                   forEach
```

If the result shape is hard to explain, the code probably needs a clearer method or a named helper function.

## 5. `map`: Transform Each Item

```js
const prices = [10, 20, 30];
const withTax = prices.map(price => price * 1.14);

console.log(withTax);
// [11.4, 22.8, 34.199999999999996]
console.log(prices);
// [10, 20, 30]
```

### Real Frontend Use

```jsx
function ProductGrid({ products }) {
  return (
    <ul>
      {products.map(product => (
        <li key={product.id}>
          {product.name} - ${product.price}
        </li>
      ))}
    </ul>
  );
}
```

### Common Bug: `parseInt` With `map`

```js
console.log(["10", "10", "10"].map(parseInt));
// [10, NaN, 2]
```

> [!warning] Index becomes the radix
> `map` passes `(value, index, array)`. `parseInt` accepts `(string, radix)`, so the index becomes the radix.

Fix:

```js
console.log(["10", "10", "10"].map(value => parseInt(value, 10)));
// [10, 10, 10]
```

## 6. `filter`: Keep Matching Items

```js
const users = [
  { id: 1, name: "Mina", active: true },
  { id: 2, name: "Sara", active: false },
  { id: 3, name: "Omar", active: true },
];

const activeUsers = users.filter(user => user.active);

console.log(activeUsers.map(user => user.name));
// ["Mina", "Omar"]
```

### Real Frontend Use

```js
function getVisibleProducts(products, query, selectedCategory) {
  const normalizedQuery = query.trim().toLowerCase();

  return products.filter(product => {
    const matchesQuery = product.name.toLowerCase().includes(normalizedQuery);
    const matchesCategory =
      selectedCategory === "all" || product.category === selectedCategory;

    return matchesQuery && matchesCategory;
  });
}
```

### Common Bug: Filtering But Mutating Items

```js
const visible = products.filter(product => {
  product.highlighted = product.name.includes(query);
  return product.highlighted;
});
```

> [!warning] Filtering while mutating items
> This filters and mutates at the same time. A safer split:

```js
const visible = products
  .map(product => ({
    ...product,
    highlighted: product.name.includes(query),
  }))
  .filter(product => product.highlighted);
```

## 7. `reduce`: Accumulate A Result

Use `reduce` when the output is not simply "one result per input item."

```js
const cart = [
  { name: "Keyboard", price: 100, quantity: 1 },
  { name: "Mouse", price: 40, quantity: 2 },
];

const total = cart.reduce((sum, item) => {
  return sum + item.price * item.quantity;
}, 0);

console.log(total);
// 180
```

### Build A Lookup Map

```js
const users = [
  { id: "u1", name: "Mina" },
  { id: "u2", name: "Sara" },
];

const userById = users.reduce((acc, user) => {
  acc[user.id] = user;
  return acc;
}, {});

console.log(userById.u2.name);
// "Sara"
```

### Common Bug: Missing Initial Value

```js
try {
  [].reduce((sum, value) => sum + value);
} catch (error) {
  console.log(error.name);
  // TypeError
}
```

Fix:

```js
const total = [].reduce((sum, value) => sum + value, 0);
console.log(total);
// 0
```

> [!tip] Always pass an initial value
> For production code, provide an `initialValue` unless you deliberately want the first existing element to become the accumulator.

## 8. `forEach`: Side Effects Only

```js
const events = ["open", "click", "close"];

const result = events.forEach(eventName => {
  console.log(`track:${eventName}`);
});

console.log(result);
// undefined
```

Use `forEach` when the point is the side effect. Do not use it to build an array when `map` or `filter` would say the intent better.

### Common Bug: `forEach` With `async`

```js
async function saveAll(items) {
  items.forEach(async item => {
    await saveItem(item);
  });

  console.log("done");
}
```

> [!warning] forEach never awaits callbacks
> `forEach` does not wait for async callbacks. `"done"` logs before the saves finish.

Sequential fix:

```js
async function saveAllSequential(items) {
  for (const item of items) {
    await saveItem(item);
  }
  console.log("done");
}
```

Parallel fix:

```js
async function saveAllParallel(items) {
  await Promise.all(items.map(item => saveItem(item)));
  console.log("done");
}
```

> [!tip] Sequential vs parallel async work
> Choose sequential when order/rate limiting matters. Choose parallel when independent requests can safely run together.

## 9. Sparse Array Behavior

```js
const sparse = [1, , 3];

console.log(sparse.map(value => value * 2));
// [2, empty, 6]

const visited = [];
sparse.forEach((value, index) => visited.push(index));
console.log(visited);
// [0, 2]
```

This is one reason API-normalized data should use explicit `null` or `undefined` values instead of accidental holes.

## 10. Production Decision Points

- Prefer `map` for transformations and React rendering.
- Prefer `filter` for keeping/removing items.
- Prefer `some`, `every`, `find`, or `includes` for existence questions instead of `filter(...).length`.
- Prefer `reduce` for totals, grouping, and lookup maps, but do not make it a puzzle.
- Prefer `for...of` over `forEach` when you need `await`, `break`, or `continue`.
- Avoid doing heavy map/filter/sort chains on every keystroke for huge lists. Measure first, then consider memoization, pagination, virtualization, server-side filtering, or a worker.

## Real-World Use Cases

### CSV export from a data table

An admin table has an "Export CSV" button. Each order becomes exactly one line — the definition of a `map` job — and `join` assembles the file.

```js
function toCsv(orders) {
  const header = ["id", "customer", "total"].join(",");
  const lines = orders.map(order =>
    [order.id, `"${order.customerName}"`, order.total.toFixed(2)].join(",")
  );
  return [header, ...lines].join("\n");
}

const blob = new Blob([toCsv(orders)], { type: "text/csv" });
```

Works because `map` guarantees one output element per input element in the same order — the row count and row order of the CSV mirror the table exactly.

### `reduce` as a pipeline runner

A checkout applies pricing rules in a fixed order: discounts, then tax, then rounding. Each step takes a cart and returns a new cart.

```js
const pricingSteps = [applyDiscounts, applyTax, roundTotals];

const finalCart = pricingSteps.reduce((cart, step) => step(cart), rawCart);
```

Works because `reduce` threads the accumulator through every element — here the accumulator is the cart itself and the "elements" are functions. Adding a rule is now a one-line array change instead of edited call-nesting.

> [!tip] Same trick for sequential async steps
> `steps.reduce((p, step) => p.then(step), Promise.resolve(input))` chains async transforms in order — see [[08 - Async JavaScript/02 - Promises|Promises]].

### Syncing React state to an imperative map API

A store locator renders MapLibre markers, which live outside React. `map` collects the created markers so `forEach` can clean them up.

```jsx
useEffect(() => {
  const markers = stores.map(store =>
    new maplibregl.Marker().setLngLat([store.lng, store.lat]).addTo(mapRef.current)
  );

  return () => markers.forEach(marker => marker.remove());
}, [stores]);
```

Works because the two methods split by result shape: creating markers must be `map` (the returned array is needed for cleanup), while removal is pure side effect, exactly what `forEach` is for. Using `forEach` for creation would throw the marker references away and leak DOM nodes on every `stores` change.

See [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]] and [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]].

## 11. Interview Answer

**Short version:** `map` transforms items into a new array, `filter` keeps selected items in a new array, `reduce` folds the array into one result, and `forEach` runs side effects and returns `undefined`.

**Strong version:** These are array iterative methods that call a callback with the current element, index, and array. They generally visit existing elements in index order and skip holes. `map` and `filter` allocate new arrays, `reduce` uses an accumulator and should usually receive an initial value, and `forEach` should not be used when you need a returned array or awaited async work. In frontend code, I choose the method based on result shape and make sure transformations do not mutate React state or props.

## 12. Common Mistakes

- Using `map` for side effects and ignoring the returned array.
- Using `forEach` with `async` and assuming it waits.
- Forgetting `reduce` can throw on an empty array without `initialValue`.
- Using `filter(...).length > 0` instead of `some`.
- Creating unreadable `reduce` pipelines when a named loop is clearer.
- Mutating objects inside a "non-mutating" array method.
- Forgetting that callbacks receive `(value, index, array)`.

## 13. Practice

1. Convert a `for` loop that builds a UI array into `map`.
2. Convert `filter(...).length > 0` into `some`.
3. Write a `reduce` that groups orders by status with an initial value.
4. Predict the output of `["10", "10", "10"].map(parseInt)`.
5. Rewrite an async `forEach` into `for...of` and `Promise.all` versions.

## Related Notes

- [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]
- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[07 - Arrays and Iteration/04 - find some every includes|find some every includes]]
- [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]
- [[01 - Roadmap|Roadmap]]
