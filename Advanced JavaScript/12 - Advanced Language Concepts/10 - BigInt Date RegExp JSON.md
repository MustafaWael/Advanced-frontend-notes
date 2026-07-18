---
tags: [javascript, language-concepts, bigint-date-regexp-json]
module: "12 - Advanced Language Concepts"
priority: important
status: not-started
---

# BigInt Date RegExp JSON

## Maturity Target

- Priority: #important
- Study time: 140-190 minutes
- Interview signal: you can explain precision, timestamps, regex state, and serialization rules with practical frontend bugs.
- Production signal: large IDs, dates, search patterns, and JSON boundaries are handled without silent data corruption.
- Dependencies: [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]], [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]], [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]

## Source Anchors

- [MDN BigInt](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/BigInt)
- [MDN Date](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date)
- [MDN RegExp](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp)
- [MDN JSON.stringify](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/stringify)
- [MDN JSON.parse](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/parse)

## 1. Concept

This note groups four built-ins that often create production bugs:

- `BigInt`: exact integer values beyond `Number.MAX_SAFE_INTEGER`;
- `Date`: timestamp object backed by milliseconds since Unix epoch;
- `RegExp`: pattern matching with flags and stateful behavior;
- `JSON`: text serialization format for data exchange.

They are not "random built-ins." They are boundary tools: database IDs, API timestamps, search input, validation, and persisted data.

## 2. BigInt

Use BigInt for integers that cannot be safely represented by `number`.

```js
console.log(Number.MAX_SAFE_INTEGER); // 9007199254740991
console.log(9007199254740992 === 9007199254740993); // true

const id = 9007199254740993n;
console.log(id + 1n); // 9007199254740994n
```

Rules:

- BigInts are integers only;
- arithmetic cannot mix `bigint` and `number`;
- division truncates toward zero;
- JSON does not support BigInt directly.

```js
// 1n + 1; // TypeError
console.log(7n / 2n); // 3n
```

Frontend decision: large database IDs should usually travel as strings, not numbers, because JSON consumers may not preserve precision.

```ts
type ApiUser = {
  id: string; // postgres bigint, snowflake ID, etc.
};

const id = BigInt(apiUser.id);
```

## 3. BigInt Bug: Broken IDs

Problem:

```ts
const user = await response.json() as { id: number };
console.log(user.id);
```

Bug: if the backend sends an integer beyond `Number.MAX_SAFE_INTEGER`, JavaScript can round it.

Fix:

```ts
type UserDto = {
  id: string;
};

const user = (await response.json()) as UserDto;
const id = BigInt(user.id);
```

> [!tip] Tradeoff
> BigInt cannot be serialized to JSON without conversion.

```js
JSON.stringify({ id: 1n }); // TypeError
JSON.stringify({ id: "1" }); // ok
```

## 4. Date

`Date` stores a point in time as milliseconds since January 1, 1970 UTC.

```js
const now = new Date();
console.log(now.getTime());      // timestamp number
console.log(now.toISOString());  // UTC ISO string
```

Common traps:

- month index in numeric constructor is zero-based;
- many string formats are unreliable across environments;
- local time and UTC methods differ;
- `Date` is mutable;
- date-only UI concepts and exact timestamps are different problems.

```js
console.log(new Date(2026, 0, 1).toDateString());  // January 1, 2026
console.log(new Date(2026, 11, 1).toDateString()); // December 1, 2026
```

Use `Intl.DateTimeFormat` for display.

```ts
const formatter = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short"
});

console.log(formatter.format(new Date()));
```

## 5. Date Bug: Local vs UTC

Problem:

```ts
const deadline = new Date("2026-05-29");
const label = deadline.toLocaleDateString();
```

Bug: a date-only string is parsed as a timestamp at UTC midnight. In some time zones, local display may show the previous calendar date.

Production fix:

- if it is an instant, store ISO timestamp with timezone: `2026-05-29T12:00:00Z`;
- if it is a calendar date, keep it as a string like `"2026-05-29"` or use a date library/type that models plain dates;
- format for the user's locale at the edge.

## 6. RegExp

Regular expressions match patterns in strings.

```js
const emailLike = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
console.log(emailLike.test("a@example.com")); // true
```

Common flags:

- `g`: global search, stateful through `lastIndex`;
- `i`: case-insensitive;
- `m`: multiline anchors;
- `s`: dot matches line terminators;
- `u`: Unicode-aware mode;
- `y`: sticky matching at `lastIndex`;
- `d`: match indices where supported.

## 7. RegExp Bug: Reusing Global Regex With `test`

Problem:

```js
const hasDigit = /\d/g;

console.log(["a1", "b2", "c3"].map((value) => hasDigit.test(value)));
```

Possible output:

```txt
[ true, false, true ]
```

Bug: `/g` makes the regex keep `lastIndex`, so repeated `test` calls continue from previous positions.

Fix:

```js
const hasDigit = /\d/;
console.log(["a1", "b2", "c3"].map((value) => hasDigit.test(value)));
```

Use `/g` when you need all matches. Avoid it for simple boolean checks.

When constructing regex from user input, escape it.

```ts
function escapeRegex(input: string) {
  return input.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const query = "a+b";
const regex = new RegExp(escapeRegex(query), "i");
```

## 8. JSON

JSON is a text format. `JSON.parse` turns JSON text into JavaScript values. `JSON.stringify` turns JavaScript values into JSON text.

Important serialization rules:

```js
console.log(JSON.stringify({
  a: undefined,
  b: null,
  c: NaN,
  d: Infinity,
  e: () => {},
  f: Symbol("x")
}));
```

Expected output:

```txt
{"b":null,"c":null,"d":null}
```

In arrays, `undefined`, functions, and symbols become `null`.

```js
console.log(JSON.stringify([1, undefined, () => {}]));
```

Expected output:

```txt
[1,null,null]
```

Circular references throw. BigInt throws. Dates become ISO strings through `toJSON`.

## 9. JSON Bug: Trusting Parsed Data

Problem:

```ts
const user = JSON.parse(localStorage.getItem("user") ?? "{}") as User;
console.log(user.email.toLowerCase());
```

Bug:

- `JSON.parse` returns `any` in TypeScript;
- the stored value can be missing, stale, corrupt, or malicious;
- the type assertion does not validate runtime shape.

Fix:

```ts
function isUser(value: unknown): value is User {
  if (typeof value !== "object" || value === null) return false;
  const user = value as Partial<User>;
  return typeof user.email === "string" && typeof user.name === "string";
}

function readStoredUser(): User | null {
  try {
    const raw = localStorage.getItem("user");
    if (raw == null) return null;

    const parsed: unknown = JSON.parse(raw);
    return isUser(parsed) ? parsed : null;
  } catch {
    return null;
  }
}
```

## 10. Production Tradeoffs

| Tool | Good for | Watch out for |
| --- | --- | --- |
| BigInt | exact large integers | JSON and Number interop |
| Date | exact instants | timezone/calendar confusion |
| RegExp | compact pattern matching | readability, escaping, `/g` state |
| JSON | data interchange | unsupported values, runtime validation |

## 11. Interview Answer

**Short version:** BigInt handles large integers exactly but cannot mix with numbers or JSON directly. Date stores timestamps but has timezone and parsing traps. RegExp is powerful but `/g` is stateful through `lastIndex`. JSON omits or changes several JavaScript values and parsed JSON must be validated.

**Strong version:** These built-ins matter at boundaries. Use BigInt or strings for large IDs beyond safe integer range. Treat Date as an instant, not a complete date/time domain model, and be explicit about UTC, local display, and date-only values. Use RegExp carefully with escaped user input and avoid global regex state for boolean tests. Use JSON as a transport format, knowing that `undefined`, functions, symbols, `NaN`, `Infinity`, Date, BigInt, and circular references have special behavior. In TypeScript, never trust `JSON.parse` as typed data without validation.

## 12. Common Mistakes

- Returning database BigInt IDs as JSON numbers.
- Mixing BigInt and Number in arithmetic.
- Forgetting Date numeric months are zero-based.
- Parsing ambiguous date strings.
- Reusing `/g` regex objects with `.test`.
- Building regex from user input without escaping.
- Assuming JSON preserves `undefined`, functions, symbols, `NaN`, or BigInt.
- Type-asserting parsed JSON without validation.

## 13. Practice

1. Show why `9007199254740992 === 9007199254740993` can be true.
2. Explain why `new Date(2026, 1, 1)` is February 1, not January 1.
3. Predict the result of repeated `/a/g.test("a")`.
4. What does `JSON.stringify({ a: undefined, b: NaN, c: Infinity })` return?
5. Design an API strategy for PostgreSQL `BIGINT` IDs in a frontend app.

## Related Notes

- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[12 - Advanced Language Concepts/03 - Type Coercion|Type Coercion]]
- [[12 - Advanced Language Concepts/04 - Truthy and Falsy|Truthy and Falsy]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]
- [[01 - Roadmap|Roadmap]]
