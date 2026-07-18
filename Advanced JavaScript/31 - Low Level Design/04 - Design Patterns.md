---
tags: [low-level-design, design-patterns, interview]
module: "31 - Low Level Design"
priority: must-know
status: not-started
aliases: [Factory, Strategy, Observer, Builder, State pattern]
---

# Design Patterns

## Maturity Target

- Priority: #must-know
- Study time: 40 minutes
- Interview signal: Implement Factory, Strategy, Observer, Builder, and State in TS, name each one's trigger, and point to where it already lives in frontend code.
- Production signal: You recognize patterns you already use by name and don't force them where they don't fit.
- Dependencies: [[31 - Low Level Design/02 - Design Principles|Design Principles]], [[31 - Low Level Design/03 - OOP Concepts|OOP Concepts]]

## Source Anchors

- [HelloInterview — Design Patterns](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/patterns)
- [patterns.dev](https://www.patterns.dev/)

## 1. Concept

Patterns are **names for structures good principles already produce** — not things to bolt on. The golden rule: use one only when the problem calls for it; forcing a pattern is the most common over-engineering smell. Interviews test ~5, not the GoF 23 (half of which modern languages made obsolete). US rounds grade design quality over pattern-naming; some regions ask patterns directly.

The five that matter, in TS:

- **Strategy** — swap an algorithm behind an interface (the composition of [[31 - Low Level Design/03 - OOP Concepts|OOP Concepts]]).
  ```ts
  interface SortStrategy { sort(xs: number[]): number[]; }
  class QuickSort implements SortStrategy { sort(xs: number[]) { /* ... */ return xs; } }
  class Sorter { constructor(private s: SortStrategy) {} run(xs: number[]) { return this.s.sort(xs); } }
  ```
- **Observer** — subscribers react to a subject's state changes. The entire reactive model.
  ```ts
  class Subject<T> {
    private subs = new Set<(v: T) => void>();
    subscribe(fn: (v: T) => void) { this.subs.add(fn); return () => this.subs.delete(fn); }
    next(v: T) { this.subs.forEach(fn => fn(v)); }
  }
  ```
- **Factory** — create the right object without the caller choosing the concrete class. Trigger: "support multiple types of X." (`makeChannel` below is a *simple factory function* — the everyday case. Distinguish it from **Factory Method**, where a subclass overrides a creation method to decide the type, and **Abstract Factory**, which creates whole *families* of related objects behind one interface — interviewers often probe which one you mean.)
  ```ts
  function makeChannel(type: "email" | "sms"): Channel {
    return type === "email" ? new EmailChannel() : new SmsChannel();
  }
  ```
- **Builder** — assemble a complex object step by step (fluent), avoiding telescoping constructors. Each method mutates internal draft state and returns `this` for chaining; `build()` produces the final object.
  ```ts
  interface Query { table: string; conds: string[]; limit?: number; }
  class QueryBuilder {
    private q: Query = { table: "", conds: [] };
    from(t: string) { this.q.table = t; return this; }
    where(col: string, op: string, val: unknown) { this.q.conds.push(`${col} ${op} ${JSON.stringify(val)}`); return this; }
    limit(n: number) { this.q.limit = n; return this; }
    build(): Query { return { ...this.q, conds: [...this.q.conds] }; }
  }
  new QueryBuilder().from("users").where("age", ">", 18).limit(10).build();
  ```
- **State** — behavior varies by an internal mode; each state is an object owning its own transitions. In the **GoF State pattern** the context delegates to a state object, and each state returns the next state — behavior lives *on* the states, not in a `switch`:
  ```ts
  interface DoorState { open(): DoorState; close(): DoorState; }
  const Closed: DoorState = { open: () => Opened, close: () => Closed };
  const Opened: DoorState = { open: () => Opened, close: () => Closed };
  class Door {
    private s: DoorState = Closed;
    open()  { this.s = this.s.open();  return this; }
    close() { this.s = this.s.close(); return this; }
  }
  ```
  On the **frontend** you usually want the lighter cousin — a *discriminated-union state machine* (below): a single `state` value the UI renders by `tag`, rather than polymorphic state objects. Same goal (illegal states unrepresentable), less ceremony; reach for full GoF State only when each state has substantial distinct *behavior*, not just distinct data.

> [!tip] Frontend mirror — you already ship all five: **Strategy** = pluggable `sort`/`validate`/`renderItem` props; **Observer** = subscriptions and `useSyncExternalStore` ([[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]]) — note the close cousin **Pub/Sub**: Observer has subscribers hold a direct reference to the subject, whereas a topic-based event emitter/broker decouples them through a channel, so "event emitter" is usually pub/sub, not textbook Observer; **Factory** = component/hook factories and `createX` helpers; **Builder** = fluent query/config APIs; **State** = an explicit machine (XState) for a complex widget instead of tangled booleans.

> [!warning] Singleton is the pattern to be wary of: a single global instance is convenient but is effectively global mutable state — it hides dependencies (breaking DIP) and makes testing hard. In JS a module is already a singleton; reach for injection before a hand-rolled Singleton.

## 2. Why It Matters

Naming a pattern compresses communication ("make it a Strategy") and, more importantly, recognizing that your reactive store *is* Observer or your `renderItem` prop *is* Strategy means you already have the instinct — the interview just wants the vocabulary and the judgment not to over-apply it.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a checkout component has grown a tangle of booleans — `isLoading`, `isError`, `isSuccess`, `isPaymentPending` — and renders wrong combinations (a success spinner, an error mid-success).

Trace: **impossible states are representable** because mode is spread across independent booleans instead of one State. This is the frontend version of missing the State pattern — behavior varies by mode, but the mode isn't modeled as a single value.

```ts
// Fix: a discriminated-union state machine (the frontend cousin of GoF State) —
// one mode value, legal transitions only
interface Receipt { id: string; cents: number; }
type CheckoutState =
  | { tag: "idle" } | { tag: "submitting" }
  | { tag: "success"; receipt: Receipt } | { tag: "error"; message: string };
// UI renders per state.tag; no impossible combinations exist.
// (Full GoF State — one object per mode owning its transitions — would be
//  overkill here: the modes differ in *data*, not in rich per-state behavior.)
```

Tradeoff: a state machine is more upfront structure than a couple of booleans — overkill for a two-state toggle (YAGNI). It pays off precisely when transitions are non-trivial, which is when the boolean soup was going to bite anyway.

## 4. Interview Answer

Short answer:

> The five patterns worth knowing are Strategy, Observer, Factory, Builder, and State — but I use one only when the problem calls for it, since forcing a pattern is the classic over-engineering smell. Most of them I already use on the frontend: Strategy as pluggable function props, Observer as reactive subscriptions and useSyncExternalStore, Factory as create-helpers, State as an explicit machine replacing boolean soup.

Deeper answer:

> Patterns are crystallized principles — Strategy is composition-over-inheritance plus dependency inversion, Observer is how you decouple a source of truth from its consumers, State makes illegal transitions unrepresentable. The judgment is knowing when *not* to: a Singleton is usually just global mutable state that hides dependencies and hurts testing, and a state machine for a two-state toggle is YAGNI. So I name the pattern to justify structure only when the complexity is real — otherwise the simplest code that works wins.

## 5. Practice

1. <details><summary>Which pattern is a React reactive store (or useSyncExternalStore) an instance of, and why?</summary>Observer — the store is the subject holding state; components subscribe and are notified on change, decoupled from who updates it. `useSyncExternalStore` is literally the subscribe/getSnapshot Observer contract wired into React's render.</details>
2. <details><summary>Why is Singleton the pattern to distrust?</summary>It's a single global instance — effectively global mutable state. It hides dependencies (callers reach for the global instead of receiving it, breaking DIP), couples code to that instance, and makes tests share state. In JS a module is already a singleton, so prefer injecting a shared instance over enforcing one.</details>
3. <details><summary>You have `isLoading/isError/isSuccess` booleans rendering wrong combinations. Which pattern fixes it?</summary>The State pattern / explicit state machine: replace independent booleans with one discriminated-union state value so only legal states exist and impossible combinations (success + error) are unrepresentable. Render per the single mode.</details>

## 6. Real-World Use Cases

The §1 snippets are deliberately textbook so the *shape* is clear; here's each pattern as code you'd actually ship in a frontend.

### Strategy — pluggable form-field validation

A form needs different rules per field, and product keeps adding more. A `switch (fieldType)` is the OCP smell; a strategy map lets you register rules without touching the validator.

```ts
type Validator = (value: string) => string | null;   // null = valid, else error message
const required: Validator = v => (v.trim() ? null : "Required");
const email: Validator    = v => (/^[^@]+@[^@]+$/.test(v) ? null : "Invalid email");
const minLen = (n: number): Validator => v => (v.length >= n ? null : `Min ${n} chars`);

const rules: Record<string, Validator[]> = {
  email: [required, email],
  password: [required, minLen(8)],
};
const validate = (field: string, value: string) =>
  (rules[field] ?? []).map(r => r(value)).find(Boolean) ?? null;
```

The algorithm is swapped behind a common `Validator` signature — adding a rule adds a function, never an edit to `validate`.

> [!tip] This is exactly a `renderItem`/`sortComparator` prop one level up: the component takes the strategy instead of hard-coding the behavior. See [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]].

### Observer — a minimal external store

Cross-tree shared state (theme, cart, auth) without prop-drilling: a subject holds state, components subscribe. This is the contract React's `useSyncExternalStore` consumes.

```ts
function createStore<T>(initial: T) {
  let state = initial;
  const subs = new Set<() => void>();
  return {
    getSnapshot: () => state,
    setState: (next: T) => { state = next; subs.forEach(fn => fn()); },
    subscribe: (fn: () => void) => { subs.add(fn); return () => subs.delete(fn); },
  };
}
// const cart = createStore({ items: [] });
// useSyncExternalStore(cart.subscribe, cart.getSnapshot);
```

`subscribe`/`getSnapshot` is the Observer contract; every state library (Zustand, Redux) is this plus ergonomics. See [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]].

### Builder — a typed request-config builder

Assembling a fetch call with optional query params, headers, and body reads badly as one giant options object; a fluent builder makes each step explicit and the terminal `build()` produces the final config.

```ts
class RequestBuilder {
  private url: URL;
  private init: RequestInit = { headers: {} };
  constructor(base: string) { this.url = new URL(base); }
  query(k: string, v: string) { this.url.searchParams.set(k, v); return this; }
  header(k: string, v: string) { (this.init.headers as Record<string, string>)[k] = v; return this; }
  json(body: unknown) { this.init.method = "POST"; this.init.body = JSON.stringify(body); return this; }
  build(): [string, RequestInit] { return [this.url.toString(), this.init]; }
}
const [url, init] = new RequestBuilder("https://api.example.com/search")
  .query("q", "shoes").query("page", "2").header("Authorization", "Bearer …").build();
```

Each method mutates the draft and returns `this`; `build()` yields the immutable result — the frontend twin of the SQL builder in §1.

## Related Notes

- [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]] (Observer)
- [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]]
- [[31 - Low Level Design/03 - OOP Concepts|OOP Concepts]]
