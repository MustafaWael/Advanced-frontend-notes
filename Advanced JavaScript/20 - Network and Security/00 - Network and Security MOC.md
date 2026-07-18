---
tags: [javascript, moc, network, security]
module: "20 - Network and Security"
priority: must-know
status: not-started
---

# Network and Security MOC

This module is the senior-signal module: how the frontend talks to servers and how it stays safe doing so. HTTP semantics and caching decide correctness and performance; CORS, cookies, XSS, CSRF, CSP, prototype pollution, and supply-chain hygiene decide whether your app can be turned against your users. It sits logically after Error Handling — once you can model failures, you can model *adversarial* failures. After it, the security questions in senior interviews ("where do you store the token, and what happens under XSS?") have real answers, not slogans.

## Prerequisites

- [[19 - DOM and Browser APIs/00 - DOM and Browser APIs MOC|DOM and Browser APIs MOC]] — fetch, storage, and the DOM sinks are used throughout.
- [[11 - Error Handling/00 - Error Handling MOC|Error Handling MOC]] — status-code handling and retry logic build on error modeling.

## Reading Order

1. [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]] — methods, status codes, headers, HTTP versions.
2. [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]] — Cache-Control, ETag, revalidation, deploy outages.
3. [[20 - Network and Security/03 - CORS Correctly Explained|CORS Correctly Explained]] — same-origin policy, preflight, and the myths.
4. [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]] — session vs JWT, attributes, where tokens live.
5. [[20 - Network and Security/05 - XSS|XSS]] — reflected/stored/DOM, what React escapes, sanitization.
6. [[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]] — auto-attached cookies, SameSite, containment via CSP.
7. [[20 - Network and Security/07 - Prototype Pollution and Supply-Chain Basics|Prototype Pollution and Supply-Chain Basics]] — `__proto__` corruption and npm trust.
8. [[20 - Network and Security/08 - WebSockets SSE and Polling|WebSockets, SSE, and Polling]] — choosing a realtime strategy.
9. [[20 - Network and Security/09 - Network and Security Checklist|Network and Security Checklist]] — active self-test.

## You're Done When

- [ ] I can turn status codes into deliberate code paths and explain HTTP/1.1 vs 2 vs 3 consequences.
- [ ] I can write correct Cache-Control per resource and debug staleness through every cache layer.
- [ ] I can explain that CORS is a browser-enforced, server-granted read permission that protects the user, and read a preflight.
- [ ] I can compare session vs JWT honestly and design the split-token auth pattern.
- [ ] I can classify XSS, state what React does and doesn't escape, and sanitize rich text safely.
- [ ] I can explain CSRF from cookie mechanics and choose defenses that match the auth model.
- [ ] I can write a basic strict CSP and roll it out report-only first.
- [ ] I can explain prototype pollution and resist it, and name concrete supply-chain mitigations.
- [ ] I can pick polling vs SSE vs WebSocket from requirements and defend the reliability tradeoffs.

## Related Notes

- [[19 - DOM and Browser APIs/07 - fetch Deep Dive|fetch Deep Dive]]
- [[22 - Next.js Deep Dive/00 - Next.js Deep Dive MOC|Next.js Deep Dive MOC]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[01 - Roadmap|Roadmap]]
