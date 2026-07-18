---
tags: [javascript, async, api-integration-examples]
module: "08 - Async JavaScript"
priority: must-know
status: not-started
---

# API Integration Examples

## Maturity Target

- Priority: #must-know
- Study time: 140-180 minutes
- Interview signal: you can turn promises, fetch, errors, cancellation, retries, and loading states into a coherent data layer.
- Production signal: your app does not scatter raw fetch calls, duplicate request policy, or inconsistent error UI across components.
- Dependencies: [[08 - Async JavaScript/02 - Promises|Promises]], [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]], [[08 - Async JavaScript/06 - AbortController|AbortController]]

## Source Anchors

- [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [MDN Response.ok](https://developer.mozilla.org/en-US/docs/Web/API/Response/ok)
- [MDN Response.json](https://developer.mozilla.org/en-US/docs/Web/API/Response/json)
- [MDN AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [React useEffect](https://react.dev/reference/react/useEffect)
- [Next.js: Fetching Data](https://nextjs.org/docs/app/getting-started/fetching-data)

## 1. Concept

API integration is the layer that turns async primitives into predictable application behavior:

```txt
request construction -> auth/headers -> fetch -> error parsing -> JSON parsing
-> cancellation -> retry/dedupe/cache policy -> UI states
```

The mature goal is not "know fetch." It is "make all network behavior consistent and recoverable."

## 2. Why It Matters

Raw `fetch` calls scattered through components create drift:

- one component checks `response.ok`, another forgets
- one request sends auth headers, another misses them
- one screen ignores abort errors, another shows them as failures
- retries happen in one place but not another
- telemetry lacks status codes and request context
- duplicate submit prevention is inconsistent
- loading and error states feel different across the app

A serious frontend codebase puts network policy at clear boundaries.

## 3. Official Mechanism

Fetch returns a promise for a `Response`. Important behavior:

- network failure and abort reject the fetch promise
- HTTP 404/500 still produce a `Response`; check `response.ok`
- response body parsing such as `response.json()` is another async step
- request cancellation uses `AbortSignal`
- request/response objects are Web API concepts, not ECMAScript promises

React and Next.js add placement questions:

- Should this fetch happen on the server or client?
- Should it run during render, in an effect, in a route handler, or in an event handler?
- Is the data cacheable, user-specific, or mutation result?
- What owns retries, stale data, and invalidation?

## 4. Mental Model

Use three layers:

| Layer | Responsibility |
| --- | --- |
| transport utility | URL, headers, method, body, response parsing, typed errors |
| data operation | `getUser`, `updateProfile`, `searchProducts` |
| UI/query layer | loading, stale data, retry, cancellation, mutation side effects |

Do not make every component rediscover HTTP policy.

## 5. API Error Type

```ts
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}
```

Why:

- components can branch on status
- telemetry can attach status/body safely
- retry policy can avoid retrying permanent failures
- form code can map validation errors to fields

## 6. Typed Fetch Boundary

```ts
type QueryParams = Record<string, string | number | boolean | undefined>;

type ApiFetchOptions = RequestInit & {
  params?: QueryParams;
};

const API_BASE_URL = "/api";

function buildUrl(path: string, params?: QueryParams) {
  const url = new URL(path, "https://example.local");
  const base = API_BASE_URL.replace(/\/$/, "");
  const cleanPath = path.startsWith("/") ? path : `/${path}`;

  url.pathname = `${base}${cleanPath}`;

  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }

  return `${url.pathname}${url.search}`;
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { params, headers, body, ...init } = options;

  const response = await fetch(buildUrl(path, params), {
    ...init,
    body,
    headers: {
      Accept: "application/json",
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    let errorBody: unknown;

    try {
      errorBody = await response.json();
    } catch {
      errorBody = undefined;
    }

    throw new ApiError(`HTTP ${response.status}`, response.status, errorBody);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
```

This is a teaching example. In a real app, the base URL should come from environment/runtime config, and authentication headers should be added in one controlled place.

## 7. Data Operation Layer

```ts
type User = {
  id: string;
  name: string;
  email: string;
};

type UpdateUserInput = {
  name?: string;
  email?: string;
};

export const usersApi = {
  list(signal?: AbortSignal) {
    return apiFetch<User[]>("/users", { signal });
  },

  detail(userId: string, signal?: AbortSignal) {
    return apiFetch<User>(`/users/${userId}`, { signal });
  },

  update(userId: string, input: UpdateUserInput) {
    return apiFetch<User>(`/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    });
  },
};
```

Benefits:

- UI code calls domain operations instead of raw URLs
- tests can mock `usersApi`
- request policy stays centralized
- types describe the data contract

## 8. Client Fetch In React Effect

```jsx
function UserProfile({ userId }) {
  const [state, setState] = useState({
    status: "idle",
    user: null,
    error: null,
  });

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setState({ status: "loading", user: null, error: null });

      try {
        const user = await usersApi.detail(userId, controller.signal);
        setState({ status: "success", user, error: null });
      } catch (error) {
        if (controller.signal.aborted) return;
        setState({ status: "error", user: null, error });
      }
    }

    load();

    return () => controller.abort();
  }, [userId]);

  if (state.status === "loading") return <UserSkeleton />;
  if (state.status === "error") return <RetryPanel error={state.error} />;
  if (state.status === "success") return <UserCard user={state.user} />;
  return null;
}
```

This is fine for learning and small apps. In larger apps, a query library usually handles caching, dedupe, retries, background refresh, and cancellation more consistently.

## 9. Request State Shape

Avoid separate booleans that can contradict each other:

```js
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);
const [data, setData] = useState(null);
```

These can accidentally represent impossible states, such as `loading: true` with stale `error`.

Prefer a discriminated state:

```ts
type RequestState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: unknown };
```

Then rendering becomes explicit:

```ts
function renderState<T>(state: RequestState<T>) {
  switch (state.status) {
    case "idle":
      return "Nothing loaded yet";
    case "loading":
      return "Loading";
    case "success":
      return "Ready";
    case "error":
      return "Error";
  }
}
```

## 10. Mutation Pattern: Prevent Duplicates

### Problem

```js
async function handleSubmit(values) {
  await usersApi.update(userId, values);
  showToast("Saved");
}
```

### Bug

> [!warning] Double-clicks double-submit
> Without an in-flight guard, fast double-clicks fire the request twice; if the endpoint isn't idempotent, the user creates duplicate work (double orders/charges). Disable the control while submitting, and back it with a server-side idempotency key.

### Fix

```jsx
function ProfileForm({ userId }) {
  const [saving, setSaving] = useState(false);

  async function handleSubmit(values) {
    if (saving) return;

    setSaving(true);

    try {
      await usersApi.update(userId, values);
      showToast("Saved");
    } catch (error) {
      if (isApiError(error) && error.status === 422) {
        showToast("Please fix the highlighted fields.");
      } else {
        showToast("Could not save. Try again.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <button disabled={saving}>
        {saving ? "Saving..." : "Save"}
      </button>
    </form>
  );
}
```

For critical mutations, pair UI prevention with server idempotency keys.

## 11. Retry Policy

```ts
function shouldRetry(error: unknown) {
  if (!isApiError(error)) {
    return true;
  }

  if ([400, 401, 403, 404, 409, 422].includes(error.status)) {
    return false;
  }

  return error.status >= 500;
}
```

Use retries for transient failures. Do not retry validation, permission, auth, not-found, or conflict errors by default.

## 12. Reads vs Mutations

| Operation | Examples | Client behavior |
| --- | --- | --- |
| read/query | list users, get profile, search products | cache, dedupe, abort obsolete work, background refresh |
| mutation | save profile, create order, delete item | disable duplicate submit, optimistic update carefully, invalidate reads |
| critical mutation | payment, booking, transfer | server idempotency, explicit final state, no blind retry |

This distinction is often more important than whether you use `fetch`, Axios, a query library, or server functions.

## 13. Next.js Placement

Server component style:

```tsx
export default async function UsersPage() {
  const users = await usersApi.list();

  return <UsersList users={users} />;
}
```

Client component style:

```tsx
"use client";

function UsersSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);

  useEffect(() => {
    const controller = new AbortController();

    async function search() {
      const data = await apiFetch<User[]>("/users/search", {
        params: { query },
        signal: controller.signal,
      });

      setResults(data);
    }

    search().catch(error => {
      if (!controller.signal.aborted) reportError(error);
    });

    return () => controller.abort();
  }, [query]);

  return <SearchResults results={results} />;
}
```

Decision point:

- server fetch: good for initial page data, SEO, secrets, and reducing client waterfalls
- client fetch: good for user-driven interactions, live search, browser-only state, and post-load updates
- route handler/server action: good for protecting secrets and enforcing backend policy

## 14. Race Condition Guard

When cancellation is not supported, guard with request identity:

```js
let latestRequestId = 0;

async function search(query) {
  const requestId = ++latestRequestId;
  const results = await apiFetch("/search", {
    params: { query },
  });

  if (requestId !== latestRequestId) {
    return;
  }

  setResults(results);
}
```

This does not stop network work, but it prevents stale state writes.

## 15. Observability

Log useful request context:

```ts
function reportApiError(error: unknown, context: Record<string, unknown>) {
  if (isApiError(error)) {
    reportError({
      type: "api",
      status: error.status,
      body: error.body,
      ...context,
    });
    return;
  }

  reportError({
    type: "unknown",
    message: error instanceof Error ? error.message : String(error),
    ...context,
  });
}
```

Useful context:

- endpoint or operation name
- HTTP status
- request id or trace id
- user action that triggered it
- whether it was initial load, refetch, mutation, retry, or background refresh
- whether it was aborted, timed out, or failed

## 16. Testing Checklist

Test more than success:

- loading state appears
- HTTP 404 maps to not found
- HTTP 401 maps to login/session recovery
- HTTP 422 maps to field errors
- HTTP 500 shows retry
- invalid JSON is handled
- aborted request does not show an error
- stale response does not overwrite newer results
- duplicate submit is prevented
- `204 No Content` does not try to parse JSON

## Real-World Use Cases

### Auth token refresh queue

An access token expires while five components have requests in flight — all five get 401. Naive handling triggers five refresh calls (and some auth servers revoke the token family on concurrent refreshes). Share one in-flight refresh promise instead.

```ts
let refreshPromise: Promise<void> | null = null;

async function withAuth<T>(operation: () => Promise<T>): Promise<T> {
  try {
    return await operation();
  } catch (error) {
    if (!isApiError(error) || error.status !== 401) throw error;

    refreshPromise ??= refreshAccessToken().finally(() => {
      refreshPromise = null;
    });

    await refreshPromise; // concurrent 401s all wait on the SAME refresh
    return operation();   // retry exactly once with the new token
  }
}

const user = await withAuth(() => usersApi.detail(userId));
```

Works because a promise is a shareable handle: the first 401 creates the refresh, the other four find `refreshPromise` already set and just await it. Same mechanism as the read-dedup cache in [[08 - Async JavaScript/02 - Promises|Promises]], applied to auth.

> [!warning]
> Retry once, not in a loop — if the refresh itself returns 401, escalate to logout. And note `operation` must be a factory (a function), because a settled promise cannot be re-run.

### Optimistic favorite toggle with rollback

Waiting a network round-trip to fill in a heart icon feels broken. Apply the mutation to local state immediately, then reconcile with the server — and keep the previous state so failure can roll back.

```tsx
async function toggleFavorite(productId: string) {
  const previous = favorites;
  const next = new Set(previous);
  next.has(productId) ? next.delete(productId) : next.add(productId);

  setFavorites(next); // optimistic: paint now

  try {
    await productsApi.setFavorite(productId, next.has(productId));
  } catch (error) {
    setFavorites(previous); // rollback to the snapshot
    showToast("Could not update favorites.");
    reportApiError(error, { operation: "setFavorite", productId });
  }
}
```

Works because the mutation row of the reads-vs-mutations table (section 12) owns reconciliation: the UI commits speculatively, and the rejected promise is the signal to restore the snapshot. Query libraries formalize exactly this as `onMutate`/`onError` rollback.

> [!warning]
> Rapid toggling creates overlapping mutations whose responses can land out of order — the race guard from section 14 (or per-item request versioning) applies to mutations too.

### Prefetch on hover

Product cards prefetch detail data when the pointer enters, so the detail page opens warm. This only stays cheap if the data layer dedupes — otherwise hover-scrubbing across ten cards fires ten wasted requests each.

```tsx
function ProductCard({ product }: { product: ProductSummary }) {
  return (
    <Link
      href={`/products/${product.id}`}
      onMouseEnter={() => {
        prefetch(`product:${product.id}`, () => productsApi.detail(product.id));
      }}
    >
      {product.name}
    </Link>
  );
}

const prefetchCache = new Map<string, Promise<unknown>>();

function prefetch(key: string, load: () => Promise<unknown>) {
  if (prefetchCache.has(key)) return;
  prefetchCache.set(key, load().catch(() => prefetchCache.delete(key)));
}
```

Works because the cache stores the promise, so navigation-time reads await the same flight the hover started — and the `.catch` both prevents an unhandled rejection (a prefetch has no UI owner) and evicts failures so navigation retries cleanly. See [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]].

## 17. Interview Answer

**Short version:** A mature API layer centralizes fetch, errors, cancellation, loading states, and request policy instead of scattering raw fetch calls in every component.

**Strong version:** I put transport behavior in a shared boundary: build URLs, attach headers, pass `AbortSignal`, check `response.ok`, parse errors, handle `204`, and throw typed errors. Then domain functions such as `usersApi.detail` expose meaningful operations. The UI/query layer owns loading states, retries, caching, stale data, and mutation side effects. For React effects, I abort obsolete reads. For mutations, I prevent duplicate submits and rely on server idempotency for critical operations. In Next.js, I decide whether data belongs on the server, client, or route boundary based on caching, secrecy, interactivity, and user timing.

## 18. Common Mistakes

- Calling raw `fetch` everywhere.
- Forgetting `response.ok`.
- Parsing JSON for `204 No Content`.
- Showing abort cleanup as an error.
- Treating every failure as retryable.
- Retrying non-idempotent mutations blindly.
- Storing inconsistent `loading/error/data` booleans.
- Fetching client-side data that could have been server-rendered.
- Fetching server-side data that depends on browser-only state.
- Missing telemetry context for failures.

## 19. Practice

1. Build an `apiFetch` wrapper with `ApiError`.
2. Add `AbortSignal` support to a domain API function.
3. Model request state as a discriminated union.
4. Write UI behavior for 401, 404, 422, 500, timeout, and abort.
5. Convert a component with scattered fetch logic into a domain API plus UI state.
6. Decide whether a Next.js data request belongs in a server component, client component, route handler, or event handler.

## Related Notes

- [[08 - Async JavaScript/02 - Promises|Promises]]
- [[08 - Async JavaScript/04 - Async Await|Async Await]]
- [[08 - Async JavaScript/05 - Async Error Handling|Async Error Handling]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|Preventing Duplicate API Requests]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
