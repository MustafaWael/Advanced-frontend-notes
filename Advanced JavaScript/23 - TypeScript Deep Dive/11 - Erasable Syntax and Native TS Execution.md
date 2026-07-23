---
tags: [typescript, tooling, transpilation, node]
module: "23 - TypeScript Deep Dive"
priority: important
status: not-started
aliases: [erasableSyntaxOnly, type stripping, strip-only mode, enum namespace parameter properties]
verified_on: 2026-07-22
version_scope: "TypeScript 5.8+, Node 24 LTS/25/26 (type stripping stable; transform flag removed in v26)"
---

# Erasable Syntax and Native TS Execution

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: explain that `tsc` does two independent jobs (check vs emit), which TypeScript syntax is *erasable* vs which emits runtime code, and why Node can run `.ts` files directly but rejects `enum`.
- Production signal: you choose greenfield defaults (`as const` over `enum`, `erasableSyntaxOnly`) that keep code compatible with strip-only runtimes, and you know why the bundler never checks your types.
- Dependencies: [[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|Modules, tsconfig and Package Types]], [[27 - Frontend Tooling and Build Systems/02 - Transpilation|Transpilation]]

## Source Anchors

- [TypeScript: erasableSyntaxOnly](https://www.typescriptlang.org/tsconfig/erasableSyntaxOnly.html)
- [TypeScript: verbatimModuleSyntax](https://www.typescriptlang.org/tsconfig/verbatimModuleSyntax.html)
- [TypeScript: isolatedModules](https://www.typescriptlang.org/tsconfig/isolatedModules.html)
- [Node.js: Running TypeScript natively](https://nodejs.org/api/typescript.html)
- [Node.js type stripping explained — Marco Ippolito](https://satanacchio.hashnode.dev/everything-you-need-to-know-about-nodejs-type-stripping)

## 1. Concept

`tsc` is two tools wearing one binary, and separating them removes most confusion:

1. **Type checking** — reads the whole program, builds a cross-file type graph, reports errors. **Produces no output.** Babel/SWC/esbuild have no equivalent to this at all.
2. **Emitting** — takes source, targets an older JS version, rewrites syntax. This *is* the same job as Babel ([[27 - Frontend Tooling and Build Systems/02 - Transpilation|Transpilation]]).

Most TypeScript syntax is **erasable** — deleted at emit with zero runtime trace. A small set is **non-erasable** — it stands for runtime code TypeScript invented, so it cannot simply be deleted.

```ts
// erasable — vanishes
const n: number = 1;               // → const n = 1;
interface User { id: string }      // → (nothing)
type Id = string;                  // → (nothing)
function f<T>(x: T): T { return x } // → function f(x) { return x }

// NON-erasable — emits real runtime code
enum Color { Red, Blue }           // → a runtime object with reverse maps
namespace Utils { export const x = 1 } // → a runtime IIFE
class A { constructor(private x: number) {} } // → this.x = x
```

## 2. Why It Matters

The erasable/non-erasable split stopped being trivia the moment single-file transpilers and native runtimes took over:

- **Bundlers strip types per-file.** SWC (Next.js), esbuild (Vite), and `@babel/preset-typescript` delete types file-by-file with **zero cross-file knowledge and zero type checking**. Your build does not check your types.
- **Node runs `.ts` directly** by *stripping only* — and refuses non-erasable syntax outright.
- Non-erasable features (`enum`, `namespace`, parameter properties) need whole-program transformation, which none of the fast tools do. The ecosystem converged on "write erasable-only code."

## 3. Official Mechanism

Three distinct ways TypeScript syntax reaches a runtime:

| Tool | What it does with types | Checks types? | Non-erasable syntax |
|---|---|---|---|
| `tsc` emit (`target: ES5`…) | downlevels + strips | ✅ (separately) | ✅ generates runtime code |
| Bundler (SWC/esbuild/Babel) | strips per file | ❌ | ✅ transforms (full mode) |
| Node native / `--strip-only` | **deletes only** | ❌ | ❌ **SyntaxError** |

Node erases by **replacing type syntax with whitespace**, keeping byte offsets identical so line numbers and stack traces stay correct without source maps. That trick only works for syntax whose removal changes nothing — which is exactly why non-erasable features break it.

```ts
// user.ts
enum Role { Admin, User }
console.log(Role.Admin);
```
```txt
$ node user.ts
ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX: TypeScript enum is not supported ...
```

It does not erase it (that would delete a real object your code calls) and it does not inject the replacement (stripping has no code generator). It **refuses** with `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` — the third option most people don't expect.

> [!warning] No built-in escape hatch since Node 26
> Node 22.7 shipped an experimental `--experimental-transform-types` flag that *did* generate the runtime code (enum/namespace/parameter properties), but **Node 26.0.0 removed it**. Native Node is now strip-only, period — there is no flag that makes it run non-erasable syntax. For full TypeScript support you use a third-party runner (`tsx`, `node --import=tsx`), a real build step (`tsc`, esbuild, SWC), or a runtime that transforms rather than strips (Bun, Deno). Node also ignores `tsconfig.json` entirely during stripping.

## 4. Mental Model

> `tsc` and Babel **compile**. Node **deletes**.

If the syntax is only information for the type checker, Node erases it and runs the result as-is. If the syntax stands for runtime code, Node refuses. There is no `target` in stripping — no `async`→generator downleveling, no polyfills. Whatever your Node version already supports is what you get; "Node runs TypeScript" does strictly less than `tsc`.

## 5. Erasable vs Non-Erasable

| Syntax | Native Node / strip-only |
|---|---|
| type annotations, `interface`, `type`, generics, `as`, `satisfies` | ✅ erased |
| `import type` / `export type` | ✅ erased |
| `enum` (and `const enum`) | ❌ `ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX` |
| `namespace` with runtime members | ❌ error |
| parameter properties (`constructor(private x)`) | ❌ error |
| import aliases (`import Foo = require(...)`) | ❌ error |
| decorators (`@Component`) | ❌ parser error (TC39 Stage 3, not transformed) |

`class`, `#private` fields, and **type-only** `namespace` (exports only types) are **not** in the non-erasable set (see below) and run fine.

## 6. The Three "private"s

`class` itself is plain ECMAScript (ES2015) — TypeScript adds nothing. Only the TS-specific bits inside a class matter, and "private" is three different things:

```ts
class User {
  constructor(private a: string) {}  // ① parameter property   → ❌ SyntaxError
  private b: string = "x";           // ② TS visibility modifier → ✅ erased (no runtime privacy)
  #c = "y";                          // ③ ECMAScript private field → ✅ real runtime privacy
}
```

- **① Parameter property** is sugar for "declare a field and assign it" — it *emits* `this.a = a`, so stripping can't handle it. The sneakiest member of the non-erasable set because it looks like an annotation.
- **② `private` modifier** is compile-time visibility only; there is no runtime privacy at all (`user.b` works from JS). Deletes cleanly.
- **③ `#c`** is a real ES2022 private field — genuinely private at runtime. Node runs it because it is just JavaScript.

Fix for ① is to write out what the sugar hid:

```ts
class User {
  private name: string;
  constructor(name: string) { this.name = name; }
}
```

## 7. The 2026 tsconfig Baseline

Two tools, two jobs, run separately: the **bundler strips types** (fast, no checking); **`tsc --noEmit` checks types** in your editor and as a blocking CI step.

```jsonc
// sane greenfield defaults
{
  "compilerOptions": {
    "strict": true,
    "noEmit": true,                 // the bundler emits, not tsc
    "target": "ES2022",
    "module": "preserve",
    "moduleResolution": "bundler",
    "isolatedModules": true,        // enforce single-file-transpilable code
    "verbatimModuleSyntax": true,   // explicit type-only imports
    "erasableSyntaxOnly": true      // error on enum/namespace/param-properties
  }
}
```

- **`isolatedModules`** enforces that every file can be transpiled *alone* — exactly the constraint SWC/esbuild operate under. Already default in Next.js.
- **`verbatimModuleSyntax`** forces `import type` on type-only imports, so erasure is predictable (see [[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|tsconfig]]).
- **`erasableSyntaxOnly`** (TS 5.8) turns "crashes when run natively" into a red squiggle in your editor.
- **`isolatedDeclarations`** (optional, for libraries) requires annotated exports so tools can generate `.d.ts` without the checker — the declaration-file equivalent of `isolatedModules`.

> [!warning] Stripping is not downleveling
> Node's native execution erases types and runs the result unchanged — no syntax downleveling, no polyfills. If you need old-browser output you still need a real build step. `tsc`/Babel compile; Node deletes.

## Real-World Use Cases

### Replacing `enum` in a shared constants module

A design-system package exports status constants. An `enum` breaks tree-shaking and any consumer that runs files natively; an `as const` object is erasable, tree-shakes, and logs real values.

```ts
// Instead of: enum Status { Active, Archived }
export const Status = { Active: "active", Archived: "archived" } as const;
export type Status = (typeof Status)[keyof typeof Status];
```

Works because the object is plain JavaScript (survives stripping) and the union type is derived, not emitted. Logs show `"active"`, not `2`, and unused members drop out of the bundle.

### A backend service you run with `node server.ts`

A small internal service skips the build step and runs TypeScript directly. Keeping the code erasable-only (`erasableSyntaxOnly: true`) means it never hits a strip-only SyntaxError in CI or on the box.

```ts
// config.ts — erasable throughout, runs under `node config.ts`
export interface Config { port: number; region: string }
export const config: Config = { port: Number(process.env.PORT ?? 3000), region: "eu" };
```

The moment someone adds a `enum LogLevel {...}`, `node config.ts` throws — `erasableSyntaxOnly` catches it at author time instead.

### Why the bundler "misses" a type error

A PR ships despite a broken type because Next.js's SWC step only strips — it never checks. The guardrail is a separate `tsc --noEmit` gate.

```jsonc
// package.json
{ "scripts": { "typecheck": "tsc --noEmit", "build": "next build" } }
```

Works because emit and checking are independent jobs: `next build` transpiles and can succeed on code `tsc` would reject. Putting `typecheck` in CI restores the check the bundler skipped.

## Interview Answer

**Short version:** TypeScript does two jobs — checking (no output) and emitting (Babel-like syntax rewriting). Most syntax is erasable; `enum`, `namespace`, and parameter properties emit runtime code and can't just be deleted.

**Strong version:** Modern toolchains split the two jobs: the bundler (SWC/esbuild) strips types per-file for speed and does no checking, so `tsc --noEmit` runs separately in CI. Node runs `.ts` natively by *stripping only* — replacing type syntax with whitespace to preserve line numbers — which is why non-erasable syntax like `enum` throws a SyntaxError instead of being transformed. That constraint is why `isolatedModules` matters and why `enum`/`namespace` have fallen out of favor; `as const` objects give the same ergonomics and erase cleanly. On new projects I add `erasableSyntaxOnly` so the crash becomes a compile error.

## Common Mistakes

- Thinking the bundler type-checks your code — it strips, it does not check.
- Assuming Node "compiles" TypeScript; it only deletes erasable syntax.
- Expecting `enum`/`namespace`/parameter properties to be erased silently (they SyntaxError).
- Confusing the `private` modifier (erased, no real privacy) with `#private` (real ES2022 privacy).
- Refactoring working `enum`-heavy code for this — these are greenfield defaults, not a migration mandate.
- Forgetting `tsc --noEmit` in CI, so type errors never block a deploy.

## Practice

1. <details><summary>Why does `node app.ts` throw on `enum` but run `interface` fine?</summary>Interfaces are pure type information — erasing them changes nothing, so strip-only mode deletes them. An `enum` emits a real runtime object; stripping can neither delete it (the code uses it) nor generate the replacement (no code generator), so Node refuses with a SyntaxError.</details>
2. <details><summary>Your build passes but a type error reached production. How?</summary>The bundler (SWC/esbuild) only strips types; it never checks them. `next build`/Vite can succeed on code `tsc` would reject. Add `tsc --noEmit` as a blocking CI step — emit and checking are independent jobs.</details>
3. <details><summary>Rewrite `enum Direction { Up, Down }` to erasable syntax.</summary>`const Direction = { Up: "up", Down: "down" } as const;` plus `type Direction = (typeof Direction)[keyof typeof Direction];` — plain-JS emit, tree-shakes, real string values, no strip-only crash.</details>
4. <details><summary>Which of `constructor(private x)`, `private y`, `#z` survive strip-only mode?</summary>`private y` (compile-time modifier) and `#z` (real ES2022 private field) survive. `constructor(private x)` is a parameter property — it emits `this.x = x`, so it SyntaxErrors under stripping.</details>

## Related Notes

- [[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|Modules, tsconfig and Package Types]]
- [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]]
- [[27 - Frontend Tooling and Build Systems/02 - Transpilation|Transpilation]]
- [[10 - Modules/09 - From Source to Browser|From Source to Browser]]
- [[01 - Roadmap|Roadmap]]
