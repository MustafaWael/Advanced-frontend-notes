---
tags: [accessibility, aria]
module: "25 - Accessibility and Inclusive UX"
priority: must-know
status: not-started
aliases: [ARIA, accessibility tree, accessible name]
---

# ARIA: Roles, Names and States

## Maturity Target

- Priority: #must-know
- Study time: 60 minutes
- Interview signal: explain the accessibility tree, how accessible names are computed, and the rules for when ARIA helps versus harms.
- Production signal: every ARIA attribute in your codebase is justifiable; none contradict native semantics or promise unimplemented behavior.
- Dependencies: [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]]

## Source Anchors

- [WAI-ARIA 1.2 specification](https://www.w3.org/TR/wai-aria-1.2/)
- [WAI-ARIA Authoring Practices Guide (APG)](https://www.w3.org/WAI/ARIA/apg/)
- [W3C: Using ARIA (the five rules)](https://www.w3.org/TR/using-aria/)
- [MDN: Accessibility tree](https://developer.mozilla.org/en-US/docs/Glossary/Accessibility_tree)
- [W3C: Accessible Name and Description Computation](https://www.w3.org/TR/accname-1.2/)

## 1. Concept

The browser builds an **accessibility tree** parallel to the DOM: each node exposes a **role** (what kind of thing — button, heading, textbox), a **name** (what it's called — "Save", "Email"), optionally a **description**, and **states/properties** (checked, expanded, disabled, invalid). Assistive tech consumes this tree, not your pixels. All accessibility work is, mechanically, *getting the right things into this tree* — semantic HTML does it implicitly; ARIA attributes write to it directly.

**Names are computed by an algorithm** (accname), roughly in priority: `aria-labelledby` (points at other elements' text) → `aria-label` (literal string) → native mechanisms (`<label>`, alt, `<caption>`, button text content) → title. Practical consequences: `aria-label` *overrides* visible text (a button showing "Send" with `aria-label="Submit form"` is announced "Submit form" — and breaks voice-control users who say "click Send"); and icon-only buttons need *some* naming mechanism or they're announced as "button" with no clue.

**ARIA's contract is one-way.** It changes what AT *hears*, never what the element *does*. `role="button"` doesn't add keyboard handling; `aria-expanded="true"` doesn't expand anything; `aria-checked` doesn't check. You are writing claims into the tree, and the [five rules of ARIA use](https://www.w3.org/TR/using-aria/) exist because false claims are worse than none:

1. Don't use ARIA if a native element/attribute does it.
2. Don't change native semantics (no `role="button"` on `<h2>` — wrap or restructure instead).
3. All interactive ARIA roles require you to implement their full keyboard behavior (per [APG patterns](https://www.w3.org/WAI/ARIA/apg/)).
4. Don't use `role="presentation"`/`aria-hidden="true"` on focusable elements (invisible-but-tabbable ghosts).
5. All interactive elements must have an accessible name.

Where ARIA is *genuinely required*: states native HTML can't express (`aria-expanded` on a disclosure button, `aria-current="page"` in nav, `aria-selected` on tabs), relationships (`aria-describedby`, `aria-controls`, `aria-activedescendant`), live regions ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|announcements]]), and composite widgets with no native equivalent (combobox, tree, tablist).

## 2. Why It Matters

- WebAIM's annual million-page survey has found for years that **pages using ARIA average more detected errors than pages without it** — misapplied ARIA is that common. "No ARIA is better than bad ARIA" is the APG's own opening warning.
- Interviews probe ARIA to detect cargo-culting: candidates who spray `aria-label` everywhere versus those who know the tree, the name computation, and the one-way contract.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a "helpful" pass added ARIA everywhere; a screen-reader user reports the nav is *worse* than before.

```tsx
// Bug: every attribute here is wrong, and each was added with good intentions
<nav aria-label="Navigation">
  <ul role="list">
    <li role="listitem">
      <a href="/docs" role="button" aria-label="Click here to open the documentation page">
        Docs
      </a>
    </li>
    <li aria-hidden="true">                {/* "decorative separator", but... */}
      <a href="/pricing">Pricing</a>       {/* ...still tabbable: a focusable ghost */}
    </li>
  </ul>
</nav>
```

Trace: `role="button"` on a link makes AT announce a button that navigates (breaking user expectations — Space won't work either); the verbose `aria-label` overrides "Docs" so voice-control "click Docs" fails and every listing is noise ("Click here to open…"); `aria-hidden` on a subtree containing a focusable link creates a stop where the screen reader says *nothing* (rule 4); and the redundant `role="list"`/`listitem"` restate what `<ul>/<li>` already expose.

```tsx
// Fix: almost no ARIA — the platform was already doing the work
<nav aria-label="Main">                    {/* justified: distinguishes this nav landmark from footer nav */}
  <ul>
    <li><a href="/docs" aria-current={isDocs ? "page" : undefined}>Docs</a></li>
    <li><a href="/pricing" aria-current={isPricing ? "page" : undefined}>Pricing</a></li>
  </ul>
</nav>
```

Two ARIA attributes survive, each doing something HTML can't: `aria-label="Main"` names the landmark (useful when multiple `<nav>`s exist), `aria-current="page"` exposes the visually-highlighted current item to AT.

Tradeoffs: the discipline of justifying every attribute costs review attention — encode it in lint (`eslint-plugin-jsx-a11y` catches role misuse, redundant roles, aria-hidden-on-focusable) and in component primitives so product code rarely writes raw ARIA at all. When a design system's `<Tabs>`/`<Dialog>`/`<Combobox>` own the APG contract, feature developers inherit correctness.

> [!tip] Reading the tree beats guessing
> Browser devtools expose the accessibility tree (Chrome: Elements → Accessibility pane; full-page tree toggle). When debugging "what will this announce," inspect the computed role, name, and states directly — it shows the accname algorithm's actual result, including surprises like an `aria-label` silently overriding your visible text, or a div flattening its children's semantics.

## Real-World Use Cases

### Notification bell whose name carries the count

A header bell icon shows a badge with "3". Visually: icon plus number. In the tree, an icon-only button with a stray "3" — announced as "button, 3" at best. The name should carry the whole message:

```tsx
<button aria-label={unread ? `Notifications, ${unread} unread` : "Notifications"}>
  <BellIcon aria-hidden="true" />
  {unread > 0 && <span className="badge" aria-hidden="true">{unread}</span>}
</button>
```

Works because the accname algorithm takes `aria-label` over content — so the visual badge is hidden from the tree (`aria-hidden` on both icon and badge) and the computed name is the complete sentence. The count updating is *not* a live region concern here; users query the button when they visit it ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|push vs query]]).

### Theme toggle: `aria-pressed` vs swapping the label

A "Dark mode" toggle button has two implementation camps, and mixing them is the bug:

```tsx
// State-based: name stays constant, state changes
<button aria-pressed={isDark} onClick={toggle}>Dark mode</button>
// announced: "Dark mode, toggle button, pressed"

// Label-based: name describes the action it will perform
<button onClick={toggle}>{isDark ? "Switch to light mode" : "Switch to dark mode"}</button>
```

Both are valid; combining them ("Switch to light mode, pressed") is contradictory noise. The mechanism: `aria-pressed` writes a *state* into the tree next to a stable *name* — pick one channel for the information. Same discipline applies to mute buttons, follow buttons, favorite stars.

> [!warning]
> A follow button that swaps its label to "Following" *and* keeps `aria-pressed={false}` (because someone copied a snippet) makes two claims that disagree — AT users can't tell which to trust. Lint can't catch this; review must.

### Autocomplete search with `aria-activedescendant`

A site-wide search shows a suggestions listbox under the input. Focus must *stay in the input* (the user is still typing), yet arrow keys visually highlight suggestions — so how does AT know which one is active? This is exactly what `aria-activedescendant` exists for:

```tsx
<input role="combobox" aria-expanded={open} aria-controls="suggestions"
       aria-activedescendant={activeId ?? undefined}
       onKeyDown={moveActiveWithArrows} />
<ul id="suggestions" role="listbox">
  {items.map(item => (
    <li key={item.id} id={`opt-${item.id}`} role="option"
        aria-selected={activeId === `opt-${item.id}`}>{item.label}</li>
  ))}
</ul>
```

Works because `aria-activedescendant` is a *relationship* attribute: real DOM focus never leaves the input, but the tree reports the referenced option as the active element, so AT announces each highlighted suggestion. This is rule 3 territory — claiming `combobox`/`listbox` obligates the full APG keyboard map (arrows, Enter, Escape), which is why teams should buy this widget from a headless library rather than hand-roll it ([[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|popovers and menus]]).

### `aria-sort` on a sortable invoice table

The admin table from [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML]] sorts by column. Sighted users see the arrow flip; the tree needs the same fact:

```tsx
<th scope="col" aria-sort={key === sortKey ? (dir === "asc" ? "ascending" : "descending") : undefined}>
  <button onClick={() => toggleSort(key)}>
    Amount{key === sortKey && <span className="sr-only">, sorted {dir}</span>}
  </button>
</th>
```

`aria-sort` is a textbook "state HTML can't express": the platform has no sorted-column attribute, the visual arrow is paint, and the attribute goes on the `<th>` (only one per table should carry it). Announce the *result* of re-sorting via the caption or a polite status ("Sorted by amount, descending"), since `aria-sort` changes alone aren't reliably announced.

## 4. Interview Answer

Short answer:

> The browser exposes an accessibility tree of roles, names, and states; assistive tech reads that tree. Semantic HTML populates it correctly for free; ARIA writes to it directly — but only the announcement side, never behavior: `role="button"` adds no keyboard handling, `aria-expanded` expands nothing. So the rules: prefer native elements; never contradict native semantics; if you claim an interactive role, implement its full APG keyboard contract; never hide focusable content; name every control. ARIA earns its place for states HTML can't express — `aria-expanded`, `aria-current`, live regions — and for composite widgets with no native equivalent.

Deeper answer:

> Accessible names come from a defined computation — `aria-labelledby`, then `aria-label`, then native (label/text/alt) — with the practical traps that `aria-label` overrides visible text (breaking voice control when they diverge) and icon buttons need explicit names. The empirical case for restraint: WebAIM's surveys repeatedly find ARIA-using pages average more errors — false claims in the tree are worse than missing ones, because users act on them. Operationally I keep raw ARIA out of product code: design-system primitives own the APG contracts, jsx-a11y lint catches misuse, and devtools' accessibility pane settles "what does this actually announce" debates with the computed tree instead of folklore.

## 5. Practice

1. <details><summary>An icon-only delete button: name three ways to give it an accessible name and rank them.</summary>(1) Visually-hidden text child (`<button><TrashIcon aria-hidden /><span className="sr-only">Delete invoice</span></button>`) — best: name lives in content, works everywhere, translatable, no divergence risk. (2) `aria-label="Delete invoice"` — fine and common; slightly riskier (can drift from a future visible label, bypassed by some translation tools). (3) `aria-labelledby` pointing at existing text — best when a name already exists elsewhere (row's invoice number: "Delete invoice 4021" via two ids). Never: `title` alone (unreliable) or nothing.</details>

2. <details><summary>Why is `aria-expanded` on the *button* (not the panel) the correct pattern for a disclosure, and what else does the pattern require?</summary>The state describes the *control* the user is on: focused on the button, they hear "Settings, button, collapsed" — actionable information at the decision point. The panel isn't where focus is when the question matters. Full pattern: button (real `<button>`) with `aria-expanded={open}` and optionally `aria-controls={panelId}`; the panel simply exists/hides. No `role` gymnastics needed — this is the APG disclosure pattern, the simplest composite and the template for menus/comboboxes' expanded states.</details>

3. <details><summary>What's the difference between `aria-hidden="true"`, `role="presentation"`, and `display: none` in tree terms?</summary>`display: none` removes the element from rendering *and* the accessibility tree (and tab order) — fully gone for everyone. `aria-hidden="true"` removes the subtree from the accessibility tree only — still visible and (bug!) still focusable if it contains interactive elements. `role="presentation"` removes the element's *semantics* (a table used for layout stops being a table) but keeps its content in the tree. Use each for its meaning: hide-for-all (display), decorative-for-AT (aria-hidden on icons), semantics-removal (presentation, rarely).</details>

4. <details><summary>Your PR reviewer asks why you added `role="alert"` instead of `role="status"` to the save-failure message. Defend the choice and its cost.</summary>`role="alert"` is an assertive live region: it interrupts the user's current announcement — justified for a failure that blocks their task (their save didn't happen and they may navigate away believing it did). `role="status"` is polite — queued until current speech finishes — right for non-blocking confirmations ("Draft saved"). Cost of assertive: interruption is hostile if overused; a chatty app of alerts trains users to ignore them. Rule: assertive for actionable failures, polite for everything else ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|live regions]]).</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]]
- [[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|Dialogs, Menus, Popovers and Focus Traps]]
- [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions, Loading States and Announcements]]
- [[24 - Testing and Quality/09 - Accessibility Testing|Accessibility Testing]]
