---
tags: [accessibility, moc, a11y]
module: "25 - Accessibility and Inclusive UX"
priority: must-know
status: not-started
---

# Accessibility and Inclusive UX MOC

This module teaches accessibility as an engineering discipline for React and Next.js work: semantics first, keyboard and focus as core interaction mechanics, ARIA as a scalpel rather than a spray, and testing that acknowledges what automation cannot see. The recurring theme: most accessibility is *using the platform correctly* — native elements, real forms ([[19 - DOM and Browser APIs/08 - Forms and FormData|module 19]]), honest markup — and most inaccessibility is rebuilding platform features out of divs.

## Prerequisites

- [[19 - DOM and Browser APIs/00 - DOM and Browser APIs MOC|DOM and Browser APIs]] — events, focus, and forms are the raw material.
- [[21 - React Internals and Patterns/12 - Controlled vs Uncontrolled Components|Controlled vs Uncontrolled Components]] — form patterns interact with a11y constantly.

## Reading Order

1. [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]] — the 80% solution and why divs-with-handlers fail.
2. [[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|Keyboard Interaction and Focus Management]] — tab order, focus visibility, roving tabindex, SPA route focus.
3. [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms, Validation and Async Errors]] — labels, descriptions, error association, async states.
4. [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA: Roles, Names and States]] — the accessibility tree, the five rules, when not to use it.
5. [[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|Dialogs, Menus, Popovers and Focus Traps]] — the hardest widgets, done with platform help.
6. [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions, Loading States and Announcements]] — making async UI audible.
7. [[25 - Accessibility and Inclusive UX/07 - Images Media Tables and Complex Content|Images, Media, Tables and Complex Content]] — alt decisions, captions, data tables.
8. [[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|Color, Contrast, Motion, Zoom and Reflow]] — the visual and vestibular requirements.
9. [[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|Accessibility Testing and Manual Screen-Reader Checks]] — the protocol that closes the gap automation leaves.
10. [[25 - Accessibility and Inclusive UX/10 - Accessibility Checklist|Accessibility Checklist]] — active self-test.

## You're Done When

- [ ] I reach for a native element first and can justify every ARIA attribute I add.
- [ ] I can make any interactive feature fully keyboard-operable with visible focus and sane order.
- [ ] I can build a form whose validation and async errors are announced and associated, not just displayed.
- [ ] I can build or fix an accessible dialog: focus in, trap, Escape, focus restore, background inert.
- [ ] I can make loading/success/error states perceivable without sight.
- [ ] I can run the manual keyboard and screen-reader protocol and say precisely what automation missed.

## Related Notes

- [[24 - Testing and Quality/09 - Accessibility Testing|Accessibility Testing (automated side)]]
- [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]
- [[17 - Practical Frontend Scenarios/07 - Async Form Submission|Async Form Submission]]
- [[01 - Roadmap|Roadmap]]
