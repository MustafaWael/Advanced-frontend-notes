---
tags: [javascript, language-concepts, advanced-concepts-checklist]
module: "12 - Advanced Language Concepts"
priority: must-know
status: not-started
---

# Advanced Concepts Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, diagnose, and fix the behavior without looking.

## Maturity Target

- Priority: #must-know
- Study time: 120-180 minutes for review.
- Interview signal: you can connect edge-case language mechanics to React, APIs, forms, state, memory, and serialization.
- Production signal: values are parsed, compared, copied, iterated, serialized, and rendered intentionally.

## Fast Track Order

1. [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
2. [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
3. [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]]
4. [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]
5. [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]
6. [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]]
7. [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]
8. [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
9. [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
10. [[12 - Advanced Language Concepts/10 - BigInt Date RegExp JSON|BigInt Date RegExp JSON]]

Reason: identity and equality explain many React bugs; parsing/iteration/collections then build on those foundations.

## Core Understanding

- [ ] I can list JavaScript primitive types.
- [ ] I can explain why JavaScript is pass-by-value, including object references.
- [ ] I can explain why object spread is shallow.
- [ ] I can compare `==`, `===`, `Object.is`, and SameValueZero.
- [ ] I can explain why React state and dependency comparisons are identity-based.
- [ ] I can list falsy values and separate falsy from nullish.
- [ ] I can explain why `&&` can render `0` in JSX.
- [ ] I can use `?.` and `??` without hiding real data bugs.
- [ ] I can explain `ToPrimitive` and the `+` operator.
- [ ] I can parse form/query/localStorage values intentionally.
- [ ] I can use destructuring, spread, and rest without assuming deep copy.
- [ ] I can explain symbol identity, `Symbol.for`, and well-known symbols.
- [ ] I can explain iterator and iterable protocols.
- [ ] I can write a generator and explain when it is lazy.
- [ ] I can choose between Object, Map, Set, WeakMap, and WeakSet.
- [ ] I can explain BigInt, Date, RegExp, and JSON production traps.

## Source-Backed Terms

| Term | Plain meaning | Technical meaning | Production use |
| --- | --- | --- | --- |
| Primitive | Simple immutable value. | Non-object language value. | Avoid mutation assumptions. |
| Reference | Way to reach an object. | Object identity value copied by assignment. | React state and memo behavior. |
| SameValue | Exact sameness. | Algorithm used by `Object.is`. | React dependency/state comparisons. |
| SameValueZero | SameValue except `-0` equals `+0`. | Used by `Map`, `Set`, `includes`. | Deduping and keyed collections. |
| Falsy | Value that becomes false in boolean context. | Result of `ToBoolean`. | JSX and defaulting bugs. |
| Nullish | `null` or `undefined`. | Used by `??` and `?.`. | Missing-value defaults. |
| ToPrimitive | Object to primitive conversion. | Uses `Symbol.toPrimitive`, `valueOf`, `toString`. | Coercion and custom objects. |
| Iterable | Can provide an iterator. | Has `[Symbol.iterator]()`. | Spread, destructuring, `for...of`. |
| WeakMap | Object-keyed metadata store. | Holds keys weakly for GC. | DOM/cache metadata without leaks. |
| JSON boundary | Text data exchange. | Serialization/parsing with special rules. | Validate parsed data. |

## Production Readiness Checklist

- [ ] I never mutate React state objects, arrays, maps, or sets in place.
- [ ] I do not use `||` defaults for values where `0`, `false`, or `""` are valid.
- [ ] I parse query params and form values before arithmetic.
- [ ] I do not trust `JSON.parse` as typed data.
- [ ] I do not use JSON stringify/parse as a general deep clone.
- [ ] I avoid `/g` regex for simple repeated boolean tests.
- [ ] I escape user input before building dynamic regexes.
- [ ] I represent large IDs as strings or BigInt, not unsafe numbers.
- [ ] I use `WeakMap` only when weak object-key semantics matter.
- [ ] I keep optional chaining from hiding required API contract breaks.

## Code-Output Drills

### Drill 1: object reference

```js
const a = { count: 0 };
const b = a;
b.count += 1;
console.log(a.count);
console.log(a === b);
```

Expected output:

```txt
1
true
```

### Drill 2: equality

```js
console.log(NaN === NaN);
console.log(Object.is(NaN, NaN));
console.log(Object.is(-0, 0));
console.log(new Set([NaN, NaN]).size);
```

Expected output:

```txt
false
true
false
1
```

### Drill 3: truthy/nullish

```js
console.log(0 || 10);
console.log(0 ?? 10);
console.log("" || "fallback");
console.log("" ?? "fallback");
```

Expected output:

```txt
10
0
fallback

```

The final line prints an empty string.

### Drill 4: coercion

```js
console.log(1 + "2" + 3);
console.log(1 + 2 + "3");
console.log(Number(""));
console.log(Number("42px"));
```

Expected output:

```txt
123
33
0
NaN
```

### Drill 5: regex state

```js
const re = /a/g;
console.log(re.test("a"));
console.log(re.test("a"));
console.log(re.test("a"));
```

Expected output:

```txt
true
false
true
```

Reason: `/g` updates `lastIndex`.

## Real-World Scenario Review

### Scenario 1: stale React UI

Problem: `setSelected(selected)` after mutating a `Set`.

Fix: create `new Set(selected)` first, mutate the new set, return it.

### Scenario 2: bad pagination

Problem: `const next = page + 1` where `page` came from `URLSearchParams`.

Fix: parse with `Number`, reject invalid/empty values, then add.

### Scenario 3: optional data hides contract bug

Problem: `apiUser?.profile?.email ?? ""` when `profile` is required by API contract.

Fix: validate response shape and fail loudly/log if required data is missing.

### Scenario 4: large ID corruption

Problem: backend sends a database `BIGINT` as JSON number.

Fix: send as string, parse with `BigInt` only when arithmetic/comparison requires it.

### Scenario 5: date-only off by one

Problem: displaying `new Date("2026-05-29")` as a local calendar date.

Fix: treat calendar dates as date strings or use a proper date library/model; treat `Date` as an instant.

## Interview Prompts

1. Explain primitive vs reference values using a React state bug.
2. What are the differences between `==`, `===`, and `Object.is`?
3. Why does `{count && <Component />}` sometimes render `0`?
4. Why is `??` safer than `||` for defaults?
5. Explain `ToPrimitive` and the `+` operator.
6. Why is object spread shallow?
7. What problem do symbols solve?
8. What is the difference between iterator and iterable?
9. When would you choose `WeakMap` over `Map`?
10. What are the biggest JSON serialization traps?

## Self-Review Rubric

| Level | What your answer sounds like |
| --- | --- |
| Weak | "These are JavaScript weird parts." |
| Junior-plus | "I know the common edge cases like `NaN` and falsy values." |
| Mid-level | "I can explain the official mechanism and connect it to React/API bugs." |
| Strong mid-level | "I choose parsing, equality, copying, iteration, collection, and serialization patterns based on production ownership and failure modes." |

## Related Notes

- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]
- [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]]
- [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]
- [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]]
- [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]
- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[12 - Advanced Language Concepts/10 - BigInt Date RegExp JSON|BigInt Date RegExp JSON]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[01 - Roadmap|Roadmap]]
