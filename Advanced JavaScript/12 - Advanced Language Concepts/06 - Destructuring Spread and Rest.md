---
tags: [javascript, language-concepts, destructuring-spread-and-rest]
module: "12 - Advanced Language Concepts"
priority: must-know
status: not-started
---

# Destructuring Spread and Rest

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can explain extraction, expansion, collection, iterables, own enumerable properties, defaults, and shallow copies.
- Production signal: props, state updates, API responses, and function signatures stay readable without accidental mutation or unsafe deep destructuring.
- Dependencies: [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]], [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]

## Source Anchors

- [MDN Destructuring](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Destructuring_assignment)
- [MDN Spread syntax](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax)
- [MDN Rest parameters](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/rest_parameters)
- [MDN Enumerability and ownership](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Enumerability_and_ownership_of_properties)

## 1. Concept

The same `...` token appears in different roles.

- Destructuring extracts values.
- Spread expands values.
- Rest collects remaining values.

```js
const [first, ...rest] = [1, 2, 3];
console.log(first); // 1
console.log(rest);  // [2, 3]

const copy = { ...user, role: "admin" };
```

## 2. Why It Matters

These features are everywhere in frontend code:

- React props;
- hook return values;
- immutable state updates;
- API response shaping;
- component prop forwarding;
- function options objects;
- array merging and deduping.

They are powerful but easy to overuse. Deep destructuring can crash when data is missing, and object spread is not a deep clone.

## 3. Accurate Mechanism

Array destructuring uses the iterable protocol.

```js
const [a, b] = new Set(["x", "y", "z"]);
console.log(a, b); // "x" "y"
```

Object destructuring reads properties by key.

```js
const { name, role = "viewer" } = user;
```

Object defaults apply only when the property value is `undefined`, not `null`.

```js
const { role = "viewer" } = { role: null };
console.log(role); // null
```

Object spread copies own enumerable properties into a new object. It is shallow.

## 4. Mental Model

> [!warning] Spread copies one level only
> A spread (`{...obj}`, `[...arr]`) copies the top level; nested objects and arrays are still shared references. Mutating a nested field on the "copy" mutates the original — the classic shallow-copy state bug. Copy each nested level you intend to change.

Destructuring is a read.

Spread is a copy/expansion at one level.

Rest is "everything not already taken."

When objects are involved, ask:

- are nested objects shared?
- are non-enumerable or prototype properties needed?
- do later spreads overwrite earlier properties?
- can the right-hand side be `null` or `undefined`?

## 5. Real Frontend Example: Props

```tsx
type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

function Button({
  variant = "primary",
  className,
  ...buttonProps
}: ButtonProps) {
  return (
    <button
      className={buildClassName(variant, className)}
      {...buttonProps}
    />
  );
}
```

Why it works:

- `variant` and `className` are consumed by the component;
- `buttonProps` collects native button props like `onClick`, `disabled`, and `type`;
- spreading forwards those props to the DOM element.

Production caution: order matters.

```tsx
<button {...buttonProps} type="button" />
```

Here `type="button"` wins over `buttonProps.type`.

```tsx
<button type="button" {...buttonProps} />
```

Here caller-provided `type` wins.

Choose intentionally.

## 6. Real Frontend Bug: Shallow Copy Mutation

Problem:

```ts
const next = { ...state };
next.user.preferences.theme = "dark";
setState(next);
```

Bug:

- `next` is a new top-level object;
- `next.user` is the same object as `state.user`;
- `preferences` is also shared;
- previous state was mutated.

Fix:

```ts
setState((current) => ({
  ...current,
  user: {
    ...current.user,
    preferences: {
      ...current.user.preferences,
      theme: "dark"
    }
  }
}));
```

Why it works: every object along the changed path receives a new reference.

## 7. Safe API Destructuring

Avoid destructuring deeply from uncertain API data.

```ts
// Risky: throws if data or user is missing.
const {
  data: {
    user: {
      profile: { avatar }
    }
  }
} = response;
```

Safer:

```ts
const avatar = response.data?.user?.profile?.avatar ?? DEFAULT_AVATAR;
```

Use destructuring when the shape is guaranteed. Use optional chaining or validation when it is not.

## 8. Rest Parameters vs `arguments`

```ts
function log(level: "info" | "error", ...messages: string[]) {
  console[level](messages.join(" "));
}
```

Rest parameters create a real array. The legacy `arguments` object is array-like, not an array, and is unavailable in arrow functions.

## 9. Production Tradeoffs

| Feature | Best use | Risk |
| --- | --- | --- |
| Array destructuring | tuples, hooks, iterables | unclear names for long tuples |
| Object destructuring | props/options | crashes on missing nested data |
| Object spread | immutable top-level update | shallow copy only |
| Rest props | forwarding HTML props | leaking unsupported props to DOM |
| Rest parameters | variadic functions | hiding a loose API shape |

## Real-World Use Cases

### Omitting a key immutably with rest

Stripping a sensitive field before a response, or removing an entry from keyed state, is the standard "immutable delete":

```ts
// API route: never send the hash to the client
const { passwordHash, ...publicUser } = user;
return Response.json(publicUser);

// UI state: dismiss one toast from a keyed map
const { [toastId]: dismissed, ...remainingToasts } = toastsById;
setToastsById(remainingToasts);
```

Works because rest collects the *remaining* own enumerable properties into a fresh object — the original is untouched, so React sees a new reference. The computed key `[toastId]:` extracts a dynamic property.

> [!warning]
> The omission is shallow like everything else here: `publicUser` still shares nested objects with `user`, and linters flag the unused `passwordHash`/`dismissed` binding unless configured (`ignoreRestSiblings`).

### Config merge where `undefined` beats the default

An API client merges caller options over defaults. The spread merge breaks when a caller passes an explicitly-undefined key:

```ts
const defaults = { timeout: 5000, retries: 3 };

function createClient(options: Partial<ClientConfig>) {
  const config = { ...defaults, ...options };
  // createClient({ timeout: undefined }) → config.timeout === undefined
}
```

Fails because spread copies own enumerable keys **even when their value is `undefined`** — the later spread wins with `undefined`. Destructuring defaults have the opposite rule (they fire *on* `undefined`), which makes them the fix:

```ts
function createClient({ timeout = 5000, retries = 3 }: Partial<ClientConfig> = {}) {
  // timeout: undefined → 5000; the `= {}` keeps createClient() callable with no args
}
```

See [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]] for the matching `??` defaulting rules.

### `Math.max(...samples)` blowing the call stack

An analytics view computes the worst response time over ~200k samples and crashes with `RangeError: Maximum call stack size exceeded` — in production only, because dev datasets were small.

```ts
const worst = Math.max(...samples); // RangeError on large arrays

const worstSafe = samples.reduce(
  (max, value) => (value > max ? value : max),
  -Infinity
);
```

Fails because argument spread materializes **every element as a separate stack-allocated argument**, and engines cap argument counts (roughly 65k-125k). `list.push(...bigChunk)` hits the same wall. See [[02 - JavaScript Runtime Foundations/04 - Call Stack|Call Stack]].

## 10. Interview Answer

**Short version:** Destructuring extracts values, spread expands values, and rest collects remaining values. Array destructuring and array spread use iterables. Object spread copies own enumerable properties and is shallow.

**Strong version:** Array destructuring consumes the iterable protocol, so it works on arrays, sets, strings, and generators. Object destructuring reads properties by key and supports renaming and defaults, but defaults apply only for `undefined`. Object spread creates a new object with own enumerable properties; it does not copy prototypes, non-enumerable properties, or nested objects deeply. In React, spread and rest are useful for immutable updates and prop forwarding, but order matters and nested updates need structural sharing.

## 11. Common Mistakes

- Assuming `{ ...obj }` deep clones.
- Destructuring deeply from nullable API data.
- Forgetting defaults do not apply to `null`.
- Spreading props in the wrong order.
- Passing rest props to DOM elements without filtering invalid custom props.
- Using `arguments` instead of rest parameters.
- Spreading a plain object into an array: `[...obj]` throws unless the object is iterable.

## 12. Practice

1. Predict:

```js
const [a, b = 5, c = 3] = [1, undefined, null];
console.log(a, b, c);

const { role = "viewer" } = { role: null };
console.log(role);
```

2. Fix a nested state update using structural sharing.
3. Explain the difference between `{ ...obj }` and `[...iterable]`.
4. Write a component that consumes `variant` and forwards the rest of button props.
5. Explain why destructuring a `Set` works.

## Related Notes

- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
- [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[17 - Practical Frontend Scenarios/05 - Avoiding Mutation in State|Avoiding Mutation in State]]
- [[01 - Roadmap|Roadmap]]
