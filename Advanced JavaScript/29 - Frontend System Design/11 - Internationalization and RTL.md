---
tags: [system-design, interview, i18n, rtl, localization]
module: "29 - Frontend System Design"
priority: important
status: not-started
aliases: [i18n design, localization, RTL, bidi]
---

# Internationalization and RTL

## Maturity Target

- Priority: #important
- Study time: 35 minutes
- Interview signal: Raise i18n/RTL in the Requirements phase unprompted and design for it — message formatting, layout direction, locale data — not string swapping.
- Production signal: Your components work in RTL and don't hardcode date/number/plural formats or English word order.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|Color, Contrast, Motion, Zoom and Reflow]]

## Source Anchors

- [MDN — Intl](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl)
- [W3C — Internationalization](https://www.w3.org/International/techniques/authoring-html)
- [MDN — CSS logical properties](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values)

## 1. Concept

Simple version: i18n is a design constraint, not a late translation pass. Asking "which locales and does that include RTL?" in Requirements changes the architecture.

The real dimensions:

- **Message formatting, not concatenation** — never build sentences by joining strings; word order, gender, and pluralization differ per language. Use ICU MessageFormat / `Intl` so plurals (`Intl.PluralRules`), dates (`Intl.DateTimeFormat`), numbers/currency (`Intl.NumberFormat`), and relative time (`Intl.RelativeTimeFormat`) are locale-correct.
- **Layout direction (RTL)** — Arabic/Hebrew flip the layout. Use **CSS logical properties** (`margin-inline-start`, not `margin-left`; `inset-inline`) and `dir="rtl"` so mirroring is automatic instead of a second stylesheet. Icons with direction (back arrows, progress) flip too.
- **Locale data loading** — translations and locale bundles are payload; load the active locale, split the rest, don't ship all languages to everyone.
- **Text expansion** — German/Finnish run ~30–40% longer than English; layouts must not assume string length (truncation, wrapping, no fixed-width buttons).
- **Formatting inputs** — accept locale-specific number/date input, collation for sorting (`Intl.Collator`).

> [!tip] Design-round move: put "locales + RTL?" in your first requirements questions. If yes, it gates layout (logical properties), the component API (formatting props, not baked-in strings), bundle strategy (per-locale splitting), and testing (pseudo-localization). Retrofitting i18n is a rewrite; designing for it is cheap.

## 2. Why It Matters

i18n is a classic "did they think of it" signal — a candidate who never asks about locales reveals a single-market mindset. Mechanically, string concatenation and physical CSS properties are the two mistakes that make retrofitting expensive, so raising them early is senior. For a global product it's also a correctness issue: wrong plurals and date formats are bugs.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an app "supports Arabic" by swapping strings, but the layout is broken — the sidebar is on the wrong side, back arrows point the wrong way, and "3 items" reads wrong for Arabic plural rules.

Trace: translation ≠ internationalization. The CSS used physical properties (`left`/`margin-left`), so nothing mirrored under `dir="rtl"`; sentences were concatenated (`count + " items"`), so plural rules and word order were ignored.

```tsx
// Fix: logical properties + ICU formatting
// CSS: use margin-inline-start / inset-inline-start, set dir="rtl" on <html>
<p>{new Intl.NumberFormat(locale).format(count)}</p>
{/* plurals via ICU: "{count, plural, one {# item} other {# items}}" resolved per locale */}
<span>{t('itemCount', { count })}</span>   // library resolves plural category for the locale
```

Tradeoff: logical properties and a formatting library add upfront discipline and a small learning curve, and per-locale bundles add build complexity. But they're the difference between "true multi-locale" and "English app with translated strings that breaks in RTL." There's no cheap retrofit.

## 4. Interview Answer

Short answer:

> I treat i18n as a requirement, asking about locales and RTL up front. That means formatting via ICU/Intl for plurals, dates, numbers, and relative time instead of concatenating strings; CSS logical properties plus `dir` so RTL mirrors automatically; per-locale bundle loading so I don't ship every language to everyone; and layouts that tolerate text expansion. Translation is the last step, not the whole of internationalization.

Deeper answer:

> The two decisions that make or break retrofit cost are message formatting and layout direction. Concatenated strings bake in English word order and ignore plural/gender rules, so I use ICU MessageFormat where the library picks the plural category per locale. Physical CSS properties don't mirror, so I use logical properties and let `dir="rtl"` flip the whole layout for free, including directional icons. Both are cheap if designed in and a rewrite if bolted on — which is exactly why raising locales in the requirements phase is what keeps the cost down, not a nice-to-have.

## 5. Practice

1. <details><summary>Why is `count + " items"` a bug beyond just translation?</summary>It assumes English word order and a single plural form. Other languages place the number differently and have multiple plural categories (Arabic has six; Polish/Russian have several). ICU MessageFormat lets the locale data choose the correct form and placement; concatenation hardcodes English grammar.</details>
2. <details><summary>What makes RTL support cheap vs expensive?</summary>Using CSS logical properties (`margin-inline-start`, `inset-inline`) and a single `dir="rtl"` makes mirroring automatic — cheap. Using physical properties (`left`, `margin-left`) means every rule needs an RTL override — expensive and error-prone. The choice is made at build-the-component time, so raising RTL early is what keeps it cheap.</details>
3. <details><summary>How does i18n affect bundle strategy?</summary>Translation catalogs and locale data (e.g., `Intl` polyfill data, date libraries) are payload. Shipping all locales to every user bloats the bundle, so you split by locale and load the active one (plus lazy-load on switch). It's a data-fetching/code-splitting decision that i18n forces into the architecture.</details>

## 6. Real-World Use Cases

§3 covers number/plural formatting; the `Intl` family and locale routing carry the rest.

### Relative timestamps with `Intl.RelativeTimeFormat`

"2 hours ago" hand-rolled breaks in every non-English locale. `Intl` localizes it for free.

```ts
const rtf = new Intl.RelativeTimeFormat(navigator.language, { numeric: "auto" });
function ago(date: Date) {
  const mins = Math.round((date.getTime() - Date.now()) / 60000);
  if (Math.abs(mins) < 60) return rtf.format(mins, "minute");   // "5 minutes ago" / "il y a 5 minutes"
  return rtf.format(Math.round(mins / 60), "hour");
}
```

The platform owns the grammar per locale. See [[12 - Advanced Language Concepts/16 - Intl|Intl]].

### Locale-aware sorting with `Intl.Collator`

`Array.sort()`'s default is code-unit order — wrong for accented or non-Latin names. Sort through a collator.

```ts
const names = ["Öztürk", "Andersson", "Zulu", "Ávila"];
const collator = new Intl.Collator("sv");            // Swedish orders Ö after Z
names.sort(collator.compare);                        // locale-correct, not "Ö" as ASCII 214
```

Collation is locale-specific; never `<`-compare user-facing strings. See [[12 - Advanced Language Concepts/16 - Intl|Intl]].

### App Router locale routing + per-locale bundle

A `[locale]` segment scopes the URL and lets you load only the active locale's message catalog instead of shipping all of them.

```tsx
// app/[locale]/layout.tsx
export default async function LocaleLayout({
  children, params,
}: { children: React.ReactNode; params: { locale: string } }) {
  const messages = await import(`@/messages/${params.locale}.json`); // only this locale's bundle
  return <IntlProvider messages={messages.default} locale={params.locale}>{children}</IntlProvider>;
}
```

Per-locale splitting keeps the payload flat as languages grow. See [[29 - Frontend System Design/07 - Component API Design|Component API Design]].

## Related Notes

- [[25 - Accessibility and Inclusive UX/08 - Color Contrast Motion Zoom and Reflow|Color, Contrast, Motion, Zoom and Reflow]]
- [[29 - Frontend System Design/07 - Component API Design|Component API Design]]
- [[12 - Advanced Language Concepts/16 - Intl|Intl]]
