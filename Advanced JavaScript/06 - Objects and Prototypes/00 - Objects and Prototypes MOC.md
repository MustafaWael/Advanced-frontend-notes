---
tags: [javascript, moc, objects, prototypes]
module: "06 - Objects and Prototypes"
priority: important
status: not-started
---

# Objects and Prototypes MOC

This module teaches JavaScript's object model from the inside: internal slots, property descriptors, the prototype chain, `__proto__` vs `.prototype`, what `new` really does, classes as prototype sugar, and copying vs immutability. It explains why spread is shallow, why React state updates require new references, and how `instanceof` can lie across iframes. Interviews use prototype-chain and copy-semantics questions to test whether you understand identity and delegation rather than syntax.

## Prerequisites

- [[05 - this Binding/00 - this Binding MOC|this Binding MOC]] — inherited methods receive the instance as `this`; you need the binding rules first.
- [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]] — `new` and class `this` are extended here into the full object model.

## Reading Order

1. [[06 - Objects and Prototypes/01 - Objects Internally|Objects Internally]] — properties, internal slots, reference identity, and key stringification.
2. [[06 - Objects and Prototypes/02 - Property Descriptors|Property Descriptors]] — `writable`, `enumerable`, `configurable`, and the `defineProperty` false defaults.
3. [[06 - Objects and Prototypes/03 - Prototype and Prototype Chain|Prototype and Prototype Chain]] — lookup from own property to `null`, shadowing, and `instanceof`.
4. [[06 - Objects and Prototypes/04 - proto vs prototype|proto vs prototype]] — the internal link vs the constructor property, untangled once and for all.
5. [[06 - Objects and Prototypes/05 - Constructor Functions and new|Constructor Functions and new]] — the four steps of `new` and the object-return override.
6. [[06 - Objects and Prototypes/06 - Classes and Inheritance|Classes and Inheritance]] — `extends`, `super`, static and private members over the same prototype machinery.
7. [[06 - Objects and Prototypes/07 - Object Copying and Immutability|Object Copying and Immutability]] — shallow vs deep copies, structural sharing, and React state updates.
8. [[06 - Objects and Prototypes/08 - Objects Checklist|Objects Checklist]] — active self-test with trace snippets and production drills.

## You're Done When

- [ ] I can explain objects as string/symbol-keyed property collections with internal slots, and distinguish own from inherited properties.
- [ ] I can read data and accessor descriptors, explain `writable`/`enumerable`/`configurable`, and why `defineProperty` defaults flags to false.
- [ ] I can trace property lookup through the prototype chain to `null`, explain shadowing, and explain how `instanceof` works.
- [ ] I can explain `__proto__` vs `.prototype` and show `Object.getPrototypeOf(instance) === Constructor.prototype`.
- [ ] I can explain the four steps of `new`, implement a simplified `myNew`, and explain the constructor object-return override.
- [ ] I can explain classes as prototype-based with stricter rules: TDZ, strict mode, `new` requirement, `extends`, `super`, static and private fields.
- [ ] I can explain shallow vs deep copy, structural sharing, and update nested React state by copying only the changed path.
- [ ] I can solve all seven checklist snippets without running them.
