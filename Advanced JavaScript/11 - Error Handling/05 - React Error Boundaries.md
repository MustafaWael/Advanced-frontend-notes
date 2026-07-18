---
tags: [javascript, error-handling, react-error-boundaries, react]
module: "11 - Error Handling"
priority: important
status: not-started
---

# React Error Boundaries

## Maturity Target

- Priority: #important
- Study time: 110-150 minutes
- Interview signal: you can explain what error boundaries catch, what they do not catch, and how Next.js route error files relate to boundaries.
- Production signal: render failures are isolated with useful fallback UI, reset paths, and logging.
- Dependencies: [[11 - Error Handling/01 - try catch throw finally|try catch throw finally]], [[11 - Error Handling/04 - Promise Rejections|Promise Rejections]], [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]

## Source Anchors

- [React Component: catching rendering errors with an error boundary](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [React lazy](https://react.dev/reference/react/lazy)
- [Next.js Error Handling](https://nextjs.org/docs/app/getting-started/error-handling)
- [Next.js error.js file convention](https://nextjs.org/docs/app/api-reference/file-conventions/error)

## 1. Concept

A React error boundary catches errors thrown while rendering its descendant tree and renders fallback UI instead of letting the entire tree unmount.

In React core, an error boundary is a class component that defines one or both of:

- `static getDerivedStateFromError(error)`: update state so fallback UI renders;
- `componentDidCatch(error, info)`: log or report the error after React commits the fallback.

```tsx
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error("Render error", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return <p role="alert">Something went wrong.</p>;
    }

    return this.props.children;
  }
}
```

## 2. Why It Matters

Without boundaries, one render-time exception can take down a large part of the UI. With boundaries, you can isolate failures:

- a dashboard widget can fail while the rest of the dashboard stays usable;
- a product reviews panel can show "Reviews unavailable";
- route-level failures can show retry UI;
- component stack traces can reach monitoring tools;
- users get recovery options instead of a blank screen.

## 3. Accurate Mechanism

React catches errors during rendering, constructors, and lifecycle methods of the tree below the boundary. React then finds the nearest parent boundary, updates it to render fallback UI, and calls logging lifecycle methods.

Important limitations:

- boundaries do not catch errors in event handlers;
- boundaries do not automatically catch async promise rejections;
- boundaries do not catch errors thrown inside `setTimeout`;
- a boundary cannot catch its own render error;
- server rendering has framework-specific handling.

```tsx
function BadButton() {
  function handleClick() {
    throw new Error("click failed");
  }

  return <button onClick={handleClick}>Click</button>;
}
```

The error above is not caught by an error boundary because event handlers run after render. Use local `try/catch` or state-based error UI for event work.

## 4. Mental Model

Error boundaries protect React rendering. They are not global JavaScript `try/catch`.

Use them where a subtree can be replaced with fallback UI:

- route boundary;
- panel or widget boundary;
- risky lazy-loaded feature;
- third-party component boundary;
- non-critical recommendations, charts, maps, or comments.

Do not use them as a substitute for API error states, form validation, or mutation error handling.

## 5. Real Frontend Example: Granular Dashboard

```tsx
function Dashboard() {
  return (
    <main>
      <AccountSummary />

      <ErrorBoundary>
        <RevenueChart />
      </ErrorBoundary>

      <ErrorBoundary>
        <ActivityFeed />
      </ErrorBoundary>
    </main>
  );
}
```

Production reasoning:

- `AccountSummary` may be critical enough to bubble to a route-level error page;
- `RevenueChart` and `ActivityFeed` can fail independently;
- the user can still use the page when a non-critical widget fails.

Better fallback component:

```tsx
function WidgetErrorFallback({
  title,
  onRetry
}: {
  title: string;
  onRetry: () => void;
}) {
  return (
    <section role="alert" aria-live="polite">
      <h2>{title}</h2>
      <p>This section could not load.</p>
      <button onClick={onRetry}>Retry</button>
    </section>
  );
}
```

Fallback UI should be useful, small, and safe. Do not expose raw stack traces to users.

## 6. Real Frontend Bug: Expecting Boundary To Catch Fetch Failure

> [!warning] Error boundaries don't catch async or event-handler errors
> They catch errors thrown during render, lifecycle, and constructors — not rejections in `fetch`/`.then`, `setTimeout`, or event handlers. Handle those with try/catch or `.catch` and surface them into state (or throw during render) so a boundary can see them.

Problem:

```tsx
function UserCard({ id }: { id: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    fetch(`/api/users/${id}`)
      .then((response) => response.json())
      .then(setUser);
  }, [id]);

  return <p>{user!.name}</p>;
}
```

Bugs:

- fetch rejection is not caught by the boundary;
- HTTP errors are not checked;
- `user!.name` can throw during render while loading;
- render crash and async failure are mixed together.

Fix:

```tsx
function UserCard({ id }: { id: string }) {
  const [state, setState] = useState<
    | { status: "loading" }
    | { status: "success"; user: User }
    | { status: "error"; message: string }
  >({ status: "loading" });

  useEffect(() => {
    let ignore = false;

    async function load() {
      try {
        const response = await fetch(`/api/users/${id}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const user = (await response.json()) as User;

        if (!ignore) setState({ status: "success", user });
      } catch (error) {
        console.error("User load failed", error);
        if (!ignore) {
          setState({ status: "error", message: "Could not load user." });
        }
      }
    }

    void load();

    return () => {
      ignore = true;
    };
  }, [id]);

  if (state.status === "loading") return <Spinner />;
  if (state.status === "error") return <p role="alert">{state.message}</p>;
  return <p>{state.user.name}</p>;
}
```

The error boundary remains useful for unexpected render bugs, while async failures become explicit component state.

## 7. Next.js App Router Error Files

In the App Router, an `error.tsx` file defines fallback UI for a route segment. It must be a Client Component.

```tsx
// app/dashboard/error.tsx
"use client";

import { useEffect } from "react";

export default function DashboardError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Dashboard route failed", error);
  }, [error]);

  return (
    <section role="alert">
      <h2>Dashboard could not load.</h2>
      <button onClick={reset}>Try again</button>
    </section>
  );
}
```

Production notes:

- `reset` retries rendering the route segment;
- `digest` can identify server-side errors without exposing sensitive details;
- do not render raw server error details to users;
- keep route-level fallback copy useful and calm.

See [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]].

## 8. Lazy Loading Errors

Dynamic imports used by `React.lazy` can fail due to network problems, deployment mismatch, blocked chunks, or stale caches. Put lazy-loaded subtrees inside `Suspense` and an error boundary.

```tsx
const SettingsPanel = lazy(() => import("./SettingsPanel"));

function SettingsRoute() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<p>Loading settings...</p>}>
        <SettingsPanel />
      </Suspense>
    </ErrorBoundary>
  );
}
```

`Suspense` handles pending loading. The error boundary handles render or chunk-load failure after the lazy promise rejects.

See [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]].

## 9. Reset Strategy

Users need a way out of fallback UI.

Common reset triggers:

- user clicks "Try again";
- route changes;
- query key changes;
- component key changes;
- a parent clears failed state.

```tsx
function ProductBoundary({ productId, children }: PropsWithChildren<{ productId: string }>) {
  return (
    <ErrorBoundary key={productId}>
      {children}
    </ErrorBoundary>
  );
}
```

Changing `key` creates a fresh boundary instance for a new product.

## 10. Production Tradeoffs

| Boundary placement | Benefit | Risk |
| --- | --- | --- |
| Root-level boundary | catches last-resort crashes | one widget can replace the whole app |
| Route-level boundary | clear page fallback | may hide which section failed |
| Widget-level boundary | isolates non-critical UI | too many fallbacks can feel fragmented |
| Third-party boundary | contains risky packages | can hide repeated vendor bugs if not logged |
| Lazy boundary | handles chunk failures | must coordinate with `Suspense` |

## 11. Interview Answer

**Short version:** An error boundary is a React class component that catches render-time errors in its child tree and shows fallback UI. It uses `getDerivedStateFromError` for fallback state and `componentDidCatch` for logging.

**Strong version:** Error boundaries catch errors that occur while React is rendering descendants, constructing class components, or running lifecycle methods. They do not catch event handler errors, async promise rejections, timers, or errors inside the boundary itself. In production I place boundaries at route and feature boundaries, log in `componentDidCatch`, show safe fallback UI, and provide reset behavior. In Next.js App Router, `error.tsx` provides route-segment error UI and must be a Client Component.

## 12. Common Mistakes

- Expecting boundaries to catch `fetch` failures in `useEffect`.
- Throwing inside an event handler and expecting a boundary fallback.
- Having only one root boundary, so a small widget crash replaces the whole app.
- Showing raw `error.message` from server failures to users.
- Logging only to the console and not to production monitoring.
- Forgetting reset behavior, trapping users in fallback UI.
- Confusing `Suspense` loading fallback with error fallback.
- Forgetting `"use client"` in a Next.js `error.tsx` file.

## 13. Practice

1. A child throws during render inside nested boundaries. Which fallback appears?
2. Why does an error thrown in `onClick` bypass an error boundary?
3. Where would you put boundaries on a dashboard with five independent widgets?
4. What does `componentDidCatch` provide that `getDerivedStateFromError` should not do?
5. Explain how `Suspense` and an error boundary cooperate around `React.lazy`.

## Related Notes

- [[11 - Error Handling/03 - Async Error Handling|Async Error Handling]]
- [[11 - Error Handling/04 - Promise Rejections|Promise Rejections]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[10 - Modules/04 - Static and Dynamic Imports|Static and Dynamic Imports]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense and Concurrent Features]]
- [[01 - Roadmap|Roadmap]]
