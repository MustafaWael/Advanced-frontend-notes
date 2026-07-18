---
tags: [javascript, network, security, cors]
module: "20 - Network and Security"
priority: must-know
status: not-started
aliases: [CORS, Same-Origin Policy, Preflight]
---

# CORS Correctly Explained

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can state what the same-origin policy actually blocks, when a preflight happens, and correct the myths ("CORS protects the server", "just add the header client-side").
- Production signal: you can fix a CORS failure in minutes by reading the preflight exchange, and you know why the fix is never in frontend code.
- Dependencies: [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]], [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]

## Source Anchors

- [MDN - Cross-Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
- [Fetch Living Standard - CORS protocol](https://fetch.spec.whatwg.org/#http-cors-protocol)
- [MDN - Same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy)
- [web.dev - Cross-Origin Resource Sharing](https://web.dev/articles/cross-origin-resource-sharing)

## 1. Concept — Get the Direction Right

An **origin** is scheme + host + port: `https://app.example.com` ≠ `https://api.example.com` ≠ `http://app.example.com` ≠ `https://app.example.com:8443`.

The **same-origin policy (SOP)** is a *browser* rule: scripts on origin A may send requests anywhere, but may not **read** cross-origin responses (and may not touch cross-origin DOM/storage). **CORS is not the blocker — CORS is the unlock**: a protocol by which the *server* tells the browser "origin A may read my responses."

> [!warning] CORS protects the user, not the server
> The threat model: you're logged into `bank.com`; you visit `evil.com`; its JavaScript calls `bank.com/api/accounts` — and the browser (for legacy-mode requests) attaches your bank cookies. Without SOP, evil.com *reads your account data with your credentials*. SOP blocks the read; CORS lets bank.com opt in selectively. The server is not protected by CORS at all — curl, Postman, and any backend can call it freely with no Origin checks. Server protection is authn/authz; CSRF protection guards the *side effects* of unreadable requests ([[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]).

## 2. The Mechanism

**Simple requests** (roughly: GET/HEAD/POST with only safelisted headers, and Content-Type limited to `application/x-www-form-urlencoded`, `multipart/form-data`, or `text/plain`) are sent immediately with an `Origin` header. The browser then checks the response for `Access-Control-Allow-Origin`; absent/mismatched → the *response is hidden from JS* (`TypeError: Failed to fetch`) — note the request **did execute server-side**.

**Preflighted requests** — anything else (e.g. `Content-Type: application/json`, an `Authorization` header, PUT/DELETE) — trigger an automatic `OPTIONS` exchange first:

```text
OPTIONS /api/orders
Origin: https://app.example.com
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: authorization, content-type

← 204
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, PUT, DELETE
Access-Control-Allow-Headers: authorization, content-type
Access-Control-Max-Age: 86400      ← cache this verdict 24h (browser caps apply)
```

Only if the preflight passes is the real request sent. Preflight exists so that *new* kinds of requests (custom headers, JSON, unusual methods) can't hit legacy servers that predate CORS without an explicit opt-in — HTML forms could always POST urlencoded/multipart cross-origin, which is why exactly those shapes skip preflight.

**Credentials tier**: by default CORS requests omit cookies. `credentials: "include"` sends them, but then the server must reply `Access-Control-Allow-Credentials: true` **and** an explicit (non-`*`) `Access-Control-Allow-Origin`, and the cookie itself needs `SameSite=None; Secure` ([[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]).

## 3. Myths to Kill in Interviews

- **"Add the CORS header to my fetch call."** CORS response headers come from the *server*; nothing you write client-side grants access. (`mode: "cors"` just names the default.)
- **"CORS blocked my request."** For simple requests the request *ran*; the browser hid the response. A "CORS-blocked" POST may have already mutated data — which is why CSRF defenses must not rely on CORS visibility.
- **"`Access-Control-Allow-Origin: *` is insecure."** For public, credential-less APIs it's exactly right; `*` is refused by browsers *when credentials are included*, which is the dangerous combination.
- **"CORS applies to everything."** `<img>`, `<script src>`, CSS, form submissions all load cross-origin without CORS (that legacy is the CSRF attack surface). CORS governs *programmatic reads* — fetch/XHR, plus opt-in cases (`crossorigin` attr, fonts, ES modules).
- **"It works in Postman, so the API is fine — frontend bug."** Postman isn't a browser and has no SOP; the API is missing CORS config. The fix belongs to whoever owns the server.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: SPA on `https://app.acme.com`, API on `https://api.acme.com`. Login works; then `GET /api/me` returns 401. Meanwhile `PUT /api/profile` shows a redlined `OPTIONS ... 405` in devtools.

Diagnosis, traced:

1. Login `POST` (simple shape) succeeded and `Set-Cookie` came back — but subsequent fetches used default `credentials: "same-origin"` → cross-origin cookie **not sent** → 401.
2. The `PUT` with JSON triggered preflight; the API server has no `OPTIONS` route → 405 → browser never sends the PUT.

Buggy "fix" seen in the wild (server):

```js
res.setHeader("Access-Control-Allow-Origin", "*");
res.setHeader("Access-Control-Allow-Credentials", "true"); // browsers reject * + credentials
```

Production-safe fix (server, e.g. Express):

```js
const ALLOWED = new Set(["https://app.acme.com", "https://staging.acme.com"]);

app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (origin && ALLOWED.has(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin); // echo the specific origin
    res.setHeader("Vary", "Origin");                      // caches must key on Origin!
    res.setHeader("Access-Control-Allow-Credentials", "true");
  }
  if (req.method === "OPTIONS") {
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE");
    res.setHeader("Access-Control-Allow-Headers", "content-type,authorization");
    res.setHeader("Access-Control-Max-Age", "86400");
    return res.sendStatus(204);
  }
  next();
});
```

Client: `fetch(url, { credentials: "include" })`; cookie set as `SameSite=None; Secure; HttpOnly`.

Tradeoffs: an allow-*list* (never reflect arbitrary Origins with credentials — that's "CORS misconfiguration", a bounty classic) needs maintenance per environment; `Vary: Origin` reduces CDN cache efficiency; `Max-Age` caches preflight verdicts, so config changes lag for returning users. The architectural alternative: serve app and API same-origin (`/api` behind the same domain or a BFF proxy — the Next.js default posture) and CORS disappears along with preflight latency; the cost is coupling deploy/infrastructure.

## 5. Adjacent Mechanisms Worth Naming

`Access-Control-Expose-Headers` (JS can read only safelisted response headers otherwise); opaque responses (`mode: "no-cors"` — sendable, unreadable, mostly a trap); `crossorigin` attribute (needed on fonts, canvas-safe images, and for useful error details from CDN scripts); `postMessage` as the sanctioned cross-origin *window* channel; CORP/COEP/COOP (cross-origin isolation — required for `SharedArrayBuffer`, see [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Workers]]).

## Real-World Use Cases

### Classic interview trap: works in Postman, fails in the browser

The most-filed CORS ticket in existence: `POST https://api.partner.com/quotes` returns 200 in Postman, but in the app it's a red request and `TypeError: Failed to fetch`.

```js
const res = await fetch("https://api.partner.com/quotes", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ sku: "A-1042" }),
});
```

Tick-by-tick:

1. `Content-Type: application/json` is not a form-legacy type → the request is **not simple** → the browser sends an `OPTIONS` preflight first (section 2).
2. `api.partner.com` has no CORS config → no `Access-Control-Allow-Origin` on the preflight response.
3. Verdict fails → the browser never sends the POST at all; `fetch` rejects with the deliberately vague `TypeError`.
4. Postman has no same-origin policy — SOP is a *browser* rule protecting *users* (section 1) — so it happily shows 200.

The senior answer: nothing is wrong with the request or the API's logic; the API is missing CORS opt-in and the fix is server-side (or a proxy — below). Bonus point: had the request been a *simple* shape, it would have executed server-side and only the read would fail — which is [[20 - Network and Security/06 - CSRF and CSP|why CSRF defenses can't rely on CORS]].

### Adding an Authorization header wakes up preflights

A public weather API worked for months with plain GETs. The provider introduces API keys via `Authorization: Bearer …` — and suddenly every request is preceded by an `OPTIONS`, and some fail behind a corporate proxy that mishandles OPTIONS.

```js
// Before: simple request, no preflight
fetch("https://api.weather.io/v1/today?city=cairo");

// After: Authorization is not a safelisted header → preflight on every endpoint
fetch("https://api.weather.io/v1/today?city=cairo", {
  headers: { Authorization: `Bearer ${apiKey}` },
});
```

The preflight triggers to recite: non-simple methods (PUT/DELETE/PATCH), any non-safelisted header (`Authorization`, `X-Anything`), and `Content-Type` beyond the three form-legacy values.

> [!tip]
> If you control the server, `Access-Control-Max-Age: 86400` makes the preflight tax nearly free after the first hit. If you don't control it, the API key probably shouldn't be in the browser at all — proxy it (next case).

### Killing CORS in development with a Next.js rewrite

Local SPA on `localhost:3000`, backend on `localhost:8000` — different port = different origin (section 1), so dev is a parade of preflights and cookie problems that won't exist in production behind one domain.

```js
// next.config.mjs — the browser only ever talks to :3000
export default {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://localhost:8000/:path*" }];
  },
};
```

Rewrites make every request same-origin from the browser's point of view, so SOP never engages: no preflights, and cookies flow as first-party without `SameSite=None` gymnastics ([[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]). The same BFF/proxy posture carries to production — practice 4 has the tradeoffs.

## 6. Interview Answer

Short answer:

> The same-origin policy stops JavaScript from reading cross-origin responses; CORS is the server-side opt-out, not the blocker. Non-legacy requests get an automatic OPTIONS preflight asking permission for the method and headers; the response headers decide. And crucially, CORS protects the *user* — the server is equally reachable from curl; what's guarded is a malicious page riding the user's browser and credentials.

Deeper answer:

> Requests matching what HTML forms could always send skip preflight; JSON content types, Authorization headers, and non-simple methods trigger it, with `Access-Control-Max-Age` caching verdicts. Credentialed CORS requires include-mode on the client, `Allow-Credentials: true`, an explicit echoed origin plus `Vary: Origin`, and `SameSite=None; Secure` cookies. Reflecting arbitrary origins with credentials is a known vulnerability class, and "blocked" simple requests still execute server-side — that's why CSRF protection exists independently.

## 7. Practice

1. <details><summary>`fetch("https://api.other.com/data")` shows the request with a 200 in the Network tab, but your code got `TypeError: Failed to fetch`. Explain the discrepancy.</summary>The network layer completed the exchange (devtools sees it), but the response lacked a matching `Access-Control-Allow-Origin`, so the browser withheld it from JavaScript and rejected the promise. Key implication: the server processed the request; only the *read* was blocked. Fix is server-side CORS config.</details>

2. <details><summary>Why does changing `Content-Type` from `application/x-www-form-urlencoded` to `application/json` suddenly cause OPTIONS requests?</summary>Urlencoded is one of the three form-legacy content types that qualify as "simple" (forms could always send them cross-origin, so no new risk). JSON is not — it signals a modern programmatic request, so the browser preflights to get explicit server opt-in before sending. The OPTIONS is the preflight; the server must handle it or the real request never goes out.</details>

3. <details><summary>Security review finds: server echoes any `Origin` value into `Access-Control-Allow-Origin` and sets `Allow-Credentials: true`. Construct the attack.</summary>Any website can now read authenticated responses: victim (logged into the API via cookies) visits `evil.com`, which runs `fetch("https://api.victim.com/me", { credentials: "include" })`. The browser sends `Origin: https://evil.com`; the server reflects it with credentials allowed; the browser hands evil.com the response — full account data exfiltration. Fix: strict allowlist; never reflect with credentials.</details>

4. <details><summary>Team proposal: "avoid CORS entirely by proxying the third-party API through our own backend." Evaluate.</summary>Valid and common (BFF pattern; Next.js route handlers do this). Pros: no preflights (latency win), API keys stay server-side, response reshaping/caching, one origin policy. Cons: your backend becomes a hop for all that traffic (cost, latency to *your* server, availability coupling), you must forward/limit headers carefully, and SSRF risk if the proxied URL is user-influenced. For third-party APIs with secrets, proxying is usually *mandatory* anyway — the key must never ship to the browser.</details>

## Related Notes

- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]]
- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
- [[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]
- [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]
- [[01 - Roadmap|Roadmap]]
