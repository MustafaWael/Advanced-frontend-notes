---
tags: [tooling, transpilation, babel, typescript]
module: "27 - Frontend Tooling and Build Systems"
priority: important
status: not-started
aliases: [Babel SWC esbuild, Syntax downleveling]
verified_on: 2026-07-17
version_scope: "TypeScript 5.x, Babel 7, SWC 1.x, esbuild 0.2x"
---

# Transpilation

## Maturity Target

- Priority: #important
- Study time: 35 minutes
- Interview signal: Explain what a transpiler does (parse → transform → print), why JSX and TS *require* one, the difference between syntax transforms and polyfills, and where Babel/SWC/esbuild differ.
- Production signal: You can configure targets via browserslist deliberately, and debug "works in dev, SyntaxError on old Android" class bugs.
- Dependencies: [[27 - Frontend Tooling and Build Systems/01 - Why Build Tools Exist|Why Build Tools Exist]]

## Source Anchors

- [Babel - How Babel works](https://babeljs.io/docs/)
- [TypeScript - tsconfig target](https://www.typescriptlang.org/tsconfig/#target)
- [browserslist](https://browsersl.ist/)

## 1. Concept

Simple version: a transpiler is a source-to-source compiler — it parses your code into an AST, transforms the tree, and prints new source. It lets you write modern/augmented syntax (TS, JSX, ES2024) while shipping code your oldest supported browser can parse.

The accurate mechanics, in three separations people blur:

**1. Syntax transform vs polyfill.** Transpilers rewrite *syntax* (`?.` → `a == null ? undefined : a.b`; arrow fn → `function`). They cannot invent *runtime features*: `Promise`, `structuredClone`, `Array.prototype.at` are library code that must be *polyfilled* (core-js, or served conditionally). A `SyntaxError` on old browsers = missing transform; a `TypeError: x is not a function` = missing polyfill.

**2. TS type-checking vs TS transpilation.** Stripping types is trivial and every fast tool does it (esbuild, SWC) — *without checking them*. Type *checking* is expensive and only `tsc` (or an IDE server) does it. Modern setups split the jobs: SWC/esbuild transpile per-file for speed; `tsc --noEmit` checks types in CI. Consequence: `isolatedModules` — each file must be transpilable alone, which is why `export type` exists and `const enum` is discouraged.

**3. The tools.**

- **Babel** — the extensible veteran: plugin ecosystem, `preset-env` reads **browserslist** and applies only the transforms your targets need. Slow (JS itself).
- **SWC** — Rust, Babel-compatible mental model, ~20× faster. Powers Next.js.
- **esbuild** — Go, bundler *and* transpiler, fastest; fewer niche transforms and no type checking. Powers Vite's dev-time transforms.

```tsx
// JSX is not JavaScript — no engine can parse it. This:
const el = <button onClick={fn}>Save</button>;
// must become (React 17+ automatic runtime):
import { jsx as _jsx } from "react/jsx-runtime";
const el = _jsx("button", { onClick: fn, children: "Save" });
```

`browserslist` (`"defaults", "not dead"`, or explicit versions) is the single contract shared by Babel, SWC, PostCSS/autoprefixer — one config that decides how much down-leveling and prefixing you ship.

## 2. Why It Matters

- "Why does JSX need a build step?" and "does esbuild check my types?" are direct interview questions; the type-check/transpile split trips up many mid-levels.
- Shipping over-transpiled code is a silent perf tax: compiling async/await down to generator-state-machines for browsers you don't support bloats bundles and slows execution. Targets should reflect *your actual users*.
- Every "SyntaxError: Unexpected token" from a user's ancient WebView is this note.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: CI is green, types pass in the editor — yet production crashes with `ReferenceError` from a file that "shouldn't even compile."

```ts
// utils.ts
export const config = { retries: 3 };
export type Config = typeof config;

// consumer.ts
import { Config, config } from './utils';   // mixes a type and a value
```

Trace: the build uses esbuild, which strips types *per file without checking*. It must decide syntactically what `Config` is; with certain configs/imports the type import survives or a value import gets elided wrongly — and any real type *errors* elsewhere ship to production because nothing type-checks in the pipeline. The team assumed "it built" meant "it checked."

```ts
// Fix 1: make type-only imports explicit (isolatedModules-safe)
import { config } from './utils';
import type { Config } from './utils';

// Fix 2: put checking back in the pipeline
// package.json: "typecheck": "tsc --noEmit"  → run in CI alongside the build
// tsconfig: "isolatedModules": true, "verbatimModuleSyntax": true
```

Tradeoffs: running `tsc --noEmit` adds CI time (it's the slow part you removed) — but in parallel with the build, not blocking it. `verbatimModuleSyntax` forces explicit `import type`, minor ceremony for deterministic emit.

> [!warning] Footgun: "esbuild/SWC compiled my TypeScript" never means "my TypeScript is type-correct." If nothing runs `tsc --noEmit`, your types are decoration.

## 4. Interview Answer

Short answer:

> A transpiler parses source to an AST, transforms it, and prints JavaScript that your target browsers can parse — that's how JSX and TypeScript, which no engine understands, become runnable, and how modern syntax gets down-leveled. Two key distinctions: transpilers handle *syntax*, while missing runtime APIs need *polyfills*; and fast tools like esbuild and SWC strip TypeScript types without checking them — type checking is tsc's separate job, usually run in CI.

Deeper answer:

> The ecosystem splits by speed and role: Babel is the extensible standard with preset-env driven by browserslist; SWC is its Rust-speed equivalent inside Next.js; esbuild is Go, powers Vite's transforms, fastest but less extensible. Browserslist is the shared contract deciding transform depth and autoprefixing — over-broad targets are a real bundle-size and runtime tax. Per-file transpilation imposes isolatedModules constraints: explicit `import type`, no `const enum`, because the transpiler can't see across files the way tsc can.

## 5. Practice

1. <details><summary>Old Android WebView: one user gets `SyntaxError: Unexpected token '?'`, another gets `TypeError: navigator.clipboard.writeText is not a function`. Diagnose both.</summary>First: optional chaining syntax wasn't transpiled — the parser itself fails; fix targets/browserslist. Second: syntax parsed fine but a runtime API is missing — needs a polyfill or feature detection. Syntax error = transform gap; type error at runtime = polyfill gap.</details>
2. <details><summary>Why can't esbuild catch `const n: number = "hi"`?</summary>It doesn't build a type system — it tokenizes and strips type annotations per file for speed. Checking assignability requires whole-program type analysis, which is tsc's job (`tsc --noEmit` in CI).</details>
3. <details><summary>What does `browserslist` actually control, and what happens if you set it to `last 1 chrome version` for a public app?</summary>It's the shared target contract for Babel/SWC (which syntax transforms run), autoprefixer (CSS prefixes), and polyfill selection. Setting it that narrow ships nearly-untransformed code — smallest and fastest bundles, but hard SyntaxError crashes for every user outside latest Chrome.</details>

## Related Notes

- [[27 - Frontend Tooling and Build Systems/01 - Why Build Tools Exist|Why Build Tools Exist]]
- [[23 - TypeScript Deep Dive/00 - TypeScript Deep Dive MOC|TypeScript Deep Dive MOC]]
- [[27 - Frontend Tooling and Build Systems/04 - Vite Mental Model|Vite Mental Model]]
