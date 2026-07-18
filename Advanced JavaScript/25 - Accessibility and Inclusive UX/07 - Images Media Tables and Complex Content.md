---
tags: [accessibility, images, media, tables]
module: "25 - Accessibility and Inclusive UX"
priority: important
status: not-started
aliases: [alt text, captions, data tables]
---

# Images, Media, Tables and Complex Content

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: make the alt-text decision (informative/functional/decorative) correctly and mark up a data table AT can actually navigate.
- Production signal: your content components enforce these decisions structurally (required alt props, header scopes) instead of relying on authors remembering.
- Dependencies: [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]]

## Source Anchors

- [WAI Tutorials: Images (decision tree)](https://www.w3.org/WAI/tutorials/images/decision-tree/)
- [WAI Tutorials: Tables](https://www.w3.org/WAI/tutorials/tables/)
- [MDN: the track element (captions/subtitles)](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/track)
- [WCAG 2.2: 1.1.1 Non-text Content, 1.2 Time-based Media](https://www.w3.org/WAI/WCAG22/quickref/#text-alternatives)

## 1. Concept

**Images: the decision is about function, not the picture.** The W3C decision tree reduces to:

- **Informative** — conveys content: alt describes the *information*, not the pixels. A chart: `alt="Revenue grew 40% from January to June"`, not `alt="line chart"`. Length ∝ information; complex charts get a short alt plus an adjacent text/data alternative ([[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|and never color-only encoding]]).
- **Functional** — inside a link/button: alt names the *destination/action* (`alt="Search"` for the magnifier icon), because it becomes the control's accessible name ([[25 - Accessibility and Inclusive UX/04 - ARIA Roles Names and States|accname]]).
- **Decorative** — adds nothing: `alt=""` (empty, present!) so AT skips it. A *missing* alt attribute makes screen readers read the filename — `alt=""` is an explicit, correct statement. Icon fonts/inline SVGs: `aria-hidden="true"` when decorative, `role="img"` + `aria-label`/`<title>` when informative.

In `next/image`, `alt` is required by design ([[22 - Next.js Deep Dive/08 - Asset Optimization|asset optimization]]) — make your own image components equally strict, with an explicit `decorative` prop rather than an optional alt.

**Media**: prerecorded video needs **captions** (dialog + meaningful sound, for deaf/HoH users — also the most-used-by-everyone feature) and an **audio description** or text alternative when visuals carry information the audio doesn't; audio-only needs a transcript. `<track kind="captions">` wires WebVTT into native video. Autoplaying media with sound: don't; and anything moving > 5s needs pause/stop/hide (WCAG 2.2.2, [[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|motion]]).

**Data tables**: AT navigates tables cell-by-cell, announcing the *headers* for each cell — but only if the relationships are marked: `<th scope="col">`/`<th scope="row">` (or `headers`/`id` for multi-level monsters), plus `<caption>` naming the table. A div-grid styled to look tabular has none of this — the user hears disconnected numbers. Conversely, layout-abused `<table>`s should be `role="presentation"` (or better, CSS). Sortable tables announce sort state via `aria-sort` on the header.

## 2. Why It Matters

- Alt text and captions are the oldest, most audited accessibility requirements (WCAG 1.1.1 is criterion number one) — and still the most commonly failed, because they're authored per-content-item rather than fixed once in code. Your leverage as an engineer is making components enforce the decision.
- Data tables are where enterprise apps live (dashboards, admin panels); an unnavigable table makes the core product unusable, not just a page imperfect.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a finance dashboard's "spend by category" table, built as styled divs for design flexibility, plus a trend chart with `alt="chart"`.

```tsx
// Bug: looks like a table, isn't one
<div className="table">
  <div className="row header"><div>Category</div><div>Q1</div><div>Q2</div></div>
  {rows.map(r => (
    <div className="row" key={r.id}><div>{r.name}</div><div>{r.q1}</div><div>{r.q2}</div></div>
  ))}
</div>
<img src={trendUrl} alt="chart" />
```

Trace: a screen-reader user in the div-grid hears "Marketing, 42,000, 38,000" with no way to ask "which column am I in?" — table navigation commands (next column, read header) do nothing because there are no semantics. Fifty rows of context-free numbers. The chart announces "chart, image" — the actual trend information exists only in pixels.

```tsx
// Fix: real table semantics + an informative alt with a data fallback
<table>
  <caption>Spend by category, Q1–Q2 2026</caption>
  <thead>
    <tr><th scope="col">Category</th><th scope="col">Q1</th><th scope="col">Q2</th></tr>
  </thead>
  <tbody>
    {rows.map(r => (
      <tr key={r.id}>
        <th scope="row">{r.name}</th><td>{r.q1}</td><td>{r.q2}</td>
      </tr>
    ))}
  </tbody>
</table>

<img src={trendUrl}
     alt="Total spend trended down 12% across the half, driven by Marketing" />
{/* The chart's underlying data is also available in the table above — say so nearby if not adjacent */}
```

Now cell navigation announces "Q2, Marketing, 38,000" — headers travel with the cell; the caption names the table in the tables-list AT can jump between; row headers make row context explicit. The chart alt conveys the *conclusion* the visualization exists to show, with the full data in the adjacent table.

Tradeoffs: real `<table>` markup constrains layout less than feared (CSS handles almost everything short of virtualized infinite grids), but genuinely virtualized data grids do need `role="grid"` + ARIA row/cell semantics and are a serious build ([[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|custom widget budget]]). Informative alt for dynamic charts requires generating text from *data*, not templates ("Revenue chart" forever) — a real feature to build, and the honest cost of showing information visually.

> [!tip] Enforce decisions in the component API
> `<Image>` requiring `alt: string` OR `decorative: true` (a union prop — [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|discriminated unions]]) turns the decision tree into the type system; `<DataTable columns={...}>` owning `scope` and `<caption>` means feature code can't build the div-grid. Content authors make the *judgment*; components make forgetting impossible.

## 4. Interview Answer

Short answer:

> Alt text is a decision about function: informative images describe the information ("revenue grew 40%", not "line chart"); functional images name the action, since alt becomes the control's name; decorative images take explicit `alt=""` so AT skips them — a missing attribute reads the filename. Video needs captions and, when visuals carry unique information, described or text alternatives. Data tables need real semantics — `th` with scope, caption — because AT table navigation announces each cell's headers; a styled div-grid is a stream of disconnected numbers.

Deeper answer:

> The engineering leverage is structural enforcement: image components typed to require alt or an explicit decorative flag, table components owning scope/caption, chart components requiring a data-derived text summary — the per-item authoring judgment stays human, but omission becomes impossible. For complex visuals the honest standard is equivalence: the chart's alt states its conclusion and the data has a navigable representation. And the edge cases have exact rules: SVG icons get aria-hidden or role=img+label; sortable headers announce `aria-sort`; virtualized grids are the one case where div-based `role="grid"` semantics are justified, budgeted as the serious custom-widget work they are.

## 5. Practice

1. <details><summary>Write alt for: (a) a hero photo of an office behind the heading "About us", (b) a PDF-download icon button, (c) a user's avatar next to their visible name, (d) a screenshot in a bug report.</summary>(a) Likely decorative — `alt=""`: it sets mood, adds no information the heading lacks (if it *shows* something referenced — "our Lisbon office" — describe that). (b) `alt="Download PDF"` — the action, it's the button's name. (c) `alt=""` — the name is adjacent text; `alt="Jane Doe"` would double-announce. (d) Informative and specific: `alt="Settings page with the Save button overlapping the footer"` — the content the report depends on.</details>

2. <details><summary>Why is `alt=""` fundamentally different from no alt attribute?</summary>`alt=""` is an explicit semantic statement: "decorative, skip it" — AT ignores the image entirely. A missing attribute is an authoring error, and AT falls back to announcing the src filename ("IMG_20260712_final_v2.jpg") — noise that's worse than either alternative. Lint rules (jsx-a11y/alt-text) enforce the attribute's presence; the human still chooses empty vs informative.</details>

3. <details><summary>A sortable table column is sorted descending. What does AT need, and where?</summary>`aria-sort="descending"` on that column's `<th>` (only on the sorted column; others omit it), so navigating to the header announces the state. The sort *control* should be a real `<button>` inside the `th` named e.g. "Sort by date", and the sort *change* deserves a polite announcement ("Sorted by date, newest first" — [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|live regions]]) since the reorder happens away from focus. Visual arrow icons are `aria-hidden` — the state lives in `aria-sort`, not the glyph.</details>

4. <details><summary>Product wants an auto-playing muted background video in the hero. Accessibility requirements?</summary>Muted autoplay dodges the audio problem, but WCAG 2.2.2 still applies to motion: if it plays > 5s, provide a visible pause/stop control; respect `prefers-reduced-motion` by not autoplaying at all for those users ([[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|motion]]); ensure text over the video keeps contrast in all frames (overlay/scrim); and if the video conveys information (not just ambience), it needs the full captions/description treatment. Decorative-ambience video with a pause button and reduced-motion opt-out is shippable.</details>

## Related Notes

- [[25 - Accessibility and Inclusive UX/01 - Semantic HTML Before ARIA|Semantic HTML Before ARIA]]
- [[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|Color, Contrast, Motion, Zoom and Reflow]]
- [[22 - Next.js Deep Dive/08 - Asset Optimization|Asset Optimization]]
- [[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|Discriminated Unions (API enforcement)]]
