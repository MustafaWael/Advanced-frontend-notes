---
tags: [javascript, code-output, interview, mixed-advanced-output-questions]
module: "16 - Code Output Questions"
priority: important
status: not-started
---

# Mixed Advanced Output Questions

## Maturity Target

- Priority: #important
- Study time: 120-150 minutes
- Interview signal: can combine coercion, destructuring, iterators, symbols, private fields, WeakMap, closures, prototypes, and async timing.
- Production signal: can spot edge cases that cause bugs in real frontend data handling and framework code.
- Fast track: solve Q1-Q8 first, then use Q11-Q12 as final boss drills.

## Source Anchors

- [MDN: Type coercion](https://developer.mozilla.org/en-US/docs/Glossary/Type_coercion)
- [MDN: Destructuring](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Destructuring_assignment)
- [MDN: Generator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Generator)
- [MDN: Symbol](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol)
- [MDN: Optional chaining](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining)
- [MDN: WeakMap](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/WeakMap)

## Trace Method

For mixed questions:

1. Identify which concept is active.
2. Reduce expressions step by step.
3. For objects, ask whether keys are string or Symbol.
4. For defaults, ask whether the value is exactly `undefined`.
5. For async, use the Module 16 async trace method.
6. Avoid saying "weird"; name the rule.

## Q1. Coercion With Operators

```js
console.log(1 + '2');
console.log('3' - 1);
console.log(true + true);
console.log([] + []);
console.log([] + {});
console.log(+[]);
```

### Expected Output

```text
12
2
2

[object Object]
0
```

### Why

- `1 + '2'` performs string concatenation.
- `'3' - 1` performs numeric subtraction.
- `true + true` becomes `1 + 1`.
- `[] + []` converts both arrays to empty strings.
- `[] + {}` becomes `'' + '[object Object]'`.
- Unary `+[]` converts `[]` to `''`, then to `0`.

### Common Wrong Answer

Assuming `+` always means numeric addition. It can mean string concatenation after ToPrimitive.

Related: [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]

## Q2. Abstract Equality Edge Cases

```js
console.log(null == undefined);
console.log(null == 0);
console.log('' == false);
console.log(0 == false);
console.log(NaN == NaN);
```

### Expected Output

```text
true
false
true
true
false
```

### Why

`null == undefined` is a special true case. `null` does not equal `0`. Empty string and `false` both coerce to `0` in the relevant comparisons. `NaN` is not equal to itself under `==` or `===`.

Related: [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]

## Q3. Destructuring Defaults

```js
const [a = 1, b = 2, c = 3, d = 4] = [10, undefined, null, 0];

console.log(a, b, c, d);
```

### Expected Output

```text
10 2 null 0
```

### Why

Destructuring defaults apply only when the value is exactly `undefined`. They do not replace `null`, `0`, empty string, or `false`.

### Production Bug

Using defaults and expecting them to replace `null` API values can produce unexpected UI. Normalize API data explicitly.

Related: [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]]

## Q4. Object Spread Last Wins

```js
const defaults = { size: 'md', disabled: false, color: 'blue' };
const userProps = { disabled: true, color: 'red' };

const props = { ...defaults, ...userProps, color: 'green' };

console.log(props);
```

### Expected Output

```text
{ size: 'md', disabled: true, color: 'green' }
```

### Why

Object spread copies own enumerable properties from left to right. Later properties overwrite earlier properties with the same key.

### Production Angle

Order matters when merging default props, API payloads, and user overrides.

Related: [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]]

## Q5. Generator Steps

```js
function* gen() {
  yield 1;
  yield 2;
  return 3;
  yield 4;
}

const iterator = gen();

console.log(iterator.next());
console.log(iterator.next());
console.log(iterator.next());
console.log(iterator.next());
```

### Expected Output

```text
{ value: 1, done: false }
{ value: 2, done: false }
{ value: 3, done: true }
{ value: undefined, done: true }
```

### Why

Calling a generator returns an iterator without running the body. Each `next()` resumes until the next `yield` or `return`. A `return` completes the generator with `done: true`; later `next()` calls stay complete.

### Follow-Up

`for...of` ignores the final return value because iteration stops when `done` is `true`.

Related: [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]

## Q6. Symbol Keys

```js
const id = Symbol('id');
const user = {
  [id]: 123,
  name: 'Mustafa',
};

console.log(Object.keys(user));
console.log(user[id]);
console.log(JSON.stringify(user));
console.log(Reflect.ownKeys(user).length);
```

### Expected Output

```text
[ 'name' ]
123
{"name":"Mustafa"}
2
```

### Why

`Object.keys` returns enumerable string keys, not Symbols. Direct access with the Symbol works. `JSON.stringify` ignores Symbol-keyed properties. `Reflect.ownKeys` includes both string and Symbol own keys.

Related: [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]

## Q7. Private Field Access

```js
class Person {
  #name;

  constructor(name) {
    this.#name = name;
  }

  getName() {
    return this.#name;
  }
}

const person = new Person('Mustafa');

console.log(person.getName());

try {
  eval('person.#name');
} catch (error) {
  console.log(error.name);
}
```

### Expected Output

```text
Mustafa
SyntaxError
```

### Why

Private fields are syntax-enforced. Code outside the class body cannot access `#name`. Using `eval` lets the SyntaxError be caught for demonstration; writing `person.#name` directly would prevent the whole script from parsing.

Related: [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]

## Q8. Optional Chaining Is Nullish-Only

```js
const data = { count: 0, nested: { value: '' } };

console.log(data?.count);
console.log(data?.missing?.value);
console.log(data?.nested?.value?.length);
console.log(data?.count?.toString());
```

### Expected Output

```text
0
undefined
0
0
```

### Why

Optional chaining short-circuits only on `null` or `undefined`. It does not short-circuit on `0` or `''`. `data.count` is `0`, and `(0).toString()` returns `'0'`, which logs as `0`.

Related: [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]

## Q9. Nullish Coalescing Vs OR

```js
console.log(0 || 'default');
console.log(0 ?? 'default');
console.log('' || 'fallback');
console.log('' ?? 'fallback');
console.log(null ?? 'value');
console.log(undefined ?? 'value');
```

### Expected Output

```text
default
0
fallback

value
value
```

### Why

`||` falls back for any falsy value. `??` falls back only for `null` or `undefined`. That preserves meaningful falsy values like `0` and `''`.

### Production Bug

Using `value || defaultValue` can incorrectly replace legitimate `0`, empty string, or `false` values in forms and UI state.

Related: [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]

## Q10. WeakMap Key After Reference Is Cleared

```js
const cache = new WeakMap();

let element = { id: 'button' };

cache.set(element, 'metadata');

console.log(cache.get(element));

element = null;

console.log(cache.has(element));
```

### Expected Output

```text
metadata
false
```

### Why

Before reassignment, `element` references the key object. After `element = null`, `cache.has(element)` is `cache.has(null)`, and `null` is not the stored key. The original object may become eligible for garbage collection if no other strong references exist.

### Production Angle

WeakMap is useful for metadata tied to object lifetimes, such as DOM nodes, because it does not keep keys alive.

Related: [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]

## Q11. Closure Plus Prototype Trap

```js
'use strict';

function Counter() {
  let count = 0;

  this.increment = function () {
    count += 1;
    return count;
  };
}

Counter.prototype.reset = function () {
  count = 0;
};

const counter = new Counter();

console.log(counter.increment());
console.log(counter.increment());

try {
  counter.reset();
} catch (error) {
  console.log(error.name);
}

console.log(counter.increment());
```

### Expected Output

```text
1
2
ReferenceError
3
```

### Why

`increment` is created inside the constructor and closes over that constructor call's `count`. `reset` is defined on the prototype outside the constructor, so it does not close over the constructor's `count`. In strict mode, assigning to undeclared `count` in `reset` throws `ReferenceError`. The closure count remains `2`, so the final increment returns `3`.

### Fix

Define `reset` inside the constructor too, or use a class private field.

Related: [[03 - Scope and Variables/05 - Closures|Closures]], [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]]

## Q12. Async Timing With Shared Binding

```js
let value = 1;

async function update() {
  await Promise.resolve();
  value = 2;
}

update();

console.log(value);

Promise.resolve().then(() => console.log(value));
```

### Expected Output

```text
1
2
```

### Why

`update` suspends at `await` and queues its continuation first. The synchronous log reads `value = 1`. Then a separate Promise microtask is queued to log `value`. During microtask draining, `update`'s continuation runs first and sets `value = 2`; the later `.then` reads `2`.

### Follow-Up

If the `.then` were queued before `update()`, it would log `1` because microtask order is FIFO.

Related: [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]]

## Review Loop

- [ ] I can name the rule behind each surprising output.
- [ ] I can distinguish falsy from nullish.
- [ ] I can explain Symbol-key visibility.
- [ ] I can explain generator `return` vs `yield`.
- [ ] I can combine closure and prototype reasoning.
- [ ] I can trace async shared binding timing.

## Related Notes

- [[12 - Advanced Language Concepts/11 - Advanced Concepts Checklist|Advanced Concepts Checklist]]
- [[15 - Interview Preparation/03 - Strong Mid Level Questions|Strong Mid Level Questions]]
- [[15 - Interview Preparation/07 - Interview Checklist|Interview Checklist]]
- [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]]
- [[16 - Code Output Questions/05 - Async and Event Loop Output Questions|Async and Event Loop Output Questions]]
