---
tags: [javascript, language-concepts, primitive-vs-reference-values]
module: "12 - Advanced Language Concepts"
priority: must-know
status: not-started
---

# Primitive vs Reference Values

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can explain value copying, reference copying, object mutation, shallow copies, and React identity bugs without saying "objects are pass by reference."
- Production signal: you update state immutably, avoid shared nested mutations, and know when deep copying is required.
- Dependencies: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]], [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]], [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]

## Source Anchors

- [MDN JavaScript data types and data structures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Data_structures)
- [MDN Object](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object)
- [MDN structuredClone](https://developer.mozilla.org/en-US/docs/Web/API/Window/structuredClone)
- [React updating objects in state](https://react.dev/learn/updating-objects-in-state)

## 1. Concept

JavaScript has primitive values and object values.

Primitive language values:

- `undefined`
- `null`
- `boolean`
- `number`
- `bigint`
- `string`
- `symbol`

Everything else you commonly use as a data structure is an object: plain objects, arrays, functions, dates, regexes, maps, sets, class instances, promises, and errors.

Primitives are immutable values. Objects are mutable containers accessed through references.

```js
let a = "hello";
let b = a;
b = "world";

console.log(a); // "hello"
console.log(b); // "world"
```

```js
const userA = { name: "Ada" };
const userB = userA;

userB.name = "Grace";

console.log(userA.name); // "Grace"
```

## 2. Why It Matters

This concept sits under many production frontend bugs:

- React state mutates but the component does not re-render;
- a shallow copied object still shares nested data;
- `useEffect` runs every render because a dependency object is recreated;
- memoized components re-render because props have new references;
- form drafts accidentally mutate server data;
- cache entries are updated in place and subscribers miss the change.

Strong mid-level developers can name both the language rule and the UI consequence.

## 3. Accurate Mechanism

JavaScript passes arguments by value. For primitives, the value is the primitive itself. For objects, the value is a reference to the object.

That means a function can mutate the object through the reference it receives, but it cannot reassign the caller's variable.

```js
function mutate(obj) {
  obj.count += 1;
}

function replace(obj) {
  obj = { count: 999 };
}

const state = { count: 0 };

mutate(state);
console.log(state.count); // 1

replace(state);
console.log(state.count); // 1
```

Reason:

- `mutate` changes the object both references point to;
- `replace` changes only the local parameter binding.

> [!tip] Say identity, not stack vs heap
> Avoid overclaiming exact stack/heap storage. Engines optimize aggressively. The reliable language-level model is value identity for primitives and object identity for objects.

## 4. Mental Model

Variables do not contain object contents. They contain a way to reach an object.

> [!example] Tracing a shallow copy
> Copying an object variable copies the reference. Copying with spread creates a new top-level object, but nested objects remain shared unless you copy them too.

```js
const original = {
  user: {
    name: "Ada",
    settings: { theme: "light" }
  }
};

const shallow = { ...original };
shallow.user.settings.theme = "dark";

console.log(original.user.settings.theme); // "dark"
```

> [!warning] Nested objects stay shared
> The top-level object is new. `user` and `settings` are still the same nested objects.

## 5. Real Frontend Bug: Mutating React State

Problem:

```tsx
function Cart() {
  const [items, setItems] = useState([{ id: "a", quantity: 1 }]);

  function addOne(id: string) {
    const item = items.find((item) => item.id === id);
    if (item) item.quantity += 1;

    // Bug: same array reference.
    setItems(items);
  }

  return <button onClick={() => addOne("a")}>Add</button>;
}
```

Bug:

- `item.quantity += 1` mutates an object inside the existing state array;
- `setItems(items)` passes the same array reference;
- React compares the previous and next state with `Object.is`;
- the UI may not re-render.

Fix:

```tsx
function addOne(id: string) {
  setItems((current) =>
    current.map((item) =>
      item.id === id
        ? { ...item, quantity: item.quantity + 1 }
        : item
    )
  );
}
```

Why it works:

- `map` returns a new array;
- the changed item gets a new object;
- unchanged items keep their references;
- React sees a new top-level state reference.

## 6. Shallow Copy vs Deep Copy

Use shallow copies when updating one known path.

```ts
const next = {
  ...user,
  address: {
    ...user.address,
    city: "Cairo"
  }
};
```

Use `structuredClone` when you truly need a deep clone of cloneable data.

```ts
const draft = structuredClone(serverPayload);
draft.preferences.theme = "dark";
```

Tradeoffs:

- `structuredClone` handles many built-in types better than JSON round-tripping;
- it does not clone functions or DOM nodes;
- deep cloning large data can be expensive;
- in React state updates, targeted structural sharing is usually better than cloning everything.

Avoid this as a general clone strategy:

```js
JSON.parse(JSON.stringify(value));
```

> [!warning] JSON round-trip loses data
> It drops `undefined`, functions, symbols, `BigInt`, prototypes, and turns dates into strings.

## 7. Primitives Are Immutable, Variables Are Not

```js
let name = "ada";
name = name.toUpperCase();

console.log(name); // "ADA"
```

The original string was not mutated. `toUpperCase()` returned a new string, and the variable was reassigned.

Primitive wrappers can confuse people:

```js
const text = "hello";
console.log(text.toUpperCase()); // "HELLO"
```

The language temporarily boxes primitives so methods can be called. Do not use wrapper object types like `String`, `Number`, or `Boolean` for normal values in TypeScript. Prefer `string`, `number`, and `boolean`.

## 8. Production Tradeoffs

| Decision | Good when | Risk |
| --- | --- | --- |
| Mutate local temporary object | object is not shared and will not be reused | accidentally mutating shared state |
| Shallow copy | updating one known level | nested references remain shared |
| Deep clone | independent editable draft is needed | expensive and may lose unsupported values |
| Structural sharing | React state, reducers, caches | more code for nested updates |
| Object.freeze in development | catching accidental mutation | runtime cost and shallow by default |

## Real-World Use Cases

### In-place `.sort()` corrupting parent state

A product table sorts rows when the user clicks a column header. `Array.prototype.sort` mutates in place, so sorting the prop array silently reorders the parent's state array too — every consumer of that state now sees the "sorted" order, and React may skip re-renders because the reference never changed.

```tsx
function ProductTable({ products }: { products: Product[] }) {
  // Bug: sort mutates the array the parent's state still points to.
  const sorted = products.sort((a, b) => a.price - b.price);

  // Fix: copy first — the copy is a new reference, the original stays intact.
  const sortedSafe = [...products].sort((a, b) => a.price - b.price);
  return <Rows items={sortedSafe} />;
}
```

Works/fails because the prop is a **reference to the same array object** the parent owns — mutating through any reference mutates the one shared object. Same trap with `reverse` and `splice`; prefer `toSorted`/`toReversed` where available.

### Shared module-level default config

A fetch wrapper exports `DEFAULT_OPTIONS`. One call site "customizes" it by assigning onto it, and from then on every request in the app carries that header.

```ts
export const DEFAULT_OPTIONS = { retries: 2, headers: {} as Record<string, string> };

function createRequest(options = DEFAULT_OPTIONS) {
  options.headers["X-Trace"] = traceId(); // mutates the shared module object
  return options;
}
```

Every caller that defaulted to `DEFAULT_OPTIONS` received the **same object reference** — module scope makes it app-global. Build a fresh object per call instead: `{ ...DEFAULT_OPTIONS, headers: { ...DEFAULT_OPTIONS.headers } }`, or freeze the default in development to catch writers.

> [!warning]
> `Object.freeze(DEFAULT_OPTIONS)` is shallow — the nested `headers` object is still mutable unless frozen too.

### Optimistic update rollback snapshot

An optimistic UI stores "the previous items" before mutating, to roll back if the server rejects. Storing the reference is not a snapshot — after the optimistic change, the "backup" points at the already-changed data.

```ts
const previous = items;              // reference, not a snapshot
items.push(optimisticItem);          // "backup" now includes the new item
// rollback: setItems(previous)      // restores nothing

const snapshot = items.map((item) => ({ ...item })); // real copy to roll back to
```

Rollback only works if the snapshot is an **independent object graph**, which a reference assignment never gives you. This is exactly what React Query's `onMutate` context pattern relies on. See [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]] and [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]].

## 9. Interview Answer

**Short version:** Primitives are immutable values. Objects are mutable values accessed through references. JavaScript passes everything by value; for objects, the value being copied is the reference. That is why mutating an object through one variable is visible through another variable pointing at the same object.

**Strong version:** Assigning a primitive copies an independent value. Assigning an object variable copies the reference to the same object. A function parameter receives a copy of the value, so mutating a passed object is visible, but reassigning the parameter is not. In React this matters because state comparisons are based on identity. If I mutate an array and pass the same array back, React can bail out. The production fix is immutable updates: create new references along the path that changed while preserving references for unchanged data.

## 10. Common Mistakes

- Saying JavaScript objects are "passed by reference" without clarifying that the reference value is passed by value.
- Mutating React state and calling the setter with the same object or array.
- Using `{ ...obj }` and assuming it deep clones nested values.
- Using JSON stringify/parse as a clone for dates, functions, `undefined`, symbols, or BigInt.
- Creating new object literals in dependency arrays and expecting them to compare by structure.
- Using `String`, `Number`, or `Boolean` wrapper types instead of primitives.

## 11. Practice

1. What does this log?

```js
function update(obj) {
  obj.name = "Grace";
  obj = { name: "Linus" };
}

const user = { name: "Ada" };
update(user);
console.log(user.name);
```

Expected output: `"Grace"`.

2. Fix a nested React state update without mutating the original state.
3. Explain why `{ ...state }` is not enough when `state.user.profile.name` changes.
4. Explain why `useEffect(() => {}, [{ page: 1 }])` runs every render.
5. Name one case where `structuredClone` is useful and one case where it is too expensive.

## Related Notes

- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[17 - Practical Frontend Scenarios/05 - Avoiding Mutation in State|Avoiding Mutation in State]]
- [[01 - Roadmap|Roadmap]]
