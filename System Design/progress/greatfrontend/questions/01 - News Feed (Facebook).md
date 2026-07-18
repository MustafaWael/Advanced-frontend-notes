# 01 - News Feed (e.g. Facebook)

**Source:** https://www.greatfrontend.com/questions/system-design/news-feed-facebook
**Summary:** Design a web news feed (browse posts, react, create posts) — a classic FE system design question forcing tradeoffs around rendering (CSR vs SSR), cursor pagination, a normalized client store, virtualization, and optimistic/offline-safe writes.

> Difficulty: Medium · Recommended duration: ~30 mins · Author: Yangshun Tay (Ex-Meta)
> Interview tip: cover requirements → rendering/navigation defaults → state shape → API shape first. Only go into pagination edge cases, virtualization, stale sessions, or live updates if asked.

---

## R — Requirements

### Functional (core scope)
- Browse a news feed of posts by the user and their friends.
- Like/react to feed posts.
- Create and publish new posts (text + image primarily).
- Infinite scrolling pagination UX; surface newer posts at the top without disrupting reading.
- Out of core scope (follow-up depth only): commenting, sharing, single-post surface, feed ranking, ads, back-end fan-out.

### Non-functional
- Render initial feed quickly (fast first paint / LCP); load more as user scrolls.
- Handle long-lived sessions (tab open for hours) and stale data.
- Smooth scroll performance with a growing DOM (INP matters most).
- Web-first; mobile is nice-to-have, not a priority.
- Resilience: offline reads, safe retryable writes.

---

## A — Architecture / High-level design

### Rendering approach: CSR by default
- **SSR:** server generates full HTML → fast first paint, strong SEO; client hydrates for interactivity.
- **CSR:** minimal HTML shell + JS bundles; browser fetches data and renders. Great interactivity after load; slower cold start, weaker SEO.
- **Hybrid:** SSR for initial page, CSR after hydration.

For a **personalized, signed-in feed**, SEO doesn't matter (content is personalized), so **CSR is the safe default answer** — it's a long-session state-management tradeoff, not a claim that CSR has the fastest cold start. Keep LCP competitive with tight budgets on app-shell bytes, initial feed data, and critical JS. Use **SSR/hybrid for public post permalinks, logged-out pages, marketing surfaces**. Frameworks (Next.js, TanStack Start) let you mix strategies per route.

### Navigation: SPA
- SPA keeps **shared client state** alive: cached entities, optimistic updates, composer drafts, scroll position.
- Opening a post from the feed can render nearly instantly because post/author/media are already in the store — only comments need fetching.
- MPA tears down page state on every navigation → slower transitions, lost in-memory state.

### Architecture layers (4 layers)
| Layer | Responsibility | Example tech |
|---|---|---|
| **View** | Feed page, post detail, feed posts, composer; renders store data, triggers actions | React / Vue / Svelte |
| **Store** | Source of truth for client state: feed, posts, users, composer, optimistic updates, freshness | Redux / Zustand / Jotai |
| **Data access** | Network requests, parsing, caching policy, pagination, retries, normalization | TanStack Query / RTK Query / Relay / Apollo |
| **Server** | HTTP endpoints: feed, single post, create post, media upload, reactions/shares | — |

In an SPA, Store + Data access initialize once and persist for the whole session. Every later optimization (virtualization, optimistic updates, outbox, stale-feed handling) slots into exactly one layer.

---

## D — Data model / Entities

Key idea: **the feed is NOT a nested array of post objects** — it's an ordered list of post IDs + pagination/freshness metadata, with canonical post/user/media records stored alongside in a **normalized store**.

### Post (canonical feed item)
```ts
type PostBody = {
  text: string;
  entities: Array<{
    type: 'mention' | 'hashtag' | 'link';
    start: number; // inclusive
    end: number;   // exclusive (String.prototype.slice semantics)
    userId?: string;
    url?: string;
  }>;
};

type ReactionType = 'like' | 'love' | 'haha' | 'wow' | 'sad' | 'angry';

type EngagementSummary = {
  reactions: Record<ReactionType, number>;
  totalReactions: number;
  commentCount: number;
  shareCount: number;
};

type Post = {
  id: string;
  authorId: string;      // reference, not nested User
  body: PostBody;
  mediaIds: string[];    // references, not nested Media
  engagementSummary: EngagementSummary;
  viewerReaction: ReactionType | null;
  viewerHasShared: boolean;
  createdAt: number;
};
```

### User
```ts
type User = {
  id: string;
  name: string;
  handle: string;
  profilePhotoUrl: string;
  isVerified: boolean;
  relationshipToViewer: { isFriend?: boolean; isFollowing?: boolean; isMuted?: boolean; isBlocked?: boolean };
};
```
Users are globally cached entities — a profile change updates everywhere at once; no duplicated nested user blobs, no repeated fetches.

### Feed (ordered IDs + pagination/freshness metadata)
```ts
type Feed = {
  id: string;
  postIds: string[];
  olderCursor: string | null;
  newerCursor: string | null;
  hasOlder: boolean;
  hasNewer: boolean;
  lastFetchedAt: number | null;
};
```
Older posts append at the bottom on scroll; newer posts can be fetched separately and merged at the top later.

### Normalized store
```ts
type Store = {
  feedsById: Record<string, Feed>;
  postsById: Record<string, Post>;
  usersById: Record<string, User>;
  mediaById: Record<string, Media>; // { id, src, previewSrc?, alt, width, height }
  composerDraft: ComposerDraft;     // body, mediaIds, uploadState, submitState
};
```
- **Why normalize:** same user appears as author / resharer / commenter in many places. Denormalized nested posts require finding and rewriting every embedded copy on any change. Normalized: update `usersById[id]` once, reflected everywhere; reactions update one canonical `Post`; loading more posts = merge IDs + entities, not appending nested blobs.
- Server can return normalized payloads (favors weak client devices — what large feed products do) or nested payloads that the data access layer normalizes (favors API simplicity).

---

## I — Interface definition (API)

| Source → Destination | Type | Functionality |
|---|---|---|
| Server → Data access | HTTP | Feed posts, single posts, mutation responses |
| Data access → Server | HTTP | Fetch feed; writes (create post, media upload, reactions, shares) |
| Data access → Store | JS | Normalize responses; write entities + pagination state |
| Store → View | JS | Rendered state: posts, reactions, drafts, freshness |

**Identity comes from the authenticated session (cookies/token), never a client-supplied `userId` param** — a caller-supplied userId is a security mistake.

### Feed fetch
- `GET /feed` with params: `count`/`limit`, `cursor`, direction (`older`/`newer`). Supports initial load, downward infinite scroll, and background checks for newer posts.

### Pagination deep dive (the key API discussion)

**Offset-based** — `?offset=20&limit=10`:
- ✅ Simple; supports jumping to arbitrary pages.
- ❌ New posts shift offsets → **duplicate or missing items** (e.g., page size 3, fetched F/E/D; posts H/G arrive; next offset page returns E/D/C — E and D are duplicates).
- ❌ Large offsets are slow — DB must skip increasing numbers of rows.
- Best fit: relatively **static, page-numbered lists** (search results, admin tables).

**Cursor-based (keyset)** — "next 10 after post ID X" (cursor = unique ID or timestamp marking the page boundary):
- ✅ Stable under inserts/deletes/re-ranking; same example correctly returns C/B/A next.
- ✅ Efficient regardless of dataset size (no skipping).
- ✅ Enables **bidirectional navigation**: scroll down for older, separately check for newer at the top.
- ❌ No random page jumps.
- **Clear choice for a dynamic feed.** *(Reference: Evolving API Pagination at Slack.)*

**Dynamic loading count:** size the initial `count` from `window.innerHeight` (CSR knows viewport before first request); server-rendered initial responses must slightly overfetch, then adapt.

### HTTP caching, dedupe, idempotency
- Feed/post responses: short-lived `Cache-Control` + `ETag` (cheap `304`), `stale-while-revalidate` to paint cached data while refetching (great for detail→feed back-navigation).
- **Dedupe in-flight identical requests** and cancel superseded ones via `AbortController` (TanStack Query/Relay do this by default).
- **Idempotency keys on all writes**, generated **at submit time** (not send time) — a UUID in the body or `Idempotency-Key` header — so any retry (client, service worker, proxy) carries the same key and the server dedupes instead of creating duplicates.

### Other endpoints
| Endpoint | Purpose |
|---|---|
| `GET /posts/{postId}` | Single post / permalink |
| `PUT /posts/{postId}/reaction` | Set/change viewer reaction |
| `DELETE /posts/{postId}/reaction` | Remove reaction |
| `POST /media/uploads` | Upload media first → returns `mediaId` (often a presigned URL for direct-to-blob-storage upload) |
| `POST /posts` | Create post: `{ body: '...', mediaIds: [...] }` |

**Post creation flow:** upload binary first → get `mediaId` → create post as a small JSON request. Response is the single post + referenced entities, written straight into the normalized store (merge users/media, prepend post ID to `feed.postIds`; usually with optimistic UI — temp local post reconciled with the canonical response):

```json
{
  "post": {
    "id": "124", "authorId": "456",
    "body": { "text": "Hello world", "entities": [] },
    "mediaIds": ["m_1"],
    "engagementSummary": { "reactions": { "like": 20, "haha": 15 }, "totalReactions": 35, "commentCount": 0, "shareCount": 0 },
    "viewerReaction": null, "viewerHasShared": false, "createdAt": 1620639583
  },
  "users": [{ "id": "456", "name": "John Doe" }],
  "media": [{ "id": "m_1", "src": "https://www.example.com/feed-images.jpg", "alt": "An image alt", "width": 1200, "height": 800 }]
}
```

---

## O — Optimizations & deep dives

### Feed list
- **Virtualized lists:** render only viewport + overscan. Facebook replaces off-screen post contents with spacer `<div>`s of measured height (`style="height: 300px"`) — preserves scroll position, removes heavy subtrees. Benefits: fewer DOM nodes/layouts to paint, cheaper virtual-DOM diffing. Needs stable keys, measurement caches, recomputation when image dimensions arrive. Tradeoffs: focused elements unmount when scrolled away (must restore focus / keep mounted); find-in-page (Cmd+F) can't see unmounted content.
- **Infinite scrolling:** render a bottom marker element; prefetch ~one viewport height before the end (can adapt to network speed / scroll speed). Two implementations: throttled `scroll` handler + `getBoundingClientRect` (worse — forces layout synchronously) vs **Intersection Observer (preferred)** — browser batches visibility checks, no polling.
- **Loading indicators:** prefer **skeleton/shimmer placeholders** shaped like a post over spinners — they reserve layout so real content swaps in with minimal jump.
- **Scroll restoration:** cache feed data + scroll position in the store; back-navigation from post detail renders instantly with no round trip.
- **Stale feeds:** for tabs left open hours, options: prompt refresh when `lastFetchedAt` is old; auto-prepend (risky for scroll position); Facebook force-refreshes after a duration. **Best middle ground: background-fetch newer posts + "New posts available" banner** — preserves reading position, user controls the merge. Also consider **server-driven invalidation** over the live-update channel (version/high-water-mark push) for viral or removed posts.
- **Cross-tab consistency:** optimistic update in one tab leaves the other stale. Use **`BroadcastChannel`** from the data access layer on every canonical-entity mutation; with IndexedDB-backed stores, Web Locks API can elect a leader tab to own the socket/polling.

### Feed post
- **Data-driven dependencies (code splitting per post format):** Facebook supports 50+ post formats — don't ship all renderers upfront, but naive lazy loading adds a data→code round trip. Relay's `@match` / `@module` directives return **module metadata alongside the GraphQL payload**, so the client downloads only the matched renderer:
  ```graphql
  ... on Post {
    content @match {
      ...TextPostFragment @module(name: "TextComponent.react")
      ...ImagePostFragment @module(name: "ImageComponent.react")
    }
  }
  ```
  Caveat: avoid a data-then-code waterfall — keep common above-the-fold renderers in Tier 2 or prefetched.
- **Mentions/hashtags — message format options:**
  - **Entity ranges (recommended):** plaintext once + `{type, start, end, userId?/url?}` ranges (start inclusive, end exclusive). Compact, renderable on any client; index maintenance is a composer concern only.
    ```json
    { "text": "Check out @greatfrontend at https://www.greatfrontend.com #webdev",
      "entities": [
        { "type": "mention", "start": 10, "end": 24, "userId": "u_99" },
        { "type": "link", "start": 28, "end": 57, "url": "https://www.greatfrontend.com" },
        { "type": "hashtag", "start": 58, "end": 65 } ] }
    ```
  - **Custom syntax:** e.g. `[[#1234: HBO Max]]`; hashtags need only a render-time regex. Lightweight if entity types won't grow.
  - **Rich text editor formats** (Lexical/TipTap/Slate/Draft.js `RawDraftContentState` = blocks + entityMap): extensible but verbose on the wire.
  - **HTML (anti-pattern):** direct XSS vector, couples API to web markup, hard to reuse on iOS/Android or re-decorate later.
- **Rendering rich text safely (XSS):** output-encode plaintext (framework default — avoid `dangerouslySetInnerHTML` unless DOMPurify-sanitized); **validate `href` schemes against an allowlist (`http`, `https`, `mailto`)** — `javascript:`/`data:` URLs in entities are clickable bombs; `rel="noopener noreferrer"` on new-tab links; restrictive **CSP** (`default-src 'self'`, tight `script-src`, `img-src` limited to media CDN) as defense in depth.
- **Images:** CDN; modern formats (AVIF → WebP → JPEG via `<picture>` fallback); meaningful `alt` (FB generates via ML); `loading="lazy"` or IntersectionObserver for earlier control; `srcset`/`<picture>` + viewport dimensions sent to server for right-sized images; **`width`/`height` (or `aspect-ratio`) to reserve space → less CLS**; adaptive loading by network (prefetch on WiFi, low-res click-to-load on poor connections); LQIP/BlurHash progressive placeholders. **Upload side:** strip EXIF (GPS, device IDs) via `<canvas>` re-encode, honor orientation flag, resize client-side to largest displayed size.
- **Lazy-load interaction code (Tier 3):** reactions popover, ellipsis menu, hover cards — load on idle, on demand (hover/click), or prefetch on pointer-down.
- **Optimistic updates:** immediately reflect reaction + updated count; roll back + show error on failure. Built into Relay/SWR/React Query. Edge cases: **server response is authoritative** (its `engagementSummary` wins); racing mutations need last-writer-wins / server sequence numbers; offline writes go to the outbox with a pending indicator; idempotency keys keep retries safe. Normalized store means one canonical record updates every surface.
- **Timestamps:** multilingual options: raw timestamp + client formatting (flexible, ships locale rules); server-translated (no client rules, but inflexible); **`Intl.DateTimeFormat` / `Intl.RelativeTimeFormat` (best of both — native)**. Refresh recent relative timestamps ("2 minutes ago") with a low-frequency timer in long sessions; old ones can stay static.
  ```js
  new Intl.RelativeTimeFormat('zh-CN', { numeric: 'always', style: 'long' }).format(-1, 'day'); // 1天前
  ```
- **Icons:** separate images (many requests) vs spritesheet (one request, complex) vs icon fonts (screen-reader/FOUT issues) vs SVG file (flicker, per-file request) vs **inlined SVG (FB/Twitter's choice — crisp, no extra request, but inflates payload and isn't independently cacheable)**.
- **Truncation & counts:** "See more" for long posts; abbreviate big counts ("John, Mary and 103K others", not "103,312"); never send the full reactor list; server-vs-client formatting tradeoffs mirror timestamps.

### Composer
- WYSIWYG via `contenteditable` — but it's a browser primitive, not a production editor; use battle-tested libraries (Lexical, TipTap, Slate; Draft.js deprecated).
- **Paste/drop is an XSS entry point:** intercept `paste`/`drop`, take `text/plain` from DataTransfer and discard `text/html` (or sanitize with an explicit tag whitelist).
- **Internal editor model ≠ wire format:** editor can use a rich tree model for selection/undo, serialize to compact entity ranges at the API boundary — also enables cross-platform (web/iOS/Android) rendering.
- Lazy-load optional tools most sessions never open: image uploader, GIF/emoji/sticker pickers, background images.

### Networking, resilience, offline, retries
- **Error states:** inline error/toast/retry for transient failures (failed page, dropped reaction); full fallback + retry button only for total initial-load failure.
- **Offline reads:** Service Worker caches app shell + last N feed pages + recent media (cache-first for shell/media, stale-while-revalidate for feed pages, network-only for writes); persist query cache to IndexedDB; show "connection lost" banner and cached-post indicators.
- **Offline writes — outbox pattern:** on submit, write pending mutation to IndexedDB keyed by its idempotency key → apply optimistic update → fire request. Success drops the entry; failure retries. Background Sync API can flush after tab close (Safari lacks it — best-effort only; keep in-tab retry loop as the correctness path).
- **Retries:** exponential backoff + jitter (avoids thundering herd); cap retry count; short-circuit non-retryable statuses (400/401/403/404/422). Combined with dedupe + idempotency keys, the write path is safe under any mix of retries.

### Comments & live updates (follow-up depth)
- Comments: cursor pagination, same drafting/optimistic-update patterns, lazy-loaded pickers; post-detail surface loads replies only on demand.
- Live update transports: short polling (simple, chatty) < long polling < **SSE** (server push over HTTP, auto-reconnect via `Last-Event-ID`) < **WebSockets (default at Facebook scale — full-duplex, multiplexes comments/reactions/typing over one socket)**. Polling ok for low-priority freshness checks (new-post banner).
- **Subscribe only for visible posts** (unsubscribe when scrolled away); **throttle/debounce hot posts** (celebrities) down to count-only updates — nobody can read every comment anyway, and it saves client CPU + server fan-out.

### Performance & metrics
- **Core Web Vitals:** LCP (first useful feed content), **INP (the key metric for a long-lived interactive session — jank compounds over thousands of interactions)**, CLS (images/skeletons keeping layout stable).
- **Budgets (interview-level):** p75 LCP < 2.5s on mid-range mobile, p75 INP < 200ms, CLS < 0.1; JS ~100–150 KB gzipped for the first visual shell, ~300 KB for above-the-fold interactivity. Segment by device class + network.
- **Facebook loading tiers:** Tier 1 = shell + skeleton + critical CSS; Tier 2 = above-the-fold feed rendering, common renderers, basic actions; Tier 3 = everything that can wait (pickers, hover cards, logging, rare renderers).
- **Splitting levels:** route-level, data-driven renderer chunks, interaction-triggered chunks, idle/intent prefetch (gated on device/network). Beware: splitting helps LCP but can hurt INP if a first tap waits on a chunk — prefetch common interactions on idle.
- **Main thread:** move payload parsing / entity-range rendering / media metadata decoding to Web Workers or `scheduler.postTask()`; no layout-forcing `onScroll` handlers; `content-visibility: auto` (+ `contain-intrinsic-size`) as a secondary primitive for surrounding chrome.
- **Measure:** `web-vitals` library → RUM pipeline.

### Accessibility
- **Feed list:** `role="feed"`, `aria-label="Home feed"`, skip link to jump past chrome.
- **Posts:** `role="article"`, `aria-labelledby` pointing to the author-name element; native `<button>`/`<a>` over clickable divs; `tabindex="-1"` on detail-page headings for programmatic focus.
- **Interactions:** keyboard-accessible reactions (FB shows a focus-only button to open the reactions menu); `aria-label` on icon-only buttons; visible focus indicators; ≥44×44px touch targets (WCAG 2.5.5); FB ships feed keyboard shortcuts (Shift+?) as an enhancement, not a replacement for tab order.
- **Dynamic updates/motion:** `aria-live="polite"` for the new-posts banner; update accessible names for count bumps (don't announce each one); `aria-live="assertive"` only for real errors; honor `prefers-reduced-motion` (disable shimmer/tweens); preserve/restore focus when virtualization unmounts a focused post.

### Internationalization
- **RTL:** CSS logical properties (`margin-inline-start`, `padding-inline`, `inset-inline`) + flex/grid so `dir="rtl"` flips layout; retrofitting physical properties later is painful — author logically from day one.
- **Bidi text:** `dir="auto"` on the post body so the base direction follows the first strong character.
- **Plurals/counts:** `Intl.PluralRules` + ICU MessageFormat (Arabic has 6 plural forms — never hand-roll `count === 1 ? 'like' : 'likes'`); `Intl.NumberFormat` ("103K" / "103 тыс." / "10.3萬"); `Intl.ListFormat` ("John, Mary, and 103K others").

### Telemetry & observability
- **Impressions:** reuse the IntersectionObserver primitive — a post is an impression at ≥50% visible for ≥1s, deduped per session; batch events on `visibilitychange`/`pagehide` so tracking doesn't cost INP.
- **Dwell/engagement:** per-post entry/exit timestamps, click-through on reactions/comments/shares — feeds ranking, not just dashboards.
- **RUM:** CWV broken down by device class, network, route, release, feature flag.
- **Error reporting:** Sentry-style with uploaded source maps; sample high-volume surfaces, full fidelity on the composer submit path.
- **Feature flags:** gate risky changes (new virtualization, live-update protocol), ramp % while watching INP + error rates; the data access layer is a natural place to read flags.

---

## Interview cheat sheet (one-liner answer skeleton)
1. **CSR + SPA** for the signed-in feed (SSR for public permalinks); four layers: View / Store / Data access / Server.
2. **Normalized store**: feed = ordered post IDs + cursors + `lastFetchedAt`; canonical Post/User/Media by ID.
3. **Cursor pagination** (offset breaks under inserts + slow at large offsets); dynamic `count` from viewport; idempotency keys on all writes.
4. Depth on request: virtualization + IntersectionObserver infinite scroll + skeletons; data-driven renderer chunks (`@match`/`@module`); optimistic updates + IndexedDB outbox; entity-range rich text + XSS hardening; `Intl` APIs + RTL; `role="feed"`/`aria-live` a11y; LCP/INP/CLS budgets + RUM.

## Key references
- [Rebuilding our tech stack for the new Facebook.com](https://engineering.fb.com/2020/05/08/web/facebook-redesign/) — loading tiers, data-driven deps
- [Evolving API Pagination at Slack](https://slack.engineering/evolving-api-pagination-at-slack) — cursor pagination
- [Making Instagram.com faster, Part 3 — cache first](https://instagram-engineering.com/making-instagram-com-faster-part-3-cache-first-6f3f130b9669)
- [Dissecting Twitter's Redux Store](https://medium.com/statuscode/dissecting-twitters-redux-store-d7280b62c6b1) — normalized store
- [Making Facebook.com accessible](https://engineering.fb.com/2020/07/30/web/facebook-com-accessibility/)
- [Rendering on the Web](https://web.dev/rendering-on-the-web/)
