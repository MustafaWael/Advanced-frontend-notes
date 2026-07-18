---
tags: [javascript, language-concepts, symbols]
module: "12 - Advanced Language Concepts"
priority: important
status: not-started
---

# Symbols

## Maturity Target

- Priority: #important
- Study time: 80-110 minutes
- Interview signal: you can explain unique symbol identity, the global registry, symbol property keys, and well-known symbols.
- Production signal: you recognize iterator, coercion, branding, metadata, and collision-avoidance patterns without treating symbols as privacy.
- Dependencies: [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]], [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]

## Source Anchors

- [MDN Symbol](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol)
- [MDN Symbol.for](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/for)
- [MDN Symbol.iterator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/iterator)
- [MDN Symbol.toPrimitive](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/toPrimitive)

## 1. Concept

A symbol is a unique primitive value that can be used as a property key.

```js
const a = Symbol("id");
const b = Symbol("id");

console.log(a === b); // false
```

The description helps debugging. It is not the identity.

## 2. Why It Matters

Symbols solve two important problems:

- avoiding accidental property-name collisions;
- giving objects hooks into built-in language behavior.

Examples:

- `[Symbol.iterator]` makes an object usable with `for...of`;
- `[Symbol.toPrimitive]` customizes conversion;
- `[Symbol.toStringTag]` customizes `Object.prototype.toString`;
- `Symbol.for("app.feature")` creates a shared registry key.

## 3. Accurate Mechanism

`Symbol()` is a factory function, not a constructor.

```js
Symbol("x");     // ok
// new Symbol("x"); // TypeError
```

Symbols can be own property keys.

```js
const META = Symbol("meta");

const user = {
  name: "Ada",
  [META]: { loadedAt: Date.now() }
};

console.log(Object.keys(user));              // ["name"]
console.log(Object.getOwnPropertySymbols(user)); // [Symbol(meta)]
console.log(Reflect.ownKeys(user));          // ["name", Symbol(meta)]
```

Symbol keys are skipped by `Object.keys`, `for...in`, and JSON serialization. They are not private; `Object.getOwnPropertySymbols` and `Reflect.ownKeys` can reveal them.

## 4. Global Symbol Registry

`Symbol.for(key)` returns the same symbol for the same string key from the global symbol registry.

```js
const one = Symbol.for("app.theme");
const two = Symbol.for("app.theme");

console.log(one === two); // true
console.log(Symbol.keyFor(one)); // "app.theme"
console.log(Symbol.keyFor(Symbol("app.theme"))); // undefined
```

Use `Symbol()` for local uniqueness. Use `Symbol.for()` only when different modules or realms intentionally need the same symbol.

## 5. Mental Model

Think of symbols as unguessable keys, not hidden fields.

They are excellent for:

- library metadata;
- avoiding collisions on objects you do not fully own;
- spec hooks such as iteration and coercion;
- branding internal values.

They are not a security boundary.

## 6. Real Frontend Example: Metadata Without Collision

```ts
const QUERY_META = Symbol("query.meta");

type QueryResult<T> = {
  data: T;
  status: "success" | "error";
  [QUERY_META]?: {
    fetchedAt: number;
    cacheKey: string;
  };
};

function attachMeta<T>(
  result: QueryResult<T>,
  cacheKey: string
): QueryResult<T> {
  return {
    ...result,
    [QUERY_META]: {
      fetchedAt: Date.now(),
      cacheKey
    }
  };
}
```

Why this works:

- user-facing property names cannot collide with `QUERY_META`;
- normal JSON output omits the metadata;
- library code that has the symbol can still read it.

> [!tip] Tradeoff
> debugging and serialization need explicit symbol-aware tools.

## 7. Well-Known Symbols

| Symbol | Customizes |
| --- | --- |
| `Symbol.iterator` | sync iteration for `for...of`, spread, destructuring |
| `Symbol.asyncIterator` | async iteration for `for await...of` |
| `Symbol.toPrimitive` | object-to-primitive conversion |
| `Symbol.hasInstance` | `instanceof` behavior |
| `Symbol.toStringTag` | `Object.prototype.toString` label |
| `Symbol.match` | string matching behavior |

Example:

```js
const range = {
  start: 1,
  end: 3,
  [Symbol.iterator]() {
    let current = this.start;
    const end = this.end;

    return {
      next() {
        return current <= end
          ? { value: current++, done: false }
          : { value: undefined, done: true };
      }
    };
  }
};

console.log([...range]); // [1, 2, 3]
```

## 8. Production Tradeoffs

| Pattern | Benefit | Risk |
| --- | --- | --- |
| Local `Symbol()` | collision-free internal key | hard to share across modules |
| `Symbol.for()` | shared known key | global registry naming conflicts if not namespaced |
| Symbol metadata | avoids normal enumeration | not serialized and not private |
| Well-known symbols | integrates with language features | can surprise readers if overused |
| Private class fields | real encapsulation | only for class internals, not object metadata |

## 9. Interview Answer

**Short version:** A symbol is a unique primitive often used as an object property key. `Symbol("id") !== Symbol("id")`; the description is only for debugging. Well-known symbols customize built-in behavior such as iteration and coercion.

**Strong version:** Symbols solve property collision and extension-point problems. Symbol keys are own property keys but are skipped by common enumeration and JSON serialization. They are discoverable, so they are not private. `Symbol.for` uses a global registry and returns the same symbol for the same key, while `Symbol()` always creates a new symbol. Built-in operations use well-known symbols like `Symbol.iterator`, `Symbol.toPrimitive`, and `Symbol.toStringTag` to let objects participate in language protocols.

## 10. Common Mistakes

- Thinking symbol descriptions determine identity.
- Using symbols for true privacy.
- Forgetting symbol keys are skipped by JSON.
- Using `Symbol.for` without a namespaced key.
- Trying to call `new Symbol()`.
- Forgetting `Object.keys` does not show symbol keys.

## 11. Practice

1. Predict:

```js
const a = Symbol("x");
const b = Symbol("x");
const c = Symbol.for("x");
const d = Symbol.for("x");

console.log(a === b);
console.log(c === d);
console.log(Symbol.keyFor(a));
console.log(Symbol.keyFor(c));
```

2. Add `[Symbol.iterator]` to a `Range` object.
3. Explain why symbol keys are useful for library metadata.
4. Explain why symbol keys are not private.
5. Implement `[Symbol.toPrimitive]` on a `Money` object.

## Related Notes

- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
- [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[01 - Roadmap|Roadmap]]
