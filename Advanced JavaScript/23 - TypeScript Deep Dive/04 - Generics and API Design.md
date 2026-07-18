---
tags: [typescript, generics, api-design]
module: "23 - TypeScript Deep Dive"
priority: important
status: not-started
aliases: [generic]
---

# Generics and API Design

## Maturity Target

- Priority: #important
- Study time: 60 minutes
- Interview signal: explain generics as a relationship between inputs and outputs, not a replacement for domain names.
- Production signal: reusable helpers preserve caller information without unsafe casts.
- Dependencies: [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]]

## Source Anchors

- [TypeScript: Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)
- [TypeScript: keyof](https://www.typescriptlang.org/docs/handbook/2/keyof-types.html)
- [TypeScript: Indexed Access Types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html)

## 1. Concept

A generic lets a caller supply a type parameter so one function preserves a relationship instead of collapsing values to `unknown` or `any`.

```ts
function groupBy<T, K extends PropertyKey>(items: T[], keyOf: (item: T) => K): Map<K, T[]> {
  const groups = new Map<K, T[]>();
  for (const item of items) {
    const key = keyOf(item);
    groups.set(key, [...(groups.get(key) ?? []), item]);
  }
  return groups;
}
```

`T` is the caller's item type; `K` is constrained to valid map keys. The return type preserves both.

## 2. Bug → Fix → Tradeoff

```ts
function first(items: any[]) { return items[0]; } // loses the caller's type
```

```ts
function first<T>(items: readonly T[]): T | undefined {
  return items[0];
}
```

The generic version forces the caller to handle an empty list. Do not make every domain model generic: `User`, `Order`, and `CheckoutState` communicate meaning better than `TData`.

> [!tip] Generic only when a relationship repeats
> A helper that works for many caller types deserves a generic. A business rule usually deserves a named domain type.

## 3. Interview Answer

> A generic preserves a relationship between inputs and outputs — `first<T>(items: T[]): T | undefined` keeps the caller's type instead of collapsing to `any`. I add constraints (`K extends PropertyKey`) so the implementation can safely use what it needs. The judgment call is when *not* to be generic: a helper used across many types earns a type parameter; a domain model earns a name. `TData` in business logic is usually an abstraction smell.

## 4. Practice

1. <details><summary>What does `T extends { id: string }` mean?</summary>The caller may choose any type that has at least an `id: string` member. The constraint permits the implementation to read `id`.</details>
2. <details><summary>Why return `T | undefined` from `first`?</summary>Arrays can be empty. The type keeps that runtime possibility visible to callers.</details>
3. <details><summary>When is `any` a bad substitute for a generic?</summary>When the output should depend on the input. `any` loses that relationship and allows unsafe operations.</details>

## Related Notes

- [[07 - Arrays and Iteration/03 - map filter reduce forEach|Array transformations]]
- [[23 - TypeScript Deep Dive/06 - Type Operators and Exhaustiveness|Type Operators and Exhaustiveness]]
