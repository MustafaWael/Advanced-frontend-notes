---
tags: [javascript, modules, es-modules]
module: "10 - Modules"
priority: must-know
status: not-started
aliases: [ESM]
---

# ES Modules

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: you can explain static module structure, parse/link/evaluate, strict mode, module scope, live bindings, and top-level side effects.
- Production signal: you design modules that are tree-shakable, server/client safe, and easy to refactor in React/Next.js projects.
- Dependencies: [[02 - JavaScript Runtime Foundations/03 - Execution Context|Execution Context]], [[10 - Modules/05 - Live Bindings|Live Bindings]]

## Source Anchors

- [MDN JavaScript modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [MDN import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import)
- [MDN export](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/export)
- [MDN import.meta](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import.meta)
- [ECMAScript Modules](https://tc39.es/ecma262/#sec-modules)
- [Node.js ECMAScript modules](https://nodejs.org/api/esm.html)

## 1. Concept

ES modules are the standard JavaScript module system. They use `import` and `export` declarations to connect files into a statically analyzable module graph.

```js
// price.js
export function formatPrice(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(value);
}

// product-card.js
import { formatPrice } from "./price.js";

console.log(formatPrice(19));
// "$19.00"
```

ESM is not just syntax. It changes loading, scoping, strictness, linking, circular dependency behavior, and bundler optimization.

## 2. Why It Matters

Modern frontend apps depend on module design for:

- routing and route-level chunks
- shared UI components
- tree shaking
- lazy loading
- server/client boundaries in Next.js
- testability
- circular dependency avoidance
- environment-specific code
- bundle size and startup cost

> [!warning] Cost of bad module design
> Bad module design can ship too much JavaScript, run browser-only code on the server, create import cycles, or make a simple refactor painful.

## 3. Official Mechanism

ES modules are statically structured:

- `import` and `export` declarations appear at module top level.
- imports are resolved and linked before module code evaluates.
- module code runs in strict mode automatically.
- top-level declarations are scoped to the module, not added to `globalThis`.
- modules expose live bindings.
- a module is evaluated once per module graph instance/realm, then reused by importers.
- dynamic `import()` is an expression that returns a promise for the module namespace object.

The useful lifecycle model:

```txt
Parse    -> find imports/exports and syntax errors
Link     -> connect imported names to exported bindings
Evaluate -> run module code and initialize values
```

## 4. Mental Model

Think of ESM as a graph:

```txt
entry module
  imports route module
    imports component module
      imports utility module
```

Because the structure is visible before execution, engines and bundlers can reason about dependencies, unused exports, and cycles.

## 5. Module Scope And Strict Mode

```html
<script type="module" src="/app.js"></script>
```

```js
// app.js
const appName = "shop";

console.log(window.appName);
// undefined
```

Top-level `const`, `let`, `class`, and function declarations in a module do not become global object properties.

Modules are strict by default:

```js
// In a module:
console.log(this);
// undefined
```

This reduces accidental global writes and makes module behavior more predictable.

## 6. Module Evaluation And Singletons

```js
// store.js
console.log("store evaluated");

export const store = {
  user: null,
};

// a.js
import { store } from "./store.js";

// b.js
import { store } from "./store.js";
```

> [!example] One evaluation, shared instance
> For the same resolved module, `store.js` is evaluated once. Both importers receive bindings connected to the same module instance.

Production use:

- shared client-side stores
- caches
- feature flag clients
- SDK setup

Production caution:

- avoid user-specific mutable data at module top level in server runtimes
- server modules may stay cached across requests
- top-level side effects run when the module is imported, even if only one helper is needed

## 7. Top-Level Side Effect Bug

### Problem

```js
// analytics.js
window.analytics = createAnalyticsClient();
window.analytics.track("module loaded");

export function track(eventName) {
  window.analytics.track(eventName);
}
```

### Bug

> [!warning] Import triggers side effects
> Importing `track` runs global browser-only side effects immediately. This can break server rendering, tests, and bundle tree shaking.

### Fix

```js
// analytics.js
let client;

export function getAnalytics() {
  if (!client) {
    client = createAnalyticsClient();
  }

  return client;
}

export function track(eventName) {
  getAnalytics().track(eventName);
}
```

Even better for SSR:

```js
export function track(eventName) {
  if (typeof window === "undefined") return;
  getAnalytics().track(eventName);
}
```

## 8. `import.meta`

`import.meta` gives module-specific metadata.

```js
console.log(import.meta.url);
// URL of the current module
```

Common production uses:

```js
const workerUrl = new URL("./worker.js", import.meta.url);
const worker = new Worker(workerUrl, { type: "module" });
```

Tool-specific examples:

- Vite exposes `import.meta.env`.
- Vite supports `import.meta.glob`.
- Node exposes file URL metadata in ESM.

> [!tip] Isolate tool-specific metadata
> Keep tool-specific `import.meta` usage isolated so it is not confused with standard ECMAScript behavior.

## 9. TypeScript Type-Only Imports

```ts
import type { User } from "./types";

export function getUserName(user: User) {
  return user.name;
}
```

> [!tip] Erase type-only imports
> `import type` tells TypeScript the import is only for types and can be erased from runtime JavaScript. This helps avoid unnecessary runtime imports and can reduce circular dependency risk.

## 10. Native Browser Module Notes

Native browser modules have practical constraints:

- use `<script type="module">`
- module scripts are deferred by default
- browsers require a JavaScript MIME type
- relative imports need resolvable URLs
- many native environments require explicit file extensions
- local `file://` testing often fails because module fetching expects proper HTTP behavior

Bundlers hide some of this with resolution rules, TypeScript path aliases, and dev servers. Know whether you are running native ESM, Node ESM, or bundled ESM.

## 11. Real Frontend Module Design

```ts
// product-formatters.ts
export function formatPrice(value: number, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(value);
}

export function formatInventory(count: number) {
  return count > 0 ? `${count} available` : "Out of stock";
}
```

This module is:

- side-effect-light
- easy to test
- tree-shaking friendly
- safe on server and client
- clear about ownership

Compare that with a module that imports the whole app store, starts analytics, reads `window`, and exports one formatter. That module becomes hard to reuse and risky to import.

## 12. Production Tradeoffs

- Top-level work is paid when the module loads. Keep it cheap.
- Module singletons are useful for app-wide services but risky for request-specific server data.
- Static imports improve analysis but load required code upfront.
- Dynamic imports improve initial payload but add async loading states and chunk-failure paths.
- Barrel files improve ergonomics but can hide side effects and cycles.
- Type-only imports improve runtime boundaries, but developers must understand what is erased.

## Real-World Use Cases

### Classic interview trap: code above an import does not run first

```js
// logger.js
console.log("logger evaluated");
export function log(msg) {
  console.log(msg);
}

// main.js
console.log("main starts");
import { log } from "./logger.js";
log("hello");
```

Wrong guess: `"main starts"` prints first because it is written first. Actual output:

```txt
logger evaluated
main starts
hello
```

Tick-by-tick: during **parse**, the engine discovers `main.js` imports `logger.js` — import declarations are hoisted to the module level regardless of where they appear. During **link**, `log` is connected to the export binding. During **evaluate**, dependencies run first (depth-first), so `logger.js`'s top-level code executes before any statement in `main.js`. Statement order inside a module never changes dependency evaluation order. See [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]] and [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]].

### Prisma client singleton surviving Next.js dev hot reload

"Evaluated once per module graph" is why a database client lives at module level — but in Next.js dev, HMR creates fresh module instances, so a naive singleton spawns a new connection pool on every save until the database hits its connection limit.

```ts
// lib/db.ts
import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as { prisma?: PrismaClient };

export const prisma = globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma; // survives module re-evaluation in dev
}
```

Works because module evaluation happens once **per module graph instance** — HMR builds a new graph, so true cross-reload state must escape to `globalThis`.

> [!tip]
> This exact pattern is in the official Prisma + Next.js docs. It only makes sense once you know "singleton" means per-graph, not per-process.

### Embeddable widget script that needs no DOMContentLoaded

A checkout widget is dropped into arbitrary merchant pages with one tag. Because module scripts are deferred by default, the DOM is fully parsed before the module evaluates — no `DOMContentLoaded` wrapper, no "container not found" race.

```html
<script type="module" src="https://cdn.pay.example/widget.js"></script>
<div id="pay-widget" data-merchant="acme"></div>
```

```js
// widget.js — safe to query immediately: module scripts run after parsing
const mount = document.querySelector("#pay-widget");
renderWidget(mount, mount.dataset.merchant);
```

This relies on the native browser module constraint from section 10: `type="module"` implies deferred execution, and the module's top-level scope keeps the widget's variables off the merchant's `globalThis`.

> [!warning]
> A classic non-module `<script>` at the same position would run before the `<div>` exists. Teams migrating widgets to ESM sometimes delete the `DOMContentLoaded` handler and forget older embed instructions told merchants to put the tag in `<head>` — that still works for modules, but only because of defer.

## 13. Interview Answer

**Short version:** ES modules are JavaScript's standard module system. They use top-level `import` and `export`, are statically linked, run in strict mode, have module scope, and expose live bindings.

**Strong version:** An ES module participates in a module graph. The engine parses modules to discover imports and exports, links imported names to exported bindings, then evaluates modules. Static structure is what enables bundlers to tree-shake and split code. Imports are live read-only views of exported bindings, and a module is evaluated once for a given resolved module instance. In frontend production, I keep modules side-effect-light, avoid browser-only top-level work in shared/server code, use type-only imports when appropriate, and treat module boundaries as part of performance architecture.

## 14. Common Mistakes

- Putting static `import` inside a function or conditional.
- Assuming top-level module declarations become globals.
- Forgetting modules are strict by default.
- Hiding browser-only side effects at module top level.
- Storing request-specific server data in module singletons.
- Confusing native browser ESM resolution with bundler resolution.
- Mixing `process.env`, `import.meta.env`, and runtime configuration without knowing the framework.
- Assuming module code runs every time it is imported.

## 15. Practice

1. Explain parse, link, and evaluate in plain English.
2. Write a side-effect-light utility module and a risky side-effectful version.
3. Explain why `import` must be top-level.
4. Show how `import.meta.url` can locate a worker file.
5. Explain why a module-level cache can be useful on the client but dangerous for per-user server data.

## Related Notes

- [[10 - Modules/02 - CommonJS|CommonJS]]
- [[10 - Modules/03 - Named vs Default Exports|Named vs Default Exports]]
- [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[01 - Roadmap|Roadmap]]
