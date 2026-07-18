---
tags: [javascript, scope, scope-types]
module: "03 - Scope and Variables"
priority: must-know
status: not-started
---

# Scope Types

## Maturity Target

- Priority: #must-know
- Study time: 75-90 minutes
- Interview signal: you can predict identifier lookup without saying "JavaScript moves code around."
- Production signal: you can spot globals, module state, loop-handler bugs, stale closures, and accidental shadowing before they become hidden defects.
- Dependencies: [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]], [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]], [[03 - Scope and Variables/03 - var let const|var let const]]

## Source Anchors

- [ECMAScript 2026 - Environment Records](https://tc39.es/ecma262/2026/multipage/executable-code-and-execution-contexts.html#sec-environment-records)
- [MDN - Closures and lexical scoping](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [MDN - var](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/var)
- [MDN - let](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let)
- [MDN - import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import)
- [Next.js - Fetching data](https://nextjs.org/docs/app/getting-started/fetching-data)

## 1. Concept

Scope is the region of code where an identifier can be resolved to a binding. A binding is the association between a name and a value slot, not just the value currently stored in that slot.

JavaScript scope is mostly lexical: the place where code is written determines which outer scopes a function can access. A function does not look for variables in the caller's local scope unless that caller is already part of the function's lexical outer chain.

The practical categories you need for mid-level frontend work are:

| Scope type | Created by | Main risk |
| --- | --- | --- |
| Global scope | Script-level declarations and host-provided globals | Accidental shared state, global name collisions |
| Module scope | Top-level code in ES modules | Hidden singleton state, circular dependency reads |
| Function scope | Function body, parameters, `var` | Leaked loop counters, confusing redeclarations |
| Block scope | Blocks with `let`, `const`, `class` | TDZ errors, shadowing |
| Catch scope | `catch (error)` binding | Shadowing a wider `error` value |
| Class scope | Class body and private names | TDZ-like class reads before initialization |
| Eval/with-related behavior | Direct `eval`, `with` | Hard-to-optimize dynamic lookup; avoid in application code |

## 2. Why It Matters

Scope is the root model behind closures, hoisting, React stale closures, module live bindings, and many "what does this print?" questions. If you can identify the binding being read, you can explain most confusing JavaScript output questions calmly.

In frontend production code, scope mistakes usually appear as:

- A browser global overwritten by a script or old third-party snippet.
- A loop-created click handler reading the final loop index.
- A React callback reading state from an old render.
- A Next.js module-level cache accidentally shared across requests.
- A local variable shadowing an imported helper and making debugging misleading.

## 3. Official Mechanism

ECMAScript models scope through Environment Records. An Environment Record stores identifier bindings, and each record has an outer reference. Identifier lookup starts at the current lexical environment and walks outward until the name is found or becomes an unresolvable reference.

Important details:

- A function call creates a function environment for that invocation.
- A block can create a declarative environment for `let`, `const`, and `class`.
- A module has a module environment for top-level declarations and imports.
- A global script has a global environment, which is a special composite of object-backed global properties and declarative lexical bindings.
- These records are specification mechanisms. Engines can optimize them, but the observable behavior must match the spec.

## 4. Mental Model

Think of scope as nested notebooks:

1. The innermost notebook is checked first.
2. If the name is not there, JavaScript checks the outer notebook.
3. The chain is based on where the code was written, not where a function is called.
4. Closures keep access to notebooks that would otherwise feel "finished."

> [!example] Lexical lookup traced
> That is why this code returns `"module"` instead of `"caller"`:

```js
const label = "module";

function readLabel() {
  return label; // Resolved from the scope where readLabel was defined.
}

function caller() {
  const label = "caller";
  return readLabel(); // The caller's local label is not used.
}

console.log(caller()); // "module"
```

## 5. Scope Types in Practice

### Global Scope

Global scope is shared by all scripts in the same realm. In browser script mode, top-level `var` and function declarations can create properties on `globalThis`/`window`; top-level `let` and `const` do not create global object properties.

```js
// In a classic browser <script>, not an ES module:
var legacyToken = "abc";
const modernToken = "xyz";

console.log(window.legacyToken); // "abc"
console.log(window.modernToken); // undefined
```

> [!tip] Namespace global bridges deliberately
> Production rule: avoid application state on `window`. If integration code needs a global bridge, namespace it deliberately and document ownership.

### Module Scope

ES modules have their own top-level scope. A top-level variable is visible inside that module, not in other modules unless exported.

```js
// filters.js
const defaultLimit = 50; // Module-scoped implementation detail.

export function limitResults(items, limit = defaultLimit) {
  return items.slice(0, limit);
}
```

> [!warning] Module scope is long-lived
> Module scope is useful for constants, pure helpers, and caches. The danger is that module scope is also long-lived. In a server runtime, a module-level mutable value can outlive one request.

```js
// Bad in server code: one user's value can be observed by another request.
let currentUserId = null;

export async function loadDashboard(userId) {
  currentUserId = userId;
  const data = await fetchDashboard(userId);
  return { ...data, debugUserId: currentUserId };
}
```

Safer pattern:

```js
// Request-owned data stays in the call frame.
export async function loadDashboard(userId) {
  const data = await fetchDashboard(userId);
  return { ...data, debugUserId: userId };
}
```

### Function Scope

`var`, function parameters, and function declarations live in function scope. A `var` inside an `if` block is not block-scoped.

```js
function pickMode(isAdmin) {
  if (isAdmin) {
    var mode = "admin";
  }

  return mode; // "admin" or undefined, not ReferenceError.
}

console.log(pickMode(false)); // undefined
```

This is one reason modern application code uses `const` by default and `let` only when reassignment is intended.

### Block Scope

Blocks create scope for `let`, `const`, and `class`.

```js
if (true) {
  const status = "loaded";
  console.log(status); // "loaded"
}

// console.log(status); // ReferenceError: status is not defined
```

Block scope is especially important in loops because `let` creates a fresh per-iteration binding for many loop forms.

```js
const handlers = [];

for (let index = 0; index < 3; index += 1) {
  handlers.push(() => index); // Each callback closes over its own index binding.
}

console.log(handlers.map((handler) => handler())); // [0, 1, 2]
```

### Catch Scope

The `catch` parameter has its own binding.

```js
const error = "outer";

try {
  JSON.parse("{");
} catch (error) {
  console.log(error.name); // "SyntaxError"; shadows the outer binding.
}

console.log(error); // "outer"
```

Use meaningful names such as `parseError` or `networkError` when shadowing would make logs hard to read.

## 6. Real Frontend Scenario

Problem: a dashboard stores the last selected tab in module scope so multiple components can reuse it.

```js
// tabMemory.js
let lastSelectedTab = "overview";

export function rememberTab(tab) {
  lastSelectedTab = tab;
}

export function getRememberedTab() {
  return lastSelectedTab;
}
```

> [!warning] Module state leaks across requests
> Bug: in client-only code, this can be acceptable for a small singleton. In server rendering or tests, the module instance can be reused across requests or test cases, so one user/test can influence another.

Fix:

```js
// Keep request/user state in explicit ownership: URL, component state, storage, or request context.
export function readInitialTab(searchParams) {
  return searchParams.get("tab") ?? "overview";
}
```

> [!tip] When module scope is safe
> Tradeoff: module scope is fine for constants, pure memoization with safe keys, and runtime feature detection. It is risky for user-specific mutable state because the lifetime is larger than a component render or a request.

Production checklist:

- Is this binding shared across users, tabs, components, or requests?
- Does this value need cleanup?
- Would a test pass alone but fail after another test?
- Should this live in component state, a ref, a URL param, local storage, context, or a request-scoped cache?

## 7. Interview Answer

Short answer:

> Scope is where a name can be resolved. JavaScript uses lexical scoping, so the source-code nesting decides which outer bindings a function can access.

Deeper answer:

> The spec models scope with Environment Records linked by outer references. Identifier lookup starts in the current lexical environment and walks outward. `var` is function/global scoped, `let` and `const` are block scoped, modules have their own top-level scope, and closures preserve access to the lexical environment where a function was created.

Follow-up angle:

> In production, the real question is lifetime. A block variable may disappear after the block, a function environment may be retained by a closure, and module/global state can outlive a component or request. That is why stale closures and shared module state are scope problems, not just framework problems.

## 8. Common Mistakes

| Mistake | Better model |
| --- | --- |
| "Scope means object properties." | Scope resolves identifiers; property lookup resolves keys on values. |
| "A function uses variables from wherever it is called." | JavaScript is lexical, so it uses the environment where it was created. |
| "Top-level variables are always globals." | ES modules have module scope; script mode behaves differently. |
| "`const` means the value is frozen." | `const` prevents rebinding; object contents can still mutate. |
| "Blocks always scoped variables before ES2015." | Blocks only scope `let`, `const`, `class`, and some declarations in modern semantics; `var` remains function/global scoped. |

## 9. Practice

1. Predict the output:

```js
const name = "outer";

function getName() {
  return name;
}

function run() {
  const name = "inner";
  return getName();
}

console.log(run());
```

Expected output: `"outer"`, because `getName` closes over the scope where it was defined.

2. Refactor a module-level mutable variable into request-owned or component-owned state.
3. Explain why `window.someValue` can appear for top-level `var` in a script but not for top-level `const`.
4. Create one loop-handler bug with `var`, then fix it with `let`.
5. Describe one case where module scope is helpful and one case where it is dangerous.

## Real-World Use Cases

### Third-party snippets colliding in global scope

Two classic `<script>` tags — a tag manager and an A/B-testing vendor — both declare the analytics queue at top level. The later script silently rebinds the same global and drops every event queued before it loaded.

```js
// tag-manager.js (classic script)
var dataLayer = dataLayer || [];
dataLayer.push({ event: "page_view" });

// experiment.js (classic script, loaded later)
var dataLayer = []; // Same global binding — the queued page_view is gone.
```

This is global scope in action: all classic scripts share one global environment, and top-level `var` re-declarations rebind the same slot without any error. The `dataLayer || []` guard exists precisely because vendors know this.

> [!tip]
> Own integration globals in exactly one bootstrap module and expose everything else through module scope. If a bridge on `window` is unavoidable, namespace it (`window.__myApp`) and document which script owns it.

### Module-scope request deduplication

On first paint, three components in a Next.js page all call `loadSession()`. A module-scoped `Map` of in-flight promises collapses them into one network request.

```ts
// sessionClient.ts
const inFlight = new Map<string, Promise<Session>>();

export function loadSession(userId: string) {
  if (!inFlight.has(userId)) {
    inFlight.set(userId, fetch(`/api/session/${userId}`).then((r) => r.json()));
  }
  return inFlight.get(userId)!;
}
```

This works because a module is evaluated once per realm, so every importer resolves `inFlight` to the same module-scoped binding. The same long lifetime that makes per-user mutable state dangerous (section 6) is exactly what makes a shared cache possible — keying by `userId` is what keeps it correct on the server. See [[10 - Modules/01 - ES Modules|ES Modules]] and [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]].

### Shadowing an imported helper

A component needs a one-off currency format for a promo banner, so someone declares a local helper with the same name as the imported one. Every call in the component now resolves to the local binding, including the ones that were supposed to use the library.

```jsx
import { formatCurrency } from "@/lib/intl";

function CartTotal({ total }) {
  // Added for the promo banner — but it shadows the import for the whole function.
  const formatCurrency = (value) => `${value} EGP`;

  return <span>{formatCurrency(total)}</span>; // Never reaches the intl version.
}
```

Identifier lookup stops at the nearest binding in the scope chain, so the module-scope import is never consulted.

> [!warning]
> Shadows on common names (`error`, `data`, `format*`, `response`) are the worst kind: no error, plausible output, misleading logs. Rename the local (`formatPromoPrice`) instead of shadowing.

## Related Notes

- [[03 - Scope and Variables/02 - Lexical Environment|Lexical Environment]]
- [[03 - Scope and Variables/03 - var let const|var let const]]
- [[03 - Scope and Variables/04 - Hoisting and TDZ|Hoisting and TDZ]]
- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[01 - Roadmap|Roadmap]]
