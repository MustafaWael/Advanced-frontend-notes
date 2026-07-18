---
tags: [labs, accessibility, async, search, forms]
module: "90 - Labs"
priority: important
status: not-started
aliases: [accessible search lab]
---

# Lab 03 — Accessible Async Search and Form Flow

Build the vault's flagship integration: a debounced, cancellable search-and-book flow that a keyboard-and-screen-reader user can complete end to end — with the async machinery of modules 08/14/17 and the accessibility contracts of module 25 in one feature.

## Prerequisites

- [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]] · [[08 - Async JavaScript/06 - AbortController|AbortController]] · [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]] · [[29 - Frontend System Design/02 - Designing an Autocomplete|Designing an Autocomplete]] · [[29 - Frontend System Design/14 - Accessibility in System Design|Accessibility in System Design]]
- [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms]] · [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions]] · [[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|Focus Management]]

## Build Brief

Vite + React + TypeScript, MSW as the fake backend (artificial latency + failure switches), Vitest + RTL, `@axe-core/playwright` optional. Product: "find a doctor, book a slot."

1. **Search**: a labeled search input; debounced (300ms) requests; results as a list of doctor cards; result-count announcements ("8 doctors for 'cardio'"); slow-search "Searching…" announcement past 400ms; stale responses impossible (abort or ignore on supersede); error state with retry.
2. **Booking form** (opens from a result): name, email, reason (select), date; client validation + one *server-side* failure mode (slot taken — returned by MSW on a switch); pending state; success confirmation; full error-summary pattern on failure ([[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|forms]]).
3. **Two implementations of the results container**: (a) plain list + separate input (simple, correct), (b) an APG combobox (`role="combobox"`, `aria-expanded`, `aria-activedescendant`, arrow-key navigation). Ship (a) first; attempt (b) only after (a) passes everything — and keep both for comparison.

## Acceptance Criteria

- [ ] Typing "car", pausing, typing "cardio" fires ≤2 requests; out-of-order resolution can never show "car" results after "cardio" ones (prove with a hung-response switch).
- [ ] With eyes closed and a screen reader: you can search, hear the result count, reach a result, open booking, fail validation, *hear* the errors, fix them, submit, and hear the confirmation. This is the lab's defining test.
- [ ] Keyboard-only: every step reachable and operable; focus moves into the booking form on open, to the error summary on failure, to the confirmation on success, back to the trigger on cancel ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|focus destinations]]).
- [ ] Per-keystroke announcements do not exist; loading announcements only past the threshold; routine states are silent ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|choreography]]).
- [ ] The pending submit stays focusable (`aria-disabled`), and double-submit is guarded in the handler.

## Debugging Tasks (create, observe, fix)

1. **The classic race**: remove cancellation, add per-request random latency in MSW, and screen-record the stale-results bug; restore the fix and prove it deterministically in a test ([[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|forced interleaving]]).
2. **The silent failure**: conditionally render the live region *with* the message ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|the injection bug]]); verify with a screen reader that announcements stop; fix with the always-rendered region.
3. **The stale closure**: introduce a `useEffect` handler that reads the query from a stale render ([[14 - JavaScript in React and Next.js/03 - Stale Closures|stale closures]]) so submitting books the *previous* doctor; diagnose from symptoms, then fix.
4. **The focus drop**: make "Cancel booking" unmount the form without a focus destination; observe with the keyboard where you land; fix.

## Testing Expectations

- Deterministic tests for: debounce boundary (fake timers), race (explicit resolution order), abort-on-unmount, error-summary focus, `aria-describedby` wiring, result-count announcement presence ([[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|MSW]], [[24 - Testing and Quality/09 - Accessibility Testing|behavioral a11y assertions]]).
- One axe sweep across states (empty, results, error, form open, form failed).
- The manual protocol from [[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|manual checks]], executed and findings written down. Findings become tests.

## Performance and Security Considerations

- Debounce + abort is also a *load* decision — compute worst-case request rate per typing user with and without it.
- Render the results list efficiently (stable keys — [[21 - React Internals and Patterns/02 - Reconciliation and Keys|keys]]); no re-render of every card per keystroke (check with React DevTools profiler).
- Escape/encode everything user-typed that is echoed ("results for '<query>'") — where would XSS enter ([[20 - Network and Security/05 - XSS|XSS]])? Validate the booking payload shape server-side (MSW handler asserts it) as if the client were hostile.

## Interview Questions

1. Walk the full lifecycle of one keystroke: debounce timer, effect, fetch, abort of the predecessor, state update, announcement. Name every mechanism.
2. Why does the combobox version need `aria-activedescendant` (or roving tabindex) — what problem is DOM-focus-vs-virtual-focus solving?
3. Your announcement fired but the SR said nothing — give three mechanically-distinct causes ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|live regions]]).
4. The PM wants search-as-you-type replaced with instant search (no debounce). Argue costs and the UX/infra tradeoff.

## Retrospective

[[98 - Vault Operations/Templates/Lab Retrospective Template|Template]] — plus: what the eyes-closed run taught you that the code review didn't.

## Related Notes

- [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]
- [[25 - Accessibility and Inclusive UX/00 - Accessibility and Inclusive UX MOC|Accessibility and Inclusive UX MOC]]
- [[24 - Testing and Quality/00 - Testing and Quality MOC|Testing and Quality MOC]]
- [[29 - Frontend System Design/02 - Designing an Autocomplete|Designing an Autocomplete]]
- [[29 - Frontend System Design/09 - Network and API Design for Frontend|Network and API Design for Frontend]]
- [[90 - Labs/00 - Labs MOC|Labs MOC]]
