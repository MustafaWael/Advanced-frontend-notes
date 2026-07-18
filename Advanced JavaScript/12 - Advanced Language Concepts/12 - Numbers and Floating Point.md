---
tags: [javascript, numbers, floating-point]
module: "12 - Advanced Language Concepts"
priority: important
status: not-started
aliases: [IEEE 754, Number.EPSILON, Floating Point]
---

# Numbers and Floating Point

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain why `0.1 + 0.2 !== 0.3`, what IEEE 754 doubles can/can't represent, safe integers, and how to handle money.
- Production signal: you never store money as floats, and you compare computed numbers with a tolerance instead of `===`.
- Dependencies: [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]], [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]

## Source Anchors

- [MDN - Number](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number)
- [MDN - Number.EPSILON](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/EPSILON)
- [MDN - Number.MAX_SAFE_INTEGER](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/MAX_SAFE_INTEGER)
- [0.30000000000000004.com - Floating Point Guide](https://0.30000000000000004.com/)

## 1. Concept

JavaScript has one number type: a 64-bit **IEEE 754 double-precision float**. Every `Number` — including "integers" — is stored as sign + 11-bit exponent + 52-bit mantissa. This has two consequences that generate most number bugs:

1. **Most decimals can't be represented exactly.** `0.1` in binary is a repeating fraction, rounded to the nearest representable double. So `0.1 + 0.2` accumulates rounding error → `0.30000000000000004`.
2. **Integer precision is limited to 2^53.** Beyond `Number.MAX_SAFE_INTEGER` (9,007,199,254,740,991), integers lose precision — consecutive integers become indistinguishable.

```js
0.1 + 0.2 === 0.3;                 // false → 0.30000000000000004
9007199254740992 === 9007199254740993;  // true (!) — past safe integer range
0.1 + 0.2;                          // 0.30000000000000004
```

## 2. Why It Matters

- Money, quantities, IDs, and any computed comparison are everywhere in frontend code, and floats silently corrupt all of them: a cart total off by a cent, a `=== 0.3` check that never passes, a 64-bit database ID mangled on the way through JSON.
- "Why does `0.1 + 0.2` not equal `0.3`?" is a canonical interview question; the strong answer names IEEE 754 and gives the correct handling.

## 3. Comparing Floats and the Safe Integer Range

Never compare computed floats with `===`. Compare within a tolerance:

```js
Math.abs(0.1 + 0.2 - 0.3) < Number.EPSILON;   // true — EPSILON is the smallest representable gap near 1
```

`Number.EPSILON` (~2.2e-16) is the spacing between 1 and the next double; for values far from 1 you may need a scaled tolerance. For integers, check `Number.isSafeInteger(n)` before trusting arithmetic; for values beyond 2^53 (database bigints, snowflake IDs, timestamps in nanoseconds), use **BigInt** ([[12 - Advanced Language Concepts/10 - BigInt Date RegExp JSON|BigInt]]).

> [!warning] 64-bit IDs die in JSON
> An API returning a 64-bit integer ID (`"id": 12345678901234567890`) parsed by `JSON.parse` becomes a `Number` and loses precision — two different IDs can collapse to the same value, causing wrong-record bugs that are maddening to trace. Fix: serialize large IDs as *strings* on the server, or parse with a BigInt-aware reviver. Never let a 64-bit ID pass through a JS Number.

## 4. Money — Never Floats

Representing currency as floating dollars (`19.99`) guarantees rounding drift across additions, multiplications (tax, discounts), and comparisons. Two standard patterns:

- **Integer minor units**: store money as integer cents (`1999`), do all math in integers, format for display only. Simple, exact for addition/subtraction, and the most common approach.
- **Decimal library** (dinero.js, decimal.js): arbitrary-precision decimals when you need division, multi-currency, or complex rounding rules.

```js
// ❌ float dollars
0.1 + 0.2;                    // 0.30000000000000004
(19.99 * 3);                  // 59.97000000000001

// ✅ integer cents
const cents = 1999;
cents * 3;                    // 5997 → format as $59.97
```

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a cart shows `$59.97000000000001` and a "free shipping over $60" check misfires.

Buggy version:

```js
const total = items.reduce((sum, i) => sum + i.price, 0);   // prices like 19.99
if (total >= 60) applyFreeShipping();                        // float drift near the threshold
displayTotal(total);                                         // "$59.97000000000001"
```

Trace: float addition of `19.99` three times yields `59.97000000000001`; the display leaks the artifact, and a total that *should* be exactly `60.00` might compute as `59.999999...`, failing the threshold (or the reverse), producing a wrong shipping charge — a real money bug.

Production-safe fix — integer cents end to end:

```js
const totalCents = items.reduce((sum, i) => sum + i.priceCents, 0);  // 1999 + 1999 + 1999 = 5997
if (totalCents >= 6000) applyFreeShipping();                          // exact integer comparison
displayTotal(totalCents);                                            // format: (c/100).toFixed(2) → "$59.97"
```

Tradeoffs: integer cents is exact for add/subtract but needs care for *division* (splitting a bill, percentage discounts) where you must decide a rounding policy and handle remainders (allocate the leftover cent deterministically). For heavy financial math (interest, multi-currency, tax tables) a decimal library is worth the dependency. And `toFixed` for display *rounds* and returns a string — fine for output, but never round-trip through it for storage. The rule: compute in the smallest exact unit, format only at the edge.

## 6. Interview Answer

Short answer:

> JavaScript numbers are 64-bit IEEE 754 doubles, so most decimals (like 0.1) can't be represented exactly — `0.1 + 0.2` is `0.30000000000000004`. Compare computed floats within a tolerance (`Number.EPSILON`), not with `===`. Integers are exact only up to `Number.MAX_SAFE_INTEGER` (2^53−1); beyond that use BigInt. For money, use integer minor units (cents) or a decimal library — never floating dollars.

Deeper answer:

> The double format is sign + exponent + 52-bit mantissa, so binary-repeating fractions round and errors accumulate across operations; that's why threshold comparisons and displayed totals drift. Two production traps: 64-bit IDs lose precision through `JSON.parse` into a Number (serialize as strings or use a BigInt reviver), and money computed as floats produces off-by-a-cent bugs. The discipline is compute in the smallest exact unit (integer cents), decide an explicit rounding policy for division, and format to a string only at display.

## 7. Practice

1. <details><summary>Write a correct equality check for `0.1 + 0.2` and `0.3`, and explain why `===` fails.</summary>`Math.abs((0.1 + 0.2) - 0.3) < Number.EPSILON` → true. `===` fails because 0.1, 0.2, and 0.3 are each rounded to the nearest representable double, and the rounding errors of the sum don't match the rounding of the literal 0.3, leaving a ~5.5e-17 difference. Comparing floats requires a tolerance; `Number.EPSILON` is the gap between 1 and the next double (scale it for values far from 1).</details>

2. <details><summary>An API sends `"userId": 9007199254740993`. What happens in JS and how do you handle it?</summary>`JSON.parse` produces a Number, but 9007199254740993 is past `MAX_SAFE_INTEGER`, so it's rounded — possibly to 9007199254740992, colliding with a different id and causing wrong-record lookups. Handle it by having the server serialize large ids as strings (`"9007199254740993"`), or parse with a BigInt-aware reviver / a JSON library that preserves bigints. Never let a 64-bit id become a JS Number.</details>

3. <details><summary>Why is `19.99 * 3` unreliable for a price, and what's the fix?</summary>`19.99` isn't exactly representable, so multiplying accumulates error → `59.97000000000001`. Money math on floats drifts and leaks artifacts into displays and comparisons. Fix: store and compute in integer cents (`1999 * 3 = 5997`, exact), formatting to dollars only for display. For division/percentages, define a rounding policy and allocate remainder cents deterministically, or use a decimal library.</details>

4. <details><summary>Is `Number.isSafeInteger` about the value being an integer, the value being safe, or both?</summary>Both: it returns true only if the value is an integer *and* within the safe range (|n| ≤ 2^53−1), where every integer is exactly representable and distinct from its neighbors. `1.5` → false (not integer); `2**53` → false (integer but unsafe — indistinguishable from 2^53+1). Use it to guard integer arithmetic before trusting results; beyond the range, switch to BigInt.</details>

## Related Notes

- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/10 - BigInt Date RegExp JSON|BigInt Date RegExp JSON]]
- [[12 - Advanced Language Concepts/16 - Intl|Intl]]
- [[01 - Roadmap|Roadmap]]
