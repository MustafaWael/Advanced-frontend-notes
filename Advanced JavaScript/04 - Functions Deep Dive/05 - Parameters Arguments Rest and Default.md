---
tags: [javascript, functions, parameters-arguments-rest-and-default]
module: "04 - Functions Deep Dive"
priority: must-know
status: not-started
---

# Parameters Arguments Rest and Default

## Maturity Target

- Priority: #must-know
- Study time: 90 minutes
- Interview signal: you can distinguish parameters, arguments, rest parameters, spread syntax, defaults, destructuring, and `arguments`.
- Production signal: you design function APIs that are hard to misuse and easy to evolve.
- Dependencies: [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]], [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]]

## Source Anchors

- [MDN - Functions guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions)
- [MDN - Rest parameters](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/rest_parameters)
- [MDN - Default parameters](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Default_parameters)
- [MDN - arguments object](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/arguments)
- [ECMAScript 2026 - Function definitions](https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-function-definitions)

## 1. Concept

Parameters are the named bindings in a function definition. Arguments are the values supplied at call time.

```js
function greet(name) {
  // name is a parameter.
  return `Hello, ${name}`;
}

console.log(greet("Ava")); // "Ava" is an argument.
```

Rest parameters collect remaining arguments into a real array.

```js
function sum(...numbers) {
  return numbers.reduce((total, number) => total + number, 0);
}

console.log(sum(1, 2, 3)); // 6
```

Default parameters provide a value when the argument is `undefined`.

```js
function createPage(limit = 20) {
  return { limit };
}

console.log(createPage());          // { limit: 20 }
console.log(createPage(undefined)); // { limit: 20 }
console.log(createPage(null));      // { limit: null }
```

## 2. Why It Matters

Function signatures are contracts. In frontend production code, bad signatures cause:

- Confusing boolean arguments.
- Options objects with unsafe defaults.
- Rest/spread confusion.
- Accidental mutation of passed objects.
- `null` vs `undefined` bugs.
- React props defaults that do not behave as expected.
- Wrappers that lose arguments or `this`.

Good function API design makes call sites readable and failure modes obvious.

## 3. Parameters vs Arguments

```js
function logRequest(method, url, options) {
  console.log(method, url, options);
}

logRequest("GET", "/api/products", { cache: "no-store" });
```

`method`, `url`, and `options` are parameters. The values passed to `logRequest` are arguments.

Too many positional parameters become hard to read:

```js
createToast("Saved", "success", true, 4000, "bottom-right");
```

Prefer an options object when values are optional, named, or likely to evolve:

```js
createToast({
  message: "Saved",
  type: "success",
  dismissible: true,
  durationMs: 4000,
  position: "bottom-right"
});
```

## 4. Default Parameters

Defaults run when the argument is `undefined`, not when it is any falsy value.

```js
function normalizePage(page = 1) {
  return page;
}

console.log(normalizePage());          // 1
console.log(normalizePage(undefined)); // 1
console.log(normalizePage(0));         // 0
console.log(normalizePage(null));      // null
```

Default expressions are evaluated at call time.

```js
function createRequestId(id = crypto.randomUUID()) {
  return id;
}
```

Earlier parameters are available to later defaults:

```js
function createRange(start = 0, end = start + 10) {
  return [start, end];
}

console.log(createRange(5)); // [5, 15]
```

Later parameters are not available to earlier defaults:

```js
function broken(start = end, end = 10) {
  return [start, end];
}

try {
  broken();
} catch (error) {
  console.log(error.name); // "ReferenceError"
}
```

## 5. Defaults With Objects

```js
function fetchProducts({
  page = 1,
  limit = 20,
  sort = "popular"
} = {}) {
  return fetch(`/api/products?page=${page}&limit=${limit}&sort=${sort}`);
}
```

The `= {}` default protects calls with no argument:

```js
fetchProducts(); // works
```

Without it, destructuring `undefined` would throw.

Use nullish coalescing inside the function when `null` should also mean "default":

```js
function normalizeLimit(limit) {
  return limit ?? 20;
}

console.log(normalizeLimit(undefined)); // 20
console.log(normalizeLimit(null));      // 20
console.log(normalizeLimit(0));         // 0
```

## 6. Rest Parameters vs `arguments`

`arguments` is array-like, not a real array, and arrows do not have their own `arguments`.

```js
function oldSum() {
  return Array.from(arguments).reduce((total, number) => total + number, 0);
}

console.log(oldSum(1, 2, 3)); // 6
```

Rest parameters are clearer:

```js
function sum(...numbers) {
  return numbers.reduce((total, number) => total + number, 0);
}

console.log(sum(1, 2, 3)); // 6
```

Rest parameters must come last:

```js
// SyntaxError:
// function invalid(...items, options) {}
```

## 7. Spread at Call Sites

Rest gathers. Spread expands.

```js
function maxOfThree(a, b, c) {
  return Math.max(a, b, c);
}

const values = [4, 9, 2];

console.log(maxOfThree(...values)); // 9
```

Production concern: spreading huge arrays into function calls can hit engine argument limits. For large arrays, prefer iteration or reducers:

```js
function max(values) {
  let result = -Infinity;

  for (const value of values) {
    if (value > result) {
      result = value;
    }
  }

  return result;
}
```

## 8. Function Length and API Design

`function.length` counts parameters before the first one with a default, rest, or destructuring pattern.

```js
function one(a, b) {}
function two(a, b = 1) {}
function three(...items) {}

console.log(one.length);   // 2
console.log(two.length);   // 1
console.log(three.length); // 0
```

Do not over-rely on `fn.length` for runtime behavior in application code. It can be misleading once defaults/rest/destructuring are involved.

## 9. Real Frontend Scenario

Problem: a request helper takes too many positional parameters.

```js
request("/api/products", "GET", true, 3, 5000, false);
```

Nobody remembers what `true` or `false` means.

Fix with an options object:

```js
function request(url, {
  method = "GET",
  auth = true,
  retries = 0,
  timeoutMs = 5000,
  cache = true
} = {}) {
  return fetchWithTimeout(url, {
    method,
    auth,
    retries,
    timeoutMs,
    cache
  });
}

request("/api/products", {
  retries: 3,
  cache: false
});
```

> [!tip] Tradeoff
> options objects are slightly more verbose, but they scale much better as APIs grow.

## 10. Bug -> Fix -> Checklist

Bug: a wrapper loses arguments.

```js
function withLogging(fn) {
  return function wrapped() {
    console.log("calling");
    return fn(); // Bug: caller arguments are dropped.
  };
}

const add = (a, b) => a + b;
const loggedAdd = withLogging(add);

console.log(loggedAdd(2, 3)); // NaN
```

Fix:

```js
function withLogging(fn) {
  return function wrapped(...args) {
    console.log("calling");
    return fn(...args);
  };
}

console.log(withLogging(add)(2, 3)); // 5
```

Checklist:

- Are optional arguments named clearly?
- Should this be an options object?
- Does `null` mean "no value" or should it override the default?
- Does the wrapper forward all arguments?
- Does the wrapper preserve `this` if needed?
- Is rest used instead of `arguments` in modern code?
- Could huge spread calls become a performance or engine-limit issue?

## Real-World Use Cases

### Classic interview trap: `["1", "7", "11"].map(parseInt)`

The canonical parameters-vs-arguments question — it looks like a string-parsing bug but is entirely about arity.

```js
["1", "7", "11"].map(parseInt);
// Guess: [1, 7, 11]
// Actual: [1, NaN, 3]
```

Tick-by-tick:

1. `map` calls its callback with **three arguments**: `(element, index, array)`.
2. `parseInt` has **two parameters**: `(string, radix)`. Extra arguments are silently ignored; the index lands in `radix`.
3. `parseInt("1", 0)` → radix 0 means "auto" → `1`. `parseInt("7", 1)` → radix 1 is invalid → `NaN`. `parseInt("11", 2)` → binary `11` → `3`.

Fix by controlling the arity yourself: `["1", "7", "11"].map(s => parseInt(s, 10))` or `.map(Number)`. The general rule: never pass a function reference straight into a higher-order API unless you know both signatures line up.

See [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]] and [[16 - Code Output Questions/06 - Mixed Advanced Output Questions|Mixed Advanced Output Questions]].

### React handler: the event object eats your default

A reset button reuses a helper with a default parameter. Passed directly as an event handler, it receives the click event — and the default never applies.

```tsx
function resetFilters(overrides = {}) {
  setFilters({ ...DEFAULT_FILTERS, ...overrides }); // spread of a SyntheticEvent!
}

<button onClick={resetFilters}>Reset</button>          // bug: overrides = click event
<button onClick={() => resetFilters()}>Reset</button>  // fix: call with no arguments
```

Defaults apply only when the argument is `undefined` — React calls `onClick(event)`, so `overrides` is a truthy event object and the `= {}` default is skipped. The spread then copies event properties into your filter state.

> [!warning]
> Any `onClick={someFn}` where `someFn` has optional parameters is a latent version of this bug. If the function was not designed as an event handler, wrap it: `onClick={() => someFn()}`.

### URL query params: `null` slips past every default

Defaults guard `undefined`, but `URLSearchParams.get()` returns `null` for missing keys — so a search page's defaults silently never fire.

```ts
function ProductList({ searchParams }: { searchParams: URLSearchParams }) {
  const page = parsePage(searchParams.get("page"));
  // ...
}

function parsePage(raw: string | null, fallback = 1) {
  const parsed = Number(raw ?? fallback);       // ?? catches the null
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}
```

Without the `??`, `Number(null)` is `0` and the page silently requests page zero. The mechanism: default parameters fire on `undefined` only, so any boundary that produces `null` (URL params, JSON fields, database rows) needs explicit `??` handling inside the function.

> [!tip]
> Treat every external boundary (URL, JSON API, form data) as a `null`-producer and every internal optional argument as an `undefined`-producer. Defaults handle the second group; `??` handles the first.

See [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]].

## 11. Interview Answer

Short answer:

> Parameters are names in the function definition; arguments are values passed at call time. Rest parameters gather extra arguments into an array. Default parameters apply when the argument is `undefined`.

Deeper answer:

> Defaults are evaluated at call time and in parameter order, so earlier parameters can be used by later defaults but not the other way around. `arguments` is array-like and unavailable as an own binding in arrow functions, so rest parameters are clearer. Spread at call sites is the opposite of rest: it expands iterable values into arguments.

Production answer:

> I use options objects for APIs with optional or evolving settings, rest parameters for wrappers and variadic functions, and explicit nullish handling when `null` should be treated like missing. Wrapper functions should forward both arguments and `this` deliberately.

## 12. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Default values apply to `null`." | Defaults apply to `undefined`; use `??` for `null` too. |
| "Rest and spread are the same." | Rest gathers; spread expands. |
| "`arguments` is an array." | It is array-like. Use rest for real arrays. |
| "Arrows have their own `arguments`." | They do not. |
| "`fn.length` is reliable for business logic." | Defaults/rest/destructuring make it misleading. |

## 13. Practice

1. Predict the output:

```js
function test(a = 1, b = a + 1) {
  return [a, b];
}

console.log(test());
console.log(test(5));
console.log(test(undefined, 10));
console.log(test(null));
```

Expected output:

```txt
[1, 2]
[5, 6]
[1, 10]
[null, 1]
```

2. Rewrite a function with five positional arguments into an options object.
3. Fix a wrapper that drops arguments.
4. Explain why `function f(...args) {}` has `f.length === 0`.
5. Replace `arguments` with rest parameters.

## Related Notes

- [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]]
- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[04 - Functions Deep Dive/06 - Currying and Partial Application|Currying and Partial Application]]
- [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]]
- [[12 - Advanced Language Concepts/05 - Optional Chaining and Nullish Coalescing|Optional Chaining and Nullish Coalescing]]
- [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]
- [[01 - Roadmap|Roadmap]]
