---
tags: [javascript, objects, prototypes, prototype-and-prototype-chain]
module: "06 - Objects and Prototypes"
priority: must-know
status: not-started
---

# Prototype and Prototype Chain

## Maturity Target

- Priority: #must-know
- Study time: 90 minutes
- Interview signal: you can explain property lookup, method sharing, shadowing, `Object.create`, and `instanceof`.
- Production signal: you can debug inherited properties, prototype pollution risks, class method lookup, and surprising `for...in` results.
- Dependencies: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]], [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]

## Source Anchors

- [MDN - Inheritance and the prototype chain](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Inheritance_and_the_prototype_chain)
- [MDN - Object.getPrototypeOf](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/getPrototypeOf)
- [MDN - Object.create](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/create)
- [MDN - instanceof](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/instanceof)
- [ECMAScript 2026 - OrdinaryGet](https://tc39.es/ecma262/2026/multipage/ordinary-and-exotic-objects-behaviours.html#sec-ordinaryget)

## 1. Concept

Every ordinary object has an internal \[\[Prototype\]\] link to another object or `null`. When JavaScript cannot find a property on the object itself, it follows that link. This repeated lookup is the prototype chain.

```js
const sharedMethods = {
  greet() {
    return `Hi ${this.name}`;
  }
};

const user = Object.create(sharedMethods);
user.name = "Ava";

console.log(user.greet()); // "Hi Ava"
```

`greet` is not an own property of `user`; it is found on `sharedMethods`.

## 2. Why It Matters

Prototypes power:

- Methods on arrays, functions, dates, maps, sets, and classes.
- Constructor function instances.
- Class methods.
- Method sharing without copying functions onto every object.
- `instanceof` checks.

They also create risks:

- Inherited properties during iteration.
- Shadowing bugs.
- Prototype pollution.
- Confusion between own and inherited data.

## 3. Property Lookup

```js
const animal = {
  eats: true
};

const dog = Object.create(animal);
dog.barks = true;

console.log(dog.barks); // true, own property
console.log(dog.eats);  // true, inherited property
console.log(dog.missing); // undefined
```

Lookup order:

1. Check own properties on `dog`.
2. If missing, check `Object.getPrototypeOf(dog)`.
3. Continue until the property is found or the prototype becomes `null`.

## 4. Shadowing

An own property shadows an inherited property with the same key.

```js
const defaults = {
  theme: "light"
};

const userSettings = Object.create(defaults);

console.log(userSettings.theme); // "light"

userSettings.theme = "dark";

console.log(userSettings.theme); // "dark"
console.log(defaults.theme);     // "light"
```

> [!warning] Shadowing hides inherited values
> This is useful for defaults, but can confuse debugging when inherited values appear without being visible in `Object.keys`.

## 5. Methods and `this`

When an inherited method is called as `obj.method()`, `this` is still `obj`, not the prototype where the method was found.

```js
const methods = {
  describe() {
    return this.name;
  }
};

const user = Object.create(methods);
user.name = "Ava";

console.log(user.describe()); // "Ava"
```

That is why prototype methods work for instances.

## 6. Constructor Prototypes

```js
function User(name) {
  this.name = name;
}

User.prototype.greet = function greet() {
  return `Hi ${this.name}`;
};

const user = new User("Ava");

console.log(Object.getPrototypeOf(user) === User.prototype); // true
console.log(user.greet()); // "Hi Ava"
```

`new User()` sets the instance's internal prototype to `User.prototype`.

## 7. `instanceof`

`instanceof` checks whether a constructor's `.prototype` appears in an object's prototype chain.

```js
console.log(user instanceof User); // true
console.log(user instanceof Object); // true
```

Be careful:

- It can fail across realms, such as iframes.
- It can change if prototypes are reassigned.
- It checks prototype chain, not object shape.

> [!tip] Prefer shape checks for API data
> For API data, shape validation is usually better than `instanceof`.

## 8. Real Frontend Scenario: Inherited Keys in Iteration

Bug:

```js
const defaults = {
  role: "guest"
};

const formValues = Object.create(defaults);
formValues.email = "ava@example.com";

const payload = {};

for (const key in formValues) {
  payload[key] = formValues[key];
}

console.log(payload); // { email: "ava@example.com", role: "guest" }
```

Fix:

```js
const payload = {};

for (const key in formValues) {
  if (Object.hasOwn(formValues, key)) {
    payload[key] = formValues[key];
  }
}

console.log(payload); // { email: "ava@example.com" }
```

Or use `Object.keys(formValues)`, which returns own enumerable string keys.

## 9. Prototype Pollution Awareness

> [!warning] Prototype pollution risk
> Prototype pollution happens when user-controlled keys change object prototypes or inherited values.

Risky merge:

```js
function merge(target, source) {
  for (const key in source) {
    target[key] = source[key];
  }

  return target;
}
```

Safer habits:

- Reject keys like `__proto__`, `constructor`, and `prototype` in deep merge utilities.
- Use `Object.hasOwn` during iteration.
- Use `Map` or `Object.create(null)` for dictionaries.
- Prefer well-tested merge libraries for untrusted data.

## Real-World Use Cases

### Classic interview trap: shared mutable state on the prototype

The canonical prototype question: put a mutable value on the prototype and mutate it through one instance.

```js
function Playlist(name) {
  this.name = name;
}

Playlist.prototype.tracks = [];

const workout = new Playlist("Workout");
const focus = new Playlist("Focus");

workout.tracks.push("Eye of the Tiger");

console.log(focus.tracks); // ?
```

Wrong guess: `[]`. Actual output: `["Eye of the Tiger"]`.

Tick-by-tick:

1. `workout.tracks` is a **read**: no own property on `workout`, so `[[Get]]` walks the chain and finds the single array on `Playlist.prototype`.
2. `.push(...)` mutates that array in place — mutation is not an own-property write, so no shadowing happens (contrast with section 4: `userSettings.theme = "dark"` was an assignment, which does shadow).
3. `focus.tracks` walks the same chain to the same array.

Fix: initialize per-instance state in the constructor (`this.tracks = []`), keeping only functions on the prototype. See [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]] and [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]].

### `hasOwnProperty` crash on null-prototype objects

Query-string and header parsers often return dictionaries built with `Object.create(null)` precisely to avoid inherited keys. Code that calls `params.hasOwnProperty("redirect")` then throws — the method was never inherited because the chain is empty.

```js
const params = Object.create(null);
params.redirect = "/dashboard";

params.hasOwnProperty("redirect");        // TypeError: not a function
Object.hasOwn(params, "redirect");        // true — does not depend on the chain
```

Fails because `hasOwnProperty` itself lives on `Object.prototype`, and lookup hits `null` before finding it. `Object.hasOwn` is a static method, so it works on any object. See [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]].

### Third-party script patches `Array.prototype` and breaks iteration

An old analytics snippet adds a helper to `Array.prototype` as a plain (enumerable) property. Every `for...in` over any array in the app now yields a phantom key.

```js
// somewhere in a legacy vendor bundle:
Array.prototype.contains = function (value) { return this.includes(value); };

const selectedIds = ["a1", "b2"];

for (const key in selectedIds) {
  console.log(key); // "0", "1", "contains"
}
```

Fails because `for...in` walks enumerable properties **up the whole prototype chain**, and the patch skipped `Object.defineProperty` with `enumerable: false` (which is how the platform defines built-in methods).

> [!warning]
> This is why extending built-in prototypes is banned in most style guides: the pollution is global and shows up far from the patch. Iterate arrays with `for...of`, `map`, or index loops, which read elements rather than enumerating keys. See [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]] and [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]].

## 10. Interview Answer

Short answer:

> The prototype chain is the chain of objects JavaScript searches when a property is not found as an own property.

Deeper answer:

> Every ordinary object has an internal \[\[Prototype\]\] link. Property lookup checks own properties first, then follows that link until it finds the property or reaches `null`. Constructor functions and classes use prototypes to share methods across instances.

Production answer:

> I care about prototypes when debugging inherited properties, class methods, `instanceof`, `for...in`, and prototype pollution. In data-heavy frontend code, I usually prefer own-property operations like `Object.keys`, `Object.hasOwn`, and plain view models.

## 11. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Inherited methods get `this` equal to the prototype." | `this` is the receiver object used in the call. |
| "`Object.keys` includes inherited properties." | It includes own enumerable string keys only. |
| "`for...in` is the same as `Object.keys`." | `for...in` includes enumerable inherited properties. |
| "`instanceof` checks object shape." | It checks whether a prototype object is in the chain. |
| "Changing prototypes at runtime is harmless." | It can hurt performance and make behavior hard to reason about. |

## 12. Practice

1. Predict the output:

```js
const proto = { value: 1 };
const obj = Object.create(proto);

console.log(obj.value);
console.log(Object.hasOwn(obj, "value"));

obj.value = 2;

console.log(obj.value);
console.log(proto.value);
```

Expected output:

```txt
1
false
2
1
```

2. Build an object with `Object.create` and an inherited method.
3. Explain why inherited methods still see instance data through `this`.
4. Fix a `for...in` bug that copies inherited defaults.
5. Explain when `instanceof` is useful and when shape checks are better.

## Related Notes

- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]
- [[06 - Objects and Prototypes/04 - proto vs prototype|proto vs prototype]]
- [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]
- [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]
- [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]
- [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]]
- [[20 - Network and Security/07 - Prototype Pollution and Supply-Chain Basics|Prototype Pollution and Supply-Chain Basics]]
- [[12 - Advanced Language Concepts/15 - Proxy and Reflect|Proxy and Reflect]]
- [[01 - Roadmap|Roadmap]]
