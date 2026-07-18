---
tags: [javascript, dom, events, react]
module: "19 - DOM and Browser APIs"
priority: must-know
status: not-started
aliases: [Delegation]
---

# Event Delegation

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: you can explain why one listener on a container beats a thousand listeners on rows, write the `closest()` pattern from memory, and connect it to React's synthetic event system.
- Production signal: you reach for delegation for dynamic lists, tables, and infinite scroll — and know when NOT to.
- Dependencies: [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]], [[03 - Scope and Variables/05 - Closures|Closures]]

## Source Anchors

- [MDN - Element.closest](https://developer.mozilla.org/en-US/docs/Web/API/Element/closest)
- [MDN - Event delegation (Learn: events)](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/Event_bubbling#event_delegation)
- [DOM Living Standard - Dispatching events](https://dom.spec.whatwg.org/#dispatching-events)
- [React - Common components: events](https://react.dev/reference/react-dom/components/common#react-event-object)

## 1. Concept

Event delegation: instead of attaching a listener to every interactive descendant, attach one listener to a common ancestor and use bubbling + `event.target` to work out which descendant was activated.

```js
const table = document.querySelector("#orders");

table.addEventListener("click", (e) => {
  const row = e.target.closest("tr[data-order-id]");
  if (!row || !table.contains(row)) return;

  const action = e.target.closest("[data-action]")?.dataset.action;
  const orderId = row.dataset.orderId;

  if (action === "delete") deleteOrder(orderId);
  if (action === "expand") toggleDetails(orderId);
});
```

`closest()` walks *up* from the actual click target (which might be an `<svg>` icon inside the button) to the nearest matching ancestor — this is what makes delegation robust against nested markup.

## 2. Why It Matters

- **Dynamic content**: rows added after page load are handled automatically — no re-binding after every render or AJAX update.
- **Memory and setup cost**: 1 listener object vs N; for a 5,000-row virtualized table this is the difference between trivial and measurable overhead (each listener is a closure the GC must track; see [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]).
- **Cleanup**: one `removeEventListener` (or one `AbortController.signal`) instead of bookkeeping per row.
- It is the mechanism React itself used to scale event handling — knowing it means you understand your framework, not just its API.

## 3. Mechanism, Traced

1. User clicks the trash icon: `<tr data-order-id="42"><button data-action="delete"><svg>…`
2. `click` dispatches with `event.target = <svg>` (deepest element hit).
3. Event bubbles: svg → button → td → tr → tbody → table.
4. The table's single listener runs with `currentTarget = table`, `target = svg`.
5. `e.target.closest("tr[data-order-id]")` walks svg → button → td → tr ✅.
6. `e.target.closest("[data-action]")` resolves the button, giving the intent.

> [!warning] target can be a text-decoration surprise
> `event.target` is the *deepest* element — an icon, a `<span>`, even a pseudo-content wrapper. Never compare `e.target === row`; always resolve upward with `closest()`. Also guard `if (!row) return` — clicks on the table's empty space produce `closest() === null`.

## 4. Delegation and Non-Bubbling Events

`focus`, `blur`, `mouseenter`, `mouseleave` do not bubble. To delegate them:

- Use the bubbling siblings: `focusin`/`focusout`, `mouseover`/`mouseout` (with `closest()` guards against inner-element noise).
- Or register the non-bubbling event with `{ capture: true }` on the ancestor — capture visits ancestors on the way *down*, so it works even without bubbling.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Buggy version — infinite-scroll product list, handler per card:

```js
async function loadMoreProducts() {
  const products = await fetchProducts(nextPage);
  for (const p of products) {
    const card = renderCard(p);
    card.querySelector(".add-to-cart").addEventListener("click", () => {
      addToCart(p.id); // closure per card
    });
    list.append(card);
  }
}
```

Failure modes, traced:

1. Every page of 50 products adds 50 listeners + 50 closures, each closing over its product object — after 20 pages, 1,000 closures retaining 1,000 product objects even if the card data is no longer needed elsewhere.
2. A later "sort" feature re-renders cards from cached data via `innerHTML` — all listeners silently vanish (new DOM nodes), producing "add to cart randomly stopped working after sorting".

Production-safe fix — one delegated listener, data in the DOM:

```js
list.addEventListener("click", (e) => {
  const button = e.target.closest(".add-to-cart");
  if (!button) return;
  const card = button.closest("[data-product-id]");
  addToCart(card.dataset.productId);
});

// Rendering is now free of wiring:
list.append(...products.map(renderCard));
```

Tradeoffs to state in an interview:

- The handler runs for *every* click inside the list and does a `closest()` walk — trivially cheap for clicks, but for high-frequency events (`mousemove`, `scroll`) delegated handlers on a huge container can add per-event cost. Delegate clicks freely; think twice for pointermove.
- Intent now lives in `data-*` attributes: serializable and re-render-proof, but stringly-typed — you lose closure-captured rich objects and must look data up by id.
- `stopPropagation()` anywhere in the subtree breaks the delegated handler — a team convention problem, not a code problem.

## 6. The React Connection

React has always been a delegation system: your `onClick` props do not become per-element native listeners. React attaches one native listener pair (capture/bubble) per event type at the React root, receives the native event there, and dispatches synthetic events by walking the fiber tree from the target upward, calling your handlers in order.

Consequences worth saying out loud:

- Adding `onClick` to 10,000 rows in React costs props/fiber bookkeeping, not 10,000 native listeners — manual DOM delegation inside React is usually solving a problem React already solved.
- React 17 moved the attach point from `document` to the root container, so multiple React versions can coexist and `stopPropagation` interops more predictably with non-React code.
- You *still* apply the delegation mindset in React at the data level: one handler on the list receiving an id beats creating a fresh arrow closure per row when profiling shows re-render pressure (see [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]).

## Real-World Use Cases

### Analytics click tracking via data-attributes

Product wants every meaningful click tracked without sprinkling `track()` calls through components. One document-level listener + declarative `data-track` attributes means new features get analytics by adding markup, not code.

```js
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-track]");
  if (!el) return;
  analytics.track(el.dataset.track, { label: el.dataset.trackLabel });
}, { capture: true });
```

Capture phase is deliberate: the listener runs on the way *down*, before any widget's bubble-phase `stopPropagation()` can hide the click ([[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]).

> [!tip]
> `data-*` intent attributes make tracking auditable — you can grep the codebase for `data-track` and diff the taxonomy in code review, which closures wired per-component never allow.

### Link interception in CMS content (Next.js)

A blog renders CMS HTML via `dangerouslySetInnerHTML`. Every `<a>` inside it is a raw anchor — internal links trigger full page loads, losing client-side navigation. You can't attach `onClick` props to markup you didn't render; delegation on the container is the only handle you have.

```tsx
function ArticleBody({ html }: { html: string }) {
  const router = useRouter();
  const onClick = (e: React.MouseEvent) => {
    const link = (e.target as HTMLElement).closest("a[href^='/']");
    if (!link || e.metaKey || e.ctrlKey) return; // let new-tab clicks behave natively
    e.preventDefault();
    router.push(link.getAttribute("href")!);
  };
  return <div onClick={onClick} dangerouslySetInnerHTML={{ __html: html }} />;
}
```

Works because the click bubbles from the anchor up to the container React *did* render — `closest()` recovers the link no matter how deeply the CMS nested it.

### Delegated keydown on a virtualized data grid

A 10,000-row grid renders only ~30 rows at a time (react-window style). Rows mount and unmount constantly as the user scrolls, so per-row keyboard listeners are wired and destroyed hundreds of times — and arrow-key navigation breaks whenever focus sits on a row that just recycled.

```js
gridEl.addEventListener("keydown", (e) => {
  const row = e.target.closest("[data-row-index]");
  if (!row) return;
  if (e.key === "ArrowDown") focusRow(Number(row.dataset.rowIndex) + 1);
  if (e.key === "ArrowUp") focusRow(Number(row.dataset.rowIndex) - 1);
  if (e.key === "Enter") openDetails(row.dataset.rowId);
});
```

Works because `keydown` bubbles from the focused cell to the stable grid container — the one element that never unmounts. Row identity lives in `data-*`, so recycled DOM nodes need no re-wiring; this is the same reason the note's `innerHTML` re-render bug can't happen here.

## 7. Interview Answer

Short answer:

> Attach one listener to an ancestor, let events bubble, and resolve the intended child with `event.target.closest()`. Works for elements added later, uses one listener instead of thousands, and simplifies cleanup.

Deeper answer:

> The click target is the deepest node, so robust delegation resolves upward with `closest()` and guards for misses. Non-bubbling events delegate via their bubbling variants or capture phase. React applies the same idea internally: root-attached native listeners dispatching synthetic events through the component tree — which is why per-row `onClick` props are cheap in React.

## 8. Practice

1. <details><summary>Why does `if (e.target.matches(".delete-btn"))` fail when the button contains an icon, and what's the fix?</summary>Clicking the icon makes the icon the `target`; `matches` checks only that exact element. Fix: `e.target.closest(".delete-btn")`, which walks ancestors, and check the result is non-null (and inside `currentTarget` if the DOM is untrusted).</details>

2. <details><summary>You need to show a tooltip when any row gains keyboard focus, using one listener on the table. `focus` doesn't bubble — options?</summary>Two: listen for `focusin` on the table (the bubbling counterpart of focus), or `table.addEventListener("focus", handler, true)` using the capture phase, which visits the table on the way down regardless of bubbling.</details>

3. <details><summary>After introducing delegation, clicks on rows inside a third-party dropdown widget stopped triggering your handler. Likely cause?</summary>The widget calls `stopPropagation()` (or `stopImmediatePropagation`) on click events inside itself, so the event never reaches your ancestor listener. Options: capture-phase listener on the ancestor (runs before the widget's bubble handlers), configure/patch the widget, or attach directly inside the widget's subtree.</details>

4. <details><summary>Is delegating `mousemove` on `document.body` for a 10k-node page a good idea?</summary>Usually no. `mousemove` fires continuously; every event runs your handler plus a DOM walk. Prefer attaching to the smallest relevant container, throttling with `requestAnimationFrame`, or using pointer events with `setPointerCapture` for drag scenarios.</details>

## Related Notes

- [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]
- [[21 - React Internals and Patterns/16 - Synthetic Events and Portals|Synthetic Events and Portals]]
- [[19 - DOM and Browser APIs/04 - Custom Events and EventTarget|Custom Events and EventTarget]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[17 - Practical Frontend Scenarios/06 - Cleaning Event Listeners|Cleaning Event Listeners]]
- [[01 - Roadmap|Roadmap]]
