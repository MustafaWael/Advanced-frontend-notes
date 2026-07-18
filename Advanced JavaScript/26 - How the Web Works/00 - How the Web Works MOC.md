---
tags: [browser, web-platform, moc]
module: "26 - How the Web Works"
priority: must-know
status: not-started
---

# How the Web Works MOC

This module answers "how does the frontend actually work, from the ground up?" — the journey from a typed URL to painted pixels. It grounds everything else in the vault: DNS and connections explain *why* performance work matters, browser architecture explains *where* your JS actually runs, and the engines landscape explains *why* "the browser" is not one thing. After it, "walk me through what happens when you type a URL" — a classic screening question — becomes a story you can tell at any depth the interviewer wants.

## Prerequisites

- [[02 - JavaScript Runtime Foundations/00 - JavaScript Runtime Foundations MOC|JavaScript Runtime Foundations MOC]] — engine vs runtime distinction is assumed.
- [[20 - Network and Security/01 - HTTP Essentials for Frontend|HTTP Essentials for Frontend]] — HTTP semantics; this module covers what happens *below* HTTP.

## Reading Order

1. [[26 - How the Web Works/01 - From URL to Pixels|From URL to Pixels]] — the full journey, hub for everything below.
2. [[26 - How the Web Works/02 - DNS and Domains|DNS and Domains]] — how a name becomes an IP, and why frontend devs should care.
3. [[26 - How the Web Works/03 - Connection Layer|Connection Layer]] — TCP vs QUIC, TLS, HTTP/1.1 vs 2 vs 3 consequences.
4. [[26 - How the Web Works/04 - Browser Architecture|Browser Architecture]] — the multi-process model and sandboxing.
5. [[26 - How the Web Works/05 - Engines Landscape|Engines Landscape]] — JS engines vs rendering engines, correctly separated.
6. [[26 - How the Web Works/06 - How V8 Runs Your Code|How V8 Runs Your Code]] — parsing, interpretation, JIT, deopts.
7. [[26 - How the Web Works/07 - HTML CSS JS Roles|HTML CSS JS Roles]] — what each layer owns, and how scripts block parsing.
8. [[26 - How the Web Works/08 - How the Web Works Checklist|How the Web Works Checklist]] — active self-test.

## You're Done When

- [ ] I can narrate the URL-to-pixels journey end to end, zooming into any stage on request.
- [ ] I can trace DNS resolution through its cache layers and explain TTL tradeoffs.
- [ ] I can explain what HTTP/2 and HTTP/3 changed and what that means for bundling strategy.
- [ ] I can draw the browser's process model and explain what sandboxing buys.
- [ ] I can separate JS engines from rendering engines and name who ships what.
- [ ] I can describe V8's pipeline (parse → bytecode → JIT) and what makes code deoptimize.
- [ ] I can explain parser blocking and choose between `defer`, `async`, and `type="module"` deliberately.

## Related Notes

- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]] — the rendering half of the journey lives there.
- [[20 - Network and Security/02 - HTTP Caching|HTTP Caching]]
- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[01 - Roadmap|Roadmap]]
