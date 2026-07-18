---
tags: [javascript, objects, prototypes, classes-and-inheritance]
module: "06 - Objects and Prototypes"
priority: important
status: not-started
---

# Classes and Inheritance

## Maturity Target

- Priority: #important
- Study time: 100-120 minutes
- Interview signal: you can explain classes as syntax over prototypes, `extends`, `super`, static members, private fields, and method binding.
- Production signal: you can choose composition vs inheritance, avoid class instance serialization mistakes, and debug method/context issues.
- Dependencies: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]], [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]

## Source Anchors

- [MDN - Classes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes)
- [MDN - constructor](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes/constructor)
- [MDN - extends](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes/extends)
- [MDN - super](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/super)
- [ECMAScript 2026 - Class definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-class-definitions)

## 1. Concept

JavaScript classes are syntax for creating constructor functions, prototypes, methods, inheritance, fields, static members, and private names.

```js
class User {
  constructor(name) {
    this.name = name;
  }

  greet() {
    return `Hi ${this.name}`;
  }
}

const user = new User("Ava");

console.log(user.greet()); // "Hi Ava"
```

Class methods are on the prototype:

```js
console.log(Object.hasOwn(user, "greet")); // false
console.log(Object.getPrototypeOf(user) === User.prototype); // true
```

## 2. Why It Matters

You need class knowledge for:

- React class components and error boundaries.
- Custom elements.
- SDK/client classes.
- Legacy codebases.
- Inheritance and subclass debugging.
- Private fields and encapsulation.
- Prototype output questions.

Even if you prefer functions/hooks, classes still appear in JavaScript APIs and interviews.

## 3. Class Semantics That Matter

- Class declarations are in TDZ until initialized.
- Class constructors must be called with `new`.
- Class bodies are strict mode.
- Prototype methods are not auto-bound.
- Instance fields are created per instance.
- Static fields/methods live on the class constructor.
- Private fields use `#name` syntax and are not normal properties.

```js
try {
  new Product();
} catch (error) {
  console.log(error.name); // "ReferenceError"
}

class Product {}
```

## 4. Instance Fields and Prototype Methods

```js
class Counter {
  count = 0;

  increment() {
    this.count += 1;
    return this.count;
  }
}

const a = new Counter();
const b = new Counter();

console.log(a.increment === b.increment); // true
```

`count` is an own property on each instance. `increment` is shared on `Counter.prototype`.

Arrow field:

```js
class Counter {
  count = 0;

  increment = () => {
    this.count += 1;
    return this.count;
  };
}

const a = new Counter();
const b = new Counter();

console.log(a.increment === b.increment); // false
```

Use arrow fields when callback safety matters more than shared method memory.

## 5. Inheritance With `extends`

```js
class ApiResource {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  url(path) {
    return `${this.baseUrl}${path}`;
  }
}

class ProductResource extends ApiResource {
  productUrl(productId) {
    return this.url(`/products/${productId}`);
  }
}

const products = new ProductResource("/api");

console.log(products.productUrl("p1")); // "/api/products/p1"
```

`extends` sets up two prototype relationships:

- `ProductResource.prototype` inherits from `ApiResource.prototype`.
- `ProductResource` inherits static members from `ApiResource`.

```js
console.log(Object.getPrototypeOf(ProductResource.prototype) === ApiResource.prototype); // true
console.log(Object.getPrototypeOf(ProductResource) === ApiResource); // true
```

## 6. `super`

In derived constructors, call `super()` before using `this`.

```js
class BaseView {
  constructor(root) {
    this.root = root;
  }
}

class ModalView extends BaseView {
  constructor(root, title) {
    super(root);
    this.title = title;
  }
}
```

`super.method()` calls the parent prototype method with the current `this`.

```js
class BaseButton {
  label() {
    return "Base";
  }
}

class SaveButton extends BaseButton {
  label() {
    return `${super.label()}: Save`;
  }
}

console.log(new SaveButton().label()); // "Base: Save"
```

## 7. Static Members

```js
class ApiClient {
  static defaultBaseUrl = "/api";

  static createDefault() {
    return new this(this.defaultBaseUrl);
  }

  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }
}

const client = ApiClient.createDefault();

console.log(client.baseUrl); // "/api"
```

In a static method, `this` is the class used for the call. This supports subclass factories, but use it carefully because static inheritance can hide dependencies.

## 8. Private Fields

```js
class TokenStore {
  #token = null;

  setToken(token) {
    this.#token = token;
  }

  authorizationHeader() {
    return this.#token ? { Authorization: `Bearer ${this.#token}` } : {};
  }
}

const store = new TokenStore();
store.setToken("abc");

console.log(store.authorizationHeader());
// { Authorization: "Bearer abc" }
```

Private fields are not string-keyed properties. You cannot access `store["#token"]`.

> [!tip] Tradeoff
> private fields provide real encapsulation, but can make testing internals harder. Test public behavior.

## 9. Real Frontend Scenario: Class Instances in State

Bug:

```jsx
class Cart {
  items = [];

  add(item) {
    this.items.push(item);
  }
}

function CartView() {
  const [cart, setCart] = useState(() => new Cart());

  function addItem(item) {
    cart.add(item);
    setCart(cart); // Same reference; React may not re-render.
  }
}
```

Fix with plain immutable state:

```jsx
function CartView() {
  const [items, setItems] = useState([]);

  function addItem(item) {
    setItems((currentItems) => [...currentItems, item]);
  }
}
```

> [!tip] Tradeoff
> classes can be good for services and controllers. React render state is usually better as plain serializable data.

## 10. Composition vs Inheritance

Inheritance is useful when there is a true "is-a" relationship and shared behavior is stable. Composition is often better for frontend features because requirements change and combinations multiply.

Inheritance:

```js
class AuthenticatedClient extends ApiClient {}
```

Composition:

```js
function createAuthenticatedClient(fetcher, getToken) {
  return {
    async get(path) {
      return fetcher(path, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
    }
  };
}
```

Composition makes dependencies explicit and is usually easier to test.

## 11. Interview Answer

Short answer:

> JavaScript classes are syntax over prototypes. Methods go on the prototype, constructors initialize instances, and `extends` sets up prototype inheritance.

Deeper answer:

> Classes are strict, must be called with `new`, and have TDZ behavior. `extends` links both the instance prototype chain and the constructor/static chain. `super()` is required before `this` in derived constructors. Instance fields are own properties, while methods are usually shared on the prototype.

Production answer:

> I use classes for objects with real behavior and lifecycle, such as controllers or clients. I avoid putting mutable class instances in React state unless I intentionally manage identity. For feature code, composition is often simpler than deep inheritance.

## 12. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Classes are a different object model." | They still use prototypes. |
| "Class methods auto-bind." | They do not. |
| "Instance fields are on the prototype." | They are own properties per instance. |
| "`extends` only links instance methods." | It also links static inheritance. |
| "Private fields are just naming convention." | `#private` fields are language-enforced private names. |

## 13. Practice

1. Predict the output:

```js
class A {
  method() {
    return "A";
  }
}

class B extends A {
  method() {
    return `${super.method()}B`;
  }
}

console.log(new B().method());
console.log(Object.getPrototypeOf(B.prototype) === A.prototype);
console.log(Object.getPrototypeOf(B) === A);
```

Expected output:

```txt
AB
true
true
```

2. Create a class with a private field and a public getter.
3. Explain why `this` before `super()` throws.
4. Convert a small inheritance example to composition.
5. Explain why spreading a class instance loses prototype methods.

## Related Notes

- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[06 - Objects and Prototypes/04 - proto vs prototype|proto vs prototype]]
- [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]
- [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[01 - Roadmap|Roadmap]]
