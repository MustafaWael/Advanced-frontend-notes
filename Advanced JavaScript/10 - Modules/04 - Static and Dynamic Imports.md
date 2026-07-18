---
tags: [javascript, modules, static-and-dynamic-imports]
module: "10 - Modules"
priority: must-know
status: not-started
---

# Static and Dynamic Imports

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can explain static imports, dynamic `import()`, namespace objects, top-level restrictions, and split points.
- Production signal: you load required code eagerly, optional heavy code lazily, and handle chunk failure/loading states.
- Dependencies: [[10 - Modules/01 - ES Modules|ES Modules]], [[08 - Async JavaScript/02 - Promises|Promises]]

## Source Anchors

- [MDN import](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/import)
- [MDN import()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import)
- [MDN JavaScript modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [React lazy](https://react.dev/reference/react/lazy)
- [Next.js Lazy Loading](https://nextjs.org/docs/app/guides/lazy-loading)
- [webpack Code Splitting](https://webpack.js.org/guides/code-splitting/)

## 1. Concept

Static imports are declarations:

```js
import { formatPrice } from "./format.js";
```

They are part of the module's static structure and are linked before evaluation.

Dynamic imports are expressions:

```js
const module = await import("./format.js");
```

They run at runtime and return a promise for the module namespace object.

## 2. Why It Matters

Static imports are best for code the module always needs. Dynamic imports are best for code needed only after a route, interaction, feature flag, or browser-only condition.

Frontend examples:

- load a rich text editor only when the edit modal opens
- load charting code only on analytics pages
- load browser-only code only on the client
- split rarely used admin features from the initial bundle
- conditionally load polyfills or adapters

## 3. Accurate Mechanism

Static `import`:

- appears only at module top level
- is resolved and linked before module evaluation
- is hoisted in the module sense
- gives bundlers a static graph
- cannot be wrapped in `if`, `try`, or a function

Dynamic `import()`:

- is an expression
- can appear inside functions and conditionals
- returns a promise
- resolves to a module namespace object
- often creates a code-splitting boundary in bundlers
- can fail if the chunk cannot load

## 4. Mental Model

Static import:

```txt
this module cannot run without that module
```

Dynamic import:

```txt
this code path may need that module later
```

## 5. Static Import Patterns

```ts
import { formatPrice } from "./format-price";
import type { Product } from "./types";

export function ProductLabel({ product }: { product: Product }) {
  return `${product.name} - ${formatPrice(product.price)}`;
}
```

Use static imports for:

- always-needed utilities
- components required for initial render
- types
- shared constants
- CSS or side-effect imports that must always run

## 6. Dynamic Import Patterns

```ts
async function openEditor() {
  const { default: Editor } = await import("./Editor");

  showModal(Editor);
}
```

The returned value is a module namespace object:

```js
const math = await import("./math.js");

console.log(math.add(2, 3));
console.log(math.default);
```

Default export is accessed through `.default`.

## 7. Real Frontend Bug: Heavy Library In Initial Bundle

### Problem

```tsx
import RichTextEditor from "./RichTextEditor";

function ArticlePage() {
  const [editing, setEditing] = useState(false);

  return (
    <>
      <ArticleBody />
      {editing ? <RichTextEditor /> : null}
    </>
  );
}
```

### Bug

> [!warning] Static imports ship whether or not the code runs
> A top-level `import` puts the module in the initial bundle even if most users never trigger it — a heavy editor/chart lands in everyone's first load. Split rarely-used, heavy features behind a dynamic `import()` / `React.lazy`, and handle chunk-load failure.

### Fix With React.lazy

```tsx
const RichTextEditor = lazy(() => import("./RichTextEditor"));

function ArticlePage() {
  const [editing, setEditing] = useState(false);

  return (
    <>
      <ArticleBody />
      {editing ? (
        <Suspense fallback={<EditorSkeleton />}>
          <RichTextEditor />
        </Suspense>
      ) : null}
    </>
  );
}
```

### Fix With Next.js

```tsx
import dynamic from "next/dynamic";

const RichTextEditor = dynamic(() => import("./RichTextEditor"), {
  loading: () => <EditorSkeleton />,
  ssr: false,
});
```

Use `ssr: false` only when the component truly depends on browser-only APIs or should not render on the server.

## 8. Dynamic Import Error Handling

Chunk loading can fail:

- user goes offline
- deployment changed chunk filenames while user has old HTML
- ad blockers/network policies block a chunk
- server/CDN returns an error

```ts
async function loadEditorSafely() {
  try {
    const { default: Editor } = await import("./RichTextEditor");
    return Editor;
  } catch (error) {
    reportError(error);
    showToast("Editor could not be loaded. Please retry.");
    return null;
  }
}
```

For React `lazy`, handle failures with an error boundary around the lazy component.

## 9. Static Import Cannot Be Conditional

Invalid:

```js
if (featureEnabled) {
  import { startFeature } from "./feature.js";
}
```

Valid:

```js
if (featureEnabled) {
  const { startFeature } = await import("./feature.js");
  startFeature();
}
```

## 10. Browser-Only Code

```js
async function loadBrowserOnlyChart() {
  if (typeof window === "undefined") {
    return null;
  }

  const { default: Chart } = await import("./Chart.js");
  return Chart;
}
```

This pattern prevents server code from evaluating modules that touch `window`, `document`, or browser-only libraries at top level.

## 11. Production Tradeoffs

- Static imports are simpler and better for required code.
- Dynamic imports reduce initial payload but add async states.
- Too much splitting can create many network requests and worse UX.
- Dynamic import paths should be analyzable by your bundler.
- Lazy-loaded code needs loading UI and error recovery.
- Server/client boundaries matter in frameworks such as Next.js.
- Measure production bundles; do not assume the split happened.

## Real-World Use Cases

### i18n locale files: dynamic paths the bundler can still analyze

A storefront supports 12 languages but each user needs one. A template literal with a static prefix and suffix lets the bundler enumerate every possible chunk at build time; a fully dynamic variable path cannot be split at all.

```ts
async function loadMessages(locale: string) {
  // bundler sees "./locales/*.json" and emits one chunk per file
  const messages = await import(`./locales/${locale}.json`);
  return messages.default;
}

// broken split: the bundler has no idea what `path` can be
const messages = await import(path); // bundles nothing / warns / inlines all
```

This works because `import()` is a runtime expression, but code splitting is a **build-time** decision — the bundler needs a statically analyzable path pattern to know which chunks to create.

> [!warning]
> Validate `locale` against a known list before interpolating. A user-controlled value in an import path is both a chunk-miss bug and a request-forgery surface.

### Prefetch on intent: warm the chunk before the click

The settings page is code-split behind a dynamic import, but users feel a 400ms stall on click. Firing the same `import()` on hover/focus starts the network fetch early; because the module registry caches by resolved specifier, the later "real" import resolves instantly.

```tsx
function SettingsLink() {
  const prefetch = () => { import("./SettingsPanel"); }; // fire-and-forget
  return (
    <button onMouseEnter={prefetch} onFocus={prefetch} onClick={openSettings}>
      Settings
    </button>
  );
}
```

Safe because a module is evaluated once per graph — repeated `import()` calls for the same specifier return the same promise/namespace, so hovering five times costs one fetch. See [[10 - Modules/01 - ES Modules|ES Modules]].

> [!tip]
> This is what `next/link` prefetching and `router.prefetch` do for routes; the manual version covers non-route splits like modals and panels.

### Feature-detected polyfill loading

An analytics dashboard uses `IntersectionObserver` for lazy-rendering rows, but a slice of traffic is on old WebViews. A conditional dynamic import loads the polyfill only for those users instead of taxing everyone's initial bundle.

```ts
export async function ensureObserverSupport() {
  if (!("IntersectionObserver" in window)) {
    await import("intersection-observer"); // side-effect module patches window
  }
}

await ensureObserverSupport();
startRowObserver();
```

Only `import()` can do this — static `import` cannot sit inside an `if` (section 9), so eager polyfilling would ship the code to 100% of users for the 2% who need it.

## 12. Interview Answer

**Short version:** Static imports are top-level module declarations linked before evaluation. Dynamic `import()` is a runtime expression that returns a promise for a module namespace object.

**Strong version:** Static imports give the engine and bundler a module graph before code runs, which supports linking, live bindings, and tree shaking. Dynamic imports run at runtime, can be conditional, and often become code-splitting points in bundlers. The result of `import()` is a promise resolving to a namespace object where named exports are properties and the default export is `.default`. In production, I use static imports for required code and dynamic imports for heavy or conditionally used code, while handling loading, errors, SSR constraints, and bundle verification.

## 13. Common Mistakes

- Trying to put static `import` inside an `if`.
- Forgetting dynamic `import()` returns a promise.
- Forgetting the default export is `.default` on the namespace object.
- Lazy-loading code without a loading state.
- Lazy-loading code without an error boundary or retry path.
- Using `ssr: false` as a general fix instead of understanding browser-only code.
- Assuming dynamic import always creates the split you expected without checking the bundle.

## 14. Practice

1. Convert a conditional static import into dynamic `import()`.
2. Load a named export and default export from a dynamic import.
3. Add error handling to a lazy-loaded editor.
4. Explain when `React.lazy` is enough and when Next `dynamic` is more appropriate.
5. Inspect a production bundle and confirm a heavy module split.

## Related Notes

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/03 - Named vs Default Exports|Named vs Default Exports]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[01 - Roadmap|Roadmap]]
