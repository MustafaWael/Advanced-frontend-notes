---
tags: [javascript, performance, memory, react-performance-examples, react]
module: "13 - Performance and Memory"
priority: important
status: not-started
---

# React Performance Examples

## Maturity Target

- Priority: #important
- Study time: 130-180 minutes
- Interview signal: you can reason about render, commit, memoization, context, list size, effects, network waterfalls, and INP.
- Production signal: you measure before optimizing and choose fixes based on the bottleneck rather than defaulting to `useMemo`.
- Dependencies: [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]], [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]], [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]

## Source Anchors

- [React Render and Commit](https://react.dev/learn/render-and-commit)
- [React memo](https://react.dev/reference/react/memo)
- [React useMemo](https://react.dev/reference/react/useMemo)
- [React useCallback](https://react.dev/reference/react/useCallback)
- [React Profiler](https://react.dev/reference/react/Profiler)
- [web.dev INP](https://web.dev/articles/inp)

## 1. Concept

React performance is not one trick. It is reducing the work that matters:

- unnecessary renders;
- expensive render calculations;
- large DOM output;
- broad context updates;
- slow effects;
- network waterfalls;
- main-thread blocking during interactions.

React rendering has a render phase, where React calculates what the UI should look like, and a commit phase, where changes are applied to the host environment.

## 2. Why It Matters

Users feel performance at interaction points:

- typing in a search box;
- opening a menu;
- filtering a table;
- navigating a route;
- expanding a chart;
- submitting a form.

web.dev's INP guidance focuses on responsiveness across interactions. If JavaScript blocks the main thread during a click or keypress, the next paint is delayed and the UI feels broken.

## 3. Accurate Mechanism

React re-renders a component when:

- its state changes;
- its parent renders and passes it new props;
- consumed context changes;
- external store subscriptions notify it;
- framework routing or data changes cause updates.

`memo` can skip a child render when props are equal by shallow comparison. `useMemo` and `useCallback` can stabilize values and functions when that stability protects an expensive boundary.

They help only when identity stability is part of the bottleneck.

## 4. Mental Model

Find the bottleneck before choosing the tool.

| Bottleneck | Likely fix |
| --- | --- |
| expensive pure calculation | `useMemo`, precompute, worker |
| memoized child rerenders | stabilize props or split component |
| huge list DOM | virtualization or pagination |
| broad context update | split context or selectors |
| slow click response | reduce main-thread work, defer non-urgent work |
| network waterfall | parallelize or move fetch to route/server layer |
| repeated effect work | fix dependencies or ownership |

## 5. Real Frontend Bug: Memoized Chart Still Rerenders

Problem:

```tsx
const Chart = memo(function Chart({ data, options }: ChartProps) {
  return <HeavyChart data={data} options={options} />;
});

function Dashboard({ data }: { data: Point[] }) {
  const [query, setQuery] = useState("");

  return (
    <>
      <input value={query} onChange={(event) => setQuery(event.target.value)} />
      <Chart data={data} options={{ showLegend: true }} />
    </>
  );
}
```

Bug:

- every keystroke renders `Dashboard`;
- `options={{ showLegend: true }}` creates a new object;
- `memo` sees changed props and re-renders `Chart`;
- the expensive chart rerenders while typing.

Fix:

```tsx
function Dashboard({ data }: { data: Point[] }) {
  const [query, setQuery] = useState("");

  const chartOptions = useMemo(
    () => ({ showLegend: true }),
    []
  );

  return (
    <>
      <input value={query} onChange={(event) => setQuery(event.target.value)} />
      <Chart data={data} options={chartOptions} />
    </>
  );
}
```

Better if the option is constant and not user-specific:

```tsx
const CHART_OPTIONS = { showLegend: true };
```

> [!tip] Tradeoff
> memoization is justified only if `Chart` is expensive or the rerender is visible in profiling.

## 6. Real Frontend Bug: Context Rerenders Everything

Problem:

```tsx
const AppContext = createContext<{
  theme: Theme;
  currentUser: User;
  notifications: Notification[];
} | null>(null);
```

If notifications update frequently, every consumer of the combined context may re-render, including components that only need theme.

Fix:

```tsx
const ThemeContext = createContext<Theme | null>(null);
const CurrentUserContext = createContext<User | null>(null);
const NotificationsContext = createContext<Notification[] | null>(null);
```

Production reasoning: split context by update frequency and ownership. Do not put all app state into one provider because it is convenient.

## 7. Real Frontend Bug: Derived List Blocks Typing

Problem:

```tsx
function ProductSearch({ products }: { products: Product[] }) {
  const [query, setQuery] = useState("");

  const visible = products
    .filter((product) => product.name.includes(query))
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <>
      <input value={query} onChange={(event) => setQuery(event.target.value)} />
      <ProductList products={visible} />
    </>
  );
}
```

Fix first step:

```tsx
const visible = useMemo(() => {
  return products
    .filter((product) => product.name.includes(query))
    .sort((a, b) => a.name.localeCompare(b.name));
}, [products, query]);
```

If typing is still slow because the rendered list is huge, use virtualization or pagination. If the calculation itself is heavy, consider indexing, debouncing, deferred updates, or a worker.

## 8. Measuring React Work

Use React Profiler for render cost:

```tsx
function onRender(
  id: string,
  phase: "mount" | "update" | "nested-update",
  actualDuration: number,
  baseDuration: number
) {
  console.log({ id, phase, actualDuration, baseDuration });
}

<Profiler id="ProductSearch" onRender={onRender}>
  <ProductSearch products={products} />
</Profiler>
```

Use Chrome Performance for main-thread work, layout, paint, long tasks, and interaction delay.

Use field data for real user responsiveness. Lab data is useful for reproduction, but field data tells you what real users experience.

## 9. Next.js and React Performance

Performance can be won or lost before React even hydrates:

- avoid moving server-only work into client components;
- keep `"use client"` boundaries small;
- lazy-load heavy client-only widgets;
- avoid route-level waterfalls;
- stream or split non-critical UI where appropriate;
- reduce JavaScript shipped to the browser.

See [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]] and [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]].

## 10. Production Tradeoffs

| Tool | Helps | Cost |
| --- | --- | --- |
| `memo` | skip expensive child renders | prop comparison overhead |
| `useMemo` | skip expensive calculation | dependency complexity and memory |
| `useCallback` | stable function prop | can add noise if child is not memoized |
| context splitting | reduce broad updates | more providers |
| virtualization | lower DOM/render work | scroll/accessibility complexity |
| debounce/defer | smoother typing | delayed results |
| lazy loading | lower initial JS | loading/error states needed |

## 11. Interview Answer

**Short version:** React performance work starts with measurement. Then you reduce the specific bottleneck: unnecessary renders, expensive calculations, huge DOM, broad context updates, network waterfalls, or main-thread blocking.

**Strong version:** React rerenders from state, prop, context, and external store changes. `memo`, `useMemo`, and `useCallback` work through identity comparison and help only when they protect expensive work. A new object prop can defeat `memo`, but stabilizing props is not always the right fix; sometimes the real issue is rendering thousands of rows, blocking the main thread during input, or fetching data in a waterfall. I use React Profiler for render cost, Chrome Performance for main-thread work, and field metrics like INP for real responsiveness.

## 12. Common Mistakes

- Adding `useMemo` everywhere without measuring.
- Using `useCallback` when no memoized child receives the callback.
- Passing new object/array literals to memoized children.
- Putting all app state in one context.
- Rendering huge lists and only memoizing the filter.
- Ignoring network and bundle cost while focusing only on rerenders.
- Profiling only development builds.

## 13. Practice

1. Fix a memoized chart that rerenders because of a new object prop.
2. Split a broad context into smaller providers by update frequency.
3. Decide whether a slow search needs memoization, debouncing, indexing, virtualization, or a worker.
4. Explain what React Profiler's `actualDuration` and `baseDuration` tell you.
5. Connect a slow click interaction to INP and main-thread blocking.

## Related Notes

- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[10 - Modules/07 - Tree Shaking and Code Splitting|Tree Shaking and Code Splitting]]
- [[17 - Practical Frontend Scenarios/04 - Optimizing Large List Transformations|Optimizing Large List Transformations]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]]
- [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling Overview]]
- [[21 - React Internals and Patterns/10 - React 19|React 19]]
- [[01 - Roadmap|Roadmap]]
