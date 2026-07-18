---
tags: [typescript, functions, variance, callbacks]
module: "23 - TypeScript Deep Dive"
priority: important
status: not-started
aliases: [overloads, variance, strictFunctionTypes]
---

# Function Types, Overloads and Variance

## Maturity Target

- Priority: #important
- Study time: 60 minutes
- Interview signal: explain why a callback taking *fewer* parameters is assignable, why method parameters are bivariant, and when overloads beat unions.
- Production signal: your callback-based APIs (event handlers, subscriptions) are safe to call and pleasant to implement.
- Dependencies: [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]], [[23 - TypeScript Deep Dive/04 - Generics and API Design|Generics and API Design]]

## Source Anchors

- [TypeScript: More on Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html)
- [TypeScript: strictFunctionTypes](https://www.typescriptlang.org/tsconfig/#strictFunctionTypes)
- [TypeScript FAQ: function parameter bivariance](https://github.com/microsoft/TypeScript/wiki/FAQ#why-are-function-parameters-bivariant)
- [TypeScript: Overloads](https://www.typescriptlang.org/docs/handbook/2/functions.html#function-overloads)

## 1. Concept

A function type describes what a caller may do: `type Listener = (event: MessageEvent) => void`. Compatibility between function types follows from safety for the **caller**:

- **Fewer parameters are fine.** `array.map(x => x * 2)` works even though `map` passes `(value, index, array)` — a function that ignores trailing arguments can never be broken by receiving them. This mirrors runtime JavaScript, where extra arguments are simply ignored.
- **Parameter types are contravariant** (under `strictFunctionTypes`): a handler accepting `Animal` can stand in where a handler of `Dog` is expected — it handles *at least* everything it will receive. The reverse is unsafe: a `Dog` handler registered for all `Animal`s will someday receive a `Cat` and call `.bark()` on it.
- **Return types are covariant**: returning something more specific than promised is always safe.
- **Method shorthand is bivariant** — a deliberate soundness hole kept for pragmatism (otherwise things like `Array<Dog>` wouldn't be assignable to `ReadonlyArray<Animal>`). Prefer property-style signatures (`onEvent: (e: E) => void`) over method shorthand (`onEvent(e: E): void`) in interfaces you own, so `strictFunctionTypes` actually checks them.

### Overloads — and why unions usually win

Overloads declare several call signatures for one implementation:

```ts
function parseDate(value: string): Date;
function parseDate(value: number): Date;
function parseDate(value: string | number): Date {
  return new Date(value);
}
```

They earn their keep only when the **return type depends on the argument types** in ways a union or generic can't express (e.g., `createElement("a")` returning `HTMLAnchorElement`). Otherwise prefer a union parameter — overloads are checked loosely against the implementation, resolved top-to-bottom (order matters), and every overload is API surface you must document and maintain. A conditional return type or a generic with constraints often replaces two overloads with less machinery.

## 2. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a shared `useSubscription` helper for a WebSocket wrapper.

```ts
// Bug: over-broad callback type forces every consumer to re-narrow.
function subscribe(topic: string, cb: (data: any) => void) { /* ... */ }

subscribe("orders", (order) => {
  updateBadge(order.status.toUpperCase()); // 💥 runtime crash when a "heartbeat" message arrives
});
```

Trace: `any` erased the relationship between topic and payload. The `orders` handler also receives heartbeat frames because nothing ties `topic` to a payload type — the compiler couldn't object.

```ts
// Fix: a typed event map — topic determines the payload type.
type Topics = {
  orders: { id: string; status: "paid" | "shipped" };
  heartbeat: { at: number };
};

function subscribe<K extends keyof Topics>(topic: K, cb: (data: Topics[K]) => void) { /* ... */ }

subscribe("orders", (order) => {
  order.status;        // "paid" | "shipped" — heartbeats can't reach this handler's type
});
```

The generic + indexed access ([[23 - TypeScript Deep Dive/06 - Type Operators and Exhaustiveness|type operators]]) makes the topic-payload relationship explicit; adding a topic means adding one line to `Topics`.

Tradeoffs: the event map must be maintained and truly match what the server sends — which is a *runtime* fact, so messages still need boundary validation ([[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|runtime validation]]) if the server isn't trusted to match. The type only guarantees your handlers are consistent with the declared map, not that the wire agrees.

> [!tip] Design callbacks for the caller
> When you accept a callback, type its parameters as narrowly as what you will actually pass (callers may accept broader) and type your call as passing everything you have. When you *pass* a callback, it's fine to declare fewer parameters than provided. This asymmetry is variance doing its job.

## 3. Interview Answer

> Function-type compatibility follows caller safety: fewer declared parameters are assignable because extra arguments are ignored; parameters are contravariant under `strictFunctionTypes` (a handler must accept at least what it will receive); returns are covariant. Method-shorthand signatures stay bivariant for pragmatic reasons, so I use property-style function signatures in my own interfaces to keep checking strict. Overloads I reserve for cases where the return type genuinely depends on the argument type; otherwise a union parameter or a constrained generic is simpler and better checked. For callback APIs like event subscriptions, a typed event map (`subscribe<K extends keyof Topics>`) preserves the topic→payload relationship that `any` destroys.

## 4. Practice

1. <details><summary>Why does `["a","b"].forEach(console.log)` print index and array too, and why does TypeScript allow a one-parameter callback there?</summary>`forEach` always calls the callback with `(value, index, array)`; `console.log` accepts variadic arguments and prints all three. TypeScript allows callbacks with fewer parameters because ignoring trailing arguments can't cause a runtime error — the callback simply never reads them. Parameter *count* is safe to shrink; parameter *types* are not safe to narrow.</details>

2. <details><summary>`type H = (e: Event) => void` — can you assign a `(e: MouseEvent) => void` to it? Why not?</summary>No (under `strictFunctionTypes`). Whoever holds an `H` may invoke it with *any* `Event`; a `MouseEvent`-specific handler would read mouse-only fields on, say, a `KeyboardEvent`. The safe direction is the reverse: a handler accepting `Event` (or anything broader) is assignable where a `MouseEvent` handler is expected. Parameters are contravariant.</details>

3. <details><summary>When is an overload genuinely better than a union parameter?</summary>When distinct argument types produce distinct return types that callers need statically — `document.createElement("video")` returning `HTMLVideoElement`, or a `query(sql, params?)` returning typed rows per query object. If the return type is the same for all inputs, a union parameter is simpler, and the implementation is checked more strictly too.</details>

4. <details><summary>Your interface has `onSelect(item: Item): void` and a teammate says strict mode isn't catching an unsound handler assignment. Likely cause?</summary>Method shorthand syntax is bivariant even under `strictFunctionTypes` — the flag only applies to property-style function types. Change the declaration to `onSelect: (item: Item) => void` and the unsound assignment becomes an error. This is a known, deliberate escape hatch in the language.</details>

## Related Notes

- [[04 - Functions Deep Dive/03 - Higher Order Functions and Callbacks|Higher Order Functions and Callbacks]]
- [[23 - TypeScript Deep Dive/04 - Generics and API Design|Generics and API Design]]
- [[23 - TypeScript Deep Dive/06 - Type Operators and Exhaustiveness|Type Operators and Exhaustiveness]]
- [[19 - DOM and Browser APIs/04 - Custom Events and EventTarget|Custom Events and EventTarget]]
