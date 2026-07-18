---
tags: [javascript, code-output, interview, scope-and-hoisting-output-questions]
module: "16 - Code Output Questions"
priority: must-know
status: not-started
---

# Scope and Hoisting Output Questions

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: can state output first, then explain binding creation, initialization, scope lookup, and TDZ.
- Production signal: can debug initialization-order bugs in modules, functions, and blocks.
- Fast track: solve Q1-Q8 without reading answers, then explain Q2 and Q5 aloud.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN: Grammar and types](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Grammar_and_types)
- [MDN: let](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let)
- [MDN: var](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/var)

## Trace Method

For every question:

1. Identify the scope: script, module, function, or block.
2. Do the creation phase: which bindings exist, and are they initialized?
3. Execute line by line.
4. Distinguish `ReferenceError` from `TypeError`.
5. State the output before explaining.

## Q1. `var` Hoisting

```js
console.log(x);
var x = 5;
console.log(x);
```

### Expected Output

```text
undefined
5
```

### Why

During creation, `var x` creates a binding and initializes it to `undefined`. The assignment `x = 5` runs later during execution.

### Common Wrong Answer

"It throws because `x` is used before declaration."

That would be true for `let` or `const`, not `var`.

### Interview Line

Nothing moved. The binding was created and initialized before execution.

Related: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

## Q2. Function Declaration Vs Function Expression

```js
console.log(foo());
console.log(bar());

function foo() {
  return 'foo';
}

var bar = function () {
  return 'bar';
};
```

### Expected Output

```text
foo
TypeError: bar is not a function
```

### Why

`foo` is a function declaration, so its binding is initialized to the function object during creation. `bar` is a `var` binding initialized to `undefined`; the function expression assignment has not executed yet. Calling `undefined()` throws `TypeError`.

### Common Wrong Answer

"`bar` gives `ReferenceError`."

`bar` exists. The problem is that its current value is `undefined`, not callable.

Related: [[04 - Functions Deep Dive/01 - Function Declarations vs Expressions|Function Declarations vs Expressions]]

## Q3. TDZ With `let`

```js
console.log(value);
let value = 10;
```

### Expected Output

```text
ReferenceError: Cannot access 'value' before initialization
```

### Why

The `let` binding exists from the start of the block, but it is uninitialized until the declaration is evaluated. Accessing it inside the Temporal Dead Zone throws `ReferenceError`.

### Common Wrong Answer

"It logs `undefined`."

That is `var` behavior. `let` and `const` were designed to make this bug loud.

Related: [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

## Q4. `var` In A Block

```js
if (true) {
  var status = 'ready';
}

console.log(status);
```

### Expected Output

```text
ready
```

### Why

`var` is function-scoped or global-scoped, not block-scoped. The `if` block does not create a `var` scope.

### Production Bug

Old code that uses `var` inside conditionals can accidentally leak names into the wider function scope and shadow values used later.

Related: [[03 - Scope and Variables/03 - var let const|var let const]]

## Q5. `let` In A Block

```js
if (true) {
  let status = 'ready';
}

console.log(status);
```

### Expected Output

```text
ReferenceError: status is not defined
```

### Why

`let status` is scoped to the `if` block. After the block ends, that binding is not in the outer scope.

### ReferenceError Detail

This is different from TDZ. Here no accessible binding exists. In Q3, the binding existed but was uninitialized.

Related: [[03 - Scope and Variables/01 - Scope Types|Scope Types]]

## Q6. Shadowing Inside A Function

```js
var name = 'global';

function printName() {
  console.log(name);
  var name = 'local';
  console.log(name);
}

printName();
console.log(name);
```

### Expected Output

```text
undefined
local
global
```

### Why

When `printName` is called, its creation phase creates a local `var name` initialized to `undefined`. That local binding shadows the global `name` throughout the function. The first log reads the local `undefined`, not the global value.

### Interview Line

Hoisting is per scope. A local declaration shadows outer scope from the start of that function's execution context.

Related: [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]

## Q7. `typeof` With Undeclared Vs TDZ

```js
console.log(typeof missing);

try {
  console.log(typeof hidden);
} catch (error) {
  console.log(error.name);
}

let hidden = 1;
```

### Expected Output

```text
undefined
ReferenceError
```

### Why

`typeof missing` is safe for an undeclared identifier and returns `'undefined'`. `hidden` is different: the `let hidden` binding exists in the current scope but is uninitialized. `typeof hidden` inside the TDZ throws `ReferenceError`.

### Production Bug

Feature-detection patterns using `typeof` can fail if a same-scope `let` or `const` declaration creates a TDZ binding.

Related: [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]]

## Q8. Class TDZ

```js
try {
  new User();
} catch (error) {
  console.log(error.name);
}

class User {
  constructor() {
    this.name = 'A';
  }
}
```

### Expected Output

```text
ReferenceError
```

### Why

Class declarations are block-scoped and have a TDZ like `let` and `const`. The class binding is not initialized until execution reaches the class declaration.

### Common Wrong Answer

"Function declarations work before their line, so classes should too."

Classes deliberately do not behave like function declarations here.

Related: [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]

## Q9. `var` Loop After Exit

```js
for (var i = 0; i < 3; i++) {}
console.log(i);
```

### Expected Output

```text
3
```

### Why

`var i` belongs to the enclosing function/global scope. After the loop exits, the same `i` binding remains accessible with the value that failed the condition.

### Production Bug

This is the setup for the classic closure loop bug. The timer callbacks all read the same `i` binding after it becomes `3`.

Related: [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]]

## Q10. `let` Loop After Exit

```js
for (let i = 0; i < 3; i++) {}
console.log(i);
```

### Expected Output

```text
ReferenceError: i is not defined
```

### Why

`let i` is scoped to the loop. Outside the loop, there is no accessible `i` binding.

### Follow-Up

Inside a `for (let i...)` loop, closures get a fresh per-iteration binding. That is why `let` fixes the timer loop question.

Related: [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]

## Review Loop

- [ ] I predicted the output before reading the answer.
- [ ] I named whether the issue was uninitialized binding, missing binding, or wrong value type.
- [ ] I can explain why `ReferenceError` and `TypeError` are different.
- [ ] I can rewrite one `var` question using `let` and predict the new result.

## Related Notes

- [[03 - Scope and Variables/07 - Scope Checklist|Scope Checklist]]
- [[15 - Interview Preparation/01 - Junior to Mid Questions|Junior to Mid Questions]]
- [[16 - Code Output Questions/02 - Closure Output Questions|Closure Output Questions]]
- [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]]
