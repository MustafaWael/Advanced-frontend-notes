---
tags: [accessibility, checklist]
module: "25 - Accessibility and Inclusive UX"
priority: must-know
status: not-started
---

# Accessibility Checklist

Use this checklist as an active test. Mark an item complete only when you can explain, predict, debug, and refactor without looking.

## Source Anchors

- [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/)
- [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WAI: Easy Checks](https://www.w3.org/WAI/test-evaluate/preliminary/)

## Semantics and Structure

- [ ] I can list what `<button>` provides that a div-with-handler doesn't, and the five-part cost of rebuilding it.
- [ ] I apply the decision procedure: native element → extend native → only then ARIA + APG pattern.
- [ ] I keep heading levels structural (outline), landmarks meaningful, and links vs buttons honest.

## Keyboard and Focus

- [ ] I can state the only two safe `tabindex` values and why positive values are bugs.
- [ ] I can implement roving tabindex for a composite widget.
- [ ] I can name the focus destination after: dialog open/close, item deletion, SPA route change.
- [ ] My focus styles use `:focus-visible` and never silently remove the indicator.

## Forms and Async

- [ ] Every field I ship has a programmatic label, and errors/hints are wired via `aria-describedby` + `aria-invalid`.
- [ ] I can build the focusable error-summary pattern for server-side failures.
- [ ] My pending states stay focusable (`aria-disabled` + text change) instead of ejecting keyboard users.
- [ ] Async outcomes — loading past a threshold, results, failures — are announced at the right politeness.

## ARIA and Widgets

- [ ] I can recite the five rules of ARIA use and explain "no ARIA is better than bad ARIA" with the WebAIM data.
- [ ] I can explain the accessibility tree and how accessible names are computed (labelledby → label → native).
- [ ] I can state the full modal contract and what `showModal()`/popover/`inert` each provide.
- [ ] I can argue disclosure-of-links vs `role="menu"` for a nav dropdown.

## Content and Visual

- [ ] I can run the alt decision tree (informative/functional/decorative) and explain `alt=""` vs missing alt.
- [ ] I can mark up a data table AT can navigate: caption, `th` scope, `aria-sort`.
- [ ] I know the numbers: 4.5:1 / 3:1 contrast, 200% text, 400% zoom → 320px reflow, no `maximum-scale=1`.
- [ ] Color never carries meaning alone in my UIs; motion respects `prefers-reduced-motion` by default.

## Testing

- [ ] I can state what axe catches vs what only manual passes find, with examples of each.
- [ ] I can run the 10-minute keyboard protocol and the 20-minute screen-reader protocol from memory.
- [ ] I encode manual findings as automated behavioral regression tests (focus, names, announcements).
- [ ] I never claim automated-green means accessible.

## Exit Test

- [ ] Fix the inaccessible async form: placeholder-labels, unassociated errors, disabled-while-pending, silent failure — produce the full accessible version and name each mechanism.
- [ ] Fix the div-modal: enumerate its contract violations, then replace it with `<dialog>` and justify what remains hand-wired.
- [ ] Take any feature you built this month and run both manual passes on it. File what you find.
- [ ] Explain to a PM, in three sentences without jargon, why the team tests with keyboards and screen readers.

## Related Notes

- [[25 - Accessibility and Inclusive UX/00 - Accessibility and Inclusive UX MOC|Accessibility and Inclusive UX MOC]]
- [[24 - Testing and Quality/12 - Testing Checklist|Testing Checklist]]
- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
- [[01 - Roadmap|Roadmap]]
