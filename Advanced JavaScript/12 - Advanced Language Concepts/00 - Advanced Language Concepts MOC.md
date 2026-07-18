---
tags: [javascript, moc, language-concepts]
module: "12 - Advanced Language Concepts"
priority: important
status: not-started
---

# Advanced Language Concepts MOC

This module teaches the value-level mechanics of JavaScript: how values are copied and compared, how coercion and boolean conversion actually work, and how symbols, iterators, collections, and serialization behave under the hood. Mastering it unlocks a large family of real bugs — stale React UI from mutated state, `0` rendering in JSX, `||` defaults eating valid values, `/g` regex state, and large IDs corrupted by JSON. In interviews, this is where "knows the syntax" is separated from "can explain `Object.is`, `ToPrimitive`, and why spread is shallow."

## Prerequisites

- [[03 - Scope and Variables/05 - Closures|Closures]] — value lifetime and bindings underpin identity reasoning.
- [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]] — references, property lookup, and object identity.
- [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying]] — shallow vs deep copying is assumed throughout.
- [[07 - Arrays and Iteration/06 - Iteration Protocols|Iteration Protocols]] — groundwork for iterators, generators, and collections.

## Reading Order

1. [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]] — the copy-vs-reference model everything else builds on.
2. [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]] — the exact comparison algorithms React and collections use.
3. [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]] — `ToPrimitive`, the `+` operator, and intentional parsing.
4. [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]] — why `{count && <X />}` can render `0`.
5. [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]] — safe defaults without hiding contract bugs.
6. [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]] — the shallow-copy tools used in every immutable update.
7. [[12 - Advanced Language Concepts/07 - Symbols|Symbols]] — unique keys and the well-known symbols that drive protocols.
8. [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]] — the protocol behind spread, `for...of`, and lazy sequences.
9. [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]] — choosing keyed collections and weak references deliberately.
10. [[12 - Advanced Language Concepts/10 - BigInt Date RegExp JSON|BigInt Date RegExp JSON]] — the built-in objects with the sharpest production traps.
11. [[12 - Advanced Language Concepts/11 - Advanced Concepts Checklist|Advanced Concepts Checklist]] — active self-test with drills and scenarios.
12. [[12 - Advanced Language Concepts/12 - Numbers and Floating Point|Numbers and Floating Point]] — IEEE 754, `0.1 + 0.2`, safe integers, money handling.
13. [[12 - Advanced Language Concepts/13 - Strings Unicode and Template Literals|Strings, Unicode and Template Literals]] — code units vs code points vs graphemes, normalize, tagged templates.
14. [[12 - Advanced Language Concepts/14 - Typed Arrays and Binary Data|Typed Arrays and Binary Data]] — ArrayBuffer, DataView, Blob/File, base64, file scenarios.
15. [[12 - Advanced Language Concepts/15 - Proxy and Reflect|Proxy and Reflect]] — traps, framework reactivity, invariants, performance cost.
16. [[12 - Advanced Language Concepts/16 - Intl|Intl]] — NumberFormat, DateTimeFormat, RelativeTimeFormat, Collator; kill hand-rolled formatting.

## You're Done When

- [ ] I can explain why JavaScript is pass-by-value, including object references, and why object spread is shallow.
- [ ] I can compare `==`, `===`, `Object.is`, and SameValueZero, and explain why React comparisons are identity-based.
- [ ] I can list the falsy values, separate falsy from nullish, and explain why `&&` can render `0` in JSX.
- [ ] I can explain `ToPrimitive` and the `+` operator, and parse form/query/localStorage values intentionally.
- [ ] I can use `?.` and `??` without hiding real data bugs, and avoid `||` defaults where `0`, `false`, or `""` are valid.
- [ ] I can explain symbol identity, the iterator and iterable protocols, and write a generator that is lazy.
- [ ] I can choose between Object, Map, Set, WeakMap, and WeakSet based on key semantics and GC behavior.
- [ ] I can name the BigInt, Date, RegExp, and JSON production traps, including large-ID corruption and `/g` state.

## Related Notes

- [[12 - Advanced Language Concepts/11 - Advanced Concepts Checklist|Advanced Concepts Checklist]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[01 - Roadmap|Roadmap]]
