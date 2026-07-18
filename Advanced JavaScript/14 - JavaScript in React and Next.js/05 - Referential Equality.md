---
tags: [javascript, react, nextjs, referential-equality]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# Referential Equality

## Maturity Target

- Priority: #must-know
- Study time: 75-100 minutes
- Interview signal: can explain why `React.memo`, dependency arrays, state bailouts, and context values depend on reference identity.
- Production signal: can stabilize the right values without adding memoization everywhere.
- Fast track: sections 3, 5, 6, 8, and practice Q1-Q3.

## Source Anchors

- [MDN: Object.is](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is)
- [React docs: memo](https://react.dev/reference/react/memo)
- [React docs: useMemo](https://react.dev/reference/react/useMemo)
- [React docs: useCallback](https://react.dev/reference/react/useCallback)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)

## 1. Concept

Referential equality means two values are equal because they refer to the exact same object, array, or function, not because they have the same contents.

```js
Object.is({ page: 1 }, { page: 1 }); // false

const a = { page: 1 };
const b = a;
Object.is(a, b); // true
```

React relies on reference identity in several places:

- Dependency arrays compare each dependency with `Object.is`.
- `React.memo` compares props with `Object.is` by default.
- State updates can be skipped when the new state is `Object.is` equal to the old state.
- Context consumers update when the provided value changes identity.
- `useMemo` and `useCallback` cache only while dependency identities are stable.

## 2. Why It Matters

React does not deep-compare your data. That is a performance and correctness decision. It expects you to create new references when values really change and preserve references when values did not change.

Production symptoms:

- A memoized component re-renders every parent render.
- An effect refetches forever because an object dependency is always new.
- Context updates rerender the whole app because `{ user, logout }` is recreated every render.
- Mutated state does not rerender because the reference is the same.
- A query key or options object causes duplicated network work.

## 3. Official Mechanism

`Object.is` uses JavaScript's SameValue comparison. For objects, arrays, and functions, it compares identity. Two separate object literals are never equal even if their properties match.

Important primitive details:

```js
Object.is(NaN, NaN); // true
Object.is(0, -0); // false
Object.is(3, 3); // true
Object.is('a', 'a'); // true
Object.is({}, {}); // false
Object.is([], []); // false
Object.is(() => {}, () => {}); // false
```

React uses this kind of comparison because it is O(1) and predictable. Deep equality can be expensive, can loop on circular structures, and can hide mutation mistakes.

## 4. Mental Model

Every render reevaluates the component body:

```tsx
function Toolbar() {
  const style = { color: 'white' };
  const filters = ['active'];
  const onRefresh = () => refresh();

  return <Panel style={style} filters={filters} onRefresh={onRefresh} />;
}
```

On every render:

- `style` is a new object.
- `filters` is a new array.
- `onRefresh` is a new function.

If `Panel` is wrapped in `React.memo`, these props still look changed because the references changed.

## 5. Real Frontend Example

### Problem: memoized child still rerenders

```tsx
const OrderTable = React.memo(function OrderTable({
  columns,
  onRowClick,
}: {
  columns: string[];
  onRowClick: (id: string) => void;
}) {
  console.log('OrderTable rendered');
  return <table>{/* rows */}</table>;
});

function OrdersPage({ accountId }: { accountId: string }) {
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  return (
    <OrderTable
      columns={['id', 'status', 'total']}
      onRowClick={id => setSelectedId(id)}
    />
  );
}
```

### Bug

> [!warning] memo defeated by new references
> `OrderTable` is memoized, but it receives a new `columns` array and a new `onRowClick` function on every render. `React.memo` compares props with `Object.is`, sees changes, and rerenders — so the memo does nothing.

### Fix

```tsx
const ORDER_COLUMNS = ['id', 'status', 'total'] as const;

function OrdersPage({ accountId }: { accountId: string }) {
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  const handleRowClick = React.useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  return (
    <OrderTable
      columns={ORDER_COLUMNS}
      onRowClick={handleRowClick}
    />
  );
}
```

The array is defined once at module scope. The callback is stable because it reads only the stable setter.

## Real-World Use Cases

### Store selector that returns a fresh object

A Zustand (or any `useSyncExternalStore`-based) store is read with a selector that builds a new object on every call. The snapshot never compares equal, so the component rerenders on every store change — or React warns about an unstable snapshot and can loop.

```tsx
// BUG: new object per call — never Object.is-equal to the previous snapshot
const { status, total } = useCartStore(state => ({
  status: state.status,
  total: state.total,
}));

// FIX: select primitives, or pass a shallow-equality comparator
const status = useCartStore(state => state.status);
const total = useCartStore(state => state.total);
```

Store hooks decide "did the slice change?" with reference comparison, exactly like dependency arrays. See [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]].

### Structural sharing as a feature in data libraries

TanStack Query refetches orders in the background. The payload is byte-identical, so the library structurally shares: it keeps the previous references for unchanged rows, and memoized row components skip rerendering.

```tsx
const { data: orders } = useQuery({
  queryKey: ['orders', accountId],
  queryFn: () => fetchOrders(accountId),
});
// After a background refetch with an identical payload, `orders` keeps the SAME
// reference — <OrderRow> wrapped in React.memo does not rerender.
```

Libraries do this work precisely because React compares with `Object.is`: preserving identity is how they make refetches invisible to memoized trees.

> [!tip]
> If you post-process query data with `.map` or `.filter` in render, you throw that identity preservation away — memoize the derived value or use the library's `select` option.

### "Reset filters" that always looks like a change

A filter panel's reset button constructs a new defaults object every click. Even when the filters are already at their defaults, the state gets a new identity, the fetch effect keyed on `filters` refires, and the list reloads for no reason.

```tsx
// BUG: new identity even when nothing changed
function resetFilters() {
  setFilters({ status: 'all', dateRange: null });
}

// FIX: a module-level constant lets React bail out entirely
const DEFAULT_FILTERS = { status: 'all', dateRange: null } as const;
function resetFilters() {
  setFilters(DEFAULT_FILTERS);
}
```

React skips the render when the new state is `Object.is`-equal to the old one — a bailout you only get by reusing the same reference. See [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]].

## 6. Where Identity Matters

### Dependency arrays

```tsx
function UserSettings({ user }: { user: User }) {
  React.useEffect(() => {
    loadSettings(user.id);
  }, [user.id]);
}
```

Prefer depending on the primitive field you use. Depending on `[user]` can rerun when the parent creates a new user object with the same `id`.

### Context values

```tsx
function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);

  const value = React.useMemo(() => {
    return {
      user,
      logout: () => setUser(null),
    };
  }, [user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
```

Without `useMemo`, the provider value is a new object every render, and all consumers may update even if `user` did not change.

### Derived data

```tsx
const visibleRows = React.useMemo(() => {
  return rows.filter(row => row.status === status);
}, [rows, status]);
```

Memoization is useful when filtering is expensive or when `visibleRows` is passed to a memoized child that depends on stable identity.

### Query keys and configs

Prefer primitives:

```tsx
useQuery({
  queryKey: ['orders', accountId, status],
  queryFn: () => fetchOrders(accountId, status),
});
```

Avoid deeply nested inline objects unless the library documents how it hashes or compares them.

## 7. Production Tradeoffs

- Do not memoize every literal. Memoize when identity stability is observable: memoized child props, effect dependencies, context values, expensive derived data, or third-party cache keys.
- Passing primitives is often better than passing objects.
- Moving constants outside the component is simpler than `useMemo(..., [])`.
- A custom comparison in `React.memo` can help, but it is easy to make slower or incorrect. Prefer stable props first.
- The React Compiler can reduce manual memoization in supported setups, but the underlying identity model still matters for effects, caches, context, and JavaScript correctness.

## 8. Interview Answer

Referential equality means objects, arrays, and functions are equal only when they are the same reference. React uses `Object.is` for dependency arrays, memoized props, and state equality checks. Since object, array, and function literals are recreated every render, they are new references even if their contents look the same. This can break `React.memo`, rerun effects, and cause unnecessary context updates. The fix is to pass primitives where possible, move stable constants outside components, use `useMemo` for derived objects or arrays, and use `useCallback` for functions whose identity matters.

## 9. Mistakes to Avoid

| Mistake | Reality |
| --- | --- |
| "The object contents are the same, so React should skip it" | React compares references, not deep contents. |
| `React.memo` around a child with always-new props | One always-new prop breaks memoization for that child. |
| `JSON.stringify(obj)` in dependencies | It is expensive and hides data modeling issues. |
| `useMemo` for values no one compares | It adds complexity without benefit. |
| Mutating state to preserve reference | You preserve identity but break React's state model. |

> [!tip] Identity, not contents
> React compares with `Object.is`, so "the contents are the same" is irrelevant — one always-new prop (inline object/array/arrow) breaks a child's memoization. Stabilize the reference (`useMemo`/`useCallback`/hoist a constant) only when something actually compares it.

## 10. Practice

### Q1. What is the output?

```js
const a = { name: 'Mustafa' };
const b = { name: 'Mustafa' };
const c = a;

console.log(Object.is(a, b));
console.log(Object.is(a, c));
console.log(Object.is(NaN, NaN));
console.log(Object.is(0, -0));
```

Expected output:

```text
false
true
true
false
```

### Q2. Why does this effect rerun?

```tsx
const filters = { status: 'open' };

React.useEffect(() => {
  fetchTickets(filters);
}, [filters]);
```

`filters` is a new object every render. Move it inside the effect, depend on the primitive `status`, or memoize it if another consumer needs the same reference.

### Q3. When is `useCallback` unnecessary?

It is unnecessary when the function is not passed to a memoized child, not used as a dependency, and not part of a stable context value or external subscription. Plain inline handlers are fine for many components.

## Related Notes

- [[12 - Advanced Language Concepts/01 - Primitive vs Reference Values|Primitive vs Reference Values]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[14 - JavaScript in React and Next.js/04 - Dependency Arrays|Dependency Arrays]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
