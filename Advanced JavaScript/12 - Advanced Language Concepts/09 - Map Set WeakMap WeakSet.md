---
tags: [javascript, language-concepts, map-set-weakmap-weakset]
module: "12 - Advanced Language Concepts"
priority: important
status: not-started
---

# Map Set WeakMap WeakSet

## Maturity Target

- Priority: #important
- Study time: 110-150 minutes
- Interview signal: you can choose Object vs Map, Array vs Set, Map vs WeakMap, and explain SameValueZero and weak references.
- Production signal: collections are chosen for key type, uniqueness, iteration, mutation pattern, and memory behavior.
- Dependencies: [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]], [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]], [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]

## Source Anchors

- [MDN Map](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Map)
- [MDN Set](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Set)
- [MDN WeakMap](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakMap)
- [MDN WeakSet](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakSet)
- [MDN Keyed collections](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Keyed_collections)

## 1. Concept

`Map` is a key-value collection where keys can be objects, functions, primitives, or `NaN`.

`Set` is a collection of unique values.

`WeakMap` and `WeakSet` hold object keys/values weakly, meaning they do not keep those objects alive for garbage collection.

```js
const roles = new Map();
roles.set("ada@example.com", "admin");

const tags = new Set(["react", "react", "js"]);
console.log(tags.size); // 2
```

## 2. Why It Matters

Plain objects and arrays are not always the right collection:

- object keys in plain objects become strings;
- `Set` dedupes without manual lookup objects;
- `Map` has reliable `.size` and insertion-order iteration;
- `WeakMap` can attach metadata to DOM nodes without leaks;
- React state with `Map`/`Set` still needs immutable updates.

## 3. Accurate Mechanism

`Map` and `Set` use SameValueZero for key/value equality.

```js
const set = new Set([NaN, NaN, -0, +0]);
console.log(set.size); // 2
```

Reason:

- `NaN` equals `NaN` under SameValueZero;
- `-0` and `+0` are treated as the same.

`Map` preserves insertion order.

```js
const map = new Map();
map.set("b", 2);
map.set("a", 1);

console.log([...map.keys()]); // ["b", "a"]
```

## 4. Map vs Object

Use `Map` when:

- keys are not always strings;
- keys are objects or functions;
- you add and delete frequently;
- you need reliable `.size`;
- you want straightforward iteration of entries.

Use plain objects when:

- keys are known strings;
- the shape is fixed;
- you are modeling a record/config;
- JSON serialization matters.

```ts
const counts = new Map<string, number>();

for (const tag of tags) {
  counts.set(tag, (counts.get(tag) ?? 0) + 1);
}
```

## 5. Set for Uniqueness

```ts
const ids = ["a", "b", "a", "c"];
const uniqueIds = [...new Set(ids)];

console.log(uniqueIds); // ["a", "b", "c"]
```

Set operations:

```ts
function intersection<T>(a: Set<T>, b: Set<T>) {
  return new Set([...a].filter((value) => b.has(value)));
}

function difference<T>(a: Set<T>, b: Set<T>) {
  return new Set([...a].filter((value) => !b.has(value)));
}
```

## 6. Real Frontend Bug: Mutating Set State

Problem:

```tsx
const [selected, setSelected] = useState(new Set<string>());

function toggle(id: string) {
  if (selected.has(id)) selected.delete(id);
  else selected.add(id);

  setSelected(selected);
}
```

> [!warning] Mutating a Set/Map in state won't re-render
> `Set` and `Map` are reference types; mutating one and passing the same reference back means React sees no change and skips the render. Create a new collection: `setSelected(new Set(selected))` after the add/delete.

Bug:

- the existing `Set` is mutated;
- React receives the same reference;
- React can bail out and skip rendering.

Fix:

```tsx
function toggle(id: string) {
  setSelected((current) => {
    const next = new Set(current);

    if (next.has(id)) next.delete(id);
    else next.add(id);

    return next;
  });
}
```

## 7. WeakMap for Object Metadata

```ts
const elementState = new WeakMap<Element, { open: boolean }>();

function initDropdown(element: Element) {
  elementState.set(element, { open: false });

  element.addEventListener("click", () => {
    const state = elementState.get(element);
    if (!state) return;
    state.open = !state.open;
  });
}
```

Why `WeakMap` helps:

- when the DOM element becomes unreachable elsewhere, the entry does not keep it alive;
- a normal `Map<Element, ...>` would keep a strong reference and can leak removed nodes.

Weak collections are not iterable and have no `.size` because garbage collection timing is non-deterministic.

## 8. WeakSet Use Cases

```ts
const processed = new WeakSet<object>();

function processOnce(value: object) {
  if (processed.has(value)) return;
  processed.add(value);
  expensiveProcess(value);
}
```

WeakSet is useful when membership is metadata about an object, not a list you need to inspect later.

## 9. Production Tradeoffs

| Collection | Best for | Avoid when |
| --- | --- | --- |
| Object | fixed string-key records | arbitrary object keys |
| Map | dynamic key-value data | JSON serialization without conversion |
| Set | uniqueness and membership | ordered duplicates matter |
| WeakMap | object metadata/cache without leaks | you need iteration or size |
| WeakSet | object "seen" tracking | primitive values or enumeration |

## 10. Interview Answer

**Short version:** `Map` stores key-value pairs with any key type and insertion-order iteration. `Set` stores unique values. `WeakMap` and `WeakSet` hold object references weakly, so they do not prevent garbage collection and cannot be iterated.

**Strong version:** `Map` and `Set` use SameValueZero equality, so `NaN` works and `-0` equals `+0`. `Map` is preferable to objects when keys are dynamic, non-string, or frequently added/deleted. `Set` is good for membership and deduplication. `WeakMap` is for associating metadata with objects, like DOM nodes or instance caches, without creating memory leaks. Weak collections cannot expose iteration because entries may disappear whenever the garbage collector runs. In React state, `Map` and `Set` must still be updated immutably with new collection instances.

## 11. Common Mistakes

- Using a plain object with object keys and getting `"[object Object]"`.
- Mutating a `Set` or `Map` stored in React state and reusing the same reference.
- Using `Map` when a serializable plain record would be simpler.
- Expecting `WeakMap` to be iterable.
- Using primitives as WeakMap keys in typical code.
- Assuming `Set` dedupes objects by deep equality.

```js
console.log(new Set([{ id: 1 }, { id: 1 }]).size); // 2
```

Objects are unique by reference.

## 12. Practice

1. Count word frequency using `Map`.
2. Deduplicate an array of primitive IDs with `Set`.
3. Explain why `new Set([NaN, NaN]).size` is `1`.
4. Fix a React `Set` state mutation bug.
5. Choose `Map` or `WeakMap` for caching metadata by DOM element, and explain why.

## Related Notes

- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
- [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]
- [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[01 - Roadmap|Roadmap]]
