---
tags: [tooling, bundlers, checklist]
module: "27 - Frontend Tooling and Build Systems"
priority: important
status: not-started
---

# Frontend Tooling Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, predict, debug, and refactor without looking.

## Source Anchors

- [Webpack - Concepts](https://webpack.js.org/concepts/)
- [Vite - Why Vite](https://vite.dev/guide/why.html)
- [Babel - Docs](https://babeljs.io/docs/)

## Why Build Tools Exist

- [ ] I can tell the problem chain: globals → IIFE → CJS/npm → bundlers-as-adapters → ESM → bundlers-as-optimizers.
- [ ] I can give two concrete reasons production apps still bundle despite native browser ESM.
- [ ] I can explain bare specifiers, import maps, and the request-waterfall problem.

## Transpilation

- [ ] I can describe the parse → transform → print pipeline and why JSX/TS require it.
- [ ] I can separate syntax transforms from polyfills and diagnose SyntaxError vs TypeError accordingly.
- [ ] I can explain the type-check/transpile split: esbuild/SWC strip, only tsc checks — and the isolatedModules consequences (`import type`).
- [ ] I can explain what browserslist controls and the cost of wrong targets in both directions.

## Webpack

- [ ] I can define entry, module, loader, plugin, chunk, and runtime — and the loaders-vs-plugins one-liner.
- [ ] I can explain what `import()` does at build time and at runtime.
- [ ] I can fix a hash-cascade problem with runtimeChunk and splitChunks.

## Vite

- [ ] I can explain why dev startup is O(1) in app size: native ESM, on-demand per-file transforms.
- [ ] I can explain dependency pre-bundling: why deps only, esbuild flattening, specifier rewriting, the `.vite` cache.
- [ ] I can describe HMR propagation and React Fast Refresh's accept-boundary rules (component-only exports).
- [ ] I can name why dev/prod divergence exists (esbuild vs Rollup pipelines) and how `vite preview` mitigates it.

## Production Builds

- [ ] I can distinguish minification from compression and explain why both apply.
- [ ] I can state the caching recipe: immutable hashed assets + always-revalidated HTML — and why each half is required.
- [ ] I can explain hidden source maps and the public-env-var leak class.
- [ ] I can diagnose and fix ChunkLoadError after deploys (asset retention + graceful reload).
- [ ] I can run a bundle analysis and describe what I'd act on.

## Exit Test

- [ ] Explain to a junior why `npm run dev` works but their code throws SyntaxError on a client's old tablet.
- [ ] Given a legacy webpack.config.js, narrate what it emits without running it.
- [ ] Answer "why is Vite faster than Webpack?" with architecture first, esbuild second.
- [ ] Design the deploy story for a code-split SPA: caching headers, old-asset retention, chunk-error recovery.

## Related Notes

- [[27 - Frontend Tooling and Build Systems/00 - Frontend Tooling and Build Systems MOC|Frontend Tooling and Build Systems MOC]]
- [[10 - Modules/08 - Modules Checklist|Modules Checklist]]
- [[01 - Roadmap|Roadmap]]
