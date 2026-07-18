---
tags: [javascript, performance, memory, memoization-and-expensive-computations]
module: "13 - Performance and Memory"
priority: important
status: not-started
aliases: [Memoization]
---

# Memoization and Expensive Computations

## Maturity Target

- Priority: #important
- Study time: 100-140 minutes
- Interview signal: you can explain memoization as a cache with dependencies, invalidation, memory cost, and measurement requirements.
- Production signal: you optimize expensive pure calculations and render paths without memoizing everything blindly.
- Dependencies: [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]], [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]], [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]

## Source Anchors

- [React useMemo](https://react.dev/reference/react/useMemo)
- [React useCallback](https://react.dev/reference/react/useCallback)
- [React memo](https://react.dev/reference/react/memo)
- [React Profiler](https://react.dev/reference/react/Profiler)
- [MDN Performance API](https://developer.mozilla.org/en-US/docs/Web/API/Performance_API)

## 1. Concept

Memoization caches a result and reuses it when inputs have not changed.

In plain JavaScript, memoization is usually a map from cache key to result.

In React, `useMemo` caches a calculated value for a component render until dependencies change.

```tsx
const visibleProducts = useMemo(
  () => filterProducts(products, query),
  [products, query]
);
```

## 2. Why It Matters

Some work is expensive enough to notice:

- filtering/sorting thousands of items;
- parsing large JSON;
- grouping or aggregating table data;
- building chart series;
- recalculating derived data on every keystroke;
- re-rendering memoized children because props change identity.

Memoization can help, but it trades memory and complexity for less repeated work.

## 3. Accurate Mechanism

React compares dependency array entries with `Object.is`. If dependencies are the same, React can reuse the previous memoized value. If any dependency changed, React runs the calculation again.

```tsx
const options = { includeArchived: false };

const data = useMemo(() => {
  return compute(items, options);
}, [items, options]);
```

Bug: `options` is a new object every render, so the memo recalculates every render.

Fix:

```tsx
const data = useMemo(() => {
  return compute(items, { includeArchived: false });
}, [items]);
```

Or:

```tsx
const options = useMemo(() => ({ includeArchived: false }), []);
const data = useMemo(() => compute(items, options), [items, options]);
```

## 4. Mental Model

Memoization is a cache. Every cache needs:

- a key;
- a value;
- an invalidation rule;
- a lifetime;
- enough saved work to justify its cost.

If the calculation is cheap, memoization can make the code slower and harder to maintain.

## 5. Measure The Calculation

```ts
function getVisibleProducts(products: Product[], query: string) {
  const start = performance.now();

  const result = products
    .filter((product) => product.name.includes(query))
    .sort((a, b) => a.name.localeCompare(b.name));

  console.log(`filter/sort took ${performance.now() - start}ms`);
  return result;
}
```

Use this to identify whether the calculation is actually expensive. Remove noisy logs after investigation.

For React render cost, use React DevTools Profiler or `<Profiler>`, not only `performance.now()` inside calculations.

## 6. Real Frontend Bug: Memoizing The Wrong Thing

Problem:

```tsx
function SearchResults({ products, query }: Props) {
  const visible = useMemo(
    () => products.filter((product) => product.name.includes(query)),
    [products, query]
  );

  return (
    <ul>
      {visible.map((product) => (
        <ProductRow key={product.id} product={product} />
      ))}
    </ul>
  );
}
```

If `visible` has 10,000 items, `useMemo` may reduce filtering cost, but the page can still be slow because rendering 10,000 rows creates heavy React and DOM work.

Production fix:

```tsx
function SearchResults({ products, query }: Props) {
  const visible = useMemo(
    () => products.filter((product) => product.name.includes(query)),
    [products, query]
  );

  return (
    <VirtualizedList
      items={visible}
      rowHeight={44}
      renderRow={(product) => <ProductRow product={product} />}
    />
  );
}
```

> [!tip] Tradeoff
> virtualization adds layout/accessibility complexity, but it attacks the actual bottleneck when DOM size is the issue.

## 7. Plain JavaScript Memoization

```ts
function memoizeByString<T>(compute: (key: string) => T) {
  const cache = new Map<string, T>();

  return (key: string) => {
    const cached = cache.get(key);
    if (cached !== undefined) return cached;

    const value = compute(key);
    cache.set(key, value);
    return value;
  };
}
```

Production concern: this cache is unbounded and cannot cache actual `undefined` results accurately.

Safer bounded version:

```ts
function memoizeLatest<T>(compute: (key: string) => T, maxSize = 50) {
  const cache = new Map<string, T>();

  return (key: string) => {
    if (cache.has(key)) return cache.get(key)!;

    const value = compute(key);
    cache.set(key, value);

    if (cache.size > maxSize) {
      const oldestKey = cache.keys().next().value;
      cache.delete(oldestKey);
    }

    return value;
  };
}
```

## 8. React `memo`, `useMemo`, and `useCallback`

| Tool | Caches | Useful when |
| --- | --- | --- |
| `useMemo` | calculated value | expensive pure calculation or stable object prop |
| `useCallback` | function identity | memoized child receives callback prop |
| `memo` | component rendered output decision | child often receives same props and rendering is expensive |

`useCallback(fn, deps)` is similar to `useMemo(() => fn, deps)`.

Do not use these tools as decoration. Use them to protect an actual expensive boundary.

## 9. Production Tradeoffs

| Benefit | Cost |
| --- | --- |
| Fewer repeated calculations | retained cached values |
| Stable prop identity | dependency complexity |
| Fewer child renders | comparison overhead |
| Bounded cache | possible recomputation |
| Virtualized rendering | complexity in scrolling/accessibility |

## 10. Interview Answer

**Short version:** Memoization caches a result for inputs so repeated work can be skipped. It is useful when the saved work is more expensive than the cache and comparison overhead.

**Strong version:** Memoization is a cache with keys, values, invalidation, and lifetime. In React, `useMemo` and `useCallback` compare dependencies with `Object.is`, while `memo` compares props shallowly by default. Memoization helps expensive pure calculations and stable props at memoized boundaries, but it does not fix every performance issue. If the bottleneck is DOM size, network, layout, or a slow child render, the fix may be virtualization, data loading changes, or component restructuring instead. I measure first, memoize deliberately, and avoid unbounded caches.

## 11. Common Mistakes

- Memoizing cheap calculations.
- Forgetting that new objects/functions break dependency equality.
- Using `useMemo` to hide impure work.
- Omitting dependencies to force caching and creating stale values.
- Building unbounded memoization maps.
- Memoizing a list calculation when rendering the list is the bottleneck.
- Assuming `memo` deeply compares props.

## 12. Practice

1. Measure a sort/filter operation with `performance.now()`.
2. Fix a `useMemo` dependency that changes every render because of an object literal.
3. Explain when `useCallback` helps and when it does nothing.
4. Build a bounded memoization cache.
5. Choose between memoization and virtualization for a 20,000-row table.

## Related Notes

- [[02 - JavaScript Runtime Foundations/02 - JavaScript Engine and Runtime|JavaScript Engine and Runtime]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[01 - Roadmap|Roadmap]]
