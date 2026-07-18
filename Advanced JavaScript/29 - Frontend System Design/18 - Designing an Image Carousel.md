---
tags: [system-design, interview, carousel, images, performance]
module: "29 - Frontend System Design"
priority: important
status: not-started
aliases: [carousel design, image slider, gallery design]
verified_on: 2026-07-17
version_scope: "Browser APIs (fetchpriority, loading=lazy, AVIF/WebP) and WAI-ARIA APG carousel pattern as of 2026"
---

# Designing an Image Carousel

## Maturity Target

- Priority: #important
- Study time: 45 minutes
- Interview signal: Run RADIO on a carousel covering image loading strategy (lazy/preload neighbors), CLS prevention, gestures/keyboard, and the a11y model — with tradeoffs.
- Production signal: You can build a carousel that's smooth, doesn't shift layout, and is keyboard/screen-reader usable.
- Dependencies: [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]], [[29 - Frontend System Design/14 - Accessibility in System Design|Accessibility in System Design]]

## Source Anchors

- [WAI-ARIA APG — Carousel Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/carousel/)
- [web.dev — Optimize LCP (images)](https://web.dev/articles/optimize-lcp)
- [MDN — Intersection Observer](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)

## 1. Requirements

Ask: how many slides (5 or 5,000)? content type (images, mixed media, product cards)? autoplay? infinite loop? touch/swipe + mouse drag + keyboard? one slide or multiple visible? thumbnails/indicators? is a slide the LCP element (hero carousel)?

Design against: **a media gallery, dozens of high-res images, swipe + drag + keyboard, indicators, optional autoplay, first slide is likely the LCP.** Out of scope: video playback controls, Ken Burns effects.

The requirement that shapes it: **high-res images + the first slide is LCP.** That forces an image-loading strategy (eager LCP image, lazy neighbors) and strict layout reservation.

## 2. Architecture

```
<Carousel>
 ┌────────────────────────────────────────┐
 │ Track (transform: translateX)           │
 │  [slide n-1][ slide n ][slide n+1] …    │  only near slides mounted/loaded
 └────────────────────────────────────────┘
   Controller: activeIndex, isDragging, autoplay timer
   Gestures: pointer events → drag offset → snap
   Indicators / prev-next  ·  IntersectionObserver for lazy load
```

The **track** translates on a single transformed element (GPU-friendly) rather than re-laying-out slides. The **controller** owns `activeIndex`, drag state, and the autoplay timer. Only slides **near the active index** are mounted/loaded (windowing lite) — for dozens of images you don't need full virtualization, but you do need neighbor-only loading.

> [!warning] Two classic bugs: (1) all images `loading="eager"` → the browser downloads every high-res slide on load, wrecking LCP and bandwidth; (2) slides without reserved dimensions → each image load shifts layout (CLS). Reserve slide size with `aspect-ratio` and load only the active image eagerly, neighbors lazily.

## 3. Data Model

```ts
interface CarouselState {
  activeIndex: number;
  dragOffsetPx: number;          // live drag, for rubber-banding
  isDragging: boolean;
  autoplay: { playing: boolean; pausedByUser: boolean };
}
// slides: { id, src, srcset, alt, aspectRatio }[]  — aspectRatio reserves space
```

`aspectRatio` per slide is load-bearing: it lets the track reserve exact space before images load, so nothing shifts (CLS). Drag offset is separate from `activeIndex` so a drag rubber-bands live and *commits* to an index on release (snap).

## 4. Interface

```tsx
<Carousel
  slides={slides}
  renderSlide={(s) => <img src={s.src} srcSet={s.srcset} alt={s.alt} />}
  autoPlay={false}
  visibleCount={1}
  onIndexChange={setIndex}
  aria-label="Product photos"
/>
```

Composition on `renderSlide` (not baked-in `<img>`) so it works for product cards, video, etc. Autoplay off by default (accessibility + user control). Indicators and prev/next are real `<button>`s.

## 5. Optimizations (ranked)

1. **Image loading** — the active/LCP image eager with a **priority hint** (`fetchpriority="high"`); neighbors preloaded; far slides lazy (`loading="lazy"` / IntersectionObserver). Responsive `srcset`/`sizes` and modern formats (AVIF/WebP). This is the biggest lever for a hero carousel's LCP.
2. **Layout stability (CLS)** — reserve every slide's box via `aspect-ratio`; no reflow on image load.
3. **Smooth motion** — animate `transform: translateX` (compositor, not layout); `will-change` sparingly; respect `prefers-reduced-motion` (disable autoplay + reduce transition).
4. **Gestures** — Pointer Events (unify mouse/touch), drag with rubber-band at ends (unless infinite), velocity-based snap; don't hijack vertical scroll (respect `touch-action`).
5. **Accessibility (APG carousel)** — get the two role levels right: the **container** is `role="region"` (or a `<section>`) with `aria-roledescription="carousel"` + an `aria-label`; **each slide** is `role="group"` with `aria-roledescription="slide"` and an "n of m" label. The rotation control comes *first* in DOM order; prev/next are real `<button>`s. Set `aria-live="off"` on the slides container while auto-rotating and `aria-live="polite"` when rotation is stopped, so a browsing user isn't interrupted but a paused user hears slide changes. **Autoplay must pause on hover/focus and have a visible pause/stop control** (WCAG 2.2.2: moving content must be pausable, stoppable, or hideable), plus keyboard arrow support and `prefers-reduced-motion` handling. Autoplay without a pause control is a WCAG failure. *(Common mistake: putting `aria-roledescription="carousel"` on a `role="group"` element — that conflates the container and slide roles and matches neither half of the pattern.)*

## 6. Interview Answer

Short answer:

> A carousel is a transformed track with a controller for active index, drag, and autoplay, loading only slides near the active one. The two decisions that matter most: image strategy — eager, priority-hinted LCP image with lazy neighbors and responsive srcset — and layout stability, reserving each slide's box with aspect-ratio so image loads don't shift content. Motion animates transform for compositor smoothness. Accessibility follows the APG carousel pattern, and autoplay must pause on hover/focus with a visible pause control or it's a WCAG failure.

Deeper answer:

> For a hero carousel the LCP image dominates the perf story, so I load it eagerly with `fetchpriority=high` while neighbors preload and the rest stay lazy — loading all high-res slides upfront is the classic bandwidth-and-LCP bug. CLS is the other silent killer: without reserved `aspect-ratio` boxes, every image load nudges layout, so I reserve space per slide. I animate `translateX` because it runs on the compositor and doesn't trigger layout/paint, keeping the drag at 60fps, and I separate live drag offset from the committed index so it rubber-bands and snaps. On a11y the non-obvious requirement is autoplay: moving content must be pausable and must pause on hover/focus, and slides need "n of m" labelling — otherwise it's inaccessible motion.

## 7. Practice

1. <details><summary>Why not `loading="eager"` on all carousel images, and what's the right strategy?</summary>Eager-loading every slide downloads all high-res images on page load, hurting LCP and wasting bandwidth on slides the user may never see. Load the active/LCP image eagerly (with `fetchpriority=high`), preload immediate neighbors for smooth advance, and lazy-load the rest via `loading=lazy`/IntersectionObserver.</details>
2. <details><summary>Why animate `transform: translateX` instead of `left` or margin?</summary>`transform` is handled by the compositor and doesn't trigger layout or paint, so it animates at 60fps; animating `left`/`margin` triggers layout on every frame (jank). Combined with reserved aspect-ratio boxes, transform gives smooth motion without CLS.</details>
3. <details><summary>What does WCAG require of an autoplaying carousel?</summary>Moving/auto-updating content must be pausable, stoppable, or hideable, and it should pause on hover and keyboard focus. So autoplay needs a visible pause control and must halt when the user interacts — plus `prefers-reduced-motion` should disable it. Autoplay with no pause control is a conformance failure regardless of how nice it looks.</details>

## Related Notes

- [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]]
- [[22 - Next.js Deep Dive/08 - Asset Optimization|Asset Optimization]]
- [[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|Color, Contrast, Motion, Zoom and Reflow]]
- [[19 - DOM and Browser APIs/06 - Observers|Observers]]
