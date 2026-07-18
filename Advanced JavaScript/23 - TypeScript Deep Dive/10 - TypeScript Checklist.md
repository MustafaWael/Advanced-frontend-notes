---
tags: [typescript, checklist]
module: "23 - TypeScript Deep Dive"
priority: must-know
status: not-started
---

# TypeScript Checklist

Use this checklist as an active test. Mark an item complete only when you can explain, predict, debug, and refactor without looking.

## Source Anchors

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [TypeScript: tsconfig reference](https://www.typescriptlang.org/tsconfig/)
- [React: TypeScript](https://react.dev/learn/typescript)

## Mental Model

- [ ] I can explain static analysis, structural typing, and type erasure in three sentences.
- [ ] I can explain why `as User` on a fetch result is a claim, not a check.
- [ ] I can say what TypeScript can and cannot protect at runtime.

## Inference and Narrowing

- [ ] I can explain literal widening and when `as const` stops it.
- [ ] I can choose between an annotation, `satisfies`, and `as const` for a config object.
- [ ] I can narrow a union with `typeof`, `in`, equality, and a custom type predicate.
- [ ] I can model async UI as a discriminated union and enforce exhaustiveness with `assertNever`.

## Generics and Type Operators

- [ ] I can write a constrained generic that preserves a caller relationship (`groupBy`, typed `subscribe`).
- [ ] I can derive a union from data with `keyof typeof` and defend deriving vs duplicating.
- [ ] I can use mapped, conditional, and template-literal types — and say when they're over-engineering.
- [ ] I can name what `Partial`, `Pick`, `Omit`, `Record`, `ReturnType`, and `Awaited` are made of.

## Functions and Variance

- [ ] I can explain why callbacks may declare fewer parameters.
- [ ] I can explain parameter contravariance vs method-shorthand bivariance and `strictFunctionTypes`.
- [ ] I can say when an overload beats a union parameter.

## Boundaries and Validation

- [ ] I can name the untrusted boundaries in a frontend app (network, storage, env, actions, catch).
- [ ] I can set up one validated parse at a boundary (schema + inferred type) and explain `z.infer`.
- [ ] I can explain why shared backend types don't replace runtime validation.

## Tooling and Config

- [ ] I can explain `target`/`lib`, `module`/`moduleResolution` (`bundler` vs `nodenext`), and the `strict` family.
- [ ] I know where package types come from (bundled `.d.ts`, `@types`, local declarations) and how they can lie.
- [ ] I can plan an incremental strict migration without reverting flags.
- [ ] I can argue `as const` objects vs `enum`.

## React and Next

- [ ] I can type props, children, events, refs, hooks, and a generic component idiomatically.
- [ ] I can use `ComponentProps` to derive wrapper props.
- [ ] I can explain what the RSC serialization boundary does to prop types and why DTOs help.
- [ ] I can explain why Server Action parameter types don't protect the endpoint.

## Exit Test

- [ ] Take an untyped fetch-and-render feature and add honest types end to end: schema at the boundary, discriminated union state, typed components.
- [ ] Find the bug: a `Record<string, string>` variant map missing a key. Fix it so the compiler prevents recurrence.
- [ ] Explain to a junior why the build passed but production crashed on `user.name` — and which two flags/patterns would have caught it.

## Related Notes

- [[23 - TypeScript Deep Dive/00 - TypeScript Deep Dive MOC|TypeScript Deep Dive MOC]]
- [[22 - Next.js Deep Dive/09 - Next.js Deep Dive Checklist|Next.js Deep Dive Checklist]]
- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
- [[01 - Roadmap|Roadmap]]
