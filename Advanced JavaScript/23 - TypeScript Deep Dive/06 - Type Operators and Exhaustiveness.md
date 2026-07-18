---
tags: [typescript, type-operators, mapped-types]
module: "23 - TypeScript Deep Dive"
priority: important
status: not-started
aliases: [keyof, mapped types, conditional types, template literal types]
---

# Type Operators and Exhaustiveness

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: use `keyof`, indexed access, mapped, conditional, and template-literal types to *derive* types from one source of truth — and know when to stop.
- Production signal: renaming a field or adding a variant produces compile errors at every stale usage instead of silent drift.
- Dependencies: [[23 - TypeScript Deep Dive/04 - Generics and API Design|Generics and API Design]], [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]

## Source Anchors

- [TypeScript: keyof](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html)
- [TypeScript: Indexed Access Types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html)
- [TypeScript: Mapped Types](https://www.typescriptlang.org/docs/handbook/2/mapped-types.html)
- [TypeScript: Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)
- [TypeScript: Template Literal Types](https://www.typescriptlang.org/docs/handbook/2/template-literal-types.html)

## 1. Concept — Derive, Don't Duplicate

Every operator here exists for one practical purpose: keeping *one* source of truth when shapes are related. Instead of writing a second type that must be manually kept in sync, you compute it.

```ts
const theme = {
  colors: { primary: "#0ea5e9", danger: "#ef4444" },
  spacing: { sm: 4, md: 8, lg: 16 },
} as const;

type Theme = typeof theme;                       // derive from the value
type ColorName = keyof Theme["colors"];          // "primary" | "danger"  (keyof + indexed access)
type SpacingValue = Theme["spacing"][keyof Theme["spacing"]]; // 4 | 8 | 16

// Mapped type: transform every property of an existing shape
type Setters<T> = { [K in keyof T]: (value: T[K]) => void };
type ThemeSetters = Setters<Theme["spacing"]>;   // { sm: (v: 4) => void; md: ... }

// Template literal type: derive string patterns
type CssVar = `--color-${ColorName}`;            // "--color-primary" | "--color-danger"

// Conditional type: choose a type based on another
type ApiResult<T> = T extends { error: string } ? never : T;
```

Add a color to `theme` and `ColorName`, `CssVar`, and every consumer update automatically. Rename one and every stale usage becomes a compile error. That is the entire value proposition: **types that track reality without a human syncing them.**

The built-in utility types are just prepackaged mapped/conditional types: `Partial<T>`, `Required<T>`, `Readonly<T>`, `Pick<T, K>`, `Omit<T, K>`, `Record<K, V>`, `ReturnType<F>`, `Parameters<F>`, `Awaited<T>`. Prefer them over hand-rolling.

### `never` and exhaustiveness

`never` is the empty type — no value inhabits it. Its practical use is proving a union is fully handled ([[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|discriminated unions]]): after a `switch` covers every variant, the value in `default` has type `never`, so `assertNever(value)` compiles only while coverage is complete. A conditional type that resolves to `never` also *removes* members from a union — that's how `Exclude<T, U>` works.

## 2. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a design-system `Button` accepts a `variant` and the team keeps a parallel list of CSS classes.

```ts
// Bug: two sources of truth.
type Variant = "primary" | "secondary" | "danger";
const variantClass: Record<string, string> = {   // ❌ Record<string, ...> checks nothing
  primary: "btn-primary",
  secondary: "btn-secondary",
  // "danger" forgotten — compiles fine, renders an unstyled button
};
```

```ts
// Fix: derive the union from the single map and let the compiler enforce coverage.
const variantClass = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  danger: "btn-danger",
} as const satisfies Record<string, `btn-${string}`>;

type Variant = keyof typeof variantClass;        // union derived from the data
```

Now adding a variant is one edit: add the map entry, and `Variant` (and every prop type using it) updates. Forgetting is impossible because the union *is* the map's keys. The `satisfies` clause validates the values' pattern without widening the keys ([[23 - TypeScript Deep Dive/02 - Inference Widening and satisfies|satisfies]]).

> [!warning] Know when to stop
> Deriving types is high-value when shapes genuinely co-vary. But deeply nested conditional/mapped gymnastics that take minutes to read cost more than the drift they prevent. If a type needs a comment explaining *what it evaluates to*, prefer writing the result out explicitly — a little duplication that a human can read beats a puzzle nobody can maintain. Type-level cleverness is a budget; spend it at API boundaries, not everywhere.

Tradeoffs: derived types produce harder error messages (errors point at the operator, not the domain concept), can slow the checker in extreme cases, and raise the bar for contributors. Named intermediate type aliases mitigate all three.

## 3. Interview Answer

> `keyof` gives the keys of a type, indexed access `T[K]` gives the type at a key, mapped types transform every property of a shape, conditional types select types based on other types, and template-literal types build string unions from patterns. I use them to derive related types from one source of truth — the keys of a config object become the valid prop union, so adding an entry updates every consumer and forgetting one is a compile error. `never` closes the loop: an `assertNever` default branch proves a discriminated union is exhaustively handled. The discipline is restraint — derivation where shapes co-vary, plain named types where cleverness would hurt readability.

## 4. Practice

1. <details><summary>How would you type an object that must have exactly one CSS class per `Variant`, so adding a variant forces adding a class?</summary>`const variantClass: Record<Variant, string> = { ... }` if `Variant` is the source of truth — a missing key is a compile error. Or invert it: define the map first and derive `type Variant = keyof typeof variantClass`. Choose based on which artifact is primary; never maintain both independently.</details>

2. <details><summary>What does `type Handlers = { [K in `on${Capitalize<keyof Events & string>}`]: ... }` style typing buy in an event-emitter API?</summary>Template-literal + mapped types derive method names (`onMessage`, `onClose`) from the event map, so the emitter's listener API always matches the declared events — adding an event adds its handler type automatically, and a typo'd handler name is a compile error instead of a silently-never-called listener.</details>

3. <details><summary>Why does `Record<string, string>` catch fewer bugs than `Record<Variant, string>`?</summary>`string` keys accept anything, so misspelled and missing keys both pass. Constraining the key to a finite union makes the compiler check completeness (all members present) and correctness (no unknown members). The general rule: the narrower the key type, the more the compiler can verify.</details>

4. <details><summary>When would you deliberately NOT derive a type?</summary>When the two shapes only coincidentally look alike today (an API response vs a UI view model — they evolve independently, so coupling them creates false constraints), or when the derivation is so complex the error messages and onboarding cost outweigh the drift risk. Derive when co-variance is a domain fact; duplicate deliberately when it isn't.</details>

## Related Notes

- [[23 - TypeScript Deep Dive/02 - Inference Widening and satisfies|Inference, Widening and satisfies]]
- [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]
- [[23 - TypeScript Deep Dive/04 - Generics and API Design|Generics and API Design]]
- [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]]
