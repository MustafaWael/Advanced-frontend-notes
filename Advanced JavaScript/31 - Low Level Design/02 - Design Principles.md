---
tags: [low-level-design, principles, solid, interview]
module: "31 - Low Level Design"
priority: must-know
status: not-started
aliases: [SOLID, KISS, DRY, YAGNI, separation of concerns]
---

# Design Principles

## Maturity Target

- Priority: #must-know
- Study time: 35 minutes
- Interview signal: Name each SOLID principle, the specific smell it fixes, and show it in TS — and recognize all of them in frontend code.
- Production signal: You can articulate *why* a refactor is better, not just that it feels cleaner.
- Dependencies: [[31 - Low Level Design/01 - The Delivery Framework|The Delivery Framework]], [[23 - TypeScript Deep Dive/04 - Generics and API Design|Generics and API Design]]

## Source Anchors

- [HelloInterview — Design Principles](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/principles)
- [Robert C. Martin — SOLID](https://en.wikipedia.org/wiki/SOLID)

## 1. Concept

**General principles:**
- **KISS** — prefer the simplest thing that works.
- **DRY** — one authoritative source for each piece of knowledge (but don't over-abstract two things that merely look alike).
- **YAGNI** — don't build for imagined future requirements.
- **Separation of Concerns** — each module owns one concern (data / logic / presentation).
- **Law of Demeter** — talk to your immediate collaborators, not their internals (`a.b.c.doThing()` is a smell).

**SOLID:**

- **S — Single Responsibility.** A class has one reason to change. Fix for god-objects.
- **O — Open/Closed.** Open to extension, closed to modification — add behavior via new types, not by editing a growing `switch`.
- **L — Liskov Substitution.** *Behavioral* substitutability: a subtype must honor the base type's contract, not just its method signatures — it can't strengthen preconditions, weaken postconditions, or break invariants callers rely on. If code that works with the base breaks (or must type-check what it got) when handed a subtype, LSP is violated. The classic `Square extends Rectangle` case fails because setting width independently of height breaks a Rectangle invariant callers assume.
- **I — Interface Segregation.** Many small focused interfaces beat one fat one; don't force implementers to stub methods they don't use.
- **D — Dependency Inversion.** This is a *structural* rule about the direction of dependencies, and it's distinct from dependency injection. DIP: high-level policy and low-level details should both depend on an abstraction, and that abstraction is **owned by (defined for) the high-level module** — so the arrow points *toward* policy, not toward implementation detail. Dependency *injection* is merely one technique for supplying the concrete implementation at runtime; you can inject and still violate DIP (if the interface is dictated by the low-level module), and you can satisfy DIP without a DI container. Say "DIP is the principle, injection is a way to wire it."

```ts
// OCP + DIP: add payment methods without editing the processor
interface Receipt { id: string; cents: number; }
// The PaymentMethod abstraction is defined for Checkout's needs (DIP: policy owns the interface)
interface PaymentMethod { pay(cents: number): Promise<Receipt>; }

class Checkout {
  constructor(private method: PaymentMethod) {}          // depends on the abstraction (DIP)
  complete(cents: number) { return this.method.pay(cents); }
}
// New method = new class, Checkout is untouched (OCP)
class ApplePay implements PaymentMethod {
  async pay(cents: number): Promise<Receipt> {
    // ...call the ApplePay SDK...
    return { id: crypto.randomUUID(), cents };
  }
}
```

LSP is the letter people fumble, because it's about *behavior*, not just types. The classic violation typechecks fine yet breaks callers:

```ts
class Rectangle {
  constructor(protected w: number, protected h: number) {}
  setWidth(w: number) { this.w = w; }
  setHeight(h: number) { this.h = h; }
  area() { return this.w * this.h; }
}
// A Square "is-a" Rectangle by types, but silently breaks the invariant
// callers rely on: that width and height move independently.
class Square extends Rectangle {
  setWidth(w: number)  { this.w = w; this.h = w; }   // surprise side effect
  setHeight(h: number) { this.w = h; this.h = h; }
}
function grow(r: Rectangle) {          // written against Rectangle's contract
  r.setWidth(5); r.setHeight(4);
  return r.area();                     // caller expects 20…
}
grow(new Rectangle(1, 1)); // 20 ✓
grow(new Square(1, 1));    // 16 ✗ — setHeight clobbered width; LSP violated
```

The fix isn't a cleverer subclass — it's *not* modeling Square as a subtype of a mutable Rectangle. Prefer composition (a `Shape` interface both implement independently), so no caller written against one is surprised by the other.

> [!tip] Frontend mirror: SRP is the container/presentational split and hooks-extraction; DIP is injecting a `getData` function or a service via context/props instead of hard-importing it ([[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]]); OCP is a component that takes a `renderItem` prop instead of a `switch` over item types. You already write SOLID — this names it.

## 2. Why It Matters

Principles are the *why* behind every "this is cleaner." In an LLD round they're graded directly (especially SRP and DIP); in real work they're the vocabulary that turns "I don't like this" into a reviewable argument. The patterns in the next note are just principles crystallized into named structures.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a `NotificationService` sends email, SMS, and push, with a `switch(type)` in a `send()` method. Every new channel edits that method; a bad SMS change breaks email.

Trace: an **OCP + SRP** violation. One class owns every channel (many reasons to change) and behavior is added by *modifying* existing code (risking the other channels) instead of *extending*.

```ts
// Fix: each channel behind one interface; adding a channel adds a class, edits nothing
interface Channel { send(msg: Message): Promise<void>; }
class EmailChannel implements Channel { /* ... */ }
class SmsChannel   implements Channel { /* ... */ }

class Notifier {                                   // one job: dispatch
  constructor(private channels: Map<Type, Channel>) {}   // DIP: injected
  send(type: Type, msg: Message) { return this.channels.get(type)!.send(msg); }
}
```

Tradeoff: more types and a wiring point (the map). For two channels that will never grow, the `switch` was fine (KISS/YAGNI) — principles are judgment, not law. Apply them when change is actually likely.

## 4. Interview Answer

Short answer:

> SOLID is my vocabulary for why a design is good. Single Responsibility keeps classes cohesive; Open/Closed means I add behavior with new types instead of editing a growing switch; Liskov keeps subtypes safely substitutable; Interface Segregation keeps interfaces small and focused; Dependency Inversion has classes depend on injected abstractions. Underneath sit KISS, DRY, and YAGNI, which stop me over-applying the rest.

Deeper answer:

> The two I lean on most are SRP and DIP, because they're what make code testable and extensible — a class with one reason to change and its dependencies injected behind interfaces can be tested in isolation and extended without edits. But the meta-principle is KISS/YAGNI: SOLID over-applied becomes its own smell — needless interfaces and indirection for code that will never change. So I apply a principle when the change it guards against is actually likely, which is the same judgment as deciding when to extract a hook or split a component.

## 5. Practice

1. <details><summary>Give the smell each SOLID letter fixes, in one phrase.</summary>S: god-object (many reasons to change). O: editing existing code to add cases (growing switch). L: a subtype that breaks callers' assumptions. I: fat interfaces forcing empty stub methods. D: hard-wired concrete dependencies that can't be swapped or mocked.</details>
2. <details><summary>How can SOLID itself be over-applied?</summary>Adding interfaces, factories, and layers for code that won't change violates KISS/YAGNI — the indirection costs readability with no payoff. Principles guard against *likely* change; applied speculatively they're over-engineering, the same mistake as forcing a design pattern.</details>
3. <details><summary>Show DIP in a React setting — and how is it different from dependency injection?</summary>DIP: a `UserList` component depends on a `UserSource` interface *it defines for its own needs* (e.g. `{ getUsers(): Promise<User[]> }`), not on a concrete `api.ts` module — the dependency arrow points toward the component's policy, so the REST/GraphQL/mock implementation can change freely. Injection is the *wiring*: passing `getUsers` as a prop or via context is one way to supply that implementation. The distinction: you could inject a concrete client whose shape is dictated by the API module — that's DI without DIP (you can still only swap same-shaped clients). DIP is satisfied by who owns the abstraction, not by whether you inject.</details>

## 6. Real-World Use Cases

The frontend-mirror tip covers SRP/DIP/OCP; these two show the letters that are easiest to under-apply in a component codebase.

### ISP — split a god props interface

A `<Button>` that accepts one 15-field props type forces every caller (and every consumer of the type) to depend on fields they never use, and one added field re-types the world. Segregate by role.

```ts
// Before: one fat contract every caller depends on
interface ButtonProps { label: string; onClick(): void; icon?: string; loading?: boolean;
  href?: string; target?: string; download?: boolean; /* …8 more… */ }

// After: small, role-focused interfaces; a caller depends only on what it uses
interface Clickable { label: string; onClick(): void; }
interface Loadable  { loading?: boolean; }
interface LinkLike  { href: string; target?: string }
type ActionButtonProps = Clickable & Loadable;
type LinkButtonProps   = Clickable & LinkLike;
```

Each consumer depends on the narrow interface it needs — the client analog of not forcing an implementer to stub methods it doesn't use. See [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]].

### SRP — extract the data concern into a hook

A component that fetches, holds loading/error state, *and* renders has multiple reasons to change (API shape vs layout). Extracting the data concern into a hook gives each one job and makes the fetch logic testable in isolation.

```ts
// One reason to change each: the hook owns data, the component owns presentation
function useOrders(userId: string) {
  const [state, setState] = useState<{ orders: Order[]; loading: boolean }>({ orders: [], loading: true });
  useEffect(() => {
    let live = true;
    fetchOrders(userId).then(orders => live && setState({ orders, loading: false }));
    return () => { live = false; };
  }, [userId]);
  return state;
}
// <OrdersList> now just calls useOrders() and renders — presentation only.
```

SRP as the container/presentational split, enforced by the hook boundary rather than by discipline.

## Related Notes

- [[31 - Low Level Design/04 - Design Patterns|Design Patterns]]
- [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]]
- [[23 - TypeScript Deep Dive/04 - Generics and API Design|Generics and API Design]]
