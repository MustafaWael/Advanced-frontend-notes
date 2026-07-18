---
tags: [browser, networking, rendering]
module: "26 - How the Web Works"
priority: must-know
status: not-started
aliases: [What happens when you type a URL, Critical Rendering Path Overview]
---

# From URL to Pixels

## Maturity Target

- Priority: #must-know
- Study time: 45 minutes
- Interview signal: Narrate "what happens when you type a URL and press Enter" at any zoom level — 30 seconds or 10 minutes — without hand-waving any stage.
- Production signal: When something is slow, you can name *which stage* is slow (DNS? TTFB? render-blocking CSS? long task?) instead of guessing.
- Dependencies: [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]

## Source Anchors

- [MDN - Populating the page: how browsers work](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work)
- [web.dev - Critical rendering path](https://web.dev/learn/performance/understanding-the-critical-path)
- [Chrome - Inside look at modern web browsers](https://developer.chrome.com/blog/inside-browser-part1)

## 1. Concept

Simple version: the browser turns a name into an address, opens a secure connection, downloads documents, builds trees out of them, and turns those trees into pixels — streaming and in parallel wherever it can.

The accurate pipeline, with real names:

1. **URL parsing** — scheme, host, port, path, query, fragment. The browser checks its own caches first (HSTS list, service worker, HTTP cache) — a fully cached page may skip the network entirely.
2. **DNS resolution** — hostname → IP, through a chain of caches ([[26 - How the Web Works/02 - DNS and Domains|DNS and Domains]]).
3. **Connection** — TCP handshake + TLS handshake (or QUIC, which merges them) ([[26 - How the Web Works/03 - Connection Layer|Connection Layer]]).
4. **Request/response** — HTTP request goes out; the response streams back. Time-to-first-byte (TTFB) measures server + network latency here.
5. **Parsing** — the HTML parser builds the **DOM** incrementally as bytes arrive. `<link rel="stylesheet">` starts CSS download; CSS parses into the **CSSOM**. Classic `<script>` tags *pause* the HTML parser ([[26 - How the Web Works/07 - HTML CSS JS Roles|HTML CSS JS Roles]]). The **preload scanner** races ahead of the paused parser to discover and fetch resources early.
6. **Style → Layout → Paint → Composite** — DOM + CSSOM combine into the render tree; layout computes geometry; paint produces draw commands; the compositor assembles layers on the GPU. Detailed in [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]].
7. **JS execution** — the engine ([[26 - How the Web Works/06 - How V8 Runs Your Code|How V8 Runs Your Code]]) runs scripts, which may mutate the DOM and re-trigger stage 6. For a React app, this is where hydration happens.

The key mental model: it's a **stream**, not a sequence. The parser doesn't wait for the full HTML; paint doesn't wait for every image. Render-blocking resources (CSS, sync scripts) are the exceptions that create waterfalls — and most page-load performance work is about removing those exceptions.

## 2. Why It Matters

- This is one of the most common screening questions for frontend roles, and depth of answer strongly signals seniority.
- Every performance metric maps to a stage: TTFB → stages 2–4, FCP/LCP → stages 5–6, INP → stage 7 and beyond. You can't fix what you can't locate.
- Architecture decisions (SSR vs CSR, code splitting, critical CSS) are all interventions at specific stages of this pipeline.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

```html
<!-- Buggy: marketing "just added one script" and LCP jumped 1.2s -->
<head>
  <link rel="stylesheet" href="/styles.css" />
  <script src="https://third-party.example/analytics.js"></script>
  <link rel="stylesheet" href="/theme.css" />
</head>
```

Trace: the classic `<script>` blocks the HTML parser until it downloads *and* executes. Worse — because a script might read computed styles, the browser also waits for `/styles.css` (all CSS above it) before executing. One tag serialized the whole head: CSS → script download → script execution → resume parsing. Nothing below the script even gets parsed until it finishes.

```html
<!-- Fix -->
<head>
  <link rel="stylesheet" href="/styles.css" />
  <link rel="stylesheet" href="/theme.css" />
  <script src="https://third-party.example/analytics.js" defer></script>
</head>
```

`defer` downloads in parallel and executes after parsing, in order. `async` would also unblock the parser but executes whenever the download completes — fine for analytics that don't depend on DOM order.

Tradeoffs: deferred scripts run later, so anything the page *needs* immediately (e.g., a theme-flash preventer, consent gates) may need to stay inline and tiny. Every deferral trades earlier paint for later interactivity of that script's feature.

## 4. Interview Answer

Short answer:

> The browser parses the URL, resolves the domain via DNS through several cache layers, opens a TCP+TLS (or QUIC) connection, and sends the HTTP request. The HTML response is parsed incrementally into the DOM; CSS becomes the CSSOM; the two form the render tree, which goes through layout, paint, and compositing to reach the screen. JS executes on the main thread and can mutate the DOM, re-triggering rendering. The important nuance is that it's all streamed and parallelized — render-blocking CSS and synchronous scripts are what create waterfalls.

Deeper answer:

> If asked to go deeper, pick a stage: DNS resolution order (browser cache → OS → resolver → root/TLD/authoritative), why QUIC removes head-of-line blocking, how the preload scanner mitigates parser blocking, why CSSOM construction blocks script execution, or how the compositor thread lets scrolling stay smooth while the main thread is busy. Then connect it to metrics: TTFB measures the network half, LCP the rendering half, INP the JS half.

## 5. Practice

1. <details><summary>Why can a page start rendering before the HTML has finished downloading?</summary>The HTML parser is incremental — it builds the DOM as bytes stream in, and the browser can run style/layout/paint on the partial tree. Only render-blocking resources (CSS in head, sync scripts) pause this.</details>
2. <details><summary>A page has fast TTFB but slow first paint. Which stages do you investigate, and with what?</summary>Stages 5–6: render-blocking CSS, sync scripts, huge DOM. Use DevTools Performance panel — look at the gap between first byte and FCP, check the "Render blocking" indicators in the Network panel.</details>
3. <details><summary>Where does a service worker sit in this pipeline, and what can it short-circuit?</summary>Between URL parsing and DNS/network — its fetch handler intercepts the request and can respond from Cache Storage, skipping DNS, connection, and server entirely. That's why SW-cached apps load offline.</details>

## Related Notes

- [[26 - How the Web Works/02 - DNS and Domains|DNS and Domains]]
- [[26 - How the Web Works/03 - Connection Layer|Connection Layer]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]
- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[19 - DOM and Browser APIs/10 - Service Workers and PWA Basics|Service Workers and PWA Basics]]
