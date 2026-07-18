---
tags: [javascript, arrays, find-some-every-includes]
module: "07 - Arrays and Iteration"
priority: must-know
status: not-started
---

# find some every includes

## Maturity Target

- Priority: #must-know
- Study time: 70-95 minutes
- Interview signal: you can explain short-circuiting, return values, SameValueZero, and empty-array edge cases.
- Production signal: you use the question-shaped method instead of scanning more data than needed.
- Dependencies: [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]], [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]

## Source Anchors

- [MDN Array.prototype.find](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/find)
- [MDN Array.prototype.some](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/some)
- [MDN Array.prototype.every](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/every)
- [MDN Array.prototype.includes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/includes)
- [ECMAScript SameValueZero](https://tc39.es/ecma262/#sec-samevaluezero)

## 1. Concept

These methods answer search and condition questions:

| Method | Question | Return value |
| --- | --- | --- |
| `find(fn)` | Which first item matches? | element or `undefined` |
| `findIndex(fn)` | Where is the first match? | index or `-1` |
| `findLast(fn)` | Which last item matches? | element or `undefined` |
| `findLastIndex(fn)` | Where is the last match? | index or `-1` |
| `some(fn)` | Does at least one item match? | boolean |
| `every(fn)` | Do all items match? | boolean |
| `includes(value)` | Is this exact value present? | boolean |

Use them when you need an answer, not a transformed list.

## 2. Why It Matters

Frontend code often asks questions like:

- Is the current user allowed to see this action?
- Is there an invalid form field?
- Are all required files uploaded?
- Which row is selected?
- Does the selected ID still exist after fresh API data arrives?

Using `filter(...).length` for all of these works in small demos, but it creates weaker intent and often does unnecessary work.

## 3. Official Mechanism

- `find`, `findIndex`, `findLast`, and `findLastIndex` call a predicate and stop when they find a match.
- `some` stops when the predicate returns a truthy value.
- `every` stops when the predicate returns a falsy value.
- `includes` does not use a predicate; it compares the searched value using SameValueZero.
- `some` on an empty array returns `false`.
- `every` on an empty array returns `true`.
- `some` and `every` skip empty slots in sparse arrays.
- `find` and `includes` treat empty slots as `undefined` for their checks.

## 4. Mental Model

Ask the plain-English question first:

```txt
I need the item        -> find
I need the index       -> findIndex
I need yes/no any      -> some
I need yes/no all      -> every
I need membership      -> includes
I need all matches     -> filter
```

The method name should almost read like the requirement.

## 5. `find`: First Matching Item

```js
const users = [
  { id: "u1", name: "Mina", role: "viewer" },
  { id: "u2", name: "Sara", role: "admin" },
  { id: "u3", name: "Omar", role: "admin" },
];

const admin = users.find(user => user.role === "admin");

console.log(admin);
// { id: "u2", name: "Sara", role: "admin" }
```

If no item matches:

```js
const missing = users.find(user => user.id === "u9");
console.log(missing);
// undefined
```

### Real Frontend Bug

```jsx
function SelectedUserName({ users, selectedUserId }) {
  const selected = users.find(user => user.id === selectedUserId);

  return <span>{selected.name}</span>;
}
```

> [!warning] find can return undefined
> This crashes when the selected ID no longer exists after a refetch.

Fix:

```jsx
function SelectedUserName({ users, selectedUserId }) {
  const selected = users.find(user => user.id === selectedUserId);

  return <span>{selected?.name ?? "Unknown user"}</span>;
}
```

> [!tip] Design for inconsistent selection state
> The fix handles the real production state: UI selection and server data can become temporarily inconsistent.

## 6. `some`: At Least One

```js
const permissions = ["read", "write"];

const canDelete = permissions.some(permission => permission === "delete");
console.log(canDelete);
// false
```

Short-circuit behavior:

```js
let checks = 0;

const hasExpensiveItem = [10, 200, 300].some(price => {
  checks += 1;
  return price > 100;
});

console.log(hasExpensiveItem);
// true
console.log(checks);
// 2
```

`some` stopped after `200`.

### Replace This Pattern

```js
const hasAdmin = users.filter(user => user.role === "admin").length > 0;
```

With:

```js
const hasAdmin = users.some(user => user.role === "admin");
```

> [!tip] Prefer some over filter length
> The second version says the requirement directly and can stop early.

## 7. `every`: All Items

```js
const fields = [
  { name: "email", valid: true },
  { name: "password", valid: true },
];

const canSubmit = fields.every(field => field.valid);
console.log(canSubmit);
// true
```

Empty-array edge case:

```js
console.log([].every(Boolean));
// true

console.log([].some(Boolean));
// false
```

> [!warning] Empty arrays pass every check
> For forms, this matters. If there are no required fields loaded yet, `every` returning `true` might enable a submit button too early. Pair the check with a length condition when needed:

```js
const canSubmit =
  requiredFields.length > 0 &&
  requiredFields.every(field => field.valid);
```

## 8. `includes`: Membership With SameValueZero

```js
const selectedIds = ["p1", "p2", "p3"];

console.log(selectedIds.includes("p2"));
// true
```

`includes` compares values using SameValueZero. That means it can find `NaN`:

```js
console.log([NaN].includes(NaN));
// true

console.log([NaN].indexOf(NaN));
// -1
```

It does not perform structural object comparison:

```js
console.log([{ id: 1 }].includes({ id: 1 }));
// false
```

The two object literals are different references. Use `some` when you need to match by a property:

```js
console.log([{ id: 1 }].some(item => item.id === 1));
// true
```

## 9. Sparse Array Edge Cases

```js
const sparse = [, "loaded"];

console.log(sparse.includes(undefined));
// true

console.log(sparse.some(value => value === undefined));
// false

console.log(sparse.find(value => value === undefined));
// undefined
```

> [!warning] Ambiguous undefined from find
> The `find` example is ambiguous because a successful match can also return `undefined`. If you need to know whether an `undefined` element exists, use `findIndex`:

```js
const index = sparse.findIndex(value => value === undefined);
console.log(index);
// 0
```

Avoid accidental holes in app state. Prefer explicit `null`, `undefined`, or a status object when data is missing.

## 10. Production Tradeoffs

- `includes` is perfect for primitive IDs in small arrays.
- Use `Set` for repeated membership checks against a large list of primitive IDs.
- Use `find` when you need the item, not just a boolean.
- Use optional chaining or explicit fallback when `find` can return `undefined`.
- Use `some` for existence checks and `every` for validation checks.
- Combine `every` with a length/status check when empty data should not pass.
- For repeated lookups by ID, build a map once instead of calling `find` in a loop.

## 11. Real Frontend Scenario: Permission Gate

### Problem

```js
const canEdit = user.permissions.filter(permission => {
  return permission.resource === "invoice" && permission.action === "edit";
}).length > 0;
```

### Bug

This scans the whole permission array even after the answer is known. It also makes the code look like it needs the filtered list, but the UI only needs a boolean.

### Fix

```js
const canEdit = user.permissions.some(permission => {
  return permission.resource === "invoice" && permission.action === "edit";
});
```

### Tradeoff

For one small list, this is mostly readability. For a permission-heavy app where checks run during many renders, early exit and clearer intent both matter.

## Real-World Use Cases

### Unsaved-changes navigation guard

A settings form should warn before the tab closes if any field differs from its saved value. The question is "is at least one field dirty?" — a `some` question.

```jsx
const hasUnsavedChanges = fields.some(field => field.value !== field.savedValue);

useEffect(() => {
  if (!hasUnsavedChanges) return;
  const onBeforeUnload = (event) => event.preventDefault();
  window.addEventListener("beforeunload", onBeforeUnload);
  return () => window.removeEventListener("beforeunload", onBeforeUnload);
}, [hasUnsavedChanges]);
```

Works because `some` short-circuits at the first dirty field, and the derived boolean (not the fields array) drives the effect — the listener only attaches/detaches when the answer actually flips.

### `findLast` for the latest autosave status

An editor logs sync events in chronological order and shows "Saved 2 min ago" from the most recent successful save. Scanning from the end is what `findLast` exists for.

```js
const lastSave = syncEvents.findLast(event => event.type === "save" && event.ok);

const statusLabel = lastSave
  ? `Saved ${formatRelativeTime(lastSave.at)}`
  : "Not saved yet";
```

Works because `findLast` iterates from the highest index and short-circuits, so a long session log costs almost nothing — and like `find`, it returns `undefined` when nothing matches, so the fallback branch is mandatory.

### Upload validation: `every` for the rule, `find` for the error message

A drag-and-drop uploader accepts only images under 5 MB. The pass/fail check is boolean-shaped, but the error toast needs the offending file — so pair `every` with `find`.

```js
const MAX_BYTES = 5 * 1024 * 1024;

function validateFiles(files) {
  if (!files.every(file => file.type.startsWith("image/"))) {
    return "Only image files are allowed.";
  }
  const tooBig = files.find(file => file.size > MAX_BYTES);
  if (tooBig) {
    return `${tooBig.name} exceeds 5 MB.`;
  }
  return null;
}
```

Works because the return values match the needs: `every` yields the yes/no answer, while `find` yields the item itself, which carries the `name` for the message. `some(file => file.size > MAX_BYTES)` would confirm the problem but lose which file caused it.

See [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]] and [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]].

## 12. Interview Answer

**Short version:** `find` returns the first matching item, `some` checks whether any item matches, `every` checks whether all items match, and `includes` checks whether a value is present.

**Strong version:** `find`, `some`, and `every` use predicates and short-circuit when the result is known. `includes` compares a searched value using SameValueZero, so it can find `NaN`, but it does not compare object shapes. `some` returns `false` for an empty array, while `every` returns `true`, which matters for validation logic. In frontend code, I use these methods for question-shaped logic and reserve `filter` for when I actually need all matching items.

## 13. Common Mistakes

- Using `filter(...).length` for existence checks.
- Accessing `.name` on the result of `find` without handling `undefined`.
- Using `includes` to compare object literals by shape.
- Forgetting `every([])` is `true`.
- Forgetting `some([])` is `false`.
- Missing the difference between `includes(NaN)` and `indexOf(NaN)`.
- Repeating `find` inside `map` for large lists instead of building a lookup map.

## 14. Practice

1. Replace three `filter(...).length > 0` checks with `some`.
2. Write a safe selected-row component that handles a missing `find` result.
3. Explain why `[{ id: 1 }].includes({ id: 1 })` is false.
4. Predict the output of `[].every(Boolean)` and `[].some(Boolean)`.
5. Convert repeated `users.find(...)` calls into a `userById` lookup.

## Related Notes

- [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]]
- [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
- [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[01 - Roadmap|Roadmap]]
