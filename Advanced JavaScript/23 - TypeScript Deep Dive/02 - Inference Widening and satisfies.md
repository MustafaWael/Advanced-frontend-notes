---
tags: [typescript, inference, satisfies]
module: "23 - TypeScript Deep Dive"
priority: must-know
status: not-started
aliases: [as const]
---

# Inference, Widening and satisfies

## Maturity Target

- Priority: #must-know
- Study time: 45 minutes
- Interview signal: explain inference, literal widening, `as const`, and `satisfies` as different tools.
- Production signal: configuration stays precise without losing validation.
- Dependencies: [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]]

## Source Anchors

- [TypeScript: Everyday Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)
- [TypeScript 4.9: satisfies](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-9.html)
- [TypeScript: Literal Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#literal-types)

## 1. Concept

Inference keeps code readable, but mutable values often widen: `let status = "idle"` becomes `string` because it may later change. `as const` preserves literal values and makes object properties readonly. `satisfies` validates a shape while keeping the inferred, precise type of the expression.

```ts
type Route = { path: string; auth: boolean };

const routes = {
  dashboard: { path: "/dashboard", auth: true },
  login: { path: "/login", auth: false },
} satisfies Record<string, Route>;

routes.dashboard.path; // inferred as string, while all entries are checked as Route
```

## 2. Common Bug

```ts
const config: Record<string, Route> = {
  dashboard: { path: "/dashboard", auth: true },
};
// Annotation validates, but can discard useful literal detail.
```

Use an annotation when you want the variable to be viewed as exactly that broad type. Use `satisfies` for configuration where you want validation *and* the original inferred detail. Use `as const` when immutable literal values themselves matter; do not use it to suppress errors.

> [!tip] Let inference do ordinary work
> Annotate public function boundaries, state models, and intentionally broad values. Avoid adding redundant annotations to every local variable.

## Real-World Use Cases

### Classic interview trap: the widened config object

The canonical snippet — an object created two lines earlier suddenly "loses" its literal:

```ts
type Method = "GET" | "POST" | "PUT" | "DELETE";
declare function request(url: string, method: Method): Promise<Response>;

request("/api/orders", "POST"); // ✅ literal in a checked position stays "POST"

const config = { url: "/api/orders", method: "POST" };
request(config.url, config.method); // ❌ Argument of type 'string' is not assignable to 'Method'
```

Trace: at the `const config = ...` line there is no contextual type, and object properties are **mutable positions** — someone could later write `config.method = "banana"` — so TypeScript widens `"POST"` to `string` *at creation*. By the time `config.method` reaches `request`, the literal is already gone; the call site can't un-widen it. Fixes, in order of intent: `method: "POST" as const` (freeze one property), `const config = {...} as const` (freeze all, readonly), or `const config = {...} satisfies { url: string; method: Method }` (validate the shape *and* keep `method: "POST"` inferred). See [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]] for why the annotation alternative (`const config: { method: Method }`) also compiles but discards the literal.

### Design-token map that keeps autocomplete

A design system exports spacing and color tokens. Annotating with `Record<string, string>` validates the values but makes every key lookup a shot in the dark; `satisfies` keeps the literal keys:

```ts
const colors = {
  brand: "#6349ff",
  surface: "#0f0f10",
  danger: "#e5484d",
} satisfies Record<string, `#${string}`>;

colors.brand;  // ✅ typed as "#6349ff", autocompleted
colors.brnad;  // ❌ compile error — with the annotation, this would have been `string` and passed
```

Works because `satisfies` checks the expression against the shape without replacing its inferred type — the exact split section 2 describes. The template-literal constraint also catches a token someone pasted without the `#`.

### Custom hook returning a tuple

A `useToggle` hook returns a value and a toggler. Without intervention, array literals widen to a mutable array of the union of element types, and destructuring produces the wrong types at every call site:

```ts
function useToggle(initial = false) {
  const [on, setOn] = useState(initial);
  const toggle = useCallback(() => setOn(v => !v), []);
  return [on, toggle] as const; // readonly [boolean, () => void]
}

const [open, toggleOpen] = useToggle(); // open: boolean — not boolean | (() => void)
```

Without `as const` the return type is `(boolean | (() => void))[]`, so `open` could be a function and calling `toggleOpen()` is an error. Arrays are mutable positions, so inference has no reason to keep tuple structure — `as const` is the signal that position and length are fixed, which is exactly why `useState` itself is typed to return a tuple.

> [!tip]
> Any hook that mimics the `useState` pair shape needs `as const` (or an explicit tuple return type) — this is the single most common `as const` in real React codebases.

## 3. Interview Answer

> TypeScript infers most types, and mutable positions widen literals (`"idle"` becomes `string`) because the value may change. `as const` freezes literals and makes things readonly; an annotation validates but replaces the inferred type with the broader one; `satisfies` gives both — it checks the expression against a shape while keeping the precise inferred type. For a config or route map I reach for `satisfies`: I get validation without losing the literal keys and values downstream code relies on.

## 4. Practice

1. <details><summary>What does `as const` change?</summary>It preserves literal types, makes object properties readonly, and turns arrays into readonly tuples. It does not validate an expected shape.</details>
2. <details><summary>Why prefer `satisfies` for a route map?</summary>It catches missing or malformed route fields while retaining useful inferred details from the specific map.</details>
3. <details><summary>Does `satisfies` change emitted JavaScript?</summary>No. Like other TypeScript type syntax, it is erased.</details>

## Related Notes

- [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]
- [[22 - Next.js Deep Dive/05 - Route Handlers and Middleware|Route Handlers and Proxy]]
