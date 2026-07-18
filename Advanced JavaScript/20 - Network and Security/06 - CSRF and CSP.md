---
tags: [javascript, security, csrf, csp]
module: "20 - Network and Security"
priority: must-know
status: not-started
aliases: [CSRF, CSP, Content Security Policy]
---

# CSRF and CSP

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can explain why CSRF exists (auto-attached cookies), why SameSite changed the landscape, and read/write a basic CSP.
- Production signal: you pick CSRF defenses that match your auth model, and you can debug "CSP blocked my inline script / third-party widget".
- Dependencies: [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]], [[20 - Network and Security/05 - XSS|XSS]]

## Source Anchors

- [OWASP - CSRF](https://owasp.org/www-community/attacks/csrf)
- [OWASP - CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [MDN - Content Security Policy (CSP)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP)
- [web.dev - Strict CSP](https://web.dev/articles/strict-csp)
- [MDN - SameSite cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie/SameSite)

## 1. CSRF — The Core Idea

Cross-Site Request Forgery abuses the browser's habit of **attaching cookies automatically** ([[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]). If auth is a cookie, then a request to your site carries the user's session *regardless of who initiated it* — including a form or image on an attacker's page.

```html
<!-- On evil.com, while the victim is logged into bank.com -->
<form action="https://bank.com/transfer" method="POST">
  <input name="to" value="attacker"><input name="amount" value="5000">
</form>
<script>document.forms[0].submit()</script>
```

The victim never clicks anything meaningful; the browser sends the POST *with bank.com's session cookie*. CSRF needs **no XSS and no token theft** — it never reads the response ([[20 - Network and Security/03 - CORS Correctly Explained|CORS/SOP hides the response but doesn't stop the send]]), it only triggers a *side effect*. That's why it targets state-changing endpoints.

Crucial contrast: **Bearer-token auth in an `Authorization` header is not CSRF-able** — the attacker's page can't set that header on a cross-site form/navigation, and cookies aren't involved. CSRF is fundamentally a *cookie-auth* problem. This single fact drives the defense choice.

## 2. CSRF Defenses

- **SameSite cookies** (`Lax` is the modern default): the cookie isn't sent on cross-site POSTs/subrequests, neutering the classic attack for most flows. `Lax` still sends on top-level GET navigations — so GET must never mutate (ties back to [[20 - Network and Security/01 - HTTP Essentials for Frontend|method safety]]), and `Strict` breaks inbound links (arrive logged-out). SameSite is strong but not a complete standalone defense (same-site subdomains, older clients, GET side effects).
- **Synchronizer token**: server issues a random token bound to the session; state-changing requests must echo it in a header/hidden field; attacker's cross-site page can't read it (SOP). The traditional gold standard.
- **Double-submit cookie**: token in both a cookie and a request header; server checks they match — stateless, common in SPAs, but needs care with subdomains (a same-site subdomain can set cookies).
- **Origin/Referer check**: reject state changes whose `Origin` isn't your site — cheap defense-in-depth.

> [!tip] Match the defense to the auth model
> Cookie/session auth → SameSite=Lax **plus** CSRF tokens for mutations (frameworks like Django, Rails, Next Server Actions bake this in). Token-in-Authorization-header auth → CSRF is largely a non-issue by construction, but you've traded it for XSS token-theft exposure. There's no free lunch — you pick *which* attack surface, then defend it.

## 3. CSP — The Idea

Content Security Policy is a response header (or meta tag) declaring which sources the browser may load and execute. It's a **containment** layer: it assumes something might go wrong (an XSS payload, a compromised dependency) and limits the damage.

```text
Content-Security-Policy:
  default-src 'self';
  script-src 'self' https://cdn.trusted.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.acme.com;
  frame-ancestors 'none';
  base-uri 'self';
  report-uri /csp-report
```

What it buys against XSS: with `script-src 'self'` (no `'unsafe-inline'`), an injected `<script>…</script>` or `onerror=` handler simply **won't execute** — the sanitizer bypass from [[20 - Network and Security/05 - XSS|XSS]] becomes inert. `connect-src` also limits exfiltration destinations, and `frame-ancestors 'none'` replaces `X-Frame-Options` for clickjacking.

## 4. CSP Done Right vs Done Painfully

The naive allowlist CSP (`script-src 'self' https://a.com https://b.com …`) is famously weak: one allowlisted host with an open JSONP endpoint or a hosted-library CDN defeats it, and maintaining the list is misery. The modern recommendation is a **strict, nonce/hash-based** policy:

```text
script-src 'nonce-{random-per-response}' 'strict-dynamic';
```

Each `<script>` carries the matching `nonce`; `strict-dynamic` lets those trusted scripts load their own dependencies, so you don't enumerate CDNs. `'strict-dynamic'` is what makes strict CSP practical in framework apps. Next.js supports per-request nonces for exactly this.

> [!warning] unsafe-inline defeats the point for scripts
> `script-src 'unsafe-inline'` re-permits injected inline scripts — it hands XSS back its primary execution path. Inline *styles* are lower-risk and sometimes pragmatically allowed, but inline *scripts* should use nonces/hashes. Adding `'unsafe-inline'` "to make the errors go away" is the single most common way teams neuter their own CSP.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: you ship CSP after an XSS scare; the app half-breaks and analytics dies.

Buggy first attempt (enforced immediately):

```text
Content-Security-Policy: default-src 'self'
```

Traced breakage: inline `<script>window.dataLayer=…</script>` blocked (analytics gone), Google Tag Manager (`https://www.googletagmanager.com`) blocked, inline event handlers in legacy pages dead, `connect-src` defaulting to `'self'` blocks the third-party API and Sentry, styled-components/emotion inject `<style>` at runtime → blocked. Users hit a subtly broken app and you're reverting under pressure.

Production-safe rollout:

```text
# 1. Ship in report-only first — nothing breaks, violations are collected:
Content-Security-Policy-Report-Only: default-src 'self'; script-src 'nonce-{X}' 'strict-dynamic'; connect-src 'self' https://api.acme.com https://o123.ingest.sentry.io; report-uri /csp-report

# 2. Fix real violations (nonce your scripts, whitelist required connect-src, move inline handlers to addEventListener).
# 3. Promote to enforcing Content-Security-Policy once the report stream is clean.
```

Tradeoffs: nonces require server-rendered `<script>` tags to receive a per-request value — trivial in Next.js/SSR frameworks, awkward in a purely static SPA (which often falls back to hashes or a weaker allowlist). Report-Only generates noise from browser extensions injecting scripts (filter by `document-uri`/`source-file`). And CSP is *containment, not prevention* — it lowers XSS severity, it doesn't remove the need to sanitize. The honest framing for an interview: CSP is the seatbelt, sanitization is not crashing.

## Real-World Use Cases

### Link scanners "click" your GET mutations

An email contains `https://app.acme.com/api/items/42/approve` as a plain link. Corporate mail security (Outlook SafeLinks, Slack unfurlers) fetches every link to scan it — approving the item before any human opened the email. No attacker required.

```ts
// Never: state change on GET
app.get("/api/items/:id/approve", approveItem);

// Always: mutation behind a non-safe method, plus a section-2 defense
app.post("/api/items/:id/approve", requireCsrfToken, approveItem);
```

Two mechanisms converge: GET is *safe* by contract, so the ecosystem prefetches it freely ([[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials]]), and `SameSite=Lax` still attaches cookies on top-level GET navigations — a state-changing GET is both crawler-triggerable *and* CSRF-able even with modern cookie defaults.

### Server Actions: where Next.js already does CSRF for you

A team ports a cookie-authed app to Server Actions and asks "where do we add the CSRF token?" Mostly: you don't.

```tsx
// app/settings/actions.ts
"use server";
export async function updateEmail(formData: FormData) {
  const session = await verifySession();   // authn/authz is still entirely your job
  await db.user.update(session.userId, { email: formData.get("email") });
}
```

Next.js rejects Server Action POSTs whose `Origin` doesn't match the `Host` — the Origin-check defense from section 2, built in — and actions are unguessable POST endpoints a cross-site form can't target.

> [!warning]
> The free protection covers Server Actions only. A cookie-authed mutation in a Route Handler (`app/api/*/route.ts`) gets none of it — that endpoint still needs SameSite plus a token or Origin check of your own.

### Rolling out a per-request CSP nonce in Next.js

After the report-only phase (section 5), enforcement needs every server-rendered `<script>` to carry a fresh nonce — a static value would let injected markup reuse it.

```ts
// middleware.ts
export function middleware(req: NextRequest) {
  const nonce = crypto.randomUUID();
  const csp = `script-src 'nonce-${nonce}' 'strict-dynamic'; object-src 'none'; base-uri 'self'`;
  const headers = new Headers(req.headers);
  headers.set("x-nonce", nonce);           // Next.js picks this up and nonces its own scripts
  const res = NextResponse.next({ request: { headers } });
  res.headers.set("Content-Security-Policy", csp);
  return res;
}
```

The section-4 model made concrete: nonce minted per response, framework scripts inherit trust via `'strict-dynamic'`, and an injected inline payload ([[20 - Network and Security/05 - XSS|XSS]]) fails the nonce check and never executes.

> [!warning]
> A per-request nonce forces dynamic rendering — the HTML can't be statically cached with a nonce baked in. Static-heavy sites use hash-based CSP for their known inline scripts instead.

## 6. Interview Answer

Short answer:

> CSRF exploits that browsers auto-attach cookies: an attacker's page triggers a state-changing request to your site carrying the victim's session, without reading the response. Defenses are SameSite cookies plus CSRF tokens (or Origin checks). It's a cookie-auth problem — Authorization-header tokens aren't CSRF-able because the attacker can't set that header cross-site.

Deeper answer:

> CSP is a containment header restricting which sources load and run. Against XSS, `script-src` without `'unsafe-inline'` stops injected scripts from executing and `connect-src` limits exfiltration. Allowlist CSPs are weak and hard to maintain; the modern approach is per-response nonces plus `'strict-dynamic'`, rolled out via Content-Security-Policy-Report-Only first so you fix violations before enforcing. CSP reduces XSS severity but doesn't replace sanitization — defense in depth.

## 7. Practice

1. <details><summary>Your SPA authenticates with a JWT in the Authorization header (no cookies). A PM asks "are we protected against CSRF?" Answer precisely.</summary>Effectively yes, by construction: CSRF relies on the browser auto-attaching an ambient cookie credential; an attacker's cross-site page cannot set a custom `Authorization` header on a form/navigation, and no auth cookie exists to ride along. But you've shifted the risk — the header token typically lives in JS-readable storage, so your primary exposure is now XSS token theft ([[20 - Network and Security/05 - XSS|XSS]]). Don't add CSRF tokens reflexively; do harden against XSS.</details>

2. <details><summary>Why must GET requests never change state, phrased in terms of SameSite=Lax?</summary>`Lax` (the default) still sends cookies on top-level cross-site GET navigations — clicking a link or an attacker's `window.location`/`<img>` to your GET endpoint arrives authenticated. So a state-changing GET is CSRF-able even under Lax. Keeping GET safe/idempotent ([[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP semantics]]) closes that hole; mutations go through POST/PUT/DELETE, which Lax withholds cross-site.</details>

3. <details><summary>After enabling CSP, a third-party chat widget stops loading and console shows "Refused to load script". Walk through diagnosis without just adding 'unsafe-inline'.</summary>Read the violation: it names the blocked directive and URL. The widget's script host isn't in `script-src`, and/or it injects further scripts. Fixes in order of preference: add the specific host to `script-src` (or rely on `'strict-dynamic'` if the loader script is nonce-trusted and pulls its own deps); if it needs `connect-src`/`frame-src`, add those hosts. Never blanket `'unsafe-inline'` — that re-enables injected inline scripts globally. If the widget demands inline eval, weigh whether it belongs on the page at all.</details>

4. <details><summary>Explain double-submit cookie CSRF protection and one subdomain pitfall.</summary>Server sends a random CSRF token in a (readable) cookie; the SPA copies it into a request header on mutations; the server rejects requests where cookie and header don't match. Stateless (no server store). Attacker can't read the cookie cross-origin to forge the header (SOP). Pitfall: a compromised or attacker-controlled *same-site subdomain* can set/overwrite the cookie on the parent domain, letting the attacker choose a value they also put in the header — restoring the attack. Mitigations: sign the token, bind it to the session, use the `__Host-` cookie prefix, and lock down subdomain trust.</details>

## Related Notes

- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
- [[20 - Network and Security/05 - XSS|XSS]]
- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]]
- [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]]
- [[01 - Roadmap|Roadmap]]
