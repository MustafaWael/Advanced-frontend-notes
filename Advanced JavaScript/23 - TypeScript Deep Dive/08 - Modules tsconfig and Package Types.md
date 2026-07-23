---
tags: [typescript, tsconfig, modules, tooling]
module: "23 - TypeScript Deep Dive"
priority: important
status: not-started
aliases: [tsconfig, declaration files, moduleResolution]
verified_on: 2026-07-12
version_scope: "TypeScript 5.x"
---

# Modules, tsconfig and Package Types

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: explain what `strict` actually turns on, why `target`/`module`/`moduleResolution` exist, and where types for npm packages come from.
- Production signal: you can set up or repair a project's tsconfig deliberately instead of copying one from a random repo.
- Dependencies: [[10 - Modules/01 - ES Modules|ES Modules]], [[10 - Modules/09 - From Source to Browser|From Source to Browser]]

## Source Anchors

- [TypeScript: tsconfig reference](https://www.typescriptlang.org/tsconfig/)
- [TypeScript: Modules — Theory](https://www.typescriptlang.org/docs/handbook/modules/theory.html)
- [TypeScript: Declaration Files](https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html)
- [TypeScript: verbatimModuleSyntax](https://www.typescriptlang.org/tsconfig/#verbatimModuleSyntax)
- [DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped)

## 1. The Three Questions a tsconfig Answers

1. **What JavaScript may I assume exists?** — `target` (which syntax is emitted/allowed: `ES2022` etc.) and `lib` (which globals/APIs the checker knows: `DOM`, `ES2023`). In a bundler-based frontend, `target` mostly affects *checking*, since the bundler does the transpiling ([[10 - Modules/09 - From Source to Browser|source to browser]]).
2. **How do imports resolve?** — `module` + `moduleResolution`. Modern rules of thumb: `"moduleResolution": "bundler"` for apps built by Vite/Next/webpack (matches how bundlers actually resolve, allows extensionless imports); `"nodenext"` for code that Node itself runs (enforces real ESM rules, file extensions, `exports` maps). Next.js scaffolds the right values — the skill is knowing why they're right before changing them.
3. **How strict is checking?** — `strict: true` is the umbrella: `strictNullChecks` (null/undefined tracked in types — the single highest-value flag), `noImplicitAny`, `strictFunctionTypes` ([[23 - TypeScript Deep Dive/07 - Function Types Overloads and Variance|variance]]), `useUnknownInCatchVariables`, and friends. Two worthwhile extras beyond `strict`: `noUncheckedIndexedAccess` (indexing returns `T | undefined` — arrays can be empty) and `exactOptionalPropertyTypes` (distinguishes "absent" from "explicitly undefined").

### Type-only imports

`import type { User } from "./api"` (or `verbatimModuleSyntax: true`, which forces the distinction) marks imports that exist only for the checker. This matters at runtime: a type-only import is fully erased, so it can't create circular-dependency or side-effect problems ([[10 - Modules/06 - Circular Dependencies|circular deps]]), and bundlers can drop the module if nothing else uses it.

### Where types for packages come from

- **Bundled**: the package ships `.d.ts` files, referenced by `types`/`exports` in its package.json (most modern libraries).
- **DefinitelyTyped**: install `@types/foo` for JS packages that don't ship types. These are community-maintained — they can lag or diverge from the runtime package version.
- **Nothing**: the import is implicitly `any` (an error under `noImplicitAny`); you write a local declaration `declare module "legacy-widget" { ... }` as a stopgap.

Declaration files are the *compile-time contract* of a package: when the `.d.ts` lies about the runtime behavior (wrong version of `@types`, hand-written declarations gone stale), you get well-typed code that crashes — the same "types are hope, runtime is fact" lesson as [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|untrusted boundaries]], one layer down.

## 2. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a team inherits a codebase where "TypeScript never catches our null bugs."

```jsonc
// Bug: the inherited tsconfig
{
  "compilerOptions": {
    "strict": false,          // ❌ null/undefined vanish from every type
    "skipLibCheck": true
  }
}
```

```ts
function getInitials(user: { name: string }) {
  return user.name.split(" ").map(p => p[0]).join("");
}
getInitials(await findUser(id)); // findUser returns User | null — compiles fine, crashes at 2 a.m.
```

Trace: without `strictNullChecks`, `null` is assignable to every type, so `User | null` collapses to `User` and the crash ships. The checker was never wrong — it was configured not to look.

Fix — turn strictness on incrementally rather than boiling the ocean:

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true
  }
}
```

Then burn down errors module by module (start at the boundaries and shared utilities; use targeted `// @ts-expect-error TODO(strict-migration)` markers rather than reverting flags). Every suppression is visible, greppable, and fails the build when the underlying error is fixed.

Tradeoffs: a strict migration on a large codebase is real work and produces a noisy interim period; `noUncheckedIndexedAccess` in particular forces `!`/checks on hot paths where emptiness is impossible by construction. The payoff is that whole bug classes (null access, implicit any spread) stop reaching production. `skipLibCheck: true` is a pragmatic default (checking all of `node_modules`' declarations is slow and you can't fix them anyway) — just know it means library type errors surface at *usage* sites, not eagerly.

> [!tip] Erased types, real syntax
> Frontmatter rule for everything in this note: type annotations are erased, but `enum` and `namespace` (and parameter properties) are *runtime syntax* TypeScript invented. Prefer `as const` objects + unions over `enum` — they erase cleanly, tree-shake, and behave like ordinary JavaScript. This also keeps code compatible with type-stripping runtimes (Node's type stripping runs TS by erasing types only). Full treatment — the two jobs of `tsc`, the erasable/non-erasable table, and strip-only SyntaxErrors — in [[23 - TypeScript Deep Dive/11 - Erasable Syntax and Native TS Execution|Erasable Syntax and Native TS Execution]].

## 3. Interview Answer

> A tsconfig answers three questions: what JavaScript environment to assume (`target`/`lib`), how imports resolve (`module`/`moduleResolution` — `bundler` for bundled apps, `nodenext` for code Node runs), and how strictly to check (`strict`, which bundles `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, and more; `strictNullChecks` alone eliminates the biggest bug class). Package types come from bundled `.d.ts` files or `@types` on DefinitelyTyped, and a declaration file is a compile-time claim about runtime behavior — it can be wrong, which is why versions matter. I also keep type-only imports explicit (`import type`/`verbatimModuleSyntax`) so erasure is predictable and circular-import surprises don't appear.

## 4. Practice

1. <details><summary>Why is `strictNullChecks` the highest-value single flag?</summary>Without it, `null` and `undefined` are assignable to every type, so the type system cannot represent "this may be missing" — the most common runtime crash in UI code (reading properties of undefined). With it, absence is in the type (`User | null`) and the compiler forces handling at each use. It converts the largest class of production frontend errors into compile errors.</details>

2. <details><summary>An app compiles but crashes calling `lib.doThing()` — the function doesn't exist at runtime. The import is typed. What happened?</summary>The declaration file lied: `@types/lib` is for a newer/older version than the installed runtime package, or the package's own `.d.ts` is stale, or a local `declare module` stub drifted. Types are compile-time claims; the runtime package is the fact. Fix by aligning versions (`lib` and `@types/lib`) or correcting the declaration — and treat this as the package-level version of never trusting an unvalidated boundary.</details>

3. <details><summary>When do you need `moduleResolution: "nodenext"` instead of `"bundler"`?</summary>When Node itself executes the output (a server, CLI, scripts) — `nodenext` enforces Node's real ESM semantics: mandatory file extensions in relative imports, `package.json` `"type"`, and `exports`-map resolution. `"bundler"` mimics how bundlers resolve (extensionless imports allowed, `exports` respected) and is right when Vite/Next/webpack consume the source. Using `bundler` for Node code compiles fine and then fails at `node` runtime with ERR_MODULE_NOT_FOUND.</details>

4. <details><summary>Why prefer an `as const` object over an `enum`?</summary>`enum` emits runtime code (an object with reverse mappings for numeric enums), doesn't tree-shake well, has surprising semantics, and breaks the "types erase cleanly" rule — type-stripping runtimes reject it. `const OBJ = {...} as const` + `type T = typeof OBJ[keyof typeof OBJ]` gives the same named-constant ergonomics with plain JavaScript emit and a derivable union type.</details>

## Related Notes

- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[10 - Modules/06 - Circular Dependencies|Circular Dependencies]]
- [[10 - Modules/09 - From Source to Browser|From Source to Browser]]
- [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|unknown, Runtime Validation and Boundaries]]
