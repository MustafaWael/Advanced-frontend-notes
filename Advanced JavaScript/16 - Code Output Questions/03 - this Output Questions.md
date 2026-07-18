---
tags: [javascript, code-output, interview, this-output-questions]
module: "16 - Code Output Questions"
priority: must-know
status: not-started
---

# this Output Questions

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: can identify the call site and binding rule before predicting output.
- Production signal: can debug lost receivers in callbacks, class methods, and event handlers.
- Fast track: solve Q1-Q8, then explain Q2, Q4, and Q8 aloud.

## Source Anchors

- [MDN: this](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this)
- [MDN: Function.prototype.bind](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind)
- [ECMAScript specification](https://tc39.es/ecma262/)

## Trace Method

For `this` questions:

1. Is the function regular or arrow?
2. What is the exact call site?
3. Which rule wins: `new`, explicit, implicit, or default?
4. Is the code strict mode or class code?
5. Was the method extracted from its receiver?

## Q1. Method Call

```js
const user = {
  name: 'Mustafa',
  greet() {
    return `Hello, ${this.name}`;
  },
};

console.log(user.greet());
```

### Expected Output

```text
Hello, Mustafa
```

### Why

`user.greet()` is an implicit binding call. The object to the left of the dot becomes `this`.

Related: [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]]

## Q2. Extracted Method In Strict Mode

```js
'use strict';

const user = {
  name: 'Mustafa',
  getName() {
    return this.name;
  },
};

const getName = user.getName;

try {
  console.log(getName());
} catch (error) {
  console.log(error.name);
}
```

### Expected Output

```text
TypeError
```

### Why

`const getName = user.getName` copies the function reference but not the receiver. `getName()` is a plain function call. In strict mode, default binding sets `this` to `undefined`, so `this.name` throws.

### Fix

```js
const getName = user.getName.bind(user);
console.log(getName()); // Mustafa
```

Related: [[05 - this Binding/02 - this in Strict Mode|this in Strict Mode]]

## Q3. Arrow Inside Method

```js
const user = {
  name: 'Mustafa',
  greet() {
    const inner = () => this.name;
    return inner();
  },
};

console.log(user.greet());
```

### Expected Output

```text
Mustafa
```

### Why

`user.greet()` gives `this = user` inside the regular method. The arrow function has no own `this`, so it captures `this` from `greet`.

### Production Angle

This is a good use of arrow functions: preserving `this` inside nested callbacks.

Related: [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]

## Q4. Regular Callback Loses Method Receiver

```js
'use strict';

function runCallback(callback) {
  callback();
}

const user = {
  name: 'Mustafa',
  greetLater() {
    runCallback(function () {
      try {
        console.log(this.name);
      } catch (error) {
        console.log(error.name);
      }
    });
  },
};

user.greetLater();
```

### Expected Output

```text
TypeError
```

### Why

`user.greetLater()` initially has `this = user`. But the callback passed to `runCallback` is a regular function. `runCallback` calls it as `callback()`, not as `user.callback()`. In strict mode, its `this` is `undefined`, so `this.name` throws.

### Fix

```js
setTimeout(() => {
  console.log(this.name);
}, 0);
```

The arrow callback captures `this` from `greetLater`.

Related: [[09 - Event Loop Advanced/04 - Timers|Timers]]

## Q5. `call` And `apply`

```js
function greet(prefix, suffix) {
  return `${prefix} ${this.name}${suffix}`;
}

const user = { name: 'Mustafa' };

console.log(greet.call(user, 'Hi', '!'));
console.log(greet.apply(user, ['Hello', '.']));
```

### Expected Output

```text
Hi Mustafa!
Hello Mustafa.
```

### Why

Both use explicit binding. `call` passes arguments individually. `apply` passes them as an array.

Related: [[05 - this Binding/05 - call apply bind|call apply bind]]

## Q6. Bound Function Cannot Be Rebound With `call`

```js
function getName() {
  return this.name;
}

const bound = getName.bind({ name: 'A' });

console.log(bound());
console.log(bound.call({ name: 'B' }));
```

### Expected Output

```text
A
A
```

### Why

`bind` creates a bound function with an internal bound `this`. Later `call` cannot override the bound `this`.

### Production Angle

Binding inside render creates a new function reference every render. In React, prefer stable handlers when identity matters.

Related: [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]

## Q7. `new` Binding

```js
function User(name) {
  this.name = name;
}

const user = new User('Mustafa');

console.log(user.name);
console.log(Object.getPrototypeOf(user) === User.prototype);
```

### Expected Output

```text
Mustafa
true
```

### Why

`new` creates a new object, sets its prototype to `User.prototype`, calls `User` with `this` bound to the new object, and returns that object.

Related: [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]]

## Q8. Class Method Extraction

```js
class Counter {
  count = 0;

  increment() {
    this.count += 1;
    return this.count;
  }
}

const counter = new Counter();
const increment = counter.increment;

try {
  console.log(increment());
} catch (error) {
  console.log(error.name);
}
```

### Expected Output

```text
TypeError
```

### Why

Class bodies are strict mode. `increment` is extracted and called as a plain function, so `this` is `undefined`. Accessing `this.count` throws.

### Fix

Use a bound method, wrapper, or arrow class field.

Related: [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]]

## Q9. Arrow Class Field

```js
class Counter {
  count = 0;

  increment = () => {
    this.count += 1;
    return this.count;
  };
}

const counter = new Counter();
const increment = counter.increment;

console.log(increment());
console.log(increment.call({ count: 100 }));
console.log(counter.count);
```

### Expected Output

```text
1
2
2
```

### Why

The arrow function is created as an instance field and captures `this` from instance initialization. It remains bound to `counter`, even when extracted or called with `.call`.

### Tradeoff

Each instance gets its own function, unlike prototype methods which are shared. That is usually fine for UI classes but worth knowing.

Related: [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]

## Q10. `this` In An Event-Like Wrapper

```js
const button = {
  label: 'Save',
  click(handler) {
    handler();
  },
  clickWithReceiver(handler) {
    handler.call(this);
  },
};

function logLabel() {
  console.log(this && this.label);
}

button.click(logLabel);
button.clickWithReceiver(logLabel);
```

### Expected Output

```text
undefined
Save
```

### Why

`button.click(logLabel)` calls `handler()` as a plain function, so `this` is not `button`. `clickWithReceiver` explicitly calls `handler.call(this)`, and `this` inside `clickWithReceiver` is `button`.

### Production Angle

APIs decide how callbacks are called. Do not assume a callback receives your original object as `this`.

Related: [[05 - this Binding/08 - this Checklist|this Checklist]]

## Review Loop

- [ ] I identified the call site before predicting output.
- [ ] I explained strict mode where it changes the result.
- [ ] I named when arrow functions ignore call-site binding.
- [ ] I can fix each broken case with `bind`, wrapper, or arrow where appropriate.

## Related Notes

- [[05 - this Binding/08 - this Checklist|this Checklist]]
- [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]]
- [[16 - Code Output Questions/04 - Prototype Output Questions|Prototype Output Questions]]
