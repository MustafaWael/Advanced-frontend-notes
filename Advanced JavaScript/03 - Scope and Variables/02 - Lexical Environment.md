---
tags: [javascript, scope, lexical-environment]
module: "03 - Scope and Variables"
priority: must-know
status: not-started
---

# Lexical Environment

## Maturity Target

- Priority: #must-know
- Study time: 90 minutes
- Interview signal: you can explain closures, hoisting, TDZ, and `this` lookup using one shared mechanism.
- Production signal: you can trace which render, function call, module, or block owns the value a callback reads later.
- Dependencies: [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]], [[03 - Scope and Variables/01 - Scope Types|Scope Types]]

## Source Anchors

- [ECMAScript 2026 - Execution contexts](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-execution-contexts)
- [ECMAScript 2026 - Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-environment-records)
- [ECMAScript 2026 - GetIdentifierReference](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-getidentifierreference)
- [MDN - Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [React - useEffect dependencies](https://react.dev/reference/react/useEffect)

## 1. Concept

A lexical environment is the runtime/spec structure that lets JavaScript resolve identifiers according to source-code nesting. In the current ECMAScript spec, an execution context has a `LexicalEnvironment` component, and that component points at an Environment Record used for identifier resolution.

You can think of it as:

- Environment Record: the table of bindings for a scope.
- Outer environment: the link to the next scope outside it.
- Lexical environment chain: the chain JavaScript walks when resolving a name.

This is the mechanism behind ordinary scope, closures, TDZ, module imports, and why a function remembers where it was created.

## 2. Why It Matters

Many developers know the surface rule but cannot debug the real bug:

- "The callback has stale state."
- "The loop variable is wrong."
- "The import is undefined or in TDZ."
- "This variable shadows another variable."

The mature question is: which Environment Record is this identifier resolving against at the moment it runs?

If you can answer that, the bug becomes mechanical instead of mysterious.

## 3. Official Mechanism

At runtime, code is evaluated inside an execution context. For ECMAScript code, the execution context includes:

| Component | Job |
| --- | --- |
| `LexicalEnvironment` | Environment Record used to resolve identifier references. |
| `VariableEnvironment` | Environment Record that holds `var` bindings for that context. |
| `PrivateEnvironment` | Private names for class elements when relevant. |

Identifier resolution is recursive:

1. Start with the current `LexicalEnvironment`.
2. Ask the current Environment Record whether it has the binding.
3. If yes, return a Reference Record for that binding.
4. If no, follow the internal outer-environment link.
5. If the chain reaches `null`, the reference is unresolvable and a read usually throws `ReferenceError`.

Pseudocode version:

```txt
resolve(name, env):
  if env is null:
    return unresolvable

  if env.hasBinding(name):
    return reference to env.name

  return resolve(name, env.outer)
```

## 4. Environment Record Types

| Record type | Used for | Frontend consequence |
| --- | --- | --- |
| Declarative Environment Record | `let`, `const`, `class`, function/block/catch bindings | The normal "scope table" for lexical bindings. |
| Function Environment Record | A function invocation | Each call can have separate parameter/local bindings; closures can retain them. |
| Module Environment Record | ES module top-level declarations and imports | Imports are live read-only bindings; module state can be shared. |
| Global Environment Record | Script global code and built-ins | `var`/function globals can interact with global object properties. |
| Object Environment Record | `with` and global object parts | Dynamic name lookup; avoid `with` in app code. |

The key nuance: these are spec mechanisms, not objects you can inspect directly from JavaScript.

## 5. Mental Model

Use "binding boxes" instead of "captured values."

```js
function createReader() {
  let value = 0; // One binding box named value.

  return {
    read() {
      return value; // Reads the current contents of the same binding box.
    },
    write(nextValue) {
      value = nextValue; // Updates that binding box.
    }
  };
}

const reader = createReader();
console.log(reader.read()); // 0
reader.write(42);
console.log(reader.read()); // 42
```

The returned methods do not copy `value`. They keep access to the environment where `value` lives.

## 6. Lookup Example

```js
const source = "module";

function outer() {
  const source = "outer";

  function inner() {
    const kind = "inner";
    return `${kind}:${source}`;
  }

  return inner;
}

const fn = outer();
console.log(fn()); // "inner:outer"
```

Step-by-step:

1. `inner` looks for `kind` in its own function environment and finds `"inner"`.
2. `inner` looks for `source`; it is not local to `inner`.
3. The outer link points to the environment from the `outer()` call.
4. That environment has `source = "outer"`.
5. The module-level `source = "module"` is not used because lookup already found a closer binding.

## 7. Real Frontend Example: React Render Environments

> [!example] Render environments traced
> Every React render calls the component function again. That creates a new set of local bindings for that render.

```jsx
function SearchBox({ initialQuery }) {
  const [query, setQuery] = useState(initialQuery);

  function logQuery() {
    // This function reads query from the render where logQuery was created.
    console.log(query);
  }

  return (
    <input
      value={query}
      onChange={(event) => {
        setQuery(event.target.value);
        logQuery(); // Logs the previous render's query, not the value being typed.
      }}
    />
  );
}
```

Why the bug happens:

- `setQuery` schedules a state update; it does not change the current render's `query` binding.
- `logQuery` reads from the current render's lexical environment.
- The next render will have a different `query` binding.

Better pattern:

```jsx
function SearchBox({ initialQuery }) {
  const [query, setQuery] = useState(initialQuery);

  return (
    <input
      value={query}
      onChange={(event) => {
        const nextQuery = event.target.value;
        setQuery(nextQuery);
        console.log(nextQuery); // Reads the event-owned value directly.
      }}
    />
  );
}
```

## 8. Bug -> Fix -> Tradeoff

Problem: a callback needs the latest state, but it was created once.

```jsx
function Timer() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setCount(count + 1); // Always reads count from the first render.
    }, 1000);

    return () => clearInterval(id);
  }, []); // The empty dependency list freezes the first callback.
}
```

> [!warning] Interval stuck at one
> Failure mode: the interval repeatedly sets `count` to `1`.

Fix for "derive next state from previous state":

```jsx
function Timer() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      // React provides the latest committed value to the updater.
      setCount((currentCount) => currentCount + 1);
    }, 1000);

    return () => clearInterval(id);
  }, []);
}
```

> [!tip] Updater vs dependency choice
> Tradeoff: a functional updater is ideal when the next value depends only on previous state. If the effect truly needs a changing prop or state value for synchronization, include it in the dependency list and handle cleanup.

## 9. Debugging Checklist

- Identify where the function was created.
- Identify when the function is executed.
- List every external binding the function reads.
- For each binding, ask whether it is local, outer, module, global, imported, or React render-owned.
- In React, treat props, state, and component-local functions as reactive values.
- If the code uses `[]` dependencies, prove that the callback does not need changing render values.
- If module scope is involved, ask whether the value is safe to share.

## 10. Interview Answer

Short answer:

> A lexical environment is the structure JavaScript uses to store bindings for a scope and link to outer scopes. Identifier lookup walks that chain.

Deeper answer:

> In the spec, an execution context has a `LexicalEnvironment` that points to an Environment Record. Environment Records store bindings and have an internal outer-environment link. When code reads a variable, `ResolveBinding` starts from the current lexical environment and uses `GetIdentifierReference` to search outward. Closures work because function objects remember the environment where they were created, so later calls can still resolve those bindings.

Production answer:

> In React, each render creates new bindings. If an interval, event listener, or memoized callback was created during an old render, it may keep reading old bindings. Fixing that means choosing the correct ownership model: dependencies for synchronization, functional updates for previous state, refs for intentionally mutable instance-like data, or passing the value as an argument.

## 11. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "A closure stores a copy of every value." | It preserves access to bindings in an outer Environment Record. |
| "The scope chain changes depending on who calls the function." | The lexical outer chain is decided by where the function is created. |
| "A React state variable changes immediately after `setState`." | The current render's binding stays the same; the next render gets a new binding. |
| "The spec objects are real JavaScript objects." | They are specification mechanisms, not inspectable runtime values. |
| "A dependency array is an optimization hint." | It describes which reactive bindings the effect reads. |

## 12. Practice

1. Draw the environment chain for this code:

```js
const a = "A";

function one() {
  const b = "B";
  return function two() {
    const c = "C";
    return a + b + c;
  };
}

console.log(one()()); // "ABC"
```

2. Explain why `b` is still available after `one()` has returned.
3. In a React component, explain why `console.log(query)` after `setQuery(next)` logs the old value.
4. Rewrite an effect with stale state using a functional updater.
5. Explain the difference between a property lookup like `user.name` and an identifier lookup like `user`.

## Real-World Use Cases

### Module scope as an app-wide singleton

A Next.js app creates one API client and every route imports it. This works because the module's top-level bindings live in a single Module Environment Record — every importer resolves the same binding.

```ts
// lib/apiClient.ts — evaluated once per process
const client = axios.create({ baseURL: process.env.API_URL });
client.interceptors.response.use(undefined, refreshTokenAndRetry);

export { client };
```

Imports are live references into the exporting module's environment ([[10 - Modules/05 - Live Bindings|Live Bindings]]), so "singleton" here is just identifier resolution landing in one shared Environment Record.

> [!warning]
> On the server this environment outlives a single request. A module-level `let currentUser` is one Environment Record shared by every concurrent request — request-owned data must live in function scope, not module scope.

### Shadowing swallows the outer binding in a long handler

A checkout handler destructures `data` from a response, then a nested refetch introduces a second `data`. Both compile; the inner one silently wins for the rest of the block.

```ts
async function submitOrder(form: OrderForm) {
  const { data } = await api.post("/orders", form);

  if (data.requiresVerification) {
    const { data } = await api.post("/orders/verify", { id: data.id });
    // ReferenceError: the data.id in the initializer resolves to the INNER
    // binding, which is still uninitialized (TDZ) — not to the outer data.
    showBanner(data.message);
  }

  return data.orderId; // outer data again — easy to misread
}
```

Lookup stops at the **nearest** Environment Record that has the binding — it never falls back outward just because the nearest binding is uninitialized. Inside the `if` block every `data` resolves to the inner binding, so the read in its own initializer throws in the TDZ (see [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]).

> [!tip]
> Rename at the destructuring site (`const { data: verification }`) so each name maps to exactly one binding. The vault checklist in [[03 - Scope and Variables/03 - var let const|var let const]] flags `data`/`error`/`result` as the usual suspects.

### `switch` cases share one block environment

A reducer declares `let next` in two cases and the build fails with a redeclaration error, even though the cases look independent.

```ts
switch (action.type) {
  case "add": {
    const next = [...state.items, action.item]; // braces = own environment
    return { ...state, items: next };
  }
  case "remove": {
    const next = state.items.filter((item) => item.id !== action.id);
    return { ...state, items: next };
  }
}
```

The entire `switch` body is **one block scope** — one Declarative Environment Record — so two bare `const next` declarations collide, and a `case` that runs before another case's declaration can even hit TDZ. Braces per case give each its own record.

## Related Notes

- [[03 - Scope and Variables/01 - Scope Types|Scope Types]]
- [[03 - Scope and Variables/03 - var let const|var let const]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[01 - Roadmap|Roadmap]]
