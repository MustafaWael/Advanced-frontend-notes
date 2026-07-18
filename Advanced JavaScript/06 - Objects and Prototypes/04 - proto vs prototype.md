---
tags: [javascript, objects, prototypes, proto-vs-prototype]
module: "06 - Objects and Prototypes"
priority: must-know
status: not-started
---

# proto vs prototype

## Maturity Target

- Priority: #must-know
- Study time: 60-75 minutes
- Interview signal: you can separate an object's internal \[\[Prototype\]\] link from a constructor function's `.prototype` property.
- Production signal: you can inspect prototype chains safely without mutating prototypes in hot or security-sensitive code.
- Dependencies: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]], [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]

## Source Anchors

- [MDN - Object.prototype.__proto__](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/proto)
- [MDN - Object.getPrototypeOf](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/getPrototypeOf)
- [MDN - Object.setPrototypeOf](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/setPrototypeOf)
- [MDN - new](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/new)

## 1. Concept

\[\[Prototype\]\] is the internal link from an object to its prototype.

`__proto__` is a legacy accessor that exposes that internal link on many objects.

`.prototype` is a normal property on constructor functions and classes. When you call a function with `new`, the new object's internal prototype is set to the constructor's `.prototype` object.

```js
function User(name) {
  this.name = name;
}

const user = new User("Ava");

console.log(Object.getPrototypeOf(user) === User.prototype); // true
```

## 2. Why It Matters

This distinction appears in almost every prototype interview question:

- `user.__proto__ === User.prototype`
- `User.prototype.constructor === User`
- `Object.getPrototypeOf(user) === User.prototype`
- `User.__proto__ === Function.prototype`

If you mix up instance prototype links and constructor `.prototype` objects, class/inheritance questions become confusing.

## 3. Preferred APIs

Use these in modern code:

```js
Object.getPrototypeOf(obj);
Object.setPrototypeOf(obj, proto);
Object.create(proto);
```

Avoid writing `obj.__proto__ = proto` in production code. It is legacy, can be slower, and can be dangerous with untrusted input.

## 4. `__proto__`

```js
const proto = { shared: true };
const obj = Object.create(proto);

console.log(obj.__proto__ === proto); // true in environments supporting __proto__
console.log(Object.getPrototypeOf(obj) === proto); // true
```

`__proto__` is not the same as `.prototype`.

```js
function User() {}
const user = new User();

console.log(user.__proto__ === User.prototype); // true
console.log(User.__proto__ === Function.prototype); // true
```

## 5. `.prototype`

Only functions intended for construction and classes use `.prototype` to provide instance methods.

```js
function User(name) {
  this.name = name;
}

User.prototype.greet = function greet() {
  return `Hi ${this.name}`;
};

const user = new User("Ava");

console.log(user.greet()); // "Hi Ava"
console.log(user.hasOwnProperty("greet")); // false
```

The method lives on `User.prototype`, not on the instance.

## 6. Arrow Functions and `.prototype`

Arrow functions cannot be constructors and do not have a useful `.prototype` for instance construction.

```js
const User = (name) => {
  this.name = name;
};

console.log(User.prototype); // undefined

try {
  new User("Ava");
} catch (error) {
  console.log(error.name); // "TypeError"
}
```

## 7. Runtime Prototype Mutation

Changing an object's prototype after creation is usually a bad production pattern.

```js
const user = { name: "Ava" };
const methods = {
  greet() {
    return `Hi ${this.name}`;
  }
};

Object.setPrototypeOf(user, methods);

console.log(user.greet()); // "Hi Ava"
```

Prefer creating the object with the correct prototype from the start:

```js
const user = Object.create(methods);
user.name = "Ava";
```

> [!tip] Tradeoff
> `Object.setPrototypeOf` is useful for low-level libraries and rare interoperability work, but it makes object behavior change after creation and may deoptimize engines.

## 8. Real Frontend Scenario: Debugging Class Instances

```js
class ApiClient {
  get(path) {
    return fetch(path);
  }
}

const client = new ApiClient();

console.log(Object.getPrototypeOf(client) === ApiClient.prototype); // true
console.log(Object.hasOwn(client, "get")); // false
console.log("get" in client); // true
```

This explains why spreading a class instance does not copy prototype methods:

```js
const copy = { ...client };

console.log(copy.get); // undefined
```

Production consequence: class instances do not behave like plain JSON objects. Avoid storing class instances in React state or serializing them as if they were plain data unless that is deliberate.

## Real-World Use Cases

### Rehydrating persisted state loses the prototype link

A cart class is saved to `localStorage` as JSON. On reload, `JSON.parse` builds a plain object whose internal \[\[Prototype\]\] is `Object.prototype` — not `Cart.prototype` — so methods are gone and `instanceof` fails.

```js
class Cart {
  constructor(items = []) { this.items = items; }
  total() { return this.items.reduce((sum, i) => sum + i.price, 0); }
}

const saved = JSON.parse(localStorage.getItem("cart"));

saved.total();            // TypeError: saved.total is not a function
saved instanceof Cart;    // false

const cart = Object.assign(new Cart(), saved); // re-link via `new`
cart.total();             // works: [[Prototype]] is Cart.prototype again
```

Fails because serialization copies own data properties only; the internal prototype link is not data and cannot survive a JSON round trip. This is a core reason to prefer plain objects + functions for persisted/transferred state. See [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]] and [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]].

### Mocking one method for every instance via `.prototype`

In tests, you rarely have a reference to the instance a component creates internally. Spying on the constructor's `.prototype` patches the single shared function object, so every instance — existing and future — sees the mock.

```ts
jest.spyOn(ApiClient.prototype, "get").mockResolvedValue({ orders: [] });

render(<OrdersPage />); // whatever ApiClient instance it news up uses the mock
```

Works because instances do not own `get`; each call is a chain lookup that lands on `ApiClient.prototype.get` — replace that one property and all lookups resolve to the replacement.

> [!warning]
> The patch is global and mutable shared state. Always restore it (`jest.restoreAllMocks`) or one test's mock leaks into the next. See [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]].

### `extends Error` compiled to ES5: the one legitimate `setPrototypeOf`

A famous TypeScript/Babel gotcha: with `target: "ES5"`, `class ApiError extends Error` produces instances whose internal prototype is `Error.prototype`, not `ApiError.prototype` — because ES5 can't replicate how `super()` constructs the object. Result: `err instanceof ApiError` is `false` and custom methods vanish.

```ts
class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    Object.setPrototypeOf(this, new.target.prototype); // restore the intended link
  }
}
```

This is the textbook case where mutating \[\[Prototype\]\] at runtime is correct: the constructor's `.prototype` and the instance's internal link disagree, and one line reconciles them. See [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]].

## 9. Interview Answer

Short answer:

> `.prototype` is a property on constructor functions/classes used for instances created with `new`. `__proto__` is a legacy accessor on objects for their internal prototype. Prefer `Object.getPrototypeOf`.

Deeper answer:

> When `new Fn()` runs, the new object's internal prototype is set to `Fn.prototype`. Many environments expose that internal link through `obj.__proto__`, but the standard, clear API is `Object.getPrototypeOf(obj)`. The constructor's `.prototype` object is where shared instance methods usually live.

Production answer:

> I inspect prototypes with `Object.getPrototypeOf`, create prototype-linked objects with `Object.create`, and avoid runtime prototype mutation or `__proto__` assignment in application code. For data models, I prefer plain objects unless methods/prototypes are actually needed.

## 10. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "`prototype` exists on every object." | `.prototype` is mainly on functions/classes used as constructors. |
| "`__proto__` and `.prototype` are the same." | `__proto__` accesses an object's internal prototype; `.prototype` is a constructor property. |
| "Spreading an instance copies methods." | Spread copies own enumerable properties, not prototype methods. |
| "Changing `__proto__` is normal app code." | Prefer stable creation patterns; mutation can hurt performance and safety. |
| "Arrow functions can be constructors." | They cannot and do not have constructor `.prototype` behavior. |

## 11. Practice

1. Predict the output:

```js
function User() {}
const user = new User();

console.log(Object.getPrototypeOf(user) === User.prototype);
console.log(User.prototype.constructor === User);
console.log(Object.getPrototypeOf(User) === Function.prototype);
```

Expected output:

```txt
true
true
true
```

2. Explain why `{ ...instance }` does not copy class methods.
3. Replace `obj.__proto__` usage with `Object.getPrototypeOf`.
4. Create an object with a custom prototype using `Object.create`.
5. Explain why `Object.setPrototypeOf` should be rare in application code.

## Related Notes

- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]
- [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]
- [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]
- [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]]
- [[01 - Roadmap|Roadmap]]
