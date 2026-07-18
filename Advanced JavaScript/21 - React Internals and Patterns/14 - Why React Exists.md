---
tags: [react, internals, fundamentals, architecture]
module: "21 - React Internals and Patterns"
priority: must-know
status: not-started
aliases: [Why Frameworks Exist, UI as a Function of State, Virtual DOM Tradeoffs]
---

# Why React Exists

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: you can explain the problem UI frameworks solve (state–DOM synchronization), state React's core bet (UI = f(state)), and give an honest account of the virtual DOM's costs versus fine-grained reactivity — without tribalism.
- Production signal: you choose tools by the actual tradeoff (state complexity vs runtime cost), and you can predict where React's abstraction will leak before it bites you.
- Dependencies: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]], [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]

## Source Anchors

- [react.dev - Reacting to Input with State (declarative vs imperative)](https://react.dev/learn/reacting-to-input-with-state)
- [react.dev - Thinking in React](https://react.dev/learn/thinking-in-react)
- [react.dev - Render and Commit](https://react.dev/learn/render-and-commit)
- [react.dev - You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect)
- [React Blog - React 19.2 (where the model is today)](https://react.dev/blog/2025/10/01/react-19-2)
- [Solid Docs - Fine-grained reactivity](https://docs.solidjs.com/advanced-concepts/fine-grained-reactivity)
- [Svelte Docs - What are runes?](https://svelte.dev/docs/svelte/what-are-runes)
- [Vue Docs - Reactivity in Depth](https://vuejs.org/guide/extras/reactivity-in-depth.html)

## 1. The Problem Before Frameworks

The DOM is a mutable, stateful tree with an imperative API. Before frameworks, keeping it in sync with application state was *your* job, by hand, at every state change. The cost model: with **N pieces of state** shown in **M places**, you maintain up to **N×M hand-written update paths** — and every new feature multiplies them.

```js
// jQuery-era: one "like" click must update three places, imperatively
$("#like-btn").on("click", function () {
  likes++;                                     // 1. the state (a global)
  $(this).toggleClass("liked");                // 2. the button
  $("#like-count").text(likes);                // 3. the counter
  $("#activity-badge").text(likes + follows);  // 4. a derived badge elsewhere
  // ...and the modal opened later must ALSO read/redraw these
});
```

The bug classes this breeds are predictable: **forgotten paths** (a new widget shows likes, but three of the five update sites don't know about it), **state living in the DOM** (`hasClass("liked")` *is* the data — scraping the UI to know your own state), **order-dependent reads** (code that works only if another handler ran first), and **drift** (two displays of the same value disagree, and no one knows which is right). Every one of these is a synchronization failure — the UI and the state stopped agreeing.

## 2. The Core Bet: UI = f(state)

React's founding idea is to make synchronization *someone else's job* by changing the contract: you never update the UI. You describe, as a pure function, what the UI looks like **for any given state** — and when state changes, React re-runs the function and reconciles the difference into the DOM.

```jsx
function LikeWidget({ likes, follows, liked, onLike }) {
  // No update paths. This is the answer to "what does the UI look like when state is X?"
  return (
    <>
      <button className={liked ? "liked" : ""} onClick={onLike}>Like</button>
      <span>{likes}</span>
      <Badge count={likes + follows} />
    </>
  );
}
```

State becomes plain data; the DOM becomes *output*. N×M sync paths collapse to N state transitions — the M render sites are derived automatically and can't drift, because they're recomputed from the same source every time.

This one bet explains most of React's "rules", which otherwise look arbitrary:

- **Render must be pure** — the function may be re-run at any time, so it can't have side effects ([[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]]).
- **State must be immutable** — React detects change by comparing references; mutating in place hides the change ([[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]).
- **Keys exist** — "re-run the function" produces a new description each time, so list identity across descriptions has to be declared ([[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]).

> [!tip] The transferable idea
> UI = f(state) isn't React-specific — it's the shared premise of Vue, Svelte, Solid, SwiftUI, Jetpack Compose, and Flutter. Learn it once as a model and every declarative UI system becomes "same bet, different reconciliation strategy." That's also the honest one-line answer to "why do frameworks exist": to own state→UI synchronization so application code doesn't.

## 3. The Virtual DOM — the Honest Performance Story

"Re-run the whole function on every change" sounds ruinously expensive. React's trick is that the function doesn't produce DOM — it produces **elements**: cheap, plain JS objects describing the desired UI ([[21 - React Internals and Patterns/15 - Elements JSX and Component Identity|Elements and JSX]]). React diffs the new description against the previous one and commits only the difference to the real DOM.

Get the claim right, because interviewers probe it:

- The virtual DOM makes re-render-everything **affordable, not fast**. Building and diffing object trees is pure overhead compared to a hand-written surgical `el.textContent = x` — which is why "the virtual DOM is fast" is folklore, not fact. Its value is the **programming model**: you get to write f(state) and still ship acceptable DOM updates.
- The alternative family uses **fine-grained reactivity**, but the implementation matters. Solid signals directly notify the DOM bindings that read them; Svelte compiles reactive updates from runes; Vue tracks dependencies to schedule component updates, then commonly renders and patches a virtual DOM subtree (with compiler optimizations). These models can avoid React-style whole-component re-rendering or reduce the work inside it, but they trade in different dependency-tracking and compilation rules.
- React's counter-bets on its own overhead are **scheduling** — if re-rendering is the model, make it interruptible and prioritized ([[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber]]) — and the **React Compiler**, which auto-memoizes so unchanged subtrees skip re-rendering without hand-written `memo` ([[21 - React Internals and Patterns/10 - React 19|React 19]]).

No tribalism required: signals do less work per update; React's model is arguably simpler to reason about at scale (everything is just re-running a function) and has the larger ecosystem. Both are valid engineering positions with different loss functions.

## 4. What You Pay

A framework is not free, and a senior answer names the bill:

- **Runtime + bundle cost**: React ships a reconciler, scheduler, and event system to every user; the exact transfer cost depends on React version, bundler, route splitting, compression, and what your application imports. Measure the built artifact rather than quoting a universal number.
- **Abstraction leaks**: the model is "just a function", but the machinery shows through — [[14 - JavaScript in React and Next.js/03 - Stale Closures|stale closures]], [[21 - React Internals and Patterns/08 - useSyncExternalStore|tearing]], [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|hydration mismatches]], key bugs. Roughly half this vault exists because the abstraction leaks; this module is the map of where.
- **Lock-in**: components, hooks, and ecosystem libraries are not portable; the team's knowledge investment compounds inside one ecosystem.

The trade is worth it when **UI-state complexity dominates** — many interacting pieces of state, shown in many places, changing over time. It's a bad trade for a mostly-static page with two event listeners: there, the platform (HTML + a few listeners, maybe web components) is the leaner engineering choice. "When would you *not* use React?" is a real interview question, and "a content site with trivial interactivity" is the expected answer.

## 5. Why Internals Knowledge Pays Rent

This module exists for leverage, not trivia — one concrete payoff per area:

- **Debugging**: scrambled checkbox state after a list delete stops being a mystery and becomes "index keys re-associated component instances" — a 30-second diagnosis ([[21 - React Internals and Patterns/02 - Reconciliation and Keys|keys]]). Stale UI becomes "closure over an old snapshot"; phantom re-renders become "unstable context value identity."
- **Architecture**: context vs external store, controlled vs uncontrolled forms, transition vs debounce — each is an internals-driven decision (subscription granularity, where value state lives, lane priority), not a style preference. Knowing the mechanism is what lets you defend the choice in design review.
- **Performance**: you optimize the real cost model — render cost vs commit cost vs paint cost — instead of cargo-culting `memo` everywhere. "Re-renders are not the enemy; expensive renders and unnecessary commits are" ([[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit]]).
- **Interviews**: the mid→senior filter is almost always mechanism ("*why* do index keys corrupt state?", "*what does* startTransition actually do?"). Feature knowledge is table stakes; mechanism is the differentiator.
- **Ecosystem literacy**: you can read "signals vs VDOM" or "React Compiler vs Svelte" discourse critically, evaluate the next framework in an afternoon, and recognize marketing claims ("no virtual DOM = fast") as tradeoff statements.

> [!warning] Internals knowledge has a failure mode too
> Reciting fiber field names or scheduler internals *unprompted* signals memorization, not judgment. The calibrated move is: lead with the model and the practical consequence, offer depth when asked. Every note in this module is structured that way on purpose.

## Real-World Use Cases

This note is conceptual, so the use cases invert: real features where you'd *feel* the problem React solves if you rebuilt them in vanilla JS — plus the one where vanilla wins.

### Rebuilding a checkout form in vanilla JS: the N×M explosion in miniature

A checkout form: shipping method affects the total, the total appears in the summary panel *and* the sticky pay button, and an invalid promo code disables the button. Four pieces of state, four display sites — every handler must remember every affected site.

```js
shippingSelect.addEventListener("change", () => {
  order.shipping = SHIPPING_RATES[shippingSelect.value];
  summaryTotal.textContent = formatTotal(order);      // site 1
  payButton.textContent = `Pay ${formatTotal(order)}`; // site 2
  // forgot: the mobile sticky bar also shows the total → drift bug shipped
});
promoInput.addEventListener("input", () => {
  order.promoValid = validatePromo(promoInput.value);
  payButton.disabled = !order.promoValid;             // ...and re-derive the total AGAIN here
  summaryTotal.textContent = formatTotal(order);       // duplicated update path
});
```

Every new field multiplies handlers × display sites (section 1's N×M). In React the same feature is one `total = computeTotal(order)` in render — the display sites can't disagree because they're all derived from the same state on every render. The day you feel this pain is the day UI = f(state) stops being a slogan.

### A live dashboard: state trapped in the DOM

A vanilla ops dashboard gets WebSocket updates: `{ serverId, status }`. The natural vanilla move is to update the DOM directly — and now the DOM *is* your database.

```js
socket.onmessage = (e) => {
  const { serverId, status } = JSON.parse(e.data);
  const card = document.querySelector(`[data-server="${serverId}"]`);
  card.querySelector(".status").textContent = status;
  card.classList.toggle("alert", status === "down");
  // "how many servers are down?" → scrape the DOM you just painted:
  banner.hidden = document.querySelectorAll(".alert").length === 0;
};
```

Derived values (the alert banner, a "3 down" counter, a filtered view) must be recomputed by *querying the UI*, because there is no state object — section 1's "state living in the DOM." Add a filter feature and the scraping breaks (hidden cards leave the DOM). The React version holds `servers` as data, and banner/counter/filter are three cheap derivations in render.

### The counter-case: a marketing page with an accordion

A five-section FAQ accordion on a static content page. State complexity: one integer (which section is open). Display sites: one.

```html
<script>
  document.querySelectorAll(".faq-q").forEach((q) =>
    q.addEventListener("click", () => q.parentElement.classList.toggle("open"))
  );
</script>
```

Six lines, zero bytes of framework, no hydration. Shipping React here buys nothing — there's no N×M to collapse — and costs runtime, bundle, and a hydration surface (section 4). This is the concrete answer to "when would you *not* use React," and giving it unprompted is a senior signal.

> [!tip]
> The decision rule from section 4, operationalized: count independent pieces of state and the places each is displayed. One state × one site → platform. Many states × many sites, changing over time → the framework's synchronization guarantee is what you're buying.

## 6. Interview Answer

Short answer:

> Frameworks exist because keeping a mutable DOM in sync with changing state by hand scales as state-sites × display-sites and breeds drift bugs. React's bet is UI = f(state): describe the UI for any state as a pure function, re-run it on change, and let the library reconcile the difference. The virtual DOM is what makes that affordable — cheap object trees diffed before touching the DOM — but it's overhead, not speed; its value is the programming model.

Deeper answer:

> That one bet explains React's rules — pure render, immutable state, keys — they're all requirements of "this function may re-run at any time." Fine-grained alternatives make different tradeoffs: Solid directly updates signal-bound DOM, Svelte compiles invalidation, and Vue tracks dependencies while still often patching VDOM for component updates. React's counter-moves on its own overhead are scheduling — interruptible, prioritized rendering via Fiber — and the React Compiler auto-memoizing unchanged subtrees. And the honest boundary: for a mostly static page, the platform alone is the better engineering choice; frameworks earn their cost when UI-state complexity dominates.

## 7. Practice

1. <details><summary>A teammate says "the virtual DOM is fast." Refine that claim.</summary>The virtual DOM is *slower* than optimal hand-written DOM updates — building and diffing element trees is pure overhead on top of the final DOM mutations. What it's fast *enough* for is the model it enables: re-run the whole render function on every change and still commit only the minimal diff. So the accurate claim is: the VDOM makes a declarative programming model affordable; surgical updates (or fine-grained reactivity, which skips diffing via dependency tracking) do less work per update. React compensates with scheduling (Fiber) and compile-time memoization (React Compiler), not by the VDOM being inherently fast.</details>

2. <details><summary>When is React the wrong choice for a project, and what would you say in the meeting?</summary>When UI-state complexity is low relative to the framework's cost: content/marketing sites, mostly-static pages with islands of trivial interactivity, extreme performance/size budgets (embedded webviews, low-end devices), or long-lived widgets embedded in third-party pages where React's runtime and version coupling are liabilities. In the meeting: quantify the project’s actual bundle and hydration cost — "we would add a runtime and hydration surface to manage two dropdowns; plain HTML plus a few listeners (or an islands framework like Astro) gives us the same outcome with less to break." The signal is reasoning from the measured cost model, not loyalty.</details>

3. <details><summary>Explain UI = f(state) to a backend engineer in their vocabulary.</summary>It's the same move as declarative infrastructure or SQL: you don't write the mutation steps, you declare the desired end state and an engine computes the diff. The UI is a projection (a materialized view) of application state; when the underlying data changes, the view is recomputed and the engine (React) applies the minimal changeset to the live system (the DOM). Renders must be pure and state immutable for the same reason migrations shouldn't have side effects: the engine assumes it can recompute the projection at any time and get the same answer.</details>

4. <details><summary>Signals (Solid/Svelte/Vue) vs React's re-render model — state each side's tradeoff in two sentences per side.</summary>Fine-grained systems are not identical: Solid directly updates signal-bound DOM nodes, Svelte compiles targeted invalidation, and Vue tracks dependencies but often still patches VDOM within an updated component. They can reduce per-update work, at the cost of dependency-tracking and compiler rules that developers must understand. React re-runs a pure function and reconciles the result — one uniform model with a huge ecosystem, while scheduling can prioritize and interrupt the work. Its costs are re-render/diff overhead and the referential-equality pressure that the React Compiler now automates in common cases.</details>

## Related Notes

- [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]]
- [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]
- [[21 - React Internals and Patterns/15 - Elements JSX and Component Identity|Elements JSX and Component Identity]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]
- [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[01 - Roadmap|Roadmap]]
