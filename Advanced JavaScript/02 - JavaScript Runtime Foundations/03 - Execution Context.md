---
tags:
  - javascript
  - runtime
  - execution-context
module: 02 - JavaScript Runtime Foundations
priority: must-know
status: learning
---
# Execution Context

## Maturity Target

- Priority: #must-know
- Study time: 80-100 minutes
- Outcome: explain how JavaScript tracks currently running code, scope, `this`, and evaluation state.
- Interview signal: answer "what is an execution context?" in two minutes with one example, and use it to explain hoisting, closures, `this` and `await`.
- Production signal: debug stale closures, a lost `this` in callbacks, and module-level state leaking between requests by asking which table of names and which context the code is using.
- Dependencies: [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]

## Source Anchors

- [ECMAScript specification: Execution Contexts (§9.4)](https://tc39.es/ecma262/#sec-execution-contexts)
- [ECMAScript specification: Environment Records (§9.1)](https://tc39.es/ecma262/#sec-environment-records)
- [MDN JavaScript execution model](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model)
- [MDN JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

> [!tip] How to read this note
> The spine is §1 (four questions every running piece of code must answer) and §3 (the part of the record that answers each one). §4 to §8 each take one question deeper. Do the trace in §4 with a pen. The V8 callout in §3 is optional depth.

## 1. Simple Explanation

**Where this fits.** [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]] said the engine "manages execution contexts". This note opens that box, and [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]] then shows what happens when contexts pile up.

You've probably met this React bug: an interval created in `useEffect(…, [])` keeps logging the first render's value. Nothing is broken. The callback still reads names from the call that created it, and this note explains the bookkeeping behind that.

Here is the program this note keeps coming back to. Predict what it logs.

```js
// cart.mjs — an ES module, so strict mode. Run: node cart.mjs
const cart = {
  label: 'Cart',
  summarize(prices) {
    var total = 0;
    for (let i = 0; i < prices.length; i++) {
      total += prices[i];
    }
    return () => `${this.label}: ${total}`;
  },
};

const report = cart.summarize([5, 10]);
console.log(report());
```

It logs `Cart: 15`, even though `summarize` has already returned when `report()` runs. How the arrow still finds `total` and `this` is what this note explains.

To run any line of `summarize`, JavaScript needs four answers:

1. **Names**: what names exist here? Which `prices`, which `total`, which `i`?
2. **`this`**: what does `this` mean right now?
3. **Built-ins**: which realm's built-ins are used? Which `Array`, which global object?
4. **Where we are**: what is running now, and where do we return or resume when it's done?

Every time JavaScript starts global code, evaluates a module, or calls a function, it needs a record of "what is running and what names mean here." That record holds the four answers, or points to where they're kept, and the records are stacked so JavaScript always knows where to go back. The spec calls the record an **execution context**: "a specification device that is used to track the runtime evaluation of code." *(Teaching model; the quote is the spec's own definition, §9.4.)*

You don't need every spec field, only which part answers which question. §3 maps them, and §4 to §8 go deeper one question at a time.

### Words you need first

Five terms the note leans on, each described by its job here:

- **Binding**: *answers "what does this name refer to?"* A name tied to a value: `var total = 0` creates a binding named `total`. A binding can exist before it has a value (§4).
- **Table of names** (the spec's *Environment Record*): *answers "which names exist in this scope?"* One scope's bindings, plus a link to the table of the scope around it. Lookup checks the current table, then follows the links outward, and that chain is the scope chain. → [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- **Realm**: *answers "which `Array` and which global object does this code use?"* One full set of built-ins (`Array`, `Object`, `Promise`…) plus a global object; each window, iframe and worker has its own. So an array built inside a same-origin iframe fails `instanceof Array` in the parent page (§3 shows it). → [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]]
- **Call stack**: *answers "what is running now, and what runs next?"* The pile of execution contexts: a call pushes one on top, a return or a throw pops it, and only the top one runs. → [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]
- **Continuation**: *answers "what's left to do in a paused function?"* The rest of an async function after an `await`. Once the awaited promise settles, it runs as a microtask, a small job that runs as soon as the current code has finished. → [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

**Checkpoint.** Name the four questions without looking. Which one does `this.label` depend on, and which one does `total`?

## 2. Why It Matters

Each of these everyday behaviors comes out of one of the four questions:

- **Hoisting and TDZ (temporal dead zone)**: a scope's names are created before its first line runs, `var` as `undefined` and `let`/`const` locked until their line. So an early `var` read gives `undefined`, and an early `let` read throws `ReferenceError` (§4). → [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- **Scope chains and closures**: lookup walks outward through linked tables, and a function keeps the table it was created in. So `report()` still reads `total` after `summarize` has returned (§4). → [[03 - Scope and Variables/05 - Closures|Closures]]
- **`this` binding**: a regular function's `this` comes from how it's called, and an arrow has none, so its `this` is found by walking outward. So a class method passed as a callback throws `TypeError` once it touches `this` (§8). → [[05 - this Binding/01 - What is this|What is this]]
- **Stack traces**: the engine prints the stack of contexts as it was when the error object was created. So a trace lists the calls that led to the error, newest first. (V8 keeps 10 frames by default; *named implementation, V8 12.4*.) → [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]]
- **Async/await suspension and resumption**: at `await`, the function's context leaves the stack with its place saved, and it comes back when the promise settles. So clicks and timers can run while it waits (§7). → [[08 - Async JavaScript/04 - Async Await|Async Await]]
- **Modules and top-level evaluation**: a module runs once, in its own context with its own table of names. So its top-level declarations don't land on `window`, its top-level `this` is `undefined`, and its state is shared by every importer (Use Case 2). → [[10 - Modules/01 - ES Modules|ES Modules]]
- **React render snapshots and stale closures**: each render is a new call with a fresh table, and a callback keeps the table of the render that made it. So an interval created in `useEffect(…, [])` keeps logging old state (§6). → [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

## 3. Accurate Mechanism

Here is the part of the record that answers each question. Labels follow the vault: *specification* is what every engine must do, *named implementation* is what one engine does, and *teaching model* is a simplification.

The parts, one per question *(specification, ECMAScript §9.4, in plain words)*:

| Question | Part | What it does |
| --- | --- | --- |
| Names | **LexicalEnvironment** | Points to the table where name lookup starts right now (the current block's `let`, `const` and `class`), linked outward. |
| Names (`var`) | **VariableEnvironment** | Points to the function-level (or script-level) table that holds `var`s. It stays put when you enter a block. |
| `this` | *no separate part* | Stored in tables of names: a regular function's table holds its `this`, set by the call. Lookup walks outward to find it; arrow functions' tables have none. |
| Built-ins | **Realm** | Which built-ins (`Array`, `Object`…) and which global object the code uses. |
| Where we are | **Code evaluation state** | Where execution is, so a generator or async function can pause and resume at the same spot. |

The spec lists a few more parts (Function, ScriptOrModule, PrivateEnvironment, and Generator) that this note doesn't need. Older articles show `this` as its own part, ThisBinding: that's the ES5 layout. Since ES2015, `this` lives in the tables of names, which is how arrow functions borrow it (§8).

**Realm in three lines** *(Node, ES module; `vm.runInNewContext` runs code in a fresh realm)*:

```js
import vm from 'node:vm';
const foreign = vm.runInNewContext('[1, 2]');   // built by the other realm's Array
console.log(foreign instanceof Array);          // false
console.log(Array.isArray(foreign));            // true
```

What this shows: the realm decides which built-ins a check compares against. Use Case 3 is the browser version.

The execution context stack tracks active execution contexts. The currently running context is on top. It's the call stack under its spec name, and [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]] covers it in detail.

### Block Scoping under Lexical vs. Variable Environments
The separation between `LexicalEnvironment` and `VariableEnvironment` is what lets ES6 block scoping (`let` and `const` inside `{...}`) work without breaking legacy function-scoped `var` variables. The split itself is older: ES5 already had both parts, for `with` and `catch`, and ES2015 reused it for blocks.

This is ECMAScript specification behavior, not an engine detail. When evaluation enters a block (the `{ … }` of an `if`, a loop body, or a bare block), the spec says:
1. A new **declarative Environment Record** is created to hold the block's `let`, `const`, and class declarations.
2. The outer reference of this new record points to the previous `LexicalEnvironment`.
3. The execution context's `LexicalEnvironment` pointer is updated to point to this new record, creating a nested scope.
4. The `VariableEnvironment` pointer **does not change**; it continues to point to the function-level or global-level record. This is why `var` declarations escape block boundaries: their bindings were created in that function-level record when the function started, and a `var x = 1` inside the block writes to that same binding by walking outward from the block's record.
5. When the block exits, the context's `LexicalEnvironment` pointer is restored to its original value.

One change, `var` → `let`, decides which table a name lands in *(ES module. Run: node block.mjs)*:

```js
function demo() {
  {
    var a = 'var';
    let b = 'let';
  }
  console.log(a);          // "var": lives in demo's table
  console.log(typeof b);   // "undefined": b lived in the block's table
}
demo();
```

What this shows: a block gets a new table of names, not a new execution context. Nothing is pushed onto the call stack; the context points its LexicalEnvironment at the block's table until the block ends.

> [!tip] Spec model vs engine storage *(implementation layer: V8 12.4 in Node 22, captured with `node --print-bytecode`)*
> The spec describes environment records as if every block allocates one; engines do not implement it that literally. V8 heap-allocates a "context object" for a variable only if some inner function in the source refers to it, and it decides this at compile time, not when a closure is created. Other locals live in the interpreter's register file, inside the stack frame, and vanish when the frame pops. The exceptions are top-level `let`/`const` in a classic script and functions that call `eval` directly. The takeaway: "the spec defines the observable semantics, the engine chooses the storage strategy."

### Don't mix these up

- **Execution context stack = call stack.** These are the spec name and the everyday name for one thing; MDN says an execution context is "also known generally as a stack frame".
- **Execution context ≠ V8's "contexts".** V8 uses "context" for the heap objects that hold captured variables, and for `v8::Context`, which is roughly a realm (Node's `vm.createContext` makes one). *(Named implementation, V8 12.4.)*
- **`[[Environment]]` ≠ LexicalEnvironment.** A function's `[[Environment]]` is the table it keeps from where it was created. The context's LexicalEnvironment is where lookup starts right now.
- **Binding ≠ `this` binding.** A binding is any name tied to a value. The `this` binding is the value a regular function's table holds for `this`.
- **A closure keeps a table, not a context.** `summarize`'s context left the stack when it returned; what `report` keeps is its table of names.

## 4. Creation vs Execution

The names question, in time order: when do the names in a table appear, and when do they get their values?

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

*(Specification order for a function call: the new context is created and pushed onto the stack first, then `this` is bound, then the names are set up, then the first line runs.)*

### Trace it: the running example, moment by moment

Predict first: when `summarize` starts, what is `total`? Then check the table.

| Moment | Call stack | `total` | `this` inside the arrow |
| --- | --- | --- | --- |
| `summarize` starts, before its first line | module → summarize | already in summarize's table, set to `undefined` | — |
| the loop runs | module → summarize | `0`, then `5`, then `15`; each pass's `i` sits in its own table | — |
| `summarize` returns | module | its context is popped, but its table survives because the arrow links to it | — |
| `report()` runs | module → arrow | found by walking out from the arrow's table to summarize's: `15` | the arrow's table has none, so the walk reaches summarize's `this`: `cart` |

What this shows: names exist before the first line runs (that's hoisting), one call leaves behind a table that a later call still reads (that's the closure), and the arrow finds `this` by the same outward walk it uses for names.

**Checkpoint.** Which row is hoisting? Which row is where the closure starts to matter?

Every context so far came from a function call. Where else do contexts come from?

## 5. Context Types You Should Recognize

Different kinds of code get different contexts, and the four answers change with them:

| Context | What to remember |
| --- | --- |
| Global script context | Top-level script code uses the global table of names; in a browser script, a top-level `var` becomes a property of `window`. |
| Module context | ES modules are always strict and get their own module table of names, so their top-level declarations don't become properties of `window`. Top-level `this` is `undefined`. |
| Function context | Ordinary function calls create a context with parameters, local bindings, and a `this` binding determined by the call form. Arrow functions get no `this` of their own (§8). |
| Async function continuation | `await` takes the function's context off the stack; the rest of the function (its continuation) resumes later as a microtask, once the awaited promise settles. |
| Generator context | Generators preserve evaluation state between `yield` points: each `yield` takes the generator's context off the stack, and each `next()` puts it back. |

A generator makes the pause visible *(ES module. Run: node gen.mjs)*:

```js
function* steps() {
  console.log('A');
  yield;              // the generator's context leaves the stack here
  console.log('B');   // ...and resumes here on the next .next()
}
const it = steps();
it.next();            // logs A
console.log('between');
it.next();            // logs B
```

What this shows: where we are is saved with the context. `steps` stops at `yield`, other code runs, and `.next()` resumes it at that exact spot.

## 6. Real Frontend Example

The names question in React: each render is a new function call with a new table of names.

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

What this shows: `handleSubmit` is the running example's arrow in React clothing. It keeps its render's table, the way `report` kept `summarize`'s. If an old `handleSubmit` ran after a newer render (from an interval, say), it would read old values: a stale closure. → [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

## 7. Async Context Example

The where-we-are question, when a function pauses:

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

What this shows: the continuation is everything from `console.log('after fetch')` on. At `await`, `loadUser`'s context leaves the stack with its place saved and its table of names (`id`, later `response`). When `fetch` settles, a microtask puts it back. → [[08 - Async JavaScript/04 - Async Await|Async Await]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## 8. `this` Binding Edge Case

The `this` question, in a React class component:

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

When React later calls the event handler, it does not call it as `instance.save()`. The receiver (the object before the dot) is lost. Fix it with a bound method, a class field arrow, or a function component pattern.

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

What this shows: the single change is `save() {…}` → `save = () => {…}`. The arrow has no `this` of its own, so lookup walks outward to the class field's `this`, which is the instance, because field initializers run with `this` set to it. The cost: each instance gets its own copy of `save` instead of sharing one method on the prototype, and a bound method costs the same.

The running example has the same lever. Make only `summarize`'s arrow a regular function *(ES module)*:

```js
return function () { return `${this.label}: ${total}`; };
// report() → TypeError: Cannot read properties of undefined (reading 'label')
```

`report()` is a plain call, so in strict code the regular function's `this` is `undefined`: the same `TypeError` as `SaveButton`, because class bodies are strict too. → [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]]

**Checkpoint.** In one sentence that uses the word "outward": why does the class-field arrow fix `SaveButton`?

## Real-World Use Cases

### Classic interview trap: `setTimeout` in a `for` loop with `var`

Three ideas meet in this snippet: which table holds a `var` and what a closure keeps (names), and when timer callbacks run (where we are).

```js
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 0);
}
// Logs: 3, 3, 3 — not 0, 1, 2
```

Tick-by-tick:

1. `var i` is created in the table the **VariableEnvironment** points to (the enclosing function's or the script's), and the loop block gets no binding of its own, so there is exactly one `i`. → [[03 - Scope and Variables/03 - var let const|var let const]]
2. Each arrow function keeps a link to the table it was created in, and all three links lead to the same `i` binding: a binding, not a copied value. → [[03 - Scope and Variables/05 - Closures|Closures]]
3. The loop is synchronous: the whole script runs to completion and the call stack empties, with `i` now `3`, before any timer task can run. → [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]
4. The three timer callbacks finally execute, each looking up `i` in the same shared environment: `3`.

With `let`, the spec creates a **fresh declarative Environment Record per iteration** (the LexicalEnvironment pointer swaps each pass), so each closure captures its own `i` and the output is `0, 1, 2`.

What this shows: the `var` → `let` lever from §3 again, with timers: one shared binding versus one per pass.

See [[03 - Scope and Variables/03 - var let const|var let const]], [[03 - Scope and Variables/05 - Closures|Closures]], and [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]].

### Module-level state on the Next.js server

A module is evaluated once, in its own module context, and the loaded module is then reused: in a browser, once per realm; on a server, for as long as that process keeps it loaded. On the server, that means module-level bindings outlive a single request.

```ts
// lib/user-cache.ts — imported by a route handler
const currentUser = { profile: null as Profile | null };

export async function loadProfile(session: Session) {
  if (currentUser.profile) return currentUser.profile; // whose profile?
  currentUser.profile = await db.profiles.find(session.userId);
  return currentUser.profile;
}
```

In the browser each tab gets its own realm, so this pattern feels safe. On a Node server the module is evaluated once and its bindings are shared by every request that process handles — user A's profile can be served to user B. The module's execution context is gone as soon as evaluation finishes; what stays is its module table of names, kept alive by the loaded module.

What this shows: a table lives as long as something keeps it, and a loaded module keeps its table for the life of the process. That's module caching, not a closure: no function has to be involved.

> [!warning]
> Module scope is per-realm, not per-request. Keep request-scoped data in function parameters or per-request stores, never in module-level bindings on the server.

See [[10 - Modules/01 - ES Modules|ES Modules]] and [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]].

### `instanceof Array` failing across an iframe

An embedded widget (rich-text editor, legacy portal) on the same origin exposes an array that the parent page reads directly, and a defensive check silently misroutes it. (Sent with `postMessage` instead, the array would arrive copied into the parent's realm and pass.)

```js
// Parent page receiving data built inside an iframe
const items = iframe.contentWindow.getSelectedItems();

if (items instanceof Array) {   // false!
  renderList(items);
} else {
  renderSingle(items);          // wrong branch runs
}
```

Each window/iframe is a separate **realm** with its own built-ins — the iframe's `Array` constructor is a different object than the parent's, so the prototype chain check fails. The execution context's realm field is exactly what determines which `Array` a piece of code sees. `Array.isArray(items)` works across realms because it checks whether the value is a real array (the spec's "Array exotic object"), not which realm's `Array` built it.

What this shows: the built-ins question can make two arrays that look the same fail the same check.

**What these cases share:** each one asks which table or which realm the code is looking at.

### Same mechanism, three costumes

- **A loop bug.** The `var` loop in Use Case 1 logs `3, 3, 3`, because every callback links to the one table that holds `i`.
- **A React bug.** An interval created in `useEffect(…, [])` keeps logging render 1's `filters`, because its callback links to render 1's table (§6).
- **A feature.** A debounce helper's returned function keeps `let timer` in the helper's table, so every call reaches the same timer and only the last call in a quick burst fires.

The debounce helper *(ES module. Run: node debounce.mjs)*:

```js
function debounce(fn, ms) {
  let timer;                                   // lives in debounce's table
  return (...args) => {
    clearTimeout(timer);                       // every call reaches the same timer
    timer = setTimeout(() => fn(...args), ms);
  };
}
const search = debounce((q) => console.log('search', q), 20);
search('r'); search('re'); search('react');    // logs: search react
```

What they share: a function keeps the table it was created in, for as long as the function lives. Use Case 2 looks similar but isn't this mechanism: the module ran once, and no function was needed. *(Specification model. How much of a table an engine actually keeps is an implementation detail; see §3's callout.)*

## One-Screen Recap

Cover the right column and say each answer out loud.

| Anchor | What you should be able to say |
| --- | --- |
| Execution context | The spec's record for one running script, module or function call. It answers what names exist, what `this` is, which built-ins, and where we are. |
| Names | Lookup starts at the table the LexicalEnvironment points to and walks outward. `var`s live in the function-level table. |
| Hoisting and TDZ | Names exist before the first line runs: `var` as `undefined`, `let` and `const` locked until their line. |
| `this` | Not a separate part. A regular function's table holds its `this`, set by the call; an arrow has none, so lookup walks outward. |
| Built-ins | The realm. Iframes and workers have their own. |
| Where we are | The top context on the call stack runs. `await` and `yield` lift a context off the stack and resume it later. |
| Closure | A function keeps the table it was created in, not the context. That's why stale closures read old values. |
| Block vs context | A `{ }` block gets a new table of names, not a new execution context. |

## 9. Interview Answer

**Short version:** An execution context is the spec model for currently running code. It holds, or points to, the scope information (which is also where `this` is found), the realm, and the evaluation state needed to execute that code.

**Deeper version:** JavaScript uses execution contexts for global code, modules, function calls, eval, generators, and async functions. Active contexts are managed on the execution context stack. Each context points to the tables of names used for identifier lookup (a regular function's table also holds its `this`, which arrow functions find by walking outward), its realm, and its evaluation state. This model explains hoisting, closures, `this`, stack traces, and why callbacks can read values from the render or function call where they were created.

## 10. Common Mistakes

> [!warning] An async function doesn't hold the call stack while it waits
> When an `await` suspends, its execution context is set aside and the call stack unwinds — the thread is free to run other work. The continuation resumes later as a microtask. Picturing `await` as "blocking the stack" leads to wrong reasoning about ordering and freezes.

- Saying execution context is just "memory plus code." It is a precise specification device that tracks running code: its tables of names, its realm and its evaluation state.
- Saying hoisting physically moves declarations.
- Forgetting that closures can keep lexical environments alive after a call has returned.
- Ignoring modules. Module code gets its own context and its own table of names (§5).
- Treating React stale closures as a React-only concept instead of ordinary JavaScript closure lifetime.
- Calling `this` a separate part of the execution context. That's the ES5 layout; since ES2015, `this` lives in a function's table of names.
- Saying a closure keeps the execution context alive. The context is popped when the call returns; the closure keeps the table of names.
- Thinking a `{ }` block creates a new execution context. It creates a new table of names, and the context stays the same.

## 11. Practice

1. Draw the execution context stack for three nested function calls.
2. Explain why `var` and `let` behave differently before their declaration line.
3. Explain what a callback created during render closes over.
4. What happens to an async function when it hits `await`?
5. Use "execution context" in a 2-minute explanation of closures.
6. In the running example, what would `report()` print if `summarize` used `let total` instead of `var total`? Why?

<details>
<summary>Show answer</summary>
<ol>
<li>For <code>a()</code> calling <code>b()</code> calling <code>c()</code>, the stack is global/script context, then <code>a</code>, then <code>b</code>, then <code>c</code>. When <code>c</code> returns, <code>c</code> pops; then <code>b</code>; then <code>a</code>.</li>
<li>During preparation, a <code>var</code> binding is created and initialized to <code>undefined</code>. A <code>let</code> binding is created too, but remains uninitialized until its declaration executes. Reading it early is a TDZ <code>ReferenceError</code>.</li>
<li>It closes over the lexical environment from the render/function call that created it. In React, each render is a new function call with new local bindings, so an old callback can keep reading old render values.</li>
<li>The async function's continuation is suspended. The call stack can clear and other work can run. When the awaited promise settles, the continuation is scheduled as a promise job (a microtask).</li>
<li>A strong explanation: "A closure works because a function object keeps a reference to the lexical environment from the execution context where it was created. Even after that context is no longer on the call stack, the environment can stay reachable through the function."</li>
<li>Still <code>Cart: 15</code>. A function-level <code>let total</code> lives in <code>summarize</code>'s table just like the <code>var</code> did, so the arrow keeps it the same way. The difference between <code>var</code> and <code>let</code> shows up before the declaration line (the TDZ), or when a block or loop sits between the declaration and the code that reads it.</li>
</ol>
</details>

## Related Notes

What each next note takes from this one:

- [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]] — the stack behind "where we are".
- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]] — the tables of names in full.
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]] — §4's preparation phase in depth.
- [[03 - Scope and Variables/05 - Closures|Closures]] — the kept table from §4's trace.
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]] — §6's render tables as production bugs.
- [[02 - JavaScript Runtime Foundations/06 - Realm Agent and Job Queue|Realm Agent and Job Queue]] — the realm, plus workers and job queues.
- [[05 - this Binding/01 - What is this|What is this]] — `this` for every call form.
- [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]] — §8's outward walk.
- [[08 - Async JavaScript/04 - Async Await|Async Await]] — §7's pause and resume.
- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]] — §5's generator contexts.
- [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]] — when a continuation runs.
- [[10 - Modules/01 - ES Modules|ES Modules]] — module contexts and module-level state.
