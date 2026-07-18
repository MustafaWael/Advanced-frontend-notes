---
tags: [javascript, objects, prototypes, objects-internally]
module: "06 - Objects and Prototypes"
priority: must-know
status: not-started
---

# Objects Internally

## Maturity Target

- Priority: #must-know
- Study time: 75-90 minutes
- Interview signal: you can explain objects as property collections with internal slots, prototypes, descriptors, and reference identity.
- Production signal: you can reason about dynamic keys, own vs inherited properties, shape consistency, React state identity, and object injection risks.
- Dependencies: [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]], [[03 - Scope and Variables/01 - Scope Types|Scope Types]]

## Source Anchors

- [MDN - Working with objects](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Working_with_objects)
- [MDN - Object initializer](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Object_initializer)
- [MDN - Object.getPrototypeOf](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/getPrototypeOf)
- [MDN - Object.hasOwn](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/hasOwn)
- [ECMAScript 2026 - Ordinary object internal methods](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinary-object-internal-methods-and-internal-slots)

## 1. Concept

A JavaScript object is a collection of properties. Property keys are strings or symbols, and property values can be any JavaScript value.

```js
const user = {
  id: "u1",
  name: "Ava",
  roles: ["admin"]
};

console.log(user.name);      // "Ava"
console.log(user["roles"]);  // ["admin"]
```

Objects also have internal specification state you cannot access directly, such as the \[\[Prototype\]\] and \[\[Extensible\]\] slots.

## 2. Why It Matters

Frontend applications are mostly object traffic:

- API responses.
- Form state.
- React props and state.
- DOM event objects.
- Cache entries.
- Request options.
- Component view models.

If you misunderstand object identity, property lookup, or mutation, you get bugs that look like "React did not update", "my data changed somewhere else", "this property came from nowhere", or "a user input key overwrote something dangerous."

## 3. Official Mechanism

The spec describes objects with internal slots and internal methods.

Important pieces:

| Mechanism | Meaning |
| --- | --- |
| \[\[Prototype\]\] | The object or `null` used for inherited property lookup. |
| \[\[Extensible\]\] | Whether new own properties can be added. |
| \[\[Get\]\] | Internal method used for property reads. |
| \[\[Set\]\] | Internal method used for property writes. |
| \[\[GetOwnProperty\]\] | Reads an own property's descriptor. |
| \[\[DefineOwnProperty\]\] | Defines or changes an own property descriptor. |

You do not manipulate these slots directly. You use APIs like `Object.getPrototypeOf`, `Object.defineProperty`, `Object.preventExtensions`, `Object.seal`, and `Object.freeze`.

## 4. Own vs Inherited Properties

```js
const proto = {
  inherited: true
};

const obj = Object.create(proto);
obj.own = true;

console.log(obj.own);       // true
console.log(obj.inherited); // true

console.log(Object.hasOwn(obj, "own"));       // true
console.log(Object.hasOwn(obj, "inherited")); // false
```

Property lookup checks the object first, then follows the internal prototype link if needed. Own-property checks are essential when iterating user-controlled objects.

## 5. Property Keys

Most keys become strings unless they are symbols.

```js
const keyObject = { id: 1 };
const data = {};

data[keyObject] = "value";

console.log(Object.keys(data)); // ["[object Object]"]
```

Use `Map` when keys can be objects:

```js
const data = new Map();
const keyObject = { id: 1 };

data.set(keyObject, "value");

console.log(data.get(keyObject)); // "value"
```

> [!tip] Map for object keys
> Production rule: if you need arbitrary object keys, use `Map`. If you need JSON-like data with string keys, use plain objects.

## 6. Object Identity

Two identical object literals create different objects.

```js
console.log({ id: 1 } === { id: 1 }); // false

const user = { id: 1 };
const sameUser = user;

console.log(user === sameUser); // true
```

React and memoization often depend on reference identity. A new object literal inside render is a new reference every render.

```jsx
function ProductCard({ product }) {
  const style = { color: product.inStock ? "green" : "gray" };

  return <span style={style}>{product.name}</span>;
}
```

This is fine unless the object is passed to memoized children or used as an effect dependency. Then identity becomes observable.

## 7. Real Frontend Scenario: API Object Mutation

Bug:

```js
function normalizeUser(user) {
  user.displayName = `${user.firstName} ${user.lastName}`;
  return user;
}

const apiUser = { firstName: "Ava", lastName: "Stone" };
const normalized = normalizeUser(apiUser);

console.log(apiUser.displayName); // "Ava Stone"
```

> [!warning] Mutating caller-owned objects
> Failure mode: the normalizer mutates the caller-owned API object. Other code holding `apiUser` sees new state unexpectedly.

Fix:

```js
function normalizeUser(user) {
  return {
    ...user,
    displayName: `${user.firstName} ${user.lastName}`
  };
}
```

> [!tip] Copy to make ownership explicit
> Tradeoff: copying is slightly more work, but it makes ownership explicit and avoids accidental shared mutation.

## 8. Dynamic Key Risk

> [!warning] Unsanitized dynamic keys
> Avoid writing unsanitized external keys into objects that have prototypes.

```js
function assignField(target, field, value) {
  target[field] = value;
}
```

Safer pattern for dictionary-like data:

```js
const dictionary = Object.create(null);

function assignSafeField(field, value) {
  if (field === "__proto__" || field === "constructor" || field === "prototype") {
    throw new Error("Unsafe field name");
  }

  dictionary[field] = value;
}
```

For many cases, `Map` is cleaner and avoids prototype-key collisions.

## 9. Engine Performance Note

Engines optimize objects using implementation strategies often called shapes or hidden classes. You do not need to memorize engine internals, but a practical habit helps:

- Create objects with consistent property names.
- Avoid adding/deleting many properties on hot objects.
- Prefer arrays for ordered lists and maps for dynamic key-value collections.

Do not micro-optimize object shape before measuring. Use this knowledge to avoid extremely chaotic object structures in hot paths.

## Real-World Use Cases

### Classic interview trap: object keys stringify

Interviewers use this to test whether you know plain-object keys are strings or symbols — full stop.

```js
const cache = {};
const userA = { id: "u1" };
const userB = { id: "u2" };

cache[userA] = "profile A";
cache[userB] = "profile B";

console.log(cache[userA]); // ?
```

Wrong guess: `"profile A"`. Actual output: `"profile B"`.

Tick-by-tick:

1. `cache[userA]` triggers key conversion: `userA` is not a string or symbol, so it is coerced via `toString()` to `"[object Object]"`.
2. `[[DefineOwnProperty]]` creates the own property `"[object Object]"` with value `"profile A"`.
3. `cache[userB]` coerces to the **same** string key, so `[[Set]]` overwrites that one property.
4. The final read hits the single `"[object Object]"` entry: `"profile B"`.

The fix is `Map`, which compares keys by reference identity instead of stringifying (see section 5 above). See [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]] and [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]].

### Infinite refetch loop from an inline options object

A data hook takes an options object. The caller builds it inline, so every render produces a new reference, the dependency array sees a "change", and the effect refetches forever.

```tsx
function OrdersPage({ status }) {
  const options = { status, pageSize: 20 }; // new reference every render

  useEffect(() => {
    fetchOrders(options).then(setOrders); // setOrders → re-render → new options → refetch...
  }, [options]);
}
```

Fails because dependency comparison uses `Object.is`, and object identity is by reference — structurally equal literals are never equal. Fix: depend on the primitive fields (`[status]`) or memoize the object.

> [!warning]
> The same identity rule silently defeats `React.memo` and `useMemo` when you pass inline object props. See [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]] and [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]].

### Sealing a config object to catch typos in development

A feature-flag config is read all over the app. A misspelled write (`config.enalbeBeta = true`) would normally create a junk property and fail silently. `Object.seal` flips the `[[Extensible]]` internal slot so the write throws in strict mode.

```js
const featureFlags = Object.seal({
  enableBeta: false,
  enableNewCheckout: true
});

featureFlags.enableBeta = true;    // fine: existing property
featureFlags.enalbeBeta = true;    // TypeError in strict mode: object is not extensible
```

Works because `seal` sets `[[Extensible]]` to `false` and marks own properties non-configurable — the internal slots from section 3 doing practical work.

> [!tip]
> Seal shared config and constants modules at creation time; the typo fails at the write site instead of surfacing as "flag mysteriously off" three components away. See [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]].

## 10. Interview Answer

Short answer:

> A JavaScript object is a mutable collection of string or symbol keyed properties. It also has internal slots like \[\[Prototype\]\], which powers inherited property lookup.

Deeper answer:

> Property reads first check own properties, then walk the prototype chain. Properties are described by descriptors, and object identity is by reference, not structure. Arrays and functions are specialized objects. `typeof null` returning `"object"` is historical; `null` is not an object.

Production answer:

> In frontend work, I care about object ownership and identity. Mutating API objects or React state in place can create stale UI or action-at-a-distance bugs. Dynamic keys should be handled carefully with `Object.hasOwn`, null-prototype dictionaries, or `Map`.

## 11. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "`typeof value === 'object'` means value is a usable object." | `null` also returns `"object"`. |
| "Object keys can be any value." | Plain object keys are strings or symbols; object keys stringify. |
| "A property must be own if `obj.key` works." | It may come from the prototype chain. |
| "Two objects with same fields are equal." | Objects compare by reference. |
| "TypeScript interfaces exist at runtime." | They are erased; runtime validation is separate. |

## 12. Practice

1. Predict the output:

```js
const proto = { role: "guest" };
const user = Object.create(proto);
user.name = "Ava";

console.log(user.role);
console.log(Object.hasOwn(user, "role"));
console.log(Object.hasOwn(user, "name"));
```

Expected output:

```txt
guest
false
true
```

2. Rewrite a mutating normalizer into a pure object-returning normalizer.
3. Explain why `{ id: 1 } === { id: 1 }` is false.
4. Use `Map` instead of an object when the key is another object.
5. Explain why `Object.create(null)` can be useful for dictionaries.

## Related Notes

- [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]]
- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]
- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[01 - Roadmap|Roadmap]]
