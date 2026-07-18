---
tags: [nextjs, seo, metadata]
module: "22 - Next.js Deep Dive"
priority: important
status: not-started
aliases: [Metadata, SEO]
---

# Metadata, SEO and the head

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain the Metadata API (static vs `generateMetadata`), why SSR matters for SEO/social, and how streaming interacts with metadata.
- Production signal: your pages have correct per-route titles, descriptions, canonical URLs, and Open Graph tags generated server-side.
- Dependencies: [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]], [[21 - React Internals and Patterns/10 - React 19|React 19]]

## Source Anchors

- [Next.js - Metadata and OG images](https://nextjs.org/docs/app/getting-started/metadata-and-og-images)
- [Next.js - generateMetadata](https://nextjs.org/docs/app/api-reference/functions/generate-metadata)
- [react.dev - Support for Document Metadata (React 19)](https://react.dev/blog/2024/12/05/react-19#support-for-metadata-tags)
- [Google Search Central - JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)

## 1. Concept

Document metadata — `<title>`, `<meta name="description">`, Open Graph/Twitter cards, canonical links — must be in the HTML `<head>` and, for reliability, must be present in the **server-rendered HTML** so crawlers and social scrapers see it without executing JavaScript.

Next.js provides the **Metadata API** in the App Router: export a `metadata` object (static) or a `generateMetadata` function (dynamic) from a page/layout, and Next injects the tags server-side.

```tsx
// Static
export const metadata = {
  title: "Dashboard",
  description: "Your account overview",
};

// Dynamic — depends on route data
export async function generateMetadata({ params }) {
  const product = await getProduct(params.id);   // memoized with the page's fetch
  return {
    title: product.name,
    description: product.summary,
    openGraph: { images: [product.image] },
    alternates: { canonical: `/products/${product.id}` },
  };
}
```

## 2. Why It Matters

- SEO and social sharing are business-critical for public pages, and they hinge on server-rendered metadata — a common reason to choose SSR/SSG over a client-only SPA.
- The classic failure (metadata set client-side via effects) means crawlers and link-preview bots see empty/default tags — invisible in search, broken share cards. Explaining *why* server rendering fixes this is a strong signal.

## 3. Why Client-Side Metadata Fails

Search crawlers and social scrapers (Slack, Twitter, Facebook link unfurlers) fetch your URL and read the *initial HTML*. Many don't execute JavaScript at all, or do so unreliably/with delay. If your title/OG tags are injected by a client effect (`useEffect` → `document.title`, old `react-helmet` in a CSR app), the initial HTML has the defaults → the crawler indexes "My App" for every page and the share card is blank.

Server-rendered metadata (Next Metadata API, or React 19's native `<title>`/`<meta>` hoisting — [[21 - React Internals and Patterns/10 - React 19|React 19]]) puts the correct tags in the HTML before it's sent, so non-JS consumers get them. This is the concrete, business-facing reason [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|server rendering]] matters beyond performance.

## 4. Streaming and Metadata

With streaming/PPR, the body can stream in chunks — but metadata must be in the `<head>`, which is sent first. Next handles this: it resolves `generateMetadata` (and, under Cache Components, tracks its data access separately from the page body) and emits the head before/independently of the streamed body, so crawlers still get complete metadata even as the body streams. React 19's metadata hoisting also ensures tags rendered deep in the tree land in `<head>` correctly during streaming SSR.

Practical note: `generateMetadata` fetches are request-memoized with the page's own fetches, so fetching the product in both `generateMetadata` and the page component doesn't double-fetch ([[22 - Next.js Deep Dive/06 - Data Fetching Patterns|Request Memoization]]).

## 5. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a migrated CSR app; product pages don't appear in Google, and Slack shows blank previews.

Buggy version — metadata in an effect:

```tsx
"use client";
function ProductPage({ id }) {
  const product = useProduct(id);
  useEffect(() => {
    document.title = product?.name ?? "Store";      // ❌ runs only in a JS-executing browser
  }, [product]);
  // OG tags injected client-side too
}
```

Trace: Googlebot/Slackbot fetch the URL → the initial HTML has `<title>Store</title>` and no OG image (the client effect hasn't run for them) → every product indexes as "Store," share cards are blank. The page "works" for human users with JS, hiding the problem in dev.

Production-safe fix — server metadata:

```tsx
// Server Component page (no "use client")
export async function generateMetadata({ params }) {
  const product = await getProduct(params.id);
  return {
    title: `${product.name} — Store`,
    description: product.summary,
    openGraph: { title: product.name, images: [{ url: product.image }] },
    alternates: { canonical: `/products/${product.id}` },
  };
}
export default async function ProductPage({ params }) {
  const product = await getProduct(params.id);  // memoized — same fetch as metadata
  return <ProductView data={product} />;
}
```

Now the correct title, description, canonical, and OG image are in the server HTML for every crawler and scraper.

Tradeoffs: `generateMetadata` requires the metadata's data to be fetchable server-side (fine for public products; awkward for purely client-state-derived titles like an unsaved draft name — those can stay client-side since crawlers don't need them). Dynamic metadata also means the route can't be a pure static file if the metadata depends on request data — but it's typically cacheable/ISR like the page. And you still need the SEO fundamentals metadata can't provide: semantic HTML, proper status codes (a "not found" must return 404, not 200 with an error UI), structured data, and performance ([[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals]] are a ranking factor).

## 6. Interview Answer

Short answer:

> Metadata — title, description, canonical, Open Graph — must be in the server-rendered `<head>` because crawlers and social scrapers read initial HTML and often don't run JS. Next's Metadata API exports a static `metadata` object or a dynamic `generateMetadata` function per route, injected server-side. Setting metadata in a client effect means bots see defaults — pages don't rank and share cards break.

Deeper answer:

> `generateMetadata` fetches are request-memoized with the page's fetches, so no double-fetch. With streaming/PPR the head is emitted before the streamed body, and React 19 hoists `<title>`/`<meta>` rendered anywhere in the tree into `<head>` — so metadata stays complete under streaming. Server metadata is the business-facing reason SSR/SSG beats a client-only SPA for public pages, alongside SEO fundamentals metadata can't fix: correct status codes (real 404s), semantic HTML, structured data, and Core Web Vitals as a ranking signal.

## 7. Practice

1. <details><summary>A React SPA sets `document.title` and OG tags via effects. Human users see correct titles; Google indexes them all as the app name. Why?</summary>Googlebot (and social scrapers) primarily read the initial server HTML; many don't execute JS, or do so on a delayed second pass. The effects that set the title/OG tags run only in a full JS-executing browser, so the crawler sees the static default in the HTML. Fix: render metadata server-side (Next Metadata API / SSR) so the correct tags are in the initial HTML for non-JS consumers.</details>

2. <details><summary>You fetch the product in both `generateMetadata` and the page component. Double fetch?</summary>No — within one render, identical fetches are request-memoized (and DB/ORM reads wrapped in React `cache()` dedupe similarly). So `generateMetadata` and the page share one fetch of the product. This is why splitting metadata into its own function is cheap: it reuses the page's data access rather than adding a round trip.</details>

3. <details><summary>Why must a "product not found" page return HTTP 404 and not 200 with a "not found" UI?</summary>Status codes are signals to crawlers and clients. A 200 with error content ("soft 404") tells Google the page exists and is valid, so it may index the error page and keep the URL in results; it also breaks caching/monitoring semantics. Returning a real 404 (via `notFound()` in Next) tells crawlers to drop the URL, prevents indexing junk, and is correct HTTP. SEO depends on honest status codes, which the Metadata API alone doesn't handle.</details>

4. <details><summary>Under streaming SSR, how does metadata stay complete if the body streams in chunks?</summary>The `<head>` is sent first and independently of the streamed body: Next resolves `generateMetadata` and emits the head before/around the body stream, and React 19 hoists metadata tags rendered anywhere in the component tree into `<head>` during streaming. So even though body content arrives progressively, crawlers receive a complete head with title/description/OG up front. Under Cache Components, metadata's data access is tracked separately from the page so it's resolved appropriately.</details>

## Related Notes

- [[22 - Next.js Deep Dive/01 - Rendering Strategies|Rendering Strategies]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[21 - React Internals and Patterns/10 - React 19|React 19]]
- [[13 - Performance and Memory/10 - Core Web Vitals and Measuring|Core Web Vitals and Measuring]]
- [[01 - Roadmap|Roadmap]]
