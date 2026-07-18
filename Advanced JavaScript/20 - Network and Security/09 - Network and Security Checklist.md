---
tags: [javascript, network, security, checklist]
module: "20 - Network and Security"
priority: must-know
status: not-started
---

# Network and Security Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, predict, debug, and refactor without looking.

## Source Anchors

- [MDN - HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP)
- [OWASP - Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Fetch Living Standard](https://fetch.spec.whatwg.org/)
- [web.dev - Security](https://web.dev/explore/secure)

## HTTP

- [ ] I can classify methods by safe and idempotent and say which are auto-retriable.
- [ ] I can map status codes to code paths: retry 5xx/429, don't retry 4xx, special-case 401/304.
- [ ] I can explain HTTP/1.1 vs 2 vs 3 at overview level and the frontend consequences (bundling, sharding, waterfalls).
- [ ] I can debug a request from the Network tab: Content-Type, cookies, redirects, preflight.

## Caching

- [ ] I can explain freshness vs revalidation and trace a 304 exchange.
- [ ] I can distinguish `no-cache` from `no-store` correctly.
- [ ] I can write the canonical recipe: immutable hashed assets, revalidated HTML, private/no-store APIs.
- [ ] I can explain the fresh-HTML-references-deleted-chunk deploy outage and fix it.
- [ ] I can name the cache layer stack and debug "stale data" through it.

## CORS

- [ ] I can state what the same-origin policy blocks and that CORS is the server's opt-in, not the blocker.
- [ ] I can explain that CORS protects the user, not the server.
- [ ] I can say when a preflight happens and read an OPTIONS exchange.
- [ ] I can list the requirements for credentialed cross-origin requests.
- [ ] I can correct the common myths, including "it works in Postman so it's a frontend bug".

## Cookies and Auth

- [ ] I can explain every cookie attribute and what each defends against.
- [ ] I can compare sessions vs JWT on revocation, scale, and failure modes honestly.
- [ ] I can defend a token-storage choice and explain the XSS blast radius of each.
- [ ] I can design the memory-access-token + HttpOnly-refresh-cookie pattern with rotation.
- [ ] I can explain why client-decoded JWT claims must never be trusted for authorization.

## XSS

- [ ] I can distinguish reflected, stored, and DOM-based XSS.
- [ ] I can enumerate sources and sinks by name.
- [ ] I can state exactly what React escapes and what it does not.
- [ ] I can use `dangerouslySetInnerHTML` with sanitization and justify sanitize-late.
- [ ] I can explain the defense-in-depth stack: sanitize + CSP + Trusted Types + HttpOnly.

## CSRF and CSP

- [ ] I can explain why CSRF exists (auto-attached cookies) and why header-token auth isn't CSRF-able.
- [ ] I can list CSRF defenses and match them to the auth model.
- [ ] I can read and write a basic CSP and explain what `script-src` without `unsafe-inline` buys.
- [ ] I can explain nonce + strict-dynamic and the report-only rollout.

## Prototype Pollution and Supply Chain

- [ ] I can explain how `__proto__` in attacker data corrupts every object.
- [ ] I can write merge/set code that resists it, and choose `Object.create(null)`/`Map`.
- [ ] I can name supply-chain vectors: hijacked packages, typosquatting, dependency confusion, install scripts.
- [ ] I can explain lockfiles + `npm ci`, provenance, dependency minimization, and SRI.

## Realtime

- [ ] I can pick polling vs SSE vs WebSocket from direction, frequency, and infra.
- [ ] I can explain why SSE is an underrated one-way default (auto-reconnect, Last-Event-ID).
- [ ] I can list what WebSocket makes you build: reconnect, heartbeat, backpressure, auth, sticky state.

## Exit Test

- [ ] Given a "users see stale data" report, walk every cache layer to the root cause.
- [ ] Explain to a backend dev why their `Access-Control-Allow-Origin: *` + credentials config is both broken and dangerous.
- [ ] Redesign a localStorage-JWT auth into the split-token pattern and justify each change.
- [ ] Review a markdown-rendering component and identify the XSS sink and fix.
- [ ] Choose a realtime transport for three different features and defend each.

## Related Notes

- [[20 - Network and Security/00 - Network and Security MOC|Network and Security MOC]]
- [[19 - DOM and Browser APIs/12 - DOM and Browser APIs Checklist|DOM and Browser APIs Checklist]]
- [[01 - Roadmap|Roadmap]]
