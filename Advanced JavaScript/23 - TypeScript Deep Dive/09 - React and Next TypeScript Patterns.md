---
tags: [typescript, react, nextjs, patterns]
module: "23 - TypeScript Deep Dive"
priority: must-know
status: not-started
aliases: [typing props, typing hooks, typed routes]
verified_on: 2026-07-12
version_scope: "React 19, Next.js 15–16, TypeScript 5.x"
---

# React and Next TypeScript Patterns

## Maturity Target

- Priority: #must-know
- Study time: 90 minutes
- Interview signal: type props, children, events, refs, hooks, and a generic component idiomatically — and explain what the server/client boundary does to types.
- Production signal: component APIs are self-documenting, event handlers aren't `any`, and nothing unserializable is handed across the RSC boundary.
- Dependencies: [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Discriminated Unions]], [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client]], [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|Runtime Validation]]

## Source Anchors

- [React: TypeScript](https://react.dev/learn/typescript)
- [Next.js: TypeScript](https://nextjs.org/docs/app/api-reference/config/typescript)
- [React: ref as a prop (React 19)](https://react.dev/blog/2024/12/05/react-19#ref-as-a-prop)
- [TypeScript: JSX](https://www.typescriptlang.org/docs/handbook/jsx.html)

## 1. Component Patterns

```tsx
import { useState, useRef, type ReactNode, type ComponentProps } from "react";

// Props: a named type; children is just ReactNode
type CardProps = {
  title: string;
  footer?: ReactNode;
  children: ReactNode;
  onDismiss?: () => void;
};
function Card({ title, footer, children, onDismiss }: CardProps) { /* ... */ }

// Events: React's event types, parameterized by element
function Search() {
  const [q, setQ] = useState("");                       // inferred string
  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => setQ(e.target.value);
  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => { e.preventDefault(); };
  const inputRef = useRef<HTMLInputElement>(null);      // DOM ref: element type + null
  // React 19: ref is a normal prop — type it as Ref<HTMLInputElement>, no forwardRef needed
}

// State that isn't trivially inferred: give useState the union explicitly
const [state, setState] = useState<LoadState<User>>({ kind: "idle" });

// Wrapping a DOM element or another component: derive, don't retype
type ButtonProps = ComponentProps<"button"> & { variant: "primary" | "ghost" };

// Generic component: the relationship "items ↔ renderItem ↔ keyOf" is preserved per call site
function List<T>({ items, keyOf, renderItem }: {
  items: T[];
  keyOf: (item: T) => string;
  renderItem: (item: T) => ReactNode;
}) {
  return <ul>{items.map(i => <li key={keyOf(i)}>{renderItem(i)}</li>)}</ul>;
}
```

Idioms worth internalizing: model async UI state as a discriminated union rather than `isLoading`/`error`/`data` booleans ([[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|why]]); derive wrapper props with `ComponentProps<typeof X>` instead of copying them; don't annotate what inference already knows (`useState(0)` is `number`); and avoid `React.FC` — a plain function with a typed props parameter is the current idiom (works with generics, doesn't imply children).

## 2. The Next.js Boundaries

**Server → Client serialization.** Props crossing from a Server Component to a `"use client"` component must be serializable (JSON plus Dates, Maps, Sets, etc. — but not functions, class instances, or DB handles). TypeScript does **not** enforce this — a `Date`-bearing Prisma entity with methods typechecks as a prop and fails (or silently degrades) at the boundary. Discipline: define plain DTO types for what crosses, map entities to DTOs on the server ([[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|server vs client]]).

**Server Action inputs are untrusted.** The action's parameter types describe your *intent*, not the wire. Validate with a schema inside the action ([[22 - Next.js Deep Dive/04 - Server Actions|Server Actions security]], [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|runtime validation]]).

**Typed routes and env.** Next can generate route types (`typedRoutes`) so `<Link href="/produts">` is a compile error. For env vars, validate `process.env` once at startup with a schema and export the parsed result — `process.env.API_URL!` is an assertion, not a guarantee:

```ts
// env.ts — one validated boundary for configuration
import { z } from "zod";
export const env = z.object({
  API_URL: z.string().url(),
  NEXT_PUBLIC_ANALYTICS_ID: z.string().min(1),
}).parse(process.env);   // fails fast at boot, not at 2 a.m. in a request
```

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a dashboard passes a server-fetched entity into a client chart component.

```tsx
// Bug: typechecks, breaks at the boundary.
// server component
const account = await db.account.findUnique({ where: { id } }); // entity with Decimal, methods
return <BalanceChart account={account} />;                      // ❌ crosses RSC boundary
```

Trace: `account` carries a Prisma `Decimal` (a class instance) and internal methods. TypeScript sees a structurally valid prop; at runtime the RSC serializer can't encode it — you get a serialization error, or a mangled object client-side. The type system was checking shapes, but the boundary constraint is about *values*.

```tsx
// Fix: an explicit DTO — the boundary gets its own type.
type BalancePoint = { date: string; balance: number };           // plain data only
const points: BalancePoint[] = history.map(h => ({
  date: h.date.toISOString(),
  balance: h.balance.toNumber(),
}));
return <BalanceChart points={points} />;
```

Tradeoffs: DTO mapping is boilerplate and one more type to maintain — but it decouples your DB schema from your client bundle (schema changes stop rippling into components), shrinks the payload to what the UI needs, and prevents accidental leaking of server-only fields (`passwordHash` never even exists in the DTO type). That last point makes this a security pattern, not just a typing one.

## Real-World Use Cases

### Context hook that eliminates null checks

A cart context is `null` until the provider mounts, so `createContext<CartContext | null>(null)` is the honest type — but consuming components shouldn't each re-prove non-nullness. Centralize the assertion in one hook:

```tsx
const CartContext = createContext<CartContext | null>(null);

export function useCart(): CartContext {
  const ctx = useContext(CartContext);
  if (ctx === null) throw new Error("useCart must be used within <CartProvider>");
  return ctx;
}

// consumers: const { items, addItem } = useCart(); — no optional chaining anywhere
```

The `if (ctx === null) throw` narrows the return to `CartContext`, so one runtime check (which also turns a silent misconfiguration into a loud error naming the missing provider) buys typed access everywhere. Same narrowing mechanics as [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]; context internals in [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]].

### Async `params` and validated `searchParams` in a Next 15 page

Since Next 15, `params` and `searchParams` are Promises — code that typechecked in 14 (`params.slug`) now reads a property off a Promise. Type the props honestly, await them, and treat `searchParams` as the untrusted input it is:

```tsx
type PageProps = {
  params: Promise<{ slug: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function ProductPage({ params, searchParams }: PageProps) {
  const { slug } = await params;
  const { tab } = TabParam.parse(await searchParams); // z.object({ tab: z.enum(["specs","reviews"]).catch("specs") })
  return <Product slug={slug} activeTab={tab} />;
}
```

`slug` is trustworthy-ish (it matched the route pattern), but `searchParams` is arbitrary user input on every request — the same boundary rule as Server Actions in section 2 ([[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|Runtime Validation]]).

> [!warning]
> Without a `PageProps` type (or `typedRoutes`), accessing `params.slug` synchronously may "work" during migration thanks to a compatibility shim, then break in a later major. The Promise type makes the breakage a compile error today.

### Polymorphic design-system component (`as` prop)

The design system's `<Button>` must render as a real `<button>` or an `<a>` (or Next's `Link`) while keeping the correct native props for whichever element it becomes:

```tsx
type ButtonProps<T extends React.ElementType> = {
  as?: T;
  variant: "primary" | "ghost";
} & Omit<React.ComponentPropsWithoutRef<T>, "as" | "variant">;

function Button<T extends React.ElementType = "button">({ as, variant, ...rest }: ButtonProps<T>) {
  const Component = as ?? "button";
  return <Component data-variant={variant} {...rest} />;
}

<Button as="a" href="/pricing" variant="primary" />   // href allowed
<Button href="/pricing" variant="primary" />           // ❌ href doesn't exist on "button"
```

The generic ties the `as` prop to the accepted prop set per call site — the same "relationship between props" test that justified the generic `List` in section 1, and `ComponentPropsWithoutRef` derives the element's surface instead of retyping it.

> [!tip]
> Reach for this only in shared UI libraries. For a one-off "button that's sometimes a link", two components (or a wrapper around `Link`) are simpler than the generic machinery.

## 4. Interview Answer

> For components: named props types with `children: ReactNode`, React's event types (`ChangeEvent<HTMLInputElement>`), `useRef<Element | null>`, explicit unions for `useState` when inference can't see future states, `ComponentProps` to derive wrapper props, and generic components when a real items/render relationship must be preserved. Async state is a discriminated union, not boolean flags. In Next, the type system doesn't police the two boundaries that matter: RSC props must be serializable values (so I map entities to plain DTOs), and Server Action inputs are untrusted wire data (so I schema-validate inside the action). Env vars get validated once at startup with an inferred type, instead of `process.env.X!` assertions scattered around.

## 5. Practice

1. <details><summary>Why does `useRef<HTMLInputElement>(null)` include `null`, and when do you check it?</summary>The ref starts as `null` and only points at the element after React commits the DOM; it's `null` again after unmount and could be `null` if the element renders conditionally. The type records that lifecycle honestly. You check (or use optional chaining) at usage time — typically inside effects/handlers, which run post-commit, where it's almost always present but the check documents the assumption.</details>

2. <details><summary>A wrapped `<input>` component copies 12 props by hand and drifts every React upgrade. Better approach?</summary>`type Props = ComponentProps<"input"> & { label: string }` — derive the underlying element's full prop surface and intersect your additions. Consumers get every native prop (typed), and upgrades that change React's DOM typings flow through automatically. Same pattern for wrapping components: `ComponentProps<typeof Button>`.</details>

3. <details><summary>Your Server Action has signature `(data: { role: "user" | "admin" })`. An attacker sends `{ role: "owner" }`. What does TypeScript do, and what must you do?</summary>Nothing — the annotation is erased; at runtime the action receives whatever bytes arrived. The literal-union type documents intent only. Inside the action you must schema-validate (`z.enum(["user","admin"]).parse(...)`) and also authorize the caller; the type merely mirrors what the schema enforces. Types model the contract, validation enforces it.</details>

4. <details><summary>When is a generic component worth it versus `ReactNode` props?</summary>Generic when the component enforces a relationship among its props — `items`, `keyOf`, and `renderItem` must all agree on `T`, and inference at each call site gives typed `item`s in the render callback. If the component just displays slots with no cross-prop relationship, `ReactNode` props are simpler. The test: would `unknown` items break a caller? If yes, generic.</details>

## Related Notes

- [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]
- [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|unknown, Runtime Validation and Boundaries]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[21 - React Internals and Patterns/12 - Controlled vs Uncontrolled Components|Controlled vs Uncontrolled Components]]
