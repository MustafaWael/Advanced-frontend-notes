---
tags: [javascript, scenarios, react, optimizing-large-list-transformations]
module: "17 - Practical Frontend Scenarios"
priority: important
status: not-started
---

# Optimizing Large List Transformations

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: can distinguish expensive calculation, too many DOM nodes, and unnecessary rerenders.
- Production signal: can make large list UIs responsive with measurement, memoization, pagination, and virtualization.
- Fast track: sections 2, 4, 5, and 8.

## Source Anchors

- [React docs: useMemo](https://react.dev/reference/react/useMemo)
- [React docs: memo](https://react.dev/reference/react/memo)
- [React docs: Profiler](https://react.dev/reference/react/Profiler)
- [web.dev: Optimize long tasks](https://web.dev/articles/optimize-long-tasks)
- [MDN: Array.prototype.sort](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/sort)

## 1. Scenario

A table with 5,000 rows filters and sorts on every keystroke. The input feels delayed. Users see typing lag, scroll jank, or a frozen tab.

There are usually three separate problems:

- expensive transformation work
- too many rendered DOM nodes
- unstable props causing unnecessary rerenders

Measure before choosing a fix.

## 2. Broken Version

```tsx
function OrdersTable({ orders, query, sortKey }: Props) {
  // BUG: runs on every render, even if the render was caused by unrelated state.
  const visibleOrders = orders
    .filter(order => order.customer.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => String(a[sortKey]).localeCompare(String(b[sortKey])));

  return (
    <table>
      <tbody>
        {visibleOrders.map(order => (
          <OrderRow key={order.id} order={order} />
        ))}
      </tbody>
    </table>
  );
}
```

## 3. Root Cause

`filter` creates a new array. `sort` mutates the array it is called on. Rendering thousands of rows creates thousands of React elements and DOM nodes. If `OrderRow` receives unstable props, memoization will not help.

## 4. Fix Transformation Work

```tsx
function OrdersTable({ orders, query, sortKey }: Props) {
  const normalizedQuery = query.trim().toLowerCase();

  const visibleOrders = React.useMemo(() => {
    const filtered = normalizedQuery
      ? orders.filter(order =>
          order.customer.toLowerCase().includes(normalizedQuery)
        )
      : orders;

    // Copy before sorting because sort mutates.
    return [...filtered].sort((a, b) =>
      String(a[sortKey]).localeCompare(String(b[sortKey]))
    );
  }, [orders, normalizedQuery, sortKey]);

  return (
    <table>
      <tbody>
        {visibleOrders.map(order => (
          <OrderRow key={order.id} order={order} />
        ))}
      </tbody>
    </table>
  );
}
```

Why it works:

- The expensive work only reruns when its real inputs change.
- Sorting does not mutate the original `orders` array.
- The dependency list is based on values used by the calculation.

## 5. Fix Too Many DOM Nodes

Memoization does not solve rendering 10,000 rows. Use pagination or virtualization.

```tsx
function OrdersTable({ visibleOrders }: { visibleOrders: Order[] }) {
  const rowVirtualizer = useVirtualizer({
    count: visibleOrders.length,
    getScrollElement: () => scrollParentRef.current,
    estimateSize: () => 44,
  });

  return (
    <div ref={scrollParentRef} style={{ height: 600, overflow: 'auto' }}>
      <div style={{ height: rowVirtualizer.getTotalSize(), position: 'relative' }}>
        {rowVirtualizer.getVirtualItems().map(virtualRow => {
          const order = visibleOrders[virtualRow.index];

          return (
            <div
              key={order.id}
              style={{
                position: 'absolute',
                transform: `translateY(${virtualRow.start}px)`,
                height: virtualRow.size,
              }}
            >
              <OrderRow order={order} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

Use a proven virtualization library rather than hand-rolling scrolling math in production.

## 6. Fix Unstable Row Props

```tsx
const OrderRow = React.memo(function OrderRow({
  order,
  onSelect,
}: {
  order: Order;
  onSelect: (id: string) => void;
}) {
  return (
    <tr onClick={() => onSelect(order.id)}>
      <td>{order.customer}</td>
      <td>{order.total}</td>
    </tr>
  );
});

function OrdersPage({ orders }: { orders: Order[] }) {
  const onSelect = React.useCallback((id: string) => {
    navigate(`/orders/${id}`);
  }, []);

  return <OrdersTable orders={orders} onSelect={onSelect} />;
}
```

`React.memo` only helps if props remain referentially stable when data did not change.

## 7. Tradeoffs

- `useMemo` helps expensive pure calculations; it does not reduce DOM node count.
- Virtualization improves large lists but complicates accessibility, keyboard navigation, dynamic heights, and testing.
- Pagination can be simpler and more accessible than virtualization.
- Server-side filtering and sorting may be better when the dataset is large or sensitive.
- Debounce or deferred rendering can improve typing responsiveness, but stale result handling still matters.

## 8. Production Checklist

- [ ] Did I measure with React Profiler or Performance panel?
- [ ] Is the bottleneck calculation, rendering, network, or layout?
- [ ] Is `sort` mutating incoming props?
- [ ] Are expensive transforms memoized with correct dependencies?
- [ ] Are row props stable if using `React.memo`?
- [ ] Should this be server-side filtering/pagination?
- [ ] Is virtualization accessible and tested?
- [ ] Does typing remain responsive on low-end devices?

## 9. Interview Angle

Strong answer:

"I would not start by adding `useMemo` everywhere. I would measure. If the transform is expensive, memoize the pure calculation and avoid mutating `sort`. If the DOM is too large, use pagination or virtualization. If children rerender unnecessarily, stabilize props and use `React.memo` only where it helps."

## Related Notes

- [[07 - Arrays and Iteration/07 - Frontend Data Transformation Examples|Frontend Data Transformation Examples]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[13 - Performance and Memory/09 - Performance Checklist|Performance Checklist]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
