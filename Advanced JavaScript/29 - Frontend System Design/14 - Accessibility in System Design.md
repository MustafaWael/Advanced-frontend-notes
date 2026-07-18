---
tags: [system-design, interview, accessibility, aria, apg]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [a11y in design, APG patterns, accessible components design]
---

# Accessibility in System Design

## Maturity Target

- Priority: #must-know
- Study time: 40 minutes
- Interview signal: Treat accessibility as a first-class design requirement — the right APG pattern, focus management, and announcements appear in your design unprompted, not as an afterthought.
- Production signal: Components ship with keyboard + screen-reader support built into the API, so consumers can't forget it.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[25 - Accessibility and Inclusive UX/00 - Accessibility and Inclusive UX MOC|Accessibility and Inclusive UX MOC]]

## Source Anchors

- [WAI-ARIA Authoring Practices Guide (APG)](https://www.w3.org/WAI/ARIA/apg/patterns/)
- [WCAG 2.2 Quick Reference](https://www.w3.org/WAI/WCAG22/quickref/)
- [MDN — ARIA](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA)

## 1. Concept

Simple version: in a design round, accessibility is a requirement you raise yourself and design *into* the architecture — not a checklist bolted on at the end. The mechanics live in module 25; this is the *design-decision* lens.

What "designing for a11y" means at the system level:

- **Pick the APG pattern early** — most widgets have a canonical one: combobox (autocomplete), dialog (modal), listbox/menu, tabs, disclosure, carousel, and — for data tables — a *decision* between a native `<table>` and the APG **grid** pattern (grid only when cells are interactively navigable/editable; it replaces native table semantics, so a read-mostly table should stay a plain `<table>` — see [[29 - Frontend System Design/17 - Designing a Data Table|Designing a Data Table]]). The pattern dictates roles, states, and the full **keyboard interaction model** (arrow keys, Home/End, Escape, type-ahead). Naming it up front means the a11y contract is designed, not retrofitted.
- **Focus management** — where does focus go on open/close/route-change/delete? Focus trap in modals, restore focus to the trigger on close, move focus to new content or a heading on navigation ([[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|focus traps]]).
- **Virtual vs DOM focus** — composite widgets (combobox, grid) keep DOM focus in one place and move a *virtual* cursor via `aria-activedescendant`, so screen readers track selection without losing the input.
- **Announcements** — dynamic changes (results loaded, item added, error) need `aria-live` regions, choreographed so they inform without spamming ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|live regions]]).
- **Semantics first** — native elements (`<button>`, `<dialog>`, `<nav>`) carry behavior and a11y for free; reach for ARIA only to fill gaps ([[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|semantic HTML before ARIA]]).
- **Bake it into the component API** — a headless/compound component that owns the ARIA pattern and keyboard model means every consumer gets it right by default ([[29 - Frontend System Design/07 - Component API Design|Component API Design]]).

> [!tip] The interview signal isn't reciting WCAG — it's that a11y appears *in the architecture*: "this is a combobox, so the design owns `aria-activedescendant` virtual focus and the arrow-key model," or "the modal traps focus and restores it to the trigger." Unprompted and specific beats a generic "and I'd make it accessible."

## 2. Why It Matters

Product/UX sense is a graded evaluation axis, and a11y is its clearest expression. The failure mode is treating it as a final checklist ("I'd add ARIA labels") instead of a design input that shapes the component's roles, keyboard model, and focus flow. Building it into the component API is also the only way it survives in a real design system — consumers who *can't* forget it.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a custom dropdown built from `<div>`s looks right but is unusable by keyboard and screen-reader users — you can't tab to it, arrows don't move options, and screen readers announce nothing.

Trace: no APG pattern was designed in. Divs have no role, no focusability, no keyboard behavior; nothing maps to the **listbox/combobox** pattern the widget actually is. This is the a11y version of skipping the design step — retrofitting it now means reworking structure and interaction.

Fix: design to the APG pattern — `role="combobox"` on the input, `role="listbox"`/`option` for the menu, `aria-expanded`, `aria-activedescendant` for virtual focus, and the full keyboard model (↑↓ to move, Enter to select, Esc to close, type-ahead). Better: use a semantic `<select>` or a headless library that ships the pattern, and style it.

Tradeoff: doing the full pattern by hand is real work (keyboard model, virtual focus, announcements), which is why native elements or a headless primitive are usually the right call — you trade some visual control for correctness you don't have to reimplement. Rolling your own is justified only when the design genuinely can't use the native/headless option, and then the a11y cost is part of the estimate.

## 4. Interview Answer

Short answer:

> I make accessibility a requirement and design it in. I name the APG pattern the widget maps to — combobox, dialog, grid — which dictates roles, states, and the keyboard model. I design focus management explicitly: trap and restore in modals, move focus on navigation, virtual focus via `aria-activedescendant` for composite widgets. Dynamic changes get choreographed live-region announcements. And I bake the pattern into the component API so consumers can't ship it broken.

Deeper answer:

> The mechanism that separates a working implementation from a broken one is virtual focus and focus restoration, because they're where naive implementations fail: a combobox must keep DOM focus in the input while moving a virtual cursor through options via `aria-activedescendant`, and a modal must trap focus and return it to the trigger on close or keyboard users get lost. I start from semantic HTML so I inherit behavior for free and add ARIA only to fill gaps — over-ARIA is its own bug. And I put all of this in a headless or compound component that owns the pattern, because in a design system the only accessibility that survives is the kind consumers can't forget.

## 5. Practice

1. <details><summary>What does "design to the APG pattern" give you that adding ARIA labels later doesn't?</summary>The pattern specifies the whole contract — roles, states, and the complete keyboard interaction model (arrows, Home/End, Escape, type-ahead) plus focus behavior. Labels are cosmetic; the pattern is structural. Designing to it up front means the widget is operable and announced correctly by construction, not patched.</details>
2. <details><summary>Why do comboboxes and grids use virtual focus (`aria-activedescendant`) instead of moving real focus?</summary>Moving DOM focus to each option would take focus out of the input (you couldn't keep typing) and thrash the screen reader. Virtual focus keeps real focus in one element and points `aria-activedescendant` at the active option, so the user keeps typing while the screen reader announces the highlighted choice.</details>
3. <details><summary>How do you make accessibility survive in a design system?</summary>Build it into the component API — a headless or compound component that owns the ARIA pattern, keyboard model, and focus management, so every styled consumer inherits correct behavior by default. Accessibility left to each consumer's discipline is the accessibility that gets forgotten; making it un-forgettable is the design decision.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/00 - Accessibility and Inclusive UX MOC|Accessibility and Inclusive UX MOC]]
- [[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|Dialogs, Menus, Popovers and Focus Traps]]
- [[29 - Frontend System Design/07 - Component API Design|Component API Design]]
- [[29 - Frontend System Design/15 - Designing a Modal and Dialog System|Designing a Modal and Dialog System]]
