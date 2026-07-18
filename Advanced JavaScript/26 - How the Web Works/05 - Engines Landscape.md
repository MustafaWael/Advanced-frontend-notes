---
tags: [browser, engines, javascript]
module: "26 - How the Web Works"
priority: must-know
status: not-started
aliases: [JS engines vs rendering engines, Browser engines]
---

# Engines Landscape

## Maturity Target

- Priority: #must-know
- Study time: 25 minutes
- Interview signal: Cleanly separate JS engines from rendering engines, name who ships what, and explain why "Chrome and Edge behave the same but Safari differs" mechanically.
- Production signal: You know which engine a bug report actually implicates, why iOS browser testing was historically one engine, and what "works in Chrome" really claims.
- Dependencies: [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]

## Source Anchors

- [MDN - Rendering engine](https://developer.mozilla.org/en-US/docs/Glossary/Rendering_engine)
- [V8 - What is V8?](https://v8.dev/)
- [WebKit project](https://webkit.org/)

## 1. Concept

Simple version: every browser contains two distinct engines — a **JavaScript engine** that executes JS, and a **rendering engine** (browser engine) that does everything else: parsing HTML/CSS, layout, painting. Conflating them is the classic vague answer; separating them is the mature one.

The accurate map:

| Browser | Rendering engine | JS engine |
|---|---|---|
| Chrome, Edge, Opera, Brave, Arc | **Blink** | **V8** |
| Safari (and all iOS browsers, historically) | **WebKit** | **JavaScriptCore** (JSC) |
| Firefox | **Gecko** | **SpiderMonkey** |

Key facts around the table:

- **Blink forked from WebKit** (2013). They share ancestry but have diverged heavily.
- The JS engine is embeddable on its own: **V8 powers Node.js and Deno; JSC powers Bun.** That's why "JS engine" ≠ "browser": Node is V8 + libuv + Node APIs, no rendering engine at all ([[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]).
- The rendering engine owns the DOM, CSSOM, layout, paint; the JS engine owns ECMAScript execution. **`document`, `fetch`, `setTimeout` are not JS-engine features** — they're bindings the rendering engine/runtime exposes to the engine.
- iOS: Apple long required all browsers to use WebKit — "Chrome on iOS" was a WebKit shell. The EU's DMA has begun forcing this open, but assume iOS ≈ WebKit for compatibility planning.
- Hermes (React Native) and QuickJS are engines optimized for different constraints (startup/memory over peak JIT throughput) — useful to name when asked "what engines exist?"

```ts
// Same V8 engine, different runtimes — this line works in both:
const x = [...new Set([1, 2, 2])];      // ECMAScript → JS engine
// These do not cross over:
document.title;        // rendering-engine binding — browser only
process.env.HOME;      // Node runtime API — Node only
```

## 2. Why It Matters

- "What engines are available?" is your brainstorm question — and answering with one flat list (mixing V8 with WebKit) signals confusion. Two lists, cleanly separated, signals maturity.
- Cross-browser bugs triage differently by engine: a layout difference implicates Blink/WebKit/Gecko; a JS behavior difference (rare, spec-driven) implicates V8/JSC/SpiderMonkey; most "Safari bugs" are WebKit rendering or missing web APIs, not JSC.
- Engine market concentration (Blink's dominance) is why testing Firefox and Safari still matters — they're the only independent implementations keeping "works in Chrome" from becoming the de facto spec.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: QA reports "the date parser is broken on iPhones — works on Android Chrome and desktop."

```ts
// Buggy
const d = new Date('2026-07-17 10:30');   // note: space, no timezone
d.getHours(); // Chrome: 10 — Safari (JSC): historically Invalid Date / inconsistent
```

Trace: `Date` parsing beyond the ISO 8601 format was historically implementation-defined — each *JS engine* chose its own behavior. This is one of the rare cross-*JS-engine* differences (not a rendering issue). Knowing the two-engine split lets you triage instantly: same markup renders fine → not WebKit-the-renderer; JS value differs → JSC vs V8.

```ts
// Fix: never feed Date() non-ISO strings; parse explicitly
const d = new Date('2026-07-17T10:30:00');          // ISO — specified behavior
// or construct from parts / use a library (date-fns, Temporal when available)
```

Tradeoffs: strict ISO handling pushes formatting/parsing responsibility to you or a library — small cost against removing a whole class of engine-dependent bugs.

> [!tip] Triage heuristic: visual/layout difference → rendering engine (check caniuse for CSS features); JS value/behavior difference → JS engine or missing API (check the spec and MDN compat tables); "broken only on iOS, in every browser" → WebKit, because they were all WebKit.

## 4. Interview Answer

Short answer:

> There are two separate engine categories. Rendering engines — Blink in Chrome/Edge, WebKit in Safari, Gecko in Firefox — handle HTML/CSS parsing, layout, and paint. JS engines — V8, JavaScriptCore, SpiderMonkey respectively — execute JavaScript. They're independent: V8 also powers Node and Deno without any rendering engine, and JSC powers Bun. Web APIs like the DOM and fetch belong to the runtime around the JS engine, not to the engine itself.

Deeper answer:

> Useful depth: Blink forked from WebKit in 2013; iOS historically mandated WebKit for all browsers, which made "iOS testing" one engine regardless of browser branding (loosening under the EU DMA). Cross-browser bugs triage by category — layout issues point at rendering engines, JS behavior differences at JS engines (rare and mostly in historically underspecified areas like Date parsing), and missing features at the runtime's API surface. Engine diversity is also why progressive enhancement and compat tables still matter.

## 5. Practice

1. <details><summary>Name the rendering engine and JS engine for Chrome, Safari, and Firefox — and one non-browser user of each JS engine.</summary>Chrome: Blink + V8 (Node/Deno use V8). Safari: WebKit + JavaScriptCore (Bun uses JSC). Firefox: Gecko + SpiderMonkey (embedded in some tools/Firefox's own tooling; historically MongoDB used it).</details>
2. <details><summary>Is setTimeout provided by V8? Defend your answer.</summary>No. V8 implements ECMAScript, which has no timers. setTimeout is a host API: the browser's rendering-engine/runtime layer (or Node's libuv-backed layer) provides it and schedules callbacks into the engine via the event loop.</details>
3. <details><summary>A CSS grid layout breaks only in Safari, on Mac and iPhone alike. Which engine and how do you confirm?</summary>WebKit (rendering engine — layout is its job, and Safari uses WebKit on both platforms). Confirm via caniuse/MDN compat for the specific grid feature and reduce to a minimal test case; JSC is irrelevant because no JS value differs.</details>

## Related Notes

- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]
- [[26 - How the Web Works/06 - How V8 Runs Your Code|How V8 Runs Your Code]]
- [[26 - How the Web Works/04 - Browser Architecture|Browser Architecture]]
