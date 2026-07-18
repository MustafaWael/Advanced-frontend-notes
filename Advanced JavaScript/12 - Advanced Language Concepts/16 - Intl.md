---
tags: [javascript, intl, i18n, formatting]
module: "12 - Advanced Language Concepts"
priority: important
status: not-started
aliases: [Intl, NumberFormat, DateTimeFormat]
---

# Intl

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can name the main `Intl` APIs and explain why they replace hand-rolled formatting and why locale-correctness matters.
- Production signal: you format numbers, currency, dates, relative times, and sorting with `Intl` instead of manual string building or heavy libraries.
- Dependencies: [[12 - Advanced Language Concepts/12 - Numbers and Floating Point|Numbers and Floating Point]], [[12 - Advanced Language Concepts/13 - Strings Unicode and Template Literals|Strings, Unicode and Template Literals]]

## Source Anchors

- [MDN - Intl](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl)
- [MDN - Intl.NumberFormat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat)
- [MDN - Intl.DateTimeFormat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/DateTimeFormat)
- [MDN - Intl.RelativeTimeFormat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/RelativeTimeFormat)

## 1. Concept

`Intl` is the built-in internationalization API: locale-aware formatting and comparison, implemented natively (backed by the browser's Unicode/CLDR data), so you don't ship or hand-write locale rules. The workhorses:

- **`Intl.NumberFormat`** — numbers, currency, percent, units, with locale grouping/decimal separators.
- **`Intl.DateTimeFormat`** — dates and times in locale conventions and time zones.
- **`Intl.RelativeTimeFormat`** — "3 days ago", "in 2 hours".
- **`Intl.Collator`** — locale-correct string comparison/sorting (accents, case, language rules).
- **`Intl.ListFormat`**, **`Intl.PluralRules`**, **`Intl.Segmenter`** ([[12 - Advanced Language Concepts/13 - Strings Unicode and Template Literals|graphemes]]).

```js
new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(1234.5);
// "1.234,50 €"  ← German grouping/decimal, symbol placement
new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(1234.5);
// "$1,234.50"
```

## 2. Why It Matters

- Formatting is everywhere (prices, dates, counts), and hand-rolled versions are wrong for most of the world: `$` vs `€` placement, `1,234.50` vs `1.234,50`, non-Gregorian calendars, RTL, pluralization beyond "s". `Intl` is correct and free.
- It replaces heavy dependencies (moment.js, accounting.js) with native APIs — a real bundle-size and correctness win that seniors are expected to reach for.

## 3. The Main APIs, Concretely

```js
// Currency & units — no manual symbols or rounding
new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(1234567.89);
// "₹12,34,567.89"  ← Indian digit grouping (lakh/crore), automatic

// Dates with time zones
new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeStyle: "short", timeZone: "America/New_York" })
  .format(new Date());

// Relative time
const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
rtf.format(-1, "day");   // "yesterday"   (numeric:"auto" → words when natural)
rtf.format(3, "hour");   // "in 3 hours"

// Locale-correct sorting (NOT default Array.sort, which is code-unit / UTF-16 order)
["ä", "z", "a"].sort(new Intl.Collator("de").compare);   // ["a", "ä", "z"]
```

> [!tip] Reuse formatter instances — they're expensive to construct
> Building an `Intl.NumberFormat`/`DateTimeFormat` loads and resolves locale data — non-trivial. Creating one *inside* a render or a `.map` over a large list constructs it per item, a real performance cost. Construct once (module scope, `useMemo`, or a cached map keyed by locale+options) and reuse `.format()`. This is the most common `Intl` performance mistake.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a global e-commerce app hand-formats prices and dates; users in Europe and India see wrong formats, and a product list janks.

Buggy version:

```jsx
function formatPrice(n) {
  return "$" + n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");  // hard-coded $ and US grouping
}
function ProductRow({ p }) {
  const date = new Date(p.createdAt);
  const formatted = `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`; // US date, no TZ
  return <div>{formatPrice(p.price)} — {formatted}</div>;
}
```

Trace the wrongness: `$` is hardcoded (a German user paying in EUR sees `$` with US grouping); `1.234,56` grouping is inverted for Europe; the date is US-order and ignores the user's time zone; and none of it respects the user's locale. Plus a large product list rebuilds strings per row.

Production-safe fix — Intl, formatters reused:

```jsx
const priceFmt = new Map();   // cache formatters per currency
function getPriceFmt(locale, currency) {
  const key = locale + currency;
  if (!priceFmt.has(key)) priceFmt.set(key, new Intl.NumberFormat(locale, { style: "currency", currency }));
  return priceFmt.get(key);
}

function ProductRow({ p, locale }) {
  const price = getPriceFmt(locale, p.currency).format(p.price);
  const date = new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(new Date(p.createdAt));
  return <div>{price} — {date}</div>;
}
```

Tradeoffs: `Intl` is correct and native but locale *selection* is your responsibility (from the user's setting, `Accept-Language`, or `navigator.language`) — guessing wrong is its own bug. Output isn't guaranteed byte-stable across browser/engine versions (CLDR updates change spacing/symbols), so don't snapshot-test exact `Intl` strings or rely on them as stable keys. Time zones require passing `timeZone` explicitly for server-consistent rendering (SSR uses the *server's* zone otherwise — a hydration mismatch risk, [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|hydration]]). For complex date math (parsing, arithmetic, zones) pair `Intl` formatting with the `Temporal` API (or a light date library) — `Intl` formats, it doesn't do date arithmetic.

## 5. Interview Answer

Short answer:

> `Intl` is the native i18n API: `NumberFormat` (numbers/currency/percent/units), `DateTimeFormat` (dates/times/time zones), `RelativeTimeFormat` ("3 days ago"), and `Collator` (locale-correct sorting). It's backed by the browser's CLDR data, so it correctly handles grouping separators, currency placement, calendars, and language sorting that hand-rolled code and even `Array.sort` (which sorts by UTF-16 code unit) get wrong — with zero bundle cost.

Deeper answer:

> The main performance rule is to construct formatters once and reuse them — building one is expensive (loads locale data), so per-render or per-list-item construction is the classic mistake. `Intl` replaces heavy libraries (moment, accounting), but you still own locale selection, and its output isn't byte-stable across engine/CLDR versions (don't snapshot exact strings or use them as keys). For SSR, pass an explicit `timeZone` to avoid server/client mismatch, and pair `Intl` formatting with `Temporal` or a date library for actual date arithmetic — `Intl` formats, it doesn't compute.

## 6. Practice

1. <details><summary>Why does `["ä","z","a"].sort()` order incorrectly for German, and what fixes it?</summary>Default `Array.sort` compares by UTF-16 code unit, so "ä" (U+00E4) sorts *after* "z" (U+007A) — wrong for German where ä belongs near a. Fix: `arr.sort(new Intl.Collator("de").compare)`, which applies locale collation rules to yield `["a","ä","z"]`. `Intl.Collator` also handles case sensitivity, accent weighting, and numeric ordering options that raw code-unit comparison can't.</details>

2. <details><summary>A price list renders 5,000 rows and profiling blames Intl. Likely mistake and fix?</summary>Constructing a new `Intl.NumberFormat` inside each row's render (or the `.map`) — each construction loads/resolves locale data, so 5,000 constructions dominate. Fix: build the formatter once (module scope, `useMemo`, or a cache keyed by locale+currency) and call `.format()` per row. Formatter construction is the cost; `.format()` calls are cheap.</details>

3. <details><summary>Your SSR app shows a different time on the server-rendered HTML than after hydration. How does Intl relate, and the fix?</summary>`Intl.DateTimeFormat` without an explicit `timeZone` uses the runtime's zone — the *server's* zone during SSR, the *user's* in the browser — so the strings differ, causing a hydration mismatch. Fix: pass an explicit `timeZone` (a known zone or the user's, derived consistently) so server and client format identically; or render the raw timestamp and format on the client after mount if the user's zone is only known there. Determinism across environments is the requirement.</details>

4. <details><summary>Why shouldn't you snapshot-test the exact output of `Intl.NumberFormat(...).format(1234.5)`?</summary>`Intl` output depends on the engine's bundled CLDR/ICU data, which changes across browser and Node versions — spacing (e.g., regular vs non-breaking space before a currency symbol), symbol forms, and separators can shift without your code changing. An exact-string snapshot becomes brittle and breaks on engine upgrades. Test behavior/semantics (parses back, correct magnitude, right currency) rather than the precise glyph sequence, and never use formatted strings as stable identifiers/keys.</details>

## Related Notes

- [[12 - Advanced Language Concepts/12 - Numbers and Floating Point|Numbers and Floating Point]]
- [[12 - Advanced Language Concepts/13 - Strings Unicode and Template Literals|Strings, Unicode and Template Literals]]
- [[12 - Advanced Language Concepts/10 - BigInt Date RegExp JSON|BigInt Date RegExp JSON]]
- [[14 - JavaScript in React and Next.js/10 - Hydration Related JavaScript Issues|Hydration Related JavaScript Issues]]
- [[01 - Roadmap|Roadmap]]
