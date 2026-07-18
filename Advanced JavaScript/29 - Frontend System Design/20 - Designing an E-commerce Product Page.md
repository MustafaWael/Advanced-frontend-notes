---
tags: [system-design, interview, ecommerce, seo, performance]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [ecommerce design, product detail page, PDP design, SEO performance]
---

# Designing an E-commerce Product Page

## Maturity Target

- Priority: #must-know
- Study time: 65 minutes
- Interview signal: Run RADIO on a product listing + detail flow covering rendering strategy (SEO + perf), the cart as shared state, real-time inventory, and Core Web Vitals — with tradeoffs.
- Production signal: You can reason about why a storefront ranks and converts, from render strategy down to the LCP image.
- Dependencies: [[29 - Frontend System Design/05 - Rendering Strategies for Design|Rendering Strategies for Design]], [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]], [[29 - Frontend System Design/10 - State Normalization and Optimistic Updates|State Normalization and Optimistic Updates]]

## Source Anchors

- [web.dev — Commerce](https://web.dev/explore/commerce)
- [Google — Core Web Vitals & Search](https://developers.google.com/search/docs/appearance/core-web-vitals)
- [Schema.org — Product](https://schema.org/Product)

## 1. Requirements

Ask: catalog size? does it need SEO (public storefront) or is it a logged-in app? personalization (recommendations, price)? inventory real-time? variants (size/color)? cart persistence across devices? checkout in scope? markets/currencies/locales? conversion/perf targets?

Design against: **a public storefront — listing + product detail — SEO-critical, variant selection, real-time-ish stock, a cross-page cart, i18n/multi-currency, aggressive perf targets.** Out of scope: payment processing internals, warehouse logistics.

The two requirements that dominate: **SEO + performance** (they gate rendering strategy and conversion) and **the cart** (shared, persistent state touched from every page).

## 2. Architecture

```
Listing (ISR/SSG) ──▶ Product Detail (ISR + client hydration for stock/cart)
        │                     │
        ▼                     ▼
   Cart store (persistent, cross-page)  ── optimistic add/remove
        │
   Data layer: catalog (cacheable GET/CDN) · inventory (fresh) · recommendations (personalized)
```

Render by route ([[29 - Frontend System Design/05 - Rendering Strategies for Design|rendering strategies]]): listing and detail **static/ISR** for SEO + instant load, with **client hydration** for the dynamic bits (live stock, cart, personalized recs) — so the SEO-critical, cacheable content is static while per-user/fresh data loads client-side. The **cart** is app-wide persistent state (its own store, mirrored to storage/server), touched from listing, detail, and header.

> [!tip] Split the page by data freshness: product copy/images (static, cache-forever, CDN), price/stock (fresh, may change — revalidate or fetch on client), recommendations (personalized, client). One page, three caching policies — the point is naming that split instead of picking one render mode for everything.

## 3. Data Model

```ts
interface Product { id; slug; title; images; variants: Variant[]; /* static-ish */ }
interface Variant { id; sku; options: Record<string, string>; price: Money; }
interface InventoryState { bySku: Map<string, { inStock: boolean; qty?: number }>; } // fresh
interface CartState {
  linesBySku: Map<string, { sku: string; qty: number }>;  // normalized by sku
  // derived: subtotal, count — computed, not stored
}
```

Cart lines keyed by **sku** (normalized) so add/increment/remove touch one entry; totals are **derived**, never stored (single source of truth). Inventory is separate from the static product because it changes on a different clock — mixing them would force the whole page to be dynamic.

## 4. Interface

**Network:** catalog `GET /products/:slug` (cacheable, CDN); inventory `GET /inventory?skus=` (fresh, batched) or a push channel for live stock; cart `POST/PATCH /cart` (or client-only + sync). Structured data (`schema.org/Product`) in the page for SEO rich results.

**Cart API:** `useCart()` → `{ lines, add, setQty, remove, subtotal, count }` — optimistic mutations, persistence handled inside.

## 5. Optimizations (ranked)

1. **SEO + rendering** — static/ISR for listing + detail so pages are crawlable and fast; server-rendered metadata/OpenGraph and `schema.org/Product` structured data ([[22 - Next.js Deep Dive/07 - Metadata SEO and the head|Metadata SEO]]); canonical URLs for variants.
2. **Core Web Vitals** — the product hero image is the **LCP**: eager, `fetchpriority=high`, responsive `srcset`, modern format ([[29 - Frontend System Design/08 - Frontend Performance for System Design|performance]]); reserve image/box space for **CLS**; keep interaction (variant switch, add-to-cart) fast for **INP**; code-split below-the-fold (reviews, recs).
3. **Cart correctness** — optimistic add-to-cart (instant feedback) with reconciliation; persist (localStorage/server) so it survives reload and syncs across devices/tabs ([[19 - DOM and Browser APIs/05 - Browser Storage|storage]]); normalized by sku; derived totals.
4. **Inventory freshness** — stock fetched/refreshed on the client (or pushed) so a static page doesn't show stale "in stock"; handle the race where stock runs out between view and add-to-cart (validate server-side on add, show a graceful "just sold out").
5. **i18n/currency** — locale/currency formatting via `Intl`, per-market pricing, RTL support ([[29 - Frontend System Design/11 - Internationalization and RTL|i18n]]).
6. **Resilience/a11y** — variant selection keyboard-accessible and announced; add-to-cart feedback via a toast/live region ([[29 - Frontend System Design/16 - Designing a Notification and Toast System|toasts]]); works without JS for core content (SSR/ISR gives this).

## 6. Interview Answer

Short answer:

> A storefront is rendered by route and by data freshness: listing and product detail are static/ISR for SEO and instant load, with client hydration for the dynamic parts — live stock, cart, personalized recommendations. The cart is app-wide persistent state normalized by SKU with derived totals, mutated optimistically and synced to storage/server. Core Web Vitals drive the detail: the product image is the LCP so it's eager and priority-hinted, layout is reserved for CLS, and interactions stay fast for INP. Structured data and server-rendered metadata handle SEO.

Deeper answer:

> The decision I'd lead with is splitting the page by data freshness rather than choosing one render mode: product copy and images are static and cache-forever on a CDN, price and stock are fresh and fetched or revalidated on the client, recommendations are personalized and client-loaded. That gives SEO and LCP from the static shell while keeping dynamic data current. The cart is the other core: normalized by SKU with derived totals so there's one source of truth, optimistic for instant feedback, and persisted plus cross-tab synced so it survives reloads. I'd call out the inventory race explicitly — a static page can show stale stock, so add-to-cart is validated server-side and I design the "sold out between view and add" state instead of pretending it can't happen. And CWV isn't decoration here — LCP and INP correlate with conversion, so the image and interaction budgets are business requirements.

## 7. Practice

1. <details><summary>Why not render the whole product page one way (all SSR or all static)?</summary>Its data has different freshness: copy/images are static (cache-forever, great for SEO/LCP), price/stock are fresh (change independently), recommendations are personalized. All-static shows stale stock; all-SSR wastes server work and ties TTFB to data on mostly-static content. Split it — static shell + client hydration for dynamic parts.</details>
2. <details><summary>The product image is your LCP. What do you do about it?</summary>Load it eagerly with `fetchpriority="high"`, serve responsive `srcset`/`sizes` in a modern format (AVIF/WebP), and reserve its box with width/height or `aspect-ratio` to avoid CLS. Don't lazy-load the LCP image (a common mistake) — that delays the very element the metric measures.</details>
3. <details><summary>How do you handle stock running out between page view and add-to-cart?</summary>Treat client stock as advisory (a static/ISR page can be stale), refresh it on the client or via push, and validate authoritatively on the server at add-to-cart. If it sold out, return a clear error and design the UI state ("This just sold out") rather than silently failing — it's a real-world eventual-consistency race, not an edge case to ignore.</details>

## Related Notes

- [[29 - Frontend System Design/05 - Rendering Strategies for Design|Rendering Strategies for Design]]
- [[22 - Next.js Deep Dive/07 - Metadata SEO and the head|Metadata, SEO and the head]]
- [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]]
- [[29 - Frontend System Design/11 - Internationalization and RTL|Internationalization and RTL]]
