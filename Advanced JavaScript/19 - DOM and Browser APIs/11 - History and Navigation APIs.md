---
tags: [javascript, dom, routing, nextjs]
module: "19 - DOM and Browser APIs"
priority: important
status: not-started
aliases: [History API, SPA Routing]
---

# History and Navigation APIs

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain how client-side routing works mechanically — pushState, popstate, scroll restoration — and what Next.js's router adds on top.
- Production signal: you can debug broken back-button behavior, lost scroll positions, and "URL changed but nothing re-rendered".
- Dependencies: [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]], [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]

## Source Anchors

- [MDN - History API](https://developer.mozilla.org/en-US/docs/Web/API/History_API)
- [HTML Living Standard - Session history](https://html.spec.whatwg.org/multipage/nav-history-apis.html)
- [MDN - Navigation API](https://developer.mozilla.org/en-US/docs/Web/API/Navigation_API)
- [Next.js - Linking and Navigating](https://nextjs.org/docs/app/getting-started/linking-and-navigating)

## 1. Concept

The browser keeps a **session history** per tab: a list of entries (URL + state + scroll position). A "single-page app" is an app that manipulates this list without full page loads:

```js
// Change URL without a request; push a new entry
history.pushState({ productId: 42 }, "", "/products/42");

// Replace current entry (no new back-stack item)
history.replaceState({ step: 2 }, "", "/checkout?step=2");

// Fired when the user navigates the stack (back/forward) — NOT by pushState
window.addEventListener("popstate", (e) => {
  render(location.pathname, e.state);
});
```

The complete DIY router is: intercept link clicks (delegation + `preventDefault` — [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]] in action) → `pushState` → render for the new URL → listen to `popstate` to render on back/forward. Every SPA router — React Router, Next's App Router client navigation — compiles down to this.

## 2. Why It Matters

- "How does client-side routing actually work?" is a favorite senior filter — it exposes whether frameworks are magic to you.
- The router *changes the URL*; **you** must render, restore scroll, move focus, and handle the server side. Each forgotten duty is a production bug class.
- The URL is state ([[19 - DOM and Browser APIs/05 - Browser Storage|state that survives refresh and is shareable]]) — misusing push vs replace corrupts the user's back button, one of the most user-visible bugs there is.

## 3. Mechanism Details That Bite

- `pushState` does **not** fire `popstate`, does not load anything, does not scroll — it only edits the history list. `popstate` fires only on stack *traversal* (back/forward/`history.go`).
- The `state` object is structured-clone-serialized (no functions/DOM nodes) and size-capped; it survives refresh (`history.state`) — unlike module variables.
- Same-document `#hash` changes also create entries and fire `hashchange` + `popstate` — the pre-pushState routing mechanism.
- `history.scrollRestoration = "manual"` turns off the browser's automatic scroll restore — required by SPAs (content isn't there yet when the browser would restore), which then owe users a correct reimplementation.
- **Server requirement**: deep links like `/products/42` must return your app shell (or a real page) — the classic "SPA 404s on refresh" is a missing server rewrite, not a frontend bug.
- The newer **Navigation API** (`navigation.addEventListener("navigate", ...)`) can intercept *all* navigations (links, form posts, back button) in one place — Chromium-led, not yet universal (check current support before relying on it); it exists because assembling correct routing from pushState pieces proved so error-prone.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: filterable product list; filters update the URL so views are shareable.

Buggy version:

```js
searchInput.addEventListener("input", (e) => {
  const params = new URLSearchParams(location.search);
  params.set("q", e.target.value);
  history.pushState(null, "", `?${params}`);   // BUG 1: push per keystroke
  renderList();
});
// BUG 2: no popstate listener at all
```

Traced failures:

1. Typing "shoes" pushes 5 history entries — Back now steps through `?q=shoe`, `?q=sho`… The back button is ruined; users must click Back 6 times to leave.
2. When the user *does* press Back, `popstate` fires but nobody listens: the URL changes while the list keeps showing the old results — "URL and UI disagree", the signature bug of half-built routing.

Production-safe fix:

```js
searchInput.addEventListener("input", debounce((e) => {
  const params = new URLSearchParams(location.search);
  e.target.value ? params.set("q", e.target.value) : params.delete("q");
  // Refinements REPLACE; distinct views PUSH.
  history.replaceState(null, "", params.size ? `?${params}` : location.pathname);
  renderList();
}, 300));

window.addEventListener("popstate", () => {
  const q = new URLSearchParams(location.search).get("q") ?? "";
  searchInput.value = q;   // sync UI ← URL
  renderList();
});
```

Trace: keystrokes mutate the *current* entry (one Back press exits the page); traversal re-reads the URL as the single source of truth and re-renders. The rule of thumb: **push** for locations users think of as "places" (product page, tab), **replace** for refinements of the current place (filters, sort, wizard step correction).

Tradeoff: replace-only refinements mean Back never returns to a previous filter combination — some products *want* filter history (then push, but debounced and semantically, e.g. on filter commit rather than keystroke). URL-as-state also forces you to define the empty/default serialization (`?q=` vs no param) or you get duplicate cache keys and ugly shares.

## 5. What Next.js Adds on Top

The App Router's `<Link>`/`router.push()` sit on this exact machinery, adding:

- **Interception**: `<Link>` renders a real `<a>` (SEO, middle-click work) and intercepts same-origin clicks → `pushState` instead of navigation.
- **Data fetching**: client navigation requests the **RSC payload** for the target route — not HTML — and reconciles it into the tree ([[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client]]).
- **Prefetching** of routes for in-viewport links (an IntersectionObserver under the hood — [[19 - DOM and Browser APIs/06 - Observers|Observers]]).
- **Router Cache** so Back/Forward can restore instantly from memory ([[22 - Next.js Deep Dive/02 - The Caching Layers|Caching Layers]]) plus scroll and focus management.
- `useSearchParams`/`usePathname` as the React-idiomatic `location`, and `router.replace` mirroring the push-vs-replace decision above (Next's own docs use `replace` for search filters — `window.history.replaceState` is even sanctioned for high-frequency cases).

Knowing the layer boundaries is the senior skill: when Back behaves oddly in a Next app, you can ask "is this pushState misuse (my code), Router Cache staleness (Next), or scroll restoration (browser)?"

## 6. Interview Answer

Short answer:

> SPA routing is: intercept link clicks, `pushState` to change the URL without a load, render for the new URL yourself, and listen for `popstate` to re-render on back/forward. `pushState` adds a history entry; `replaceState` edits the current one; `popstate` only fires on traversal, never on your own pushes.

Deeper answer:

> The URL is the source of truth: on popstate you re-derive UI from `location`, and refinements use replace while new "places" use push, or you corrupt the back stack. SPAs must also own scroll restoration and focus, and the server must rewrite deep links to the app. Next.js layers link interception, RSC-payload fetching, prefetching, and a router cache on the same primitives.

## 7. Practice

1. <details><summary>Why doesn't `popstate` fire after you call `pushState`, and what implication does that have for router design?</summary>By spec, `pushState`/`replaceState` silently edit the session history — `popstate` signals *traversal* (user/programmatic back-forward). Implication: your router can't centralize rendering in the popstate handler alone; programmatic navigations must call render explicitly, so real routers funnel both paths through a single `navigate(url)` function (or use the Navigation API, which unifies them).</details>

2. <details><summary>A Next.js app: user scrolls deep into an infinite list, clicks a product, presses Back — lands at the top of an empty list. Which layers could be at fault?</summary>Three suspects: (1) scroll restoration — the list page must restore scroll, but content must exist first; (2) data — infinite-scroll pages that refetch page 1 on Back lose loaded pages (fix: cache loaded pages in memory/sessionStorage or rely on the Router Cache's snapshot); (3) manual `history.scrollRestoration = "manual"` somewhere without reimplementation. Debug by separating "was the DOM rebuilt identically?" from "was scroll restored?"</details>

3. <details><summary>Multi-step checkout wizard: which steps should push and which replace? Defend it.</summary>Completing a step and moving forward: **push** — users expect Back to return to the previous step. Corrections within a step (validation retries, toggling payment method), and redirects like `/checkout` → `/checkout?step=1`: **replace** — Back should never revisit a half-invalid state or the bare redirecting URL. Also store step data in `state`/server, not just the URL, so refresh mid-wizard survives.</details>

4. <details><summary>What breaks if a dev "routes" by setting `location.href = "/products/42"` inside an SPA?</summary>It triggers a full document navigation: complete reload, all in-memory state lost, server round-trip, flash of empty app — the SPA advantages disappear (though the URL and back button remain correct, since it's a real navigation). Legitimate uses: cross-origin links, escaping a fatally broken app state, or forcing fresh auth. Otherwise use the router.</details>

## Related Notes

- [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]]
- [[19 - DOM and Browser APIs/06 - Observers|Observers]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[22 - Next.js Deep Dive/02 - The Caching Layers|The Caching Layers]]
- [[01 - Roadmap|Roadmap]]
