---
tags: [accessibility, color, contrast, motion, responsive]
module: "25 - Accessibility and Inclusive UX"
priority: important
status: not-started
aliases: [contrast ratio, prefers-reduced-motion, reflow]
---

# Color, Contrast, Motion, Zoom and Reflow

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: know the contrast numbers, the color-isn't-the-only-channel rule, `prefers-reduced-motion`, and the 400%-zoom reflow requirement.
- Production signal: your design tokens pass contrast by construction, motion respects user preference by default, and layouts reflow instead of clipping at high zoom.
- Dependencies: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|Render Pipeline]]

## Source Anchors

- [WCAG 2.2: 1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [WCAG 2.2: 1.4.10 Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html)
- [WCAG 2.2: 2.3.3 Animation from Interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html)
- [MDN: prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)
- [MDN: color-scheme and forced-colors](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/forced-colors)

## 1. Concept

Four visual/vestibular requirements, each with a number or a rule:

**Contrast (1.4.3 AA).** Text needs **4.5:1** against its background; large text (≥24px, or ≥18.7px bold) needs **3:1**; UI component boundaries and states (input borders, focus rings, icons that carry meaning) need **3:1** (1.4.11). Ratios are computable — enforce them in the design-token layer, not per-screen: if `--text-muted` on `--surface` passes, everything built from the tokens passes. The classic failures: light-gray placeholder text, disabled-looking-but-enabled buttons, white text on brand pastels.

**Color is never the only channel (1.4.1).** Red/green as the sole encoding of error/success excludes color-blind users (~8% of men): pair color with an icon, text, or pattern. Form errors: red border *plus* message and `aria-invalid` ([[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|forms]]); charts: patterns/labels, not hue alone; links inside prose: underline, not color-only.

**Motion (2.3.3 / 2.2.2).** Vestibular disorders make parallax, scale-zooms, and large translations physically nauseating. `prefers-reduced-motion: reduce` is the user's request — honor it by default:

```css
/* Global floor: motion becomes near-instant for users who asked */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Reduced ≠ none: opacity fades are fine; it's *movement* (translate/scale/parallax) that triggers symptoms — a considered implementation swaps slides for fades rather than deleting all feedback. In React, gate JS-driven animation (`matchMedia("(prefers-reduced-motion: reduce)")`) and autoplaying video ([[25 - Accessibility and Inclusive UX/07 - Images Media Tables and Complex Content|media]]).

**Zoom and reflow (1.4.4 / 1.4.10).** Text must scale to 200% without loss; the page must **reflow to a single 320px-wide column at 400% zoom** without horizontal scrolling of content. This falls out of honest responsive design — until it doesn't: `position: fixed` headers that eat half the zoomed viewport, `overflow: hidden` clipping, px-fixed heights truncating scaled text, and `maximum-scale=1` in the viewport meta (never do this — it disables pinch-zoom on mobile). Use `rem` for type, test at 400%, and let the 320px layout *be* your mobile layout.

## 2. Why It Matters

- These are the most *measurable* accessibility criteria — automated checks catch contrast ([[24 - Testing and Quality/09 - Accessibility Testing|axe]]), and audits lead with them — but the fixes are architectural (tokens, motion policy, responsive strategy), which is why retrofits are expensive and defaults matter.
- Low vision and color-blindness dwarf blindness in prevalence; zoom-and-reflow users are the largest assistive-usage population you have. This note is the "majority accessibility" note.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a redesign ships a marketing-grade dashboard: pastel palette, scroll-triggered parallax, and a status system of colored dots (green/amber/red).

Trace three user reports: (a) "can't read the secondary text" — `#9aa` on `#f5f7f8` is ~2.4:1, well under 4.5:1; (b) "the dashboard makes me motion-sick" — parallax translates entire panels on scroll with no reduced-motion path; (c) "which services are down?" — a deuteranope sees the green and red dots as nearly identical; the status *only* exists as hue.

```css
/* Fix (a): repair at the token layer, verify by computation */
:root {
  --surface: #f5f7f8;
  --text-secondary: #4a5568;   /* 7.5:1 on --surface — was #9aa at 2.4:1 */
}
/* CI: a token-pair contrast test fails the build if a future edit regresses it */
```

```css
/* Fix (b): motion as progressive enhancement */
.panel { opacity: 0; }
.panel.visible { opacity: 1; transition: opacity 300ms, transform 500ms; transform: none; }
@media (prefers-reduced-motion: no-preference) {
  .panel { transform: translateY(24px); }   /* movement only for users who accept it */
}
```

```tsx
/* Fix (c): status gets three channels — color, shape, text */
const STATUS = {
  up:      { color: "green", Icon: CheckCircle, label: "Operational" },
  degraded:{ color: "amber", Icon: AlertTriangle, label: "Degraded" },
  down:    { color: "red",   Icon: XOctagon, label: "Down" },
} as const;
// dot → icon + visible label (or icon + tooltip + sr-only text where space is tight)
```

Tradeoffs: token-level contrast constrains the palette (designers lose some pastels — the negotiation is real, and the tool is showing the computed ratios early, in design review, not at audit time); reduced-motion-by-default costs a second implementation path for signature animations (scope it: the design system's transition utilities handle it once); three-channel status costs horizontal space (the icon+sr-only compromise keeps dense tables workable).

> [!tip] Put the checks where the values are born
> Contrast is enforceable in the token pipeline (a unit test over token pairs — [[24 - Testing and Quality/11 - Typecheck Lint Format and CI Gates|CI gates]]); reduced-motion belongs in the design system's animation primitives; reflow belongs in the responsive baseline. Screen-level audits then only catch *content* mistakes, not systemic ones.

## 4. Interview Answer

Short answer:

> The numbers: 4.5:1 contrast for text, 3:1 for large text and UI component boundaries; 200% text scaling and reflow to a 320px column at 400% zoom without horizontal scrolling; never `maximum-scale=1`. The rules: color never carries meaning alone — pair it with text, icons, or patterns; and `prefers-reduced-motion` gets honored by default, replacing movement (translate, scale, parallax) with opacity changes rather than deleting feedback entirely, because it's motion that triggers vestibular symptoms.

Deeper answer:

> The engineering insight is that all four are systemic, not per-screen: contrast lives in the design tokens (testable in CI over token pairs), motion policy lives in the animation primitives (one `prefers-reduced-motion` implementation), and reflow falls out of a mobile-first responsive baseline where the 320px layout is real. Retrofitting any of them screen-by-screen is the expensive path. The status-indicator case is the canonical color-channel bug: green/red dots identical to 8% of male users — fixed by making status a triple of color, shape, and label, encoded once in the component.

## 5. Practice

1. <details><summary>A designer insists the light-gray placeholder text is "fine because it's just a hint." Adjudicate.</summary>Placeholder text is still text conveying information (format hints, examples) and needs 4.5:1 — and it disappears on input, which is why hints belong in persistent `aria-describedby` helper text anyway ([[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|forms]]). If it's genuinely non-informational decoration, why is it there? Resolution: move the hint to visible helper text at compliant contrast; the placeholder becomes optional flavor or goes away. (Exception carved by WCAG: truly disabled controls are exempt from contrast minimums.)</details>

2. <details><summary>Why is `user-scalable=no` / `maximum-scale=1` in the viewport meta a hard "no", and what breaks without it... nothing?</summary>It disables pinch-zoom — the primary low-vision adaptation on mobile — to protect a layout from a scaling it should handle anyway (WCAG 1.4.4 failure). The historical excuse (input-focus zoom jumps on iOS) is solved by 16px+ input font sizes instead. Nothing legitimate breaks with zoom enabled on a properly responsive layout; if zoom "breaks" the design, the design was relying on clipping, which is the 1.4.10 reflow bug wearing a costume.</details>

3. <details><summary>Implement "reduced motion" for a route-transition animation in a React app — what's the policy, mechanically?</summary>Wrap the motion decision once: a `usePrefersReducedMotion()` hook (matchMedia + change listener) or CSS-only via `@media (prefers-reduced-motion: no-preference)` gating the transform. Reduced path: crossfade (opacity 150ms) instead of slide; instant scroll instead of smooth ([[19 - DOM and Browser APIs/11 - History and Navigation APIs|scrollRestoration]]). Put it in the design system's `<Transition>` primitive so feature teams inherit the policy; never per-page media queries. Test both paths — the reduced one is a real UX, not an off switch.</details>

4. <details><summary>At 400% zoom your app's sticky header + sticky sidebar leave a 90px × 200px content window. Which criterion fails and what's the fix pattern?</summary>1.4.10 Reflow (and effectively 1.4.4): content must be usable in a 320px-equivalent column without 2D scrolling — chrome consuming the viewport defeats it. Pattern: demote sticky chrome at high zoom/small viewports — the same breakpoints that trigger the mobile layout should un-stick or collapse the header/sidebar (they're already designed for 320px widths). Sticky positioning is a wide-viewport enhancement, not a constant. Test by zooming a 1280px window to 400% — that *is* the 320px test.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/07 - Images Media Tables and Complex Content|Images, Media, Tables and Complex Content]]
- [[25 - Accessibility and Inclusive UX/03 - Accessible Forms Validation and Async Errors|Accessible Forms, Validation and Async Errors]]
- [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals and the Render Pipeline]]
- [[24 - Testing and Quality/11 - Typecheck Lint Format and CI Gates|Typecheck, Lint, Format and CI Gates]]
