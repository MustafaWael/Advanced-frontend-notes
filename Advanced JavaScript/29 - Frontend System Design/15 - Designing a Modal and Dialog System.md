---
tags: [system-design, interview, modal, dialog, accessibility]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [modal design, dialog system, focus trap design]
verified_on: 2026-07-17
version_scope: "Browser APIs (native <dialog> showModal(), inert) and WAI-ARIA APG dialog-modal pattern as of 2026"
---

# Designing a Modal and Dialog System

## Maturity Target

- Priority: #must-know
- Study time: 60 minutes
- Interview signal: Run RADIO on "design a modal system" covering focus management, portals/stacking, the dialog APG contract, and a promise-based imperative API — with tradeoffs.
- Production signal: You can build a reusable dialog that's accessible, stackable, and scroll-locked without bugs.
- Dependencies: [[29 - Frontend System Design/07 - Component API Design|Component API Design]], [[29 - Frontend System Design/14 - Accessibility in System Design|Accessibility in System Design]], [[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|Dialogs and Focus Traps]]

## Source Anchors

- [WAI-ARIA APG — Dialog (Modal) Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/)
- [MDN — <dialog> element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dialog)
- [MDN — inert](https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/inert)

## 1. Requirements

Ask: one modal at a time or **stackable** (confirm-on-top-of-form)? content-driven only, or **imperative** (`await confirm()` from anywhere)? dismiss rules (backdrop click, Escape, only via buttons for destructive)? scroll behavior of the page behind? animations? SSR?

Design against: **a reusable dialog system — accessible, stackable, imperatively callable for confirms, backdrop + Escape dismiss (configurable), scroll-locked, animated.** Out of scope: the visual design language.

Non-functional, said aloud: accessibility is a hard requirement (this is the APG dialog pattern), and the modal must not break the page underneath (scroll position, focus, background interaction).

## 2. Architecture

```
<DialogProvider>  (holds a stack of open dialogs, renders a Portal)
        │  imperative API: openDialog(config) → Promise<result>
        ▼
   Portal → document.body
    ┌──────────────────────────────┐
    │ Backdrop (per stack level)    │  scroll-lock, click-to-dismiss
    │  ┌────────────────────────┐   │
    │  │ <dialog role="dialog"   │   │  focus trap + restore
    │  │  aria-modal="true">     │   │  aria-labelledby / describedby
    │  └────────────────────────┘   │
    └──────────────────────────────┘
   background tree → inert / aria-hidden
```

Key decisions: render via a **Portal** to `document.body` so the modal escapes parent `overflow`/`z-index`/`transform` traps (a portal keeps it in the React tree for context/events but moves the DOM node — [[21 - React Internals and Patterns/16 - Synthetic Events and Portals|portals]]). A **provider holds a stack** so multiple dialogs layer correctly; only the top is interactive, everything below is `inert`. The background (siblings of the portal) is marked `inert`/`aria-hidden` so focus and screen readers can't reach it.

> [!warning] Nested `overflow:hidden`/`transform` ancestors clip or mis-position a modal rendered inline — the reason portals exist for this. And a modal that only sets `aria-hidden` on the background but not `inert` still lets keyboard focus tab into the page behind it.

## 3. Data Model

```ts
interface DialogInstance<R = unknown> {
  id: string;
  render: (close: (result: R) => void) => ReactNode;
  dismissable: boolean;              // backdrop/Escape allowed?
  resolve: (result: R | undefined) => void;   // promise resolver for imperative API
  triggerEl: HTMLElement | null;     // focus restoration target
}
type DialogStack = DialogInstance[];  // last = topmost/active
```

The **stack** is the core state: opening pushes, closing pops and resolves its promise. `triggerEl` (the element focused when the dialog opened) is stored so focus returns exactly there on close — losing this is the most common a11y regression.

## 4. Interface

**Two APIs.** Declarative for content modals; imperative for confirmations:

```tsx
// Declarative
<Dialog open={open} onClose={setClosed} aria-labelledby="t">
  <Dialog.Title id="t">Delete project?</Dialog.Title>
  <Dialog.Body>This can't be undone.</Dialog.Body>
  <Dialog.Footer>{/* buttons */}</Dialog.Footer>
</Dialog>

// Imperative (promise-based) — reads like a native confirm(), works from anywhere
const ok = await dialogs.confirm({ title: 'Delete project?', danger: true });
if (ok) deleteProject();
```

The imperative promise API is the detail worth stealing: `openDialog` returns a promise that resolves with the result when the dialog closes, so callers write linear code instead of threading callbacks and open-state. Compound sub-components (`Dialog.Title` wired to `aria-labelledby`) make the a11y contract hard to get wrong ([[29 - Frontend System Design/07 - Component API Design|Component API Design]]).

## 5. Optimizations (ranked)

1. **Accessibility (APG dialog)** — `role="dialog"` + `aria-modal="true"`, labelled by title (`aria-labelledby`); **focus trap** while open, **focus restore** to `triggerEl` on close; Escape closes (if dismissable); background `inert`. Native `<dialog>`'s `showModal()` gives trap + top-layer + backdrop for much of this — prefer it, polyfill the gaps.
2. **Scroll lock** — prevent background scroll without layout shift (compensate for scrollbar width); restore on close. A jumping page on open is the classic bug.
3. **Stacking** — z-index/top-layer ordering, only the top dialog interactive, Escape closes the top only.
4. **Rendering/animation** — mount on open, keep in DOM during exit animation then unmount; `prefers-reduced-motion` respected ([[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|reduced motion]]).
5. **Resilience** — SSR-safe portal (create target on mount), route-change closes open dialogs, focus never lost to a hidden element.

## 6. Interview Answer

Short answer:

> A modal system is a provider holding a stack of dialogs, rendered through a portal to the body so it escapes overflow and z-index traps. The core is the APG dialog contract: `aria-modal`, focus trap while open, focus restored to the trigger on close, Escape to dismiss, and the background marked inert. I expose two APIs — declarative compound components for content modals and a promise-based imperative `confirm()` for confirmations so callers write linear code. Scroll-lock without layout shift and correct stacking round it out.

Deeper answer:

> The decisions I'd defend: portal plus inert background, because inline rendering gets clipped by ancestor overflow/transform and `aria-hidden` alone still lets focus tab behind the modal. Storing the trigger element for focus restoration, because returning focus exactly where it left is the a11y detail people miss. And the promise-based imperative API, because confirmation flows are painful with callback+state threading — `const ok = await confirm()` reads like the native primitive. I'd lean on native `<dialog>`'s `showModal()` for the top-layer, backdrop, and trap, and only hand-build what it doesn't cover, because reimplementing a focus trap correctly is deceptively hard.

## 7. Practice

1. <details><summary>Why render a modal in a portal, and what breaks without one?</summary>A portal moves the DOM node to the body so it escapes ancestor `overflow:hidden`, `transform`, and `z-index` stacking contexts that would clip or mis-layer it — while keeping it in the React tree for context/events. Rendered inline inside a scrolled or transformed container, the modal gets clipped or positioned wrong.</details>
2. <details><summary>What are the two focus responsibilities of a modal, and the bug if you skip each?</summary>Trap focus inside while open (skip → keyboard users tab into the page behind, lost), and restore focus to the triggering element on close (skip → focus jumps to `<body>`, disorienting screen-reader/keyboard users). Store the trigger element on open; `inert` on the background enforces the trap.</details>
3. <details><summary>Why a promise-based imperative API for confirmations?</summary>Confirmation is inherently sequential — "ask, then act on the answer." A promise (`const ok = await confirm()`) expresses that linearly, versus managing open state and threading an `onConfirm` callback through components. It mirrors the native `confirm()` ergonomics while staying non-blocking and accessible.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|Dialogs, Menus, Popovers and Focus Traps]]
- [[21 - React Internals and Patterns/16 - Synthetic Events and Portals|Synthetic Events and Portals]]
- [[29 - Frontend System Design/16 - Designing a Notification and Toast System|Designing a Notification and Toast System]]
- [[29 - Frontend System Design/07 - Component API Design|Component API Design]]
