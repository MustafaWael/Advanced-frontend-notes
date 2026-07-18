---
tags: [testing, accessibility, axe]
module: "24 - Testing and Quality"
priority: important
status: not-started
aliases: [axe, a11y testing]
verified_on: 2026-07-12
version_scope: "axe-core 4.x, Playwright 1.5x"
---

# Accessibility Testing

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: state accurately what automated a11y checks cover (a minority of issues), and name the manual checks that cover the rest.
- Production signal: axe runs in CI as a floor; keyboard and screen-reader passes happen on every interactive feature before ship.
- Dependencies: [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]], [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|Component Testing]]

## Source Anchors

- [axe-core: rule descriptions](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
- [Playwright: Accessibility testing](https://playwright.dev/docs/accessibility-testing)
- [WAI: Evaluating Web Accessibility Overview](https://www.w3.org/WAI/test-evaluate/)
- [Deque: automated coverage research](https://www.deque.com/blog/automated-testing-study-identifies-57-percent-of-digital-accessibility-issues/)

## 1. Concept — Automated Checks Are a Floor, Not a Proof

Automated engines (axe-core, used by Lighthouse, jest-axe, `@axe-core/playwright`) verify what is *machine-decidable from the DOM*: missing alt attributes, form controls without labels, insufficient contrast of computed colors, invalid ARIA attribute combinations, duplicate ids, missing document language. Industry research consistently finds this catches **a minority of real accessibility issues** (Deque's own study: ~57% of issue *instances*; per WCAG criteria the automatable share is far lower).

What no engine can decide: whether alt text is *meaningful* (`alt="image"` passes), whether focus lands somewhere sensible after a dialog closes, whether the tab order matches the visual order, whether a screen reader announces the async error, whether the experience is *usable* rather than merely rule-compliant. Those are semantic and interaction questions — they need a human running [[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|manual checks]].

The three layers that work together:

```ts
// 1. CI floor — every page/state, fails the build on regressions
import AxeBuilder from "@axe-core/playwright";
test("dashboard has no automated a11y violations", async ({ page }) => {
  await page.goto("/dashboard");
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

```tsx
// 2. Behavioral a11y assertions in component tests — the semantics YOUR feature promises
it("associates the error with the field", async () => {
  render(<EmailField />);
  const input = screen.getByRole("textbox", { name: /email/i });
  await userEvent.type(input, "not-an-email");
  await userEvent.tab();
  expect(input).toHaveAccessibleDescription(/valid email/i);  // aria-describedby wired
  expect(input).toBeInvalid();                                // aria-invalid state
});
```

3. **Manual passes** — keyboard-only walkthrough and a screen-reader session per interactive feature ([[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|the protocol]]).

Note that Testing Library's role/name queries already make every component test a small a11y test ([[24 - Testing and Quality/03 - React Component Testing Through User Behavior|component testing]]) — layer 2 extends that to states and relationships (`toHaveAccessibleName`, `toHaveAccessibleDescription`, `toBeInvalid`, focus assertions).

## 2. Why It Matters

- "We run Lighthouse, we're accessible" is a false-confidence pattern with legal exposure (ADA/EAA claims) and real excluded users. Knowing the coverage boundary is the difference between compliance theater and engineering.
- The behavioral layer is where regressions actually happen: a refactor drops an `aria-describedby`, focus stops returning after modal close — axe passes both, users lose the feature.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a signup form passes axe with zero violations; a blind user cannot complete it.

Trace the gap: every field has a label (axe ✅). But the async "email already registered" error renders as a visually-red div *not associated with the field and never announced* — a screen-reader user submits, hears nothing, and is stuck. Machine-decidable? No: the div is valid DOM; its *meaninglessness to AT* is a relationship/behavior question.

```tsx
// Fix: wire the relationships and the announcement
<input
  id="email"
  aria-invalid={!!error}
  aria-describedby={error ? "email-error" : undefined}
/>
{error && <p id="email-error" role="alert">{error}</p>}   {/* announced on appearance */}
```

```tsx
// ...and pin it with behavioral tests so refactors can't silently drop it
expect(await screen.findByRole("alert")).toHaveTextContent(/already registered/i);
expect(screen.getByRole("textbox", { name: /email/i }))
  .toHaveAccessibleDescription(/already registered/i);
```

(Full pattern: [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|accessible forms]].)

Tradeoffs: behavioral a11y assertions are per-feature work — you write them for the contracts your UI promises, not exhaustively. Axe in CI costs ~1s per page and occasionally false-positives on intentional patterns (document exceptions explicitly with rule disables + comments, never blanket-disable). Manual passes cost minutes per feature and don't automate — schedule them at feature completion, not "before the audit."

> [!warning] Don't let the tooling define the goal
> The goal is operable-by-real-users, and the tools are detectors for *specific failure classes*. Inverting it — "make axe pass" — produces label-stuffed, ARIA-sprayed DOMs that satisfy the linter and confuse actual screen readers ([[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|when not to use ARIA]]).

## 4. Interview Answer

Short answer:

> Automated checks (axe in CI) catch the machine-decidable minority — missing labels, contrast, invalid ARIA — and are worth running on every page as a regression floor. The majority of real issues are semantic or interactional: meaningful alt text, focus management, tab order, announcements. I cover those with behavioral assertions in component tests — accessible name/description, `aria-invalid`, focus position — and manual keyboard and screen-reader passes per interactive feature. Automated green is a floor, never proof.

Deeper answer:

> The practical stack: Testing Library's role/name queries make every component test enforce basic semantics for free; explicit assertions pin the relationships my features promise (error `aria-describedby` wiring, focus return after dialog close); `@axe-core/playwright` sweeps whole pages including states only reachable mid-flow; and the manual protocol — tab through everything, then a screen-reader run — catches what no DOM analysis can, like tab order diverging from visual order. When axe false-positives on an intentional pattern, I disable that one rule with a comment at that one call site — a blanket disable converts the floor into a hole.

## 5. Practice

1. <details><summary>Name four issue classes axe catches and four it cannot, with the reason for the boundary.</summary>Catches: form control without accessible name; `<img>` without alt; contrast below threshold (computable from rendered colors); invalid/conflicting ARIA (e.g., `aria-checked` on a role that doesn't support it). Cannot: alt text that's present but wrong (meaning); focus not moving into an opened dialog (behavior over time); tab order vs visual order (spatial-semantic comparison); missing announcement of an async result (AT behavior). Boundary: axe sees one DOM snapshot and decides rule-shaped predicates; meaning, time, and intent aren't in the snapshot.</details>

2. <details><summary>Where in the test stack does "focus returns to the trigger button after the dialog closes" belong?</summary>Component test with userEvent (real focus events in jsdom): open via the trigger, close via Escape, `expect(trigger).toHaveFocus()`. It's a deterministic behavior of your component, so it doesn't need a browser E2E — though dialogs with complex focus traps may warrant one real-browser check since jsdom's focus model has limits ([[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|dialogs]]). It will never be caught by axe: no snapshot rule can see it.</details>

3. <details><summary>Your CI axe check fails on a third-party chat widget you can't fix. Options?</summary>Scope the analysis: `AxeBuilder.exclude('#chat-widget')` with a comment and a tracking issue — keeping the floor intact for your own DOM. Report upstream; evaluate replacement if the widget is materially inaccessible (it's your product's exposure regardless of authorship). Never solve it by disabling rules globally or dropping the check — that removes protection from all your code to accommodate someone else's bug.</details>

4. <details><summary>Why do Testing Library queries constitute "free" accessibility testing, and where does the free ride end?</summary>`getByRole("button", { name: /save/i })` fails unless the element exposes that role and accessible name — so tests written this way continuously verify baseline semantics. The ride ends at states and relationships (invalid, described-by, expanded, focus position — assert explicitly), page-level concerns (landmarks, heading structure, contrast — axe), and everything behavioral/AT-specific (manual). Free floor, not free coverage.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|Accessibility Testing and Manual Screen-Reader Checks]]
- [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms, Validation and Async Errors]]
- [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|React Component Testing Through User Behavior]]
- [[24 - Testing and Quality/07 - Playwright Workflows|Playwright Workflows]]
