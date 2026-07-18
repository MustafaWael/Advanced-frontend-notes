---
tags: [react, state-management, architecture]
module: "28 - Frameworks and Application Architecture"
priority: must-know
status: not-started
aliases: [Local vs global state, Redux Zustand Jotai, State classification]
verified_on: 2026-07-17
version_scope: "React 19; Redux Toolkit 2.x, Zustand 5, Jotai 2"
---

# State Management Taxonomy

## Maturity Target

- Priority: #must-know
- Study time: 50 minutes
- Interview signal: Classify any piece of state — local, lifted, shared, global, server, URL — and defend a storage choice per class with a decision tree, including *why not* the alternatives.
- Production signal: Your apps don't have a god-store; state lives at the narrowest sufficient scope; adding a feature doesn't mean adding to a global blob.
- Dependencies: [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]], [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]

## Source Anchors

- [React - Sharing State Between Components](https://react.dev/learn/sharing-state-between-components)
- [React - Scaling Up with Reducer and Context](https://react.dev/learn/scaling-up-with-reducer-and-context)
- [Zustand - docs](https://zustand.docs.pmnd.rs/)

## 1. Concept

Simple version: "state management" is not a library choice — it's a *classification* problem. Ask two questions about every piece of state: **who reads it?** and **who writes it?** The answers place it in a class, and each class has a natural home.

The taxonomy:

- **Local** — one component reads/writes. Home: `useState`/`useReducer`. A form input's draft value, an open/closed flag. *Most state is local; keeping it local is the single best state decision.*
- **Lifted** — siblings need the same state → move it to the closest common ancestor, pass down props/callbacks. This is React's own first answer, not a workaround. Costs prop-drilling depth.
- **Shared (subtree)** — a whole feature subtree needs it (theme within a wizard, current step) → **Context**, ideally as `<Provider value={useMemo(...)}>` with split contexts for readers/writers ([[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics]]). Context is a *dependency-injection* mechanism, not a state manager — every consumer re-renders on value change.
- **Global (client)** — cross-cutting, app-lifetime: auth session, theme, cart, feature flags. Home: an external store — Zustand/Jotai/Redux — subscribed via `useSyncExternalStore` semantics ([[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]) so components re-render *only for the slices they select*.
- **Server state** — data whose source of truth is the backend. It's a *cache*, not state — different rules entirely ([[28 - Frameworks and Application Architecture/06 - Server State|Server State]]). Putting it in Redux is the classic architecture smell.
- **URL state** — filters, tabs, pagination, selected item. Home: the router/search params. Test: *should this survive refresh and be shareable as a link?* If yes, it's URL state — putting it in `useState` breaks back-button and deep links.

The store models differ meaningfully:

```ts
// Zustand — single store, selector-subscribed slices
const useCart = create<CartState>((set) => ({
  items: [],
  add: (i: Item) => set(s => ({ items: [...s.items, i] })),
}));
const count = useCart(s => s.items.length);   // re-renders ONLY when length changes

// Jotai — atoms: bottom-up, derived state graph (signals-flavored)
const itemsAtom = atom<Item[]>([]);
const countAtom = atom(get => get(itemsAtom).length);

// Redux Toolkit — event-log flavor: actions describe WHAT happened,
// reducers decide HOW state changes; devtools time-travel, middleware.
dispatch(cartItemAdded(item));
```

Decision tree, compressed: *Can it stay local? → local. Two siblings? → lift. Subtree concern? → context. App-wide client state? → small external store. From the server? → query cache. Belongs in the link? → URL.*

## 2. Why It Matters

- "How do you manage state?" is a guaranteed interview question, and "we use Redux/Zustand" is the weak answer — the classification-first answer is the strong one.
- Misclassification is *the* root cause of state architecture pain: server data in Redux (hand-rolled caching, staleness bugs), URL state in useState (broken back button), local state in a global store (spooky coupling, impossible-to-trace writes).
- Context-as-state-manager is the most common mid-level performance mistake — one fat context value re-rendering half the app.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

```tsx
// Buggy: the "one big context" pattern
const AppContext = createContext<{
  user: User; theme: Theme; cart: Item[]; notifications: Note[];
  setTheme: (t: Theme) => void; addToCart: (i: Item) => void; /* … */
}>(/* … */);

function App() {
  const [state, setState] = useState(initial);
  return (
    <AppContext.Provider value={{ ...state, ...makeSetters(setState) }}>
      {/* everything */}
    </AppContext.Provider>
  );
}
```

Trace: two compounding failures. (1) The value object is re-created every render → *every* consumer re-renders whenever *anything* changes: a notification arriving re-renders the theme toggle. (2) Unrelated domains share one write surface — no way to subscribe to a slice. Context has no selector mechanism; consumption is all-or-nothing.

```tsx
// Fix: classify, then home each class
const theme = useTheme();                  // shared/subtree → its own small context
const cartCount = useCart(s => s.items.length);  // global → Zustand w/ selector
const { data: notifications } = useQuery({ queryKey: ['notifications'], queryFn: fetchNotes }); // server → query cache
const [filter, setFilter] = useSearchParams();   // URL state → router
```

Tradeoffs: more homes to learn than one blob — the team must know the taxonomy. Zustand adds a (tiny) dependency and lives outside React's tree (SSR needs per-request stores). Split contexts add provider nesting. All cheaper than the god-context's re-render tax and coupling.

> [!warning] Footgun: putting derived state in a store (`totalPrice` stored alongside `items`) creates sync bugs — the M×N problem *inside* your store. Derive at read time (selectors, `useMemo`, derived atoms); store only source facts.

## 4. Interview Answer

Short answer:

> I classify state before choosing tools. Local state stays in useState — most state should. Siblings share via lifting to a common ancestor. Subtree concerns like theme use context, kept small and memoized because context has no selectors — every consumer re-renders. App-wide client state — session, cart — goes in a small external store like Zustand, where selector subscriptions limit re-renders. Server data is a cache, not state — React Query territory. And anything that should survive refresh or be shareable belongs in the URL.

Deeper answer:

> The library differences that matter: Redux is an event-log model — actions as facts, reducers as deciders — buying auditability, devtools time-travel, and middleware at the cost of ceremony; Zustand is a mutable-feeling store with selector subscriptions and near-zero boilerplate; Jotai builds a derived-atom graph, signals-flavored, great for fine-grained derived client state. All modern stores integrate through useSyncExternalStore for concurrent-rendering safety. The two smells I name: server data hand-cached in a client store, and derived values stored instead of computed — both reintroduce the sync problem frameworks exist to solve.

## 5. Practice

1. <details><summary>Classify: (a) dropdown open flag, (b) checkout form draft, (c) auth session, (d) product-list filters, (e) the product list itself.</summary>(a) Local — useState. (b) Local to the form (useReducer if complex); lift only if siblings need it. (c) Global client state — external store or auth context (rarely changes, so context is fine). (d) URL state — search params: shareable, refresh-proof, back-button-correct. (e) Server state — query cache with a key including the filters.</details>
2. <details><summary>Why does context "re-render everything" while Zustand doesn't, mechanically?</summary>Context propagation re-renders every consumer whenever the provider's value is referentially new — there is no built-in slicing. External stores subscribe components via useSyncExternalStore with a selector; on store change, React re-renders only components whose selected slice changed by equality check.</details>
3. <details><summary>Your PM asks why the back button "doesn't work" on the filtered products page. Diagnose from state classification.</summary>Filters live in useState, so navigation doesn't record them — the URL never changed. Reclassify as URL state: write filters to search params (router API), read them as the source of truth. Bonus: links become shareable and refresh-safe, and the query cache can key on them.</details>

## Related Notes

- [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context Mechanics and Performance]]
- [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]
- [[28 - Frameworks and Application Architecture/06 - Server State|Server State]]
- [[14 - JavaScript in React and Next.js/06 - Immutability in State Updates|Immutability in State Updates]]
- [[30 - Backend System Design/04 - Data Modeling and Databases|Data Modeling and Databases]] — client normalization mirrors DB normalization
