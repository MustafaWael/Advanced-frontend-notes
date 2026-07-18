---
tags: [typescript, javascript, type-system]
module: "23 - TypeScript Deep Dive"
priority: must-know
status: not-started
aliases: [static typing, structural typing]
---

# Type System Mental Model

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: explain static, structural typing and type erasure without claiming TypeScript makes code safe at runtime.
- Production signal: model valid states while treating API, storage, and user input as untrusted.
- Dependencies: [[02 - JavaScript Runtime Foundations/01 - ECMAScript vs JavaScript|ECMAScript vs JavaScript]]

## Source Anchors

- [TypeScript: TypeScript for JavaScript Programmers](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html)
- [TypeScript: Structural Typing](https://www.typescriptlang.org/docs/handbook/type-compatibility.html)
- [TypeScript: Erased Types](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#erased-types)

## 1. Concept

TypeScript checks the JavaScript you intend to run before execution. Its types are erased when JavaScript is emitted, so they guide development but do not inspect values arriving at runtime.

It is mostly **structural**: a value is compatible when it has the required shape, not because it explicitly declared a nominal class or interface.

```ts
type HasId = { id: string };

const fromAnotherModule = { id: "p_42", name: "Keyboard" };
const item: HasId = fromAnotherModule; // shape is compatible
```

## 2. Why It Matters

Static checking catches mismatched props, impossible branches, unsafe refactors, and incorrect API use before users find them. It cannot prove a server sent what it promised, that localStorage was not edited, or that a user submitted valid data.

> [!warning] A type annotation is not a runtime guard
> `const user = response.json() as User` tells the compiler to trust you. It does not test the HTTP response. A bad payload can still crash later code.

## 3. Bug → Fix → Tradeoff

```ts
// Bug: this assertion can lie.
const profile = (await response.json()) as { id: string; name: string };
renderProfile(profile);
```

```ts
// Better boundary: unknown until runtime validation proves the shape.
const payload: unknown = await response.json();
const profile = parseProfile(payload); // throws or returns a typed failure on bad input
renderProfile(profile);
```

The tradeoff is explicit parsing work. That work belongs at the boundary once, rather than being replaced with unsafe assertions throughout the application.

## Real-World Use Cases

### Classic interview trap: excess property checks on fresh literals

Interviewers love this because it looks like structural typing contradicting itself:

```ts
type CardProps = { title: string };

renderCard({ title: "Invoices", subtitle: "Q3" }); // ❌ 'subtitle' does not exist in CardProps

const props = { title: "Invoices", subtitle: "Q3" };
renderCard(props); // ✅ compiles
```

Trace, mechanism by mechanism: TypeScript is structural, so `props` (which *has* `title`) is compatible — extra members don't break shape compatibility. But a **fresh object literal** in an argument or assignment position gets an extra check: since the literal can't be referenced anywhere else, an unknown property there is almost certainly a typo (think `onDissmiss` on a React prop), so the compiler rejects it. Assigning to a variable first launders the freshness, and plain structural rules apply. The fix for real code is to fix the typo or widen the target type — not to launder through a variable.

### One utility, many shapes: structural typing as the API

An analytics helper needs an id from whatever entity it's given. Structurally typed parameters mean products, users, and orders all qualify without a shared class hierarchy or adapter layer:

```ts
function trackView(entity: { id: string }) {
  analytics.send("view", { entityId: entity.id });
}

trackView(product); // { id, price, stock } — compatible
trackView(user);    // { id, email }       — compatible
```

This works because compatibility is checked against the **required shape**, not a declared name — the exact opposite of Java-style nominal typing, and the reason narrow parameter types (`{ id: string }`, not `Product`) make utilities maximally reusable.

### Type erasure kills `instanceof` on your interfaces

A notifications feed receives mixed payloads and someone tries the intuitive check:

```ts
interface CommentEvent { kind: "comment"; body: string }

if (payload instanceof CommentEvent) { /* ❌ 'CommentEvent' only refers to a type */ }
```

`instanceof` walks a prototype chain at runtime, and erased interfaces leave nothing behind to walk. Runtime branching needs **value-level** evidence — a discriminant field (`payload.kind === "comment"`), a type guard, or a schema parse ([[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]], [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|Runtime Validation and Boundaries]]).

> [!tip]
> This is also why enums-as-types and `typeof`-checks feel different: `typeof x === "string"` survives compilation because it tests a value; anything that only names a type is gone from the emitted JavaScript.

## 4. Interview Answer

> TypeScript is a compile-time layer over JavaScript. It uses structural compatibility for most object checks and removes types when emitting JavaScript. It prevents many refactor and API-usage mistakes, but external values are still untrusted at runtime, so I validate them at the boundary and use TypeScript to preserve the validated shape afterward.

## 5. Practice

1. <details><summary>Does `interface User { id: string }` validate `JSON.parse` output?</summary>No. Interfaces do not exist at runtime. Parse into `unknown`, validate the shape, then return `User` only after validation succeeds.</details>
2. <details><summary>Why can an object with extra fields satisfy a smaller type?</summary>TypeScript is structurally typed: a value that contains the required members is compatible. Extra properties are usually fine after a value has been created.</details>
3. <details><summary>When is an assertion appropriate?</summary>Only when an invariant has already been established but TypeScript cannot infer it. It should document evidence, not replace validation or silence a real mismatch.</details>

## Related Notes

- [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|Runtime Validation and Boundaries]]
- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
