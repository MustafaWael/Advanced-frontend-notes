---
tags: [system-design, interview, autocomplete, async]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [typeahead design, search suggestions design]
---

# Designing an Autocomplete

## Maturity Target

- Priority: #must-know
- Study time: 75 minutes
- Interview signal: You can run the full RADIO pass on "design an autocomplete" in 35 minutes, unprompted, covering races, caching, a11y, and the component contract with tradeoffs.
- Production signal: You can build or review a reusable typeahead and know exactly which corners were cut.
- Dependencies: [[29 - Frontend System Design/01 - The Frontend System Design Framework|RADIO]], [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]], [[17 - Practical Frontend Scenarios/10 - Request Cancellation|Request Cancellation]]

## Source Anchors

- [WAI-ARIA APG — Combobox Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)
- [GreatFrontEnd — Autocomplete case study](https://www.greatfrontend.com/questions/system-design/autocomplete)
- [MDN — AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)

## 1. Requirements (the questions, then the answers you design against)

Ask: server-backed or local data? reusable library component or one app feature? result count and shape (plain strings, or rich rows with avatars)? latency/scale targets? keyboard + screen reader support required (yes — always yes)? mobile?

Design against a deliberately hard version: **server-backed, reusable across teams, rich results, p95 suggestion latency under 300ms perceived, fully accessible.** Out of scope: fuzzy ranking algorithm (server concern), multi-token highlighting.

Non-functional requirements worth saying out loud: resilience (network failure must not break the input — typing always works), payload discipline on mobile, and no layout shift when results open.

## 2. Architecture

```
┌────────────────────────────────────────────┐
│  <Autocomplete>                            │
│  ┌──────────┐   ┌──────────────────────┐   │
│  │  Input   │──▶│  Controller          │   │
│  └──────────┘   │  (state machine:     │   │
│  ┌──────────┐   │  idle→debouncing→    │   │
│  │  Listbox │◀──│  loading→open/error) │   │
│  └──────────┘   └─────────┬────────────┘   │
└───────────────────────────┼────────────────┘
                    ┌───────▼────────┐
                    │  Query layer   │  debounce · dedup · abort
                    │  + LRU cache   │  key = normalized query
                    └───────┬────────┘
                            ▼  network
```

The load-bearing boundary is **controller vs query layer**. The controller owns UI state (open/closed, highlighted index, input value); the query layer owns server state (in-flight requests, cache). Mixing them is the root cause of most typeahead bugs — it's [[28 - Frameworks and Application Architecture/06 - Server State|server state vs UI state]] in miniature. Modeling the controller as an explicit state machine (idle → debouncing → loading → open | empty | error) kills impossible-state bugs like "spinner and stale results visible together".

## 3. Data Model

```ts
// Server state — owned by the query layer
type QueryCache = Map<string, {           // key: normalized query (trim, lowercase)
  results: SuggestionId[];                // ids, not objects
  fetchedAt: number;                      // for TTL eviction
}>;
type SuggestionStore = Map<SuggestionId, Suggestion>;  // normalized entities

// UI state — owned by the controller
interface ControllerState {
  inputValue: string;
  status: 'idle' | 'debouncing' | 'loading' | 'open' | 'empty' | 'error';
  highlightedIndex: number | null;
  lastRequestId: number;                  // supersede guard for races
}
```

Why normalize (ids + entity store) instead of caching result arrays directly: overlapping queries ("car", "cart") share entities — dedup memory, and an entity updated once is consistent everywhere. Tradeoff: indirection cost; for plain-string suggestions this is over-engineering, and saying *that* is part of the answer. Cache policy: LRU capped (~50 queries) + TTL, because suggestion freshness matters less than memory on long sessions ([[13 - Performance and Memory/03 - Memory Leaks|unbounded caches are leaks]]).

## 4. Interface

**Component API** — the contract other teams consume:

```ts
interface AutocompleteProps<T> {
  // Controlled or uncontrolled — support both, like native inputs
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  onSelect: (item: T) => void;

  // Data in: the component does NOT fetch — consumers inject the source
  getSuggestions: (query: string, signal: AbortSignal) => Promise<T[]>;

  // Composition over configuration for rich rows
  renderItem?: (item: T, state: { highlighted: boolean }) => ReactNode;

  debounceMs?: number;   // default 300
  minChars?: number;     // default 1
}
```

The decision that carries this design: **inversion of control on fetching**. Passing `getSuggestions` (with the `AbortSignal` threaded through) keeps the component transport-agnostic — REST, GraphQL, local filter, mock in tests — while the component still owns debounce/dedup/abort orchestration. Tradeoff: consumers can pass a non-cancellable function; document that `signal` must be honored.

**Network API**: `GET /suggest?q=<query>&limit=10`. GET (not POST) so [[20 - Network and Security/02 - HTTP Caching|HTTP caching]] and CDN caching work — popular prefixes are extremely cacheable. Response includes the echoed query so the client can drop mismatched responses even without abort support. Keep payloads lean: ids + display fields only.

## 5. Optimizations (ranked for this requirement set)

1. **Race safety** — the defining correctness issue. Abort superseded requests (`AbortController`) *and* guard with `lastRequestId` compare-on-resolve, because abort alone doesn't cover cached/near-simultaneous resolutions. Traced fully in [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]].
2. **Request discipline** — debounce (~300ms) + minChars + cache-before-network + in-flight dedup. Worst case drops from request-per-keystroke to ~2 per word.
3. **Accessibility** — APG combobox contract: `role="combobox"`, `aria-expanded`, `aria-activedescendant` for virtual focus (DOM focus stays in the input), `aria-live` result-count announcements. Built hands-on in [[90 - Labs/03 - Accessible Async Search Lab|Lab 03]].
4. **Rendering** — stable keys ([[21 - React Internals and Patterns/02 - Reconciliation and Keys|reconciliation]]); virtualization only if results exceed ~50 (usually capped at 10 — say so instead of reflex-virtualizing).
5. **Resilience** — error state keeps input usable, retry on transient failure, empty-state copy. Escape rendered query text — echoed input is an [[20 - Network and Security/05 - XSS|XSS]] door.

> [!warning] The classic planted trap: an interviewer asks "you debounced — do you still need cancellation?" Yes. Debounce reduces request *count*; it does nothing about *ordering* of the requests that do fire. A slow "car" response can still land after a fast "cardio" one.

## 6. Interview Answer

Short answer:

> "Autocomplete is a controller state machine over a query layer. The controller owns UI state — open, highlighted index; the query layer owns server state — debounce, in-flight dedup, abort, LRU cache keyed by normalized query. The component API inverts control on fetching via a `getSuggestions(query, signal)` prop, so it's transport-agnostic and testable. Top risks: response races — abort plus request-id guard — and the APG combobox a11y contract."

Deeper answer:

> "The two decisions I'd defend hardest: separating server state from UI state, because merging them is where stale-result and impossible-state bugs come from; and designing the network API as a cacheable GET with the query echoed back, which makes the CDN do most of the scaling work for popular prefixes and gives a race guard even without client abort. What I'd cut under time pressure, explicitly: entity normalization for plain-string results, and virtualization for a 10-item list — both are real costs with no payoff at that scale."

## 7. Practice

1. <details><summary>Both abort and a request-id guard — why isn't abort alone enough?</summary>Abort only cancels requests still in flight over the network. A response served synchronously from cache, or one that resolved just before abort was called, still reaches your handler. The compare-on-resolve guard (`if (id !== lastRequestId) return`) is the invariant; abort is the bandwidth optimization on top.</details>
2. <details><summary>Consumer complains: suggestions flash old results when reopening with the same query. Diagnose from the design.</summary>Cache-before-network showing stale cache while revalidating — that's stale-while-revalidate behavior. Either it's desired (render cached, swap in fresh — say so in docs) or the TTL is too long. The bug report is really a missing product decision about staleness tolerance; the data model (fetchedAt) already supports either policy.</details>
3. <details><summary>Transfer: which parts of this design survive unchanged for "design a mention picker (@user) in a comment box"?</summary>Query layer (debounce/abort/cache/normalization), race guards, APG combobox semantics, and the inversion-of-control API survive. What changes: trigger detection (parsing `@` mid-text with cursor position), anchored positioning of the listbox to the caret, and insertion semantics replacing `onSelect` navigation.</details>

## Related Notes

- [[29 - Frontend System Design/01 - The Frontend System Design Framework|The Frontend System Design Framework]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[90 - Labs/03 - Accessible Async Search Lab|Accessible Async Search Lab]]
- [[28 - Frameworks and Application Architecture/06 - Server State|Server State]]
