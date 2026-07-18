---
tags: [javascript, modules, tree-shaking-and-code-splitting]
module: "10 - Modules"
priority: important
status: not-started
---

# Tree Shaking and Code Splitting

## Maturity Target

- Priority: #important
- Study time: 110-150 minutes
- Interview signal: strong candidates separate ECMAScript module semantics from bundler optimizations.
- Production signal: you can reduce initial JavaScript without breaking side effects, CSS, SSR, or lazy-loaded UX.

## Source Anchors

- [MDN JavaScript modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [MDN dynamic import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import)
- [webpack Tree Shaking](https://webpack.js.org/guides/tree-shaking/)
- [webpack Code Splitting](https://webpack.js.org/guides/code-splitting/)
- [React lazy](https://react.dev/reference/react/lazy)
- [Next.js Lazy Loading](https://nextjs.org/docs/app/guides/lazy-loading)
- Related: [[10 - Modules/01 - ES Modules|ES Modules]], [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]], [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]

## 1. Concept

Tree shaking and code splitting are build/runtime delivery techniques built on top of module boundaries.

- **Tree shaking**: the bundler removes code that is reachable in source files but not needed by the final bundle.
- **Code splitting**: the bundler emits multiple chunks instead of one large bundle, so some code can load later.
- **Lazy loading**: the application delays loading code until a route, interaction, or condition actually needs it.

They are often discussed together because they both reduce shipped JavaScript, but they solve different problems.

| Technique | Main question | Typical tool |
| --- | --- | --- |
| Tree shaking | Can unused code be excluded from this bundle? | ESM static analysis + side-effect analysis |
| Code splitting | Can this code become a separate chunk? | route entries, `import()`, bundler config |
| Lazy loading | When should the user pay the network/parse cost? | `React.lazy`, `next/dynamic`, framework routing |

Important boundary: ECMAScript defines module syntax and dynamic import behavior. Tree shaking and chunk generation are bundler/framework behaviors, not language guarantees.

## 2. Why It Matters

JavaScript is not only downloaded. It is parsed, compiled, executed, cached, invalidated, and sometimes hydrated. A frontend can have fast API responses and still feel slow because the browser is busy processing unnecessary JavaScript.

This matters in production because:

- large initial bundles delay interactivity;
- heavy third-party libraries can dominate route cost;
- top-level module side effects can prevent safe dead-code removal;
- poorly chosen dynamic imports can create network waterfalls;
- too many tiny chunks can add request overhead and make loading feel jumpy;
- browser-only modules can break server rendering when imported too early.

Interviewers like this topic because it reveals whether you understand the chain from code structure -> build output -> browser work -> user experience.

## 3. Official Mechanism

### ECMAScript gives bundlers a static shape

Static `import` and `export` declarations must appear at the top level. They are parsed before module code evaluates. That static shape lets tools build a module graph.

```ts
// The bundler can see this dependency without running the program.
import { formatCurrency } from "./money";

export function renderPrice(value: number) {
  return formatCurrency(value);
}
```

Because the import is static, a bundler can ask:

- which module does this import point to?
- which binding is used?
- can an unused export be removed?
- is the imported module safe to skip if no used binding remains?

CommonJS is harder because `require()` is a runtime function call. Bundlers can optimize common patterns, but dynamic calls are fundamentally less predictable.

```js
// This can depend on runtime data, so static analysis is weaker.
const moduleName = process.env.FEATURE === "charts" ? "./charts" : "./table";
const view = require(moduleName);
```

See [[10 - Modules/02 - CommonJS|CommonJS]] for the Node-side mechanics.

### Tree shaking is conservative

A bundler cannot remove code merely because an export is unused if importing the module might change observable behavior.

```ts
// analytics.ts
console.log("analytics module loaded");
window.analyticsReady = true;

export function track(event: string) {
  window.analytics?.track(event);
}
```

Even if `track` is unused, importing this file runs top-level code. A production bundler must preserve that behavior unless it has enough information to prove it is safe to remove.

The common package-level signal is `sideEffects` in `package.json`.

```json
{
  "sideEffects": false
}
```

This says: if a module's exports are unused, dropping that module should not change observable behavior.

> [!warning] Side-effect imports can be shaken out — declare them
> Tree shaking assumes dropping an unused module changes nothing observable. Files whose import *is* the point — CSS, polyfills, global setup, custom-element registration — break that assumption and can be wrongly removed. Mark them via the package's `sideEffects` field so the bundler keeps them.

Some files really are side effects. CSS imports, polyfills, global setup, and custom element registration often must be listed explicitly.

```json
{
  "sideEffects": [
    "*.css",
    "./src/polyfills.ts",
    "./src/register-web-components.ts"
  ]
}
```

### Code splitting creates chunks

Bundlers create chunks from entry points and split points.

```ts
// Static import: usually part of the current route or shared chunk.
import { renderHeader } from "./header";

// Dynamic import: a runtime expression. Bundlers usually treat this as a split point.
const editorModule = await import("./RichTextEditor");
```

`import()` returns a Promise that resolves to the module namespace object. For bundlers, it also marks a place where the requested module can become a separate file loaded later.

## 4. Mental Model

Think of delivery in three budgets:

1. **Initial route budget**: code needed before the user can see or interact with the first screen.
2. **Interaction budget**: code needed after a user chooses a feature, tab, modal, editor, chart, or map.
3. **Cache budget**: code that changes often should not force users to re-download stable vendor code.

Tree shaking answers: "Can this code disappear?"

Code splitting answers: "Can this code wait?"

The mature question is not "Can I split everything?" It is "Which code is needed for this user's current task, and what loading experience do they get when the delayed code is requested?"

## 5. Real Frontend Example: Heavy Editor

Problem: an admin dashboard imports a rich text editor on the initial route. Only a small percentage of users click "Edit description", but everyone pays for the editor bundle.

### Failing version

```tsx
// ProductDetails.tsx
import RichTextEditor from "@/components/RichTextEditor";

export function ProductDetails({ product }: { product: Product }) {
  const [isEditing, setIsEditing] = useState(false);

  return (
    <section>
      <button onClick={() => setIsEditing(true)}>Edit description</button>

      {isEditing ? (
        // The editor is rendered only after the click,
        // but its code was already imported into the initial route bundle.
        <RichTextEditor initialValue={product.description} />
      ) : (
        <p>{product.description}</p>
      )}
    </section>
  );
}
```

Failure mode:

- the route's first-load JavaScript includes the editor;
- parse and execution cost increase before the user clicks edit;
- bundle analyzer shows the editor inside the route chunk.

### React fix with `lazy`

```tsx
import { Suspense, lazy, useState } from "react";

const RichTextEditor = lazy(() => import("@/components/RichTextEditor"));

export function ProductDetails({ product }: { product: Product }) {
  const [isEditing, setIsEditing] = useState(false);

  return (
    <section>
      <button onClick={() => setIsEditing(true)}>Edit description</button>

      {isEditing ? (
        <Suspense fallback={<div aria-busy="true">Loading editor...</div>}>
          {/* The editor chunk is requested only when this branch renders. */}
          <RichTextEditor initialValue={product.description} />
        </Suspense>
      ) : (
        <p>{product.description}</p>
      )}
    </section>
  );
}
```

Why it works:

- `lazy` expects a function that calls dynamic `import()`;
- React waits for the Promise and renders the nearest `Suspense` fallback;
- the bundler can emit the editor as a separate chunk.

Tradeoff:

- the initial route is lighter;
- the first edit interaction may wait for a network request;
- you need a real loading state and error handling strategy.

### Next.js fix with browser-only code

```tsx
import dynamic from "next/dynamic";

const RichTextEditor = dynamic(
  () => import("@/components/RichTextEditor"),
  {
    loading: () => <div aria-busy="true">Loading editor...</div>,
    ssr: false
  }
);

export function ProductDetails({ product }: { product: Product }) {
  return <RichTextEditor initialValue={product.description} />;
}
```

Use `ssr: false` only when the component genuinely depends on browser-only APIs during render or module initialization, such as `window`, selection APIs, canvas-only libraries, or DOM-measuring plugins. For normal components, keeping server rendering is usually better for first paint and SEO.

See [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]].

## 6. Real Frontend Bug: Barrel File Pulls Too Much

Problem: a route imports one component from a barrel file, but the barrel re-exports modules with side effects.

```ts
// components/index.ts
export { Button } from "./Button";
export { Modal } from "./Modal";
export { Chart } from "./Chart";
export { registerDesignSystem } from "./registerDesignSystem";

// Chart.tsx
import "chart-library/styles.css";
console.log("Chart module loaded");

export function Chart() {
  return <canvas />;
}
```

```tsx
// LoginPage.tsx
import { Button } from "@/components";

export function LoginPage() {
  return <Button>Sign in</Button>;
}
```

Bug:

- the login page only needs `Button`;
- the barrel makes the bundler inspect the whole export surface;
- side-effectful modules such as `Chart` can be retained;
- CSS or global setup may be included in an unrelated route.

Fix:

```tsx
// Direct import keeps the dependency surface explicit.
import { Button } from "@/components/Button";

export function LoginPage() {
  return <Button>Sign in</Button>;
}
```

Better barrel discipline:

```ts
// components/index.ts
export { Button } from "./Button";
export { Modal } from "./Modal";

// Keep heavy or side-effectful exports out of broad barrels.
// Import charts, editors, maps, and global setup directly at their usage site.
```

Checklist for barrels:

- keep top-level files side-effect-light;
- do not put global setup in general barrels;
- avoid re-exporting route components from shared component barrels;
- prefer direct imports inside components that live in the same folder;
- use bundle analysis when a route unexpectedly imports a large library.

See [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]] for another barrel-file failure mode.

## 7. Tree-Shaking-Friendly Exports

Named exports usually expose a clearer static surface than a default-exported utility object.

### Less friendly

```ts
// utils.ts
function formatCurrency(value: number) {
  return `$${value.toFixed(2)}`;
}

function formatDate(value: Date) {
  return value.toISOString().slice(0, 10);
}

function parsePhone(value: string) {
  return value.replace(/\D/g, "");
}

export default {
  formatCurrency,
  formatDate,
  parsePhone
};
```

```ts
import utils from "./utils";

console.log(utils.formatCurrency(42));
```

The bundler sees one object. Some optimizers can inline aggressively, but the object-property pattern makes the used surface less explicit.

### More friendly

```ts
// money.ts
export function formatCurrency(value: number) {
  return `$${value.toFixed(2)}`;
}

// dates.ts
export function formatDate(value: Date) {
  return value.toISOString().slice(0, 10);
}

// phone.ts
export function parsePhone(value: string) {
  return value.replace(/\D/g, "");
}
```

```ts
import { formatCurrency } from "./money";

console.log(formatCurrency(42));
```

Why it works better:

- the import names exactly which binding is used;
- unused modules can be removed when they are side-effect-free;
- refactors are safer because symbol names are explicit.

See [[10 - Modules/03 - Named vs Default Exports|Named vs Default Exports]].

## 8. Common Library Import Decisions

### Package entry points matter

```ts
// Often heavier if the package entry includes many features.
import _ from "lodash";

// More explicit. The final result depends on the package and bundler.
import debounce from "lodash/debounce";

// ESM build, commonly easier for bundlers to analyze.
import { debounce } from "lodash-es";
```

Do not memorize package-size folklore as a rule. Inspect the actual production bundle. Different package versions, bundlers, transpilation targets, and framework settings can change the result.

### Type-only imports matter in TypeScript

```ts
import type { Product } from "@/types/product";
import { formatCurrency } from "@/utils/money";

export function priceLabel(product: Product) {
  return formatCurrency(product.price);
}
```

Type-only imports document that the import is erased from runtime JavaScript. This reduces accidental runtime dependencies and makes module intent clearer.

## 9. Split Point Tradeoffs

Good split candidates:

- route-level code;
- modal content opened rarely;
- rich editors;
- dashboards with charting libraries;
- maps and geospatial libraries;
- admin-only panels;
- large syntax highlighters;
- expensive browser-only widgets.

Risky split candidates:

- tiny components used immediately above the fold;
- code needed by almost every route;
- core layout and navigation;
- validation logic needed before form interaction;
- modules that create waterfall chains of imports.

Tradeoff table:

| Decision | Benefit | Cost |
| --- | --- | --- |
| Split heavy editor | lower initial bundle | first editor open may wait |
| Split every component | many small files | request overhead and coordination cost |
| Keep vendor chunk stable | better caching | users may download broad shared code |
| Disable SSR for browser library | avoids `window is not defined` | weaker first render and SEO |
| Direct import instead of barrel | clearer dependency graph | longer import paths |

## 10. Debugging and Measurement

Use measurement before and after the change.

Things to inspect:

- route-level bundle size;
- initial JavaScript requested on first load;
- duplicated dependencies across chunks;
- chunk waterfalls after a click;
- parse/compile/execute time in the browser;
- Core Web Vitals impact, especially INP when heavy JS blocks interaction.

Practical tools:

- Next bundle analyzer or framework bundle report;
- webpack stats and analyzer tools;
- Chrome DevTools Network panel for chunk loading;
- Chrome DevTools Performance panel for long tasks;
- source-map explorer style tooling when source maps are available.

Debugging process:

1. Identify the route or interaction that feels slow.
2. Capture the current bundle/chunk output.
3. Find the largest unexpected modules.
4. Check whether they entered through a static import, barrel, side effect, or shared chunk.
5. Change one boundary at a time.
6. Rebuild in production mode and compare output.

Development builds often do not reflect production tree shaking or minification. Always verify with a production build before making a final claim.

## 11. Production Checklist

- [ ] Heavy libraries are not statically imported into routes that do not need them.
- [ ] Dynamic imports have loading UI and error handling.
- [ ] Browser-only modules are isolated from server render paths.
- [ ] Package `sideEffects` settings preserve CSS, polyfills, and global registration files.
- [ ] Utility modules use named exports where practical.
- [ ] Barrels are side-effect-light and do not hide large dependencies.
- [ ] Bundle analysis confirms the expected code moved or disappeared.
- [ ] Splitting does not create a worse interaction waterfall.
- [ ] The optimization is measured in a production build.

## 12. Interview Answer

**Short version:** Tree shaking removes unused code from a bundle. Code splitting creates separate chunks so some code can load later. Tree shaking depends heavily on static ESM structure and side-effect analysis; code splitting often comes from route entry points or dynamic `import()`.

**Deeper version:** Static ESM imports give bundlers a dependency graph before code runs. That lets the bundler mark which exports are used, then remove unused code if the module is safe to drop. The hard part is side effects: a module can change global state, register CSS, patch prototypes, or run setup at import time, so bundlers stay conservative unless package metadata and source structure prove removal is safe. Code splitting is different: a dynamic import or route entry can become a separate chunk fetched later. In React or Next.js, that usually means using `React.lazy`, `Suspense`, or `next/dynamic` with an intentional loading experience. The production tradeoff is smaller initial JavaScript versus delayed code loading and possible waterfalls.

**Strong follow-up:** "I would verify the change with a production bundle report and DevTools. I would also check whether the dependency entered through a barrel file, a CommonJS package, a top-level side effect, or a browser-only module imported on the server."

## 13. Common Mistakes

- Treating tree shaking as a language feature instead of a bundler optimization.
- Assuming named imports from any package guarantee only that function ships.
- Marking `"sideEffects": false` while the package imports CSS or runs global setup.
- Exporting a large default object and expecting precise dead-code elimination.
- Lazy-loading a component without a loading state.
- Using `ssr: false` as a general fix instead of isolating browser-only code intentionally.
- Splitting tiny components and creating more loading overhead than benefit.
- Measuring development builds and assuming the same output in production.
- Blaming React rendering when the real issue is a large JavaScript chunk blocking the main thread.

## 14. Practice

1. A Next.js route imports `import { Button } from "@/components"`, and the bundle includes a chart library. What three files would you inspect first?
2. Explain why `sideEffects: false` can improve tree shaking but can also break CSS imports if used carelessly.
3. Rewrite a default-exported `utils` object into tree-shaking-friendly named exports.
4. A user clicks "Open map" and waits two seconds. What network and performance signals tell you whether code splitting helped or hurt?
5. Explain why dynamic `import()` returns a Promise and how React `lazy` uses that Promise.
6. Give a 30-second interview answer that distinguishes tree shaking from code splitting.

## Related Notes

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/02 - CommonJS|CommonJS]]
- [[10 - Modules/03 - Named vs Default Exports|Named vs Default Exports]]
- [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]
- [[10 - Modules/05 - Live Bindings|Live Bindings]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[01 - Roadmap|Roadmap]]
