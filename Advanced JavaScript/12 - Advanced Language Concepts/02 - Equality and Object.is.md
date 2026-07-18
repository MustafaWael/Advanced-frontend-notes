---
tags: [javascript, language-concepts, equality-and-objectis]
module: "12 - Advanced Language Concepts"
priority: must-know
status: not-started
---

# Equality and Object.is

## Maturity Target

- Priority: #must-know
- Study time: 80-110 minutes
- Interview signal: you can compare `==`, `===`, `Object.is`, and SameValueZero with real edge cases.
- Production signal: you avoid coercion bugs, know React's identity comparison model, and choose the right equality for `NaN`, `-0`, maps, sets, and dependencies.
- Dependencies: [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]], [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]], [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]

## Source Anchors

- [MDN Equality comparisons and sameness](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Equality_comparisons_and_sameness)
- [MDN Strict equality](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Strict_equality)
- [MDN Equality](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Equality)
- [MDN Object.is](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is)
- [React useState caveats](https://react.dev/reference/react/useState)

## 1. Concept

JavaScript has several equality algorithms.

| Operation | Coerces types? | `NaN` equals itself? | Distinguishes `-0` and `+0`? |
| --- | --- | --- | --- |
| `==` | yes | no | no |
| `===` | no | no | no |
| `Object.is` | no | yes | yes |
| SameValueZero | no | yes | no |

> [!tip] Default to strict equality
> Most production code should use `===`, with `Object.is` for exact sameness edge cases and React identity reasoning.

## 2. Why It Matters

Equality bugs often look like state bugs:

- memoized React components re-render because object references changed;
- state does not update because the same reference was reused;
- `NaN` is not found by `indexOf`;
- `Set` dedupes `NaN` as expected but `===` does not;
- loose equality makes form input comparisons pass unexpectedly;
- `-0` matters in numeric/chart/graphics code.

## 3. Accurate Mechanism

`==` uses Abstract Equality Comparison, which may convert operands before comparing. `===` uses strict equality: if types differ, it returns `false`. `Object.is` uses SameValue. `Map`, `Set`, and `Array.prototype.includes` use SameValueZero.

```js
console.log(NaN === NaN);              // false
console.log(Object.is(NaN, NaN));      // true

console.log(-0 === 0);                 // true
console.log(Object.is(-0, 0));         // false

console.log([NaN].indexOf(NaN));       // -1
console.log([NaN].includes(NaN));      // true
```

Reason:

- `indexOf` uses strict equality;
- `includes` uses SameValueZero.

## 4. Mental Model

Use this default:

- `===` for normal business comparisons;
- `value == null` only when you intentionally mean `value === null || value === undefined`;
- `Object.is` when explaining React bailouts or numeric edge cases;
- `Number.isNaN` when validating `NaN`;
- deep equality only when you deliberately implement or import it.

Objects compare by identity, not by shape.

```js
console.log({ a: 1 } === { a: 1 }); // false
console.log([] === []);             // false
```

## 5. Real Frontend Bug: Dependency Array Identity

Problem:

```tsx
function ProductList({ category }: { category: string }) {
  const filters = { category, inStock: true };

  useEffect(() => {
    fetchProducts(filters);
  }, [filters]);

  return null;
}
```

Bug:

- each render creates a new object;
- React compares dependencies with `Object.is`;
- `Object.is(previousFilters, nextFilters)` is `false`;
- the effect runs again even when `category` did not change.

Fix:

```tsx
function ProductList({ category }: { category: string }) {
  useEffect(() => {
    fetchProducts({ category, inStock: true });
  }, [category]);

  return null;
}
```

Alternative when the object must be shared:

```tsx
const filters = useMemo(
  () => ({ category, inStock: true }),
  [category]
);
```

## 6. Loose Equality: The One Useful Pattern

> [!tip] The one safe loose equality
> `value == null` is a common intentional pattern because only `null` and `undefined` loosely equal each other.

```ts
function hasValue(value: string | null | undefined) {
  return value != null;
}
```

This accepts empty string:

```js
console.log("" != null); // true
console.log(0 != null);  // true
```

> [!warning] Loose equality coerces surprisingly
> Avoid broad loose equality for normal comparisons.

```js
console.log("" == false); // true
console.log([] == false); // true
console.log("0" == 0);    // true
```

## 7. `NaN` and Validation

Use `Number.isNaN` to check the actual `NaN` value without coercion.

```js
console.log(isNaN("hello"));        // true, because it coerces first
console.log(Number.isNaN("hello")); // false
console.log(Number.isNaN(NaN));     // true
```

Practical form parsing:

```ts
function parseQuantity(raw: string): number | null {
  const value = Number(raw);
  return Number.isNaN(value) ? null : value;
}
```

> [!warning] Empty string becomes zero
> If an empty string should be invalid, check it before `Number("")` turns it into `0`.

## 8. Production Tradeoffs

| Comparison | Use for | Avoid when |
| --- | --- | --- |
| `===` | ordinary comparisons | you need to match `NaN` |
| `== null` | null or undefined check | comparing user data broadly |
| `Object.is` | React identity and numeric exactness | general object shape comparison |
| SameValueZero collections | `Set`, `Map`, `includes` behavior | expecting `-0` distinction |
| Deep equality | tests, snapshots, rare memo cases | hot render paths without measurement |

## Real-World Use Cases

### External store selector returning a fresh object

A Zustand/`useSyncExternalStore` selector builds a new object on every call. React compares the previous and next snapshot with `Object.is`, sees a new reference each time, and re-renders on every store change — or, with `useSyncExternalStore`, throws "getSnapshot should be cached" and can loop.

```tsx
// Re-renders on every store update — new object identity each call.
const cart = useStore((s) => ({ items: s.items, total: s.total }));

// Fix: select primitives (compared by value), or use a shallow comparator.
const items = useStore((s) => s.items);
const total = useStore((s) => s.total);
```

The subscription bailout is `Object.is(prevSnapshot, nextSnapshot)` — objects pass it only by identity, primitives by value, so selecting primitives restores the bailout. See [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]].

### Deduping metric values that include `NaN`

A data-cleaning step dedupes numeric readings from a CSV import where failed parses produced `NaN`. `Set` uses SameValueZero, so all the `NaN`s collapse into one — but a hand-rolled dedupe with `===` or `indexOf` keeps every `NaN`, because `NaN === NaN` is false.

```ts
const readings = [12.5, NaN, 12.5, NaN, 7];

const viaSet = [...new Set(readings)];              // [12.5, NaN, 7]
const viaIndexOf = readings.filter(
  (v, i) => readings.indexOf(v) === i
);                                                   // [12.5, NaN, 12.5, NaN, 7] — indexOf(NaN) is always -1
```

`Set` and `includes` use **SameValueZero** (`NaN` equals itself); `indexOf` uses **strict equality** (`NaN` never matches). Filter out `NaN` with `Number.isNaN` before deduping if it should not survive at all.

### `-0` leaking into chart labels

A finance dashboard rounds small deltas for display. Rounding a tiny negative produces `-0`, and number formatting happily prints the sign — users file bugs about "-0.0%".

```ts
const delta = -0.004;
const rounded = Number(delta.toFixed(1)); // -0

console.log(`${delta.toFixed(1)}%`);      // "-0.0%"
console.log(Object.is(rounded, -0));      // true — the only direct way to see it
const display = rounded === 0 ? 0 : rounded; // normalize: -0 === 0 is true
```

`===` treats `-0` and `+0` as equal (handy for normalizing), while `Object.is` distinguishes them (handy for detecting). Know which one your formatting path relies on.

> [!tip]
> `x === 0 ? 0 : x` is the idiomatic one-liner to scrub `-0` before display, precisely because strict equality ignores the sign of zero.

## 9. Interview Answer

**Short version:** `==` compares after coercion, `===` compares without coercion, and `Object.is` is like strict sameness except it treats `NaN` as equal to itself and distinguishes `-0` from `+0`.

**Strong version:** JavaScript has multiple equality algorithms. `==` follows the abstract equality algorithm and can coerce values, which is why `"" == false` and `[] == false` are true. `===` avoids coercion but still has numeric edge cases: `NaN !== NaN` and `-0 === +0`. `Object.is` uses SameValue, fixing those two cases. SameValueZero is used by `Map`, `Set`, and `includes`, so `NaN` works as a key and duplicate but `-0` and `+0` are treated as the same. React uses `Object.is` for state and hook dependency comparisons, so object identity matters.

## 10. Common Mistakes

- Using `==` because it "usually works."
- Using global `isNaN` for validation without realizing it coerces.
- Expecting two object literals with the same fields to be equal.
- Thinking `React.memo` compares object props deeply.
- Forgetting that `setState(sameReference)` can bail out.
- Using `indexOf(NaN)` and expecting it to find `NaN`.

## 11. Practice

1. Predict each output:

```js
console.log(null == undefined);
console.log(null === undefined);
console.log(Object.is(NaN, NaN));
console.log(Object.is(-0, 0));
console.log([NaN].includes(NaN));
console.log([NaN].indexOf(NaN));
```

2. Explain why `options={{ retry: 3 }}` can break memoization.
3. Write a safe `isPresent(value)` helper that accepts `0` and `""`.
4. Explain the difference between `Number.isNaN("x")` and `isNaN("x")`.
5. Name which equality algorithm `Set` uses and why `new Set([NaN, NaN]).size` is `1`.

## Related Notes

- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]
- [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[01 - Roadmap|Roadmap]]
