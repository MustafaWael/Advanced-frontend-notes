---
tags: [javascript, dom, events, architecture]
module: "19 - DOM and Browser APIs"
priority: important
status: not-started
aliases: [CustomEvent, EventTarget]
---

# Custom Events and EventTarget

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain when a custom event beats a callback prop or a store, and you know `EventTarget` is subclassable without any DOM element involved.
- Production signal: you can decouple a widget/micro-frontend from its host page with events instead of shared globals.
- Dependencies: [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]], [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]]

## Source Anchors

- [MDN - CustomEvent](https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent)
- [MDN - EventTarget](https://developer.mozilla.org/en-US/docs/Web/API/EventTarget)
- [DOM Living Standard - Interface EventTarget](https://dom.spec.whatwg.org/#interface-eventtarget)
- [MDN - Creating and triggering events](https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model/Events/Creating_and_triggering_events)

## 1. Concept

The browser's event system is not reserved for built-in events. Two capabilities matter:

1. **Dispatch your own events on DOM nodes** with `CustomEvent` + `dispatchEvent` — they propagate like native events (if you opt in) and carry a `detail` payload.
2. **`EventTarget` is a standalone base class** — you can `new EventTarget()` or extend it to build pub/sub objects with zero DOM involvement.

```js
// 1. DOM custom event
element.dispatchEvent(
  new CustomEvent("cart:item-added", {
    detail: { productId: "p42", qty: 2 },
    bubbles: true,     // default is false!
    composed: true     // crosses shadow DOM boundaries
  })
);

// 2. Pure pub/sub, no DOM
class UploadQueue extends EventTarget {
  add(file) {
    // ...start upload...
    this.dispatchEvent(new CustomEvent("progress", { detail: { pct: 0 } }));
  }
}
const queue = new UploadQueue();
queue.addEventListener("progress", (e) => render(e.detail.pct));
```

## 2. Why It Matters

- It is the platform-native decoupling mechanism: a date-picker web component or a micro-frontend can announce "date selected" without knowing anything about its consumers.
- `new EventTarget()` replaces hand-rolled emitter classes (and their subtle bugs around remove-during-emit) with a spec-tested implementation that supports `once`, `signal`, and capture out of the box.
- Interviewers use it to probe whether you know the event system as a *system*, or only as `onClick`.

## 3. Mechanism Details That Bite

- `dispatchEvent` is **synchronous**: every listener runs before the `dispatchEvent` call returns. This is unlike a real user event arriving as a new task. Exceptions inside one listener don't stop the others (they're reported), but re-entrancy is real: if a listener dispatches another event, you're nested.
- `bubbles: false` is the default — the #1 reason "my parent never hears the event".
- `cancelable: true` lets listeners call `preventDefault()`; `dispatchEvent` then returns `false`, letting the dispatcher implement "vetoable" actions.
- Shadow DOM: events need `composed: true` to escape a shadow root; `event.target` is *retargeted* to the host element for outside listeners.
- `detail` is not cloned — listeners receive your object reference. Mutation by one listener is visible to the next.

> [!tip] Namespace your event types
> Use `"cart:item-added"`, `"upload:progress"` style names. Custom events share a global string namespace with all current and future native events; a bare `"change"` or `"toggle"` custom event will eventually collide with native behavior.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a legacy jQuery header and a new React app must both react when the cart changes.

Buggy version — shared global + polling:

```js
// React island
window.__cartCount = cart.items.length;

// Legacy header polls
setInterval(() => {
  badge.textContent = window.__cartCount ?? 0;
}, 1000);
```

Failure modes: 1-second staleness, a timer that runs forever (see [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]), an unowned global that any script can clobber, and no way to know *what* changed.

Production-safe fix — custom event as the contract:

```js
// React island announces (after commit, e.g. in useEffect):
useEffect(() => {
  window.dispatchEvent(
    new CustomEvent("cart:changed", { detail: { count: cart.items.length } })
  );
}, [cart.items.length]);

// Legacy header subscribes:
window.addEventListener("cart:changed", (e) => {
  badge.textContent = e.detail.count;
});
```

Trace: state commits → effect runs → `dispatchEvent` synchronously invokes the header's listener → badge updates in the same task, before next paint. No polling, no global, and the payload documents the contract.

Tradeoffs: events are fire-and-forget — no return values, no delivery guarantee if the header loads late (mitigate: dispatch on subscribe or keep last value readable), and stringly-typed payloads need a documented (or TypeScript-declared) event map. For rich bidirectional flows inside one app, a store ([[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]) is usually better; events shine at *boundaries* between systems.

## 5. AbortSignal Cleanup Pattern

`EventTarget` composes with `AbortController` for group cleanup — one controller tears down many listeners:

```js
const ac = new AbortController();
window.addEventListener("cart:changed", onCart, { signal: ac.signal });
window.addEventListener("resize", onResize, { signal: ac.signal });
// teardown:
ac.abort();
```

This is the modern alternative to keeping arrays of `[target, type, fn]` tuples, and it pairs naturally with [[08 - Async JavaScript/06 - AbortController|AbortController]] for fetch cancellation in the same lifecycle.

## 6. Interview Answer

Short answer:

> `CustomEvent` lets you dispatch your own events with a `detail` payload through the normal propagation system, and `EventTarget` is a subclassable base class, so you get platform-native pub/sub with `once`, capture, and `AbortSignal` cleanup for free — no DOM required.

Deeper answer:

> `dispatchEvent` runs listeners synchronously and returns whether the event went uncanceled, so you can build vetoable operations. Custom events don't bubble by default and need `composed: true` to cross shadow roots, where targets get retargeted to the host. It's the right tool at system boundaries — web components, micro-frontends, framework islands — while in-app state flows usually belong in props or a store.

## 7. Practice

1. <details><summary>A web component dispatches `new CustomEvent("select", { detail })` but the page's listener on a wrapper div never fires. Two likely causes?</summary>(1) `bubbles` defaults to `false` — the event fires on the component but never reaches the wrapper. (2) If the component uses shadow DOM, it also needs `composed: true` to escape the shadow root. Fix: `{ detail, bubbles: true, composed: true }`.</details>

2. <details><summary>What does `dispatchEvent` return, and how would you build a "closable unless vetoed" panel with it?</summary>It returns `false` if the event was `cancelable` and some listener called `preventDefault()`, else `true`. Dispatch `new CustomEvent("panel:before-close", { cancelable: true })`; if `dispatchEvent(...)` returns `true`, proceed to close; listeners veto by calling `preventDefault()`.</details>

3. <details><summary>Is `target.dispatchEvent(evt)` async like a real click? Prove your answer in code.</summary>No — synchronous. `let order = []; el.addEventListener("x", () => order.push("listener")); el.dispatchEvent(new Event("x")); order.push("after");` yields `["listener", "after"]`. A real user click arrives as a new task instead.</details>

4. <details><summary>When would you choose a custom event over a React context/store, and vice versa?</summary>Custom events: crossing ownership boundaries — web components, micro-frontends, legacy+modern coexistence, third-party embeds — where consumers are unknown and coupling must stay near zero. Context/store: within one app where you want typed state, return values, devtools, and predictable re-render integration. Events are fire-and-forget notifications, not state containers.</details>

## Related Notes

- [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]
- [[13 - Performance and Memory/05 - Event Listeners and Timers Cleanup|Event Listeners and Timers Cleanup]]
- [[01 - Roadmap|Roadmap]]
