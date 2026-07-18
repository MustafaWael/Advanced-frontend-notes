---
tags: [react, internals, context, performance]
module: "21 - React Internals and Patterns"
priority: must-know
status: not-started
aliases: [Context]
---

# Context: Mechanics and Performance

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: you can explain how context propagates, why every consumer re-renders when the value changes, and the value-identity trap.
- Production signal: you split contexts and stabilize values deliberately instead of dumping everything into one provider and memoizing blindly.
- Dependencies: [[21 - React Internals and Patterns/04 - State Batching and Updater Queues|State Batching]], [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]

## Source Anchors

- [react.dev - useContext](https://react.dev/reference/react/useContext)
- [react.dev - Passing Data Deeply with Context](https://react.dev/learn/passing-data-deeply-with-context)
- [react.dev - Scaling Up with Reducer and Context](https://react.dev/learn/scaling-up-with-reducer-and-context)
- [react.dev - createContext](https://react.dev/reference/react/createContext)

## 1. Concept

Context is a way to pass a value down the tree without prop-drilling. A provider holds a value; any descendant that calls `useContext(TheContext)` reads it and **subscribes** to it.

The mechanism to internalize: when a provider's `value` changes (by `Object.is` comparison), React re-renders **every consumer** of that context, regardless of how deep, and regardless of whether they care about the part that changed. Context has no selector — a consumer subscribes to the whole value.

```jsx
const ThemeContext = createContext(null);

function App() {
  const [theme, setTheme] = useState("dark");
  return (
    <ThemeContext value={{ theme, setTheme }}>  {/* React 19: <Context> is the provider */}
      <Page />
    </ThemeContext>
  );
}
```

## 2. Why It Matters

- Context is the default "global state" reach in React, and misused it becomes a performance footgun: one unrelated field changing re-renders half the app.
- The "new object every render" identity bug ([[14 - JavaScript in React and Next.js/05 - Referential Equality|referential equality]]) is *most* damaging through context because it fans out to all consumers at once.

## 3. The Two Performance Traps

**Trap 1 — unstable value identity.** `value={{ theme, setTheme }}` creates a new object every render of the provider's parent. Even if `theme` didn't change, the *object* is new, so `Object.is(prev, next)` is false → all consumers re-render on every parent render.

```jsx
// ❌ new object each render → every consumer re-renders every time App renders
<ThemeContext value={{ theme, setTheme }}>

// ✅ stabilize identity
const value = useMemo(() => ({ theme, setTheme }), [theme]);
<ThemeContext value={value}>
```

**Trap 2 — one context, many concerns.** Bundling `{ user, theme, cart, notifications }` into one provider means a cart update re-renders every component reading *theme*. Split by change frequency:

```jsx
// ✅ separate providers so a change in one doesn't re-render consumers of another
<AuthContext value={authValue}>
  <ThemeContext value={themeValue}>
    <CartContext value={cartValue}>{children}</CartContext>
  </ThemeContext>
</AuthContext>
```

A common refinement is **splitting state from dispatch**: put the frequently-changing state in one context and the stable `dispatch`/setters (which never change identity) in another, so components that only dispatch never re-render when the state changes.

> [!warning] `memo` does not stop context-driven re-renders
> `React.memo` compares props; it does nothing about context. A `memo`-wrapped component that calls `useContext` still re-renders whenever that context value changes — the subscription bypasses the props comparison entirely. To limit context re-renders you must split contexts or stabilize the value, not wrap consumers in memo.

## 4. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: an app-wide provider holds auth, theme, and a live-updating `notifications` array.

Buggy version:

```jsx
function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState("light");
  const [notifications, setNotifications] = useState([]);
  // notifications updates every few seconds from a socket
  return (
    <AppContext value={{ user, setUser, theme, setTheme, notifications }}>
      {children}
    </AppContext>
  );
}
```

Trace the cost: every incoming notification calls `setNotifications` → `AppProvider` re-renders → a brand-new context object → **every** consumer re-renders, including the theme toggle, the nav, the avatar, deeply memoized subtrees that only read `theme`. On a busy app this is continuous wasted rendering; profiler shows unrelated components flashing on every socket message.

Production-safe fix — split by concern and stabilize:

```jsx
function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState("light");
  const [notifications, setNotifications] = useState([]);

  const auth = useMemo(() => ({ user, setUser }), [user]);
  const themeVal = useMemo(() => ({ theme, setTheme }), [theme]);
  // notifications changes often → isolate it so only its consumers re-render
  return (
    <AuthContext value={auth}>
      <ThemeContext value={themeVal}>
        <NotificationsContext value={notifications}>{children}</NotificationsContext>
      </ThemeContext>
    </AuthContext>
  );
}
```

Now a notification re-renders only `NotificationsContext` consumers; the theme toggle and avatar are untouched.

Tradeoffs: more providers means more nesting and more `useMemo` bookkeeping — over-splitting a rarely-changing value is premature optimization that adds noise. The honest senior take: context is a *dependency-injection / low-frequency* tool (theme, current user, locale). For high-frequency or selector-heavy global state, context's "re-render all consumers" model is a poor fit — reach for an external store with selective subscriptions (`useSyncExternalStore`, Zustand, Redux — [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]) instead of contorting context. Choosing the right tool beats micro-optimizing the wrong one.

## Real-World Use Cases

### Dependency injection of stable services: the case where context is perfect

An app needs its API client, analytics tracker, and feature-flag client available everywhere, without imports of singletons (which kill testability). These objects are created once and never change identity — so the "all consumers re-render" cost is zero.

```jsx
const ServicesContext = createContext(null);

function ServicesProvider({ children }) {
  const [services] = useState(() => ({          // lazy init: created exactly once
    api: createApiClient(),
    analytics: createAnalytics(),
    flags: createFlagClient(),
  }));
  return <ServicesContext value={services}>{children}</ServicesContext>;
}

const useServices = () => useContext(ServicesContext);
// in a test: <ServicesContext value={mockServices}>...</ServicesContext>
```

Because the value's identity never changes, `Object.is` never reports a change and no consumer ever re-renders from it — context at its best: low-frequency (here: zero-frequency) injection, trivially swappable in tests.

### i18n: the recreated `t` function that re-renders every translated component

A locale provider exposes a translate function. Written naively, `t` is a new function identity on every provider render, so *every component that renders text* re-renders whenever anything above the provider updates.

```jsx
function LocaleProvider({ children }) {
  const [locale, setLocale] = useState("en");
  const t = (key) => translations[locale][key];       // ❌ new identity each render
  return <I18nContext value={{ locale, t, setLocale }}>{children}</I18nContext>;
  // ✅ const value = useMemo(() => ({ locale, setLocale,
  //      t: (key) => translations[locale][key] }), [locale]);
}
```

This is Trap 1 at app-wide blast radius: an i18n context typically has more consumers than any other, so an unstable value here shows up in the profiler as "the entire page renders on every keystroke in the header search." Memoize on `[locale]` — the one input `t` actually depends on ([[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]).

### Cart actions context: "Add to cart" buttons that never re-render

A store has an add-to-cart button on every product card — hundreds per page — but each button only *dispatches*; it never reads cart contents. Splitting state from actions means cart updates re-render the mini-cart badge, not the grid.

```jsx
const CartStateContext = createContext(null);
const CartActionsContext = createContext(null);

function CartProvider({ children }) {
  const [items, dispatch] = useReducer(cartReducer, []);
  const actions = useMemo(() => ({
    add: (sku) => dispatch({ type: "add", sku }),
    remove: (sku) => dispatch({ type: "remove", sku }),
  }), []);                                   // dispatch is stable → actions never change
  return (
    <CartActionsContext value={actions}>
      <CartStateContext value={items}>{children}</CartStateContext>
    </CartActionsContext>
  );
}

function AddButton({ sku }) {
  const { add } = useContext(CartActionsContext);  // subscribes to a never-changing value
  return <button onClick={() => add(sku)}>Add to cart</button>;
}
```

This is the state/dispatch split from section 3 in working form: `useReducer`'s `dispatch` is referentially stable, so the actions context value memoizes with empty deps and its consumers are permanently exempt from cart-driven re-renders.

> [!warning]
> If product cards also show "in cart ✓", they now read `CartStateContext` and re-render on every cart change again. At that point per-item subscription is what you actually need — an external store with selectors ([[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]], Zustand) beats further context surgery.

## 5. Interview Answer

Short answer:

> Context propagates a value to any descendant that calls `useContext`, which subscribes to the whole value. When the provider's value changes by `Object.is`, every consumer re-renders — there's no partial subscription. So the two failure modes are unstable value identity (a new object each render re-renders all consumers) and cramming unrelated concerns into one context (one change re-renders everyone).

Deeper answer:

> Fixes are stabilizing the value with `useMemo`, splitting contexts by change frequency, and separating state from dispatch so dispatch-only consumers don't re-render. `React.memo` doesn't help — context subscriptions bypass props comparison. And context is fundamentally a low-frequency injection mechanism; for high-frequency or selector-based state, an external store with `useSyncExternalStore` gives per-selector subscriptions that context can't, so the right move is often to change tools rather than optimize context.

## 6. Practice

1. <details><summary>A `React.memo`-wrapped `<Sidebar>` re-renders every second even though its props never change. It calls `useContext(AppContext)`. Explain.</summary>`React.memo` only skips re-renders caused by *prop* changes; it has no effect on context subscriptions. `Sidebar` subscribes to `AppContext`, so whenever that context's value changes (e.g., a per-second update bundled into it), `Sidebar` re-renders regardless of memo. Fix: move the frequently-changing data out of the context Sidebar reads, or split contexts so Sidebar only subscribes to stable data.</details>

2. <details><summary>Why does `<Ctx value={{ user }}>` re-render all consumers on every parent render even when `user` is unchanged?</summary>The object literal `{ user }` is a new reference each render; context compares values with `Object.is`, which sees a different object and notifies all consumers. The primitive `user` being equal doesn't matter — context compares the whole value's identity. Fix: `const value = useMemo(() => ({ user }), [user])`.</details>

3. <details><summary>Design a theme + auth + live-cart context setup to minimize re-renders. What goes where?</summary>Three separate providers (or at least separate the live-cart). Theme and auth change rarely → their own memoized contexts. Cart changes often → its own context so cart updates don't touch theme/auth consumers. Consider splitting cart *state* from cart *actions* (dispatch), putting actions in a stable context so "add to cart" buttons that only dispatch never re-render on cart changes. If cart needs fine-grained selectors (item count vs full list), an external store is the better tool than context.</details>

4. <details><summary>When is context the wrong tool entirely, and what's the alternative?</summary>When state changes frequently and consumers need only slices of it — context's all-consumers-re-render model wastes work, and it offers no selector API. Alternative: an external store subscribed via `useSyncExternalStore` (or Zustand/Redux/Jotai), which lets each component subscribe to a specific slice and re-render only when that slice changes. Context stays best for low-frequency dependency injection: theme, locale, current user, feature flags.</details>

## Related Notes

- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]
- [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[01 - Roadmap|Roadmap]]
