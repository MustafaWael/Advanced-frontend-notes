---
tags: [javascript, objects, prototypes, object-copying-and-immutability]
module: "06 - Objects and Prototypes"
priority: must-know
status: not-started
---

# Object Copying and Immutability

## Maturity Target

- Priority: #must-know
- Study time: 100-120 minutes
- Interview signal: you can explain shallow copy, deep copy, structural sharing, `structuredClone`, `Object.freeze`, and React state immutability.
- Production signal: you can update nested UI state safely without unnecessary deep clones or hidden mutation.
- Dependencies: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]], [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]

## Source Anchors

- [React - Updating objects in state](https://react.dev/learn/updating-objects-in-state)
- [React - Updating arrays in state](https://react.dev/learn/updating-arrays-in-state)
- [MDN - structuredClone](https://developer.mozilla.org/en-US/docs/Web/API/Window/structuredClone)
- [MDN - Object.freeze](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/freeze)
- [MDN - Spread syntax](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax)

## 1. Concept

Object copying creates a new object reference. The important question is whether nested values are copied too.

Shallow copy:

```js
const original = {
  name: "Ava",
  address: { city: "Cairo" }
};

const copy = { ...original };

copy.name = "Mina";
copy.address.city = "Alexandria";

console.log(original.name); // "Ava"
console.log(original.address.city); // "Alexandria"
```

The top-level object is new, but `address` is shared.

Deep copy creates independent nested values when possible.

## 2. Why It Matters

Frontend bugs from mutation are everywhere:

- React state does not re-render because the same reference is reused.
- A shallow copy is made, but nested state is still mutated.
- API response data is mutated by a normalizer.
- A memoized selector returns stale results because input identity did not change.
- JSON deep copy breaks Dates, Maps, Sets, undefined values, and functions.
- Deep cloning everything creates performance problems.

The mature skill is not "always deep clone." It is copying at the boundary that changed.

## 3. Shallow Copy Tools

Objects:

```js
const nextUser = {
  ...user,
  name: "Ava"
};
```

Arrays:

```js
const nextItems = [...items, newItem];
const withoutDeleted = items.filter((item) => item.id !== deletedId);
const renamed = items.map((item) =>
  item.id === id ? { ...item, name: "Updated" } : item
);
```

Other shallow tools:

```js
Object.assign({}, source);
array.slice();
Array.from(arrayLike);
```

## 4. Deep Copy Tools

`structuredClone` handles many built-in data types better than JSON round trips.

```js
const original = {
  createdAt: new Date("2026-01-01"),
  tags: new Set(["frontend"])
};

const copy = structuredClone(original);

console.log(copy.createdAt instanceof Date); // true
console.log(copy.tags instanceof Set);       // true
```

JSON round trip is lossy:

```js
const original = {
  createdAt: new Date("2026-01-01"),
  missing: undefined,
  greet() {
    return "hi";
  }
};

const copy = JSON.parse(JSON.stringify(original));

console.log(typeof copy.createdAt); // "string"
console.log("missing" in copy);     // false
console.log(copy.greet);            // undefined
```

Use JSON only when you intentionally want JSON-compatible data.

## 5. React State Immutability

Bug:

```jsx
function Profile() {
  const [person, setPerson] = useState({
    name: "Ava",
    artwork: { city: "Cairo" }
  });

  function moveCity(city) {
    person.artwork.city = city;
    setPerson(person); // Same reference.
  }
}
```

Fix:

```jsx
function moveCity(city) {
  setPerson((currentPerson) => ({
    ...currentPerson,
    artwork: {
      ...currentPerson.artwork,
      city
    }
  }));
}
```

Why it works:

- The top-level `person` object is new.
- The nested `artwork` object is new.
- Unchanged fields are shared.
- React can see the top-level reference changed.

## 6. Structural Sharing

You do not need to deep clone an entire object tree to update one nested field. Copy only the path that changed.

```js
const nextState = {
  ...state,
  user: {
    ...state.user,
    preferences: {
      ...state.user.preferences,
      theme: "dark"
    }
  }
};
```

Unchanged branches keep their references:

```js
console.log(nextState.products === state.products); // true
console.log(nextState.user === state.user); // false
```

This is efficient and supports memoization.

## 7. `Object.freeze`

```js
"use strict";

const config = Object.freeze({
  apiBaseUrl: "/api",
  flags: { beta: true }
});

try {
  config.apiBaseUrl = "/v2";
} catch (error) {
  console.log(error.name); // "TypeError"
}

config.flags.beta = false;
console.log(config.flags.beta); // false
```

`Object.freeze` is shallow. Use it for development safety or API contracts, not as a full immutability solution for deep graphs unless you implement deep freeze.

## 8. Immer and Mutable Syntax

Immer-style libraries let you write mutation-like code while producing immutable results.

```js
// Conceptual example:
const nextState = produce(state, (draft) => {
  draft.user.preferences.theme = "dark";
});
```

Tradeoff:

- Great for deeply nested updates.
- Adds dependency and runtime abstraction.
- You still need to understand references and ownership.

## 9. Real Frontend Scenario: Sorting State

Bug:

```jsx
function ProductTable({ initialProducts }) {
  const [products, setProducts] = useState(initialProducts);

  function sortByPrice() {
    products.sort((a, b) => a.price - b.price);
    setProducts(products);
  }
}
```

Fix:

```jsx
function sortByPrice() {
  setProducts((currentProducts) =>
    [...currentProducts].sort((a, b) => a.price - b.price)
  );
}
```

> [!tip] Tradeoff
> copying has cost, but mutating state breaks React's reference model. For huge lists, sort on the server, virtualize rendering, or memoize derived sorted views carefully.

## 10. Choosing the Right Copy

| Situation | Tool |
| --- | --- |
| Add/update one top-level field | Object spread |
| Update nested state | Copy each changed level |
| Add/remove array item | Spread, `filter`, `map`, `slice` |
| Clone JSON-compatible data | JSON round trip only if loss is acceptable |
| Clone Dates, Maps, Sets, typed arrays | `structuredClone` if supported and types are cloneable |
| Prevent top-level mutation | `Object.freeze` |
| Complex nested immutable updates | Immer or reducer patterns |
| Object keys are dynamic objects | `Map`, not object copy tricks |

## Real-World Use Cases

### Store selector that builds a fresh object every call

A Zustand/Redux selector returns a derived object. Every store notification produces a brand-new reference, the equality check sees "changed", and the component re-renders on every unrelated store update — or worse, `useSyncExternalStore` throws an infinite-loop error.

```ts
// Re-renders on ANY store change:
const cartSummary = useStore((state) => ({
  count: state.items.length,
  total: state.items.reduce((sum, i) => sum + i.price, 0)
}));

// Stable: select primitives, or use a shallow-equality selector
const count = useStore((state) => state.items.length);
```

This is structural sharing's contract from the consumer side: memoization only works if **unchanged data keeps its reference**, and a fresh object literal per call breaks that promise. See [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]] and [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]].

### Optimistic update with snapshot and rollback

An optimistic UI writes the expected result into the cache before the server confirms, keeping a snapshot to restore on failure. The snapshot must not share the references you are about to change.

```ts
onMutate: async (newTodo) => {
  const previousTodos = queryClient.getQueryData(["todos"]);

  // New array + new object: the snapshot's references stay untouched
  queryClient.setQueryData(["todos"], (old) => [...old, { ...newTodo, pending: true }]);

  return { previousTodos };
},
onError: (_err, _newTodo, context) => {
  queryClient.setQueryData(["todos"], context.previousTodos); // rollback
}
```

Works only because the update is non-mutating: `previousTodos` still points at the untouched old array. If you had `old.push(newTodo)` instead, the "snapshot" and the corrupted cache would be the same object, and rollback would restore the wrong state. See [[17 - Practical Frontend Scenarios/05 - Avoiding Mutation in State|Avoiding Mutation in State]].

### Web Worker messages are structured clones, not shared references

Offloading a heavy report computation to a worker, a developer mutates the sent object afterwards and expects the worker to see it.

```js
const reportInput = { rows, filters, generatedAt: new Date() };

worker.postMessage(reportInput); // structured clone crosses the boundary
reportInput.filters.region = "EU"; // worker never sees this

worker.postMessage({ onProgress: () => {} }); // DataCloneError: functions aren't cloneable
```

`postMessage` runs the same structured clone algorithm as `structuredClone` (section 4): the worker gets an independent deep copy — `Date`, `Map`, `Set` survive, functions and DOM nodes throw. Each realm owns its copy; there is no shared mutable state to corrupt.

> [!tip]
> For large binary payloads, pass `ArrayBuffer`s in the transfer list to move instead of copy — cloning megabytes on every message is a real jank source. See [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]].

## 11. Interview Answer

Short answer:

> A shallow copy creates a new top-level object but shares nested references. A deep copy recursively copies nested values. React state should be treated as immutable, so updates should create new references for changed data.

Deeper answer:

> Object spread and `Object.assign` are shallow. `structuredClone` can deep clone many structured-clone-compatible values, while JSON serialization is lossy. `Object.freeze` is shallow and prevents changing own properties of the frozen object but not nested objects. Production code often uses structural sharing: copy only the path that changed.

Production answer:

> I avoid deep cloning everything because it can be slow and breaks referential sharing. For React, I create new references for changed paths, keep unchanged branches shared, and use Immer or reducers when nested updates become too noisy.

## 12. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Spread deep copies objects." | Spread is shallow. |
| "`Object.freeze` is deep." | It freezes only the object itself. |
| "JSON clone is safe for all data." | It loses Dates, Maps, Sets, undefined, functions, and prototypes. |
| "React state objects are actually immutable." | They are mutable JavaScript objects, but you must treat them as read-only. |
| "Deep clone on every update is safest." | It can be expensive and destroys useful reference sharing. |

## 13. Practice

1. Predict the output:

```js
const original = { nested: { count: 0 } };
const copy = { ...original };

copy.nested.count = 1;

console.log(original.nested.count);
console.log(original === copy);
console.log(original.nested === copy.nested);
```

Expected output:

```txt
1
false
true
```

2. Fix a nested React object update without mutation.
3. Replace a mutating `sort` state update with an immutable update.
4. Show one value JSON cloning corrupts but `structuredClone` preserves.
5. Explain structural sharing in one paragraph.

## Related Notes

- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]
- [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]]
- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[17 - Practical Frontend Scenarios/05 - Avoiding Mutation in State|Avoiding Mutation in State]]
- [[01 - Roadmap|Roadmap]]
