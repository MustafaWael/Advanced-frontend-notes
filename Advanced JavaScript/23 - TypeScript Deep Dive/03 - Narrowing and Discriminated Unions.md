---
tags: [typescript, narrowing, unions]
module: "23 - TypeScript Deep Dive"
priority: must-know
status: not-started
aliases: [discriminated union, exhaustive check]
---

# Narrowing and Discriminated Unions

## Maturity Target

- Priority: #must-know
- Study time: 60 minutes
- Interview signal: model async UI as valid states and prove each state is handled.
- Production signal: impossible loading/error/data combinations disappear from component state.
- Dependencies: [[23 - TypeScript Deep Dive/02 - Inference Widening and satisfies|Inference and satisfies]]

## Source Anchors

- [TypeScript: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [TypeScript: Union and Intersection Types](https://www.typescriptlang.org/docs/handbook/unions-and-intersections.html)
- [TypeScript: never](https://www.typescriptlang.org/docs/handbook/2/functions.html#never)

## 1. Concept

Narrowing is TypeScript refining a union after runtime evidence such as `typeof`, `in`, equality, or a custom type guard. A discriminated union gives every variant a shared literal field, making UI state explicit and exhaustive.

```tsx
type LoadState<T> =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; data: T };

function UserPanel({ state }: { state: LoadState<User> }) {
  switch (state.kind) {
    case "idle": return <button>Load</button>;
    case "loading": return <p>Loading…</p>;
    case "error": return <p role="alert">{state.message}</p>;
    case "ready": return <p>{state.data.name}</p>;
  }
}
```

## 2. Bug → Fix → Tradeoff

```ts
// Invalid combinations are representable.
type BadState = { loading: boolean; error?: string; user?: User };
```

`{ loading: true, error: "Failed", user }` can now exist even if the UI has no coherent meaning for it. The union above makes each state intentional. The tradeoff is more variants, which is useful complexity because it records real product states.

```ts
function assertNever(value: never): never {
  throw new Error(`Unhandled state: ${JSON.stringify(value)}`);
}
```

Use `assertNever` in a `default` branch when a switch must fail compilation after a new variant is added.

## Real-World Use Cases

### WebSocket message router in a live-price widget

A trading dashboard receives heterogeneous messages over one socket. A discriminated union plus an exhaustive switch turns "did we handle every message type?" into a compile question:

```ts
type ServerMessage =
  | { type: "price_update"; symbol: string; price: number }
  | { type: "order_filled"; orderId: string; fillPrice: number }
  | { type: "session_expired" };

socket.onmessage = (event) => {
  const msg = ServerMessageSchema.parse(JSON.parse(event.data)); // wire is untrusted
  switch (msg.type) {
    case "price_update": updateTicker(msg.symbol, msg.price); break;
    case "order_filled": toastFill(msg.orderId, msg.fillPrice); break;
    case "session_expired": redirectToLogin(); break;
    default: assertNever(msg);
  }
};
```

Narrowing on `msg.type` is what gives each branch its payload fields; when the backend adds `"margin_call"`, the `assertNever` default is where compilation breaks. Note the parse first — the union describes messages *after* validation, not raw bytes ([[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|Runtime Validation and Boundaries]]).

> [!warning]
> Narrowing only works if the discriminant is a **literal** type. If a schema or handwritten type declares `type: string`, every `case` narrows nothing and the payload fields stay unreachable — a common failure when generating types from loose OpenAPI specs.

### `useReducer` actions as a discriminated union

A multi-step checkout reducer: each action carries exactly the payload its transition needs, and the reducer switch narrows per case.

```ts
type CheckoutAction =
  | { type: "set_address"; address: Address }
  | { type: "apply_coupon"; code: string }
  | { type: "submit" };

function checkoutReducer(state: CheckoutState, action: CheckoutAction): CheckoutState {
  switch (action.type) {
    case "set_address": return { ...state, address: action.address };
    case "apply_coupon": return { ...state, coupon: action.code };
    case "submit": return { ...state, status: "submitting" };
  }
}
```

`dispatch({ type: "apply_coupon" })` without `code` is a compile error, and `dispatch` calls autocomplete the payload per `type` — the same mechanism as the `LoadState` union in section 1, applied to events instead of states.

### Typed `Result` from a single fetch wrapper

Instead of throwing, the app's one data-access wrapper returns success or a categorized failure; every caller is forced to narrow before touching `data`:

```ts
type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: "network" | "unauthorized" | "server"; status?: number };

const result = await fetchJson<Invoice[]>("/api/invoices");
if (!result.ok) {
  return result.error === "unauthorized" ? redirectToLogin() : <RetryBanner />;
}
renderRows(result.data); // ok: true is proven here
```

The boolean literal `ok` is the discriminant; after the early return, TypeScript knows `result.data` exists. This makes "forgot to handle the error case" a type error rather than a production incident — the pattern behind [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]].

## 3. Interview Answer

> Narrowing is the compiler refining a union from runtime evidence — `typeof`, `in`, equality, or a custom type guard. A discriminated union adds a shared literal field (`kind`) so each variant is unambiguous; modeling async UI as `idle | loading | error | ready` makes impossible combinations like "loading with data and an error" unrepresentable. I add an `assertNever` default branch so adding a variant breaks compilation everywhere it isn't handled — the type system becomes a to-do list for the refactor.

## 4. Practice

1. <details><summary>Why is `unknown` safer than `any` at a boundary?</summary>`unknown` requires evidence before use. `any` disables checking and lets invalid assumptions spread.</details>
2. <details><summary>What makes a union discriminated?</summary>Every member has a common property whose literal value uniquely identifies the member, such as `kind`.</details>
3. <details><summary>What does an exhaustive `never` check catch?</summary>A newly added variant that no switch branch handles.</details>

## Related Notes

- [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|Runtime Validation and Boundaries]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
