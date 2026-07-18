---
tags: [javascript, modules, named-vs-default-exports]
module: "10 - Modules"
priority: must-know
status: not-started
---

# Named vs Default Exports

## Maturity Target

- Priority: #must-know
- Study time: 75-100 minutes
- Interview signal: you can explain named exports, default exports, aliases, namespace imports, re-exports, and refactor tradeoffs.
- Production signal: you choose export style intentionally for components, utilities, routes, barrels, and tree shaking.
- Dependencies: [[10 - Modules/01 - ES Modules|ES Modules]], [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]

## Source Anchors

- [MDN export](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/export)
- [MDN import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import)
- [MDN JavaScript modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [React lazy](https://react.dev/reference/react/lazy)
- [Next.js Lazy Loading](https://nextjs.org/docs/app/guides/lazy-loading)

## 1. Concept

Named exports expose bindings by explicit names. Default exports expose one special export named `default`.

```js
// named
export function formatPrice(value) {
  return `$${value}`;
}

// default
export default function ProductCard() {
  return null;
}
```

Imports:

```js
import { formatPrice } from "./format.js";
import ProductCard from "./ProductCard.js";
```

## 2. Why It Matters

Export style affects:

- refactor safety
- auto-import behavior
- tree-shaking clarity
- code navigation
- React lazy loading
- barrel-file design
- public API consistency

> [!tip] No universal export rule
> There is no universal rule that "default is bad" or "named is always better." The mature decision depends on the role of the module.

## 3. Accurate Mechanism

Named imports must match exported names unless aliased:

```js
import { formatPrice as money } from "./format.js";
```

Default imports can choose any local name:

```js
import AnythingHere from "./ProductCard.js";
```

A default export is still an export entry under the name `default`.

```js
const ProductCard = () => null;

export { ProductCard as default };
```

## 4. Mental Model

Use named exports for modules with multiple reusable capabilities.

Use default exports when the file truly has one primary value, or a framework convention requires it.

## 5. Named Export Patterns

```ts
// product-formatters.ts
export function formatPrice(value: number) {
  return `$${value.toFixed(2)}`;
}

export function formatSku(value: string) {
  return value.trim().toUpperCase();
}
```

```ts
import { formatPrice, formatSku } from "./product-formatters";
```

Benefits:

- import names are consistent
- renames are easier for tooling
- unused exports are easier for bundlers to reason about
- code search is clearer

## 6. Default Export Patterns

```tsx
// ProductCard.tsx
export default function ProductCard({ product }) {
  return <article>{product.name}</article>;
}
```

```tsx
import ProductCard from "./ProductCard";
```

Good fits:

- framework route files that require default exports
- one primary React component per file
- `React.lazy`, which expects the dynamic import to resolve to a module object with a `default` component

```tsx
const ProductCard = lazy(() => import("./ProductCard"));
```

## 7. Default Export Refactor Risk

```js
// user-service.js
export default function createUserService() {}
```

Different importers can name it differently:

```js
import service from "./user-service.js";
import createUsers from "./user-service.js";
import makeThing from "./user-service.js";
```

> [!warning] Divergent default import names
> This can make large refactors harder. Named exports force the shared API name unless an alias is explicit.

## 8. Default Object Anti-Pattern

```js
// utils.js
export default {
  formatPrice,
  formatDate,
  debounce,
  calculateTax,
};
```

> [!warning] Default object hides usage
> This hides which properties are used and can reduce tree-shaking clarity.

Prefer:

```js
export { formatPrice } from "./format-price.js";
export { formatDate } from "./format-date.js";
export { debounce } from "./debounce.js";
export { calculateTax } from "./calculate-tax.js";
```

## 9. Re-Exports And Barrels

```ts
// components/index.ts
export { Button } from "./Button";
export { Dialog } from "./Dialog";
export { default as ProductCard } from "./ProductCard";
export type { ButtonProps } from "./Button";
```

Barrels can improve imports:

```ts
import { Button, Dialog } from "@/components";
```

But barrels can also:

- hide circular dependencies
- pull in side effects
- slow tooling in large repos
- make bundle analysis harder

Use direct imports inside a folder when a barrel would import back through itself.

## 10. Real Frontend Decision

### Utilities

Prefer named exports:

```ts
export function formatCurrency() {}
export function parseCurrency() {}
```

### React Component File

Either is acceptable, based on team convention:

```tsx
export function ProductCard() {}
```

or:

```tsx
export default function ProductCard() {}
```

### Route/Page Files

Follow framework convention:

```tsx
export default function Page() {
  return <Dashboard />;
}
```

## 11. Real Frontend Bug: Lazy Loading A Named Export

> [!example] Lazy loading a named export
> Problem: a component library uses named exports, but `React.lazy` expects the dynamically imported module to expose the component as `default`.

```tsx
// ProductChart.tsx
export function ProductChart({ data }) {
  return <Chart data={data} />;
}
```

```tsx
import { lazy } from "react";

// Bug: the imported module has no default export.
const ProductChart = lazy(() => import("./ProductChart"));
```

Failure mode:

- the dynamic import resolves successfully;
- React looks for `module.default`;
- `module.default` is `undefined`;
- the lazy component fails when React tries to render it.

Fix:

```tsx
import { lazy } from "react";

const ProductChart = lazy(() =>
  import("./ProductChart").then((module) => ({
    // Adapt the named export into the default shape React.lazy expects.
    default: module.ProductChart
  }))
);
```

> [!tip] Adapter vs convention change
> Tradeoff: this adapter is fine for one-off lazy loading, but if most files in a component directory need lazy loading, the team may prefer default exports for one-component files and named exports for shared utilities.

Interview angle: default and named exports are both ESM export entries, but consuming tools can impose a shape. `React.lazy` is one of those tools.

## 12. Production Checklist

- Use named exports for shared utilities and service functions.
- Use default exports where one primary value or framework convention is clear.
- Avoid default-exported utility objects.
- Alias named imports only when it improves clarity.
- Keep barrel files side-effect-light.
- Export types with `export type` where appropriate.
- Verify lazy-loaded React components expose a default component when using `React.lazy`.
- Avoid mixing many unrelated exports into one module.

## Real-World Use Cases

### Icon library imports that decide your bundle size

A product header needs three icons from `lucide-react` (1500+ icons). Named exports from a package with proper ESM let the bundler drop the other 1497; importing a namespace or a default bag ships everything.

```tsx
// ships 3 icons after tree shaking
import { ShoppingCart, Search, UserRound } from "lucide-react";

// ships the whole library — the bundler can't prove which keys you read
import * as Icons from "lucide-react";
const CartIcon = Icons[iconName]; // dynamic key kills static analysis
```

Named exports work here because each icon is a separate export entry in the static module graph — the exact property the bundler needs for dead-code elimination. See [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]].

> [!warning]
> Dynamic icon-by-name lookups (`Icons[iconName]`) are a real product need (CMS-driven icons). Solve them with an explicit whitelist map of named imports, not a namespace import.

### Mocking modules in Vitest: default exports need the `default` shape

A checkout test mocks the pricing module. Named exports mock naturally; a default export must be returned under the literal key `default`, because that is its real export name.

```ts
// pricing.ts: export function applyDiscount() {...}  export default calculateTotal
vi.mock("./pricing", () => ({
  applyDiscount: vi.fn(() => 90),
  default: vi.fn(() => 100), // forget this key and the import is undefined
}));
```

The factory must reproduce the module's export entries — and a default export is just an entry named `default` (section 3). Omitting it gives the same silent-`undefined` failure mode as the `React.lazy` bug in section 11, but at test time.

### Importing a CommonJS package: what does "default" even mean?

A Next.js API route imports a CJS-only package (for example an older `qs` or `lodash` build). Bundlers with interop make `import qs from "qs"` work, but native Node ESM assigns `module.exports` itself as the default export — named-looking imports may or may not exist depending on Node's static analysis of the CJS file.

```ts
import qs from "qs";               // safe: default = module.exports in Node ESM
import { parse } from "qs";        // works only if Node's cjs-module-lexer detects it
qs.parse("a=1");                   // always safe
```

The mechanism: CJS has no export entries, so the ESM loader synthesizes them — `default` is guaranteed, named entries are best-effort. Code that passed in webpack (interop shims) can throw `SyntaxError: named export not found` in plain Node.

> [!tip]
> For CJS dependencies, prefer the default import plus property access. Reserve named imports for packages that ship real ESM. See [[10 - Modules/02 - CommonJS|CommonJS]].

## 13. Interview Answer

**Short version:** Named exports expose specific names that importers must use. Default exports expose one special `default` binding that importers can name locally.

**Strong version:** Named exports are usually better for shared utilities because they improve refactorability, searchability, and static analysis. Default exports are ergonomic when a module has one primary value and are required by some framework patterns, such as route components or `React.lazy` expecting a default component. A default export is not magic; it is an export entry named `default`. In production, I avoid default-exported utility objects and keep barrels side-effect-light so bundlers and humans can understand what is actually used.

## 14. Common Mistakes

- Assuming default import names must match the exported function name.
- Exporting a bag object as default for utilities.
- Mixing unrelated values in one module.
- Using a barrel file from inside a file that the barrel re-exports.
- Forgetting `React.lazy` expects a default export unless adapted.
- Exporting runtime values when only types are needed.
- Treating export style as purely personal preference instead of API design.

## 15. Practice

1. Convert a default utility object into named exports.
2. Import a named export with an alias.
3. Re-export a default component as a named export from a barrel.
4. Explain why a default export can make search/refactor harder.
5. Make a `React.lazy` import work for a named-exported component.

## Related Notes

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[01 - Roadmap|Roadmap]]
