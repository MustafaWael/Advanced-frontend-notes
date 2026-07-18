---
tags: [typescript, code-output, interview, inference, narrowing]
module: "16 - Code Output Questions"
priority: important
status: not-started
verified_on: 2026-07-17
version_scope: "TypeScript 5.x, strict mode"
---

# TypeScript Inference Output Questions

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: given a snippet, you state what the compiler *infers* or where it *errors* — and name the rule (widening, narrowing loss, contextual typing), not "TS is weird here."
- Production signal: you fix red squiggles by mechanism instead of `as`-casting them quiet.
- Fast track: solve Q1-Q4, then explain aloud why Q3's callback loses its narrowing.

All questions assume `strict: true`. The "output" is the compiler's verdict: the inferred type, or the error.

## Source Anchors

- [TypeScript Handbook — Type Inference](https://www.typescriptlang.org/docs/handbook/type-inference.html)
- [TypeScript Handbook — Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript release notes](https://www.typescriptlang.org/docs/handbook/release-notes/overview.html)

## Trace Method

For inference questions:

1. Is the position **mutable**? `let` and object properties widen literals (`"a"` → `string`); `const` keeps primitive literals narrow.
2. Is there a **contextual type**? Expressions checked against an expected type (annotation, `satisfies`, function parameter) don't widen the same way.
3. Has **narrowing** survived? Control-flow narrowing applies to a specific reference at a specific point — it's lost across function boundaries, and never applies to results of *new* expressions.
4. Is it a **union of functions being called** or an object being *assigned*? Assignability is structural and checks compatibility, not identity.

## Q1. const vs let Widening

```ts
const a = "hello";
let b = "hello";
const obj = { kind: "circle" };
let c: "circle" = obj.kind;
```

### Compiler Verdict

```text
a: "hello"        (literal type)
b: string         (widened — mutable binding)
obj.kind: string  (widened — mutable property)
last line: Error — Type 'string' is not assignable to type '"circle"'.
```

### Why

Widening is about mutability of the *position*: `const a` can never be reassigned, so the literal type is safe; `let b` and `obj.kind` can, so TS widens to `string`. Fixes, by intent: `{ kind: "circle" } as const` (deep readonly + narrow), `kind: "circle" as "circle"` (narrow one property), or an annotation/`satisfies` giving contextual expectation. This single rule explains most "why did my discriminated union stop discriminating" moments.

## Q2. as const vs satisfies

```ts
const config1 = { mode: "dark", retries: 3 } as const;
const config2 = { mode: "dark", retries: 3 } satisfies { mode: string; retries: number };
config1.retries = 4;   // ?
config2.retries = 4;   // ?
const m: "dark" = config2.mode;  // ?
```

### Compiler Verdict

```text
config1: { readonly mode: "dark"; readonly retries: 3 }
config2: { mode: "dark"; retries: number }  (inferred, validated — not replaced)
config1.retries = 4  → Error: read-only property
config2.retries = 4  → OK
m: OK — config2.mode stayed the literal "dark"
```

### Why

`as const` freezes: readonly everywhere, narrowest possible literals. `satisfies` *checks* the expression against a type but keeps the **inferred** type — so `mode` stays `"dark"` (the inferred literal is assignable to `string`, check passes) while `retries` infers as… careful: with `satisfies`, literal widening still follows normal rules per property context; the value keeps its precise inferred shape for reads, remains mutable. The interview one-liner: annotation *replaces* the type, `as const` *narrows and freezes* it, `satisfies` *validates without replacing*.

## Q3. Narrowing Lost Across Function Boundaries

```ts
function f(x: string | null) {
  if (x !== null) {
    setTimeout(() => {
      x.toUpperCase(); // ?
    }, 0);
  }
}

function g(x: string | null) {
  const done = () => x!.length;
  if (x === null) return;
  [1, 2].forEach(() => {
    console.log(x.toUpperCase()); // ?
  });
}
```

### Compiler Verdict

```text
f: OK — x is narrowed to string inside the callback
g: OK — same
(but change x to a mutable `let` reassigned anywhere, and both become errors)
```

### Why

The precise rule: narrowing propagates into closures only for `const`-like bindings (parameters and `const` that are never reassigned) — TS can prove no code path un-narrows them before the callback runs. Reassign `x` anywhere in the function and the compiler must assume the callback might run after the reassignment (it usually does — `setTimeout` fires later), so narrowing resets to `string | null` inside the closure. This is the type-level shadow of [[14 - JavaScript in React and Next.js/03 - Stale Closures|stale closures]]: both are about *when the function body runs* vs when the surrounding facts were established.

## Q4. Inference from Usage — Generic Return

```ts
function first<T>(arr: T[]): T {
  return arr[0]; // ?
}
const n = first([1, 2, 3]);
const s = first([]);
const mixed = first([1, "a"]);
```

### Compiler Verdict

```text
arr[0] return: OK in default config — but Error with noUncheckedIndexedAccess (T | undefined not assignable to T)
n: number
s: never
mixed: number | string
```

### Why

`T` infers from the argument: `[1,2,3]` → `number`; the empty array gives no candidates, so `T` falls to `never` (a lie at runtime — `first([])[0]` is `undefined`); mixed elements infer the union via best-common-type. The `arr[0]` line is the honest-compiler question: indexing can miss, and only `noUncheckedIndexedAccess` makes the type system admit it. Senior follow-up: the fix is an honest signature — `T | undefined` return — not a cast.

## Q5. Structural Assignability and Excess Properties

```ts
type Point = { x: number; y: number };
const p1: Point = { x: 1, y: 2, z: 3 };      // ?
const tmp = { x: 1, y: 2, z: 3 };
const p2: Point = tmp;                        // ?
function len(p: Point) { return p.x + p.y; }
len({ x: 1, y: 2, z: 3 });                    // ?
len(tmp);                                     // ?
```

### Compiler Verdict

```text
p1: Error — Object literal may only specify known properties ('z' does not exist on Point)
p2: OK
len({...z: 3}): Error — same excess property check
len(tmp): OK
```

### Why

TypeScript is structural: `tmp`'s type has *at least* Point's members, so it's assignable — extra properties are fine through a variable. But **fresh object literals** in a checked position get the excess property check, a deliberate lint-like exception, because a literal with an unknown key is almost always a typo (`colour` vs `color`), not intentional extra data. Knowing that this is an exception — and that aliasing through a variable "launders" it — separates "TS blocked me" from understanding.

## Q6. Discriminated Union Exhaustiveness

```ts
type Shape =
  | { kind: "circle"; r: number }
  | { kind: "square"; side: number };

function area(s: Shape): number {
  switch (s.kind) {
    case "circle": return Math.PI * s.r ** 2;
    case "square": return s.side ** 2;
    default: {
      const _exhaustive: never = s; // ?
      return _exhaustive;
    }
  }
}
// Later: add { kind: "triangle"; base: number; h: number } to Shape. What happens?
```

### Compiler Verdict

```text
As written: OK — in default, s narrows to never (all cases handled)
After adding triangle: Error at _exhaustive — Type '{ kind: "triangle"; ... }' is not assignable to type 'never'.
```

### Why

Each `case` narrows the union by discriminant; when every member is handled, the remaining type in `default` is `never`, so the assignment checks. Adding a variant makes `s` in `default` be the triangle type — not assignable to `never` — and the compiler points at every switch you forgot, at build time. This is the "make invalid states unrepresentable" pattern in executable form ([[23 - TypeScript Deep Dive/00 - TypeScript Deep Dive MOC|TypeScript Deep Dive]]): the union change *finds* its own call sites.

## Related Notes

- [[23 - TypeScript Deep Dive/00 - TypeScript Deep Dive MOC|TypeScript Deep Dive MOC]]
- [[16 - Code Output Questions/00 - Code Output Questions MOC|Code Output Questions MOC]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
