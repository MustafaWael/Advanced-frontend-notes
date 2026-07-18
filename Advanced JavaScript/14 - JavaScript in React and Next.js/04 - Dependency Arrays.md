---
tags: [javascript, react, nextjs, dependency-arrays]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
---

# Dependency Arrays

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: can explain what dependencies mean and why React compares them with `Object.is`.
- Production signal: can remove unnecessary dependencies without lying to the linter.
- Fast track: sections 3, 5, 6, 7, and practice Q1-Q4.

## Source Anchors

- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [React docs: Removing Effect Dependencies](https://react.dev/learn/removing-effect-dependencies)
- [React docs: useMemo](https://react.dev/reference/react/useMemo)
- [React docs: useCallback](https://react.dev/reference/react/useCallback)
- [React docs: exhaustive-deps lint](https://react.dev/reference/eslint-plugin-react-hooks/lints/exhaustive-deps)
- [MDN: Object.is](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/is)

## 1. Concept

A dependency array tells React which reactive values a hook callback or calculation depends on. React compares each dependency with its previous value using `Object.is`. If any dependency is different, React updates the effect, memoized value, or memoized callback.

Dependency arrays appear in:

- `useEffect(setup, deps)`
- `useMemo(calculate, deps)`
- `useCallback(fn, deps)`
- `useLayoutEffect`, `useInsertionEffect`, and custom hooks built on them

They are not a scheduling wish list. They are a data-flow declaration.

## 2. Why It Matters

Wrong dependency arrays cause two opposite bug classes:

- Missing dependency: stale closure, stale memo, stale callback.
- Unstable dependency: effect loops, repeated subscriptions, unnecessary refetches, defeated memoization.

Good dependency reasoning is a core mid-level skill because it combines closures, referential equality, effects, and production performance.

## 3. Official Mechanism

For `useEffect`, React follows this lifecycle:

1. Run setup after the component commits.
2. On a later commit, compare every dependency using `Object.is`.
3. If at least one dependency changed, run the old cleanup with old values.
4. Run the new setup with new values.
5. On unmount, run the latest cleanup.

Dependency shapes:

```tsx
useEffect(() => {
  // Runs after every commit.
});

useEffect(() => {
  // Runs after mount, then cleanup on unmount.
}, []);

useEffect(() => {
  // Runs after mount and whenever userId changes.
}, [userId]);
```

For `useMemo` and `useCallback`, React compares dependencies and either returns the cached value/function or computes a new one.

```tsx
const visibleItems = React.useMemo(
  () => filterItems(items, query),
  [items, query]
);

const onSelect = React.useCallback(
  (id: string) => selectItem(projectId, id),
  [projectId]
);
```

## 4. What Counts as a Dependency

A dependency is any reactive value read inside the hook callback or calculation.

Reactive values include:

- Props
- State
- Variables declared inside the component
- Functions declared inside the component
- Values returned by hooks

Values that usually do not need dependencies:

- Module-level constants
- Imported functions that are stable module bindings
- State setter functions from `useState`
- Dispatch functions from `useReducer`
- Ref objects themselves, although `ref.current` reads require careful reasoning

```tsx
const API_ROOT = 'https://api.example.com';

function UserCard({ userId }: { userId: string }) {
  React.useEffect(() => {
    fetch(`${API_ROOT}/users/${userId}`);
  }, [userId]);
}
```

`API_ROOT` is module-level and not reactive. `userId` is a prop and must be listed.

## 5. Real Frontend Example

### Problem: object dependency creates an effect loop

```tsx
function ProductFeed({ categoryId }: { categoryId: string }) {
  const [products, setProducts] = React.useState<Product[]>([]);
  const options = { includeOutOfStock: false };

  React.useEffect(() => {
    fetchProducts(categoryId, options).then(setProducts);
  }, [categoryId, options]);

  return <ProductGrid products={products} />;
}
```

### Bug

> [!warning] The inline-object effect loop
> `options` is a new object on every render. React compares it with `Object.is`, and `Object.is(previousOptions, nextOptions)` is always `false`. The effect runs after every render. Since the effect sets state, it can cause repeated fetching.

### Fix 1: move object creation inside the effect

```tsx
function ProductFeed({ categoryId }: { categoryId: string }) {
  const [products, setProducts] = React.useState<Product[]>([]);

  React.useEffect(() => {
    const options = { includeOutOfStock: false };

    fetchProducts(categoryId, options).then(setProducts);
  }, [categoryId]);

  return <ProductGrid products={products} />;
}
```

The effect depends on `categoryId`. The object is created inside the effect and no longer needs to be tracked as a render-time reference.

### Fix 2: memoize the object only when it must be shared

```tsx
function ProductFeed({ categoryId }: { categoryId: string }) {
  const [products, setProducts] = React.useState<Product[]>([]);
  const options = React.useMemo(
    () => ({ includeOutOfStock: false }),
    []
  );

  React.useEffect(() => {
    fetchProducts(categoryId, options).then(setProducts);
  }, [categoryId, options]);

  return <ProductGrid products={products} options={options} />;
}
```

Use this if `options` also needs stable identity as a prop. Otherwise moving the object into the effect is simpler.

## Real-World Use Cases

### Custom hook that loops on an inline options argument

A team ships `usePaginatedQuery` and every call site quietly refetches on every render, because callers pass an inline object and the hook depends on it.

```tsx
function usePaginatedQuery(endpoint: string, options: { pageSize: number; sort: string }) {
  React.useEffect(() => {
    fetchPage(endpoint, options).then(setData);
  }, [endpoint, options]); // options is a new object at every call site render
}

// Innocent-looking call site — refetches every render:
const { data } = usePaginatedQuery('/api/orders', { pageSize: 25, sort: 'date' });
```

`Object.is` compares the inline object by identity, so the dependency changes every render. Fix inside the hook: destructure to primitives and depend on those.

```tsx
const { pageSize, sort } = options;
React.useEffect(() => {
  fetchPage(endpoint, { pageSize, sort }).then(setData);
}, [endpoint, pageSize, sort]);
```

> [!tip]
> Design custom hook APIs around primitives (or destructure internally) so callers cannot accidentally create effect loops. Document which arguments are reactive.

### Inline callback prop that retriggers a fetch effect

A dashboard panel notifies its parent when data loads. The parent passes a fresh arrow function every render, and the child's effect depends on it — every parent render triggers a refetch.

```tsx
function ReportPanel({ reportId, onLoaded }: Props) {
  React.useEffect(() => {
    loadReport(reportId).then(report => onLoaded(report.rowCount));
  }, [reportId, onLoaded]); // onLoaded: new function identity each parent render
}
```

Functions are compared by reference like objects. Fix at the parent with `useCallback`, or in the child by syncing `onLoaded` into a ref so the effect depends only on `reportId`. See [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]].

### Chart re-initialized on every keystroke

A revenue page derives chart points with `.map` during render and passes them to an effect that builds a Chart.js instance. Typing in an unrelated search box rerenders the component, `points` gets a new identity, and the chart is destroyed and rebuilt — tooltips and animations reset mid-interaction.

```tsx
const points = orders.map(o => ({ x: o.date, y: o.totalCents })); // new array each render

React.useEffect(() => {
  const chart = new Chart(canvasRef.current!, { data: points });
  return () => chart.destroy();
}, [points]);
```

The array's contents are identical but its reference is not, and `Object.is` only sees the reference. Fix: `useMemo` the points on `[orders]`, or key the effect on `orders` and derive points inside it. See [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]].

## 6. Removing Dependencies Correctly

Do not remove dependencies by deleting them. Change the code so the dependency is no longer read.

### Before: reads `messages`

```tsx
React.useEffect(() => {
  socket.on('message', message => {
    setMessages([...messages, message]);
  });
}, [socket, messages]);
```

This resubscribes after every message because `messages` changes.

### After: functional update removes the dependency

```tsx
React.useEffect(() => {
  function onMessage(message: Message) {
    setMessages(prev => [...prev, message]);
  }

  socket.on('message', onMessage);
  return () => socket.off('message', onMessage);
}, [socket]);
```

The effect no longer reads `messages`, so `messages` is no longer a dependency.

## 7. Dependency Decision Table

| Situation | Dependency strategy |
| --- | --- |
| Effect uses a prop to subscribe | Include the prop |
| Effect updates state from previous state | Use functional updater to remove that state dependency |
| Effect creates an object only for setup | Create it inside the effect |
| Object is passed to memoized child | Use `useMemo` or pass primitives |
| Function is passed to memoized child | Use `useCallback` with real dependencies |
| Long-lived listener needs latest value | Sync a ref and read `ref.current` |
| Value is module-level constant | No dependency needed |
| Linter warns | Treat it as a design review, not noise |

## 8. Production Tradeoffs

- The simplest correct dependency list is usually best.
- Too few dependencies produce stale closures.
- Too many unstable dependencies produce loops and wasted work.
- `useMemo` and `useCallback` add cognitive overhead. Prefer moving objects/functions into effects when only the effect needs them.
- In custom hooks, expose a stable API where possible and document which arguments are reactive.
- During debugging, log dependency identity changes. `Object.is(prev, next)` is the mental model React uses.

## 9. Interview Answer

A dependency array declares the reactive values used by a hook callback or calculation. React compares each dependency to the previous one with `Object.is`. For an effect, if dependencies changed, React runs the old cleanup and then the new setup. Missing dependencies create stale closures. Unstable object or function dependencies can make effects run every render. The mature approach is not to suppress the linter; it is to restructure code: move non-reactive objects into the effect, use functional state updates, memoize only when identity matters, or use a ref when a stable callback intentionally needs the latest value.

## 10. Mistakes to Avoid

| Mistake | Better pattern |
| --- | --- |
| `[]` while reading props | Include props or move logic so they are not read. |
| Inline object in dependencies | Move object into effect, pass primitives, or memoize. |
| Function dependency causes loop | Move function into effect or wrap with `useCallback` if shared. |
| Suppressing `exhaustive-deps` | Explain and restructure. |
| Depending on whole objects when only one field matters | Depend on the field, such as `user.id`. |

> [!tip] Depend on values, not containers
> When only one field matters, depend on the field (`user.id`), not the whole object — objects get new identity every render and retrigger the effect. Suppressing `exhaustive-deps` hides exactly the bug the rule catches; restructure instead.

## 11. Practice

### Q1. How many times can this effect run?

```tsx
function Demo({ id }: { id: string }) {
  const options = { retry: 2 };

  React.useEffect(() => {
    load(id, options);
  }, [id, options]);
}
```

It can run after every render because `options` is a new object each time.

### Q2. Fix it without `useMemo`.

```tsx
React.useEffect(() => {
  const options = { retry: 2 };
  load(id, options);
}, [id]);
```

### Q3. Why does React use `Object.is` instead of deep equality?

It is fast, predictable, and works with immutable update patterns. Deep equality would be expensive, can hide mutation bugs, and becomes ambiguous with functions, class instances, DOM nodes, circular references, and large data structures.

### Q4. Is this valid?

```tsx
const submit = React.useCallback(() => {
  setForm(prev => ({ ...prev, submitted: true }));
}, []);
```

Yes if it reads no reactive values other than the stable setter. The updater receives the latest state.

## Related Notes

- [[14 - JavaScript in React and Next.js/02 - Closures in Hooks|Closures in Hooks]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[12 - Advanced Language Concepts/02 - Equality and Object.is|Equality and Object.is]]
- [[13 - Performance and Memory/06 - Memoization and Expensive Computations|Memoization and Expensive Computations]]
