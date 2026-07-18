---
tags: [typescript, moc, javascript]
module: "23 - TypeScript Deep Dive"
priority: must-know
status: not-started
---

# TypeScript Deep Dive MOC

TypeScript is a static analysis language layered on JavaScript. This module teaches it as a tool for modelling valid states, designing safe APIs, and making boundaries explicit—not as a way to write clever type puzzles.

## Prerequisites

- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Values and references]]
- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[20 - Network and Security/04 - Cookies and Auth Patterns|Untrusted boundaries]]

## Reading Order

1. [[23 - TypeScript Deep Dive/01 - Type System Mental Model|Type System Mental Model]]
2. [[23 - TypeScript Deep Dive/02 - Inference Widening and satisfies|Inference, Widening and satisfies]]
3. [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Narrowing and Discriminated Unions]]
4. [[23 - TypeScript Deep Dive/04 - Generics and API Design|Generics and API Design]]
5. [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|unknown, Runtime Validation and Boundaries]]
6. [[23 - TypeScript Deep Dive/06 - Type Operators and Exhaustiveness|Type Operators and Exhaustiveness]]
7. [[23 - TypeScript Deep Dive/07 - Function Types Overloads and Variance|Function Types, Overloads and Variance]]
8. [[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|Modules, tsconfig and Package Types]]
9. [[23 - TypeScript Deep Dive/09 - React and Next TypeScript Patterns|React and Next TypeScript Patterns]]
10. [[23 - TypeScript Deep Dive/10 - TypeScript Checklist|TypeScript Checklist]]

## You're Done When

- [ ] I can explain why TypeScript can prevent invalid states but cannot validate network input.
- [ ] I can narrow `unknown`, design a discriminated union, and enforce exhaustiveness.
- [ ] I can write a useful generic without hiding a simple domain model behind type gymnastics.
- [ ] I can explain function-type variance and design callback APIs that are safe for callers.
- [ ] I can configure a strict project, understand its emitted JavaScript, and type React/Next boundaries honestly.

## Related Notes

- [[20 - Network and Security/05 - XSS|XSS]]
- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[24 - Testing and Quality/00 - Testing and Quality MOC|Testing and Quality]]
