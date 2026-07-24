---
tags: [javascript, runtime, execution-context]
module: "02 - JavaScript Runtime Foundations"
priority: must-know
status: not-started
---

# Execution Context

## Maturity Target

- Priority: #must-know
- Study time: 50-70 minutes
- Outcome: explain how JavaScript tracks currently running code, scope, `this`, and evaluation state.

## Source Anchors

- [ECMAScript specification](https://tc39.es/ecma262/)
- [MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)
- [MDN JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

## 1. Simple Explanation

An execution context is the specification model for a piece of code currently being evaluated. It tracks the code's lexical environment, variable environment, `this` binding, realm, and where evaluation should continue.

In simpler words: every time JavaScript starts global code, evaluates a module, or calls a function, the engine needs a record of "what is running and what names mean here."

## 2. Why It Matters

Execution context is the base layer behind:

- Hoisting and TDZ.
- Scope chains and closures.
- `this` binding.
- Stack traces.
- Async/await suspension and resumption.
- Modules and top-level evaluation.
- React render snapshots and stale closures.

If you understand execution contexts, many advanced topics stop feeling separate.

## 3. Accurate Mechanism

At a high level, an execution context includes:

| Part | Purpose |
| --- | --- |
| Lexical environment | Stores lexical bindings such as `let`, `const`, class declarations, and outer-scope links. |
| Variable environment | Tracks `var` and function declaration behavior in many execution contexts. |
| This binding | The `this` value for ordinary function, global, or module evaluation where applicable. |
| Realm | The set of intrinsics and global object associated with the code. |
| Evaluation state | Where execution is currently paused or running, especially relevant for generators and async functions. |

The execution context stack tracks active execution contexts. The currently running context is on top.

### Block Scoping under Lexical vs. Variable Environments
The separation between `LexicalEnvironment` and `VariableEnvironment` is what enables ES6 block scoping (`let` and `const` inside `{...}`) without breaking legacy function-scoped `var` variables.

This is ECMAScript specification behavior, not an engine detail. When evaluation enters a block (such as an `if` block or `for` loop), the spec says:
1. A new **declarative Environment Record** is created to hold the block's `let`, `const`, and class declarations.
2. The outer reference of this new record points to the previous `LexicalEnvironment`.
3. The execution context's `LexicalEnvironment` pointer is updated to point to this new record, creating a nested scope.
4. The `VariableEnvironment` pointer **does not change**; it continues to point to the function-level or global-level record. This is why `var` declarations escape block boundaries—they are written directly to the `VariableEnvironment`'s record.
5. When the block exits, the context's `LexicalEnvironment` pointer is restored to its original value.

> [!tip] Spec model vs engine storage — a senior interview signal
> The spec describes environment records as if every block allocates one; engines do not implement it that literally. V8 only heap-allocates a scope (a "context object") when a closure actually captures its bindings. Uncaptured `let`/`const` live in stack slots or registers and vanish when the frame pops. Being able to say "the spec defines the observable semantics, the engine chooses the storage strategy" is exactly the layering discipline that separates a memorized answer from a mature one.

## 4. Creation vs Execution

Do not explain hoisting as "JavaScript moves code." A better model is two broad phases:

1. Preparation: create bindings and environments needed for the code.
2. Execution: run statements in order and assign values as the program evaluates.

```js
console.log(a); // undefined
var a = 1;

// console.log(b); // ReferenceError if uncommented
let b = 2;
```

`var a` has a binding initialized to `undefined` before the line executes. `let b` also has a binding, but it is uninitialized until its declaration is evaluated, so early access is in the temporal dead zone.

## 5. Context Types You Should Recognize

| Context | What to remember |
| --- | --- |
| Global script context | Top-level script code has global environment behavior; browser script `var` can become a global object property. |
| Module context | ES modules are strict by default and have module environment bindings. Top-level `this` is `undefined`. |
| Function context | Ordinary function calls create a context with parameters, local bindings, and a `this` binding determined by the call form. |
| Async function continuation | `await` suspends the function and resumes the continuation later through promise scheduling. |
| Generator context | Generators preserve evaluation state between `yield` points. |

The goal is not to memorize every spec field. The goal is to know which record answers which question: "what names exist?", "what does `this` mean?", "where are we resuming?", and "which realm's built-ins are used?"

## 6. Real Frontend Example

```tsx
function SearchBox({ initialQuery }: { initialQuery: string }) {
  const [query, setQuery] = React.useState(initialQuery);

  function handleSubmit() {
    // This function was created during a particular render.
    // It closes over the bindings from that render's execution.
    submitSearch(query);
  }

  return (
    <form onSubmit={event => {
      event.preventDefault();
      handleSubmit();
    }}>
      <input value={query} onChange={event => setQuery(event.target.value)} />
    </form>
  );
}
```

Every render calls `SearchBox` again. Each call creates fresh local bindings. A callback created during one render sees the bindings from that render. This is normal JavaScript; React makes the lifetime visible.

## 7. Async Context Example

```ts
async function loadUser(id: string) {
  console.log('before fetch');

  // The async function does not block the JavaScript thread here.
  // Its continuation is resumed later through promise scheduling.
  const response = await fetch(`/api/users/${id}`);

  console.log('after fetch');
  return response.json();
}
```

`await` suspends the async function's continuation. The call stack can clear, other work can run, and the continuation resumes later when the awaited promise settles.

## 8. `this` Binding Edge Case

Execution context also explains class callback bugs:

```tsx
class SaveButton extends React.Component {
  state = { saving: false };

  save() {
    // In strict mode, calling save as a plain function gives this === undefined.
    this.setState({ saving: true });
  }

  render() {
    return <button onClick={this.save}>Save</button>;
  }
}
```

When React later calls the event handler, it does not call it as `instance.save()`. The receiver is lost. Fix it with a bound method, a class field arrow, or a function component pattern.

```tsx
class SaveButton extends React.Component {
  state = { saving: false };

  save = () => {
    this.setState({ saving: true });
  };

  render() {
    return <button onClick={this.save}>Save</button>;
  }
}
```

## Real-World Use Cases

### Classic interview trap: `setTimeout` in a `for` loop with `var`

The one interviewers reach for when they want to see if you actually understand environments, not just the word "hoisting."

```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// Logs: 3, 3, 3 — not 0, 1, 2
```

Tick-by-tick:

1. `var i` is written to the **VariableEnvironment** of the enclosing function/global context — the loop block gets no binding of its own, so there is exactly one `i`.
2. Each arrow function closes over that single environment record, not over a value.
3. The loop is synchronous; the current execution context runs to completion, incrementing `i` to `3`, before any timer task can run.
4. The three timer callbacks finally execute, each looking up `i` in the same shared environment: `3`.

With `let`, the spec creates a **fresh declarative Environment Record per iteration** (the LexicalEnvironment pointer swaps each pass), so each closure captures its own `i` and the output is `0, 1, 2`.

See [[03 - Scope and Variables/03 - var let const|var let const]], [[03 - Scope and Variables/05 - Closures|Closures]], and [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]].

### Module-level state on the Next.js server

A module is evaluated once per realm, in its own module context. On the server, that means module-level bindings outlive a single request.

```ts
// lib/user-cache.ts — imported by a route handler
const currentUser = { profile: null as Profile | null };

export async function loadProfile(session: Session) {
  if (currentUser.profile) return currentUser.profile; // whose profile?
  currentUser.profile = await db.profiles.find(session.userId);
  return currentUser.profile;
}
```

In the browser each tab gets its own realm, so this pattern feels safe. On a Node server the module context is created once and shared across every request — user A's profile can be served to user B. This works/fails because module evaluation is a single execution context whose environment stays reachable for the life of the process.

> [!warning]
> Module scope is per-realm, not per-request. Keep request-scoped data in function parameters or per-request stores, never in module-level bindings on the server.

See [[10 - Modules/01 - ES Modules|ES Modules]] and [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]].

### `instanceof Array` failing across an iframe

An embedded widget (payment iframe, rich-text editor, legacy portal) posts an array to the parent page, and a defensive check silently misroutes it.

```js
// Parent page receiving data built inside an iframe
const items = iframe.contentWindow.getSelectedItems();

if (items instanceof Array) {   // false!
  renderList(items);
} else {
  renderSingle(items);          // wrong branch runs
}
```

Each window/iframe is a separate **realm** with its own intrinsics — the iframe's `Array` constructor is a different object than the parent's, so the prototype chain check fails. The execution context's realm field is exactly what determines which `Array` a piece of code sees. `Array.isArray(items)` works across realms because it checks the internal slot, not identity.

## 9. Interview Answer

**Short version:** An execution context is the spec model for currently running code. It holds the scope information, `this` value, realm, and evaluation state needed to execute that code.

**Deeper version:** JavaScript uses execution contexts for global code, modules, function calls, eval, generators, and async functions. Active contexts are managed on the execution context stack. Each context contains environment information for identifier lookup, a `this` binding when applicable, and evaluation state. This model explains hoisting, closures, `this`, stack traces, and why callbacks can read values from the render or function call where they were created.

## 10. Common Mistakes

> [!warning] An async function doesn't hold the call stack while it waits
> When an `await` suspends, its execution context is set aside and the call stack unwinds — the thread is free to run other work. The continuation resumes later as a microtask. Picturing `await` as "blocking the stack" leads to wrong reasoning about ordering and freezes.

- Saying execution context is just "memory plus code." It is a precise runtime record with environment and evaluation information.
- Saying hoisting physically moves declarations.
- Forgetting that closures can keep lexical environments alive after a call has returned.
- Ignoring modules. Module evaluation also has its own environment behavior.
- Treating React stale closures as a React-only concept instead of ordinary JavaScript closure lifetime.
- Assuming an async function keeps occupying the call stack while it waits for I/O.

## 11. Practice

1. Draw the execution context stack for three nested function calls.
2. Explain why `var` and `let` behave differently before their declaration line.
3. Explain what a callback created during render closes over.
4. What happens to an async function when it hits `await`?
5. Use "execution context" in a 2-minute explanation of closures.

<details>
<summary>Show answer</summary>
<ol>
<li>For <code>a()</code> calling <code>b()</code> calling <code>c()</code>, the stack is global/script context, then <code>a</code>, then <code>b</code>, then <code>c</code>. When <code>c</code> returns, <code>c</code> pops; then <code>b</code>; then <code>a</code>.</li>
<li>During preparation, a <code>var</code> binding is created and initialized to <code>undefined</code>. A <code>let</code> binding is created too, but remains uninitialized until its declaration executes. Reading it early is a TDZ <code>ReferenceError</code>.</li>
<li>It closes over the lexical environment from the render/function call that created it. In React, each render is a new function call with new local bindings, so an old callback can keep reading old render values.</li>
<li>The async function's continuation is suspended. The call stack can clear and other work can run. When the awaited promise settles, the continuation is scheduled through promise-job/microtask behavior.</li>
<li>A strong explanation: "A closure works because a function object keeps a reference to the lexical environment from the execution context where it was created. Even after that context is no longer on the call stack, the environment can stay reachable through the function."</li>
</ol>
</details>

## Related Notes

- [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
