---
tags: [accessibility, testing, screen-reader]
module: "25 - Accessibility and Inclusive UX"
priority: must-know
status: not-started
aliases: [screen reader testing, manual a11y checks]
verified_on: 2026-07-12
version_scope: "VoiceOver/NVDA current, axe-core 4.x"
---

# Accessibility Testing and Manual Screen-Reader Checks

## Maturity Target

- Priority: #must-know
- Study time: 60 minutes + hands-on practice
- Interview signal: describe a concrete manual protocol (keyboard pass, screen-reader pass) and what each step verifies that automation can't.
- Production signal: manual passes are part of your definition-of-done for interactive features, and you can actually drive a screen reader.
- Dependencies: [[24 - Testing and Quality/09 - Accessibility Testing|Accessibility Testing (automated)]], [[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|Focus Management]]

## Source Anchors

- [WAI: Easy Checks — A First Review](https://www.w3.org/WAI/test-evaluate/preliminary/)
- [WebAIM: Testing with VoiceOver](https://webaim.org/articles/voiceover/)
- [WebAIM: Testing with NVDA](https://webaim.org/articles/nvda/)
- [WAI: Involving Users in Evaluating Accessibility](https://www.w3.org/WAI/test-evaluate/involving-users/)

## 1. Concept — Two Manual Passes, Each With a Script

Automation covers the machine-decidable floor ([[24 - Testing and Quality/09 - Accessibility Testing|automated side]]). The manual half is two protocols, cheap enough to run per feature:

**Pass 1 — keyboard only (10 minutes, no tools).** Unplug the mouse, then:

1. **Tab through the whole feature.** Every interactive element reachable? Order matches visual logic ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|tab order]])?
2. **Look at every stop.** Focus visibly indicated at each one (`:focus-visible` present)?
3. **Operate everything.** Enter/Space on buttons and links, arrows in composites (tabs, menus), Escape out of overlays.
4. **Watch the transitions.** Open a dialog — is focus inside? Close — back on the trigger? Delete an item — focus somewhere sane? Navigate a route — focus and title updated?
5. **Try to get trapped.** Embedded editors, media players, infinite widgets — can you always leave?

**Pass 2 — screen reader (20–30 minutes).** Use what you have: **VoiceOver** on macOS (Cmd+F5; navigate with VO keys, Rotor via VO+U), **NVDA** on Windows (free; browse mode, Elements list via NVDA+F7). Script:

1. **Navigate by structure**: headings list (does the outline make sense?), landmarks (can you jump to main/nav?), links list (do names make sense out of context — no "click here"?).
2. **Walk the feature linearly** — is everything announced with a sensible role, name, and state ("Save, button", "Email, edit text, invalid, entry required")?
3. **Run the interactions blind** (screen curtain on, or eyes off the monitor): submit the form incorrectly — do you *hear* the errors ([[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|forms]])? Trigger the async flow — do you hear loading/result ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|announcements]])? Open the dialog — announced with its title?
4. **Note what you heard vs what sighted users see** — every mismatch is a finding.

Two calibrations: you are testing *your markup's contract*, and a developer driving a screen reader clumsily still finds the big breaks (silence, wrong roles, traps) — but you are not simulating a real AT user's fluency; for products with significant AT usage, paid testing by disabled users is the real verification (WAI's own guidance). And test one primary SR/browser pairing consistently (VoiceOver+Safari or NVDA+Firefox/Chrome) rather than chasing differences across all of them per feature.

## 2. Why It Matters

- Every issue class the automated note lists as "cannot" — focus placement, announcement timing, tab-order sense, name quality, actual task completability — is only found here. Teams that skip manual passes ship axe-clean, unusable features.
- Interviewers increasingly ask "walk me through testing this with a screen reader" to separate real practice from checkbox knowledge. Having actually done it is unmistakable.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a feature ships axe-clean with 100% RTL coverage. The manual pass finds three blockers in 25 minutes.

Findings from the keyboard pass: the custom date picker opens on click but arrow keys move *page scroll*, not the date grid (its keydown handlers were on the wrong element); after picking a date the popover closes and focus lands on `<body>` (Tab restarts from the page top).

Finding from the SR pass: the "3 appointments found" result renders visually but is never announced — the results region existed conditionally, so the live region was injected *with* its message ([[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|the classic]]); the user hears silence and re-submits.

```tsx
// Fixes, respectively:
// 1. Key handling on the grid container with roving tabindex ([[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|pattern]])
// 2. On close: dateButtonRef.current?.focus()  — restore to trigger
// 3. Always-rendered status region; set its text on results:
<div role="status" className="sr-only">{resultsMessage}</div>
```

Why nothing else caught these: axe sees a static snapshot (all three are behavioral); RTL tests *drove* the picker via its buttons' click handlers (never pressing real arrow keys against real focus) and asserted the results *text* rendered (not that it was announced). The manual pass is not redundant with good automated tests — it verifies the layer they structurally can't.

Tradeoffs: 30–40 minutes per feature of human time, plus the initial learning curve of driving a screen reader (an afternoon, once). Amortize: run the full protocol on interactive features and flows, not on copy changes; encode each manual *finding* as a regression test where possible (the focus-restore and announcement fixes above are RTL-assertable — [[24 - Testing and Quality/09 - Accessibility Testing|behavioral layer]]) so the manual pass keeps finding *new* bugs instead of re-finding old ones.

> [!tip] The findings ladder
> Manual finding → fix → *encode as automated regression test* → manual passes stay novel. The manual protocol is a discovery tool; automation is the memory. Teams that skip the encoding step re-discover the same focus bugs quarterly.

## Real-World Use Cases

### PR review checklist for a design-system component

A shared `<Combobox>` is about to merge — every product team will inherit its bugs. The reviewer's manual pass is the highest-leverage 30 minutes in the component's life: keyboard script against the ARIA combobox pattern (arrows navigate options, Escape closes, Tab commits), SR pass verifying announced role/name/state at each step, and the findings encoded as RTL assertions before approval. Shared components deserve the *full* protocol precisely because their bugs multiply across consumers (see [[25 - Accessibility and Inclusive UX/05 - Dialogs Menus Popovers and Focus Traps|composite widgets]]).

### Triaging an accessibility audit report

An external audit lands with 74 findings and the team panics. The manual-testing skills turn triage from guesswork into an afternoon: reproduce each finding with the keyboard/SR protocol, separate the three blockers (checkout unreachable by keyboard) from the forty advisories (redundant alt text), and reject the two false positives where the auditor's SR pairing diverges from your supported matrix. Without the ability to *drive* a screen reader, every finding is equally mysterious and equally expensive.

```ts
// Each confirmed finding becomes a regression test before the fix merges:
it("moves focus into the dialog on open and restores it on close", async () => {
  await user.click(screen.getByRole("button", { name: /edit profile/i }));
  expect(screen.getByRole("dialog")).toContainElement(document.activeElement);
  await user.keyboard("{Escape}");
  expect(screen.getByRole("button", { name: /edit profile/i })).toHaveFocus();
});
```

This is the findings ladder from section 3 operating at audit scale — manual verification is the filter, automation is the memory.

### The demo that changes a team's behavior

A screen-curtain demo in sprint review — attempting the team's own signup flow with VoiceOver, eyes off the screen — accomplishes what a quarter of Jira tickets couldn't: the room *hears* the silence after form submission. Ten minutes of a developer driving AT (clumsily is fine) converts "a11y backlog" into "our checkout is broken for real people." The demo works because manual testing produces experiences, not reports.

> [!tip]
> Record the SR pass (screen + audio) when filing findings — a 20-second clip of the silence is unanswerable in a way "missing live region" never is.

## 4. Interview Answer

Short answer:

> Two scripted passes per interactive feature. Keyboard-only: tab everywhere, focus visible at every stop, operate everything (Enter/Space/arrows/Escape), and watch focus through transitions — dialogs, deletions, route changes. Screen reader (VoiceOver or NVDA): navigate by headings/landmarks/links to check structure, then run the actual flows without looking — do I hear the form errors, the loading state, the results? Everything automation can't decide — announcement, focus behavior, name quality, task completability — lives in these passes.

Deeper answer:

> The calibrations that make it honest: a developer driving VoiceOver finds contract breaks — silence, wrong roles, traps, lost focus — but doesn't simulate a fluent AT user, so for AT-significant products the real bar is testing by actual disabled users. Consistency beats coverage: one SR/browser pairing per platform, run the same way every time. And each manual finding gets encoded as an automated behavioral test — focus restore, announcement presence — so the expensive human pass keeps discovering novel issues rather than regressions. That ladder is what makes 30 minutes per feature sustainable.

## 5. Practice

1. <details><summary>Run the headings-list check on your current project's main page. What three questions does the list answer?</summary>(1) Is there exactly one h1, and does it name the page? (2) Do levels nest without skips (h2 → h3, not h2 → h5 for styling — [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|semantics]])? (3) Could you find any section from the list alone — i.e., is the outline a usable table of contents? If the list is empty or nonsense, screen-reader users have no scanning mechanism for the page.</details>

2. <details><summary>During the SR pass a button announces as "button" with no name. List the likely causes in order of probability.</summary>Icon-only button with no text and no naming mechanism (most common — needs sr-only text or aria-label — [[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|accname]]); an SVG child not marked aria-hidden but contributing no text; a name that exists only as `title` on the SVG that this SR/browser pairing ignores; text hidden with `display:none` instead of an sr-only class (removes it from the tree); or `aria-labelledby` pointing at a nonexistent/empty id — the silent typo automation flags but only if the rule is enabled.</details>

3. <details><summary>Why "one consistent SR/browser pairing" instead of testing all combinations, and when do you break that rule?</summary>SR/browser pairs differ on edge cases, and chasing differences per feature dissolves the protocol into research — consistency makes findings comparable across features and time, and the big contract breaks (silence, traps, wrong roles) reproduce on any pairing. Break it: before major releases (a second pairing sweep), when a user reports a pairing-specific bug, and for widgets relying on newer ARIA where support genuinely diverges (verify on NVDA and VoiceOver both). Depth per feature, breadth per release.</details>

4. <details><summary>Design the definition-of-done entry for accessibility on an interactive feature, with time budget.</summary>Automated: axe on the feature's states (CI), RTL behavioral assertions for the feature's specific contracts — names, focus moves, announcements (~already part of test-writing). Manual: 10-min keyboard pass + 20-min SR pass on the primary pairing, findings filed and either fixed or triaged; each fixed finding encoded as a regression test. Budget: ~40 min human time per feature. Exempt: pure copy/style changes (axe only). This makes accessibility a completion criterion rather than an audit event — the cheapest time to fix is before merge.</details>

## Related Notes

- [[24 - Testing and Quality/09 - Accessibility Testing|Accessibility Testing (automated side)]]
- [[25 - Accessibility and Inclusive UX/02 - Keyboard Interaction and Focus Management|Keyboard Interaction and Focus Management]]
- [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions, Loading States and Announcements]]
- [[25 - Accessibility and Inclusive UX/10 - Accessibility Checklist|Accessibility Checklist]]
