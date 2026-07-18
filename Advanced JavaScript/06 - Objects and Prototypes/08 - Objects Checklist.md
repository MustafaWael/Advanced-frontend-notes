---
tags: [javascript, objects, prototypes, objects-checklist]
module: "06 - Objects and Prototypes"
priority: important
status: not-started
---

# Objects Checklist

Use this checklist as an active test. Mark an item complete only when you can explain the mechanism, predict code output, and connect it to a real frontend bug.

## Source Anchors

- [MDN - Working with objects](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Working_with_objects)
- [MDN - Prototype chain](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Inheritance_and_the_prototype_chain)
- [MDN - Object.getOwnPropertyDescriptor](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/getOwnPropertyDescriptor)
- [MDN - new](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/new)
- [React - Updating objects in state](https://react.dev/learn/updating-objects-in-state)

## Objects Internally

- [ ] I can explain objects as property collections with string/symbol keys.
- [ ] I can explain internal slots like \[\[Prototype\]\] and \[\[Extensible\]\].
- [ ] I can distinguish own properties from inherited properties.
- [ ] I can explain reference identity.
- [ ] I can explain why object keys stringify unless they are symbols.
- [ ] I can choose `Map` when keys are objects.
- [ ] I can identify prototype pollution risk in dynamic-key code.

## Property Descriptors

- [ ] I can read a data descriptor.
- [ ] I can read an accessor descriptor.
- [ ] I can explain `writable`, `enumerable`, and `configurable`.
- [ ] I can explain why `Object.defineProperty` defaults missing booleans to false.
- [ ] I can create a non-enumerable property.
- [ ] I can explain why `Object.freeze` is shallow.
- [ ] I can avoid getters with expensive side effects in render paths.

## Prototype Chain

- [ ] I can trace property lookup from own property to prototype to `null`.
- [ ] I can explain shadowing.
- [ ] I can explain why inherited methods still receive the instance as `this`.
- [ ] I can explain why `for...in` includes inherited enumerable properties.
- [ ] I can explain how `instanceof` uses the prototype chain.
- [ ] I can explain when `Object.hasOwn` is safer than property access.

## proto vs prototype

- [ ] I can explain the internal \[\[Prototype\]\] link.
- [ ] I can explain why `__proto__` is legacy.
- [ ] I can explain `.prototype` as a constructor/class property.
- [ ] I can show `Object.getPrototypeOf(instance) === Constructor.prototype`.
- [ ] I can explain why spreading a class instance does not copy prototype methods.
- [ ] I can avoid runtime prototype mutation in application code.

## Constructors and Classes

- [ ] I can explain the four steps of `new`.
- [ ] I can implement a simplified `myNew`.
- [ ] I can explain constructor object-return override.
- [ ] I can explain why methods belong on prototypes for sharing.
- [ ] I can explain class TDZ, strictness, and `new` requirement.
- [ ] I can explain `extends`, `super`, static members, and private fields.
- [ ] I can choose class, constructor, or factory based on the problem.

## Copying and Immutability

- [ ] I can explain shallow copy vs deep copy.
- [ ] I can update nested React state by copying the changed path.
- [ ] I can explain structural sharing.
- [ ] I can avoid mutating arrays with `sort`, `push`, or `splice` in state.
- [ ] I can explain what `structuredClone` handles better than JSON cloning.
- [ ] I can explain why deep cloning everything is not always good.
- [ ] I can explain when Immer is useful.

## Code Snippets to Trace

### Snippet 1: Own vs Inherited

```js
const proto = { role: "guest" };
const user = Object.create(proto);
user.name = "Ava";

console.log(user.role);
console.log(Object.hasOwn(user, "role"));
console.log(Object.keys(user));
```

Expected output:

```txt
guest
false
["name"]
```

### Snippet 2: Descriptor Defaults

```js
const obj = {};

Object.defineProperty(obj, "id", {
  value: 1
});

console.log(Object.keys(obj));
console.log(Object.getOwnPropertyDescriptor(obj, "id").writable);
```

Expected output:

```txt
[]
false
```

### Snippet 3: Prototype Shadowing

```js
const defaults = { theme: "light" };
const settings = Object.create(defaults);

console.log(settings.theme);

settings.theme = "dark";

console.log(settings.theme);
console.log(defaults.theme);
```

Expected output:

```txt
light
dark
light
```

### Snippet 4: `__proto__` vs `.prototype`

```js
function User() {}
const user = new User();

console.log(Object.getPrototypeOf(user) === User.prototype);
console.log(Object.getPrototypeOf(User) === Function.prototype);
```

Expected output:

```txt
true
true
```

### Snippet 5: Constructor Return

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

### Snippet 6: Class Inheritance

```js
class Shape {
  area() {
    return 0;
  }
}

class Circle extends Shape {
  area() {
    return super.area() + 10;
  }
}

const circle = new Circle();

console.log(circle.area());
console.log(Object.getPrototypeOf(Circle.prototype) === Shape.prototype);
console.log(Object.getPrototypeOf(Circle) === Shape);
```

Expected output:

```txt
10
true
true
```

### Snippet 7: Shallow Copy

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

## Production Debugging Drills

1. Inspect an API response normalizer and identify whether it mutates caller-owned objects.
2. Find a `for...in` loop and add `Object.hasOwn` if inherited keys would be unsafe.
3. Inspect a class instance spread and explain what methods are lost.
4. Convert a mutating React state update into a structural-sharing update.
5. Replace a dynamic-key object dictionary with `Map` or a null-prototype object.
6. Add a non-enumerable debug property and inspect it with `Object.getOwnPropertyDescriptor`.
7. Explain whether `instanceof` is appropriate for validating API data.

## Interview Quick Answers

| Question | Strong short answer |
| --- | --- |
| What is an object? | A mutable collection of string/symbol keyed properties with internal slots like \[\[Prototype\]\]. |
| Own vs inherited? | Own is stored on the object; inherited is found through the prototype chain. |
| What is a descriptor? | Metadata describing an own property's value/getter and flags. |
| What is the prototype chain? | The chain searched when a property is missing on the object itself. |
| `.prototype` vs `__proto__`? | `.prototype` is on constructors; `__proto__` exposes an object's internal prototype link. |
| What does `new` do? | Creates an object, links its prototype, calls the constructor with `this`, returns the object unless overridden. |
| Are classes a new object model? | No. They use prototypes with stricter syntax and class features. |
| Shallow vs deep copy? | Shallow copies the top level; deep copies nested values too. |
| Why immutable React state? | React uses reference changes to know what changed and re-render. |

## Mastery Criteria

- [ ] I can solve every snippet without running it.
- [ ] I can explain each file in this module in 30 seconds and in 2 minutes.
- [ ] I can connect every concept to a realistic frontend bug.
- [ ] I can preserve links between object identity, React rendering, prototypes, and `this`.
- [ ] I can name one production tradeoff for descriptors, classes, copying, and prototypes.

## Related Notes

- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]
- [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]]
- [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]
- [[06 - Objects and Prototypes/04 - proto vs prototype|proto vs prototype]]
- [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]
- [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]]
- [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]]
- [[01 - Roadmap|Roadmap]]
