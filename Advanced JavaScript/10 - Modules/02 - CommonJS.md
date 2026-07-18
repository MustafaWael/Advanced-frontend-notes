---
tags: [javascript, modules, commonjs]
module: "10 - Modules"
priority: important
status: not-started
aliases: [CJS]
---

# CommonJS

## Maturity Target

- Priority: #important
- Study time: 90-120 minutes
- Interview signal: you can explain `require`, `module.exports`, the module wrapper, cache, cycles, and CJS/ESM interop.
- Production signal: you can diagnose bundler tree-shaking issues, config-file format problems, and package compatibility bugs.
- Dependencies: [[10 - Modules/01 - ES Modules|ES Modules]], [[10 - Modules/05 - Live Bindings|Live Bindings]]

## Source Anchors

- [Node.js CommonJS modules](https://nodejs.org/api/modules.html)
- [Node.js ECMAScript modules](https://nodejs.org/api/esm.html)
- [MDN JavaScript modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [webpack: Tree Shaking](https://webpack.js.org/guides/tree-shaking/)

## 1. Concept

CommonJS is Node.js's original module system. It uses `require()` to load modules and `module.exports` to expose values.

```js
// math.cjs
function add(a, b) {
  return a + b;
}

module.exports = { add };

// app.cjs
const { add } = require("./math.cjs");

console.log(add(2, 3));
// 5
```

CommonJS is still common in Node tooling, older packages, test configs, and some build pipelines.

## 2. Why It Matters

Frontend developers hit CommonJS when:

- installing older npm packages
- reading Node config files
- debugging bundler output
- migrating packages to ESM
- using Jest or older tooling
- mixing `require` and `import`
- analyzing why a dependency did not tree-shake

You do not need to prefer CommonJS for modern frontend app code, but you should understand it because the ecosystem still contains it.

## 3. Accurate Mechanism

CommonJS is a Node module system, not part of ECMAScript.

Node wraps CommonJS modules in a function-like wrapper that provides:

- `exports`
- `require`
- `module`
- `__filename`
- `__dirname`

`require()` roughly:

1. resolves a module id
2. checks the require cache
3. creates a module object if needed
4. executes the module
5. returns `module.exports`

The first load evaluates the module. Later loads usually return the cached `module.exports`.

## 4. Mental Model

CommonJS is runtime loading of an exports object.

ESM is static linking of live bindings.

That difference affects tree shaking, circular dependencies, and interop.

## 5. `module.exports` vs `exports`

```js
exports.name = "cart";
exports.createCart = function createCart() {
  return [];
};
```

This works because `exports` initially references `module.exports`.

This does not work:

```js
exports = {
  name: "cart",
};
```

> [!warning] Reassigning exports does nothing
> Reassigning `exports` changes the local variable, not `module.exports`.

Use `module.exports` when replacing the entire export:

```js
module.exports = function createLogger() {
  return {
    log(message) {
      console.log(message);
    },
  };
};
```

## 6. Cache And Singleton Behavior

```js
// config.cjs
console.log("config evaluated");

module.exports = {
  featureEnabled: true,
};

// app.cjs
const a = require("./config.cjs");
const b = require("./config.cjs");

console.log(a === b);
// true
```

The module is evaluated once and cached.

Production caution:

- module-level state persists
- tests can leak state between cases
- server processes can reuse cached module state across requests

## 7. CommonJS Export Values Are Not ESM Live Bindings

```js
// counter.cjs
let count = 0;

function increment() {
  count += 1;
}

module.exports = { count, increment };

// main.cjs
const { count, increment } = require("./counter.cjs");

console.log(count);
// 0

increment();

console.log(count);
// 0
```

> [!example] Stale destructured primitive
> `count` was copied out by destructuring. A getter function preserves a live read:

```js
// counter.cjs
let count = 0;

module.exports = {
  increment() {
    count += 1;
  },
  getCount() {
    return count;
  },
};
```

## 8. Circular Dependencies In CommonJS

CommonJS caches a module before it finishes evaluating so cycles can terminate.

```js
// a.cjs
const b = require("./b.cjs");
exports.name = "A";
exports.fromB = b.name;

// b.cjs
const a = require("./a.cjs");
exports.name = "B";
exports.fromA = a.name;
```

> [!warning] Partial exports in cycles
> When `b.cjs` reads `a.name`, `a.cjs` may not have assigned it yet. The result can be `undefined` or incomplete behavior.

Fix cycles by:

- extracting shared code to a third module
- deferring reads into functions
- inverting dependencies
- removing barrel-file self-imports

## 9. CJS/ESM Interop

Modern Node and bundlers support many interop cases, but rules differ by runtime and version.

General practical rules:

- ESM can usually import CommonJS; `module.exports` appears as the default export in many environments.
- CommonJS can use dynamic `import()` to load ESM asynchronously.
- Modern Node can `require()` some ESM modules under specific constraints, but this is not a universal browser/bundler assumption.
- TypeScript and bundlers add interop flags that can change emitted code.

Portable CommonJS to ESM loading:

```js
async function loadModernModule() {
  const module = await import("./modern-module.mjs");
  return module.default ?? module;
}
```

## 10. Frontend Production Bug: CJS Dependency Bloats Bundle

### Problem

```js
import { debounce } from "some-old-cjs-utils";
```

### Bug

> [!warning] CJS blocks tree shaking
> The package exposes only CommonJS entry points. The bundler cannot reliably tree-shake the unused code, so a small helper import may pull in much more than expected.

### Fix Options

- prefer an ESM entry if the package exposes one
- import a smaller subpath if documented
- replace the dependency with a native/smaller utility
- inspect production bundle output
- avoid assuming dev-server behavior equals production bundle behavior

## 11. Common Real Files

CommonJS still appears in:

```js
// older config files
module.exports = {
  testEnvironment: "jsdom",
};
```

```js
// scripts/build.cjs
const fs = require("node:fs");
const path = require("node:path");
```

> [!tip] Check project module conventions
> Many modern tools support ESM configs too, but project conventions and package type settings matter.

## 12. Production Tradeoffs

- CommonJS is simple and mature in Node tooling.
- Synchronous `require` fits server startup scripts but not native browser loading.
- Dynamic `require` makes static analysis harder.
- CommonJS packages can reduce tree-shaking quality in frontend bundles.
- ESM interop is better than it used to be, but exact behavior depends on runtime, package metadata, transpiler, and bundler.

## 13. Interview Answer

**Short version:** CommonJS is Node's older module system. It uses `require()` and `module.exports`, loads modules at runtime, and returns the cached exports object.

**Strong version:** CommonJS is not ECMAScript. Node wraps each CJS file with parameters such as `exports`, `require`, and `module`. The first `require` resolves, executes, and caches the module; later requires return the cached `module.exports`. `exports` is only a shortcut to `module.exports` until you reassign it. Compared with ESM, CommonJS is more dynamic and less statically analyzable, which can hurt tree shaking. In production, I watch for CJS-only dependencies in client bundles, module cache state in tests/server code, and circular dependencies that expose partial exports.

## 14. Common Mistakes

- Reassigning `exports` instead of `module.exports`.
- Assuming destructured CommonJS primitive exports update like ESM live bindings.
- Forgetting `require` caches modules.
- Forgetting tests can share module cache state.
- Assuming all CJS/ESM interop works the same in Node, TypeScript, webpack, Vite, and Next.js.
- Using dynamic `require` in code expected to tree-shake.
- Ignoring circular `require` partial export behavior.

## 15. Practice

1. Explain Node's CommonJS wrapper.
2. Predict the `counter.cjs` output in this note.
3. Show why `exports = {}` does not replace `module.exports`.
4. Explain how the require cache can affect tests.
5. Diagnose why a CJS-only package increases a frontend bundle.

## Related Notes

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/03 - Named vs Default Exports|Named vs Default Exports]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[01 - Roadmap|Roadmap]]
