---
tags: [labs, code-review, react, async, accessibility]
module: "90 - Labs"
priority: important
status: not-started
aliases: [code review lab 1, search results PR]
---

# Lab 05 — Code Review Lab: The Search Results PR

A different lab format: you are the reviewer. Below is a "pull request" from a teammate — a search-results feature that *works in the happy path* and would probably get approved on a rushed Friday. It contains **8 planted issues** ranging from ship-blocking to nitpick. Review it like a senior would, *then* check yourself against the hidden model review.

## How to Work This Lab

1. Read the diff top to bottom **without opening the model review**. Timebox: 25 minutes, like a real review.
2. Write your review as actual PR comments: quote the line, state the *mechanism* of the bug (not "this looks wrong"), the user-visible symptom, the fix, and a severity: 🔴 blocks merge · 🟡 should fix · ⚪ nit.
3. Only then open the model review and grade yourself. A found bug only counts if you named the mechanism.
4. Score: 8/8 with mechanisms = solid. Missing any 🔴 = reread the linked note and redo the lab in a week.

## The Pull Request

> **feat: add product search results panel** — "Adds live search to the products page. Tested locally, works great."

```tsx
// SearchResults.tsx
import { useEffect, useState } from "react";

type Product = { id: string; name: string; priceCents: number };

export function SearchResults({ query }: { query: string }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [sorted, setSorted] = useState<Product[]>([]);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/search?q=${query}`)
      .then((res) => res.json())
      .then((data) => {
        setProducts(data.items);
        setLoading(false);
      });
  }, [query]);

  useEffect(() => {
    setSorted([...products].sort((a, b) => a.priceCents - b.priceCents));
  }, [products]);

  function handleSelect(product: Product) {
    trackEvent("select", product.id);
    location.href = `/products/${product.id}`;
  }

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <p dangerouslySetInnerHTML={{ __html: `Results for <b>${query}</b>` }} />
      <ul>
        {sorted.map((p, i) => (
          <li key={i}>
            <div className="result-row" onClick={() => handleSelect(p)}>
              {p.name} — ${(p.priceCents / 100).toFixed(2)}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

async function trackEvent(name: string, id: string) {
  fetch("/api/analytics", {
    method: "POST",
    body: JSON.stringify({ name, id, ts: Date.now() }),
  });
}
```

Stop here. Write your review before scrolling.

---

## Model Review (open each only after writing your own comment)

1. <details><summary>🔴 The fetch effect — races and no cancellation</summary>Nothing cancels or supersedes the previous request when <code>query</code> changes. Two rapid queries can resolve out of order — slow "car" response overwrites fast "cardio" results (mechanism: promise resolution order ≠ dispatch order). Also fires per keystroke: no debounce. Fix: <code>AbortController</code> in the effect with cleanup aborting the prior request, plus debounce upstream. [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]], [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]].</details>
2. <details><summary>🔴 The fetch effect — setState after unmount + no error path</summary>No cleanup means the <code>.then</code> chain runs after unmount (setState on unmounted component; with abort this disappears since abort rejects). Worse: no <code>.catch</code> and no <code>res.ok</code> check — a network failure leaves <code>loading</code> stuck <code>true</code> forever (the symptom users report as "infinite spinner"), and the rejection is unhandled. Fix: abort in cleanup; check <code>res.ok</code>; <code>catch</code> ignoring <code>AbortError</code>, setting an error state otherwise. [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling]], [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|cleanup]].</details>
3. <details><summary>🔴 <code>dangerouslySetInnerHTML</code> with user input</summary>Textbook reflected XSS: <code>query</code> is user-typed and lands in <code>innerHTML</code>. <code>?q=&lt;img src=x onerror=...&gt;</code> executes. Fix: plain JSX interpolation (<code>Results for &lt;b&gt;{query}&lt;/b&gt;</code>) — React escapes text children; the bold styling never needed raw HTML. [[20 - Network and Security/05 - XSS|XSS]].</details>
4. <details><summary>🔴 Clickable <code>div</code> — accessibility</summary><code>&lt;div onClick&gt;</code> is invisible to keyboard and screen-reader users: not focusable, no role, no Enter/Space activation. And since activation is navigation, the right element is a link — <code>&lt;a href=&#96;/products/${p.id}&#96;&gt;</code> — which also restores open-in-new-tab and SPA routing (use the router's Link, not <code>location.href</code>, which full-page-reloads). [[25 - Accessibility and Inclusive UX/00 - Accessibility and Inclusive UX MOC|a11y]].</details>
5. <details><summary>🟡 <code>key={i}</code> — index as key</summary>Results reorder across queries and sorts; index keys make React match old item state/DOM to wrong products (mechanism: keys drive reconciliation identity). Symptom class: wrong row highlights, misapplied animations. Fix: <code>key={p.id}</code>. [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]].</details>
6. <details><summary>🟡 <code>sorted</code> state + effect — derived state stored</summary><code>sorted</code> is derivable from <code>products</code>; storing it costs an extra render per update (effect runs after commit, sets state, re-renders) and a frame where <code>products</code> and <code>sorted</code> disagree. Fix: derive during render — <code>const sorted = useMemo(() =&gt; [...products].sort(...), [products])</code> — or just sort inline. [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|derived-state smell]].</details>
7. <details><summary>🟡 Unencoded query in URL + unhandled analytics rejection</summary><code>&#96;/api/search?q=${query}&#96;</code> breaks on <code>&amp;</code>, <code>#</code>, <code>+</code>, non-ASCII — needs <code>encodeURIComponent</code> (or <code>URLSearchParams</code>). In <code>trackEvent</code>, the inner <code>fetch</code> promise is floating: a rejection is unhandled (noise in error tracking, <code>unhandledrejection</code> events). Fix: <code>catch</code> and drop, and note <code>navigator.sendBeacon</code> is the right tool for fire-and-forget analytics on navigation — <code>location.href</code> may kill the in-flight fetch. [[11 - Error Handling/00 - Error Handling MOC|Error Handling]].</details>
8. <details><summary>⚪ Loading UX + missing states</summary><code>if (loading) return</code> replaces existing results with a spinner on every keystroke — layout jank and lost context; keep stale results visible with an inline indicator. No empty state ("no results for X") and the loading div isn't announced to screen readers ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|live regions]]). Nit-level here, but it's the difference between working and polished.</details>

## After the Review

- Rewrite the component with all 🔴 and 🟡 issues fixed, in a scratch repo, and add two deterministic tests: the race (explicit resolution order) and the stuck-spinner-on-error case ([[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|deterministic async tests]]).
- Answer out loud: which *three* of these would you mention if you only had two minutes with the author? (Ranking severity under constraint is the reviewer skill.)
- Retrospective: [[98 - Vault Operations/Templates/Lab Retrospective Template|template]] — note which bugs you missed and which module that points at.

## Related Notes

- [[90 - Labs/00 - Labs MOC|Labs MOC]]
- [[17 - Practical Frontend Scenarios/00 - Practical Frontend Scenarios MOC|Practical Frontend Scenarios MOC]]
- [[15 - Interview Preparation/05 - Bad Answer vs Good Answer|Bad Answer vs Good Answer]]
