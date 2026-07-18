---
tags: [javascript, this-binding, constructor-and-class-this]
module: "05 - this Binding"
priority: important
status: not-started
---

# Constructor and Class this

## Maturity Target

- Priority: #important
- Study time: 90-110 minutes
- Interview signal: you can explain `new`, constructor returns, class strictness, `super()`, prototype methods, and class field arrows.
- Production signal: you can choose instance methods, prototype methods, arrow fields, factories, and classes with clear lifecycle and memory tradeoffs.
- Dependencies: [[05 - this Binding/01 - What is this|What is this]], [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]], [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]

## Source Anchors

- [MDN - new operator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/new)
- [MDN - constructor](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes/constructor)
- [MDN - Classes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes)
- [MDN - super](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/super)
- [MDN - this](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this)

## 1. Concept

When a regular constructable function is called with `new`, JavaScript creates a new object and uses it as `this` inside the constructor.

```js
function User(name) {
  this.name = name;
}

const user = new User("Ava");

console.log(user.name); // "Ava"
```

Classes use constructor semantics too, but with stricter rules:

- Class constructors must be called with `new`.
- Class bodies are strict.
- Derived classes must call `super()` before using `this`.
- Methods are on the prototype unless they are fields.

## 2. Why It Matters

Constructor and class `this` matters in:

- Legacy constructor functions.
- UI controller classes.
- React class components.
- Custom elements.
- Inheritance-heavy code.
- Class fields and method callbacks.
- Tests that instantiate classes directly.

The main production tradeoff is sharing methods on the prototype vs creating per-instance arrow functions that are safe as callbacks.

## 3. What `new` Does

Simplified model:

```js
function simulateNew(Constructor, ...args) {
  const instance = Object.create(Constructor.prototype);
  const result = Constructor.apply(instance, args);

  if (result !== null && (typeof result === "object" || typeof result === "function")) {
    return result;
  }

  return instance;
}
```

Example:

```js
function Product(name) {
  this.name = name;
}

const product = simulateNew(Product, "Keyboard");

console.log(product.name); // "Keyboard"
console.log(product instanceof Product); // true
```

## 4. Constructor Return Values

If a constructor returns an object, that object replaces `this`.

```js
function CreatesDifferentObject() {
  this.value = 1;
  return { value: 2 };
}

console.log(new CreatesDifferentObject().value); // 2
```

If it returns a primitive, JavaScript ignores that primitive and returns `this`.

```js
function ReturnsPrimitive() {
  this.value = 1;
  return 2;
}

console.log(new ReturnsPrimitive().value); // 1
```

Production rule: constructors should usually initialize `this` and avoid returning explicit objects unless you are using a deliberate factory pattern.

## 5. Forgetting `new`

Legacy constructor functions can fail badly without `new`.

```js
function User(name) {
  "use strict";
  this.name = name;
}

try {
  const user = User("Ava");
  console.log(user);
} catch (error) {
  console.log(error.name); // "TypeError"
}
```

Classes fail clearly:

```js
class User {
  constructor(name) {
    this.name = name;
  }
}

try {
  User("Ava");
} catch (error) {
  console.log(error.name); // "TypeError"
}
```

## 6. Class Methods and Instance Fields

Prototype method:

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

Arrow class field:

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

Tradeoff:

- Prototype methods are memory-efficient and work well for normal method calls.
- Arrow fields are callback-safe but create a function per instance.

## 7. Derived Classes and `super()`

Derived constructors do not have usable `this` until `super()` returns.

```js
class BaseController {
  constructor(root) {
    this.root = root;
  }
}

class ModalController extends BaseController {
  constructor(root, title) {
    super(root);
    this.title = title;
  }
}

const modal = new ModalController(document.createElement("div"), "Settings");
console.log(modal.title); // "Settings"
```

> [!warning] Using `this` before `super()` throws
> In a subclass constructor, `this` doesn't exist until `super()` runs — touching `this.title` before the `super(root)` call throws a `ReferenceError`. Call `super()` first, then initialize instance fields.

Bug:

```js
class BrokenModal extends BaseController {
  constructor(root) {
    this.title = "Broken";
    super(root);
  }
}

try {
  new BrokenModal(document.createElement("div"));
} catch (error) {
  console.log(error.name); // "ReferenceError"
}
```

## 8. Static `this`

In static methods, `this` is the class constructor used for the call.

```js
class ApiResource {
  static endpoint = "/api";

  static url(path) {
    return `${this.endpoint}${path}`;
  }
}

class ProductResource extends ApiResource {
  static endpoint = "/api/products";
}

console.log(ApiResource.url("/health"));      // "/api/health"
console.log(ProductResource.url("/123"));     // "/api/products/123"
```

This can be useful for inheritance, but overusing static inheritance can make dependencies harder to test than explicit configuration.

## 9. Real Frontend Scenario: UI Controller

```js
class DropdownController {
  constructor(root) {
    this.root = root;
    this.button = root.querySelector("button");
    this.menu = root.querySelector("[role='menu']");
    this.toggle = this.toggle.bind(this);
  }

  mount() {
    this.button.addEventListener("click", this.toggle);
  }

  unmount() {
    this.button.removeEventListener("click", this.toggle);
  }

  toggle() {
    const isOpen = this.menu.hidden;
    this.menu.hidden = !isOpen;
    this.button.setAttribute("aria-expanded", String(isOpen));
  }
}
```

Why this is production-safe:

- The instance owns the DOM references.
- `toggle` is bound once, so callback context is stable.
- The same function reference is used for cleanup.

## 10. TypeScript Note

TypeScript can model `this` parameters for functions that expect an explicit receiver.

```ts
function format(this: { currency: string }, price: number) {
  return `${this.currency}${price.toFixed(2)}`;
}

format.call({ currency: "$" }, 10);
```

The `this` parameter is erased at runtime; it is a type-checking aid only.

## 11. Interview Answer

Short answer:

> With `new`, JavaScript creates a new object, sets it as `this`, runs the constructor, and returns the new object unless the constructor returns another object.

Deeper answer:

> Classes use the same constructor idea but add strict-mode rules. Class constructors cannot be called without `new`. In derived classes, `super()` must run before `this` is usable because the base constructor participates in creating the instance. Prototype methods are shared, while arrow class fields are per-instance and lexically bind `this`.

Production answer:

> I use prototype methods for shared behavior and bind them when passing as callbacks. I use arrow fields for callback-heavy classes when the per-instance function cost is acceptable. For many frontend use cases, factories or functions with explicit dependencies are simpler than inheritance.

## 12. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Constructors always return `this`." | Returning an object overrides `this`; returning a primitive does not. |
| "Classes auto-bind methods." | Methods are not auto-bound. |
| "Arrow class fields live on the prototype." | They are own properties on each instance. |
| "You can use `this` before `super()` in subclasses." | That throws in derived constructors. |
| "Static methods use instance `this`." | Static `this` is the class constructor used for the call. |

## 13. Practice

1. Predict the output:

```js
function A() {
  this.value = 1;
  return { value: 2 };
}

function B() {
  this.value = 1;
  return 2;
}

console.log(new A().value);
console.log(new B().value);
```

Expected output:

```txt
2
1
```

2. Explain why class methods fail when extracted.
3. Compare memory behavior of prototype methods and arrow class fields.
4. Fix a derived class that uses `this` before `super()`.
5. Build a small controller class with `mount` and `unmount` that cleans up event listeners.

## Related Notes

- [[05 - this Binding/01 - What is this|What is this]]
- [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]
- [[05 - this Binding/07 - React this Examples|React this Examples]]
- [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]
- [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]
- [[01 - Roadmap|Roadmap]]
