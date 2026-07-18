---
tags: [system-design, interview, infinite-scroll, pagination, performance]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [news feed design, infinite feed design]
---

# Designing an Infinite Scroll Feed

## Maturity Target

- Priority: #must-know
- Study time: 75 minutes
- Interview signal: You can design a news-feed-style infinite list covering cursor pagination, virtualization, scroll restoration, and the a11y costs of infinite scroll — with the tradeoffs stated, in 35 minutes.
- Production signal: You can explain why a long-lived feed tab eats memory and janks, and fix it by layer.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[19 - DOM and Browser APIs/06 - Observers|Observers]], [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Large List Transformations]]

## Source Anchors

- [MDN — Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)
- [web.dev — Virtualize large lists](https://web.dev/articles/virtualize-long-lists-react-window)
- [GreatFrontEnd — News Feed case study](https://www.greatfrontend.com/questions/system-design/news-feed-facebook)

## 1. Requirements

Ask: how mutable is the list (append-only archive vs live social feed with inserts/deletes)? item height fixed or variable (media)? session length (quick visit vs feed users scrolling for 20 minutes)? back-navigation expectations (return to scroll position)? new-content strategy (prepend live, or "N new posts" pill)? SEO relevance?

Design against the hard version: **social feed, mutable, variable-height rich items with images, long sessions, back-nav restoration expected, "new posts" indicator.** Out of scope: ranking, composer, comments.

The requirement that shapes everything: *long sessions on a mutable list*. It forces cursor pagination (correctness), virtualization + eviction (memory), and stable identity (rendering).

## 2. Architecture

```
┌──────────────────────────────────────────────┐
│  <Feed>                                      │
│  ┌────────────────┐  ┌────────────────────┐  │
│  │ Virtual window  │  │ Controller          │  │
│  │ (renders only   │◀─│ status: idle|loading│  │
│  │  visible items) │  │ -more|error|end     │  │
│  └────────────────┘  │ + scroll anchor      │  │
│  ┌────────────────┐  └─────────┬──────────┘  │
│  │ Sentinel        │───trigger──┘             │
│  │ (IntersectionOb)│                          │
│  └────────────────┘                          │
└──────────────────────┬───────────────────────┘
               ┌───────▼─────────┐
               │ Feed query layer │  pages by cursor · entity store
               │                  │  in-flight guard · new-items buffer
               └───────┬─────────┘
                       ▼  GET /feed?cursor=…
```

Same controller/query split as [[29 - Frontend System Design/02 - Designing an Autocomplete|Autocomplete]] — the pattern generalizes. New pieces: a **sentinel** element observed by `IntersectionObserver` (with `rootMargin` ≈ one viewport so loading starts before the user hits bottom), a **virtual window** so DOM size stays O(visible) not O(loaded), and a **new-items buffer** — live posts land in the query layer but are *not* prepended to the UI until the user clicks the "N new posts" pill, because silent prepends yank content under the reader's eyes.

> [!warning] The sentinel double-fire: `IntersectionObserver` can fire while a page is already loading (fast scroll, layout shifts re-intersecting the sentinel), issuing duplicate requests and duplicate pages. The controller's `loading-more` status must gate the trigger — this is [[17 - Practical Frontend Scenarios/02 - Preventing Duplicate API Requests|duplicate-request prevention]] wearing a scroll costume.

## 3. Data Model

```ts
// Server state — query layer
interface FeedCache {
  pages: { cursor: string | null; ids: PostId[] }[];  // ordered pages
  entities: Map<PostId, Post>;                        // normalized
  nextCursor: string | null;                          // null = end reached
  pendingNew: PostId[];                               // buffered live posts
}

// UI state — controller
interface FeedUIState {
  status: 'idle' | 'loading-more' | 'error' | 'end';
  anchor: { id: PostId; offsetPx: number } | null;    // scroll restoration
}
```

Normalization earns its keep here (unlike the 10-item autocomplete): posts appear in multiple pages after edits, get updated by interactions (like counts), and are shared with detail views. One entity store means one update propagates everywhere — this is [[28 - Frameworks and Application Architecture/06 - Server State|server state as a cache]] at full scale.

Scroll restoration stores an **anchor** (topmost visible post id + pixel offset), not a raw `scrollTop` — with virtualization and variable heights, absolute scroll offsets are meaningless after remount. On back-nav: restore cached pages, render the window around the anchor, adjust.

Memory policy: pages far above the viewport can be **evicted to ids only** (drop rendered state, keep entities or even refetch by cursor). Without eviction, a 20-minute session is an [[13 - Performance and Memory/03 - Memory Leaks|unbounded growth leak]] with a scrollbar.

## 4. Interface

**Component API:**

```ts
interface FeedProps<T> {
  fetchPage: (cursor: string | null, signal: AbortSignal) => Promise<{
    items: T[];
    nextCursor: string | null;
  }>;
  getItemId: (item: T) => string;           // identity is the consumer's fact
  renderItem: (item: T) => ReactNode;
  estimateItemHeight?: (item: T) => number; // virtualization hint
  onEndReached?: () => void;                // analytics seam
}
```

Same inversion of control as autocomplete's `getSuggestions`: the feed owns orchestration (sentinel, dedup, windowing), the consumer owns transport and rendering. `getItemId` is explicit because keys and anchors both depend on identity, and guessing it (`item.id`?) is a library anti-pattern.

**Network API:** `GET /feed?cursor=<opaque>&limit=20` → `{ items, nextCursor }`.

**Cursor, not offset — be ready to defend this.** With `?offset=40`, any insert or delete above the offset shifts the window: the user sees duplicated or skipped posts (the classic "same post twice while scrolling" bug). A cursor is an opaque position marker ("after post X at time T"), immune to shifts. Tradeoff: no random access ("jump to page 7") and the cursor format couples client to server's ordering — acceptable for feeds, wrong for a paginated admin table. Knowing *which context wants which* is what separates a real answer from a memorized "always use cursors."

## 5. Optimizations (ranked for this requirement set)

1. **DOM/memory discipline** — virtualization (windowing) so thousands of loaded posts render dozens of nodes; page eviction; absolute worst case measured, not guessed. Alternative worth naming: CSS `content-visibility: auto` as a lighter-weight partial answer.
2. **Layout stability** — reserve media space with `aspect-ratio` boxes so image loads don't shift content (CLS — [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals]]); `loading="lazy"` + responsive `srcset` for offscreen images.
3. **Correctness under mutation** — cursor pagination, `key={post.id}` never index ([[21 - React Internals and Patterns/02 - Reconciliation and Keys|keys]] — prepends make index keys re-render and mis-state *every* row), in-flight guard on the sentinel.
4. **Accessibility** — infinite scroll is *hostile* by default: keyboard users can never reach content below the feed (footer trap), and screen readers get no signal that content grew. Mitigations: a real "Load more" button as the sentinel fallback (it's also the no-JS/SEO answer), `aria-live` announcement on page append ("20 more posts loaded"), `role="feed"` with `aria-busy` during loads, and a skip link past the feed.
5. **Perceived performance** — skeleton rows sized by `estimateItemHeight`, optimistic "new posts" pill count, prefetch next page at `rootMargin` distance rather than on-hit.

## 6. Interview Answer

Short answer:

> "An infinite feed is a virtualized window over a cursor-paginated cache. Query layer holds pages of ids plus a normalized entity store; controller holds a status machine and a scroll anchor. An IntersectionObserver sentinel triggers loads, gated by status to prevent duplicate pages. Cursor over offset because the list mutates — offsets shift, cursors don't. The two costs people forget: memory over long sessions, so I evict far-off pages, and accessibility, so I keep a real Load-more button and announce appended content."

Deeper answer:

> "The decisions I'd defend: buffering live posts behind an 'N new posts' pill instead of prepending — silent prepends destroy reading position, and with virtualization a prepend also invalidates every offset, which is why my scroll anchor is an item id plus offset, not a scrollTop number. And I'd push back on virtualizing reflexively: it costs complexity (variable heights need measurement caches) — for a feed capped at a few hundred lightweight rows, `content-visibility` or nothing may win. The requirement — long sessions, rich media — is what buys virtualization here."

## 7. Practice

1. <details><summary>A user reports "I saw the same post twice while scrolling." Root-cause it from the design.</summary>Two candidate mechanisms: offset pagination on a mutable list (a new post above the window shifted everything down one slot, so page N+1 re-served the last item of page N) — fixed by cursors; or the sentinel double-fire issuing the same cursor twice and appending a duplicate page — fixed by the status gate plus idempotent page insertion (dedup by cursor key in the cache).</details>
2. <details><summary>Why is scrollTop-based scroll restoration broken here, mechanically?</summary>With virtualization, offscreen items aren't in the DOM, so document height is an estimate that changes as real heights are measured; with variable-height media, heights differ between sessions (image load order, viewport width). A stored scrollTop lands somewhere else. An anchor (item id + pixel offset within it) is stable because identity is stable: render the window around that item, scroll it to the stored offset.</details>
3. <details><summary>Transfer: what changes for "design a chat message list"?</summary>Direction inverts: newest at bottom, history loads *upward* — prepending pages must not move the viewport, so you anchor to the first visible message and compensate scroll after prepend (the hard part). Live messages append at bottom with an auto-stick-to-bottom rule (only if already at bottom, else an unread pill — same buffered-content pattern). Cursor pagination, normalization, virtualization, and the a11y announcements all survive.</details>

## Related Notes

- [[29 - Frontend System Design/02 - Designing an Autocomplete|Designing an Autocomplete]]
- [[19 - DOM and Browser APIs/06 - Observers|Observers]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]
- [[25 - Accessibility and Inclusive UX/06 - Live Regions Loading and Announcements|Live Regions Loading and Announcements]]
- [[30 - Backend System Design/03 - API Design|API Design]] — cursor vs offset pagination, the contract this feed consumes
