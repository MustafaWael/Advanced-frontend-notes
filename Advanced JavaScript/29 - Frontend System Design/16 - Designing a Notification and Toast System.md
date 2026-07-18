---
tags: [system-design, interview, notifications, toast, accessibility]
module: "29 - Frontend System Design"
priority: important
status: not-started
aliases: [toast system design, notification queue, snackbar design]
verified_on: 2026-07-17
version_scope: "React 18+ useSyncExternalStore and ARIA live-region roles (status/alert) as of 2026"
---

# Designing a Notification and Toast System

## Maturity Target

- Priority: #important
- Study time: 45 minutes
- Interview signal: Design a toast/notification system covering the queue, timing/pause, deduplication, imperative API, and the a11y announcement contract.
- Production signal: Your toasts don't stack infinitely, announce to screen readers, and pause on hover/focus.
- Dependencies: [[29 - Frontend System Design/07 - Component API Design|Component API Design]], [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions, Loading and Announcements]]

## Source Anchors

- [WAI-ARIA APG — Alert & aria-live](https://www.w3.org/WAI/ARIA/apg/patterns/alert/)
- [MDN — ARIA live regions](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/ARIA_Live_Regions)

## 1. Requirements

Ask: transient toasts, persistent notifications, or both? max visible at once? auto-dismiss timing and does it pause on hover/focus? priority levels (error sticky, info auto-dismiss)? dedup repeated messages? actionable (undo button)? position? imperative `toast(...)` from anywhere including outside React?

Design against: **transient toasts with priority levels, a capped visible queue, hover/focus-pause, dedup, optional action button, imperative API callable from anywhere, fully announced.** Out of scope: a notification inbox/history (mention as an extension).

## 2. Architecture

```
notify(msg)  ──▶  Toast store (queue + visible set)  ──▶  <ToastRegion> (Portal)
 (module-level        │ cap visible (e.g. 3), rest queued        │  aria-live region
  singleton, works    │ per-toast timer (pausable)               ├─ <Toast> (role=status/alert)
  outside React)      │ dedup by key                             └─ ...
```

A **module-level store** (observable) is the backbone so `notify()` works from anywhere — event handlers, data-layer error interceptors, even non-React code — not just from components. The `<ToastRegion>` subscribes ([[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]) and renders through a **Portal**. The store **caps the visible count** and queues the overflow, runs a **pausable timer** per toast, and **dedups** by key.

> [!tip] The module-singleton store is what makes `toast.error('Saved failed')` callable from a fetch interceptor or a Zustand action — decoupling notifications from the component tree. It's the Observer pattern ([[31 - Low Level Design/04 - Design Patterns|Design Patterns]]) doing real work.

## 3. Data Model

```ts
interface Toast {
  id: string;
  key?: string;                 // dedup identity ("network-error")
  type: 'info' | 'success' | 'error';
  message: ReactNode;
  action?: { label: string; onClick: () => void };
  duration: number | null;      // null = sticky (errors)
  createdAt: number;
  remaining: number;            // ms left, frozen while paused
}
interface ToastState { visible: Toast[]; queued: Toast[]; }  // visible capped
```

Timer state (`remaining`) lives in the store, not a raw `setTimeout` id alone, so hover/focus can **pause and resume** by freezing/restoring `remaining` — a `setTimeout` you can't inspect makes pause-on-hover impossible to do correctly.

## 4. Interface

```ts
// Imperative, ergonomic, works anywhere
const id = toast.error('Upload failed', { action: { label: 'Retry', onClick: retry } });
toast.dismiss(id);
toast.promise(saveDraft(), { loading: 'Saving…', success: 'Saved', error: 'Save failed' });
```

The imperative API is the primary interface (unlike most components) because notifications are fire-and-forget from imperative code. `toast.promise` is a senior convenience — bind a toast's lifecycle to a promise. Provide `<Toaster max position />` for app-level config.

## 5. Optimizations (ranked)

1. **Accessibility** — the region is `aria-live`: `polite` (`role="status"`) for info/success, `assertive` (`role="alert"`) for errors. One persistent live region, toasts inserted into it, so screen readers announce without stealing focus. Toasts must be reachable/dismissable by keyboard; never *only* auto-dismiss critical info (screen-reader users may miss a 4s toast — errors are sticky).
2. **Timing correctness** — pause on hover **and** keyboard focus; resume on leave/blur; pause the whole stack while any is hovered. Respect `prefers-reduced-motion` for enter/exit.
3. **Queue discipline** — cap visible (avoid a wall of toasts), dedup by key (a flapping network error shows once with a count, not fifty), promote queued as visible ones dismiss.
4. **Rendering** — portal, stable keys, exit animation before unmount; virtualization irrelevant (few visible).
5. **Resilience** — errors sticky with manual dismiss; actions (undo) have enough time or are sticky; toasts survive route changes.

## 6. Interview Answer

Short answer:

> A toast system is a module-level observable store plus a portal-rendered live region. The store is a singleton so `notify()` works from anywhere, including non-React code; it caps the visible count and queues overflow, dedups by key, and runs a pausable per-toast timer. Accessibility is the core: a persistent `aria-live` region — polite for info, assertive for errors — so toasts announce without stealing focus, and errors are sticky because a screen-reader user can miss a timed toast.

Deeper answer:

> Two decisions I'd defend: the module-singleton store, because notifications originate from imperative code — a fetch interceptor, a store action — so coupling them to a component's state would force awkward plumbing; an observable the region subscribes to via `useSyncExternalStore` decouples cleanly. And storing `remaining` time rather than a bare timeout, because correct pause-on-hover/focus needs to freeze and resume the countdown, and you can't do that with an opaque `setTimeout`. On a11y I'd be specific: one persistent live region reused for all toasts (not a new region per toast, which screen readers miss), assertive only for errors, and never auto-dismiss critical messages.

## 7. Practice

1. <details><summary>Why a module-level store instead of React state for toasts?</summary>Notifications are triggered from imperative, often non-component code — fetch error interceptors, global store actions, event handlers. A module-level observable store lets `toast()` be called from anywhere and have the UI subscribe (via `useSyncExternalStore`), whereas React state would require routing every trigger through the component tree.</details>
2. <details><summary>How do you implement pause-on-hover correctly, and why does a raw setTimeout fail?</summary>Track `remaining` ms in state; on hover/focus, clear the timeout and freeze `remaining`; on leave/blur, restart with the frozen value. A bare `setTimeout` id can't tell you how much time is left, so you can't resume accurately — you'd restart the full duration or lose the pause. Pause the whole stack while any toast is hovered.</details>
3. <details><summary>What's the a11y contract, and why are errors sticky?</summary>Use a persistent `aria-live` region — `polite`/`role=status` for info, `assertive`/`role=alert` for errors — reused for all toasts so screen readers announce insertions without focus theft. Errors (and actionable toasts) are sticky because a timed auto-dismiss can vanish before a screen-reader or distracted user perceives it, losing critical information.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions, Loading and Announcements]]
- [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]
- [[29 - Frontend System Design/15 - Designing a Modal and Dialog System|Designing a Modal and Dialog System]]
- [[31 - Low Level Design/04 - Design Patterns|Design Patterns]]
