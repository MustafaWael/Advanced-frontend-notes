---
tags: [testing, unit-tests, vitest]
module: "24 - Testing and Quality"
priority: must-know
status: not-started
aliases: [unit testing, Vitest]
verified_on: 2026-07-12
version_scope: "Vitest 3.x"
---

# Pure JavaScript Unit Tests

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: write a unit test that earns its keep — edge cases, boundaries, and failure paths, not the happy path restated.
- Production signal: complex pure logic is extracted into testable functions, and its tests read as a specification.
- Dependencies: [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions]], [[24 - Testing and Quality/01 - Testing Mental Model|Testing Mental Model]]

## Source Anchors

- [Vitest: Getting Started](https://vitest.dev/guide/)
- [Vitest: expect API](https://vitest.dev/api/expect.html)
- [Vitest: test.each](https://vitest.dev/api/#test-each)
- [MDN: Number.EPSILON](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/EPSILON)

## 1. Concept

A unit test exercises one function in isolation and asserts on its output (or its observable effect). The precondition is that the function is *worth* isolating: real logic — parsing, formatting, calculation, state transitions, sorting/filtering rules — rather than glue. Purity ([[04 - Functions Deep Dive/04 - Pure Functions and IIFE|pure functions]]) is what makes this cheap: same input, same output, nothing to set up or mock.

```ts
// price.ts — pure, extracted precisely so it can be specified by tests
export function applyDiscount(cents: number, percent: number): number {
  if (!Number.isInteger(cents) || cents < 0) throw new RangeError("cents must be a non-negative integer");
  if (percent < 0 || percent > 100) throw new RangeError("percent out of range");
  return Math.round(cents * (1 - percent / 100));
}
```

```ts
// price.test.ts — the test file reads as the spec
import { describe, it, expect } from "vitest";
import { applyDiscount } from "./price";

describe("applyDiscount", () => {
  it.each([
    [1000, 0, 1000],     // no discount
    [1000, 100, 0],      // full discount
    [999, 33.5, 664],    // rounding: 664.335 → 664
    [1, 50, 1],          // rounding up: 0.5 → 1 (Math.round half-up)
  ])("(%i cents, %f%%) → %i", (cents, percent, expected) => {
    expect(applyDiscount(cents, percent)).toBe(expected);
  });

  it("rejects negative and non-integer cents", () => {
    expect(() => applyDiscount(-1, 10)).toThrow(RangeError);
    expect(() => applyDiscount(10.5, 10)).toThrow(RangeError);
  });
});
```

What makes these good unit tests: they pin **boundaries** (0%, 100%), **representation traps** (integer cents because [[12 - Advanced Language Concepts/12 - Numbers and Floating Point|floating point]] can't hold 0.1), **rounding policy** (a real business decision, now documented), and **failure behavior** (typed errors). The happy path is one row among many.

`toBe` vs `toEqual` matters: `toBe` is `Object.is` — reference identity for objects ([[12 - Advanced Language Concepts/02 - Equality and Object.is|equality]]); `toEqual` compares structure recursively. Asserting `toBe` on a returned object also asserts *the same object came back* — sometimes exactly what you mean (memoization tests), usually not.

## 2. Why It Matters

- Unit tests are the cheapest regression net for logic-heavy code, and the test-first habit ("what are this function's edge cases?") improves the function's design before any test runs.
- The interview version: given a function, enumerate what deserves testing. Weak candidates restate the happy path; strong ones probe boundaries, invalid input, and representational edge cases.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a cart total is occasionally off by one cent, only for certain quantities.

```ts
// Bug: float arithmetic in currency
export function lineTotal(priceDollars: number, qty: number) {
  return priceDollars * qty;                   // 0.1 * 3 = 0.30000000000000004
}
```

The buggy version *had a test* — `expect(lineTotal(10, 2)).toBe(20)` — which passes, because the chosen inputs dodge the failure. The unit-test skill is choosing inputs from the function's hazard model:

```ts
// Fix: integer cents + a test that pins the hazard
export function lineTotal(priceCents: number, qty: number) {
  return priceCents * qty;
}

it("does not drift for amounts that are non-representable in binary floats", () => {
  expect(lineTotal(10, 3)).toBe(30);           // 10¢ × 3 — was 0.30000000000000004 dollars
  expect(lineTotal(19, 3)).toBe(57);
});
```

Tradeoff: integer-cents pushes conversion to the display boundary (`(cents / 100).toFixed(2)` or [[12 - Advanced Language Concepts/16 - Intl|Intl.NumberFormat]]) — more explicit plumbing, but the arithmetic domain is exact. The general lesson: a unit test is only as good as the hazard analysis behind its inputs. Ask "what representation, boundary, or policy could betray this function?" and write those rows.

> [!tip] Extract to test, don't test to reach
> If logic is buried in a component and hard to unit test, don't reach for a heavier tool by reflex — first try extracting the logic into a pure function and testing that ([[24 - Testing and Quality/03 - React Component Testing Through User Behavior|component tests]] then only need to verify wiring). Hard-to-test is often a design smell, and the extraction is the fix.

## Real-World Use Cases

### Cart reducer as a table of transitions

A `useReducer`-driven cart is the app's core business logic wearing a React costume — the reducer is a pure function `(state, action) → state`, so it unit-tests like one:

```ts
it("merges same-SKU adds instead of duplicating lines", () => {
  const prev = cartReducer(empty, { type: "add", item: tShirt });
  const next = cartReducer(prev, { type: "add", item: tShirt });
  expect(next.items).toHaveLength(1);
  expect(next.items[0].qty).toBe(2);
});

it("returns new state without mutating the previous one", () => {
  const prev = { items: [{ sku: "tee-m", qty: 1 }] };
  const next = cartReducer(prev, { type: "changeQty", sku: "tee-m", qty: 3 });
  expect(next).not.toBe(prev);          // identity claim — toBe on purpose
  expect(prev.items[0].qty).toBe(1);    // prev untouched
});
```

The non-mutation test is load-bearing: React bails out of re-renders on `Object.is`-equal state, so an in-place mutation is a *silent UI freeze*, not an error ([[14 - JavaScript in React and Next.js/05 - Referential Equality|referential equality]], [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|mutating methods]]).

### Relative-time labels with an injected clock

"Posted 3 hours ago" labels depend on the current time — design the function to take `now` as a parameter and the nondeterminism vanishes without fake timers:

```ts
const now = new Date("2026-07-16T12:00:00Z");
it.each([
  ["2026-07-16T11:59:31Z", "just now"],
  ["2026-07-16T11:00:00Z", "1 hour ago"],
  ["2026-07-15T13:00:00Z", "yesterday"],   // policy pinned: calendar day, not 24h window
])("%s → %s", (iso, label) => {
  expect(formatRelative(new Date(iso), now)).toBe(label);
});
```

> [!tip] Parameterize the clock before you mock it
> An explicit `now` parameter is the cheaper cousin of `vi.useFakeTimers` ([[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|deterministic tests]]) — purity by signature design. Reach for fake timers only when the time dependency is scheduling (`setTimeout`), not just reading the clock.

### Parsing URL filters: hostile input as the hazard model

A product list drives its filters from the URL (`?minPrice=20&sort=price_asc`). URLs are user-editable and shared in Slack, so the hazard model is *hostile input*, and the happy path is the least interesting row:

```ts
it("survives garbage params without throwing", () => {
  expect(parseFilters(new URLSearchParams("minPrice=-5&sort=nonsense&utm_source=x")))
    .toEqual({ minPrice: 0, sort: "relevance" });   // clamp + fallback, unknowns ignored
});
```

Same input-selection discipline as the note's float example, different hazard: instead of representation traps, adversarial strings. This is boundary validation in miniature ([[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|runtime validation]]) — and because it's extracted from the page component, twenty edge cases cost milliseconds instead of twenty renders.

## 4. Interview Answer

Short answer:

> I unit test extracted, pure logic — parsing, calculation, state transitions — with a table of cases derived from the function's hazards: boundaries, invalid input, rounding/representation traps, failure paths. The happy path is one row. Vitest's `test.each` keeps the table readable, and the file doubles as the function's specification.

Deeper answer:

> The skill is input selection: a passing test on friendly inputs proves nothing about float drift, empty arrays, or locale-dependent parsing. I ask what representation the function relies on (floats? integer cents? code units vs graphemes?) and what policies it embodies (rounding, clamping, error type) and pin each with an assertion. If logic is hard to unit test because it's tangled in a component, the fix is usually extraction, not a heavier test. And I keep `toBe` vs `toEqual` deliberate — identity claims and structure claims are different specifications.

## 5. Practice

1. <details><summary>List the test cases you'd write for `chunk<T>(arr: T[], size: number): T[][]`.</summary>Even split (`[1,2,3,4], 2`); uneven remainder (`[1,2,3], 2` → `[[1,2],[3]]`); `size >= length` (single chunk); empty array (empty result); `size = 1`; invalid sizes (0, negative, non-integer — decide and pin the policy: throw or clamp); and a non-mutation check (input array unchanged — [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|mutation]] is a real hazard). Optionally an identity check that elements are the same references, not copies.</details>

2. <details><summary>Why is `expect(result).toEqual(expected)` sometimes too weak for a memoized function?</summary>`toEqual` checks structure, so a memoization bug that recomputes a fresh-but-equal object still passes. The memoization contract is *identity*: `expect(memoized(x)).toBe(memoized(x))`. This distinction is the testing mirror of [[14 - JavaScript in React and Next.js/05 - Referential Equality|referential equality]] — React deps and `React.memo` care about `Object.is`, so tests of caching behavior must too.</details>

3. <details><summary>A teammate writes `expect(fn).toHaveBeenCalled()` as the only assertion in five tests. What's the concern?</summary>It asserts interaction, not outcome — the tests pass if the collaborator is called with wrong arguments, or if calling it no longer produces the right result. Sometimes a call *is* the contract (analytics events); usually the outcome (return value, resulting state/UI) is checkable, stronger, and survives refactors of *how* the outcome is produced. Assert results where possible, interactions only when they are the observable contract ([[24 - Testing and Quality/10 - Mocking Seams and False Confidence|mocking]]).</details>

4. <details><summary>When is it fine to skip unit tests entirely for a piece of code?</summary>When the code has no logic to specify: a component that renders props straight to JSX, a function that just delegates, configuration objects. The behavior is either trivially visible or already covered by a component/integration test exercising it. Unit tests earn value proportional to decision density — testing glue yields tautologies that cost maintenance and catch nothing.</details>

## Related Notes

- [[04 - Functions Deep Dive/04 - Pure Functions and IIFE|Pure Functions and IIFE]]
- [[12 - Advanced Language Concepts/12 - Numbers and Floating Point|Numbers and Floating Point]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|React Component Testing Through User Behavior]]
- [[24 - Testing and Quality/10 - Mocking Seams and False Confidence|Mocking: Seams and False Confidence]]
