---
tags: [javascript, react, nextjs, hydration-related-javascript-issues]
module: "14 - JavaScript in React and Next.js"
priority: must-know
status: not-started
aliases: [Hydration]
---

# Hydration Related JavaScript Issues

## Maturity Target

- Priority: #must-know
- Study time: 90-120 minutes
- Interview signal: can explain hydration mismatches as different server/client render output.
- Production signal: can fix mismatches without hiding real bugs behind `suppressHydrationWarning`.
- Fast track: sections 3, 5, 6, 8, and practice Q1-Q5.

## Source Anchors

- [Next.js docs: Hydration error](https://nextjs.org/docs/messages/react-hydration-error)
- [Next.js docs: Server and Client Components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [React docs: hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot)
- [React docs: useEffect](https://react.dev/reference/react/useEffect)
- [React docs: State as a Snapshot](https://react.dev/learn/state-as-a-snapshot)

## 1. Concept

Hydration is React attaching interactivity to server-rendered HTML in the browser. A hydration mismatch happens when the server-rendered HTML does not match what the client render produces for the initial render.

The core rule: server output and first client output must match.

After hydration completes, React can update the UI normally. The danger is making the first client render depend on browser-only or nondeterministic values that the server did not have.

## 2. Why It Matters

Hydration mismatches are not cosmetic warnings. They can cause:

- visible content flashes
- incorrect event attachment in broken trees
- client-side fallback rendering for a subtree
- lost SSR performance benefits
- confusing bugs that appear only in production builds, time zones, locales, or specific browsers

They are common in Next.js because App Router pages often combine server rendering, Client Components, cookies, local storage, user agent differences, streaming, and dynamic values.

## 3. Official Mechanism

On the first load:

1. Next.js sends HTML to the browser.
2. The user can see a non-interactive preview quickly.
3. React runs the client component tree in the browser.
4. React expects the initial client output to match the existing HTML.
5. React attaches event handlers and makes Client Components interactive.

If the initial client render returns different text, attributes, or structure, React reports a hydration mismatch and must recover.

Common causes:

- `Date.now()` or `new Date()` during render
- `Math.random()` during render
- `window`, `document`, `navigator`, `localStorage`, or media query reads during render
- different server and browser locale/time zone formatting
- invalid HTML nesting
- browser extensions changing the DOM before hydration
- CDN or middleware rewriting HTML
- CSS-in-JS setup mismatch

## 4. Mental Model

Hydration is not "React starts from scratch." It is "React takes over existing HTML."

So this is dangerous:

```tsx
function Clock() {
  return <time>{new Date().toLocaleTimeString()}</time>;
}
```

The server renders one time. The browser renders a later time. The text can differ before React attaches event handlers.

The safe pattern is deterministic initial render, then browser-only update after mount.

## 5. Real Frontend Example

### Problem: theme from localStorage during render

```tsx
'use client';

function ThemeButton() {
  const savedTheme =
    typeof window !== 'undefined'
      ? localStorage.getItem('theme') ?? 'light'
      : 'light';

  const [theme, setTheme] = React.useState(savedTheme);

  return <button data-theme={theme}>Theme: {theme}</button>;
}
```

### Bug

> [!warning] Browser-only state during the first render breaks hydration
> The server renders `light`. The browser reads `dark` from `localStorage` during the first client render, so the first client output disagrees with the server HTML. The fix is a deterministic first render, then update after mount in an effect.

### Fix: deterministic initial render, browser update after mount

```tsx
'use client';

function ThemeButton() {
  const [theme, setTheme] = React.useState<'light' | 'dark'>('light');

  React.useEffect(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') {
      setTheme(saved);
    }
  }, []);

  function toggleTheme() {
    setTheme(prev => {
      const next = prev === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', next);
      return next;
    });
  }

  return (
    <button data-theme={theme} onClick={toggleTheme}>
      Theme: {theme}
    </button>
  );
}
```

Server render: `light`.

First client render: `light`.

After mount: effect reads local storage and updates to `dark` if needed.

## Real-World Use Cases

### Generated form ids: `crypto.randomUUID` vs `useId`

A form library generates ids to pair labels with inputs. A random id is generated once on the server and again on the client — two different values, guaranteed mismatch on every field.

```tsx
// BUG: server and client each generate their own id
const id = crypto.randomUUID();

// FIX: deterministic across server and client
const id = React.useId();

return (
  <>
    <label htmlFor={id}>Email</label>
    <input id={id} type="email" />
  </>
);
```

`useId` derives the id from the component's position in the tree, so both runtimes compute the same string — it exists precisely to make generated ids hydration-safe.

### Prices formatted by two different ICU databases

A storefront formats prices with the runtime's default locale. The Node server defaults to `en-US`, the shopper's browser is `de-DE` — the server sends `€1,234.56`, the first client render produces `1.234,56 €`, and the subtree mismatches.

```tsx
// BUG: `undefined` locale means "whatever this runtime defaults to"
<span>{new Intl.NumberFormat(undefined, { style: 'currency', currency: 'EUR' }).format(price)}</span>

// FIX: one explicit locale, decided on the server (e.g. from the Accept-Language header
// or a locale cookie) and passed down so both renders agree
<span>{new Intl.NumberFormat(locale, { style: 'currency', currency: 'EUR' }).format(price)}</span>
```

Locale-sensitive formatting is nondeterministic *across runtimes* even though it is pure within one — the initial render contract requires both sides to use the same inputs. See [[12 - Advanced Language Concepts/16 - Intl|Intl]].

### Production-only errors from browser extensions

Error monitoring shows hydration failures from a small slice of users that no one can reproduce. The cause is not your code: extensions like Grammarly or password managers inject attributes and elements into the DOM before React hydrates.

```tsx
// app/layout.tsx — extensions commonly add attributes to <body> before hydration
<body suppressHydrationWarning>{children}</body>
```

React compares the client render against the *current* DOM, not the HTML you sent — anything that edits the document between response and hydration looks like your mismatch. Diagnose by checking the reported diff for foreign `data-*` attributes and reproducing with extensions disabled.

> [!warning]
> `suppressHydrationWarning` on `<body>` only covers attribute differences on that one element and is not recursive. If an extension injects child elements, filter those known errors in your monitoring instead of suppressing real signals.

## 6. Better Server-Aware Fixes

For user preferences like theme, locale, currency, or A/B test bucket, a cookie can let the server render the correct initial output.

```tsx
// app/layout.tsx
import { cookies } from 'next/headers';

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const theme = cookieStore.get('theme')?.value === 'dark' ? 'dark' : 'light';

  return (
    <html data-theme={theme}>
      <body>{children}</body>
    </html>
  );
}
```

This avoids both mismatch and post-hydration flash because the server knows the same initial value.

Use browser-only effects when the server genuinely cannot know the value, such as screen width, online status, or APIs tied to the current browser tab.

## 7. Common Fix Patterns

### Mount guard

```tsx
function useMounted() {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  return mounted;
}

function ScreenWidth() {
  const mounted = useMounted();

  if (!mounted) {
    return <span>Width: unknown</span>;
  }

  return <span>Width: {window.innerWidth}px</span>;
}
```

The server and first client render both show `Width: unknown`.

### Effect-based browser read

```tsx
function ScreenWidth() {
  const [width, setWidth] = React.useState<number | null>(null);

  React.useEffect(() => {
    function update() {
      setWidth(window.innerWidth);
    }

    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  return <span>Width: {width === null ? 'unknown' : `${width}px`}</span>;
}
```

This also includes cleanup for the listener.

### Dynamic import with SSR disabled

Use this for components that cannot render on the server at all, such as some map, chart, editor, or browser-only SDK components.

```tsx
import dynamic from 'next/dynamic';

const MapView = dynamic(() => import('./MapView'), {
  ssr: false,
  loading: () => <div>Loading map...</div>,
});
```

This trades SSR output for safety with browser-only code.

### `suppressHydrationWarning`

```tsx
<time dateTime={createdAt} suppressHydrationWarning>
  {formatClientTime(createdAt)}
</time>
```

Use it sparingly for isolated text where a mismatch is expected and harmless. It does not fix the mismatch; it suppresses the warning.

## 8. Debugging Checklist

- Does render call `Date`, `Math.random`, `crypto.randomUUID`, or locale formatting?
- Does render read `window`, `document`, `navigator`, `localStorage`, or `matchMedia`?
- Is HTML nesting valid, such as no `<div>` inside `<p>`?
- Does the server have different data than the browser?
- Is a Client Component using a value that should come from cookies or headers?
- Did middleware, CDN, or browser extension alter the HTML?
- Is a third-party component browser-only?
- Does the first client render match the server output before effects run?

## 9. Production Tradeoffs

- Mount guards prevent mismatches but can create a "loading" flash.
- Cookie/server-driven initial values avoid flash but require server persistence and privacy decisions.
- `dynamic(..., { ssr: false })` avoids SSR crashes but loses server-rendered content for that component.
- `suppressHydrationWarning` is an escape hatch, not a general fix.
- Rendering nondeterministic values is okay after hydration, not during the initial server/client render contract.

## 10. Interview Answer

Hydration is React attaching event handlers and stateful behavior to HTML that was rendered on the server. A hydration mismatch means the client produced different output on its first render than the HTML the server sent. The most common causes are nondeterministic or browser-only reads during render, like `Date.now`, `Math.random`, `window`, or `localStorage`. The fix is to make the initial render deterministic: render the same fallback on the server and first client render, then read browser-only values in `useEffect`; or move user-specific values into cookies so the server can render the correct initial HTML. I would use `suppressHydrationWarning` only for narrow, expected text differences.

## 11. Mistakes to Avoid

| Mistake | Better approach |
| --- | --- |
| Reading localStorage in initial state for SSR UI | Use default state, then update in effect, or use cookies server-side |
| `typeof window !== 'undefined'` branch in JSX | It still creates different server/client output |
| `Math.random()` in render | Generate after mount or pass deterministic data from server |
| Using `suppressHydrationWarning` everywhere | Fix the source of mismatch |
| Ignoring invalid HTML nesting | Browser parser can rewrite the DOM before React hydrates |

## 12. Practice

### Q1. Why can this mismatch?

```tsx
function Greeting() {
  return <h1>{Math.random() > 0.5 ? 'Hello' : 'Welcome'}</h1>;
}
```

The server and browser can choose different random values during render.

### Q2. Fix a screen width component.

```tsx
function ScreenWidth() {
  const [width, setWidth] = React.useState<number | null>(null);

  React.useEffect(() => {
    setWidth(window.innerWidth);
  }, []);

  return <p>{width === null ? 'Width unknown' : `Width ${width}`}</p>;
}
```

The server and first client render both output `Width unknown`.

### Q3. What is wrong with this JSX?

```tsx
return (
  <p>
    Intro
    <div>Details</div>
  </p>
);
```

Invalid nesting. Browsers can repair the DOM differently than React expects, causing hydration errors. Use valid structure.

### Q4. When is `dynamic(..., { ssr: false })` appropriate?

When a component or library cannot execute during server rendering because it touches browser-only APIs at module load or render time, such as some map or rich text editor libraries.

### Q5. What is the best fix for theme flash?

Store the theme in a cookie, read it on the server, render the correct initial HTML, and keep client state in sync when the user toggles it.

## Related Notes

- [[14 - JavaScript in React and Next.js/09 - Server vs Client JavaScript in Next.js|Server vs Client JavaScript in Next.js]]
- [[14 - JavaScript in React and Next.js/01 - JavaScript Fundamentals in React|JavaScript Fundamentals in React]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in Effects]]
- [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering and UI Responsiveness]]
- [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]
- [[22 - Next.js Deep Dive/07 - Metadata SEO and the head|Metadata, SEO and the head]]
- [[12 - Advanced Language Concepts/16 - Intl|Intl]]
- [[17 - Practical Frontend Scenarios/06 - Cleaning Event Listeners|Cleaning Event Listeners]]
- [[01 - Roadmap|Roadmap]]
