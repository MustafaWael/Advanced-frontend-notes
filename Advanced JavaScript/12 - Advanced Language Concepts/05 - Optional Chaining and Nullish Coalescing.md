---
tags: [javascript, language-concepts, optional-chaining-and-nullish-coalescing]
module: "12 - Advanced Language Concepts"
priority: must-know
status: not-started
---

# Optional Chaining and Nullish Coalescing

## Maturity Target

- Priority: #must-know
- Study time: 80-110 minutes
- Interview signal: you can explain `?.`, `??`, short-circuiting, nullish vs falsy, and operator precedence.
- Production signal: nested API data, optional callbacks, controlled inputs, and config defaults are handled without unsafe guards.
- Dependencies: [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]], [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]

## Source Anchors

- [MDN Optional chaining](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining)
- [MDN Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)
- [MDN Nullish coalescing assignment](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing_assignment)
- [MDN Logical OR assignment](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Logical_OR_assignment)

## 1. Concept

Optional chaining (`?.`) safely reads through a path that may contain `null` or `undefined`.

Nullish coalescing (`??`) provides a fallback only when the left side is `null` or `undefined`.

```js
const city = user?.address?.city;
const label = product.name ?? "Untitled";
```

These operators are about missing values, not all falsy values.

## 2. Why It Matters

APIs often return partial data. React components receive optional callbacks. URL and feature-flag config can omit values. Before these operators, code often used noisy guard chains or unsafe `||` defaults.

The production bug is usually one of two things:

- reading through `undefined` and crashing;
- using `||` and overwriting valid `0`, `false`, or `""`.

## 3. Accurate Mechanism

`obj?.prop` checks whether `obj` is `null` or `undefined`. If it is, the expression evaluates to `undefined` and stops the chain.

```js
const user = null;
console.log(user?.profile?.name); // undefined
```

Optional call:

```ts
props.onSuccess?.();
```

Optional element access:

```ts
const first = response.items?.[0];
```

`??` checks only nullish values:

```js
console.log(0 ?? 10);      // 0
console.log("" ?? "x");    // ""
console.log(false ?? true); // false
console.log(null ?? "x");  // "x"
```

## 4. Mental Model

> [!tip] `??` guards missing, `||` guards falsy
> Use `??` when the fallback should apply only for `null`/`undefined` — it preserves valid `0`, `""`, and `false`. Reach for `||` only when every falsy value should fall back. Mixing them up is how `count || 10` turns a real `0` into `10`.

Use `?.` when a link in the chain may be missing.

Use `??` when the fallback means "missing", not "falsy."

Use explicit checks when the fallback means something more specific, such as "empty string after trimming" or "array has no items."

## 5. Real Frontend Example: API Data

```tsx
type ProductResponse = {
  product?: {
    name?: string | null;
    inventory?: {
      count?: number | null;
    } | null;
  } | null;
};

function ProductHeader({ data }: { data: ProductResponse }) {
  const name = data.product?.name ?? "Unnamed product";
  const count = data.product?.inventory?.count ?? 0;

  return (
    <header>
      <h1>{name}</h1>
      <span>{count} in stock</span>
    </header>
  );
}
```

Why this works:

- missing `product`, `name`, or `inventory` does not crash render;
- `count = 0` remains `0`, not a fallback;
- fallback meaning is explicit.

## 6. Real Frontend Bug: Wrong Default With `||`

Problem:

```ts
const timeout = config.timeout || 5000;
const showSidebar = settings.showSidebar || true;
```

Bugs:

- `timeout = 0` becomes `5000`;
- `showSidebar = false` becomes `true`.

Fix:

```ts
const timeout = config.timeout ?? 5000;
const showSidebar = settings.showSidebar ?? true;
```

If `0` is invalid for your domain, validate it directly:

```ts
const timeout =
  typeof config.timeout === "number" && config.timeout > 0
    ? config.timeout
    : 5000;
```

## 7. Short-Circuiting Details

Only a continuous optional chain is protected.

```js
const user = null;

console.log(user?.profile?.name); // undefined
```

But grouping can end the chain:

```js
// Throws because (user?.profile) is undefined, then .name is read.
console.log((user?.profile).name);
```

Optional chaining does not hide errors after a non-nullish value exists.

```js
const user = { profile: null };
console.log(user?.profile.name); // TypeError
```

Fix:

```js
console.log(user?.profile?.name); // undefined
```

## 8. Operator Precedence

You cannot mix `??` with `||` or `&&` without parentheses.

```js
// SyntaxError:
// const value = a ?? b || c;

const valueA = (a ?? b) || c;
const valueB = a ?? (b || c);
```

The two versions have different meanings. Add parentheses based on the domain rule.

## 9. Logical Assignment

```js
options.timeout ??= 5000; // assign only if null or undefined
title ||= "Untitled";     // assign if falsy
enabled &&= canUseFeature(); // assign only if currently truthy
```

Use `??=` for defaults where `0`, `false`, and `""` should be preserved.

## 10. Production Tradeoffs

| Pattern | Good when | Risk |
| --- | --- | --- |
| `a?.b?.c` | missing nested data is expected | can hide a data contract bug if overused |
| `a ?? fallback` | fallback only for null/undefined | empty strings remain empty |
| `a || fallback` | any falsy value is invalid | overwrites valid falsy values |
| optional callback `onDone?.()` | callback is truly optional | missed required handler bug |
| explicit validation | domain rule is stricter | more code |

## Real-World Use Cases

### Hydrating preferences from `localStorage`

An editor persists user preferences. `localStorage.getItem` returns `null` for missing keys, and saved values legitimately include `false` and small numbers — exactly the split `??` was built for.

```ts
const raw = localStorage.getItem("editor:prefs");
const prefs = raw == null ? {} : (JSON.parse(raw) as Partial<Prefs>);

const zoom = prefs.zoom ?? 1;          // saved zoom 0.5 survives
const autosave = prefs.autosave ?? true; // saved `false` survives
```

Works because `getItem`'s "missing" signal is `null` — nullish — so `??` applies defaults only for genuinely absent keys, while `||` would overwrite a saved `autosave: false` on every load.

### `??=` as a lazy per-key cache

`Intl.NumberFormat` construction is expensive enough to matter in a price-heavy table, so formatters are created once per currency.

```ts
const priceFormatters: Record<string, Intl.NumberFormat> = {};

function formatPrice(amount: number, currency: string) {
  priceFormatters[currency] ??= new Intl.NumberFormat("en", {
    style: "currency",
    currency,
  });
  return priceFormatters[currency].format(amount);
}
```

Works because `??=` assigns only when the slot is nullish — first call constructs, every later call reads.

> [!warning]
> `||=` looks interchangeable but re-runs the initializer whenever the cached value is falsy. Memoize a computation that can return `0` or `""` with `||=` and the cache silently never hits.

### `?.` turning a contract break into silently wrong data

The backend renames `inventory.count` to `inventory.available`. Nothing throws — every product just shows "0 in stock", and monitoring stays quiet because the crash was optional-chained away.

```ts
const count = data.product?.inventory?.count ?? 0;
// renamed field → undefined → 0, for every product, forever
```

This is the mechanism working as designed: `?.` converts what should be a loud failure into `undefined`, and `??` converts `undefined` into a plausible number. Reserve `?.` for fields that are *genuinely* optional in the contract, and validate required shapes at the API boundary instead — see [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]] on runtime response validation.

> [!tip]
> A quick heuristic in review: `?.` on a field the backend guarantees is a red flag; it documents distrust the type system should be resolving.

## 11. Interview Answer

**Short version:** `?.` returns `undefined` instead of throwing when the left side is `null` or `undefined`. `??` returns the fallback only for `null` or `undefined`, unlike `||`, which falls back for any falsy value.

**Strong version:** Optional chaining short-circuits a continuous property, element, or call chain when the checked value is nullish. It does not guard against all falsy values, and grouping can end the protected chain. Nullish coalescing solves defaulting bugs where `0`, `false`, or `""` are valid. In production I use `?.` for genuinely optional data, `??` for missing-value defaults, and explicit validation when the domain rule is stricter than nullish.

## 12. Common Mistakes

- Using `||` for defaults where `0`, `false`, or `""` are valid.
- Overusing `?.` and hiding a broken API contract.
- Forgetting the result of `user?.name` can be `undefined`.
- Thinking `?.` protects grouped follow-up access.
- Mixing `??` with `||` or `&&` without parentheses.
- Using optional call for a callback that should be required.

## 13. Practice

1. Predict:

```js
const obj = { a: { b: 0 } };
console.log(obj?.a?.b ?? "missing");
console.log(obj?.a?.b || "missing");
console.log(obj?.x?.y ?? "missing");
```

2. Rewrite `config && config.ui && config.ui.theme || "light"` safely.
3. Explain the difference between `onClick?.()` and `onClick()`.
4. Show a case where `(user?.profile).name` throws.
5. Pick `??`, `||`, or explicit validation for a form field where `""` is invalid but `0` is valid.

## Related Notes

- [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]]
- [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
