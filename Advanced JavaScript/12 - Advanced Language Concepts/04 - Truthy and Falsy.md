---
tags: [javascript, language-concepts, truthy-and-falsy]
module: "12 - Advanced Language Concepts"
priority: must-know
status: not-started
---

# Truthy and Falsy

## Maturity Target

- Priority: #must-know
- Study time: 70-100 minutes
- Interview signal: you can list falsy values, separate falsy from nullish, and explain JSX `0` rendering.
- Production signal: you do not drop valid `0`, `false`, or `""` values when rendering, defaulting, or validating forms.
- Dependencies: [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]], [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]

## Source Anchors

- [MDN Falsy](https://developer.mozilla.org/en-US/docs/Glossary/Falsy)
- [MDN Truthy](https://developer.mozilla.org/en-US/docs/Glossary/Truthy)
- [MDN Logical AND](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Logical_AND)
- [MDN Logical OR](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Logical_OR)
- [MDN Nullish coalescing](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing)

## 1. Concept

Truthy and falsy describe how values behave in boolean contexts such as `if`, `while`, `!`, `&&`, and `||`.

Falsy values:

- `false`
- `0`
- `-0`
- `0n`
- `""`
- `null`
- `undefined`
- `NaN`

Everything else is truthy, including:

- `[]`
- `{}`
- `"false"`
- `"0"`
- `new Boolean(false)`

Browsers also have the legacy special case `document.all`, but you should not design application logic around it.

## 2. Why It Matters

Frontend code often treats "missing" and "empty" as the same thing by accident.

Examples:

- quantity `0` is valid but falls through to a default;
- empty string is a valid controlled input but gets replaced;
- `false` is a valid setting but gets overwritten;
- JSX renders a literal `0`;
- `[]` is truthy, so `if (items)` does not mean "has items."

## 3. Accurate Mechanism

Boolean contexts apply the `ToBoolean` operation. Unlike `==`, this does not run a long coercion chain. It is essentially a fixed truthiness table.

```js
console.log(Boolean(0));       // false
console.log(Boolean("0"));     // true
console.log(Boolean([]));      // true
console.log(Boolean({}));      // true
console.log(Boolean(NaN));     // false
```

`&&` and `||` return operand values, not converted booleans.

```js
console.log(0 && "x");         // 0
console.log("Ada" && "x");     // "x"
console.log("" || "fallback"); // "fallback"
console.log("Ada" || "fallback"); // "Ada"
```

## 4. Nullish Is Different

Nullish means only `null` or `undefined`.

```js
console.log(0 || 10);  // 10
console.log(0 ?? 10);  // 0

console.log("" || "Untitled"); // "Untitled"
console.log("" ?? "Untitled"); // ""

console.log(false || true); // true
console.log(false ?? true); // false
```

Use `??` when `0`, `false`, or `""` are valid values.

## 5. Real Frontend Bug: JSX Renders `0`

Problem:

```tsx
function Comments({ comments }: { comments: Comment[] }) {
  return (
    <section>
      {comments.length && <CommentList comments={comments} />}
    </section>
  );
}
```

Bug:

- when `comments.length` is `0`, `&&` returns `0`;
- React renders `0` as text;
- the page shows a stray zero.

> [!warning] `{count && <X/>}` renders a stray `0`
> `&&` returns its left operand when falsy, and `0` is falsy — so React renders the number `0` as text. Guard with a real boolean (`count > 0 && ...`) or a ternary, not truthiness.

Fix:

```tsx
return (
  <section>
    {comments.length > 0 && <CommentList comments={comments} />}
  </section>
);
```

Other valid fixes:

```tsx
{!!comments.length && <CommentList comments={comments} />}
{comments.length > 0 ? <CommentList comments={comments} /> : null}
```

The explicit comparison is usually clearest.

## 6. Real Frontend Bug: Defaulting Form Values

Problem:

```ts
const retries = form.retries || 3;
const displayName = form.displayName || "Anonymous";
const emailOptIn = form.emailOptIn || true;
```

Bugs:

- `retries = 0` becomes `3`;
- `displayName = ""` becomes `"Anonymous"`;
- `emailOptIn = false` becomes `true`.

Fix:

```ts
const retries = form.retries ?? 3;
const displayName = form.displayName ?? "Anonymous";
const emailOptIn = form.emailOptIn ?? true;
```

If an empty string should fall back, make that rule explicit:

```ts
const displayName =
  form.displayName.trim() === "" ? "Anonymous" : form.displayName;
```

## 7. Common Checks

```ts
// Missing only:
if (value == null) {
  // null or undefined
}

// Non-empty string:
if (typeof value === "string" && value.trim() !== "") {
  // string with visible content
}

// Non-empty array:
if (Array.isArray(items) && items.length > 0) {
  // has at least one item
}

// Boolean flag:
if (flag === true) {
  // explicitly true
}
```

## 8. Production Tradeoffs

| Check | Meaning | Risk |
| --- | --- | --- |
| `if (value)` | any truthy value | loses `0`, `""`, `false`, `NaN` |
| `value != null` | not null or undefined | accepts empty strings and zero |
| `value ?? fallback` | fallback for nullish only | does not treat empty string as missing |
| `value || fallback` | fallback for any falsy value | overwrites valid falsy values |
| `items.length > 0` | array has items | requires `items` to be an array |

## Real-World Use Cases

The classic interview trap for this topic — `{count && <Badge />}` rendering a stray `0` — is traced in section 5 above. Beyond it, truthiness bugs cluster wherever code equates "falsy" with "absent".

### Query-string builder dropping `0` and `false`

A search page builds its URL from filter state. A truthiness filter drops `minPrice=0` and `inStock=false`, so "free items, including out of stock" silently becomes the unfiltered search — and the shared URL reproduces the wrong results.

```ts
const filters = { query: "ssd", minPrice: 0, inStock: false };

// Bug: keeps only truthy values → [["query", "ssd"]]
const broken = Object.entries(filters).filter(([, value]) => value);

// Fix: drop only missing values
const search = new URLSearchParams(
  Object.entries(filters)
    .filter(([, value]) => value != null)
    .map(([key, value]) => [key, String(value)])
);
```

Fails because `filter(([, value]) => value)` applies `ToBoolean`, collapsing "value is `0`/`false`" into "value is absent" — the falsy-vs-nullish distinction from section 4. See [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]].

### `"false"` from env vars and feature flags

Environment variables, URL params, and `localStorage` are always strings — and `Boolean("false")` is `true`.

```ts
// .env: NEXT_PUBLIC_NEW_CHECKOUT=false
if (process.env.NEXT_PUBLIC_NEW_CHECKOUT) {
  enableNewCheckout(); // runs anyway — "false" is a non-empty string
}

// Fix: compare the string explicitly
const newCheckoutEnabled = process.env.NEXT_PUBLIC_NEW_CHECKOUT === "true";
```

Fails because `ToBoolean` consults the fixed falsy table only — string *content* is irrelevant, any non-empty string is truthy. See [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]] for parsing at boundaries.

> [!warning]
> Kill switches are the worst place for this bug: the flag you flip to `"false"` mid-incident still evaluates truthy, and the feature stays on.

### `.filter(Boolean)` as a deliberate truthiness pass

Compacting optional class names or nullable lookups is the idiomatic *good* use of `ToBoolean`:

```ts
const className = [base, isActive && "active", size && `size-${size}`]
  .filter(Boolean)
  .join(" ");
```

The same idiom on numeric data deletes legitimate zeros:

```js
[3, 0, 7].filter(Boolean); // [3, 7]
```

> [!tip]
> `.filter(Boolean)` is safe when the array holds strings/JSX where every falsy value really is junk. For numbers or mixed data, filter with `value != null` instead.

## 9. Interview Answer

**Short version:** Falsy values are `false`, `0`, `-0`, `0n`, `""`, `null`, `undefined`, and `NaN`. Everything else is truthy. Nullish is narrower: only `null` and `undefined`.

**Strong version:** Boolean contexts use `ToBoolean`, so objects and arrays are truthy even when empty. `&&` and `||` return original operand values, not booleans, which is why `{count && <Badge />}` can render `0` in React. `??` exists because `||` is too broad for defaults when `0`, `false`, or `""` are valid. In production I choose conditions based on meaning: present, non-empty, non-zero, explicitly true, or valid parsed value.

## 10. Common Mistakes

- `if (items)` to check for a non-empty array.
- `value || default` when `0`, `false`, or `""` are valid.
- `{count && <Component />}` in JSX.
- Assuming `"false"` is false.
- Assuming `[]` or `{}` are false.
- Using `!value` when you mean `value == null`.

## 11. Practice

1. Predict:

```js
console.log(Boolean([]));
console.log(Boolean("0"));
console.log(0 || "zero");
console.log(0 ?? "zero");
console.log(false ?? "fallback");
console.log([] && "yes");
```

2. Fix `{items.length && <List />}`.
3. Write a condition that treats `0` as valid but rejects `null` and `undefined`.
4. Explain why `[] == false` can be true while `Boolean([])` is true.
5. Replace three unsafe `||` defaults with `??` or explicit checks.

## Related Notes

- [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]
- [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]
- [[01 - Roadmap|Roadmap]]
