---
tags: [browser, web-platform, checklist]
module: "26 - How the Web Works"
priority: must-know
status: not-started
---

# How the Web Works Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, predict, debug, and refactor without looking.

## Source Anchors

- [MDN - How browsers work](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work)
- [Chrome - Inside look at modern web browsers](https://developer.chrome.com/blog/inside-browser-part1)
- [V8 blog](https://v8.dev/blog)

## URL to Pixels

- [ ] I can narrate the full journey — URL parse, DNS, connection, request, parse, style, layout, paint, composite — and zoom into any stage on request.
- [ ] I can map each stage to the metric it moves: TTFB, FCP, LCP, INP.
- [ ] I can explain what the preload scanner does and why streaming/incremental parsing matters.

## DNS and Domains

- [ ] I can trace a cold lookup: browser cache → OS → recursive resolver → root → TLD → authoritative.
- [ ] I can explain A, AAAA, CNAME, TXT, NS records and why hosts hand out CNAME targets.
- [ ] I can plan a migration around TTLs and explain why DNS changes are eventually consistent.
- [ ] I can say when `dns-prefetch` vs `preconnect` pays off and what preconnect costs.

## Connection Layer

- [ ] I can count the round trips: TCP handshake, TLS 1.3, and QUIC's merged handshake.
- [ ] I can explain HTTP/1.1's per-connection serialization and the old workarounds (bundling, sharding).
- [ ] I can explain H2 multiplexing and why TCP head-of-line blocking survives it.
- [ ] I can explain what H3/QUIC fixes (independent streams, 1-RTT/0-RTT, connection migration).
- [ ] I can derive the modern defaults: consolidate origins, moderate code splitting, preconnect third parties.

## Browser Architecture

- [ ] I can draw the process model: browser, network, GPU, renderer processes — and what runs in each.
- [ ] I can explain the renderer sandbox and why file/network access goes through IPC.
- [ ] I can explain site isolation and its post-Spectre rationale (COOP/COEP, SharedArrayBuffer).
- [ ] I can distinguish main thread vs compositor thread and explain smooth-scroll-during-jank.

## Engines

- [ ] I can produce the two-column map: Blink/WebKit/Gecko vs V8/JSC/SpiderMonkey, and who embeds which.
- [ ] I can explain why `document` and `setTimeout` are not JS-engine features.
- [ ] I can triage a cross-browser bug to rendering engine vs JS engine vs missing runtime API.
- [ ] I can describe V8's tiers — Ignition, Sparkplug, Maglev, TurboFan — and the role of type feedback.
- [ ] I can explain hidden classes, inline caches, mono/poly/megamorphic sites, and deoptimization.
- [ ] I can name the practical rules that follow: stable shapes, no `delete` on hot objects, consistent types.

## HTML, CSS, JS

- [ ] I can define each layer by ownership and then give the blocking model: CSS render-blocks and blocks scripts; classic scripts parser-block.
- [ ] I can choose between `defer`, `async`, and `type="module"` and predict execution order.
- [ ] I can explain a fast-connection-only null-element crash as an async race.

## Exit Test

- [ ] Answer "what happens when you type a URL?" three times: in 30 seconds, in 3 minutes, and zoomed into whichever stage an interviewer picks.
- [ ] Given a slow page, name which pipeline stage you'd investigate first for: high TTFB, slow FCP, slow INP.
- [ ] Explain to a junior why their analytics snippet broke the page when moved above the stylesheet.
- [ ] Sketch why a 100k-row loop got 20× slower after rows started coming from three different endpoints.

## Related Notes

- [[26 - How the Web Works/00 - How the Web Works MOC|How the Web Works MOC]]
- [[19 - DOM and Browser APIs/12 - DOM and Browser APIs Checklist|DOM and Browser APIs Checklist]]
- [[20 - Network and Security/09 - Network and Security Checklist|Network and Security Checklist]]
- [[01 - Roadmap|Roadmap]]
