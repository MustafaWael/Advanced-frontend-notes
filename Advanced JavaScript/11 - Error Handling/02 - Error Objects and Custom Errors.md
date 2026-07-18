---
tags: [javascript, error-handling, error-objects-and-custom-errors]
module: "11 - Error Handling"
priority: must-know
status: not-started
---

# Error Objects and Custom Errors

## Maturity Target

- Priority: #must-know
- Study time: 100-140 minutes
- Interview signal: you can explain `Error`, built-in error types, `cause`, stack limitations, custom classes, and TypeScript-safe narrowing.
- Production signal: your app throws structured errors that callers can classify, log, serialize, and convert into user-safe UI.
- Dependencies: [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]], [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]], [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]

## Source Anchors

- [MDN Error](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error)
- [MDN TypeError](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/TypeError)
- [MDN AggregateError](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/AggregateError)
- [MDN DOMException](https://developer.mozilla.org/en-US/docs/Web/API/DOMException)
- [MDN throw](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/throw)

## 1. Concept

An `Error` object carries failure information. The common fields are:

- `name`: error category, such as `"TypeError"` or `"ApiError"`;
- `message`: human-readable explanation;
- `cause`: original lower-level error when one error wraps another;
- `stack`: engine-provided diagnostic stack, widely available but not the core language contract.

```js
const error = new Error("Could not save profile");

console.log(error.name);    // "Error"
console.log(error.message); // "Could not save profile"
```

> [!warning] Throwing non-Error values
> JavaScript technically allows throwing any value, but production code should throw `Error` objects or error-like domain objects at known boundaries.

## 2. Why It Matters

Frontend systems need to distinguish failure categories:

- a programmer bug should be reported and fixed;
- a validation error should attach to a field;
- a 401 should trigger auth recovery;
- a 404 may render not-found UI;
- a 429 may ask the user to wait;
- a network error may be retryable;
- an aborted request should often be ignored.

If everything is `throw "failed"` or `return null`, callers cannot make those decisions safely.

## 3. Built-In Error Types

| Type | Typical cause | Example |
| --- | --- | --- |
| `Error` | generic failure | `throw new Error("failed")` |
| `TypeError` | operation on wrong type | `null.toString()` |
| `RangeError` | value outside valid range | `new Array(-1)` |
| `ReferenceError` | missing binding | `missingVariable` |
| `SyntaxError` | invalid JavaScript syntax | `JSON.parse("{")` throws a `SyntaxError` for invalid JSON text |
| `URIError` | malformed URI operation | `decodeURIComponent("%")` |
| `AggregateError` | multiple failures collected | `Promise.any([...])` when all reject |
| `EvalError` | legacy eval-related type | rarely used directly |

Browser APIs can also throw `DOMException` values. For example, a canceled `fetch` commonly rejects with a `DOMException` whose `name` is `"AbortError"`.

See [[08 - Async JavaScript/06 - AbortController|AbortController]].

## 4. Official Mechanism

`throw` can throw any JavaScript value:

```js
throw "bad";          // valid but weak
throw { code: 500 };  // valid but weak
throw new Error("bad");
```

The problem with non-`Error` values is not syntax. The problem is diagnostics and classification:

- strings do not have stack traces;
- plain objects may not have `message`;
- `instanceof Error` checks fail;
- logging tools may not group them correctly.

Normalize unknown caught values before using them.

```ts
function toError(value: unknown): Error {
  if (value instanceof Error) return value;
  return new Error(typeof value === "string" ? value : JSON.stringify(value));
}
```

## 5. `cause`: Preserve The Original Failure

When adding context, do not destroy the original error.

```ts
async function loadProfile(userId: string) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    throw new Error(`Could not load profile for ${userId}`, {
      cause: error
    });
  }
}
```

Why this works:

- the outer error gives product-level context;
- the `cause` retains the transport or parsing failure;
- logging can show the whole chain.

Bad alternative:

```ts
catch (error) {
  // Loses the original stack and type.
  throw new Error("Could not load profile");
}
```

## 6. Real Frontend Example: Typed API Errors

```ts
export class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    options?: ErrorOptions
  ) {
    super(message, options);
    this.name = "AppError";

    // Useful when TypeScript targets older runtimes.
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class ApiError extends AppError {
  constructor(
    public readonly status: number,
    message: string,
    public readonly body?: unknown,
    options?: ErrorOptions
  ) {
    super(message, `HTTP_${status}`, options);
    this.name = "ApiError";
  }

  get retryable() {
    return this.status === 408 || this.status === 429 || this.status >= 500;
  }
}

export class ValidationError extends AppError {
  constructor(public readonly fields: Record<string, string>) {
    super("Validation failed", "VALIDATION_ERROR");
    this.name = "ValidationError";
  }
}
```

Usage:

```ts
async function saveProfile(input: ProfileInput) {
  try {
    await api.saveProfile(input);
    toast.success("Profile saved");
  } catch (error) {
    if (error instanceof ValidationError) {
      // Expected application error: attach messages to fields.
      setFieldErrors(error.fields);
      return;
    }

    if (error instanceof ApiError && error.status === 401) {
      redirectToLogin();
      return;
    }

    // Unknown or unrecoverable error: preserve the original path.
    throw error;
  }
}
```

## 7. TypeScript Catch Variables

In strict TypeScript, caught errors should be treated as `unknown`.

```ts
try {
  await riskyOperation();
} catch (error: unknown) {
  if (error instanceof Error) {
    console.error(error.message);
  } else {
    console.error("Non-Error thrown", error);
  }
}
```

> [!tip] Catch values are truly unknown
> This is not ceremony. It is accurate JavaScript: any value can be thrown.

## 8. Error Serialization

> [!example] Errors stringify to empty objects
> `Error` properties such as `message` and `stack` are not reliably serialized by `JSON.stringify`.

```js
console.log(JSON.stringify(new Error("boom")));
```

Expected output:

```txt
{}
```

Use a serializer at logging boundaries.

```ts
function serializeError(error: unknown): Record<string, unknown> {
  if (!(error instanceof Error)) {
    return { name: "NonError", message: String(error) };
  }

  return {
    name: error.name,
    message: error.message,
    stack: error.stack,
    cause: error.cause ? serializeError(error.cause) : undefined
  };
}
```

> [!warning] Do not leak internals to users
> Production warning: do not send full stacks, response bodies, tokens, cookies, or user PII to client-visible UI. Log technical details to a protected service and show safe messages to users.

## 9. Mental Model

An error type is an API contract.

If a function throws `ValidationError`, callers can safely show field messages. If it throws `ApiError`, callers can inspect status and retry. If it throws unknown values, every caller must guess.

## 10. Common Bugs and Fixes

### Bug: Throwing strings

```ts
throw "Invalid email";
```

Fix:

```ts
throw new ValidationError({ email: "Invalid email" });
```

Reason: callers can branch by type and extract structured field data.

### Bug: Losing original error context

```ts
catch {
  throw new Error("Checkout failed");
}
```

Fix:

```ts
catch (error) {
  throw new Error("Checkout failed", { cause: error });
}
```

Reason: the high-level message helps product debugging while `cause` keeps the low-level failure.

### Bug: Assuming `error.message` always exists

```ts
catch (error) {
  toast.error(error.message);
}
```

Fix:

```ts
catch (error: unknown) {
  const message = error instanceof Error ? error.message : "Unexpected error";
  toast.error(message);
}
```

Reason: catch values are not guaranteed to be `Error` instances.

## 11. Production Tradeoffs

| Choice | Benefit | Cost |
| --- | --- | --- |
| Custom error classes | strong branching and logging | too many classes can become noisy |
| Error codes | stable API across bundles/services | requires consistent naming |
| `cause` chains | preserves diagnostics | loggers must serialize them intentionally |
| User-safe messages | protects users and internals | developers need separate technical logs |
| `instanceof` checks | clear within one runtime | can fail across realms or serialized boundaries |

> [!tip] Codes beat instanceof across realms
> Across iframes, workers, server/client boundaries, or API JSON responses, prefer stable `code` fields over relying only on `instanceof`.

## Real-World Use Cases

### Monitoring noise control with `name` and `code`

An error tracker like Sentry groups issues by fingerprint. Structured errors let you drop known noise (canceled requests) and group real failures by stable code instead of by message text.

```ts
Sentry.init({
  beforeSend(event, hint) {
    const error = hint.originalException;

    if (error instanceof DOMException && error.name === "AbortError") {
      return null; // canceled navigation, not a bug
    }

    if (error instanceof AppError) {
      event.fingerprint = ["app-error", error.code];
      event.tags = { ...event.tags, errorCode: error.code };
    }

    return event;
  }
});
```

Works because `name` and `code` are the classification contract: message strings vary per user (`"HTTP 500: /api/users/8231"`), so grouping on them shatters one bug into hundreds of issues.

### Error codes across the server/client boundary

A Next.js server action cannot throw a custom class to the browser — the value gets serialized, so `instanceof` dies at the boundary. Return a stable code instead, and keep the `cause` chain in server logs.

```ts
"use server";
export async function updateEmail(formData: FormData) {
  try {
    await db.user.update({ /* ... */ });
    return { ok: true } as const;
  } catch (error) {
    logger.error(serializeError(new Error("Email update failed", { cause: error })));

    if (isUniqueConstraintViolation(error)) {
      return { ok: false, code: "EMAIL_TAKEN" } as const;
    }
    return { ok: false, code: "UNKNOWN" } as const;
  }
}
```

The client switches on `result.code` to pick field copy. This is the "codes beat instanceof across realms" tradeoff made concrete: the class hierarchy exists per-runtime, the code survives JSON.

> [!tip]
> Log the wrapped error with its `cause` chain server-side, but never send the chain to the client — database error messages leak schema details.

### `AggregateError` from a mirror fallback

A config file is served from two CDN regions. `Promise.any` returns the first success; only when every mirror fails do you get an `AggregateError` carrying each individual failure.

```ts
async function loadRemoteConfig(): Promise<Config> {
  try {
    return await Promise.any([
      fetchJson<Config>("https://cdn-eu.example.com/config.json"),
      fetchJson<Config>("https://cdn-us.example.com/config.json")
    ]);
  } catch (error) {
    if (error instanceof AggregateError) {
      error.errors.forEach((cause, i) => console.error(`Mirror ${i} failed`, cause));
    }
    return DEFAULT_CONFIG;
  }
}
```

Works because `AggregateError.errors` preserves every underlying rejection — without it you would only know "all failed", not that EU returned 403 while US timed out. See [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]].

## 12. Interview Answer

**Short version:** `Error` objects carry failure data such as `name`, `message`, optional `cause`, and often `stack`. JavaScript can throw any value, but production code should throw `Error` instances or structured custom errors so callers can classify and handle failures.

**Strong version:** Built-in errors communicate common JavaScript failure modes, while custom errors model application failures such as validation, auth, rate limits, and HTTP responses. When wrapping an error, I preserve the original with `{ cause }`. In TypeScript I treat caught values as `unknown` and narrow before reading `.message`. I also serialize errors explicitly for logging because standard `Error` fields do not JSON stringify reliably. For public UI I show safe messages and keep technical details in logs.

## 13. Common Mistakes

- Throwing strings or plain objects from application code.
- Catching `unknown` and assuming it has `.message`.
- Wrapping errors without `cause`.
- Creating custom errors without setting `name`.
- Depending only on `instanceof` across server/client or iframe boundaries.
- Sending raw error messages to users.
- Serializing `Error` objects without a custom serializer.
- Creating many custom classes when one `AppError` with a stable `code` would be clearer.

## 14. Practice

1. Write an `ApiError` with `status`, `code`, and `cause`.
2. Explain why `JSON.stringify(new Error("x"))` returns `{}`.
3. Convert `throw "Not found"` into a production-safe custom error.
4. Show how a caller should handle `ValidationError`, `ApiError`, and unknown errors differently.
5. Explain when `instanceof` is useful and when a stable `code` field is safer.

## Related Notes

- [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]]
- [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]
- [[01 - Roadmap|Roadmap]]
