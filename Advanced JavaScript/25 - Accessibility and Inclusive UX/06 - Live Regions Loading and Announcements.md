---
tags: [accessibility, live-regions, async]
module: "25 - Accessibility and Inclusive UX"
priority: must-know
status: not-started
aliases: [aria-live, role status, announcements]
---

# Live Regions, Loading States and Announcements

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: explain how `aria-live` works mechanically (regions must pre-exist; mutations are announced) and choose polite vs assertive correctly.
- Production signal: every async state change in your UI — loading, success, failure, count updates — is perceivable without sight, without spamming.
- Dependencies: [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA]], [[08 - Async JavaScript/00 - Async JavaScript MOC|Async JavaScript]]

## Source Anchors

- [MDN: ARIA live regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Guides/Live_regions)
- [MDN: aria-live](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-live)
- [WAI-ARIA 1.2: live region properties](https://www.w3.org/TR/wai-aria-1.2/#attrs_liveregions)
- [MDN: role="status"](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/status_role)

## 1. Concept

Screen readers announce where focus *is*. Anything that changes elsewhere — a toast, a result count, a "saved" indicator, an error appearing — is silent by default. **Live regions** subscribe AT to a DOM subtree: when its *content changes*, the change is announced regardless of focus.

```tsx
// The mechanics that trip everyone up: the region must EXIST BEFORE the message.
// AT registers live regions at render; injecting a region + message together often announces nothing.

function Toaster() {
  return (
    <div role="status" className="sr-only">   {/* always rendered, initially empty */}
      {message}                                 {/* mutating THIS is what announces */}
    </div>
  );
}
```

The vocabulary:

- `aria-live="polite"` (≙ `role="status"`) — queue the announcement until current speech finishes. Default for nearly everything: confirmations, counts, progress.
- `aria-live="assertive"` (≙ `role="alert"`) — interrupt immediately. Reserve for task-blocking failures ([[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|alert vs status]]).
- `aria-atomic="true"` — announce the whole region on any change, not just the changed node (a price of "$42" changing to "$45" should read "Price: $45 dollars", not "45").
- `role="log"`, `role="timer"`, `aria-relevant` — specialized; rarely needed.

**Loading-state choreography** for async UI ([[17 - Practical Frontend Scenarios/09 - Debounced Search|debounced search]] as the canonical case):

1. Request starts → after a *delay threshold* (~400ms — instant results shouldn't announce "loading" at all), politely announce "Searching…".
2. Results arrive → announce the outcome summary: "8 results for 'react'" — not the results themselves (the user will navigate them; announcing all 8 is spam).
3. Failure → the error is announced (alert or focus-to-error, [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|forms]]) *and* recoverable.
4. Never announce per keystroke or per progress-percent tick.

React note: because the region must pre-exist, render it unconditionally and swap its *children*; don't conditionally render `{error && <div role="alert">}` and expect reliability across AT (it often works for `role="alert"` on insertion, but the always-present pattern is the dependable one). Clearing the message after a few seconds prevents stale re-readings on re-render.

## 2. Why It Matters

- Modern UIs are *mostly* async state changes away from focus — search-as-you-type, optimistic updates ([[22 - Next.js Deep Dive/03 - Revalidation|cache invalidation UIs]]), autosave, toasts. Without live regions, a screen-reader user's app is frozen in time between focus moves.
- Both failure directions are real: silence (user submits, nothing announced, they assume it's broken) and spam (every keystroke announces, the app is unusable). Getting the *choreography* right is the skill.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an autosaving notes editor. Sighted users see a subtle "Saving… / Saved" indicator; a screen-reader user reports losing 20 minutes of work after assuming saves were happening. They also report the app "won't shut up" since a hotfix.

```tsx
// Bug v1: purely visual indicator — silence
{saveState === "saving" && <span className="indicator">Saving…</span>}
{saveState === "saved" && <span className="indicator">Saved</span>}

// Hotfix v2: someone added assertive + announces every state — spam
<div aria-live="assertive">{saveState === "saving" ? "Saving…" : "Saved"}</div>
// autosave fires every 3s → "Saving… Saved. Saving… Saved." forever, interrupting typing
```

Trace: v1 communicates only via paint — AT users get nothing, and silence reads as breakage (or worse, as safety). v2 overcorrects: assertive interrupts the user's own typing echo every three seconds with information that's only occasionally interesting.

```tsx
// Fix: announce transitions that carry information, politely, debounced
const [announcement, setAnnouncement] = useState("");

useEffect(() => {
  if (saveState === "error") {
    setAnnouncement("Saving failed. Your changes are not saved.");  // the one that matters
  } else if (saveState === "saved" && previous === "error") {
    setAnnouncement("Saving recovered. All changes saved.");        // recovery is news
  }
  // routine saving/saved cycles: SILENT — the steady state is the expectation
}, [saveState]);

return (
  <>
    <span className="indicator" aria-hidden="true">{visualLabel}</span>  {/* eyes */}
    <div role={saveState === "error" ? "alert" : "status"} className="sr-only">
      {announcement}                                                     {/* ears */}
    </div>
  </>
);
```

The principle: **announce information, not state machinery**. Routine success is the assumed steady state; deviations (failure, recovery) are the news. An on-demand check remains available: a "Save status" element the user can focus/query.

Tradeoffs: deciding "what is news" is a design judgment per feature — and it belongs in the same design review as the visuals, not bolted on. The sr-only + aria-hidden split duplicates a small amount of content; a shared `<Announcer>` service (one persistent region, an `announce(msg, { assertive })` API) centralizes the machinery and the debouncing.

> [!warning] Testing live regions honestly
> jsdom can assert the DOM shape (`role="status"` exists, message appears — do this in component tests), but *whether and how it's spoken* is AT behavior: VoiceOver, NVDA, and JAWS differ on injected-region edge cases. The always-rendered-region pattern minimizes the variance, and one manual screen-reader pass per announcing feature is the verification ([[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|manual checks]]).

## Real-World Use Cases

### Cart badge and optimistic updates

"Add to cart" updates a header badge from 2 to 3 — visually obvious, silent for AT. One persistent polite region announces "Added to cart, 3 items" per action, while the badge itself stays out of any live region (it re-renders on unrelated cart syncs, which would spam).

```tsx
function AddToCartButton({ product }) {
  const { addItem, count } = useCart();
  const announce = useAnnouncer();                 // shared persistent region

  return (
    <button onClick={() => {
      addItem(product);                            // optimistic — see [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|state updates]]
      announce(`${product.name} added to cart, ${count + 1} items`);
    }}>
      Add to cart
    </button>
  );
}
```

Works because the announcement is tied to the *user's action*, not to the region mirroring a state variable — reconciliation-driven re-renders can't re-trigger it.

> [!warning]
> If the optimistic update rolls back on server failure, the failure announcement is mandatory — the user was just told the item was added. Roll back silently and the spoken UI has lied.

### Route changes in an SPA

Client-side navigation never reloads the page, so screen readers announce nothing on route change — the single most common SPA a11y bug. A persistent polite region announcing the new page title on `usePathname()` change (plus moving focus to the new `<h1>`) restores the "page changed" signal a full reload gives for free. Next.js App Router's built-in route announcer does exactly this — know that it exists and that custom routers must replicate it (see [[19 - DOM and Browser APIs/11 - History and Navigation APIs|History and Navigation APIs]]).

### Countdown timers without the chatter

A ticket-checkout hold timer counts down from 10:00. Announcing every second is unusable; announcing nothing strands AT users into a surprise expiry. The pattern: `role="timer"` on the visual countdown (explicitly *not* re-announced per tick), plus milestone announcements — polite at 5:00 and 2:00, assertive at 0:30 since expiry blocks the task — mirroring the push-news/expose-state split from the upload practice question.

## 4. Interview Answer

Short answer:

> Screen readers announce the focused element; everything changing elsewhere needs a live region — a pre-existing DOM node with `aria-live`/`role="status"` whose *content mutations* get announced. Polite queues, assertive interrupts — assertive only for task-blocking failures. The choreography matters as much as the plumbing: delay "loading" announcements past ~400ms, announce outcome summaries ("8 results") rather than payloads, keep routine steady-state transitions silent, and always announce failures. The region must be rendered before the message arrives — injecting region and message together is the classic silent bug.

Deeper answer:

> In React that means unconditionally rendering an empty status node and swapping its children — a shared Announcer primitive with one persistent region and a debounced `announce()` API keeps product code from hand-rolling regions. The autosave case shows the judgment: routine save cycles are silent (steady state is the expectation), failure is assertive (it blocks the task), recovery is polite news; the visual indicator gets `aria-hidden` so the two channels don't double-speak. Verification splits: DOM shape in component tests, actual speech behavior in a manual pass, because AT implementations genuinely differ on live-region edge cases.

## 5. Practice

1. <details><summary>Why does `{error && <div aria-live="polite">{error}</div>}` often announce nothing?</summary>AT registers live regions when they enter the DOM; the announcement fires on *subsequent content changes*. Inserting the region already containing the message means there's no observed change — many AT/browser pairs skip it. (`role="alert"` is specced to announce on insertion, and usually does, but support is uneven.) The reliable pattern: region always rendered, initially empty; set its text when the error arrives.</details>

2. <details><summary>Design the announcements for a file-upload with progress. What's announced, when, at what politeness?</summary>Start: polite "Uploading report.pdf" (once). Progress: NOT per percent — either silence until done, or milestone announcements (25/50/75%) at most, polite; also expose `role="progressbar"` with `aria-valuenow` so users can *query* progress on demand rather than being told. Completion: polite "report.pdf uploaded". Failure: assertive "Upload failed" + recovery action reachable ([[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|error patterns]]). The on-demand/push split is the design tool: push news, expose state.</details>

3. <details><summary>A results list re-renders on every filter change. `aria-atomic` — on or off for the count announcer, and why?</summary>On (`aria-atomic="true"`) for the count region: you want "42 results" read as a whole phrase each change, not a bare "42" (or worse, a diffed fragment) without context. Atomic announces the entire region on any internal change. Keep the region's content a single short summary phrase precisely so atomic re-reads stay cheap. The *results themselves* are not in a live region at all — users navigate to them.</details>

4. <details><summary>Your toast library shows success toasts for 3 seconds. What are the two a11y failures baked into that design, and the mitigations?</summary>(1) Timing: 3 seconds may be gone before a screen-reader user's queue reaches it or a low-vision user locates it — WCAG 2.2.1 wants adjustable timing; mitigation: announce via live region (speech isn't bounded by the visual timeout), pause dismissal on hover/focus, and keep a reviewable notification log/center. (2) Focus: toasts must never steal focus (they'd interrupt the task mid-keystroke); they're announcement + optional action, and if they contain an action ("Undo"), it needs a keyboard-reachable path before timeout — which practically means extending/pinning on focus. Ephemeral visuals need a non-ephemeral information channel.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms, Validation and Async Errors]]
- [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA: Roles, Names and States]]
- [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]
- [[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|Async UI Testing]]
