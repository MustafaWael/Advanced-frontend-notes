---
tags: [system-design, interview, data-table, virtualization, performance]
module: "29 - Frontend System Design"
priority: must-know
status: not-started
aliases: [data grid design, table sorting filtering, virtualized table]
---

# Designing a Data Table

## Maturity Target

- Priority: #must-know
- Study time: 60 minutes
- Interview signal: Run RADIO on a large data table covering server vs client sort/filter, pagination vs virtualization, column model, and the grid-vs-native-table a11y decision.
- Production signal: You can build a performant table that scales to large datasets without freezing or breaking keyboard/screen-reader use.
- Dependencies: [[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]], [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]]

## Source Anchors

- [WAI-ARIA APG — Grid Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/grid/)
- [web.dev — Virtualize large lists](https://web.dev/articles/virtualize-long-lists-react-window)
- [TanStack Table](https://tanstack.com/table/latest)

## 1. Requirements

Ask: dataset size (hundreds vs millions)? sorting/filtering/grouping? server-side or client-side data ops? editable cells? row selection? column resize/reorder/pin? pagination or infinite/virtualized scroll? export? responsive/mobile? realtime updates?

Design against: **a large dataset (100k+ rows) with sort, multi-filter, column controls, row selection, and virtualized scrolling; data ops on the server.** Out of scope: pivot/grouping analytics, spreadsheet editing.

The requirement that decides the architecture: **dataset size + where data ops run.** 100k+ rows means the client can't hold or sort everything → server-side sort/filter/pagination and virtualized rendering.

## 2. Architecture

```
<DataTable>
 ┌───────────────┐   ┌─────────────────────────────┐
 │ Column model   │   │ Table controller             │
 │ (defs, widths, │──▶│ sort/filter/selection state  │
 │  pin, sort dir)│   │ → query params               │
 └───────────────┘   └───────────────┬─────────────┘
 ┌───────────────┐                   ▼
 │ Virtual rows   │◀── data ── Query layer (server sort/filter/page, cache)
 │ (windowed)     │            GET /rows?sort=&filter=&cursor=
 └───────────────┘
```

Same controller/query split as the other walkthroughs. The **column model** (declarative column defs: accessor, header, width, sortable, render) is the table's real API. The **controller** holds sort/filter/selection as state and translates it to **query params**; the **query layer** fetches server-sorted/filtered/paginated data and caches it; **virtual rows** render only the visible window.

> [!warning] The killer decision is server vs client data ops. Client-side sort/filter is trivial to build and fine for a few thousand rows, but sorting 100k+ rows on the main thread freezes the tab (an INP disaster — [[29 - Frontend System Design/08 - Frontend Performance for System Design|performance]]). Past a threshold, sort/filter/paginate on the server; the client only renders a window. Naming that threshold — and why it's there — is the actual answer.

## 3. Data Model

```ts
interface ColumnDef<Row> {
  id: string;
  header: ReactNode;
  accessor: (row: Row) => unknown;
  sortable?: boolean;
  width?: number; pinned?: 'left' | 'right';
  render?: (value: unknown, row: Row) => ReactNode;
}
interface TableState {
  sort: { colId: string; dir: 'asc' | 'desc' }[];
  filters: Record<string, FilterValue>;
  selection: Set<RowId>;                 // ids, not row objects
  // rows come from the query layer, keyed/paginated by (sort+filter) as cache key
}
```

Selection is a `Set<RowId>` (ids, not objects) so it survives re-fetches and virtualization — the selected row may not even be in the DOM. The query cache is keyed by the **sort+filter combination**, so switching filters doesn't clobber another view's data ([[29 - Frontend System Design/06 - Data Fetching at Scale|keys include params]]).

## 4. Interface

```tsx
<DataTable
  columns={columns}                    // the column model = the API
  fetchRows={(params, signal) => api.rows(params, signal)}  // server ops, IoC
  getRowId={(row) => row.id}           // identity for keys + selection
  sortMode="server" filterMode="server"
  onSelectionChange={setSelected}
  estimateRowHeight={() => 44}
/>
```

Inversion of control on `fetchRows` (the table sends sort/filter/page params, the consumer executes the query) keeps it transport-agnostic. `getRowId` is explicit — keys, selection, and virtualization all need stable identity. A headless core (column model + state + a11y) with a styled wrapper is the design-system-friendly shape ([[29 - Frontend System Design/07 - Component API Design|Component API Design]]).

## 5. Optimizations (ranked)

1. **Rendering at scale** — **virtualization** (windowed rows; column virtualization too if many columns). Sticky header/pinned columns must work with the virtual window. Alternative for smaller sets: plain pagination — simpler, and jump-to-page is a feature virtualization loses.
2. **Data-ops location** — server-side sort/filter/paginate past the threshold; debounce filter input; cache by sort+filter key; cursor or offset pagination per whether jump-to-page is needed ([[29 - Frontend System Design/09 - Network and API Design for Frontend|API design]]).
3. **Interaction responsiveness (INP)** — heavy client-side transforms (if any) off the main thread or deferred; don't re-render all rows on a single-cell change (normalized row state, memoized cells).
4. **Accessibility — first decide grid vs native table, then apply the pattern.** This is the choice interviewers probe: a plain **`<table>`** (with `<th scope>`, `aria-sort`, `caption`) is correct for a *read-mostly* table and lets screen readers use their native table-reading mode — reach for it by default. The APG **grid** pattern (`role="grid"`/`row`/`gridcell`, arrow-key cell navigation) is for *interactive* composite widgets — editable cells, cell-level keyboard navigation, complex in-cell selection — and it *replaces* native table semantics, hijacking arrow keys and turning off the screen reader's table mode, so using it on a static table actively degrades a11y. Our design (row selection, sortable, but cells aren't individually navigable/editable) is borderline; if cell navigation isn't a requirement, prefer native `<table>` semantics with `aria-sort` and skip `role="grid"`. Whichever you pick, virtualization needs `aria-rowcount` (the *real* total) and `aria-rowindex` on each rendered row, so screen readers report true position, not the windowed DOM count — the virtualization+a11y gotcha.
5. **Layout stability** — fixed/measured row heights to avoid CLS; reserve column widths; skeleton rows while loading.

## 6. Interview Answer

Short answer:

> A data table is a column model plus a controller that turns sort/filter/selection into query params, over a query layer that (past a size threshold) does sort/filter/pagination on the server, with virtualized row rendering. Selection is a set of ids so it survives refetch and virtualization. The a11y contract is the APG grid pattern with `aria-rowcount`/`aria-rowindex` so screen readers report the true total despite windowing. The pivotal decision is server vs client data ops — client-side sort of 100k rows freezes the tab.

Deeper answer:

> The decisions I'd defend: server-side data ops past a few thousand rows, because sorting/filtering large sets on the main thread is an INP disaster and the client can't hold everything anyway — the client becomes a windowed renderer over a server-paginated, cache-keyed dataset. Virtualization for the DOM, but I'd name its costs: sticky headers and pinned columns need special handling, jump-to-page is lost (cursor vs offset becomes a real choice), and screen readers see only the windowed rows unless I supply `aria-rowcount`/`aria-rowindex`. And selection as ids, not row objects, so it's stable across refetches and rows that aren't currently rendered. For a small table I'd cut all of this and do client-side ops with plain pagination — and say so.

## 7. Practice

1. <details><summary>At what point do you move sort/filter to the server, and why?</summary>When the dataset exceeds what the client can hold and sort responsively — roughly a few thousand rows and up. Client-side sort of 100k+ rows blocks the main thread (INP) and needs all data in memory. Past the threshold, the server sorts/filters/paginates and the client renders only a window. Name the threshold and the reason behind it.</details>
2. <details><summary>Why store row selection as a Set of ids rather than row objects?</summary>With virtualization and refetching, a selected row may not be in the DOM or may be a new object after refetch. Ids are stable identity, so selection survives windowing, sorting, and data refreshes; storing objects would lose selection on refetch and bloat memory.</details>
3. <details><summary>What's the virtualization + accessibility gotcha, and the fix?</summary>Virtualization renders only visible rows, so the DOM row count is wrong — a screen reader would announce "row 5 of 20" when there are 100k. Fix with `aria-rowcount` (true total) and `aria-rowindex` on each rendered row (its real position), plus the APG grid keyboard model, so assistive tech reports accurate position despite windowing.</details>

## Related Notes

- [[29 - Frontend System Design/08 - Frontend Performance for System Design|Frontend Performance for System Design]]
- [[29 - Frontend System Design/06 - Data Fetching at Scale|Data Fetching at Scale]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[25 - Accessibility and Inclusive UX/07 - Images Media Tables and Complex Content|Images, Media, Tables and Complex Content]]
