---
tags: [javascript, error-handling, api-error-handling-patterns]
module: "11 - Error Handling"
priority: must-know
status: not-started
---

# API Error Handling Patterns

## Maturity Target

- Priority: #must-know
- Study time: 130-180 minutes
- Interview signal: you can explain why `fetch` does not throw for HTTP errors and design a clean API error model.
- Production signal: network, HTTP, validation, auth, rate-limit, abort, parse, and business-rule failures become predictable UI states.
- Dependencies: [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]], [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]], [[08 - Async JavaScript/06 - AbortController|AbortController]]

## Source Anchors

- [MDN Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- [MDN Response.ok](https://developer.mozilla.org/en-US/docs/Web/API/Response/ok)
- [MDN Response.json](https://developer.mozilla.org/en-US/docs/Web/API/Response/json)
- [MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [Next.js Error Handling](https://nextjs.org/docs/app/getting-started/error-handling)
- Related: [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]], [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]

## 1. Concept

API error handling turns unreliable remote communication into explicit application states.

Failures can happen at several layers:

| Layer | Example | Typical UI response |
| --- | --- | --- |
| Network | offline, DNS, CORS, connection lost | retry, offline message |
| Abort | request canceled because view changed | usually ignore |
| HTTP | 401, 404, 409, 422, 429, 500 | auth flow, not found, validation, retry |
| Parse | response body is not expected JSON | generic error + logging |
| Validation | response shape does not match app contract | safe fallback + logging |
| Business | "email already taken" or "cart expired" | field or workflow message |

## 2. Why It Matters

The browser can successfully receive an HTTP response that means the application failed. A `404` or `500` is a valid HTTP response, so `fetch` resolves. Your code must decide whether that response is success for your application.

Bad API handling creates:

- false success states;
- missing form errors;
- retries that make auth failures worse;
- swallowed server failures;
- stale state after canceled requests;
- unsafe raw error messages shown to users.

## 3. Accurate Mechanism

`fetch()` returns a promise. It rejects for network-level failures and aborts. It resolves for HTTP responses, even when the status is 404 or 500.

```ts
const response = await fetch("/api/products/123");

if (!response.ok) {
  throw new Error(`HTTP ${response.status}`);
}
```

`response.ok` is true for 200-299 statuses.

## 4. Mental Model

Transport success is not product success.

Design your API layer like an adapter:

1. Talk to the platform or library.
2. Normalize platform-specific failure behavior.
3. Throw or return structured domain errors.
4. Let UI layers render states from those errors.

## 5. A Production `fetchJson` Wrapper

```ts
class NetworkError extends Error {
  constructor(message = "Network request failed", options?: ErrorOptions) {
    super(message, options);
    this.name = "NetworkError";
  }
}

class HttpError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly body: unknown,
    options?: ErrorOptions
  ) {
    super(`HTTP ${status}: ${statusText}`, options);
    this.name = "HttpError";
  }
}

async function parseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";

  if (response.status === 204) {
    return null;
  }

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

export async function fetchJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(input, init);
  } catch (error) {
    // Abort is a separate expected path in many UIs.
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }

    throw new NetworkError("Could not reach the server", { cause: error });
  }

  const body = await parseBody(response);

  if (!response.ok) {
    throw new HttpError(response.status, response.statusText, body);
  }

  return body as T;
}
```

Why it works:

- network failures are separated from HTTP failures;
- 204 empty responses do not crash JSON parsing;
- error bodies are preserved for logging or field mapping;
- `AbortError` can be handled intentionally by the caller.

## 6. Real Frontend Example: Form Submission

```tsx
function RegisterForm() {
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setFormError(null);
    setFieldErrors({});

    const formData = new FormData(event.currentTarget);

    try {
      await fetchJson<{ id: string }>("/api/register", {
        method: "POST",
        body: formData
      });

      router.push("/dashboard");
    } catch (error) {
      if (error instanceof HttpError && error.status === 422) {
        // Server validation maps to fields.
        setFieldErrors(normalizeValidationBody(error.body));
        return;
      }

      if (error instanceof HttpError && error.status === 409) {
        setFieldErrors({ email: "Email is already registered." });
        return;
      }

      if (error instanceof HttpError && error.status === 429) {
        setFormError("Too many attempts. Please wait and try again.");
        return;
      }

      console.error("Registration failed", error);
      setFormError("Could not create your account. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {formError && <p role="alert">{formError}</p>}
      <EmailField error={fieldErrors.email} />
      <PasswordField error={fieldErrors.password} />
      <button disabled={isSubmitting}>
        {isSubmitting ? "Creating account..." : "Create account"}
      </button>
    </form>
  );
}
```

Production reasoning:

- field errors stay near inputs;
- form-level errors describe workflow failures;
- raw server details stay out of the UI;
- `finally` reliably clears submitting state.

## 7. Status Code Decision Points

| Status | Common meaning | Frontend response |
| --- | --- | --- |
| 400 | bad request | generic validation or bug report |
| 401 | unauthenticated | redirect/login refresh |
| 403 | forbidden | permission message |
| 404 | resource missing | not found UI or empty state |
| 409 | conflict | show conflict-specific action |
| 422 | validation failed | map field errors |
| 429 | rate limited | wait/retry later message |
| 500+ | server failure | retry option + logging |

Do not blindly retry every failure. Retrying a 401, 403, 404, or validation error usually wastes time. Retrying a transient network or 5xx error can be helpful if the operation is safe to repeat.

## 8. Cancellation and Race Conditions

Problem:

```tsx
useEffect(() => {
  fetchJson<User>(`/api/users/${userId}`)
    .then(setUser)
    .catch(setError);
}, [userId]);
```

Bug:

- user switches from A to B quickly;
- A resolves after B;
- stale A overwrites B;
- cancellation and error state are not modeled.

Fix:

```tsx
useEffect(() => {
  const controller = new AbortController();

  async function load() {
    try {
      const user = await fetchJson<User>(`/api/users/${userId}`, {
        signal: controller.signal
      });
      setUser(user);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setError("Could not load user.");
    }
  }

  void load();

  return () => controller.abort();
}, [userId]);
```

See [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]].

## 9. Runtime Response Validation

TypeScript does not validate JSON at runtime.

```ts
type Product = {
  id: string;
  name: string;
  price: number;
};

function isProduct(value: unknown): value is Product {
  if (typeof value !== "object" || value === null) return false;
  const product = value as Partial<Product>;

  return (
    typeof product.id === "string" &&
    typeof product.name === "string" &&
    typeof product.price === "number"
  );
}

async function loadProduct(id: string) {
  const data = await fetchJson<unknown>(`/api/products/${id}`);

  if (!isProduct(data)) {
    throw new Error("Product response shape changed");
  }

  return data;
}
```

> [!tip] Tradeoff
> manual guards are lightweight but can become repetitive. Schema libraries can centralize validation, but they add runtime cost and a dependency.

## 10. Error Messages: User vs Developer

```ts
function userMessageFor(error: unknown): string {
  if (error instanceof DOMException && error.name === "AbortError") {
    return "";
  }

  if (error instanceof NetworkError) {
    return "Connection failed. Check your internet and try again.";
  }

  if (error instanceof HttpError) {
    if (error.status === 401) return "Please sign in again.";
    if (error.status === 403) return "You do not have permission to do this.";
    if (error.status === 404) return "We could not find that item.";
    if (error.status === 429) return "Too many requests. Please wait a moment.";
    if (error.status >= 500) return "The server is having trouble. Try again later.";
  }

  return "Something went wrong. Please try again.";
}
```

Always log with technical context separately:

```ts
function reportApiError(error: unknown, context: Record<string, unknown>) {
  console.error("API failure", { error, context });
}
```

## 11. Production Checklist

- [ ] `fetch` wrappers check `response.ok`.
- [ ] Network, HTTP, abort, parse, and validation failures are distinguishable.
- [ ] 204 and non-JSON responses do not accidentally crash generic JSON parsing.
- [ ] User-facing messages are safe and specific enough to act on.
- [ ] Technical details are logged with context.
- [ ] Auth and permission failures are not retried blindly.
- [ ] Rate limits and server errors have thoughtful retry behavior.
- [ ] Form field errors and form-level errors are separated.
- [ ] In-flight requests are canceled or ignored when inputs change.
- [ ] Runtime validation protects important API boundaries.

## Real-World Use Cases

### Retry policy that reads the error class

A product list fails intermittently on flaky mobile networks. Blind retry loops hammer the API after a 401 and re-submit requests that can never succeed, so the retry decision has to branch on error type.

```ts
async function fetchWithRetry<T>(url: string, attempts = 3): Promise<T> {
  for (let attempt = 1; ; attempt++) {
    try {
      return await fetchJson<T>(url);
    } catch (error) {
      const retriable =
        error instanceof NetworkError ||
        (error instanceof HttpError &&
          (error.status >= 500 || error.status === 429));

      if (!retriable || attempt === attempts) throw error;
      await sleep(2 ** attempt * 250); // exponential backoff
    }
  }
}
```

This only works because the wrapper throws **distinguishable error classes** — `instanceof` is the branch condition, which is why throwing bare `new Error("failed")` everywhere makes retry policies impossible. See [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]].

> [!tip]
> On a 429, honor the `Retry-After` header before falling back to exponential backoff — the server is telling you the exact wait.

### React Query needs you to throw

`useQuery` marks a query failed only when the query function **rejects**. Raw `fetch` resolves on a 500, so without a throwing wrapper the cache happily stores an HTML error page as "data".

```ts
const { data, error } = useQuery({
  queryKey: ["invoice", invoiceId],
  queryFn: () => fetchJson<Invoice>(`/api/invoices/${invoiceId}`),
  retry: (failureCount, error) =>
    error instanceof HttpError && error.status < 500
      ? false                  // 4xx will not improve with retries
      : failureCount < 3,
});
```

The library's `retry` predicate, `error` state, and error-boundary integration all key off rejection — "transport success is not product success" decides whether your cache gets poisoned. See [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]].

### Dashboard widgets degrading independently

A home dashboard fires four requests on load. With `Promise.all`, one widget's 500 rejects the whole screen; `Promise.allSettled` lets each card render its own success or error state.

```ts
const [orders, revenue, alerts] = await Promise.allSettled([
  fetchJson<Order[]>("/api/orders/recent"),
  fetchJson<Revenue>("/api/revenue/summary"),
  fetchJson<Alert[]>("/api/alerts"),
]);

// per widget:
// result.status === "fulfilled" ? render(result.value) : renderError(result.reason)
```

Because every failure was normalized into typed errors upstream, each `result.reason` maps safely to user copy through `userMessageFor`. See [[08 - Async JavaScript/03 - Promise Methods|Promise Methods]].

## 12. Interview Answer

**Short version:** `fetch` rejects for network failures, not for HTTP error status codes. A `404` or `500` still resolves to a `Response`, so production code checks `response.ok`, parses the body intentionally, and throws a structured error.

**Strong version:** API error handling has layers: network, abort, HTTP, parse, validation, and business rules. I usually centralize `fetch` in a wrapper that separates network errors from `HttpError`, preserves the response body, handles empty responses, and lets UI code map statuses to user actions. For forms, 422 maps to field errors, 401 maps to auth recovery, 429 maps to wait/retry messaging, and 500 gets a retry plus logging. I avoid showing raw server messages to users and make sure every async request has ownership, cancellation, and a clear UI state.

## 13. Common Mistakes

- Assuming `fetch` throws on 404 or 500.
- Parsing every response as JSON, including 204 or HTML error pages.
- Retrying client errors that cannot succeed with repetition.
- Showing raw backend error messages in the UI.
- Swallowing caught errors and leaving users with no feedback.
- Treating aborts as failures.
- Updating state from stale requests after route or input changes.
- Trusting TypeScript types for unvalidated JSON.
- Handling every HTTP status with the same generic message.

## 14. Practice

1. Write a `fetchJson` wrapper that throws `HttpError` for non-2xx responses.
2. Explain why a 500 response does not enter `catch` unless you throw.
3. Map 401, 403, 404, 422, 429, and 500 to frontend UI actions.
4. Add `AbortController` to a request in a React effect.
5. Add runtime validation for a critical API response.
6. Design an error message strategy that separates user-safe copy from developer logs.

## Related Notes

- [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]]
- [[11 - Error Handling/02 - Error Objects and Custom Errors|Error Objects and Custom Errors]]
- [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]]
- [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
- [[01 - Roadmap|Roadmap]]
