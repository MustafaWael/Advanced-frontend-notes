---
tags: [javascript, scope, var-let-const]
module: "03 - Scope and Variables"
priority: must-know
status: not-started
---

# var let const

## Maturity Target

- Priority: #must-know
- Study time: 75-90 minutes
- Interview signal: you can explain scope, hoisting, TDZ, redeclaration, and `const` object mutation without mixing them together.
- Production signal: you use declarations to communicate ownership and mutation, not just to satisfy a linter.
- Dependencies: [[03 - Scope and Variables/01 - Scope Types|Scope Types]], [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]], [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]

## Source Anchors

- [MDN - var](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/var)
- [MDN - let](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let)
- [MDN - const](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const)
- [ECMAScript 2026 - Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-environment-records)
- [ECMAScript 2026 - let and const declarations](https://tc39.es/ecma262/multipage/ecmascript-language-statements-and-declarations.html#sec-let-and-const-declarations)

## 1. Concept

`var`, `let`, and `const` all create bindings, but they differ in scope, initialization timing, redeclaration behavior, and reassignment rules.

Modern production default:

1. Use `const` when the binding is not reassigned.
2. Use `let` when the binding is reassigned.
3. Avoid `var` in new application code unless you are maintaining legacy code or intentionally relying on old behavior.

This default is not about style only. It makes scope and mutation easier to reason about.

## 2. Comparison Table

| Feature | `var` | `let` | `const` |
| --- | --- | --- | --- |
| Scope | Function, global, or module | Block, function, global, or module | Block, function, global, or module |
| Initialized before execution? | Yes, to `undefined` | Binding exists but is uninitialized until declaration runs | Binding exists but is uninitialized until declaration runs |
| TDZ? | No | Yes | Yes |
| Reassign allowed? | Yes | Yes | No |
| Redeclare in same scope? | Usually yes for `var` with `var` | No | No |
| Must initialize? | No | No | Yes |
| Top-level script property on `globalThis`? | Yes for `var` in classic scripts | No | No |
| Top-level ES module property on `globalThis`? | No | No | No |

## 3. Official Mechanism

Declaration instantiation prepares bindings before statement execution:

- `var` bindings are created in the variable environment and initialized to `undefined`.
- `let` and `const` bindings are created in a declarative environment but are uninitialized until execution reaches the declaration.
- Reading an uninitialized lexical binding throws `ReferenceError`; this period is the temporal dead zone.
- `const` creates an immutable binding, not an immutable value.

```js
console.log(legacy); // undefined
var legacy = "ready";

try {
  console.log(modern);
} catch (error) {
  console.log(error.name); // "ReferenceError"
}

let modern = "ready";
```

## 4. Mental Model

Think in two separate dimensions:

- Binding mutability: can this identifier point to a different value later?
- Value mutability: can the value itself be changed?

`const` controls the first dimension only.

```js
const user = { name: "Ava" };

user.name = "Mina"; // Allowed: the object is mutable.
console.log(user.name); // "Mina"

// user = { name: "Noor" };
// TypeError: assignment to constant variable.
```

In React state, this distinction matters a lot:

```jsx
function renameUser(user, setUser) {
  user.name = "Mina"; // Bug: mutates existing object identity.
  setUser(user);      // React may not see a meaningful identity change.
}

function renameUserSafely(user, setUser) {
  // New object identity communicates a state change.
  setUser({ ...user, name: "Mina" });
}
```

## 5. `var` Deep Dive

`var` is function-scoped, not block-scoped.

```js
function getMessage(isReady) {
  if (isReady) {
    var message = "ready";
  }

  return message;
}

console.log(getMessage(true));  // "ready"
console.log(getMessage(false)); // undefined
```

`var` can also be redeclared in the same scope:

```js
function parsePrice(input) {
  var value = Number(input);
  var value = Number.isFinite(value) ? value : 0;
  return value;
}

console.log(parsePrice("12")); // 12
```

The redeclaration works, but it hides intent. With `let`, the second declaration would fail, pushing you to express the transformation more clearly.

## 6. `let` Deep Dive

`let` creates a block-scoped mutable binding.

```js
let status = "idle";

if (navigator.onLine) {
  let status = "online"; // Different binding, scoped to this block.
  console.log(status);   // "online"
}

console.log(status); // "idle"
```

Use `let` when reassignment is part of the algorithm:

```js
function findFirstEnabled(items) {
  let match = null;

  for (const item of items) {
    if (item.enabled) {
      match = item;
      break;
    }
  }

  return match;
}
```

If you never reassign, prefer `const`. It makes later accidental writes obvious.

## 7. `const` Deep Dive

`const` requires an initializer and prevents rebinding.

```js
const apiBaseUrl = "/api";

// const missing; // SyntaxError: Missing initializer in const declaration
// apiBaseUrl = "/v2"; // TypeError at runtime
```

For objects and arrays, `const` protects identity, not contents:

```js
const selectedIds = [];
selectedIds.push("a1"); // Allowed, but mutation may be unsafe in React state.

console.log(selectedIds); // ["a1"]
```

Production habit: use `const` for stable references and use immutable update patterns when framework state relies on identity.

## 8. Real Frontend Bug: Loop Handlers

Problem: a legacy DOM script attaches handlers in a loop.

```js
const buttons = ["save", "delete", "archive"];
const handlers = [];

for (var i = 0; i < buttons.length; i += 1) {
  handlers.push(function onClick() {
    return buttons[i];
  });
}

console.log(handlers[0]()); // undefined
console.log(handlers[1]()); // undefined
console.log(handlers[2]()); // undefined
```

Why: all handlers close over the same function-scoped `i`. After the loop, `i === 3`, and `buttons[3]` is `undefined`.

Fix with `let`:

```js
const buttons = ["save", "delete", "archive"];
const handlers = [];

for (let i = 0; i < buttons.length; i += 1) {
  handlers.push(function onClick() {
    return buttons[i]; // Each iteration has its own i binding.
  });
}

console.log(handlers[0]()); // "save"
console.log(handlers[1]()); // "delete"
console.log(handlers[2]()); // "archive"
```

Alternative fix with a factory when you cannot change the loop declaration:

```js
function createHandler(button) {
  return function onClick() {
    return button; // Captures the function parameter binding.
  };
}

const handlers = [];

for (var i = 0; i < buttons.length; i += 1) {
  handlers.push(createHandler(buttons[i]));
}
```

> [!tip] Tradeoff
> `let` is the clean modern fix. A factory is useful when refactoring legacy code carefully or when you want to capture a derived value, not just the index.

## 9. Script vs Module Top Level

Do not answer "top-level `var` becomes global" without context.

```js
// Classic browser script:
var scriptValue = 1;
console.log(globalThis.scriptValue); // 1
```

```js
// ES module:
var moduleValue = 1;
console.log(globalThis.moduleValue); // undefined
```

Modules also run in strict mode and have their own top-level module scope. This is a common source of wrong interview answers because older explanations assume classic scripts.

## 10. TypeScript Note

TypeScript can catch many redeclaration and reassignment mistakes, but it does not change JavaScript runtime semantics. The emitted JavaScript still follows the target output and runtime rules.

Examples:

- `const user: User` does not make `user.name` immutable.
- Downlevel builds may transform block scoping, but the source-level semantics are meant to match `let`/`const`.
- Type narrowing is not scope. It is TypeScript's static model of what values are possible at a point in code.

## 11. Production Checklist

- Use `const` unless reassignment is needed.
- Use `let` for counters, accumulators, retries, and staged reassignment.
- Avoid `var` in new code.
- Treat `const` objects in React state as still mutable and therefore still risky.
- Avoid shadowing names like `error`, `data`, `result`, and `response` across large blocks.
- In server code, check whether top-level mutable variables can leak across requests.
- In loops with callbacks, use `let` or capture a value through a factory.

## 12. Interview Answer

Short answer:

> `var` is function/global scoped and initialized to `undefined`. `let` and `const` are block scoped and cannot be read before initialization because of the TDZ. `const` prevents rebinding, not object mutation.

Deeper answer:

> During declaration instantiation, JavaScript creates bindings before code runs. `var` bindings are initialized immediately to `undefined`, so early reads work but often hide bugs. `let` and `const` bindings exist but are uninitialized until their declaration executes, so early reads throw `ReferenceError`. `let` allows reassignment; `const` requires an initializer and prevents the identifier from being rebound.

Production answer:

> I use declaration choice as design communication: `const` means stable identity, `let` means intentional reassignment, and `var` signals legacy behavior. In React, `const` does not make state immutable, so safe updates still require creating new arrays or objects.

## 13. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "`let` is not hoisted." | The binding is created before execution but is uninitialized in the TDZ. |
| "`const` freezes objects." | `const` freezes the binding, not the object. |
| "`var` is block scoped." | `var` is scoped to the containing function, module, or script global scope. |
| "Top-level `var` always becomes `window.x`." | That is classic script behavior, not ES module behavior. |
| "Use `let` by default in case the value changes." | Prefer `const` until reassignment is actually required. |

## 14. Practice

1. Predict the output:

```js
function run() {
  console.log(a);
  var a = 1;

  try {
    console.log(b);
  } catch (error) {
    console.log(error.name);
  }

  let b = 2;
}

run();
```

Expected output:

```txt
undefined
ReferenceError
```

2. Explain why this does not throw:

```js
const settings = { theme: "dark" };
settings.theme = "light";
console.log(settings.theme); // "light"
```

3. Fix a `var` loop callback using `let`.
4. Explain how top-level `var` behaves differently in scripts and modules.
5. Rewrite one function so every binding is `const` except the values that are intentionally reassigned.

## Real-World Use Cases

### Legacy script `var` collides with `window.status`

A classic-script analytics snippet stores an HTTP status in a top-level `var` and suddenly every comparison fails: the value is a string.

```html
<script>
  var status = 200;            // top-level var in a classic script = window.status
  console.log(typeof status);  // "string" — window.status coerces writes to string!
  if (status === 200) { /* never runs */ }
</script>
```

Top-level `var` in a classic script becomes a property of the global object, and `window.status` is a legacy setter that stringifies everything (`name`, `top`, `length`, `event` are similar traps). `let status` would create a normal lexical binding and behave correctly — and inside an ES module none of this happens at all (see section 9).

> [!warning]
> This bites in inline scripts, GTM custom tags, and old jQuery bundles — anywhere code still runs as a classic script rather than a module.

### Draining a paginated API with a `let` cursor

An admin "export all customers" job walks a cursor-paginated endpoint. The cursor is the textbook case for `let`: reassignment *is* the algorithm.

```ts
async function fetchAllCustomers() {
  const customers: Customer[] = []; // stable identity, mutated contents
  let cursor: string | null = null; // reassigned every page

  do {
    const page = await api.get("/customers", { params: { cursor } });
    customers.push(...page.items);
    cursor = page.nextCursor;
  } while (cursor);

  return customers;
}
```

The declaration choice documents the design: `const customers` promises the array identity never changes, `let cursor` announces staged reassignment. A reviewer can skim the bindings and know the data flow.

### Frozen config module shared across the app

Feature flags and API endpoints live in one module that every layer imports. `const` alone only locks the binding — anyone could still do `config.flags.newCheckout = true` at runtime and poison every importer.

```ts
// lib/config.ts
export const config = Object.freeze({
  apiBaseUrl: process.env.NEXT_PUBLIC_API_URL,
  flags: Object.freeze({
    newCheckout: process.env.NEXT_PUBLIC_NEW_CHECKOUT === "true"
  })
});
```

This is the binding-vs-value distinction from section 4 applied at module scale: `const` prevents rebinding, `Object.freeze` prevents mutation, and you need both because the module's bindings are shared by every importer ([[10 - Modules/05 - Live Bindings|Live Bindings]], [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]).

> [!tip]
> `Object.freeze` is shallow — freeze nested objects explicitly, or use TypeScript's `as const` for compile-time-only protection with zero runtime cost.

## Related Notes

- [[03 - Scope and Variables/01 - Scope Types|Scope Types]]
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[16 - Code Output Questions/01 - Scope and Hoisting Output Questions|Scope and Hoisting Output Questions]]
- [[01 - Roadmap|Roadmap]]
