---
tags: [tooling, bundlers, build, moc]
module: "27 - Frontend Tooling and Build Systems"
priority: important
status: not-started
---

# Frontend Tooling and Build Systems MOC

This module explains the machinery between the code you write and the code browsers run: why build tools exist at all, what transpilers do, and how Webpack and Vite think. It builds directly on [[10 - Modules/00 - Modules MOC|Modules]] — bundlers are meaningless until you know why module systems evolved. After it, "how does Vite work?" and "what does your build actually produce?" have mechanical answers, and build failures become debuggable instead of mystical.

## Prerequisites

- [[10 - Modules/00 - Modules MOC|Modules MOC]] — ESM/CJS and the module graph are assumed throughout.
- [[10 - Modules/09 - From Source to Browser|From Source to Browser]] — the narrative bridge this module expands.

## Reading Order

1. [[27 - Frontend Tooling and Build Systems/01 - Why Build Tools Exist|Why Build Tools Exist]] — the problem timeline from script tags to module graphs.
2. [[27 - Frontend Tooling and Build Systems/02 - Transpilation|Transpilation]] — Babel, SWC, esbuild; targets and browserslist.
3. [[27 - Frontend Tooling and Build Systems/03 - Webpack Mental Model|Webpack Mental Model]] — entry, graph, loaders, plugins, chunks.
4. [[27 - Frontend Tooling and Build Systems/04 - Vite Mental Model|Vite Mental Model]] — native-ESM dev server, esbuild pre-bundling, Rollup builds.
5. [[27 - Frontend Tooling and Build Systems/05 - Production Build Concerns|Production Build Concerns]] — minification, source maps, hashing, env vars, analysis.
6. [[27 - Frontend Tooling and Build Systems/06 - Frontend Tooling Checklist|Frontend Tooling Checklist]] — active self-test.

## You're Done When

- [ ] I can tell the history as a chain of problems: globals → IIFEs → CJS → bundling → ESM → modern hybrid tools.
- [ ] I can separate transpilation from bundling from minification, and name who does what.
- [ ] I can explain Webpack's dependency graph, loaders vs plugins, and chunking.
- [ ] I can explain why Vite's dev server is fast (native ESM + esbuild pre-bundling) and why prod still bundles (Rollup).
- [ ] I can describe a production build's outputs: hashed chunks, source maps, and inlined env vars — and their caching/security implications.

## Related Notes

- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[26 - How the Web Works/03 - Connection Layer|Connection Layer]] — why HTTP/2+ changed bundling strategy.
- [[22 - Next.js Deep Dive/00 - Next.js Deep Dive MOC|Next.js Deep Dive MOC]] — the framework layer on top of these tools.
- [[01 - Roadmap|Roadmap]]
