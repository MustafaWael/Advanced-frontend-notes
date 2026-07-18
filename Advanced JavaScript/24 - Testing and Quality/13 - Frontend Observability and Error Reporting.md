---
tags: [observability, error-reporting, monitoring, testing, production]
module: "24 - Testing and Quality"
priority: important
status: not-started
aliases: [error tracking, Sentry patterns, frontend monitoring]
verified_on: 2026-07-17
version_scope: "React 19, web-vitals v4-era APIs"
---

# Frontend Observability and Error Reporting

## Maturity Target

- Priority: #important
- Study time: 60 minutes
- Interview signal: you can answer "how do you know your frontend is broken in production?" with capture surfaces, context, and signal discipline — not "we use Sentry."
- Production signal: errors arrive with enough context to reproduce, and dashboards alert on user impact instead of noise.
- Dependencies: [[11 - Error Handling/00 - Error Handling MOC|Error Handling MOC]], [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals]]

## Source Anchors

- [MDN — GlobalEventHandlers.onerror / error event](https://developer.mozilla.org/en-US/docs/Web/API/Window/error_event)
- [React docs — createRoot options (onUncaughtError, onCaughtError)](https://react.dev/reference/react-dom/client/createRoot)
- [web.dev — web-vitals library](https://web.dev/articles/vitals-field-measurement-best-practices)

## 1. Concept

Simple version: tests tell you what broke *before* shipping; observability tells you what broke *after* — in browsers, networks, and usage patterns you never tested. It's the third leg of quality, next to types and tests.

The accurate mechanism — frontend observability is three pillars, each with specific capture surfaces:

**Errors.** Four distinct surfaces, and missing any one leaves a blind spot:

| Surface | Catches | Misses |
| --- | --- | --- |
| `window.addEventListener("error")` | uncaught sync throws, resource load failures | anything already caught |
| `window.addEventListener("unhandledrejection")` | floating promise rejections | rejections handled late |
| React error boundary / `onUncaughtError` (root option, React 19) | render/lifecycle throws — pairs containment with reporting | event handlers, async code |
| Instrumented seams (`fetch` wrapper, action wrappers) | *handled* failures you still want counted | — |

That last row is the one people forget: a `catch` block that shows a toast and moves on has **handled** the error — no global surface will ever see it. Handled-but-abnormal must be *reported deliberately* or your dashboard says "all green" while checkout fails for 4% of users.

**Context.** A stack trace without context is a riddle. Minimum viable payload: release/commit hash (to symbolicate against the right **source maps** — minified `a.b is not a function at chunk-7f3.js:1:48213` is useless without them), route, user-agent, and breadcrumbs (the last N navigations, clicks, and requests before the error).

**Real-user monitoring.** Lab metrics ([[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals]]) on your machine ≠ the field. The `web-vitals` library reports LCP/INP/CLS from real sessions; send with `navigator.sendBeacon` so page unload doesn't drop the data.

## 2. Why It Matters

"How do you know it's broken?" is a standard senior-screen question precisely because mid-level candidates answer with testing and seniors answer with *feedback loops*. It also decides real incidents: time-to-detect for a frontend bug without error reporting is "whenever support tickets spike."

## 3. Real Frontend Example: Bug → Fix → Tradeoff

```ts
// Buggy: handled means invisible
async function submitOrder(payload: Order) {
  try {
    return await api.post("/orders", payload);
  } catch {
    toast.error("Something went wrong");   // user informed, team blind
  }
}
```

Trace: the rejection is caught, so `unhandledrejection` never fires; no boundary is involved; the analytics dashboard counts a session, not a failure. A payment-provider regression here is discovered by revenue reports, not engineers.

```ts
// Production-safe: report handled failures with context, classified
async function submitOrder(payload: Order) {
  try {
    return await api.post("/orders", payload);
  } catch (err) {
    reportError(err, {
      severity: err instanceof ApiError && err.status < 500 ? "warning" : "error",
      context: { flow: "checkout", step: "submit-order" },
    });
    toast.error("Something went wrong");
    throw new SubmitFailedError({ cause: err }); // let the caller decide, too
  }
}
```

Tradeoffs: reporting costs — bandwidth, a vendor bill scaled by event volume, and PII risk (breadcrumbs can capture form input — scrub by default). And over-reporting is self-defeating: report *expected* failures (validation errors, offline) at error severity and the team learns to ignore the channel — alert fatigue is the observability version of flaky tests ([[24 - Testing and Quality/10 - Mocking Seams and False Confidence|false confidence]]). Classify: expected failures are metrics, unexpected ones are alerts.

> [!tip] Wire the boundary to the reporter: React 19's `createRoot(el, { onUncaughtError, onCaughtError })` centralizes this — boundaries contain, root options report. One seam, no per-boundary duplication.

> [!warning] Sample rates cut cost but can silently sample *out* a rare browser-specific crash. Sample successes and performance events; never sample fatal errors.

## 4. Interview Answer

Short answer:

> "Three pillars: error reporting, context, and real-user metrics. Errors need four capture surfaces — global `error`, `unhandledrejection`, error boundaries, and deliberate reporting inside `catch` blocks, because a handled error is invisible to every global hook. Reports carry release hash for source maps, route, and breadcrumbs. For performance, lab numbers aren't the field — `web-vitals` from real sessions, sent via `sendBeacon`."

Deeper answer:

> "The judgment calls: severity classification — a 400 validation failure is a metric, an unexpected 500 or TypeError is an alert, and mixing them trains people to ignore alerts. Scrubbing — breadcrumbs and request bodies capture PII by default, so allowlist fields rather than blocklist. And alerting on *user impact* (error rate per session on checkout) rather than raw counts, because one bot in a retry loop shouldn't page anyone. The goal is time-to-detect measured in minutes with a reproducible payload attached."

## 5. Practice

1. <details><summary>An error boundary shows the fallback UI, but nothing appears in your error tracker. List the mechanical explanations.</summary>The boundary caught it and nobody reported it (containment without reporting — wire <code>onCaughtError</code>/<code>componentDidCatch</code> to the reporter); the reporter script itself failed to load (ad blockers — common; measure your reporter's delivery rate); or the event was sampled out / rate-limited. Also check: some trackers batch and lose events on immediate navigation — <code>sendBeacon</code> or flush-on-<code>visibilitychange</code>.</summary></details>
2. <details><summary>Production stack traces point at <code>vendor-3fa1.js:1:88742</code>. What's missing, mechanically, and how does it get fixed?</summary>Source maps. The build emits minified bundles plus <code>.map</code> files; the fix is uploading maps to the error tracker keyed by release hash at deploy time (not serving them publicly), and tagging every error event with the same release. Symbolication then rewrites frames to original file/line. Wrong-release maps produce *plausible but wrong* frames — worse than none.</details>
3. <details><summary>Transfer: your INP is great in Lighthouse but terrible in field data. Why can this happen, and what does it say about lab vs RUM?</summary>Lab runs on a warm dev machine with no extensions, no third-party tags firing, one synthetic interaction. Field INP aggregates real devices (low-end Android), real sessions (long tasks from ads/analytics), and the *worst* interactions. Lab is a regression detector; RUM is the truth. Optimize against field percentiles, verify fixes in lab.</details>

## Related Notes

- [[11 - Error Handling/05 - React Error Boundaries|React Error Boundaries]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[24 - Testing and Quality/00 - Testing and Quality MOC|Testing and Quality MOC]]
