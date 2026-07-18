---
tags: [javascript, modules, modules-checklist]
module: "10 - Modules"
priority: must-know
status: not-started
---

# Modules Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, diagnose, and fix the behavior without looking.

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes for review, more if any code-output drill feels unclear.
- Interview signal: you can connect module syntax to runtime behavior, bundler output, React/Next loading, and production debugging.
- Production signal: you know which imports execute now, which imports load later, which values stay live, and which module boundaries are risky.

## Fast Track Order

1. [[10 - Modules/01 - ES Modules|ES Modules]]
2. [[10 - Modules/03 - Named vs Default Exports|Named vs Default Exports]]
3. [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]
4. [[10 - Modules/05 - Live Bindings|Live Bindings]]
5. [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
6. [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
7. [[10 - Modules/02 - CommonJS|CommonJS]]

Reason: learn the modern ESM model first, then compare CommonJS once the ESM mechanics are clear.

## Core Understanding

- [ ] I can explain that ESM has a static import/export structure.
- [ ] I can explain parse/link/evaluate in practical terms.
- [ ] I can say why top-level module code runs once per resolved module instance.
- [ ] I can explain that modules have their own scope and run in strict mode.
- [ ] I can describe `import.meta.url` as metadata for the current module location.
- [ ] I can explain why type-only imports in TypeScript should not create runtime dependencies.
- [ ] I can explain CommonJS `require`, `module.exports`, `exports`, and the module cache.
- [ ] I can explain why assigning `exports = something` does not replace `module.exports`.
- [ ] I can compare ESM live bindings with CommonJS exported values.
- [ ] I can choose named exports, default exports, and barrels intentionally.
- [ ] I can explain dynamic `import()` as a runtime expression returning a Promise.
- [ ] I can describe the module namespace object and why default exports appear as `.default`.
- [ ] I can explain direct circular dependencies and indirect circular dependencies.
- [ ] I can identify a barrel-file circular dependency in a React or Next.js folder.
- [ ] I can explain tree shaking, side-effect analysis, code splitting, and lazy loading without mixing them together.

## Source-Backed Terms

| Term | Plain meaning | Technical meaning | Why it matters |
| --- | --- | --- | --- |
| ES module | A JavaScript file that imports or exports values. | A module with static `import`/`export`, module scope, strict mode, and linked bindings. | Enables predictable dependencies, live bindings, and static tooling. |
| CommonJS | Node's older module system. | Synchronous `require()` loading with `module.exports` as the exported object. | Still appears in config files, older packages, scripts, and Node tooling. |
| Static import | Load this dependency as part of the module graph. | A top-level `import` declaration resolved before module evaluation. | Enables early errors, bundler analysis, and clear dependencies. |
| Dynamic import | Load this module later. | `import(specifier)` expression returning a Promise for a module namespace object. | Powers lazy loading, code splitting, and conditional loading. |
| Module namespace object | The object representing a module's exports. | Object with properties for named exports and `.default` for default export. | Needed when using `await import()` or `import * as ns`. |
| Live binding | Imported value stays connected to exporter. | Import reads the exporting module's binding slot; importer cannot reassign it. | Explains updated exports, circular dependency behavior, and read-only imports. |
| Barrel file | A file that re-exports many files. | Usually `index.ts` with many `export ... from` statements. | Can improve import ergonomics but hide side effects, cycles, and bundle cost. |
| Side effect | Work that happens just by importing a module. | Top-level observable behavior such as CSS import, global patch, DOM write, or registration. | Bundlers must preserve side effects, so tree shaking becomes conservative. |
| Tree shaking | Remove unused code. | Bundler dead-code elimination based on static graph and side-effect safety. | Reduces production JavaScript when module design is clean. |
| Code splitting | Ship code in multiple files. | Bundler emits separate chunks from entries or dynamic import split points. | Reduces initial payload but requires loading-state design. |

## Production Readiness Checklist

- [ ] I avoid top-level browser API access in modules that can run during SSR.
- [ ] I keep shared utility modules side-effect-light.
- [ ] I import heavy components with dynamic import when the user does not need them immediately.
- [ ] I provide loading and error states for lazy-loaded UI.
- [ ] I avoid broad barrels for heavy, route-specific, or side-effectful modules.
- [ ] I import sibling components directly when a barrel would create a cycle.
- [ ] I use named exports for utility collections where tree shaking and refactor safety matter.
- [ ] I inspect production bundle output before claiming an optimization worked.
- [ ] I keep CSS, polyfills, and registrations listed as side effects when publishing packages.
- [ ] I handle CommonJS interop carefully instead of assuming it behaves like ESM.

## Real-World Scenario Review

### Scenario 1: `window is not defined`

Problem:

```ts
// viewport.ts
export const width = window.innerWidth;
```

Bug:

- importing this module on the server throws before React can render;
- the module does browser work at top level.

Fix:

```ts
// viewport.ts
export function getViewportWidth() {
  // The browser API is read only when the caller is in the browser.
  return window.innerWidth;
}
```

React usage:

```tsx
import { useEffect, useState } from "react";
import { getViewportWidth } from "./viewport";

export function ViewportLabel() {
  const [width, setWidth] = useState<number | null>(null);

  useEffect(() => {
    // Effects do not run during server rendering.
    setWidth(getViewportWidth());
  }, []);

  return <span>{width === null ? "Measuring..." : `${width}px`}</span>;
}
```

Interview angle: module top-level code runs when the module evaluates. In SSR, that may happen in a non-browser runtime.

### Scenario 2: CommonJS stale primitive

Problem:

```js
// counter.cjs
let count = 0;

function increment() {
  count += 1;
}

module.exports = { count, increment };
```

```js
// main.cjs
const { count, increment } = require("./counter.cjs");

console.log(count); // 0
increment();
console.log(count); // 0, because count was exported as a primitive value
```

Fix:

```js
// counter.cjs
let count = 0;

function increment() {
  count += 1;
}

function getCount() {
  return count;
}

module.exports = { increment, getCount };
```

```js
const { increment, getCount } = require("./counter.cjs");

console.log(getCount()); // 0
increment();
console.log(getCount()); // 1
```

Interview angle: CommonJS returns an object. If that object contains a primitive snapshot, destructuring does not create an ESM-style live binding.

### Scenario 3: Lazy chunk without user feedback

Problem:

```tsx
const HeavyChart = lazy(() => import("./HeavyChart"));

export function Dashboard() {
  return <HeavyChart />;
}
```

Bug:

- the component suspends;
- without a nearby `Suspense` boundary, the user experience can be blank or the nearest large boundary may hide too much UI.

Fix:

```tsx
import { Suspense, lazy } from "react";

const HeavyChart = lazy(() => import("./HeavyChart"));

export function Dashboard() {
  return (
    <Suspense fallback={<div aria-busy="true">Loading chart...</div>}>
      <HeavyChart />
    </Suspense>
  );
}
```

Interview angle: dynamic import solves loading, not UX. Production code still needs a fallback, an error path, and measurement.

### Scenario 4: Barrel-file cycle

Problem:

```ts
// components/index.ts
export { Button } from "./Button";
export { UserCard } from "./UserCard";
```

```tsx
// components/UserCard.tsx
import { Button } from "./index";

export function UserCard() {
  return <Button>View user</Button>;
}
```

Bug:

- `index.ts` imports `UserCard`;
- `UserCard` imports `index.ts`;
- the cycle can expose uninitialized bindings, undefined values, or confusing hot-reload behavior.

Fix:

```tsx
// components/UserCard.tsx
import { Button } from "./Button";

export function UserCard() {
  return <Button>View user</Button>;
}
```

Interview angle: barrels are useful at package boundaries, but internal sibling imports should often stay direct.

## Code-Output Drills

### Drill 1: ESM live binding

```js
// counter.mjs
export let count = 0;

export function increment() {
  count += 1;
}

// main.mjs
import { count, increment } from "./counter.mjs";

console.log(count);
increment();
console.log(count);
```

Expected output:

```txt
0
1
```

Reason: `count` is a live import binding. The importer reads the exporter's current binding value.

### Drill 2: Importer cannot assign

```js
import { count } from "./counter.mjs";

count = 10;
```

Expected behavior: throws a `TypeError`.

Reason: imports are read-only from the importer's side. The exporting module can update `count`; the importer cannot reassign the imported binding.

### Drill 3: Dynamic import namespace

```js
// settings.mjs
export default { theme: "dark" };
export const version = 3;

// main.mjs
const mod = await import("./settings.mjs");

console.log(mod.default.theme);
console.log(mod.version);
```

Expected output:

```txt
dark
3
```

Reason: `import()` resolves to a module namespace object. The default export is available on `.default`.

### Drill 4: `exports` pitfall

```js
// config.cjs
exports.apiUrl = "https://api.example.com";
exports = {
  apiUrl: "https://other.example.com"
};
```

```js
// main.cjs
const config = require("./config.cjs");
console.log(config.apiUrl);
```

Expected output:

```txt
https://api.example.com
```

Reason: `exports` initially references `module.exports`, but assigning `exports = ...` only reassigns the local variable. It does not replace `module.exports`.

### Drill 5: Static import vs dynamic import

```ts
if (shouldLoadEditor) {
  import Editor from "./Editor";
}
```

Expected behavior: syntax error.

Reason: static import declarations must be top-level module syntax. Conditional loading needs dynamic `import()`.

```ts
if (shouldLoadEditor) {
  const { default: Editor } = await import("./Editor");
  render(<Editor />);
}
```

## Interview Prompts

1. Explain ESM in one minute without using the word "magic".
2. Why can ESM support live bindings while CommonJS often behaves like a value snapshot?
3. What is the difference between a default export and a named export?
4. When would you choose a barrel file, and when would you avoid one?
5. Why can circular dependencies sometimes work in ESM and fail in another ESM example?
6. What does dynamic `import()` return, and how does that connect to React `lazy`?
7. What is the difference between tree shaking and code splitting?
8. Why can `"sideEffects": false` be both helpful and dangerous?
9. How would you debug a Next.js route that unexpectedly includes a charting library?
10. What does `ssr: false` solve, and what does it cost?

## Self-Review Rubric

| Level | What your answer sounds like |
| --- | --- |
| Weak | "Modules let you split files. Tree shaking removes unused code." |
| Junior-plus | "ESM uses import/export. Dynamic import loads later. CommonJS uses require." |
| Mid-level | "Static ESM imports are linked before evaluation, imports are live bindings, and dynamic import returns a Promise for a namespace object." |
| Strong mid-level | "I can also explain how those mechanics affect SSR, circular dependencies, bundle output, lazy loading UX, side effects, and CommonJS interop." |

## Final Module Test

Before leaving this module, you should be able to do all of this from memory:

- write one ESM module with named and default exports;
- import it statically and dynamically;
- explain the dynamic import return value;
- show one live binding example;
- show one CommonJS stale-value example;
- fix one circular dependency caused by a barrel file;
- turn a static heavy import into a lazy-loaded component;
- explain the production tradeoff of that lazy load;
- name one case where tree shaking must preserve unused-looking code;
- debug a route bundle that includes an unexpected dependency.

## Related Notes

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/02 - CommonJS|CommonJS]]
- [[10 - Modules/03 - Named vs Default Exports|Named vs Default Exports]]
- [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]]
- [[01 - Roadmap|Roadmap]]
