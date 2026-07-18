---
tags: [react, internals, events, portals]
module: "21 - React Internals and Patterns"
priority: important
status: not-started
aliases: [SyntheticEvent, React Event System, createPortal]
---

# Synthetic Events and Portals

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain that React delegates events to the root container (not your elements), what a SyntheticEvent is, and why events from a portal bubble through the *React* tree rather than the DOM tree.
- Production signal: you can debug the modal/click-outside/`stopPropagation` class of bugs by tracing *where listeners are actually attached* — instead of sprinkling `stopPropagation` until symptoms disappear.
- Dependencies: [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]], [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]]

## Source Anchors

- [react.dev - React event object (SyntheticEvent)](https://react.dev/reference/react-dom/components/common#react-event-object)
- [react.dev - createPortal](https://react.dev/reference/react-dom/createPortal)
- [React v17 - Changes to Event Delegation](https://legacy.reactjs.org/blog/2020/08/10/react-v17-rc.html#changes-to-event-delegation)
- [MDN - Event.stopPropagation](https://developer.mozilla.org/en-US/docs/Web/API/Event/stopPropagation)

## 1. React Doesn't Attach Your Handlers Where You Think

`<button onClick={fn}>` does **not** call `button.addEventListener("click", fn)`. React attaches **one native listener per event type on the root container** (the DOM node you passed to `createRoot`) and implements its own delegation ([[19 - DOM and Browser APIs/03 - Event Delegation|the same pattern you'd hand-write]], generalized):

1. A native click reaches the root listener (React 17+; **before 17 it was `document`**).
2. React looks up which fiber the event's target belongs to.
3. It builds a `SyntheticEvent` and walks the **fiber tree** upward, calling every matching `onClickCapture` (down) then `onClick` (up) handler along the way.

Why delegate: one listener instead of thousands (memory, fast mounts/unmounts of large lists), consistent cross-browser behavior through one code path, and — the React 17 motivation for moving off `document` — **multiple React apps/versions on one page** stop stepping on each other, and `e.stopPropagation()` in React can now actually stop events from reaching listeners outside the root.

## 2. SyntheticEvent — the Wrapper

Your handler receives a `SyntheticEvent`: a normalized, cross-browser wrapper with the standard interface (`target`, `currentTarget`, `preventDefault()`, `stopPropagation()`) plus `e.nativeEvent` for the real browser event underneath. Two dated facts worth having exactly right:

- **Event pooling is gone since React 17.** Pre-17, synthetic events were reused and nulled after the handler — the reason legacy code calls `e.persist()` before using an event asynchronously. In React 17+ `e.persist()` does nothing; reading `e.target.value` inside a `setTimeout` or debounced callback just works.
- **Not everything is delegated.** A few events don't bubble natively and get special handling: React's `onFocus`/`onBlur` use `focusin`/`focusout` under the hood (so they delegate), while `scroll`, and media events like `play`/`pause`, are attached directly to the element in React 17+ rather than delegated (`onScroll` also no longer bubbles in React 17+).

> [!tip] Debug the attachment point before changing propagation
> In DevTools, list every native and React listener involved, then trace capture → target → bubble and the React root boundary. Most “React event bugs” are really listener-placement bugs; a target/containment check is usually safer than suppressing a shared event.

## 3. The Boundary Bugs This Explains

Each of these is a "who is attached where, and in which phase" question — trace, don't guess:

**Native `document` listener vs React handler.** A native bubble-phase `document.addEventListener("click", …)` runs *after* React's root-attached handlers for the same click (root is below document on the propagation path). Call `e.stopPropagation()` inside a React `onClick` and the event never reaches `document` — silently breaking analytics listeners, closing-menu listeners, or another library's shortcuts. Conversely, a native listener registered *in the capture phase* (`{ capture: true }` on `document`) runs before anything React sees.

**Click-outside handlers.** The typical `useEffect(() => document.addEventListener("click", close))` menu: clicking the menu's own trigger button fires the React `onClick` (toggle open) *and then* the document listener (close) in the same click — the menu opens and instantly closes. Fixes: check `if (ref.current.contains(e.target)) return` in the document listener (robust), or listen on `mousedown` vs `click` to decouple, — not `stopPropagation` in the React handler, which breaks every *other* document listener too.

**Mixing `addEventListener` and React handlers on one node.** They coexist but fire by DOM rules from *different attach points*: the native listener on the node itself fires before React's root-delegated handler in the bubble phase. Ordering code across the two systems is fragile — pick one system per concern.

> [!warning] `stopPropagation` is a shared-channel mute button
> In a delegated world, stopping propagation doesn't just isolate your widget — it silences every listener above you in *both* systems (React handlers higher in the tree, native listeners on document/window). Production rule: prefer target checks (`contains`) and explicit state over `stopPropagation`; reach for it only when you own everything above you.

## 4. Portals: DOM Elsewhere, React Tree Unchanged

`createPortal(children, domNode)` renders children into a **different DOM container** (typically `document.body`) while leaving them in the **same position in the React tree**:

```jsx
function Modal({ children, onClose }) {
  return createPortal(
    <div className="overlay" onClick={onClose}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>{children}</div>
    </div>,
    document.body
  );
}
```

Two consequences, both interview-grade:

- **Context flows through.** The modal reads the same providers as its React parent, even though its DOM sits at `document.body` — because context follows the fiber tree, not the DOM tree.
- **Events bubble through the React parents.** A click inside the portal triggers `onClick` on the portal's *React* ancestors — components whose DOM nodes are nowhere near the click. React dispatches along the fiber tree; the DOM position is irrelevant to React's propagation.

This is why portals solve the *CSS* problems of overlays (escaping `overflow: hidden`, stacking contexts, `z-index` wars — [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|render pipeline]]) without breaking the *component model*: props, context, and React events behave as if the modal were inline.

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a dropdown rendered in a portal, plus a document-level click-outside close.

Buggy version:

```jsx
function Dropdown({ open, setOpen, children }) {
  const menuRef = useRef(null);
  useEffect(() => {
    if (!open) return;
    const onDocClick = (e) => {
      // ❌ "outside" judged by DOM containment — the portal's DOM is NOT inside the trigger's DOM
      if (!menuRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, [open, setOpen]);

  return (
    <div ref={menuRef}>
      <button onClick={() => setOpen(!open)}>Menu</button>
      {open && createPortal(<ul className="menu">{children}</ul>, document.body)}
    </div>
  );
}
```

Trace: the `<ul>` lives at `document.body`, so `menuRef.current.contains(e.target)` is `false` for clicks *inside the menu* → selecting an item closes the dropdown before the item's `onClick` finishes what it started (or worse, both run and the UI flickers). Meanwhile clicking the trigger both toggles (React handler) and then "closes" (document listener) — the double-fire from section 3.

Production-safe fix — judge "inside" by the pieces you actually rendered, and decouple the trigger:

```jsx
function Dropdown({ open, setOpen, children }) {
  const triggerRef = useRef(null);
  const menuRef = useRef(null);
  useEffect(() => {
    if (!open) return;
    const onDocPointerDown = (e) => {
      if (triggerRef.current?.contains(e.target)) return;  // trigger handles itself
      if (menuRef.current?.contains(e.target)) return;     // clicks in the portal are "inside"
      setOpen(false);
    };
    document.addEventListener("pointerdown", onDocPointerDown);
    return () => document.removeEventListener("pointerdown", onDocPointerDown);
  }, [open, setOpen]);

  return (
    <>
      <button ref={triggerRef} onClick={() => setOpen(o => !o)}>Menu</button>
      {open && createPortal(<ul ref={menuRef} className="menu">{children}</ul>, document.body)}
    </>
  );
}
```

Tradeoffs: two refs and explicit containment checks are more code than a `stopPropagation`, but they don't mute the shared channel (other document listeners keep working) and they state the actual rule ("inside = trigger ∪ menu"). `pointerdown` closes before click handlers fire — snappier, but means a drag starting inside and ending outside won't close; pick per UX. The platform is also catching up: the [Popover API](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API) (`popover` + "light dismiss") does trigger/outside-click/Escape natively and is the zero-JS answer where its styling constraints fit.

## 6. Interview Answer

Short answer:

> React doesn't attach handlers to your elements — it attaches one native listener per event type on the root container (document pre-17) and dispatches a normalized SyntheticEvent along the fiber tree, capture then bubble. That's why `stopPropagation` in React silences native listeners above the root, why native and React handlers on the same click fire in attach-point order, and why old code calls `e.persist()` (pooling — removed in 17). Portals move only the DOM: context and event bubbling still follow the React tree, so a click in a `document.body` portal bubbles to its React parents.

Deeper answer:

> The delegation-to-root change in 17 was about coexistence: multiple React roots/versions on a page each own their events, and stopping propagation actually contains them. Not everything delegates — focus/blur ride focusin/focusout, scroll and media events attach directly. The production bug class is click-outside + portal + stopPropagation: DOM containment checks fail for portaled content (it's not a DOM descendant), and muting propagation breaks unrelated document listeners — the fix is explicit containment against both the trigger and the portal node, or the platform's Popover API where it fits.

## 7. Practice

1. <details><summary>A React `onClick` calls `e.stopPropagation()`. A native `document.addEventListener("click", …)` (bubble phase) stops firing for those clicks — but a `{capture: true}` document listener still fires. Explain both.</summary>React's handlers run from its root-container listener. Stopping propagation there prevents the native event from bubbling further up (root → body → document), so bubble-phase document listeners never see it. Capture-phase listeners run on the way *down* (document → … → target) — before the event ever reaches React's root listener — so they already fired and can't be stopped from below. The order is: document capture → React capture+bubble handlers (at the root) → document bubble.</details>

2. <details><summary>Why did legacy code call `e.persist()`, and why can you delete it today?</summary>Before React 17, SyntheticEvent objects were pooled: after your handler returned, React nulled the fields and reused the object, so reading `e.target.value` asynchronously (setTimeout, debounce, await) gave null/garbage. `e.persist()` removed the event from the pool. React 17 dropped pooling entirely (it bought nothing in modern browsers), so events are plain objects safe to read any time, and `e.persist()` is a no-op you can delete.</details>

3. <details><summary>A modal rendered with `createPortal(…, document.body)` still shows the right theme from a ThemeContext provider, and clicking inside it fires an `onClick` on the page section component that rendered it. Why both?</summary>Both context and React event propagation follow the fiber (React) tree, not the DOM tree. The portal only changes where the DOM nodes are inserted; the modal's fiber remains a child of the section's fiber. So context lookup walks up fibers and finds the provider, and React's dispatch walks the same path for bubbling — the DOM position at body is invisible to both mechanisms. Only things that genuinely operate on the DOM tree (CSS inheritance/selectors, `element.contains`, native bubbling outside React) see the body placement.</details>

4. <details><summary>Your click-outside hook uses `if (!ref.current.contains(e.target)) close()` and users report the menu closes when clicking menu items. The menu is portaled. Diagnose and give two fixes.</summary>The portaled menu's DOM isn't a descendant of `ref.current`, so `contains` returns false for in-menu clicks — "outside" is misclassified. Fix 1: check containment against both refs (trigger and portal node) and return early for either. Fix 2 (platform): use the Popover API's light dismiss, or `dialog` element semantics, and delete the manual listener. Avoid the tempting fix of `stopPropagation` inside the menu — it breaks every other document-level listener (analytics, other menus, shortcut handlers).</details>

## Related Notes

- [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]
- [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]]
- [[21 - React Internals and Patterns/15 - Elements JSX and Component Identity|Elements JSX and Component Identity]]
- [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]]
- [[01 - Roadmap|Roadmap]]
