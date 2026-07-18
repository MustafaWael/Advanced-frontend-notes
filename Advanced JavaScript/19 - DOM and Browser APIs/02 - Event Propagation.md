---
tags: [javascript, dom, events]
module: "19 - DOM and Browser APIs"
priority: must-know
status: not-started
aliases: [Bubbling, Capturing]
---

# Event Propagation

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can name the three phases in order, explain `stopPropagation` vs `stopImmediatePropagation` vs `preventDefault`, and say what passive listeners actually do.
- Production signal: you can debug "my click handler fires twice" or "scroll feels janky because of a touch listener" without trial-and-error.
- Dependencies: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals]], [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]]

## Source Anchors

- [DOM Living Standard - Dispatching events](https://dom.spec.whatwg.org/#dispatching-events)
- [MDN - Event.stopPropagation](https://developer.mozilla.org/en-US/docs/Web/API/Event/stopPropagation)
- [MDN - EventTarget.addEventListener](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener)
- [web.dev - Passive event listeners](https://web.dev/articles/passive-event-listeners)

## 1. Concept

When an event is dispatched on a target, the browser computes a propagation path from the document root down to the target, then walks it in three phases:

1. **Capturing phase**: root → …ancestors… → target's parent. Only listeners registered with `capture: true` run.
2. **Target phase**: listeners on the target itself run (both capture and bubble listeners, in registration order).
3. **Bubbling phase**: target's parent → …ancestors… → root. Only non-capture listeners run, and only if the event's `bubbles` flag is true.

```js
parent.addEventListener("click", () => console.log("parent capture"), { capture: true });
parent.addEventListener("click", () => console.log("parent bubble"));
child.addEventListener("click", () => console.log("child"));

// Click on child logs:
// parent capture → child → parent bubble
```

`event.target` is where the event originated; `event.currentTarget` is the element whose listener is currently running. During bubbling they differ — this distinction powers [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]].

## 2. Why It Matters

- Delegation, analytics capture, modals that close on outside click, and design-system components all depend on propagation mechanics.
- Most "mystery double-fire" and "my handler never runs" bugs are propagation bugs.
- Passive listeners are a scroll-performance lever interviewers increasingly expect seniors to know.

## 3. The Three Control Methods — Precisely

| Method | What it does | What it does NOT do |
| --- | --- | --- |
| `preventDefault()` | Cancels the event's *default action* (navigation, form submit, checkbox toggle, scrolling) if `cancelable` | Does not stop propagation at all |
| `stopPropagation()` | Stops the walk to *further elements* in the path | Does not stop other listeners on the *same* element; does not cancel the default action |
| `stopImmediatePropagation()` | Stops further elements AND remaining listeners on the current element | Does not cancel the default action |

```js
button.addEventListener("click", (e) => {
  e.stopPropagation();
  console.log("first"); // runs
});
button.addEventListener("click", () => {
  console.log("second"); // STILL runs — same element
});
// With stopImmediatePropagation() in the first listener, "second" would not run.
```

> [!warning] stopPropagation is a footgun in shared codebases
> A `stopPropagation()` deep in a widget silently breaks every delegated listener above it: analytics, "close on outside click", keyboard shortcut handlers. Prefer checking `event.target` conditions in the outer handler over suppressing propagation in the inner one. If you must stop it, comment why.

## 4. Passive Listeners

`addEventListener("touchstart" | "touchmove" | "wheel", handler, { passive: true })` is a promise to the browser: *this handler will not call `preventDefault()`*.

Mechanism: normally the browser must wait for your handler to finish before scrolling, because the handler *might* cancel the scroll. That couples scroll latency to main-thread work. With `passive: true`, the browser starts scrolling immediately on the compositor thread and runs your handler in parallel. Calling `preventDefault()` inside a passive listener is ignored with a console warning.

Modern browsers default `touchstart`/`touchmove`/`wheel` listeners on window/document/body to passive — which is why old "prevent scroll" code silently stopped working.

## 5. Real Frontend Example: Modal Close-on-Outside-Click

Buggy version:

```js
// Modal component
openButton.addEventListener("click", () => {
  modal.showModal();
});

// Global: close when clicking outside modal content
document.addEventListener("click", (e) => {
  if (!modalContent.contains(e.target)) {
    modal.close();
  }
});
```

Trace the bug:

1. User clicks `openButton`.
2. Button's listener runs → modal opens.
3. The same click keeps bubbling up to `document`.
4. Document listener runs: `openButton` is not inside `modalContent` → modal closes immediately.
5. Symptom: "the modal flashes open and instantly closes."

Common bad fix: `e.stopPropagation()` in the open handler — works, but now any other document-level click logic (menus, analytics) never sees clicks on that button.

Production-safe fix — attach the outside-click listener *after* the current event finishes, or check the timestamp/element explicitly:

```js
openButton.addEventListener("click", () => {
  modal.showModal();
  // Defer registration until this click has finished propagating.
  setTimeout(() => {
    document.addEventListener("click", onOutsideClick);
  }, 0);
});

function onOutsideClick(e) {
  if (!modalContent.contains(e.target)) {
    modal.close();
    document.removeEventListener("click", onOutsideClick);
  }
}
```

Tradeoff: deferring with `setTimeout(0)` adds a task boundary — correct, but it's implicit coordination that a reader must understand. Alternatives: use the native `<dialog>` element's backdrop click behavior, or compare `e.target` against the opener. Choose the version your team can maintain.

## 6. React Synthetic Events

React attaches listeners at the React root (since React 17; previously `document`) and implements its own propagation over the fiber tree.

- `e.stopPropagation()` in a React handler stops React's propagation and, because React's root listener participates in native bubbling, usually native listeners above the root too — but a *native* listener attached between the DOM target and the root has already run by the time React's handler executes.
- Mixing native `addEventListener` and React handlers on the same subtree is a classic source of "why does my native handler run even though React stopped propagation" — order native-capture → native handlers below root (bubbling toward root) → React handlers.

## 7. Common Bugs and Edge Cases

- `focus` and `blur` do not bubble; `focusin`/`focusout` do. Delegating focus requires the latter (or `capture: true`).
- `scroll` on an element does not bubble to `document` (though it does fire on `document` when the document itself scrolls). Use capture or per-element listeners.
- A listener added with `{ once: true }` auto-removes after first invocation — great for "close on next click".
- Removing a listener requires the same function reference *and* the same capture flag: `removeEventListener("click", fn)` will not remove `addEventListener("click", fn, true)`.
- `event.eventPhase` (1 capturing, 2 at-target, 3 bubbling) is your debugging friend.

## Real-World Use Cases

### Global keyboard shortcuts that ignore form fields

An app binds `?` to open help and `/` to focus search with one `keydown` listener on `window`. Every keystroke in every input also bubbles to `window`, so the handler must check the event's origin or shortcuts fire while the user types.

```js
window.addEventListener("keydown", (e) => {
  if (e.target.closest("input, textarea, [contenteditable=true]")) return;
  if (e.key === "/") {
    e.preventDefault(); // stop "/" from being typed into the search box we focus
    searchInput.focus();
  }
  if (e.key === "?") openHelpDialog();
});
```

Works because `keydown` bubbles from the focused element up to `window` — `e.target` tells you *where the user was typing*, which is the whole guard.

### Passive wheel listener on a horizontal carousel

A product page maps vertical wheel input to horizontal carousel movement. A default (non-passive) `wheel` listener forces the browser to wait for JavaScript before scrolling the *page* too — every product page scroll now stutters under load.

```js
// Only reading wheel deltas to sync a progress indicator → promise not to cancel:
carousel.addEventListener("wheel", updateScrollIndicator, { passive: true });

// Actually hijacking scroll → must be explicit, and you own the latency cost:
carousel.addEventListener("wheel", (e) => {
  e.preventDefault();
  carousel.scrollLeft += e.deltaY;
}, { passive: false });
```

Works because `passive: true` decouples compositor scrolling from your handler; `preventDefault()` only functions when you opt out with `passive: false` — and remember document-level touch/wheel listeners are passive *by default* now.

> [!tip]
> If the goal is just "don't scroll the page while over this element", CSS `overscroll-behavior: contain` or `touch-action` gets you there with zero listener latency.

### Form-level blur validation with `focusout`

A checkout form validates each field when the user leaves it. Per-field `blur` listeners break for dynamically added fields — but `blur` doesn't bubble, so naive delegation on the `<form>` silently never fires.

```js
checkoutForm.addEventListener("focusout", (e) => {
  const field = e.target.closest("[data-validate]");
  if (field) showFieldError(field, validate(field));
});
```

Works because `focusout` is the *bubbling* counterpart of `blur` — the same fix applies to `focus`→`focusin`. The alternative is registering `blur` with `{ capture: true }`, since capture visits the form on the way down regardless of bubbling. See [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]] for the full delegation pattern.

## 8. Interview Answer

Short answer:

> Events travel root-to-target in the capturing phase, fire at the target, then bubble target-to-root. `preventDefault` cancels the default action but not propagation; `stopPropagation` stops later elements but not other listeners on the same element; `stopImmediatePropagation` stops both.

Deeper answer:

> Passive listeners decouple scrolling from the main thread: `{ passive: true }` guarantees no `preventDefault`, so the browser can begin compositor-driven scrolling without waiting for JavaScript. React implements its own synthetic propagation with listeners delegated to the root, so mixing native and React listeners has observable ordering consequences.

## 9. Practice

1. <details><summary>Listeners: document (capture), ul (bubble), li (bubble). Click the li. Order?</summary>document capture → li → ul. Capturing runs top-down first, target listeners next, then bubbling bottom-up. The document's bubble-phase listeners (none here) would run last.</details>

2. <details><summary>A checkbox inside a clickable table row toggles the row selection AND the checkbox, double-toggling. Fix without stopPropagation?</summary>In the row's click handler, ignore clicks that originate from the checkbox: `if (e.target.closest("input[type=checkbox]")) return;`. This keeps propagation intact for analytics/delegation while excluding the checkbox's own default behavior from the row logic.</details>

3. <details><summary>Why did `document.addEventListener("touchmove", e => e.preventDefault())` stop blocking scroll in modern browsers?</summary>Browsers made touch/wheel listeners on document-level targets passive by default for scroll performance, and `preventDefault()` inside a passive listener is ignored. To actually block scrolling you must pass `{ passive: false }` explicitly (and accept the scroll-latency cost), or use CSS `touch-action`/`overscroll-behavior`.</details>

4. <details><summary>`btn.addEventListener("click", handler, true)` then later `btn.removeEventListener("click", handler)` — is the listener removed?</summary>No. Capture and bubble registrations are distinct; removal must match the capture flag: `removeEventListener("click", handler, true)`.</details>

## Related Notes

- [[19 - DOM and Browser APIs/03 - Event Delegation|Event Delegation]]
- [[21 - React Internals and Patterns/16 - Synthetic Events and Portals|Synthetic Events and Portals]]
- [[19 - DOM and Browser APIs/04 - Custom Events and EventTarget|Custom Events and EventTarget]]
- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[01 - Roadmap|Roadmap]]
