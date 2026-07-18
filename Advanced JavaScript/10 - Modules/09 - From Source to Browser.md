---
tags: [javascript, modules, tooling, bundlers]
module: "10 - Modules"
priority: important
status: not-started
aliases: [Transpilers, Polyfills, Source Maps]
---

# From Source to Browser

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain transpilers vs polyfills, what "supports ES2020" really means, browserslist, source maps, and compare bundlers at overview depth.
- Production signal: you reason about what ships to users — syntax level, polyfill weight, bundle size — instead of treating the build as a black box.
- Dependencies: [[10 - Modules/01 - ES Modules|ES Modules]], [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]

## Source Anchors

- [MDN - JavaScript modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
- [Babel - What is Babel?](https://babeljs.io/docs/)
- [web.dev - Serve modern code to modern browsers](https://web.dev/articles/serve-modern-code-to-modern-browsers)
- [MDN - Source maps](https://developer.mozilla.org/en-US/docs/Web/API/CSSStyleSheet/href#source_maps)
- [Browserslist](https://github.com/browserslist/browserslist)

## 1. Concept

The code you write is not the code that runs. Between your `.ts`/`.jsx` source and the browser sits a build pipeline that does three conceptually distinct things:

1. **Transpile** — transform *syntax* the target can't parse into equivalent older syntax (JSX → `React.createElement`, `async/await` → state machines for old targets, optional chaining → conditionals). Tools: Babel, SWC, TypeScript, esbuild.
2. **Polyfill** — provide *runtime features* (APIs/methods) that don't exist in the target, by shipping an implementation (`Promise`, `Array.prototype.flat`, `fetch`, `Object.fromEntries`). Tools: core-js, whatwg-fetch.
3. **Bundle** — resolve the module graph ([[10 - Modules/01 - ES Modules|ESM]]/[[10 - Modules/02 - CommonJS|CJS]]), tree-shake, code-split, and emit optimized files. Tools: webpack, Vite (Rollup + esbuild), esbuild, Turbopack.

## 2. Why It Matters

- What actually reaches users — the syntax level, the polyfill payload, the bundle size — is a performance and compatibility decision the build encodes. "Supports ES2020" and "our bundle is 800KB" are things a senior must be able to reason about and control.
- The transpile-vs-polyfill distinction is a precise interview question that separates people who understand the toolchain from people who "just run the build."

## 3. Transpile vs Polyfill — The Key Distinction

They solve different problems:

- **Syntax** can only be *transpiled* — a browser that can't parse `a?.b` chokes at parse time before any code runs, so a polyfill (which is runtime code) can't help. The transpiler rewrites it to `a == null ? undefined : a.b`.
- **Features/APIs** can only be *polyfilled* — `Array.prototype.flat` is a method that must *exist* at runtime; no syntax transform creates it. You ship an implementation that defines it if missing.

```js
// Syntax (transpiled): the ?? operator itself
const x = a ?? b;              // → var x = a !== null && a !== undefined ? a : b;

// Feature (polyfilled): the method must exist at runtime
[1, [2]].flat();              // needs core-js to define Array.prototype.flat on old engines
```

So `async/await` needs *both* on old targets: transpilation of the syntax **and** a `Promise` polyfill for the runtime primitive it compiles to.

## 4. "Supports ES2020" and browserslist

**browserslist** is the shared config (in `package.json` or `.browserslistrc`) that names your target browsers (`"> 0.5%, last 2 versions, not dead"`). Babel/SWC (via preset-env), autoprefixer, and core-js all read it to decide *how much* to transpile and *which* polyfills to include. Narrow targets (modern browsers) → less transpilation, smaller output, faster code; wide targets (old browsers) → more transforms, more polyfills, bigger and slower.

"Supports ES2020" is ambiguous precisely because of the transpile/polyfill split: a browser "supporting ES2020" means it can *parse and run* ES2020 syntax and has ES2020 built-ins natively — so you don't need to transpile that syntax or polyfill those APIs for it. But your build targets a *set* of browsers; the output is the lowest common denominator unless you ship differential bundles.

> [!tip] Differential serving: modern + legacy bundles
> Instead of shipping heavily-transpiled, polyfill-laden code to everyone, serve two builds: `<script type="module">` (modern, minimal transforms — modern browsers pick this) and `<script nomodule>` (legacy, fully transpiled — old browsers pick this, modern ones ignore it). Modern users get smaller, faster code; legacy users still work. Vite and Next.js do this automatically. Knowing the pattern signals you think about the payload, not just correctness.

## 5. Source Maps

Because the shipped code is transformed (transpiled, minified, bundled), a stack trace points at `main.abc123.js:1:48213`, useless for debugging. **Source maps** are a separate file mapping generated positions back to original source lines, so DevTools and error trackers (Sentry) show *your* code and readable stacks.

Tradeoff: source maps must be generated (build cost) and either served (exposes source — fine for open code, risky for proprietary) or uploaded privately to your error tracker (the common production choice — keep them off the public server, give Sentry the map). Never ship no source maps to production error tracking, or every stack trace is minified gibberish.

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a bundle is 900KB and slow on modern browsers; investigation shows it targets IE11 that no analytics user runs.

Buggy setup:

```jsonc
// package.json — over-broad target inherited from an old template
"browserslist": ["> 0.1%", "ie 11"]
```

Trace: `ie 11` forces preset-env to transpile *everything* to ES5 (bloated, slower `async/await` state machines, no native classes) and pull in a large core-js polyfill set — shipped to *all* users including modern-browser ones who need none of it. The bundle is big and the code is slower than the source would run natively, for a browser no real user uses.

Production-safe fix — target real users, serve differentially:

```jsonc
"browserslist": ["defaults", "not dead"]   // realistic modern baseline
```

Plus module/nomodule differential serving (automatic in Vite/Next). Result: modern browsers get lean, near-source code; the polyfill payload shrinks dramatically; the rare old browser still gets a working legacy bundle.

Tradeoffs: verify your actual audience (analytics/CrUX) before narrowing — dropping a browser class is a product decision, not just a build tweak. Differential serving adds build complexity and two artifacts. And some polyfills are unavoidable if you use the APIs — the lever is *targeting real browsers* and *serving modern code to modern browsers*, not removing needed polyfills. Also confirm SWC/esbuild (faster, Rust/Go-based) vs Babel (more plugins/ecosystem) suits your transforms — Next.js defaults to SWC for speed.

## 7. Interview Answer

Short answer:

> The build does three distinct jobs: transpiling *syntax* the target can't parse (JSX, optional chaining → older equivalents), polyfilling *runtime features* that don't exist (`Promise`, `Array.flat` → shipped implementations), and bundling (resolve modules, tree-shake, split). Syntax can only be transpiled; features can only be polyfilled — `async/await` on old targets needs both. browserslist drives how much of each you do.

Deeper answer:

> "Supports ES2020" means a browser natively parses that syntax and has those built-ins, so you needn't transpile/polyfill for it — but your output targets a *set* of browsers, so it's the lowest common denominator unless you serve modern/legacy bundles differentially (module/nomodule). Over-broad browserslist targets (e.g., IE11) inflate bundle size and slow the code for everyone; targeting real users plus differential serving is the fix. Source maps map minified stacks back to source for debugging — uploaded privately to error trackers in production. Bundler choice (esbuild/SWC for speed, webpack/Rollup for ecosystem) rounds out the pipeline.

## 8. Practice

1. <details><summary>Can a polyfill make `const x = a?.b` work in a browser that doesn't support optional chaining? Why or why not?</summary>No. `?.` is *syntax*; a browser that doesn't support it fails at parse time — before any polyfill code could run — with a SyntaxError. Only transpilation (rewriting `a?.b` to `a == null ? undefined : a.b`) helps. Polyfills add runtime *features* (missing methods/objects) to code that already parses; they can't fix unparseable syntax.</details>

2. <details><summary>Which need transpiling, which need polyfilling: arrow functions, `Promise`, `Array.prototype.at`, `async/await`, `structuredClone`?</summary>Transpile (syntax): arrow functions, `async/await` (also needs a Promise polyfill for the runtime target). Polyfill (feature/API): `Promise`, `Array.prototype.at`, `structuredClone` — these are runtime objects/methods that must exist. `async/await` is the dual case: transpile the syntax and ensure the `Promise` primitive it lowers to exists.</details>

3. <details><summary>Why does adding `ie 11` to browserslist slow down code for Chrome users, and how do you avoid it?</summary>preset-env transpiles to the lowest target: `ie 11` forces ES5 output (slower async state machines, no native classes) and a large core-js polyfill bundle, shipped to *all* users including Chrome, which would run the modern source faster and needs none of the polyfills. Avoid it by targeting real browsers (drop IE11 if analytics justify it) and using module/nomodule differential serving so modern browsers download lean modern code and only legacy browsers get the transpiled/polyfilled bundle.</details>

4. <details><summary>Your production error tracker shows `main.js:1:88213` for every crash. What's missing and what's the safe setup?</summary>Source maps aren't available to the error tracker, so it can't map minified positions back to your original code. Safe setup: generate source maps in the production build but don't serve them publicly (to avoid exposing proprietary source); instead upload them privately to the error tracker (e.g., Sentry) during CI, so it symbolicates stack traces to readable file/line/function while the public server ships only the minified bundle (optionally without the `//# sourceMappingURL` comment or with it pointing to a protected location).</details>

## Related Notes

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[20 - Network and Security/07 - Prototype Pollution and Supply-Chain Basics|Prototype Pollution and Supply-Chain Basics]]
- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[01 - Roadmap|Roadmap]]
