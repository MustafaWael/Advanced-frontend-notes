---
tags: [javascript, arrays, frontend-data-transformation-examples]
module: "07 - Arrays and Iteration"
priority: must-know
status: not-started
---

# Frontend Data Transformation Examples

## Maturity Target

- Priority: #must-know
- Study time: 120-160 minutes
- Interview signal: you can turn raw API data into UI data while explaining complexity, identity, and failure modes.
- Production signal: your list screens stay correct, readable, and responsive with real data sizes.
- Dependencies: [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]], [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]], [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]

## Source Anchors

- [MDN Array](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array)
- [MDN Object.fromEntries](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/fromEntries)
- [React useMemo](https://react.dev/reference/react/useMemo)
- [React: Updating Arrays in State](https://react.dev/learn/updating-arrays-in-state)
- [web.dev: Virtualize large lists with react-window](https://web.dev/articles/virtualize-long-lists-react-window)

## 1. Concept

Frontend data transformation is the boundary between raw data and UI-ready data.

Raw API data is usually optimized for transport, storage, backend relationships, or database shape. UI data is optimized for rendering, labels, fallbacks, ordering, grouping, permission checks, and interactions.

Strong frontend code makes this boundary deliberate:

```txt
API response -> validated/normalized data -> derived view model -> rendered UI
```

## 2. Why It Matters

The weak version of frontend data work is "just map it in the component." That is fine for tiny screens. Real mid-level work asks:

- Is this transformation pure?
- Is it mutating server/cache/state data?
- Does it run on every keystroke or every render?
- Does the UI need lookup by ID or only display order?
- Are missing values explicit?
- Are keys stable?
- Is sorting done on the client, server, or both?
- Is memoization helping or hiding unstable inputs?

## 3. Official Mechanism

Most transformations are combinations of:

- `map` to change shape
- `filter` to remove items
- `reduce` to group or summarize
- `Object.fromEntries` to build lookup objects
- `Map` and `Set` for collection semantics
- `toSorted` or copied `sort` for stable non-mutating ordering
- `Array.from` to convert iterable or array-like input into arrays

React adds an important constraint: render calculations must be pure. If you derive data during render, do not mutate props, state, or cached results.

## 4. Mental Model

Separate four shapes:

| Shape | Example | Best for |
| --- | --- | --- |
| API shape | `{ user_id, profile: {...} }` | network/backend contract |
| entity shape | `{ id, name, avatarUrl }` | application data model |
| lookup shape | `{ [id]: entity }` or `Map` | fast access by ID |
| view model | `{ key, title, subtitle, disabled }` | rendering a specific screen |

Do not force one shape to serve every layer.

## 5. Scenario: Flatten API Data For UI

### Problem

The API returns nested user records:

```ts
type ApiUser = {
  id: string;
  username: string;
  profile: {
    firstName: string;
    lastName: string;
    avatarUrl?: string;
  };
  meta: {
    createdAt: string;
    active: boolean;
  };
};
```

The component wants a simple row:

```ts
type UserRow = {
  id: string;
  label: string;
  avatarUrl: string;
  active: boolean;
  joinedAt: Date;
};
```

### Fix

```ts
function toUserRow(user: ApiUser): UserRow {
  return {
    id: user.id,
    label: `${user.profile.firstName} ${user.profile.lastName}`,
    avatarUrl: user.profile.avatarUrl ?? "/avatar-placeholder.png",
    active: user.meta.active,
    joinedAt: new Date(user.meta.createdAt),
  };
}

const rows = apiUsers.map(toUserRow);
```

### Why It Works

- The mapping is pure and testable.
- Fallbacks are handled before rendering.
- The component no longer knows about the backend's nested shape.
- `id` remains stable for React keys and user interactions.

### Tradeoff

Creating `Date` objects during every render can be wasteful for large lists. Prefer transforming at the data boundary or memoizing on stable API data when the cost is real.

## 6. Scenario: Build Lookup Maps

### Problem

You render orders and need the customer name for each order.

```ts
type Customer = { id: string; name: string };
type Order = { id: string; customerId: string; total: number };
```

Weak version:

```ts
const rows = orders.map(order => {
  const customer = customers.find(customer => customer.id === order.customerId);

  return {
    id: order.id,
    customerName: customer?.name ?? "Unknown customer",
    total: order.total,
  };
});
```

### Bug

> [!warning] Nested `find` is quadratic
> Calling `.find` inside a `.map` is O(n × m) — with 2,000 orders and 2,000 customers that's millions of comparisons, visible as slow renders. Build a lookup `Map` by id once, then read from it in O(1) inside the map.

### Fix

```ts
const customerById = Object.fromEntries(
  customers.map(customer => [customer.id, customer])
);

const rows = orders.map(order => {
  const customer = customerById[order.customerId];

  return {
    id: order.id,
    customerName: customer?.name ?? "Unknown customer",
    total: order.total,
  };
});
```

### React Version

```tsx
function OrderTable({
  orders,
  customers,
}: {
  orders: Order[];
  customers: Customer[];
}) {
  const customerById = useMemo(() => {
    return Object.fromEntries(customers.map(customer => [customer.id, customer]));
  }, [customers]);

  const rows = useMemo(() => {
    return orders.map(order => {
      const customer = customerById[order.customerId];

      return {
        id: order.id,
        customerName: customer?.name ?? "Unknown customer",
        total: order.total,
      };
    });
  }, [orders, customerById]);

  return <DataTable rows={rows} />;
}
```

### Tradeoff

Memoization helps only if `orders` and `customers` references are stable. If a parent creates new arrays every render, the memo runs every render anyway. Fix the unstable input before adding more memoization.

## 7. Scenario: Group Data By Status

### Problem

You need kanban columns from flat tasks.

```ts
type Status = "todo" | "doing" | "done";

type Task = {
  id: string;
  title: string;
  status: Status;
};
```

### Fix

```ts
const emptyGroups: Record<Status, Task[]> = {
  todo: [],
  doing: [],
  done: [],
};

function groupTasksByStatus(tasks: Task[]): Record<Status, Task[]> {
  return tasks.reduce<Record<Status, Task[]>>(
    (groups, task) => {
      groups[task.status].push(task);
      return groups;
    },
    {
      todo: [],
      doing: [],
      done: [],
    }
  );
}

const grouped = groupTasksByStatus(tasks);
```

### Why This Local Mutation Is Acceptable

The reducer mutates `groups`, which is a new object created for this transformation. It does not mutate `tasks` or `task` objects. Local mutation inside a newly owned accumulator is often clearer and more efficient than copying the whole accumulator on every item.

### Bug To Avoid

```ts
function badGroup(tasks: Task[]) {
  return tasks.reduce((groups, task) => {
    task.title = task.title.trim(); // mutates source task
    groups[task.status].push(task);
    return groups;
  }, emptyGroups);
}
```

This mutates both task objects and the shared `emptyGroups` object.

### Fix

```ts
function safeGroup(tasks: Task[]) {
  return tasks.reduce<Record<Status, Task[]>>(
    (groups, task) => {
      groups[task.status].push({
        ...task,
        title: task.title.trim(),
      });
      return groups;
    },
    {
      todo: [],
      doing: [],
      done: [],
    }
  );
}
```

## 8. Scenario: Filter, Sort, Paginate

### Problem

A product grid supports search, category filtering, sorting, and pagination.

### Fix

```ts
type Product = {
  id: string;
  name: string;
  category: string;
  price: number;
  inStock: boolean;
};

type SortMode = "price-asc" | "price-desc" | "name";

function getVisibleProducts({
  products,
  query,
  category,
  sortMode,
  page,
  pageSize,
}: {
  products: Product[];
  query: string;
  category: string;
  sortMode: SortMode;
  page: number;
  pageSize: number;
}) {
  const normalizedQuery = query.trim().toLowerCase();

  const filtered = products.filter(product => {
    const matchesQuery = product.name.toLowerCase().includes(normalizedQuery);
    const matchesCategory = category === "all" || product.category === category;

    return matchesQuery && matchesCategory;
  });

  const sorted = filtered.toSorted((a, b) => {
    if (sortMode === "price-asc") return a.price - b.price;
    if (sortMode === "price-desc") return b.price - a.price;
    return a.name.localeCompare(b.name);
  });

  const start = (page - 1) * pageSize;

  return {
    total: sorted.length,
    pageItems: sorted.slice(start, start + pageSize),
  };
}
```

### Why This Order Works

- Filter first to reduce the number of sorted items.
- Sort before pagination so page order is globally correct.
- Slice last to return only the current page.
- Use `toSorted` so the original product data is not mutated.

### Tradeoff

For small and medium lists, this is clean client-side code. For huge lists, prefer server-side filtering/sorting/pagination or virtualization, because the browser still pays for the transformed arrays.

## 9. Scenario: Stable Selected IDs

### Problem

The UI stores selected products as full objects:

```ts
const [selectedProducts, setSelectedProducts] = useState<Product[]>([]);
```

### Bug

After a refetch, new product objects arrive. Object reference checks fail, and duplicated selections can appear.

### Better Shape

```ts
const [selectedIds, setSelectedIds] = useState<string[]>([]);

const selectedIdSet = useMemo(() => new Set(selectedIds), [selectedIds]);

const rows = products.map(product => ({
  ...product,
  selected: selectedIdSet.has(product.id),
}));
```

### Toggle Selection

```ts
function toggleSelected(id: string) {
  setSelectedIds(prev => {
    if (prev.includes(id)) {
      return prev.filter(selectedId => selectedId !== id);
    }

    return [...prev, id];
  });
}
```

### Tradeoff

Store primitive IDs for stable identity. Derive full selected objects from the latest data when you need them.

## 10. Scenario: Avoid Heavy Work In Render

### Problem

```tsx
function SearchResults({ products, query }: Props) {
  const rows = products
    .filter(product => product.name.toLowerCase().includes(query.toLowerCase()))
    .toSorted((a, b) => a.price - b.price)
    .map(product => ({
      id: product.id,
      label: `${product.name} - ${product.price}`,
    }));

  return <ResultList rows={rows} />;
}
```

This may be fine for 50 items. It may be painful for 50,000 items and a query that changes on every keypress.

### Fix Options

```tsx
function SearchResults({ products, query }: Props) {
  const normalizedQuery = query.trim().toLowerCase();

  const rows = useMemo(() => {
    return products
      .filter(product => product.name.toLowerCase().includes(normalizedQuery))
      .toSorted((a, b) => a.price - b.price)
      .map(product => ({
        id: product.id,
        label: `${product.name} - ${product.price}`,
      }));
  }, [products, normalizedQuery]);

  return <ResultList rows={rows} />;
}
```

Other valid fixes:

- debounce the query
- move filtering/sorting to the server
- precompute normalized search fields
- virtualize the rendered list
- use a Web Worker for heavy client-side computation

### Tradeoff

`useMemo` is a performance optimization, not a correctness tool. It caches based on dependencies. If the calculation is cheap, memoization can add noise. If the calculation is expensive and inputs are stable, it can be useful.

## 11. Scenario: Remove Duplicates

### Primitive Values

```js
const tags = ["react", "js", "react", "css"];
const uniqueTags = [...new Set(tags)];

console.log(uniqueTags);
// ["react", "js", "css"]
```

### Objects By ID

```js
function uniqueById(items) {
  return Array.from(
    new Map(items.map(item => [item.id, item])).values()
  );
}

const unique = uniqueById([
  { id: "p1", name: "Old" },
  { id: "p1", name: "New" },
]);

console.log(unique);
// [{ id: "p1", name: "New" }]
```

The later item wins because it overwrites the same key in the `Map`.

## 12. Scenario: Async Data Shape Guard

### Problem

```tsx
function UserList({ data }: { data?: { users?: User[] } }) {
  return data.users.map(user => <UserRow key={user.id} user={user} />);
}
```

### Bug

During loading, `data` or `data.users` can be undefined.

### Fix

```tsx
function UserList({ data }: { data?: { users?: User[] } }) {
  const users = data?.users ?? [];

  return users.map(user => (
    <UserRow key={user.id} user={user} />
  ));
}
```

### Tradeoff

An empty fallback is fine when the UI also shows loading/error state elsewhere. Do not silently hide API shape problems that should be validated or logged.

## 13. Production Checklist

- Define the transformation boundary: fetch layer, selector, component, or utility.
- Keep transformations pure unless mutation is local to a newly created accumulator.
- Use stable IDs as React keys and selection state.
- Build lookup maps for repeated ID access.
- Filter before sorting when possible.
- Sort before pagination when the page should reflect global order.
- Use `toSorted` or copy before sorting state/props.
- Memoize expensive transformations only when inputs are stable.
- Consider server-side work for large datasets.
- Consider virtualization when rendering many rows.
- Add fallbacks for missing/partial async data.
- Test transformations with empty arrays, missing fields, duplicate IDs, and out-of-order data.

## Real-World Use Cases

### Flattening infinite-scroll pages

`useInfiniteQuery` returns data as an array of pages, but the feed renders one flat list. Refetches can also re-deliver overlapping items at page boundaries.

```tsx
const { data } = useInfiniteQuery({
  queryKey: ["feed"],
  queryFn: fetchFeedPage,
  getNextPageParam: (last) => last.nextCursor,
});

const posts = useMemo(
  () => uniqueById((data?.pages ?? []).flatMap(page => page.items)),
  [data]
);
```

Works because `flatMap` maps each page to its items and flattens exactly one level in a single pass, and the `uniqueById` helper from the deduplication scenario above keeps the last occurrence when cursors overlap. The `?? []` guard covers the loading state, per the async shape-guard scenario.

### Zero-filled time series for a dashboard chart

A revenue chart shows the last 14 days. Days with no orders are simply absent from the API response, and most chart libraries either skip or interpolate missing points — both wrong for revenue.

```ts
function toDailySeries(orders: Order[], days: number) {
  const totalsByDay = new Map<string, number>();
  for (const order of orders) {
    const day = order.createdAt.slice(0, 10); // "2026-07-16"
    totalsByDay.set(day, (totalsByDay.get(day) ?? 0) + order.total);
  }

  return Array.from({ length: days }, (_, i) => {
    const day = isoDateDaysAgo(days - 1 - i);
    return { day, total: totalsByDay.get(day) ?? 0 };
  });
}
```

Works because the transformation makes missing values explicit: the `Map` accumulates only observed days, then `Array.from` manufactures a dense, ordered axis with an intentional `0` for every gap — the same "explicit placeholder over accidental hole" rule from [[07 - Arrays and Iteration/01 - Array Internals|Array Internals]].

### Diffing tags on save

A tag editor lets the user add and remove tags locally, then persists only the delta — the API expects `{ added, removedIds }`, not the whole list.

```ts
const savedIds = new Set(savedTags.map(tag => tag.id));
const currentIds = new Set(currentTags.map(tag => tag.id));

const added = currentTags.filter(tag => !savedIds.has(tag.id));
const removedIds = [...savedIds].filter(id => !currentIds.has(id));

await api.updateTags(articleId, { added, removedIds });
```

Works because each membership check against a `Set` is O(1), so the whole diff is linear — the nested-`includes` version of this is the same quadratic trap as `find` inside `map` from the lookup-map scenario. See [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]].

> [!tip] Diff on save, not on keystroke
> Keeping the working copy as plain state and computing the diff once at submit time is cheaper and simpler than maintaining incremental added/removed lists during editing.

## 14. Interview Answer

**Short version:** Frontend data transformation converts raw API data into UI-ready shapes while preserving correctness, identity, and performance.

**Strong version:** I separate API shape from UI shape. I use `map` for view models, `filter` for visible subsets, `reduce` or `Object.fromEntries` for summaries and lookup maps, and `toSorted` or copied `sort` for non-mutating order. In React, the transformation should be pure and should not mutate props, state, or cache data. I only memoize when the transformation is expensive and the dependencies are stable. For large lists, I consider server-side filtering/sorting, pagination, virtualization, or a worker instead of doing all work in render.

## 15. Common Mistakes

- Mapping API data directly in JSX until the component becomes unreadable.
- Repeating `find` inside `map` for large related datasets.
- Sorting before filtering without reason.
- Sorting state or props in place.
- Storing selected objects instead of stable selected IDs.
- Adding `useMemo` while dependencies change every render.
- Treating `[]` fallback as a substitute for loading/error UI.
- Using array indexes as keys for reorderable lists.

## 16. Practice

1. Transform a nested API user into a flat `UserRow`.
2. Build `customerById` with `Object.fromEntries`.
3. Group tasks by status with `reduce`.
4. Write a filter/sort/paginate function and explain the order.
5. Store selected IDs, then derive selected rows from fresh API data.
6. Identify when a transformation belongs on the server instead of in the browser.

## Related Notes

- [[07 - Arrays and Iteration/02 - Mutating vs Non Mutating Methods|Mutating vs Non Mutating Methods]]
- [[07 - Arrays and Iteration/03 - map filter reduce forEach|map filter reduce forEach]]
- [[07 - Arrays and Iteration/04 - find some every includes|find some every includes]]
- [[07 - Arrays and Iteration/05 - sort and Modern Immutable Array Methods|sort and Modern Immutable Array Methods]]
- [[12 - Advanced Language Concepts/09 - Map Set WeakMap WeakSet|Map Set WeakMap WeakSet]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[17 - Practical Frontend Scenarios/05 - Avoiding Mutation in State|Avoiding Mutation in State]]
- [[01 - Roadmap|Roadmap]]
