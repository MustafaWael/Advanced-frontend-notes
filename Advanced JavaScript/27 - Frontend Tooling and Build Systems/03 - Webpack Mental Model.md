---
tags: [tooling, bundlers, webpack]
module: "27 - Frontend Tooling and Build Systems"
priority: important
status: not-started
aliases: [Webpack, How Webpack works]
verified_on: 2026-07-17
version_scope: "Webpack 5"
---

# Webpack Mental Model

## Maturity Target

- Priority: #important
- Study time: 40 minutes
- Interview signal: Explain Webpack in its own vocabulary — entry, dependency graph, loaders, plugins, chunks, runtime — and how a change flows through to output files.
- Production signal: You can open a legacy webpack.config.js and predict what it produces; you can fix "loader not found for this file type" and chunk-bloat issues without stackoverflow-roulette.
- Dependencies: [[27 - Frontend Tooling and Build Systems/01 - Why Build Tools Exist|Why Build Tools Exist]]

## Source Anchors

- [Webpack - Concepts](https://webpack.js.org/concepts/)
- [Webpack - Under the hood](https://webpack.js.org/concepts/under-the-hood/)
- [Webpack - SplitChunksPlugin](https://webpack.js.org/plugins/split-chunks-plugin/)

## 1. Concept

Simple version: Webpack starts at your entry file, recursively follows every `import`/`require` to build a dependency graph, converts each file into a *module* via loaders, and emits the graph as one or more *chunks* (output files) stitched together by a small runtime.

The accurate vocabulary — each term is an interview checkpoint:

- **Entry** — graph root(s). Multiple entries = multiple graphs (e.g., app + admin).
- **Module** — any file in the graph. Webpack's core only understands JS/JSON; *everything is a module* is achieved by…
- **Loaders** — per-file transformers, applied right-to-left, that turn arbitrary content into modules: `ts-loader`/`babel-loader` (TS/JSX → JS), `css-loader` (CSS → JS module), `asset modules` (images → URLs). Loaders answer "how do I *import* this file type?"
- **Plugins** — hook into the whole compilation lifecycle, beyond per-file: `HtmlWebpackPlugin` (emit HTML with injected tags), `MiniCssExtractPlugin` (pull CSS out of JS into .css files), `DefinePlugin` (compile-time constants). Loaders transform files; plugins orchestrate the build. That one-liner distinction is a classic question.
- **Chunks** — groups of modules emitted as files. Three origins: entry chunks, **async chunks** (every `import()` creates a split point — [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]), and `splitChunks` optimization (extract shared/vendor code).
- **Runtime** — the injected glue: a module registry, `__webpack_require__`, and the chunk-loading logic that fetches async chunks and resolves the `import()` promise.
- **Module Federation** (v5) — chunks loaded from *other deployed builds* at runtime; the micro-frontend mechanism.

```js
// webpack.config.js — minimal, annotated
module.exports = {
  entry: './src/index.tsx',
  module: {
    rules: [
      { test: /\.tsx?$/, use: 'swc-loader' },              // loader: file → JS
      { test: /\.css$/, use: ['style-loader', 'css-loader'] }, // right-to-left!
    ],
  },
  plugins: [new HtmlWebpackPlugin({ template: 'index.html' })],
  output: { filename: '[name].[contenthash].js', clean: true },
  optimization: { splitChunks: { chunks: 'all' } },        // vendor extraction
};
```

## 2. Why It Matters

- Webpack still runs a huge share of production apps (and underlies older Next.js, CRA legacies) — "can you read a webpack config" is a real day-one job skill.
- Its vocabulary became *the* shared language of bundling: Vite/Rollup/Turbopack docs all define themselves relative to these concepts.
- Chunking decisions made here directly drive caching and load performance ([[20 - Network and Security/02 - HTTP Caching|HTTP Caching]], [[26 - How the Web Works/03 - Connection Layer|Connection Layer]]).

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: "the settings page is visited by 5% of users, but its charting library loads for everyone — LCP on the home page suffers."

```ts
// Buggy: static import puts the 300KB lib into the shared graph
import { HeavyChart } from './charts';        // pulled into main chunk
export function SettingsPage() { return <HeavyChart />; }
```

Trace: static `import` is a graph edge — Webpack must include `./charts` in a chunk that's loaded before any importer runs. Since `SettingsPage` sits in the main route bundle, the chart lib lands in the entry chunk. Everyone pays for it.

```tsx
// Fix: dynamic import = split point (framework wrapper: React.lazy)
const HeavyChart = React.lazy(() => import('./charts'));
export function SettingsPage() {
  return (
    <Suspense fallback={<Skeleton />}>
      <HeavyChart />
    </Suspense>
  );
}
```

Webpack sees `import()` and emits `charts.[hash].js` as an async chunk; the runtime fetches it on first render of Settings. Entry chunk shrinks by 300KB.

Tradeoffs: the settings user now pays a network round trip at click time (mitigate: prefetch on hover/`/* webpackPrefetch: true */`); more chunks = more requests (cheap under HTTP/2+, [[26 - How the Web Works/03 - Connection Layer|Connection Layer]]); Suspense fallback flashes need design. Split by route by default, by component only when heavy.

> [!warning] Footgun: `[contenthash]` in filenames without also extracting a stable runtime/vendor chunk means one line of app code can cascade hash changes through every chunk (the runtime's chunk manifest changes). `optimization.runtimeChunk: 'single'` + sane splitChunks keeps vendor hashes stable across app-only deploys.

## 4. Interview Answer

Short answer:

> Webpack builds a dependency graph starting from the entry, following every import. Loaders convert non-JS files into modules — that's how CSS or images become importable — while plugins hook into the whole compilation for things like HTML emission or CSS extraction. The graph is emitted as chunks: entry chunks, async chunks created by every dynamic import(), and shared chunks extracted by splitChunks. A small injected runtime wires module resolution and async chunk fetching at runtime.

Deeper answer:

> The distinctions that signal depth: loaders are per-file transforms applied right-to-left, plugins are lifecycle hooks over the compilation object; `import()` is both a language feature and a bundler directive creating a split point; content-hashed filenames enable immutable caching but require a separated runtime chunk to keep hashes stable. Webpack 5 added Module Federation — runtime-loaded chunks from independently deployed builds — which is the standard micro-frontend answer.

## 5. Practice

1. <details><summary>Loaders vs plugins — one sentence each, and one example each.</summary>A loader transforms individual files as they enter the graph ("how to import this file type") — e.g., css-loader; a plugin hooks into the compilation lifecycle to affect the build as a whole — e.g., HtmlWebpackPlugin emitting the HTML shell.</details>
2. <details><summary>What exactly happens, at build time and runtime, when Webpack encounters `import('./x')`?</summary>Build time: `./x` and its subgraph are emitted as a separate async chunk, and the call site compiles to a runtime chunk-load. Runtime: `__webpack_require__.e` injects a script tag for the chunk (deduped, cached), the chunk registers its modules, and the promise resolves with the module's exports.</details>
3. <details><summary>You change one string in app code and every user re-downloads the 400KB vendor chunk. Why, and what's the fix?</summary>The runtime manifest (chunk-name → hash map) lives in a chunk whose hash changed, cascading into others — or vendor and app code share a chunk. Fix: `runtimeChunk: 'single'`, splitChunks to isolate node_modules into a vendor chunk, so app-only changes leave the vendor hash untouched.</details>

## Related Notes

- [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[27 - Frontend Tooling and Build Systems/04 - Vite Mental Model|Vite Mental Model]]
- [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]
