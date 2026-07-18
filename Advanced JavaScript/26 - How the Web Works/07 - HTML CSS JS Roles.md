---
tags: [html, css, javascript, web-platform]
module: "26 - How the Web Works"
priority: must-know
status: not-started
aliases: [What is HTML CSS JS, Script loading strategies]
---

# HTML CSS JS Roles

## Maturity Target

- Priority: #must-know
- Study time: 30 minutes
- Interview signal: Define each layer by what it *owns* (structure/presentation/behavior), then explain the loading interactions: parser blocking, render blocking, and `defer` vs `async` vs `type="module"` — mechanically, not as rules of thumb.
- Production signal: You place every script tag deliberately and can explain a FOUC or a "script ran before DOM existed" bug from first principles.
- Dependencies: [[26 - How the Web Works/01 - From URL to Pixels|From URL to Pixels]]

## Source Anchors

- [MDN - script: defer and async](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/script)
- [web.dev - Render-blocking resources](https://web.dev/learn/performance/optimize-resource-loading)
- [HTML Living Standard - Scripting](https://html.spec.whatwg.org/multipage/scripting.html)

## 1. Concept

Simple version: HTML declares *what things are* (structure + semantics), CSS declares *how they look* (presentation), JS defines *how they behave* (logic). The web's resilience comes from the layering: HTML without CSS still reads; HTML+CSS without JS still renders.

The accurate mechanism is in how they *load and block each other*:

- **HTML** parses incrementally into the DOM. The parser is error-tolerant by spec — invalid HTML never throws; it's repaired deterministically (which is why `<p><div>` reshuffles your tree silently).
- **CSS is render-blocking, not parser-blocking**: HTML parsing continues past a `<link rel="stylesheet">`, but *painting* waits until the CSSOM is ready — otherwise users would see a flash of unstyled content (FOUC).
- **Classic `<script>` is parser-blocking**: the parser stops, the script downloads (if external) and executes, then parsing resumes. Why? Because `document.write` and DOM queries mean the script may depend on — or alter — the parse in progress.
- **CSS blocks scripts**: a script may read `getComputedStyle`, so its execution additionally waits for any pending stylesheets above it. CSS → JS → parsing: that's the full blocking chain.

The escape hatches:

```html
<script src="a.js"></script>                <!-- blocks parser; executes in place -->
<script src="b.js" defer></script>          <!-- parallel download; runs after parse, IN ORDER -->
<script src="c.js" async></script>          <!-- parallel download; runs ON ARRIVAL, any order, can interrupt parsing -->
<script type="module" src="d.js"></script>  <!-- deferred by default; strict mode; own scope; CORS-fetched -->
```

- `defer`: ordered, post-parse, before `DOMContentLoaded` — the right default for app code.
- `async`: unordered, ASAP — only for independent scripts (analytics) with no DOM-order dependencies.
- `type="module"`: defer semantics plus ESM (imports, top-level await, strict mode, once-only execution) — see [[10 - Modules/01 - ES Modules|ES Modules]].

## 2. Why It Matters

- "What is HTML/CSS/JS?" sounds junior, but interviewers use it to check whether you answer with the *loading model* (mature) or just "markup, styles, scripts" (junior).
- Every FOUC, every `null` from `querySelector`, every "works locally, breaks on slow 3G" script bug is this note.
- Progressive enhancement — the design philosophy the layering enables — is the intellectual ancestor of SSR-first frameworks: HTML that works, enhanced by JS ([[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]).

## 3. Real Frontend Example: Bug → Fix → Tradeoff

```html
<!-- Buggy: intermittent "Cannot read properties of null" — only on fast connections! -->
<head>
  <script src="/menu.js" async></script>
</head>
<body>
  <nav id="menu">…</nav>
</body>
```

```ts
// menu.js
document.getElementById('menu').addEventListener('click', toggle);
```

Trace: `async` executes on arrival. On slow connections the script lands after `<nav>` is parsed — works. On fast connections (or from cache) it can execute while the parser is still in `<head>` — `getElementById('menu')` returns `null`. The bug inverts intuition: *better* network, *more* crashes. That's the signature of an execution-order race.

```html
<!-- Fix -->
<script src="/menu.js" defer></script>
```

`defer` guarantees execution after the DOM is complete, in tag order. Alternative fixes — wrapping in `DOMContentLoaded` or moving the tag to end-of-body — also work but either add boilerplate or delay the *download*; `defer` gets parallel download and safe timing.

Tradeoffs: `defer` means the script's behavior attaches later than inline/blocking execution — for above-the-fold interactivity-critical code, that gap is real (and is exactly the hydration-gap problem frameworks wrestle with, [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]).

> [!warning] Footgun: `async` scripts have no order guarantee *among themselves*. Two async scripts where B depends on A is a race you'll lose intermittently. Dependencies ⇒ `defer` (ordered) or modules (explicit `import` graph).

## 4. Interview Answer

Short answer:

> HTML is structure and semantics, CSS is presentation, JS is behavior — but the mature version is the loading model. HTML parses incrementally; CSS doesn't stop parsing but blocks rendering, and it blocks script execution because scripts can read computed styles; classic scripts block the parser itself. `defer` downloads in parallel and runs in order after parsing; `async` runs on arrival in any order; `type="module"` behaves like defer plus ESM semantics.

Deeper answer:

> Practical decision rules: app code → `defer` or modules; independent third-party beacons → `async`; render-critical inline snippets (theme detection) → inline and tiny, before CSS if they must not flash. The preload scanner mitigates parser blocking by fetching ahead, but execution order still rules. And the layering has an architectural moral: the more you keep in HTML/CSS (server-rendered structure, CSS-driven interactions), the less you depend on JS arriving and executing — the core argument for progressive enhancement and SSR-first frameworks.

## 5. Practice

1. <details><summary>Why does CSS block script execution but not HTML parsing?</summary>Parsing past a stylesheet is safe — the DOM doesn't depend on CSS. But a script might call getComputedStyle or read layout, which requires an up-to-date CSSOM; running it early could observe wrong styles. So the browser stalls script execution on pending stylesheets above it, and since classic scripts block parsing, slow CSS transitively stalls parsing at the script tag.</details>
2. <details><summary>A script works from cold cache and crashes from warm cache. What class of bug is this and why?</summary>An async-timing race: cached async scripts execute almost immediately, possibly before the DOM nodes they query exist. Cold cache delays execution until after parsing has passed those nodes. Fix with defer/module or event-based readiness, never with timing hacks.</details>
3. <details><summary>Why does `type="module"` not need `defer`?</summary>Module scripts are deferred by spec — fetched in parallel (with CORS), executed after parsing, in graph order, exactly once per specifier. Adding defer is a no-op; async on a module means "execute when the graph is ready, don't wait for parse."</details>

## Related Notes

- [[26 - How the Web Works/01 - From URL to Pixels|From URL to Pixels]]
- [[10 - Modules/01 - ES Modules|ES Modules]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]
- [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]
