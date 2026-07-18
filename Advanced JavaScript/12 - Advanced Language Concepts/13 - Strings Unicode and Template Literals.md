---
tags: [javascript, strings, unicode]
module: "12 - Advanced Language Concepts"
priority: important
status: not-started
aliases: [Unicode, UTF-16, Grapheme, Tagged Templates]
---

# Strings, Unicode and Template Literals

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: you can explain UTF-16 code units vs code points vs graphemes, why `"emoji".length` lies, and what tagged templates do.
- Production signal: your character counts, truncation, and reversal don't corrupt emoji or accented text.
- Dependencies: [[12 - Advanced Language Concepts/06 - Destructuring Spread and Rest|Destructuring Spread and Rest]], [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]

## Source Anchors

- [MDN - String](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String)
- [MDN - String.prototype.normalize](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/normalize)
- [MDN - Template literals](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals)
- [MDN - Intl.Segmenter](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/Segmenter)

## 1. Concept

JavaScript strings are sequences of **UTF-16 code units** (16-bit values). Three levels of "character" that don't coincide:

- **Code unit**: one 16-bit value. `.length`, `[i]`, and `charCodeAt` work in code units.
- **Code point**: one Unicode scalar. Characters above U+FFFF (most emoji, some CJK) need *two* code units (a surrogate pair). Iterated by `for...of`, spread, and `codePointAt`.
- **Grapheme (user-perceived character)**: what a person calls "one character" — may be multiple code points (an emoji with a skin-tone modifier, a flag, a base letter + combining accent). Segmented by `Intl.Segmenter`.

```js
"a".length;        // 1
"😀".length;       // 2  ← one emoji = two UTF-16 code units (a surrogate pair)
"👨‍👩‍👧".length;    // 8  ← one perceived character = multiple code points joined by ZWJ
```

## 2. Why It Matters

- Character counting, truncation ("140 chars"), reversal, and slicing are common, and doing them by code unit corrupts any non-BMP or composed text — a garbled emoji or a broken accent in user content is a visible bug.
- The `.length` "lie" and surrogate pairs are a favorite interview probe for whether you actually understand strings versus assuming ASCII.

## 3. Iterating Correctly

Code-unit operations (`.length`, `str[i]`, `charAt`, `slice` by index) split surrogate pairs. Code-point-aware operations don't:

```js
const s = "a😀b";
s.length;              // 4 (code units)
[...s];                // ["a", "😀", "b"] — spread iterates code POINTS
[...s].length;         // 3
s.split("").reverse().join("");   // "b�?a" — BROKEN: splits the surrogate pair
[...s].reverse().join("");        // "b😀a" — correct at code-point level
```

But even code points aren't enough for *graphemes*: `[...​"👨‍👩‍👧"]` yields the component code points, not one unit. For true user-perceived characters, use `Intl.Segmenter`:

```js
const seg = new Intl.Segmenter("en", { granularity: "grapheme" });
[...seg.segment("👨‍👩‍👧")].length;   // 1 — one grapheme
```

> [!warning] "Count the characters" has three answers
> "How long is this string?" means code units (`.length`), code points (`[...s].length`), or graphemes (`Intl.Segmenter`) depending on intent. A tweet-style limit and a display-truncation want *graphemes* (one emoji = one "character" to the user). Using `.length` for a character limit lets a single emoji count as 2 and can truncate mid-surrogate, rendering a replacement box. Pick the level deliberately.

## 4. Normalization

The same visible text can have different code-point sequences: `é` can be one precomposed code point (U+00E9) or `e` + combining acute (U+0065 U+0301). They *look* identical but are `!==` and have different `.length`. `String.prototype.normalize()` canonicalizes:

```js
const a = "é";          // é precomposed
const b = "é";         // e + combining accent
a === b;                     // false
a.normalize() === b.normalize();   // true (NFC by default)
```

Normalize before comparing, deduping, or storing user text (names, search terms) that may come from different input methods, or "José" typed two ways won't match.

## 5. Template Literals and Tagged Templates

Template literals (backticks) do interpolation and multiline. **Tagged templates** call a function with the string parts and the interpolated values separately — enabling custom processing:

```js
function tag(strings, ...values) {
  // strings: the literal segments; values: the ${} results
  return strings.reduce((out, s, i) => out + s + (values[i] != null ? escape(values[i]) : ""), "");
}
const safe = tag`<p>${userInput}</p>`;   // e.g. auto-escape interpolations
```

This is how libraries like styled-components (`css\`…\``), graphql-tag (`gql\`…\``), and safe-HTML helpers work: they receive structure (static parts) and data (interpolations) distinctly, so they can escape, parse, or transform. The security relevance: a tagged template *can* escape interpolated user data by construction ([[20 - Network and Security/05 - XSS|XSS]]).

## 6. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a "160 character" SMS composer and a username display truncate emoji into broken boxes.

Buggy version:

```js
function truncate(text, max) {
  return text.length > max ? text.slice(0, max) + "…" : text;  // code-unit slice
}
const remaining = 160 - text.length;                            // code-unit count
```

Trace: `text.length` counts code units, so "😀" costs 2 against the limit, and `slice(0, max)` can cut *between* the two surrogate code units of an emoji, leaving a lone surrogate that renders as `�`. Users see wrong counts and corrupted trailing characters.

Production-safe fix — segment by grapheme:

```js
function truncate(text, max) {
  const seg = new Intl.Segmenter(undefined, { granularity: "grapheme" });
  const graphemes = [...seg.segment(text)].map(s => s.segment);
  return graphemes.length > max ? graphemes.slice(0, max).join("") + "…" : text;
}
const remaining = max - [...new Intl.Segmenter().segment(text)].length;   // grapheme count
```

Tradeoffs: `Intl.Segmenter` is correct but heavier than `.length` — for a per-keystroke counter on huge text you might memoize or debounce. For simple ASCII-only fields the cost isn't worth it; use it where user content can contain emoji/composed characters (which, for global apps, is everywhere). Note SMS *encoding* limits (GSM-7 vs UCS-2) are a separate concern — emoji force UCS-2, halving the real SMS segment size — so "160" itself may be wrong for emoji regardless of counting method; surface that to the user.

## 7. Interview Answer

Short answer:

> JS strings are UTF-16 code units. `.length` and index access count code units, so a non-BMP character like most emoji (a surrogate pair) counts as 2 and can be split by slicing. `for...of` and spread iterate code *points*; user-perceived characters (graphemes — emoji with modifiers, flags, combining accents) need `Intl.Segmenter`. So "how long is this string" has three different correct answers.

Deeper answer:

> Normalization matters because the same text can be different code-point sequences (precomposed é vs e + combining accent) that are `!==` — call `normalize()` before comparing/storing user text. Tagged templates receive static parts and interpolations separately, which powers styled-components, gql, and by-construction escaping for XSS-safe HTML. For counting/truncation in a global app, segment by grapheme; code-unit operations corrupt emoji and composed characters, and encoding-level limits (SMS UCS-2) are yet another layer.

## 8. Practice

1. <details><summary>`"😀".length` is 2. Explain, and give the code that counts it as 1.</summary>😀 (U+1F600) is above U+FFFF, so UTF-16 encodes it as a surrogate *pair* — two 16-bit code units — and `.length` counts code units. Code-point count: `[...​"😀"].length` → 1 (spread iterates code points). For user-perceived characters generally (including ZWJ sequences), `[...new Intl.Segmenter().segment("😀")].length` → 1.</details>

2. <details><summary>`"café".split("").reverse().join("")` produces garbage for some inputs. Why, and the fix?</summary>`split("")` splits by code unit, so surrogate pairs (emoji) and — depending on composition — combining marks get separated and reversed into invalid sequences (lone surrogates → �, accents on the wrong base). Fix: iterate code points with spread (`[...str].reverse().join("")`) for surrogate safety, or segment by grapheme with `Intl.Segmenter` to also keep combining marks and ZWJ sequences intact.</details>

3. <details><summary>Two users both typed "José" but a search for one doesn't match the other. Likely cause and fix?</summary>The "é" was entered differently — one precomposed (U+00E9), one as "e" + combining acute (U+0065 U+0301). They render identically but are distinct code-point sequences, so `===` and index-based search fail. Fix: `normalize()` both the stored value and the query (NFC) before comparing/indexing, so equivalent forms canonicalize to the same sequence.</details>

4. <details><summary>What do tagged templates give you that plain interpolation doesn't, with a security example?</summary>The tag function receives the static string segments and the interpolated values as *separate* arguments, so it can process them distinctly — parse, transform, or escape only the interpolations. Security example: a `safeHtml\`<p>${userInput}</p>\`` tag can HTML-escape every `${}` value while leaving the trusted static markup alone, producing XSS-safe output by construction — the same separation-of-structure-from-data idea behind React's JSX escaping and libraries like graphql-tag and styled-components.</details>

## Related Notes

- [[12 - Advanced Language Concepts/08 - Iterators and Generators|Iterators and Generators]]
- [[12 - Advanced Language Concepts/16 - Intl|Intl]]
- [[20 - Network and Security/05 - XSS|XSS]]
- [[01 - Roadmap|Roadmap]]
