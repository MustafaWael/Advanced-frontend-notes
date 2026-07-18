---
tags: [javascript, code-output, interview, prototype-output-questions]
module: "16 - Code Output Questions"
priority: must-know
status: not-started
---

# Prototype Output Questions

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: can trace own properties, prototype lookup, shadowing, `instanceof`, and class sugar.
- Production signal: can debug objects from libraries, class methods, inherited properties, and cross-instance behavior.
- Fast track: solve Q1-Q8 and explain Q3 and Q6 aloud.

## Source Anchors

- [MDN: Inheritance and the prototype chain](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Inheritance_and_the_prototype_chain)
- [MDN: instanceof](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/instanceof)
- [MDN: Object.create](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/create)
- [ECMAScript specification](https://tc39.es/ecma262/)

## Trace Method

For prototype questions:

1. List own properties.
2. List the internal prototype chain.
3. For reads, walk own property then prototype chain.
4. For writes, check whether an own property is created.
5. For `instanceof`, ask whether `Constructor.prototype` appears in the chain.

## Q1. Basic Prototype Lookup

```js
function Animal(name) {
  this.name = name;
}

Animal.prototype.speak = function () {
  return `${this.name} speaks`;
};

const dog = new Animal('Dog');

console.log(dog.speak());
console.log(dog.hasOwnProperty('speak'));
console.log(dog.hasOwnProperty('name'));
```

### Expected Output

```text
Dog speaks
false
true
```

### Why

`name` is assigned directly to `dog` by the constructor, so it is an own property. `speak` lives on `Animal.prototype`, so `dog.speak()` finds it through the prototype chain, but `hasOwnProperty('speak')` is `false`.

Related: [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]

## Q2. `instanceof` Walks The Chain

```js
function Foo() {}
function Bar() {}

Bar.prototype = Object.create(Foo.prototype);

const value = new Bar();

console.log(value instanceof Bar);
console.log(value instanceof Foo);
console.log(value instanceof Object);
```

### Expected Output

```text
true
true
true
```

### Why

The chain is:

```text
value -> Bar.prototype -> Foo.prototype -> Object.prototype -> null
```

`instanceof` checks whether the constructor's `.prototype` object exists anywhere in that chain.

### Production Note

If you replace `Bar.prototype`, remember to restore `Bar.prototype.constructor` if code depends on it.

Related: [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]

## Q3. Property Shadowing

```js
function Animal() {}

Animal.prototype.sound = function () {
  return 'generic';
};

const animal = new Animal();

animal.sound = function () {
  return 'custom';
};

console.log(animal.sound());

delete animal.sound;

console.log(animal.sound());
```

### Expected Output

```text
custom
generic
```

### Why

Assigning `animal.sound` creates an own property that shadows `Animal.prototype.sound`. Deleting the own property reveals the prototype method again.

Related: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]

## Q4. Prototype Mutation Affects Instances Without Shadowing

```js
function Box() {}

Box.prototype.label = 'old';

const a = new Box();
const b = new Box();

a.label = 'own';

console.log(a.label, b.label);

Box.prototype.label = 'new';

console.log(a.label, b.label);
```

### Expected Output

```text
own old
own new
```

### Why

`a.label = 'own'` creates an own property on `a`. `b` still reads from `Box.prototype`. Updating `Box.prototype.label` affects `b`, but not `a` because `a` has an own shadowing property.

### Production Bug

Mutating prototypes at runtime can create surprising global behavior for all instances that do not shadow the property.

Related: [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]]

## Q5. `in` Vs Own Property

```js
function User() {
  this.own = true;
}

User.prototype.inherited = true;

const user = new User();

console.log('own' in user);
console.log('inherited' in user);
console.log(Object.hasOwn(user, 'own'));
console.log(Object.hasOwn(user, 'inherited'));
```

### Expected Output

```text
true
true
true
false
```

### Why

The `in` operator checks the whole prototype chain. `Object.hasOwn` checks only own properties.

### Production Angle

Use own-property checks when iterating user-controlled objects to avoid inherited keys.

Related: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]

## Q6. `Object.create`

```js
const proto = {
  greet() {
    return `Hello ${this.name}`;
  },
};

const user = Object.create(proto);
user.name = 'Mustafa';

console.log(user.greet());
console.log(Object.getPrototypeOf(user) === proto);
```

### Expected Output

```text
Hello Mustafa
true
```

### Why

`Object.create(proto)` creates a new object whose internal prototype is `proto`. `greet` is found on `proto`, and the method call binds `this` to `user`.

Related: [[06 - Objects and Prototypes/04 - proto vs prototype|proto vs prototype]]

## Q7. End Of The Prototype Chain

```js
const normal = {};
const dictionary = Object.create(null);

console.log(Object.getPrototypeOf(Object.prototype));
console.log(normal instanceof Object);
console.log(dictionary instanceof Object);
console.log(typeof dictionary.toString);
```

### Expected Output

```text
null
true
false
undefined
```

### Why

`Object.prototype` ends at `null`. A normal object has `Object.prototype` in its chain, so `normal instanceof Object` is `true`. A null-prototype object has no prototype, so it is not an instance of `Object` and does not inherit `toString`.

### Production Angle

Null-prototype objects can be useful as dictionaries, but code that assumes `obj.toString` or `obj.hasOwnProperty` exists can fail.

Related: [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]]

## Q8. `.prototype` Vs Internal Prototype

```js
function Tool() {}

const tool = new Tool();

console.log(typeof Tool.prototype);
console.log(typeof tool.prototype);
console.log(Object.getPrototypeOf(tool) === Tool.prototype);
```

### Expected Output

```text
object
undefined
true
```

### Why

`Tool.prototype` is a property on the constructor function. Instances do not automatically get a `.prototype` property. The instance's internal prototype is what points to `Tool.prototype`.

### Interview Line

Constructor `.prototype` is the object used for future instances. An instance's internal prototype is the actual delegation link.

Related: [[06 - Objects and Prototypes/04 - proto vs prototype|proto vs prototype]]

## Q9. Class Inheritance

```js
class Animal {
  speak() {
    return 'sound';
  }
}

class Dog extends Animal {
  speak() {
    return 'woof';
  }
}

const dog = new Dog();

console.log(dog.speak());
console.log(dog instanceof Dog);
console.log(dog instanceof Animal);
console.log(Object.getPrototypeOf(Dog.prototype) === Animal.prototype);
```

### Expected Output

```text
woof
true
true
true
```

### Why

`Dog.prototype` inherits from `Animal.prototype`. `dog.speak()` finds the overriding method on `Dog.prototype` first. `instanceof` succeeds for both constructors because both prototypes appear in the chain.

Related: [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]

## Q10. Static Vs Instance Methods

```js
class MathHelper {
  static square(n) {
    return n * n;
  }

  cube(n) {
    return n * n * n;
  }
}

const helper = new MathHelper();

console.log(MathHelper.square(3));
console.log(helper.cube(3));
console.log(helper.square);
console.log(MathHelper.cube);
```

### Expected Output

```text
9
27
undefined
undefined
```

### Why

Static methods live on the constructor function. Instance methods live on the prototype. Instances do not inherit static methods, and the class constructor does not directly have instance methods.

Related: [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]

## Review Loop

- [ ] I can draw the prototype chain for each question.
- [ ] I can explain own property vs inherited property.
- [ ] I can explain why `instanceof` can cross multiple prototype links.
- [ ] I can explain why null-prototype objects are special.

## Related Notes

- [[06 - Objects and Prototypes/08 - Objects Checklist|Objects Checklist]]
- [[15 - Interview Preparation/03 - Strong Mid Level Questions|Strong Mid Level Questions]]
- [[16 - Code Output Questions/03 - this Output Questions|this Output Questions]]
- [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]]
