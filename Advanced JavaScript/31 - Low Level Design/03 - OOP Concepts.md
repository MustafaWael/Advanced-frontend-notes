---
tags: [low-level-design, oop, interview]
module: "31 - Low Level Design"
priority: important
status: not-started
aliases: [encapsulation, abstraction, polymorphism, inheritance vs composition]
---

# OOP Concepts

## Maturity Target

- Priority: #important
- Study time: 30 minutes
- Interview signal: Define the four OOP pillars precisely and argue composition over inheritance with a concrete failure case.
- Production signal: You default to composition in component and module design and know when inheritance genuinely fits.
- Dependencies: [[31 - Low Level Design/02 - Design Principles|Design Principles]], [[06 - Objects and Prototypes/00 - Objects and Prototypes MOC|Objects and Prototypes MOC]]

## Source Anchors

- [HelloInterview — OOP Concepts](https://www.hellointerview.com/learn/low-level-design/in-a-hurry/oop)
- [MDN — Object-oriented JavaScript](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Advanced_JavaScript_objects)

## 1. Concept

- **Encapsulation** — bundle state with the methods that manage it, and hide internals behind an interface. Callers can't corrupt invariants because they can't reach the fields. (TS `private` is *compile-time only* — erased at runtime, still reachable via bracket access or JS; `#fields` are *runtime-enforced* true privates. Reach for `#fields` when the guarantee must hold at runtime.)
- **Abstraction** — expose *what* an object does, hide *how*. A `PaymentMethod.pay()` caller doesn't know the gateway.
- **Polymorphism** — one interface, many implementations, chosen at runtime. `channels.get(type).send()` calls the right `send` without a conditional.
- **Inheritance** — a subclass reuses/extends a superclass (is-a). Powerful and overused.

**Composition over inheritance** — the load-bearing takeaway. Inheritance couples a subclass to its parent's implementation and forces a single rigid hierarchy; real requirements are usually mix-and-match (a duck that swims *and* flies, a logger that's also buffered). Composition — build behavior by holding collaborators — stays flexible.

```ts
// Inheritance trap: behavior varies on two independent axes → hierarchy explodes
// FlyingSwimmingDuck, FlyingNonSwimmingDuck, ... one class per combination

// Composition: inject behaviors, combine freely
interface FlyBehavior { fly(): void; }
interface SwimBehavior { swim(): void; }
class Duck {
  constructor(private flyBehavior: FlyBehavior, private swimBehavior: SwimBehavior) {}
  fly()  { this.flyBehavior.fly(); }    // swap behaviors at runtime; no subclass per combo
  swim() { this.swimBehavior.swim(); }
}
```

> [!warning] Inheritance breaks when behavior varies on more than one axis, or when a subclass can't honor the parent's contract (a Liskov violation, [[31 - Low Level Design/02 - Design Principles|Design Principles]]). The symptom is a combinatorial explosion of subclasses or overrides that throw "not supported."

> [!tip] Frontend mirror: React chose composition deliberately — you compose components and hooks, you don't subclass a `Button` into `PrimaryLargeIconButton`. A behavior mixed in via a custom hook is the `FlyBehavior` injection above ([[21 - React Internals and Patterns/11 - Custom Hook Design Patterns|Custom Hook Design Patterns]]).

## 2. Why It Matters

Interviewers probe "inheritance or composition here?" to see if you reach for inheritance reflexively. And the composition instinct is exactly what makes frontend architecture flexible — hooks and component composition over base-class hierarchies. Encapsulation shows up as module boundaries; polymorphism as strategy-style pluggability.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a UI toolkit models buttons with inheritance — `Button` → `IconButton` → `LoadingIconButton` → `PrimaryLoadingIconButton`. A request for a "secondary loading icon button" means yet another class, and shared tweaks force edits up and down the tree.

Trace: variation on independent axes (variant × loading × icon) modeled as a single inheritance chain → combinatorial explosion, and changes ripple through the hierarchy (fragile base class).

Fix: composition — one `Button` that takes props/slots (`variant`, `loading`, `icon`), combining behaviors instead of subclassing per combination. Cross-cutting behavior (a loading spinner) becomes a wrapper or hook, injected where needed.

Tradeoff: composition can push complexity into configuration (prop soup) if overdone; a very stable single-axis hierarchy (a strict `Shape` taxonomy) can be cleaner as inheritance. Choose by how many independent axes actually vary.

## 4. Interview Answer

Short answer:

> The four pillars: encapsulation hides state behind methods to protect invariants; abstraction exposes what not how; polymorphism lets one interface have many runtime implementations; inheritance reuses via an is-a relationship. I default to composition over inheritance because real behavior usually varies on multiple independent axes, and inheritance forces a single rigid hierarchy that explodes combinatorially.

Deeper answer:

> Inheritance is right for a genuine, stable is-a with a shared contract every subtype honors — otherwise you hit Liskov violations or a subclass per feature combination. Composition injects behaviors as collaborators, so you mix them freely and swap at runtime, which is exactly the Strategy pattern and exactly why React composes components and hooks instead of subclassing. Encapsulation and polymorphism are the enablers: hidden state keeps invariants safe, and programming to an interface lets the composed pieces be interchangeable.

## 5. Practice

1. <details><summary>Name two concrete signals that you've outgrown inheritance and should compose.</summary>(1) A combinatorial explosion of subclasses because behavior varies on independent axes (variant × size × state). (2) Subclasses overriding methods to throw "not supported," i.e. they can't honor the base contract — a Liskov violation. Both say the shared behavior should be injected, not inherited.</details>
2. <details><summary>How does encapsulation protect invariants — give an example?</summary>By hiding fields behind methods, callers can't set an illegal state. A `BankAccount` with a private `balance` and only `deposit`/`withdraw` methods can enforce "never negative"; if `balance` were public, any code could break the invariant and the class couldn't guarantee anything.</details>
3. <details><summary>Where does React embody composition-over-inheritance?</summary>Components compose other components (children/slots) and reuse behavior via hooks rather than subclassing base components. A shared behavior is a custom hook injected into any component — the runtime behavior-injection of composition — which is why there's no `class PrimaryButton extends Button` idiom in modern React.</details>

## Related Notes

- [[31 - Low Level Design/04 - Design Patterns|Design Patterns]] (Strategy = injected behavior)
- [[21 - React Internals and Patterns/11 - Custom Hook Design Patterns|Custom Hook Design Patterns]]
- [[06 - Objects and Prototypes/00 - Objects and Prototypes MOC|Objects and Prototypes MOC]]
