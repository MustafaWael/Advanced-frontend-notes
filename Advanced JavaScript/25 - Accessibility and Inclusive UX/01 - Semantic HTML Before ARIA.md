---
tags: [accessibility, html, semantics]
module: "25 - Accessibility and Inclusive UX"
priority: must-know
status: not-started
aliases: [semantic HTML, native elements]
---

# Semantic HTML Before ARIA

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: enumerate concretely what `<button>` provides that a click-handling `<div>` doesn't, and why "add ARIA" is the wrong first fix.
- Production signal: your PRs use native elements by default; div-buttons don't survive your review.
- Dependencies: [[19 - DOM and Browser APIs/02 - Event Propagation|Event Propagation]], [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]

## Source Anchors

- [MDN: HTML — a good basis for accessibility](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Accessibility/HTML)
- [WAI ARIA Authoring Practices: No ARIA is better than bad ARIA](https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/)
- [HTML Living Standard: sections and headings](https://html.spec.whatwg.org/multipage/sections.html)
- [MDN: the button element](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button)

## 1. Concept

Native HTML elements ship with accessibility built in. One `<button>` gives you, for free:

- **Role** — exposed as `button` in the accessibility tree, so assistive tech (AT) announces "button" and includes it in button navigation.
- **Keyboard operability** — focusable by Tab, activated by Enter *and* Space, with correct event ordering.
- **Focusability semantics** — participates in tab order; respects `disabled`.
- **State exposure** — `disabled`, and for inputs: checked, value, validity.

A `<div onClick={...}>` gives you none of these. To reconstruct a real button from a div you need `role="button"`, `tabIndex={0}`, a keydown handler for Enter and Space (with `preventDefault` on Space so the page doesn't scroll), disabled-state handling that also blocks the handlers, and focus styling — five things to get right forever, versus zero. Multiply by every menu, checkbox, tab list, and dialog rebuilt from divs, and "we'll fix accessibility later" becomes a rewrite.

The same economics apply to structure: `<nav>`, `<main>`, `<header>`, `<h1>–<h6>`, `<ul>`, `<table>`, `<a href>` create the *landmark and outline structure* screen-reader users navigate by (jump to main, list headings, next link). A div soup has no structure to navigate — the page is a flat wall of text.

The decision procedure:

1. A native element does this → **use it** (`<button>`, `<a href>`, `<input>`, `<select>`, `<details>`, `<dialog>`).
2. A native element *almost* does this → **extend it** (style it; add attributes) rather than rebuild.
3. Nothing native exists (tabs, comboboxes, trees) → **now** ARIA + scripted keyboard per the [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/) ([[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA note]]).

## 2. Why It Matters

- This is the highest-leverage accessibility decision: most WCAG failures in the wild are rebuilt platform features (div-buttons, unlabeled inputs, fake links). Choosing native elements prevents whole categories at zero cost.
- It also pays in non-a11y currency: native elements work before JS hydrates ([[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|hydration gap]]), integrate with forms ([[19 - DOM and Browser APIs/08 - Forms and FormData|FormData]]), and need no maintenance. Testing Library queries find them by role for free ([[24 - Testing and Quality/03 - React Component Testing Through User Behavior|component testing]]).

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a design-system "Card with action" — the whole card is clickable.

```tsx
// Bug: a click-handling div pretending to be interactive
function ProjectCard({ project, onOpen }: Props) {
  return (
    <div className="card" onClick={() => onOpen(project.id)}>
      <h3>{project.name}</h3>
      <p>{project.description}</p>
    </div>
  );
}
```

Trace the failures: keyboard users can't reach it (no tab stop) or activate it (no key handling); screen readers announce nothing interactive — it's a heading and a paragraph; there's no focus indicator; and in tests, `getByRole` finds nothing to click. The information "this opens the project" exists only for mouse users who guess.

```tsx
// Fix: a real link does the job (navigation → <a>; action → <button>)
function ProjectCard({ project }: Props) {
  return (
    <article className="card">
      <h3>
        <Link href={`/projects/${project.id}`} className="card-link">
          {project.name}
        </Link>
      </h3>
      <p>{project.description}</p>
    </article>
  );
}
```

```css
/* Whole-card clickability via CSS, not a div handler */
.card { position: relative; }
.card-link::after { content: ""; position: absolute; inset: 0; }
```

The pseudo-element stretches the link's hit area over the card: mouse users get the same UX, keyboard users get a tab stop with visible focus, AT announces "link, project name," and the semantics are honest — it *is* navigation, so it's an `<a>` (middle-click, open-in-new-tab, and prefetch all work too).

Tradeoffs: the stretched-link pattern makes text inside the card unselectable and nested interactive elements need `position: relative` + higher z-index to stay clickable. If the card genuinely needs multiple actions, don't make the whole card a single control — one primary link plus explicit buttons beats a clickable region with surprise targets.

> [!warning] "role='button'" is not the fix — it's step one of five
> Adding `role="button"` to a div changes only the *announcement*. It does not add focusability, key handling, or state. AT users now hear "button" for an element their keyboard cannot operate — arguably worse than no role, because it promises behavior that isn't there. If you must build on a div (a constraint worth challenging), implement the entire contract: role, tabindex, Enter+Space, disabled semantics, focus styles.

## Real-World Use Cases

### FAQ accordion with `<details>` instead of a disclosure widget

A marketing site needs collapsible FAQ items. The reflex is a `useState`-driven div with a chevron — but this is decision-procedure step 1: a native element already does it.

```tsx
function FaqItem({ question, answer }: FaqProps) {
  return (
    <details className="faq-item">
      <summary>{question}</summary>
      <p>{answer}</p>
    </details>
  );
}
```

Works because `<details>/<summary>` ship the whole disclosure contract natively: `summary` is a focusable button-like control, Enter/Space toggle, the expanded state is exposed to AT, and it works with zero JS — including before hydration ([[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|hydration gap]]).

> [!tip]
> Style the marker with `::details-content` and `summary::marker` (or `list-style: none` + your own icon); need exclusive-open accordion behavior? `<details name="faq">` groups them natively — still no state code.

### Sortable data table: extend `<table>`, don't rebuild it

An admin dashboard shows invoices with sortable columns. Div-grids lose everything `<table>` provides: AT users get row/column context ("row 3 of 40, Amount column: $120") and table-navigation commands only from real table semantics.

```tsx
<table>
  <caption className="sr-only">Invoices, sorted by {sortLabel}</caption>
  <thead>
    <tr>
      <th scope="col" aria-sort={sortKey === "amount" ? sortDir : undefined}>
        <button onClick={() => toggleSort("amount")}>Amount</button>
      </th>
      {/* ... */}
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
```

This is decision step 2 — *extend* the native element: real `<th scope>` gives header association for free; the sort button and `aria-sort` are the only additions ([[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA]] earning its place on top of semantics, not instead of them).

> [!warning]
> `display: flex` or `display: grid` on `<tr>`/`<td>` can strip table semantics from the accessibility tree in some browsers — a purely visual refactor silently demotes the table to div soup. Check the accessibility pane after restyling tables.

### Skip link plus landmarks in a Next.js root layout

Every page starts with the same header and 40-link nav. Keyboard users pay that toll on every page unless the layout provides structure to skip by.

```tsx
// app/layout.tsx
<body>
  <a href="#main" className="skip-link">Skip to main content</a>
  <header>…</header>
  <nav aria-label="Main">…</nav>
  <main id="main">{children}</main>
  <footer>…</footer>
</body>
```

Works because landmarks (`<main>`, `<nav>`, `<header>`) are what screen readers jump between, and the skip link — an ordinary `<a href="#fragment">`, first in DOM order, visually hidden until focused — serves sighted keyboard users who can't use the landmark shortcuts. One layout file, every page inherits it ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|tab order]]).

### Native `<select>` vs custom dropdown in a filter bar

A product-list filter needs a "Sort by" control. The design comp shows a styled dropdown; the team debates building a custom listbox. The decision procedure says: does `<select>` do this? Yes — it's a single-choice picker, and it brings free keyboard support (type-ahead, arrows, Home/End), mobile-native pickers, and form participation ([[19 - DOM and Browser APIs/08 - Forms and FormData|FormData]]).

```tsx
<label htmlFor="sort">Sort by</label>
<select id="sort" value={sort} onChange={e => setSort(e.target.value)}>
  <option value="newest">Newest</option>
  <option value="price-asc">Price: low to high</option>
</select>
```

The custom rebuild is justified only when the requirement is something `<select>` can't express — option images, multi-column layout, async search — and then it's the full APG combobox contract, not a styled div (step 3 of the procedure — [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA]], budgeted per [[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|manual checks]]).

## 4. Interview Answer

Short answer:

> Native elements ship the full accessibility contract — role in the accessibility tree, keyboard focus and activation, state exposure — so a `<button>` is accessible by default while a click-handling div is invisible to keyboards and screen readers. My decision procedure: use the native element; if it almost fits, extend it; only when nothing native exists (tabs, combobox) do I reach for ARIA plus scripted keyboard handling per the Authoring Practices. Most real-world accessibility failures are rebuilt platform features, so this one habit prevents whole categories.

Deeper answer:

> The div-button illustrates the cost precisely: reconstructing `<button>` needs role, tabindex, Enter and Space handling with correct preventDefault, disabled semantics that also block handlers, and focus styling — five permanent maintenance burdens replacing zero. Semantics also create the navigation structure AT relies on — landmarks, heading outline, lists, link collections — which no ARIA sprinkling can retrofit onto div soup. And it compounds beyond a11y: native controls work pre-hydration, participate in forms and native validation, and are queryable by role in tests, so the accessible version is also the more robust and more testable one.

## 5. Practice

1. <details><summary>`<a href>` vs `<button>` — what's the rule, and why does styling one as the other not change it?</summary>Links navigate (URL changes, works with middle-click/new-tab/history); buttons perform actions (submit, toggle, open dialog). AT announces them differently and users form expectations: Enter activates links; Enter and Space activate buttons. Styling is irrelevant to the contract — a button styled as a link still acts in the action register. The bug pattern is `<a href="#" onClick>`: it pollutes history, scrolls to top, and lies about its nature; if it doesn't navigate, it's a button.</details>

2. <details><summary>Why does heading structure (h1–h6, in order, no skips for styling) matter functionally, not just stylistically?</summary>Screen-reader users navigate by heading list/level jumps (e.g., H to next heading, 2 for next h2) — the outline is their table of contents and primary scanning mechanism. Choosing `<h4>` because it "looks right" inside a card breaks the outline: the card appears nested under a nonexistent h3. Style with CSS, structure with levels. This also feeds SEO and the reader-mode parsers.</details>

3. <details><summary>You inherit a `<div className="checkbox" onClick={toggle}>`. Sketch the native replacement including the label, and name what you delete.</summary>`<label><input type="checkbox" checked={checked} onChange={toggle} /> Send me updates</label>`. Deleted: the role announcement problem, tabindex, Space-key handler, aria-checked bookkeeping, focus-style special-casing, and the test's `data-testid` (now `getByRole("checkbox", { name: /updates/i })`). Gained: label-click toggling, form participation ([[19 - DOM and Browser APIs/08 - Forms and FormData|FormData]]), native validity. Style the native input with CSS (`accent-color`, or the appearance-none + pseudo-element technique) — visual polish never required the div.</details>

4. <details><summary>When is building a custom control genuinely justified, and what's the checklist before starting?</summary>When no native element expresses the interaction (combobox with async options, tab panels, tree view) or a native one is irreparably unstylable for a hard requirement (rare — check `appearance`, `::picker`, `<selectedcontent>` era CSS first). Before building: read the WAI-ARIA Authoring Practices pattern for the widget (roles, states, full keyboard map), plan the focus behavior ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|roving tabindex]]), and budget for testing with a real screen reader ([[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|manual checks]]). If that budget isn't available, the native element's styling limits win.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|Keyboard Interaction and Focus Management]]
- [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|ARIA: Roles, Names and States]]
- [[19 - DOM and Browser APIs/08 - Forms and FormData|Forms and FormData]]
- [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|React Component Testing Through User Behavior]]
