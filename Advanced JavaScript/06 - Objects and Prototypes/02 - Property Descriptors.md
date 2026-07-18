---
tags: [javascript, objects, prototypes, property-descriptors]
module: "06 - Objects and Prototypes"
priority: important
status: not-started
---

# Property Descriptors

## Maturity Target

- Priority: #important
- Study time: 75-90 minutes
- Interview signal: you can explain value descriptors, accessor descriptors, enumerability, writability, configurability, and why assignment is not the same as definition.
- Production signal: you can debug hidden/non-enumerable properties, read-only properties, getters with side effects, and shallow freezing.
- Dependencies: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]

## Source Anchors

- [MDN - Object.getOwnPropertyDescriptor](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/getOwnPropertyDescriptor)
- [MDN - Object.defineProperty](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/defineProperty)
- [MDN - Object.freeze](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/freeze)
- [ECMAScript 2026 - Property descriptors](https://tc39.es/ecma262/2026/multipage/ecmascript-data-types-and-values.html#sec-property-descriptor-specification-type)

## 1. Concept

A property descriptor describes the attributes of an own property.

Data descriptor:

```js
const user = { name: "Ava" };

console.log(Object.getOwnPropertyDescriptor(user, "name"));
// { value: "Ava", writable: true, enumerable: true, configurable: true }
```

Accessor descriptor:

```js
const user = {
  firstName: "Ava",
  lastName: "Stone",
  get fullName() {
    return `${this.firstName} ${this.lastName}`;
  }
};

console.log(Object.getOwnPropertyDescriptor(user, "fullName").get instanceof Function);
// true
```

## 2. Why It Matters

Descriptors explain several "why is this weird?" bugs:

- `Object.keys` skips a property.
- Assignment silently fails or throws in strict mode.
- A getter runs during rendering or logging.
- A property cannot be deleted.
- `Object.freeze` does not freeze nested objects.
- A library defines metadata that exists but is not enumerable.

## 3. Descriptor Attributes

Data descriptor attributes:

| Attribute | Meaning |
| --- | --- |
| `value` | The stored value. |
| `writable` | Whether assignment can change `value`. |
| `enumerable` | Whether it appears in `Object.keys`, spread, `for...in` own part, etc. |
| `configurable` | Whether descriptor shape can be changed or property can be deleted. |

Accessor descriptor attributes:

| Attribute | Meaning |
| --- | --- |
| `get` | Function called when property is read. |
| `set` | Function called when property is assigned. |
| `enumerable` | Whether the property appears in enumerations. |
| `configurable` | Whether descriptor shape can be changed or property can be deleted. |

A descriptor cannot be both a data descriptor and accessor descriptor at the same time.

## 4. Assignment vs defineProperty

Normal assignment creates writable, enumerable, configurable properties.

```js
const user = {};
user.name = "Ava";

console.log(Object.getOwnPropertyDescriptor(user, "name"));
// writable: true, enumerable: true, configurable: true
```

> [!warning] defineProperty defaults to false
> `Object.defineProperty` defaults missing boolean attributes to `false`.

```js
const user = {};

Object.defineProperty(user, "id", {
  value: "u1"
});

console.log(Object.keys(user)); // []
console.log(user.id);           // "u1"
console.log(Object.getOwnPropertyDescriptor(user, "id"));
// writable: false, enumerable: false, configurable: false
```

This default is a common interview trap.

## 5. Non-Writable Properties

```js
"use strict";

const config = {};

Object.defineProperty(config, "apiBaseUrl", {
  value: "/api",
  writable: false,
  enumerable: true,
  configurable: false
});

try {
  config.apiBaseUrl = "/v2";
} catch (error) {
  console.log(error.name); // "TypeError"
}

console.log(config.apiBaseUrl); // "/api"
```

In sloppy mode, assignment to a non-writable property may fail silently. Strict mode is better because it fails visibly.

## 6. Non-Enumerable Properties

```js
const user = { name: "Ava" };

Object.defineProperty(user, "internalId", {
  value: "secret-1",
  enumerable: false
});

console.log(user.internalId); // "secret-1"
console.log(Object.keys(user)); // ["name"]
console.log({ ...user }); // { name: "Ava" }
```

Production use: internal metadata that should not be serialized or spread accidentally. But do not rely on non-enumerability for security; the property is still readable.

## 7. Getters and Setters

```js
const cart = {
  items: [
    { price: 10, quantity: 2 },
    { price: 5, quantity: 1 }
  ],
  get total() {
    return this.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }
};

console.log(cart.total); // 25
```

> [!tip] Keep getters cheap and pure
> Getters should be cheap and side-effect-free when used in UI code. A getter that fetches data, mutates state, or logs excessively can make property reads surprising.

Bug:

```js
const user = {
  get profile() {
    throw new Error("Network not loaded");
  }
};

// Even a harmless-looking spread can read properties.
try {
  console.log({ ...user });
} catch (error) {
  console.log(error.message); // "Network not loaded"
}
```

## 8. Freezing, Sealing, and Preventing Extensions

```js
const settings = {
  theme: "dark",
  nested: { compact: true }
};

Object.freeze(settings);

console.log(Object.isFrozen(settings)); // true

settings.nested.compact = false;
console.log(settings.nested.compact); // false
```

> [!warning] Object.freeze is shallow
> `Object.freeze` is shallow. It prevents adding/removing/reconfiguring own properties and makes data properties non-writable on the frozen object, but nested objects remain mutable unless frozen too.

## 9. Real Frontend Scenario: Metadata on View Models

```js
function attachDebugId(viewModel, debugId) {
  Object.defineProperty(viewModel, "debugId", {
    value: debugId,
    enumerable: false,
    configurable: true
  });

  return viewModel;
}

const product = attachDebugId({ name: "Keyboard" }, "row-1");

console.log(Object.keys(product)); // ["name"]
console.log(product.debugId);      // "row-1"
```

> [!tip] Document hidden metadata
> Tradeoff: non-enumerable metadata avoids polluting JSON and UI spreads, but it can surprise teammates. Document it and avoid hiding business data this way.

## 10. Interview Answer

Short answer:

> A property descriptor is the metadata for an own property: value or getter/setter, plus writable, enumerable, and configurable flags.

Deeper answer:

> Assignment creates ordinary writable/enumerable/configurable data properties. `Object.defineProperty` lets you control those attributes, and missing flags default to false. Accessor properties use get/set functions instead of a value. `Object.freeze` changes descriptors but only shallowly.

Production answer:

> I use descriptors when I need hidden metadata, read-only configuration, or accessors. I avoid getters with expensive work in render paths and remember that non-enumerable is not private or secure.

## 11. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "If `obj.x` works, `Object.keys` will show it." | Non-enumerable and inherited properties are skipped. |
| "`defineProperty` defaults match assignment." | Missing descriptor booleans default to false. |
| "`writable: false` freezes nested objects." | It only prevents rebinding that property value. |
| "Getters are just fields." | Getters execute code on read. |
| "Non-enumerable means private." | It is still accessible if you know the key. |

## 12. Practice

1. Predict the output:

```js
const obj = {};

Object.defineProperty(obj, "id", {
  value: 1
});

console.log(obj.id);
console.log(Object.keys(obj));
console.log(Object.getOwnPropertyDescriptor(obj, "id").writable);
```

Expected output:

```txt
1
[]
false
```

2. Define a non-enumerable `debugId` property.
3. Create a getter for `fullName` and inspect its descriptor.
4. Freeze an object with a nested object and show why the nested value can still change.
5. Explain why a getter with network work is a bad UI pattern.

## Related Notes

- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]
- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]
- [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[01 - Roadmap|Roadmap]]
