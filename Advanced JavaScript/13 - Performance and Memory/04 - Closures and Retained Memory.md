---
tags: [javascript, performance, memory, closures-and-retained-memory]
module: "13 - Performance and Memory"
priority: deep-dive
status: not-started
---

# Closures and Retained Memory

## Maturity Target

- Priority: #deep-dive
- Study time: 90-130 minutes
- Interview signal: you can explain closure reachability, stale closures, retained payloads, and cleanup in callback registries.
- Production signal: callbacks do not keep large objects or dead components alive longer than intended.
- Dependencies: [[03 - Scope and Variables/05 - Closures|Closures]], [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]], [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]

## Source Anchors

- [MDN Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [MDN Memory management](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Memory_management)
- [React useEffect](https://react.dev/reference/react/useEffect)
- [Chrome DevTools Memory Problems](https://developer.chrome.com/docs/devtools/memory-problems)

## 1. Concept

A closure lets a function remember variables from its lexical environment.

That is useful for state and callbacks, but it also means the function can retain objects reachable from that environment.

```js
function createCounter() {
  let count = 0;

  return function increment() {
    count += 1;
    return count;
  };
}

const increment = createCounter();
console.log(increment()); // 1
```

The returned function keeps `count` alive.

## 2. Why It Matters

Closures are everywhere in frontend code:

- event handlers;
- effects;
- promise callbacks;
- debounced functions;
- memoized callbacks;
- subscriptions;
- store listeners;
- analytics handlers.

A tiny callback can keep a large object graph alive if the callback is stored somewhere long-lived.

## 3. Accurate Mechanism

A function object has access to the lexical environment where it was created. If a long-lived object references that function, the function's captured environment can remain reachable too.

```ts
const callbacks = new Set<() => void>();

function register(callback: () => void) {
  callbacks.add(callback);
  return () => callbacks.delete(callback);
}
```

If a registered callback closes over a large payload and is never unregistered, the payload can remain alive.

## 4. Mental Model

Closures retain what they can reach, not just what they visibly use after bundling and engine optimizations.

A good production habit is to close over stable, small identifiers instead of large mutable objects when possible.

## 5. Real Frontend Bug: Global Callback Registry

Problem:

```tsx
function ProductInspector({ product }: { product: Product }) {
  useEffect(() => {
    const unsubscribe = debugPanel.register(() => {
      console.log(product);
    });

    return unsubscribe;
  }, [product]);

  return <ProductView product={product} />;
}
```

This is mostly fine if cleanup always runs. The leak appears when cleanup is missing or the registry outlives the component:

```tsx
useEffect(() => {
  debugPanel.register(() => {
    console.log(product);
  });
}, [product]);
```

Bug:

- every product change registers a new callback;
- each callback closes over a full product payload;
- the global registry keeps old products reachable.

Fix:

```tsx
function ProductInspector({ product }: { product: Product }) {
  useEffect(() => {
    const productId = product.id;

    const unsubscribe = debugPanel.register(() => {
      // Close over the small id, then read current data from the owner.
      console.log(productStore.get(productId));
    });

    return unsubscribe;
  }, [product.id]);

  return <ProductView product={product} />;
}
```

Why it works:

- the registry gets cleaned up;
- the closure captures a small stable value;
- the large product object is not retained only for debugging.

## 6. Debounce and Retained State

Problem:

```tsx
function SearchPage({ results }: { results: Result[] }) {
  const debouncedLog = useMemo(
    () =>
      debounce(() => {
        console.log(results);
      }, 500),
    [results]
  );

  return <input onChange={debouncedLog} />;
}
```

Bug:

- each `results` change creates a new debounced function;
- old scheduled callbacks can retain old result arrays until they run or are canceled;
- large result sets linger longer than expected.

Fix:

```tsx
function SearchPage() {
  const latestCount = useRef(0);

  const debouncedLog = useMemo(
    () =>
      debounce(() => {
        console.log(latestCount.current);
      }, 500),
    []
  );

  useEffect(() => {
    return () => {
      debouncedLog.cancel();
    };
  }, [debouncedLog]);

  function handleResults(results: Result[]) {
    latestCount.current = results.length;
  }

  return <SearchBox onResults={handleResults} onChange={debouncedLog} />;
}
```

> [!tip] Tradeoff
> refs must be used carefully because they bypass React render updates. Here they avoid retaining large arrays for a logging callback.

## 7. Stale Closure vs Memory Closure

Stale closure bug: callback sees an old value.

Memory retention bug: callback keeps an old value alive.

They often share the same root cause: a callback outlives the render that created it.

```tsx
useEffect(() => {
  const id = setInterval(() => {
    console.log(count);
  }, 1000);

  return () => clearInterval(id);
}, [count]);
```

This updates the interval when `count` changes, but repeated setup may be unnecessary. A ref can keep the latest primitive value without recreating the interval:

```tsx
const latestCount = useRef(count);

useEffect(() => {
  latestCount.current = count;
}, [count]);

useEffect(() => {
  const id = setInterval(() => {
    console.log(latestCount.current);
  }, 1000);

  return () => clearInterval(id);
}, []);
```

## 8. Production Tradeoffs

| Pattern | Benefit | Risk |
| --- | --- | --- |
| Close over object | convenient access | can retain too much |
| Close over id | smaller retention | requires lookup owner |
| Store callback globally | flexible extension point | cleanup becomes critical |
| Use ref for latest value | avoids recreating callbacks | can hide data flow |
| Memoized callback | stable identity | can retain dependencies |

## 9. Interview Answer

**Short version:** A closure can keep variables from its lexical environment alive. If a long-lived callback closes over a large object, that object may stay reachable even after the UI no longer needs it.

**Strong version:** Functions retain access to their lexical environment. When those functions are stored by event targets, timers, registries, promises, or global stores, the captured environment can remain reachable. This is useful for state but dangerous for memory when callbacks capture large responses, DOM nodes, or component data and are not cleaned up. I reduce retention by unregistering callbacks, canceling debounced work, closing over small identifiers, and using refs or stores deliberately when a long-lived callback needs the latest value.

## 10. Common Mistakes

- Thinking closures only cause stale values, not memory retention.
- Registering callbacks without unsubscribe cleanup.
- Closing over full API responses when only an ID is needed.
- Memoizing a callback that captures large dependencies.
- Forgetting to cancel debounced or throttled callbacks on unmount.
- Keeping old DOM nodes through event handler closures.

## 11. Practice

1. Write a callback registry leak and then fix it with unsubscribe.
2. Refactor a closure to capture an ID instead of a full object.
3. Explain how a debounced function can retain old state.
4. Compare stale closure and retained-memory closure bugs.
5. Use DevTools retaining paths to identify a closure-held object.

## Related Notes

- [[03 - Scope and Variables/05 - Closures|Closures]]
- [[03 - Scope and Variables/06 - Closure Bugs|Closure Bugs]]
- [[13 - Performance and Memory/02 - Garbage Collection and Reachability|Garbage Collection and Reachability]]
- [[13 - Performance and Memory/03 - Memory Leaks|Memory Leaks]]
- [[14 - JavaScript in React and Next.js/03 - Stale Closures|Stale Closures]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[01 - Roadmap|Roadmap]]
