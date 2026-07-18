---
tags: [javascript, language-concepts, type-coercion]
module: "12 - Advanced Language Concepts"
priority: must-know
status: not-started
---

# Type Coercion

## Maturity Target

- Priority: #must-know
- Study time: 90-130 minutes
- Interview signal: you can explain implicit vs explicit coercion, `ToPrimitive`, `ToNumber`, `ToString`, and the `+` operator without memorized trivia.
- Production signal: form values, query params, local storage, and API payloads are parsed intentionally instead of relying on accidental conversion.
- Dependencies: [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]], [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]], [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]

## Source Anchors

- [MDN Type coercion](https://developer.mozilla.org/en-US/docs/Glossary/Type_coercion)
- [MDN Addition operator](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Addition)
- [MDN Symbol.toPrimitive](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/toPrimitive)
- [ECMAScript Type Conversion](https://tc39.es/ecma262/#sec-type-conversion)

## 1. Concept

Type coercion means converting a value from one type to another.

- Explicit coercion: you wrote the conversion.
- Implicit coercion: an operator or language construct requested it.

```js
Number("42"); // explicit: 42
"42" - 2;     // implicit numeric coercion: 40
"42" + 2;     // string concatenation: "422"
```

## 2. Why It Matters

Most frontend inputs arrive as strings:

- text inputs;
- URL search params;
- `localStorage`;
- dataset attributes;
- JSON payload fields from unknown sources.

If you add, compare, or default those values without parsing, you can ship quiet bugs:

```ts
const price = 100;
const quantity = "2";

console.log(price + quantity); // "1002"
```

## 3. Accurate Mechanism

The specification describes abstract operations such as:

- `ToPrimitive`: convert an object to a primitive;
- `ToNumber`: convert to number;
- `ToString`: convert to string;
- `ToBoolean`: convert to boolean.

For objects, `ToPrimitive` checks:

1. `[Symbol.toPrimitive](hint)`, if present;
2. `valueOf()` and `toString()` in an order depending on the hint;
3. throws if no primitive is produced.

```js
const money = {
  amount: 25,
  [Symbol.toPrimitive](hint) {
    if (hint === "string") return `$${this.amount}`;
    return this.amount;
  }
};

console.log(+money);      // 25
console.log(`${money}`);  // "$25"
```

## 4. The `+` Operator Rule

The addition operator is tricky because it can add numbers or concatenate strings.

Simplified rule:

1. Convert both operands to primitives.
2. If either primitive is a string, concatenate strings.
3. Otherwise, convert both to numbers or BigInts and add.

```js
console.log(1 + 2 + "3"); // "33"
console.log("1" + 2 + 3); // "123"
console.log(true + 1);    // 2
console.log(null + 1);    // 1
console.log(undefined + 1); // NaN
```

## 5. Common Conversion Table

```js
Number("");        // 0
Number(" 5 ");     // 5
Number("42px");    // NaN
Number(null);      // 0
Number(undefined); // NaN
Number(true);      // 1
Number(false);     // 0

String(null);      // "null"
String(undefined); // "undefined"
String(false);     // "false"

Boolean("");       // false
Boolean("false");  // true
Boolean([]);       // true
Boolean({});       // true
```

> [!warning] parseInt is not Number
> `parseInt` and `Number` are not interchangeable.

```js
Number("42px");      // NaN
parseInt("42px", 10); // 42
```

> [!tip] Match the parser to the format
> Use `Number` when the whole string must be numeric. Use parsing when the format intentionally contains units and you have validated that format.

## 6. Real Frontend Bug: Query Param Pagination

Problem:

```ts
const page = new URLSearchParams(location.search).get("page") || 1;
const nextPage = page + 1;

console.log(nextPage);
```

If `?page=2`, expected `3`, actual `"21"`.

Fix:

```ts
function parsePage(search: string) {
  const raw = new URLSearchParams(search).get("page");
  if (raw == null || raw.trim() === "") return 1;

  const value = Number(raw);
  if (!Number.isInteger(value) || value < 1) return 1;

  return value;
}

const page = parsePage(location.search);
const nextPage = page + 1;
```

Why it works:

- nullish/missing input is handled separately;
- empty string is not accidentally accepted as `0`;
- `Number.isInteger` validates the parsed value;
- arithmetic happens with numbers.

## 7. Real Frontend Bug: JSX `&&` With Numbers

> [!example] Coercion meets JSX
> Coercion and truthiness meet in JSX.

```tsx
function Inbox({ unreadCount }: { unreadCount: number }) {
  return <div>{unreadCount && <Badge count={unreadCount} />}</div>;
}
```

> [!warning] Stray zero in the UI
> When `unreadCount` is `0`, `&&` returns `0`. React renders the number `0`.

Fix:

```tsx
return <div>{unreadCount > 0 && <Badge count={unreadCount} />}</div>;
```

See [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]].

## 8. Mental Model

> [!tip] Convert explicitly at boundaries
> Explicit conversion is documentation. Implicit conversion is a bet that every future reader knows the same rules.

Use implicit coercion only when it is idiomatic and obvious:

```js
Boolean(value);
Number(raw);
String(id);
```

Prefer clear parsing at boundaries:

- form submit handlers;
- router/search-param parsing;
- API response validation;
- local storage reads;
- feature flag config reads.

## 9. Production Tradeoffs

| Pattern | Benefit | Risk |
| --- | --- | --- |
| `Number(raw)` | strict whole-value conversion | `""` becomes `0` |
| `parseInt(raw, 10)` | handles unit-like strings | accepts partial values |
| `Boolean(value)` | explicit truthiness | may collapse valid `0` or `""` |
| `value == null` | concise null/undefined check | should not be generalized to other `==` |
| schema parsing | strong boundaries | dependency and runtime cost |

## Real-World Use Cases

### Classic interview trap: `[] == ![]`

Interviewers love this one because the true answer forces you to name three separate mechanisms.

```js
console.log([] == ![]); // true
```

Wrong guess: "comparing a thing to its own negation must be false." Tick-by-tick trace:

1. `![]` evaluates first. `ToBoolean([])` is `true` (all objects are truthy), so `![]` is `false`. The comparison is now `[] == false`.
2. Abstract equality sees object vs boolean. The boolean goes through `ToNumber`: `false` becomes `0`. Now `[] == 0`.
3. Object vs number triggers `ToPrimitive([])` with the default hint: `valueOf()` returns the array itself (not a primitive), so `toString()` runs and yields `""`. Now `"" == 0`.
4. String vs number: `ToNumber("")` is `0`. `0 == 0` is `true`.

One expression, three conversion pipelines: `ToBoolean` for `!`, `ToNumber` for the boolean operand, `ToPrimitive`→`ToString`→`ToNumber` for the array. The modern fix is simply `===`, which stops at step 2 with `false` because the types differ. See [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]] and [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]].

### Default `Array.prototype.sort` coercing to strings

An order dashboard sorts orders by ID. Default `sort` converts elements with `ToString` and compares UTF-16 code units, so numeric IDs come back in dictionary order.

```ts
const orderIds = [101, 9, 30, 1002];

orderIds.sort();                     // [1002, 101, 30, 9] — string comparison
orderIds.sort((a, b) => a - b);      // [9, 30, 101, 1002]
```

Fails because the no-comparator path runs **`ToString` on every element** before comparing — implicit coercion hidden inside a standard library default. Same trap sorts `"2024-9-1"` after `"2024-10-1"` in hand-rolled date strings.

> [!warning]
> This bug hides in small datasets: `[1, 2, 3].sort()` looks correct, then production IDs cross a digit boundary and ordering silently breaks.

### Date math that works because of `ToPrimitive`

Measuring a duration by subtracting dates is legitimate implicit coercion — `-` requests the number hint, and `Date`'s `ToPrimitive` returns its timestamp.

```ts
const start = new Date();
await runImport();
const elapsedMs = new Date() - start; // ToPrimitive(number hint) → getTime()
```

But `+` prefers the string hint for dates, so the same-looking expression concatenates:

```js
new Date() + 1; // "Wed Jul 15 2026 ...1" — string, not a timestamp
```

Both behaviors fall out of the **hint passed to `ToPrimitive`**: `-` always asks for a number, `+` lets `Date` answer with a string. Prefer `Date.now() - start.getTime()` in shared code — explicit, and no reader has to know the hint rules.

## 10. Interview Answer

**Short version:** Type coercion is JavaScript converting values between types. Explicit coercion is deliberate, like `Number("42")`; implicit coercion is triggered by operators, like `"5" - 2`. The `+` operator is special because it concatenates if either primitive operand is a string.

**Strong version:** JavaScript uses abstract conversion operations such as `ToPrimitive`, `ToNumber`, `ToString`, and `ToBoolean`. Objects convert through `[Symbol.toPrimitive]`, `valueOf`, or `toString`. The `+` operator first converts operands to primitives, then concatenates if either is a string, otherwise it performs numeric addition. In production I parse strings at boundaries and avoid relying on accidental coercion from form values or query params. I also distinguish falsy checks from nullish checks so valid values like `0` and `""` are not lost.

## 11. Common Mistakes

- Adding numbers to string form values.
- Using `parseInt` when the entire input must be numeric.
- Forgetting `Number("")` is `0`.
- Using `if (value)` when `0` or `""` are valid.
- Comparing with `==` beyond the intentional `value == null` pattern.
- Logging objects through template literals and getting `"[object Object]"`.
- Treating coercion trivia as useless while missing real form/query bugs.

## 12. Practice

1. Predict:

```js
console.log(1 + "2" + 3);
console.log(1 + 2 + "3");
console.log(+"");
console.log(+[]);
console.log(+{});
console.log(true + true + "1");
```

2. Explain `[] + {}` using `ToPrimitive`.
3. Parse a `?limit=` query param where missing means `20`, but `0` is invalid.
4. Explain why `Number.isNaN(Number(raw))` is safer than `isNaN(raw)`.
5. Implement `[Symbol.toPrimitive]` for a `Money` object.

## Related Notes

- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]]
- [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]
- [[12 - Advanced Language Concepts/07 - Symbols|Symbols]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
