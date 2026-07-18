---
tags: [javascript, network, fetch, async]
module: "19 - DOM and Browser APIs"
priority: must-know
status: not-started
aliases: [Fetch API]
---

# fetch Deep Dive

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can explain why fetch doesn't reject on 404, what a body stream being "consumed once" means, credentials modes, and how to implement timeout + retry correctly.
- Production signal: your data layer handles HTTP errors, network errors, aborts, and JSON parse failures as *distinct* cases.
- Dependencies: [[08 - Async JavaScript/02 - Promises|Promises]], [[08 - Async JavaScript/06 - AbortController|AbortController]], [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]

## Source Anchors

- [Fetch Living Standard](https://fetch.spec.whatwg.org/)
- [MDN - Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- [MDN - Response](https://developer.mozilla.org/en-US/docs/Web/API/Response)
- [MDN - AbortSignal.timeout](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal/timeout_static)
- [MDN - ReadableStream](https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream)

## 1. Concept

`fetch(input, init)` returns a promise for a `Response` — an object wrapping status, headers, and a **body stream**. Three design decisions explain most fetch surprises:

1. **The promise tracks the *network operation*, not HTTP success.** It resolves for a 500 and rejects only for network-level failure (DNS, offline, CORS block, abort).
2. **The promise resolves at headers-received time.** The body may still be streaming — that's why reading it (`res.json()`) is a *second* await.
3. **Bodies are streams, consumable once.** `res.json()` and `res.text()` drain the stream; a second read throws `TypeError: body ... already read`.

```js
const res = await fetch("/api/orders");        // resolves once headers arrive
if (!res.ok) throw new HttpError(res.status);  // 4xx/5xx: YOUR job to check
const data = await res.json();                 // drains the body stream
```

## 2. Why It Matters

Every frontend data layer — including what React Query, SWR, and Next.js wrap — sits on these semantics. Seniors are expected to build (and debug) the wrapper: distinguishing "server said no" from "network died" from "we gave up", without caching half-read bodies or retrying non-idempotent requests.

## 3. Request Anatomy: The Options That Bite

```js
await fetch("/api/orders", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(order),
  credentials: "same-origin",  // see below
  signal: ac.signal,           // cancellation
  cache: "no-store",           // bypass HTTP cache
  keepalive: true,             // survive page unload (analytics; ~64KB cap)
});
```

**Credentials modes** — whether cookies (and HTTP auth) are attached:

| Mode | Behavior |
| --- | --- |
| `omit` | Never send cookies |
| `same-origin` (default) | Cookies only for same-origin requests |
| `include` | Cookies also on cross-origin requests — requires the server to respond with `Access-Control-Allow-Credentials: true` **and** a non-wildcard `Access-Control-Allow-Origin` |

The classic bug: "login works but every subsequent API call is 401" on a cross-origin API — the session cookie isn't being sent because nobody set `credentials: "include"` (and/or the cookie lacks `SameSite=None; Secure`). Full story in [[20 - Network and Security/03 - CORS Correctly Explained|CORS]] and [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]].

**Bodies you can send:** string, `FormData` (browser sets multipart boundary — don't set Content-Type yourself, see [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]), `URLSearchParams`, `Blob`, `ArrayBuffer`, `ReadableStream`.

**Headers** is a class with case-insensitive names: `res.headers.get("content-type")`. You can't read cross-origin response headers beyond a safelist unless the server exposes them (`Access-Control-Expose-Headers`).

## 4. Streams: What "Body Consumed Once" Enables

`res.body` is a `ReadableStream` of `Uint8Array` chunks. `res.json()` is just "read everything, decode, parse". Reading manually enables progress and incremental processing:

```js
const res = await fetch("/api/export.csv");
const reader = res.body.getReader();
const total = Number(res.headers.get("Content-Length")) || 0;
let received = 0;

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  received += value.byteLength;
  if (total) updateProgressBar(received / total);
}
```

Need the body twice (e.g., try JSON, fall back to text for error pages)? `res.clone()` *before* reading tees the stream. Cloning makes the browser buffer for the slower consumer — fine for API payloads, wasteful for large files.

> [!tip] Streaming is also how AI-style UIs work
> Server-sent chunks rendered as they arrive = `res.body.getReader()` + `TextDecoder` in a loop. The same mechanism underlies Next.js streaming SSR responses ([[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]).

## 5. Real Frontend Example: Bug → Fix → Tradeoff (Timeout + Retry)

Buggy version — the wrapper "everyone writes first":

```js
async function getJSON(url) {
  try {
    const res = await fetch(url);
    return await res.json();
  } catch {
    return getJSON(url); // "just retry"
  }
}
```

Traced failures:

1. A 500 response *resolves* → `res.json()` on an HTML error page throws `SyntaxError` → caught → **infinite retry loop** hammering a failing server.
2. No timeout: fetch has none by default — a hung connection pends for minutes.
3. Unbounded recursive retry with no backoff: self-inflicted DDoS during outages, and it retries POSTs the same as GETs if reused.

Production-safe fix:

```js
class HttpError extends Error {
  constructor(res) {
    super(`HTTP ${res.status} ${res.statusText}`);
    this.name = "HttpError";
    this.status = res.status;
  }
}

async function getJSON(url, { retries = 2, timeoutMs = 8000, signal } = {}) {
  for (let attempt = 0; ; attempt++) {
    try {
      const res = await fetch(url, {
        // Give up after timeoutMs OR when the caller aborts — whichever first.
        signal: AbortSignal.any([AbortSignal.timeout(timeoutMs), signal].filter(Boolean)),
      });
      if (!res.ok) throw new HttpError(res);
      return await res.json();
    } catch (err) {
      const retriable =
        err.name === "TimeoutError" ||
        (err instanceof TypeError) ||                      // network failure
        (err instanceof HttpError && err.status >= 500);   // server fault
      const aborted = err.name === "AbortError";           // caller cancelled: never retry
      if (aborted || !retriable || attempt >= retries) throw err;
      await new Promise((r) => setTimeout(r, 2 ** attempt * 300 + Math.random() * 100));
    }
  }
}
```

Trace of the design: HTTP errors become typed exceptions (4xx = caller bug/user input → don't retry; 5xx = transient → retry); `TimeoutError` (from `AbortSignal.timeout`) is distinguishable from a caller's `AbortError` (component unmounted → stop entirely); exponential backoff with jitter prevents synchronized retry storms.

Tradeoffs: retries are only safe for idempotent requests — a timed-out POST may have *succeeded server-side*, so retrying can double-charge; POST retry needs idempotency keys. Timeout values are product decisions (search box: 3s; report generation: 60s). At some scope this wrapper *is* React Query/SWR — adopting one is often the honest fix.

## 6. Common Bugs and Edge Cases

- `await res.json()` on a 204 No Content throws — check status or use `res.text()` and guard empty.
- Reading `res.json()` twice: "body stream already read". Clone first or store the parsed result.
- Setting `Content-Type` manually alongside a `FormData` body breaks the multipart boundary.
- CORS failures reject as an opaque `TypeError: Failed to fetch` — indistinguishable from offline in JS; the *why* is only in devtools. See [[20 - Network and Security/03 - CORS Correctly Explained|CORS]].
- `cache: "no-store"` vs `"no-cache"`: the first bypasses the HTTP cache entirely; the second revalidates. See [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]].
- In React effects, an unguarded `setState` after fetch resolves on an unmounted component = the classic race; abort in cleanup ([[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]).

## Real-World Use Cases

### Auth token refresh queue (single-flight 401 recovery)

An access token expires mid-session; five components fire requests simultaneously and all get 401. Naive per-request refresh sends five refresh calls — token rotation invalidates four of them and logs the user out. The fix: one shared in-flight refresh promise.

```ts
let refreshing: Promise<void> | null = null;

async function apiFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const res = await fetch(url, { ...init, credentials: "include" });
  if (res.status !== 401) return res;

  refreshing ??= fetch("/auth/refresh", { method: "POST", credentials: "include" })
    .then((r) => { if (!r.ok) throw new SessionExpiredError(); })
    .finally(() => { refreshing = null; });

  await refreshing;                      // all concurrent 401s await the SAME promise
  return fetch(url, { ...init, credentials: "include" }); // replay once
}
```

Works because a 401 *resolves* — the wrapper can inspect status and replay, and the module-level promise makes concurrent callers share one refresh ([[08 - Async JavaScript/02 - Promises|Promises]]). Replaying a request whose body was a one-shot stream requires rebuilding `init`, not reusing a consumed `Request`.

### Next.js server-side fetch: the same API, extended caching

In React Server Components, `fetch` is the data layer — and Next.js patches it with cache semantics, so the `init` object now encodes your rendering strategy.

```tsx
// Product page (RSC)
const product = await fetch(`${API}/products/${id}`, {
  next: { revalidate: 3600, tags: [`product-${id}`] }, // ISR: cached, refreshed hourly
}).then((r) => { if (!r.ok) notFound(); return r.json(); });

const stock = await fetch(`${API}/stock/${id}`, {
  cache: "no-store",                                   // always fresh → dynamic render
}).then((r) => r.json());
```

Works because these are ordinary Fetch API options plus a `next` extension — but `cache: "no-store"` anywhere in a route opts that route out of static rendering, so a stray "always fresh" fetch silently changes deployment behavior ([[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]], [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]).

### Avatar upload: FormData and the upload-progress gap

A settings page uploads a profile photo. Two fetch-specific facts decide the implementation: the browser must set the multipart boundary itself, and fetch has **no upload progress events**.

```js
async function uploadAvatar(file) {
  const body = new FormData();
  body.append("avatar", file, file.name);
  const res = await fetch("/api/me/avatar", {
    method: "POST",
    body, // NO Content-Type header — browser writes multipart boundary itself
  });
  if (!res.ok) throw new HttpError(res);
  return res.json();
}
```

Works because a `FormData` body makes fetch generate `Content-Type: multipart/form-data; boundary=...`; setting the header manually omits the boundary and the server rejects the parse ([[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]).

> [!warning]
> `res.body` streaming gives *download* progress only. For a real upload progress bar you still need `XMLHttpRequest` (`xhr.upload.onprogress`) — request-body streaming in fetch requires HTTP/2 plus `duplex: "half"` and has narrow browser support. Interviewers like this asymmetry; most candidates assume fetch does both.

## 7. Interview Answer

Short answer:

> fetch resolves when response headers arrive and only rejects on network-level failure — a 404 resolves fine, so you check `res.ok` yourself. The body is a one-shot stream; `res.json()` drains it. There's no built-in timeout; you compose one with `AbortSignal.timeout`.

Deeper answer:

> A production wrapper distinguishes four outcomes: HTTP error (typed error carrying status; retry only 5xx), network failure (TypeError; retriable), timeout (AbortSignal.timeout → TimeoutError; retriable with backoff and jitter), and caller abort (AbortError; never retry). Cross-origin cookie flows need `credentials: "include"` plus matching server CORS headers, and body streams enable progress UIs and incremental rendering via `getReader()`.

## 8. Practice

1. <details><summary>`fetch("/api/x").catch(handle)` — which of these invoke `handle`: 404, 500, CORS rejection, offline, malformed JSON body?</summary>CORS rejection and offline (both network-level → the fetch promise rejects with TypeError). 404 and 500 resolve — never reach catch unless you throw on `!res.ok`. Malformed JSON only rejects the *`res.json()`* promise — it reaches this catch only if the call chain awaits json() inside the same chain.</details>

2. <details><summary>Why can retrying a timed-out POST create duplicate orders, and what's the standard fix?</summary>Timeout means *you stopped waiting* — the server may have received and processed the request; the response just never arrived. Retrying re-executes a possibly-completed non-idempotent operation. Fix: client-generated idempotency key header per logical operation; the server deduplicates. Alternatively only auto-retry idempotent methods (GET/PUT/DELETE by contract).</details>

3. <details><summary>Implement "parse JSON, but if parsing fails, log the raw text" — why does the naive version throw, and what's the fix?</summary>Naive: `try { await res.json() } catch { log(await res.text()) }` — throws "body already read": json() drained the stream even though parsing failed. Fix: `const copy = res.clone();` before reading, then read text from the clone in the catch. Or read `text()` once and `JSON.parse` it yourself, which needs no clone.</details>

4. <details><summary>What does `keepalive: true` do and when is it required?</summary>It lets the request outlive the page (unload/navigation) — normally in-flight fetches are dropped on unload. Required for last-moment analytics/beacons ("user left the checkout"). Payload is capped (~64KB in-flight per origin) and streaming responses aren't available. `navigator.sendBeacon` is the older single-purpose sibling.</details>

## Related Notes

- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]]
- [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]]
- [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]
- [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]
- [[01 - Roadmap|Roadmap]]
