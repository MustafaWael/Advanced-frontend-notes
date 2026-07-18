# 02 - Autocomplete

> **Source:** [GreatFrontEnd — Autocomplete System Design](https://www.greatfrontend.com/questions/system-design/autocomplete)
> **Summary:** Design a generic, customizable autocomplete UI component (input + results popup) — the design hinges on a central controller, a query-keyed cache that doubles as the race-condition guard, debounced network requests, and the WAI-ARIA combobox pattern.

- **Difficulty:** Medium | **Duration:** ~30 mins
- Highly recommended question — the concepts (debounce, caching, race conditions, a11y) generalize to many other front-end system design questions.

---

## 1. Requirements (R)

### The question
Design an autocomplete UI component: user types a search term into a text box, a list of search results appears in a popup, and the user can select a result. A back-end API is provided that returns results for a query.

Real-life examples: Google search bar (text suggestions), Facebook search (rich results: friends, celebrities, groups, pages).

### Functional requirements
- Generic enough to be usable by **different websites** (a reusable component, not a product).
- Input field UI and search results UI should be **customizable**.

### Requirements exploration (questions to ask the interviewer)
- **What kind of results should be supported?** Text, image, and media (image + text) are most common — but we can't anticipate every result type consumers will want to render (motivates render customization APIs).
- **What devices?** All: laptops, tablets, mobile, etc.
- **Fuzzy search?** Not in the initial version; explore if time permits.

### Non-functional requirements (implied throughout)
- Performance: fast-feeling results (caching, debounce, virtualization).
- Resilience: flaky networks, out-of-order responses, retries, offline.
- Accessibility: keyboard-only and screen reader usable (ARIA combobox).
- Memory-conscious on long-lived pages (cache eviction).

---

## 2. Architecture (A)

Four parts, with the controller at the center (MVC-style):

| Component | Responsibility |
|---|---|
| **Input field UI** | Handles user input; passes it to the controller. |
| **Results UI (popup)** | Receives results from the controller and presents them; handles user selection and informs the controller which item was selected. |
| **Cache** | Stores results for previous queries so the controller can check it before hitting the server. |
| **Controller** | The "brain" — all components interact with it. Passes user input and results between components; fetches from the server when the cache misses. |

Flow per keystroke: input → controller → consult cache → on miss, fetch from server → write response back into cache → push results into popup.

---

## 3. Data model (D)

- **Controller**
  - Props/options exposed via the component API
  - Current search string
  - Transient UI state: active suggestion index (`activeIndex`), open/closed flag (`isOpen`)
- **Cache**
  - Initial results (for empty query / on focus)
  - Cached results, keyed by query string, referencing result entities (see cache structure options below)

Only core fields for basic functionality — more fields get added by the deep dives (e.g. timestamps for TTL eviction).

---

## 4. Interface definition / API (I)

Focus on the **component API**; only briefly touch the server search API.

### Client — Basic API
- **Number of results** to show in the list.
- **API URL** to hit as the user types.
- **Event listeners / hooks**: `'input'`, `'focus'`, `'blur'`, `'change'`, `'select'` — useful for consumers (e.g. logging interactions).
- **Customized rendering** — three approaches, in increasing flexibility:
  1. **Theming options object** — e.g. `{ textSize: '12px', textColor: 'red' }`. Easiest to use, least flexible.
  2. **Classnames** — consumers supply CSS class names added to the UI sub-components.
  3. **Render function/callback** — inversion of control (common in React): the component invokes a developer-provided function with data, developer fully controls rendering. Most flexible, most effort.

### Client — Advanced API (UX/performance)
- **Minimum query length** — very short queries return too many irrelevant results; only trigger search at e.g. 3+ characters.
- **Debounce duration** — firing the API on every keystroke is wasteful; with a 300ms debounce, the API is only called after 300ms of no input.
- **API timeout duration** — how long to wait before treating the search as timed out and showing an error.
- **Cache-related options**: initial results; results source (network only / network + cache / cache only); function to merge server + cache results; cache duration (TTL).

### Server API
HTTP API with parameters:
- `query` — the search query
- `limit` — number of results per page
- `pagination` — page number

`pagination` + `limit` support scrolling beyond the initial results for the next "page".

---

## 5. Optimizations & deep dives (O)

### 5.1 Network

Autocomplete fires a request on nearly every keystroke — the network layer must tolerate out-of-order responses, transient failures, and dropped connectivity.

#### Concurrent requests / race conditions
- Never trust **response arrival order** — an earlier request can complete after a later one, flashing stale results for a query the user already moved past.
- Two options to pick the right response:
  1. **Timestamp each request**; only display results of the latest *request* (not latest response); discard irrelevant responses.
  2. **Save results in a map keyed by the query string**; only present results matching the current input value.
- **Option 2 is clearly better** since we already have a query-keyed cache — the cache doubles as the race-condition guard.
- **Don't abort requests** (`AbortController`) or discard responses: the server already did the work; storing the response under its query string populates the cache "for free".
- Caching historical keystrokes helps fat-finger recovery: `"foot"` → `"footr"` → delete `"r"` → `"foot"` served instantly from cache. (With debounce, intermediate queries may never fire, so this mainly benefits no-debounce setups or slow typists.)

#### Failed requests & retries
- Auto-retry failed queries (flaky connections).
- Use **exponential backoff** if the server might be down, to avoid overloading it.

#### Offline usage
- Read purely from the cache (limited value if cache is empty).
- Don't fire requests at all — don't waste CPU cycles.
- Indicate in the component that there's no network connection.

### 5.2 Cache

Purpose: save results of previous queries in memory so repeat searches show instantly — no network request, no latency. Google and Facebook both cache queries.

#### Cache structure — three options (know the tradeoffs!)

**Option 1: Hash map — query string → results.** O(1) lookup, simplest.

```js
const cache = {
  fa: [
    { type: 'organization', text: 'Facebook' },
    { type: 'organization', text: 'FasTrak', subtitle: 'Government office, San Francisco, CA' },
    { type: 'text', text: 'face' },
  ],
  fac: [
    { type: 'organization', text: 'Facebook' },
    { type: 'text', text: 'face' },
    { type: 'text', text: 'facebook messenger' },
  ],
  face: [ /* ... */ ],
  faces: [ /* ... */ ],
};
```
- Con: lots of **duplicate results** across keys (especially without debounce) → high memory usage.

**Option 2: Flat list of results**, filter on the client.

```js
const results = [
  { type: 'company', text: 'Facebook' },
  { type: 'organization', text: 'FasTrak', subtitle: 'Government office, San Francisco, CA' },
  { type: 'text', text: 'face' },
  { type: 'text', text: 'facebook messenger' },
  // ...
];
```
- Pro: little/no duplication.
- Cons: client-side filtering is bad for performance, can **block the UI thread** on large datasets/slow devices; server **ranking order may be lost**.

**Option 3: Normalized map** (inspired by normalizr) — like a database: results stored by unique ID; cache maps query → list of IDs. Combines fast lookup + no duplication.

```js
const results = {
  1: { id: 1, type: 'organization', text: 'Facebook' },
  2: { id: 2, type: 'organization', text: 'FasTrak', subtitle: 'Government office, San Francisco, CA' },
  3: { id: 3, type: 'text', text: 'face' },
  4: { id: 4, type: 'text', text: 'facebook messenger' },
  5: { id: 5, type: 'text', text: 'facebook stock' },
  6: { id: 6, type: 'television', text: 'Faces of COVID', subtitle: 'TV program' },
  7: { id: 7, type: 'musician', text: 'Faces', subtitle: 'Rock band' },
  8: { id: 8, type: 'television', text: 'Faces of Death', subtitle: 'Film series' },
};

const cache = {
  fa: [1, 2, 3],
  fac: [1, 3, 4],
  face: [1, 3, 5],
  faces: [6, 7, 8],
};
```
- Small pre-processing cost to map IDs → items before rendering (negligible for few items).

**Which to use?**
- **Short-lived pages** (e.g. Google search page — resets on navigation): Option 1. Duplication doesn't matter; cache clears when the user clicks a result.
- **Long-lived SPAs** (e.g. Facebook): Option 3 — repeated queries would otherwise duplicate entities and pressure memory. But don't cache for too long: stale results waste memory.

#### Initial results
- Show results on **focus, before any typing** (like Google) — saves typing and server cost.
- Google: trending/popular queries + historical searches; Facebook: historical searches; stock/crypto exchanges: historical searches or trending tickers.
- Implement as a component option, cached under the **empty string key**.
- Historical note: Facebook preloaded a user's friends/pages/groups into the browser cache for instant client-side filtering ([The Life of a Typeahead Query](https://engineering.fb.com/2010/05/17/web/the-life-of-a-typeahead-query/)).

#### Caching strategy (eviction / TTL)
Caching is a **space/time tradeoff**. Eviction depends on how fresh results must be:
- **Google**: results change rarely → cache can live long (hours).
- **Facebook**: moderately fresh → evict every ~half hour.
- **Stock/currency exchanges**: prices change every minute → maybe don't cache at all.

Expose as configuration:
- **Data source**: `network-only` / `network-and-cache` / `cache-only`.
- **Cache duration / TTL**: timestamp each entry; evict stale entries periodically.

### 5.3 Performance

- **Loading speed**: client-side caching shows previous queries' results near-instantly; can even reuse cached results for future matching queries.
- **Debounce vs throttle**:
  - **Debounce** is right for typing — fires after the user pauses, so fast typists produce one call instead of one per keystroke. Default ~**300ms**; expose as a prop.
  - **Throttle** fits continuous signals (scroll, resize) where you want a bounded stream of updates.
  - Pipeline per keystroke: debounce → cache lookup → network fetch → query-string guard → render only if response matches current input.
- **Memory usage**: long-lived pages accumulate cache entries. Purge when the browser is **idle** or when entry count/memory exceeds a **threshold**.
- **Virtualized lists** ("windowing"): with hundreds/thousands of results, rendering all DOM nodes hogs memory and slows the browser. Only render what's visible; recycle DOM nodes; use fake off-screen spacer elements to fake the full scroll height.

### 5.4 User experience

- **Autofocus**: add `autofocus` on search-centric pages (like Google) where usage intent is high.
- **Handle states**:
  - *Loading*: spinner during background request.
  - *Error*: error message + retry button.
  - *No network*: message that network is unavailable.
- **Long strings**: truncate with ellipsis or wrap nicely; never overflow outside the component.
- **Mobile-friendliness**:
  - Result items large enough to tap.
  - Dynamic result count per viewport size (better done in userland).
  - Set `autocapitalize="off"`, `autocomplete="off"`, `autocorrect="off"`, `spellcheck="false"` so browser suggestions don't interfere.
- **Keyboard interaction**: fully keyboard-operable (see Accessibility); add a global shortcut to focus the input — commonly `/` (Facebook, X, YouTube).
- **Typos / fuzzy search**: match closely rather than exactly. Client-side: edit distance (e.g. **Levenshtein distance**), pick smallest. Server-side: send query as-is, fuzzy-match on the server.
- **Query results positioning**: popup normally renders below the input; if the input is near the bottom of the viewport, detect available space and **flip to render above**.

### 5.5 Accessibility

A plain `<input>` has no combobox semantics — follow the **WAI-ARIA combobox pattern**, don't invent roles (screen readers already know how to announce it when roles/states match the spec).

#### Screen readers
- Semantic HTML (`<ul>`/`<li>`) or `role="listbox"` + `role="option"` for the results.
- `aria-label` on the `<input>` (usually no visible label).
- `role="combobox"` on the `<input>`.
- `aria-haspopup` — element triggers an interactive popup.
- `aria-expanded` — whether the popup is currently displayed.
- `aria-live` on the results region — announce new results to screen reader users.
- `aria-autocomplete` — the interaction model: `"inline"` (single value inline) vs `"list"` (collection of values). Google uses `"both"`; Facebook and X use `"list"`.
- `aria-activedescendant` — mirrors the currently highlighted option while DOM focus stays on the input.

#### Keyboard interaction
- **Enter** to search — free by wrapping the `<input>` in a `<form>`.
- **Up/Down arrows** navigate options, **wrapping around** at the ends.
- **Escape** dismisses the results popup.
- Follow the full [WAI-ARIA Combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/).
- Think of it as a lifecycle: popup opens on focus/typing → loading → results → closes on selection, blur, or Escape, with `aria-expanded`/`aria-activedescendant` mirroring state.

---

## 6. Summary — the three key decisions

1. **Centralize traffic through a controller.** Input UI, results popup, cache, and server all talk to one controller owning current input, `activeIndex`, `isOpen`. Every keystroke: consult cache → fall back to server on miss → write response back — so races and stale state resolve in one place.
2. **Normalize the cache (query → `resultIds` → shared result store).** O(1) lookup, no duplication on long-lived pages, and the same structure is the **race-condition guard**: responses are filed under their issuing query string, so a late old response populates the cache without ever rendering.
3. **Lean on platform primitives.** ~300ms debounce collapses keystrokes; repeat/backspace queries served from cache; WAI-ARIA combobox (`role="combobox"`, `aria-expanded`, `aria-activedescendant`) instead of bespoke roles.

> Start by keying responses to their query string and treating the cache as the view's source of truth — other tradeoffs build on that choice.

---

## 7. Real-world comparison: Google vs Facebook vs X

| HTML Attribute | Google | Facebook | X |
| --- | --- | --- | --- |
| HTML Element | `<textarea>` | `<input>` | `<input>` |
| Within `<form>` | Yes | No | Yes |
| `type` | `"text"` | `"search"` | `"text"` |
| `autocapitalize` | `"off"` | Absent | `"sentence"` |
| `autocomplete` | `"off"` | `"off"` | `"off"` |
| `autocorrect` | `"off"` | Absent | `"off"` |
| `autofocus` | Present | Absent | Present |
| `placeholder` | Absent | `"Search Facebook"` | `"Search"` |
| `role` | `"combobox"` | Absent | `"combobox"` |
| `spellcheck` | `"false"` | `"false"` | `"false"` |
| `aria-activedescendant` | Present | Absent | Present |
| `aria-autocomplete` | `"both"` | `"list"` | `"list"` |
| `aria-expanded` | Present | Present | Present |
| `aria-haspopup` | `"false"` | Absent | Absent |
| `aria-invalid` | Absent | `"false"` | Absent |
| `aria-label` | `"Search"` | `"Search Facebook"` | `"Search query"` |
| `aria-owns` | Present | Absent | Present |
| `dir` | Absent | `"ltr"`/`"rtl"` | `"auto"` |
| `enterkeyhint` | Absent | Absent | `"search"` |

Takeaway: **no standardized practice** on which ARIA properties to use — even the biggest companies differ.

---

## 8. References

- [The Life of a Typeahead Query — Facebook Engineering](https://engineering.fb.com/2010/05/17/web/the-life-of-a-typeahead-query/)
- [Query Autocomplete from LLMs — Reddit Engineering](https://www.reddit.com/r/RedditEng/comments/1loewqg/query_autocomplete_from_llms/)
- [Building an accessible autocomplete control — Adam Silver](https://adamsilver.io/blog/building-an-accessible-autocomplete-control/)
- [Combobox pattern — W3C ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)
- [React Select](https://react-select.com/) — popular combobox library
- [AbortController — MDN](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [Trie — Wikipedia](https://en.wikipedia.org/wiki/Trie) — prefix tree for client-side suggestion lookup
- Related: [Dropdown Menu](https://www.greatfrontend.com/questions/system-design/dropdown-menu), [E-commerce (Amazon)](https://www.greatfrontend.com/questions/system-design/e-commerce-amazon)
