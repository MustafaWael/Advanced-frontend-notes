---
tags: [javascript, network, http]
module: "20 - Network and Security"
priority: must-know
status: not-started
aliases: [HTTP]
---

# HTTP Essentials for Frontend

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can use methods and status codes precisely (idempotency included), read headers fluently, and give an overview-level account of HTTP/1.1 vs 2 vs 3.
- Production signal: you choose status-code handling in your data layer deliberately (retry 503, don't retry 400) and can explain a waterfall in the Network tab.
- Dependencies: [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]], [[08 - Async JavaScript/02 - Promises|Promises]]

## Source Anchors

- [MDN - HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview)
- [RFC 9110 - HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
- [MDN - HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)
- [web.dev - HTTP/2](https://web.dev/articles/performance-http2)
- [MDN - HTTP versions and evolution](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Evolution_of_HTTP)

## 1. Concept

HTTP is a stateless request/response protocol: every request carries everything the server needs (URL, method, headers, body); every response carries a status code, headers, and usually a body. "Stateless" is why cookies and tokens exist at all — continuity must be smuggled back in via headers ([[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]).

## 2. Methods — Semantics, Not Spelling

| Method  | Semantics                         | Safe | Idempotent | Body |
| ------- | --------------------------------- | ---- | ---------- | ---- |
| GET     | Read a resource                   | ✅    | ✅          | No   |
| HEAD    | GET without the body              | ✅    | ✅          | No   |
| POST    | Create / non-idempotent action    | ❌    | ❌          | Yes  |
| PUT     | Replace entire resource           | ❌    | ✅          | Yes  |
| PATCH   | Partial update                    | ❌    | ❌*         | Yes  |
| DELETE  | Remove                            | ❌    | ✅          | Rare |
| OPTIONS | Ask capabilities (CORS preflight) | ✅    | ✅          | No   |

*PATCH can be designed idempotent but isn't guaranteed by spec.

**Safe** = no server state change (browsers/proxies may prefetch and cache GETs — which is why "GET that mutates" is a real incident category: crawlers and prefetchers "click" your delete links). **Idempotent** = N identical requests ≡ 1 — this is what makes automatic retry legal; a timed-out DELETE can be retried, a timed-out POST cannot without an idempotency key ([[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]] covers the retry wrapper).

## 3. Status Codes — The Ones That Drive Code Paths

- **2xx**: 200 OK; 201 Created (+ `Location`); **204 No Content** — beware `res.json()` throwing on an empty body.
- **3xx**: 301/308 permanent vs 302/307 temporary (307/308 preserve the method — 302 historically let POSTs become GETs); **304 Not Modified** — the caching handshake ([[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]).
- **4xx — client's fault, don't blind-retry**: 400 malformed; **401 unauthenticated** vs **403 unauthorized** (distinct UX: re-login vs "no access"); 404; 409 conflict (optimistic concurrency); 422 validation; **429 rate-limited** — honor `Retry-After`.
- **5xx — server's fault, retry with backoff is reasonable**: 500; 502/504 (bad gateway/timeout — often infra, not app); **503 unavailable** — the canonical "retry later, with jitter".

A senior tell: your fetch wrapper treats these as *branches* (401 → refresh token flow; 429 → scheduled retry; 400 → surface validation; 503 → backoff), not as one `!res.ok` bucket.

## 4. Headers Worth Knowing Cold

Request: `Accept`, `Content-Type` (what *you're sending*), `Authorization`, `Cookie`, `Origin`/`Referer`, `If-None-Match` (caching). Response: `Content-Type` (mismatch = the classic "JSON parse error on an HTML error page"), `Set-Cookie`, `Cache-Control`/`ETag`, `Location`, CORS headers (`Access-Control-*`), security headers (`Content-Security-Policy`, `Strict-Transport-Security` — [[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]).

> [!tip] The Network tab is the source of truth
> Most "mystery" frontend bugs resolve in 30 seconds once you read the actual request/response: wrong Content-Type, missing cookie, unexpected 304, a redirect eating your POST, an OPTIONS preflight failing. Debug from the wire in, not from the code out.

## 5. HTTP/1.1 vs 2 vs 3 — Overview Level

- **HTTP/1.1**: one request at a time per TCP connection (pipelining failed in practice) → browsers opened ~6 parallel connections per origin → **head-of-line blocking** at the connection level. This era's workarounds — sprite sheets, bundle-everything, domain sharding — shaped old frontend "best practices".
- **HTTP/2**: one TCP connection, many interleaved **streams** (multiplexing), header compression (HPACK), prioritization. Kills most 1.1 workarounds: many small files became fine, which is what made fine-grained code splitting and preload economical. Remaining flaw: a lost TCP packet stalls *all* streams (TCP-level head-of-line blocking).
- **HTTP/3**: runs on **QUIC over UDP**: streams are independent at the transport level (packet loss stalls only its stream), faster handshakes (0/1-RTT), connection migration (Wi-Fi→cellular without reconnect). Negotiated via the `Alt-Svc` header; you mostly get it "for free" from CDNs.

Frontend consequences to actually say: under HTTP/2+, bundling is a *cache-granularity* decision, not a connection-count one; domain sharding is actively harmful (breaks multiplexing); and per-request overhead is low enough that request *waterfalls* (sequential dependent fetches) dominate performance instead — see [[22 - Next.js Deep Dive/06 - Data Fetching Patterns|Data Fetching Patterns]].

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — one bucket for all failures:

```js
async function apiFetch(url, init) {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error("Request failed");   // 400? 401? 429? 503? Who knows.
  return res.json();
}
```

Traced failures: a 401 (expired session) shows the same toast as a 503 (deploy blip) — users see "Request failed" and rage-refresh; the retry layer (if any) retries 400s (pointless, hammers server with the same bad payload) and doesn't honor 429's `Retry-After`; a 204 from a DELETE crashes on `res.json()`.

Production-safe fix:

```js
class ApiError extends Error {
  constructor(res, body) {
    super(`${res.status} ${res.statusText}`);
    this.status = res.status;
    this.retryAfter = Number(res.headers.get("Retry-After")) || null;
    this.body = body;
  }
}

async function apiFetch(url, init) {
  const res = await fetch(url, init);
  if (res.status === 401) return handleAuthRefresh(url, init); // one retry after refresh
  if (!res.ok) {
    const body = await res.json().catch(() => null);           // error envelope if present
    throw new ApiError(res, body);
  }
  if (res.status === 204) return null;
  return res.json();
}
// Retry policy elsewhere: only network errors, 429 (respect retryAfter), and 5xx; backoff + jitter.
```

Tradeoff: the 401-refresh path must guard against loops (refresh returns 401 → logout, don't recurse) and against thundering herds (dedupe concurrent refreshes behind one promise — [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|same pattern]]). More branches = more tests; that's the cost of good failure UX.

## Real-World Use Cases

### FormData upload broken by a wrapper's default Content-Type

An avatar upload returns 400 "Malformed multipart body" — but only through the shared `apiFetch` wrapper, never in a scratch `fetch`. The wrapper defaults `Content-Type` onto every request.

```js
const form = new FormData();
form.append("avatar", file);

// Broken: any hand-set Content-Type destroys the boundary parameter
fetch("/api/avatar", {
  method: "POST",
  headers: { "Content-Type": "multipart/form-data" }, // no boundary=... → unparseable
  body: form,
});

// Fix: omit the header — the browser writes
// Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryX7…
fetch("/api/avatar", { method: "POST", body: form });
```

This is the section-4 `Content-Type` contract in action: the header describes the body's *serialization*, and multipart is only parseable with the browser-generated boundary token — so wrapper defaults must be per-body-type, not global ([[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]).

### 202 Accepted + Location for a slow report export

"Download CSV" runs a 90-second warehouse query. Holding one request open that long trips gateway timeouts (the 504s from section 3). The status-code-native design: acknowledge immediately, poll for completion.

```ts
async function exportReport(params: ReportParams) {
  const res = await fetch("/api/reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (res.status !== 202) throw new ApiError(res, await res.json().catch(() => null));
  const statusUrl = res.headers.get("Location");
  while (true) {
    await sleep(2000);
    const poll = await fetch(statusUrl);
    if (poll.status === 200) return poll.json();   // { downloadUrl }
    if (poll.status !== 202) throw new ApiError(poll, null);
  }
}
```

Status codes working as *protocol*, not decoration: 202 = accepted-not-done, `Location` = where to look, 200 = ready — and no request ever outlives the load balancer's patience.

### Idempotency keys to make checkout POSTs retriable

Section 2 says a timed-out POST can't be legally retried. Production checkouts retry anyway — by attaching a client-generated key so the server dedupes duplicate executions.

```ts
const idempotencyKey = crypto.randomUUID(); // minted once per checkout attempt, reused across retries

async function placeOrder(cart: Cart) {
  return apiFetch("/api/orders", {
    method: "POST",
    headers: { "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(cart),
  });
}
```

This works because idempotency is a semantic property, not a method spelling: the key turns N identical POSTs into one server-side effect, making retry-on-timeout legal for the one method where it's normally forbidden (the Stripe-popularized header).

> [!tip]
> Mint the key when the user *intends* the action (checkout mount / first click), not per request — a fresh key per retry means the dedupe never fires.

## 7. Interview Answer

Short answer:

> HTTP is stateless request/response. Methods carry semantics — safe (GET) and idempotent (GET/PUT/DELETE) properties decide what's cacheable and what's automatically retriable. Status codes are code paths: 4xx means the client must change something (don't blind-retry), 5xx means the server failed (retry with backoff), with special handling for 401, 429, and 304.

Deeper answer:

> HTTP/1.1's one-request-per-connection limit created bundling and sharding; HTTP/2's multiplexing over one connection removed connection scarcity but kept TCP head-of-line blocking; HTTP/3 on QUIC removes that too, plus faster handshakes and connection migration. The modern frontend consequence: request count matters far less than request *dependencies* — waterfalls are the performance killer, and bundling is now about cache granularity.

## 8. Practice

1. <details><summary>Why is it legal for your wrapper to auto-retry a timed-out DELETE but not a timed-out POST?</summary>DELETE is idempotent: deleting the same resource twice converges to the same state, so a duplicate execution is harmless. POST is not — the timed-out attempt may have succeeded server-side, so a retry can create a second order/charge. To retry POST safely, send an idempotency key so the server dedupes.</details>

2. <details><summary>User clicks "export", the API returns 302 → the browser follows it and the download works, but your fetch-based code gets a CORS error on the redirect target. What's happening and what are your options?</summary>fetch follows redirects transparently (`redirect: "follow"` default), and the redirect target (e.g., a signed S3 URL on another origin) must *itself* satisfy CORS for a JS-read response. Options: have the API return the URL in a JSON body and navigate/`<a download>` to it (browser navigation isn't CORS-restricted), make the target send CORS headers, or proxy the file through your origin. Also note 307/308 preserve method+body; 302 may downgrade POST→GET.</details>

3. <details><summary>Your dashboard fires 40 small parallel GETs. A tech lead says "bundle them into one endpoint, HTTP requests are expensive." Evaluate under HTTP/2.</summary>Under HTTP/2 all 40 ride one connection as multiplexed streams — per-request cost is small (headers compressed, no new connections). If they're truly parallel, latency ≈ the slowest response either way. Batching still helps when: server-side work can be joined (one DB query), payloads share data, or you must support HTTP/1.1 clients/proxies. It hurts cache granularity (one change invalidates the batch) and error isolation. Measure before bundling.</details>

4. <details><summary>401 vs 403 vs 404 for "you can't see this document" — argue the choices.</summary>401: not authenticated — send to login/refresh; the request might succeed after auth. 403: authenticated but not allowed — show "no access", don't retry. 404 for a document that exists but is forbidden is a deliberate *information-hiding* choice (don't reveal existence — GitHub private repos do this); the cost is confused debugging and support. Pick per resource sensitivity and document it.</details>

## Related Notes

- [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]
- [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]
- [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[01 - Roadmap|Roadmap]]
