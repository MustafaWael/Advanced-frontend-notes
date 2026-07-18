---
tags: [javascript, functions, currying-and-partial-application]
module: "04 - Functions Deep Dive"
priority: important
status: not-started
---

# Currying and Partial Application

## Maturity Target

- Priority: #important
- Study time: 75-90 minutes
- Interview signal: you can clearly distinguish currying from partial application and explain closures as the mechanism.
- Production signal: you use these patterns when they simplify configuration, not when they make call sites clever.
- Dependencies: [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]], [[03 - Scope and Variables/05 - Closures|Closures]], [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]]

## Source Anchors

- [MDN - Functions guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions)
- [MDN - Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [MDN - Function.prototype.bind](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind)
- [MDN - Rest parameters](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/rest_parameters)
- [React - useCallback](https://react.dev/reference/react/useCallback)

## 1. Concept

Currying transforms a multi-argument function into a chain of functions, usually one argument at a time.

```js
const add = (a) => (b) => a + b;

console.log(add(2)(3)); // 5
```

Partial application fixes some arguments now and returns a function waiting for the remaining arguments.

```js
function multiply(a, b, c) {
  return a * b * c;
}

const doubleThenMultiply = multiply.bind(null, 2);

console.log(doubleThenMultiply(3, 4)); // 24
```

Key difference:

- Currying changes the call shape into a chain.
- Partial application pre-fills some arguments but the returned function may still take multiple arguments.

## 2. Why It Matters

These patterns are useful for:

- Event handler factories.
- Reusable validators.
- Configured API clients.
- Middleware.
- Dependency injection.
- Testable utilities.
- Function composition.

They are also easy to overuse. Mature code values readable call sites more than clever abstractions.

## 3. Mechanism

Both patterns use closures. A returned function remembers the arguments supplied earlier.

```js
function createMinLengthValidator(minLength) {
  return function validate(value) {
    return value.length >= minLength;
  };
}

const isPasswordLengthValid = createMinLengthValidator(8);

console.log(isPasswordLengthValid("secret"));    // false
console.log(isPasswordLengthValid("longsecret")); // true
```

`validate` closes over `minLength`.

## 4. Manual Currying

```js
function buildUrl(baseUrl) {
  return function withPath(path) {
    return function withQuery(query) {
      const params = new URLSearchParams(query);
      return `${baseUrl}${path}?${params}`;
    };
  };
}

const apiUrl = buildUrl("/api");
const productUrl = apiUrl("/products");

console.log(productUrl({ page: "1", sort: "popular" }));
// "/api/products?page=1&sort=popular"
```

This can be powerful, but if the reader has to count parentheses, an options object may be clearer.

## 5. Partial Application

Manual partial helper:

```js
function partial(fn, ...presetArgs) {
  return function partiallyApplied(...laterArgs) {
    return fn(...presetArgs, ...laterArgs);
  };
}

function request(method, url, body) {
  return { method, url, body };
}

const post = partial(request, "POST");

console.log(post("/api/products", { name: "Keyboard" }));
// { method: "POST", url: "/api/products", body: { name: "Keyboard" } }
```

Preserving `this` when needed:

```js
function partialMethod(fn, ...presetArgs) {
  return function partiallyApplied(...laterArgs) {
    return fn.apply(this, [...presetArgs, ...laterArgs]);
  };
}
```

This matters when wrapping object methods.

## 6. `bind` as Partial Application

`bind` fixes `this` and can also pre-fill leading arguments.

```js
function track(category, eventName, payload) {
  return { category, eventName, payload };
}

const trackCheckout = track.bind(null, "checkout");

console.log(trackCheckout("started", { step: 1 }));
// { category: "checkout", eventName: "started", payload: { step: 1 } }
```

> [!tip] Tradeoff
> `bind` is concise, but explicit wrapper functions are often more readable when argument order is not obvious.

## 7. Real Frontend Example: Form Handlers

Curried event handler:

```jsx
function ProfileForm() {
  const [form, setForm] = useState({
    name: "",
    email: ""
  });

  const handleChange = useCallback(
    (fieldName) => (event) => {
      const value = event.target.value;

      setForm((currentForm) => ({
        ...currentForm,
        [fieldName]: value
      }));
    },
    []
  );

  return (
    <>
      <input value={form.name} onChange={handleChange("name")} />
      <input value={form.email} onChange={handleChange("email")} />
    </>
  );
}
```

> [!tip] Tradeoff
> this creates a new inner handler when `handleChange("name")` is evaluated during render. Usually fine for small forms. If identity matters for memoized children, precompute handlers or move each input into a component.

Alternative with explicit handler:

```jsx
function ProfileForm() {
  const [form, setForm] = useState({ name: "", email: "" });

  function updateField(fieldName, value) {
    setForm((currentForm) => ({
      ...currentForm,
      [fieldName]: value
    }));
  }

  return (
    <input
      value={form.name}
      onChange={(event) => updateField("name", event.target.value)}
    />
  );
}
```

The explicit version is sometimes easier for a team to read.

## 8. Real Frontend Example: Configured API Client

```js
function createApiClient(baseUrl) {
  return function withAuthToken(token) {
    return async function request(path, options = {}) {
      const response = await fetch(`${baseUrl}${path}`, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      return response.json();
    };
  };
}

const apiForToken = createApiClient("/api");
const request = apiForToken("abc");
```

This is readable when configuration happens in stages. It becomes too abstract if every small helper gets curried without a real reason.

## 9. Real Frontend Example: Validators

```js
const minLength = (length) => (value) => value.length >= length;
const matches = (pattern) => (value) => pattern.test(value);

const validators = [
  minLength(8),
  matches(/[A-Z]/),
  matches(/[0-9]/)
];

function validatePassword(password) {
  return validators.every((validate) => validate(password));
}

console.log(validatePassword("abc"));       // false
console.log(validatePassword("Abcdefg1"));  // true
```

This works because every validator is a configured function.

## 10. Common Pitfalls

### Confusing Currying With Partial Application

```js
const curried = (a) => (b) => (c) => a + b + c;
const partiallyApplied = (a, b) => (c) => a + b + c;

console.log(curried(1)(2)(3));       // 6
console.log(partiallyApplied(1, 2)(3)); // 6
```

### Auto-Curry and `fn.length`

Generic currying often uses `fn.length`, but `fn.length` ignores rest params and stops before default params.

```js
function createUser(name, role = "user") {}

console.log(createUser.length); // 1
```

Auto-curry helpers can break on defaults, rest parameters, and optional arguments.

### Lost `this`

```js
const cart = {
  taxRate: 0.1,
  total(subtotal, shipping) {
    return subtotal + shipping + subtotal * this.taxRate;
  }
};

const withSubtotal = partial(cart.total, 100);

try {
  console.log(withSubtotal(10));
} catch (error) {
  console.log(error.name); // TypeError in strict mode
}
```

Fix with `bind`:

```js
const withSubtotal = cart.total.bind(cart, 100);

console.log(withSubtotal(10)); // 120
```

## 11. Bug -> Fix -> Checklist

Bug: currying hides unnecessary function creation in render.

```jsx
function List({ items, onSelect }) {
  const select = (id) => () => onSelect(id);

  return items.map((item) => (
    <Row key={item.id} onSelect={select(item.id)} />
  ));
}
```

Fix if `Row` is memoized and handler identity matters:

```jsx
const Row = memo(function Row({ item, onSelect }) {
  const handleSelect = useCallback(() => {
    onSelect(item.id);
  }, [item.id, onSelect]);

  return <button onClick={handleSelect}>{item.name}</button>;
});
```

Checklist:

- Does the pattern make the call site clearer?
- Are you preserving `this` if wrapping methods?
- Are you relying on `fn.length` with defaults/rest?
- Does the returned function close over stale values?
- Is this creating many functions during render, and does identity matter?
- Would an options object be clearer?

## 12. Interview Answer

Short answer:

> Currying turns a multi-argument function into a chain of single-argument functions. Partial application fixes some arguments and returns a function for the rest.

Deeper answer:

> Both rely on closures. The returned function remembers arguments supplied earlier. Currying changes the function's call shape; partial application keeps the same general operation but pre-fills part of the input. `bind` can perform partial application for leading arguments while also fixing `this`.

Production answer:

> I use currying for handler factories and validators when the staged configuration is meaningful. I use partial application for configured clients or wrappers. I avoid it when it makes code harder to search, debug, type, or memoize.

## 13. Common Mistakes

| Mistake | Reality |
| --- | --- |
| "Currying and partial application are identical." | They overlap, but currying specifically returns a chain of functions. |
| "Currying is always more advanced and better." | It is better only when it improves clarity or reuse. |
| "`bind` only changes `this`." | It can also pre-fill arguments. |
| "Auto-curry works for every function." | Defaults/rest/optional parameters complicate arity. |
| "Curried React handlers are always free." | Function identity can matter for memoized children. |

## 14. Practice

1. Convert this function to curried form:

```js
function hasRole(user, role) {
  return user.roles.includes(role);
}
```

Possible answer:

```js
const hasRole = (role) => (user) => user.roles.includes(role);

const isAdmin = hasRole("admin");
console.log(isAdmin({ roles: ["admin"] })); // true
```

2. Implement `partial(fn, ...presetArgs)`.
3. Explain how `bind(null, "POST")` can configure a request helper.
4. Fix a partial application helper that loses `this`.
5. Refactor a curried helper into an options object and compare readability.

## Related Notes

- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[04 - Functions Deep Dive/05 - Parameters Arguments Rest and Default|Parameters Arguments Rest and Default]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[05 - this Binding/05 - call apply bind|call apply bind]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[01 - Roadmap|Roadmap]]
