---
tags: [javascript, moc, this-binding]
module: "05 - this Binding"
priority: must-know
status: not-started
---

# this Binding MOC

This module teaches `this` as a call-site-determined binding, not a mystical object pointer: default, implicit, explicit, `new`, and lexical arrow binding, plus strict-mode differences and `call`/`apply`/`bind`. It ends the guesswork behind method extraction bugs, lost receivers in callbacks, and class component handler crashes in React. Interviews love `this` output questions because they instantly separate call-site reasoning from memorized folklore.

## Prerequisites

- [[04 - Functions Deep Dive/00 - Functions Deep Dive MOC|Functions Deep Dive MOC]] — function forms and arrows are assumed throughout.
- [[04 - Functions Deep Dive/02 - Arrow Functions|Arrow Functions]] — lexical `this` is the key exception to every rule here.

## Reading Order

1. [[05 - this Binding/01 - What is this|What is this]] — the five binding rules and why the call site decides.
2. [[05 - this Binding/02 - this in Strict Mode|this in Strict Mode]] — `undefined` vs global substitution, and top-level `this` in scripts vs modules.
3. [[05 - this Binding/03 - this in Objects and Functions|this in Objects and Functions]] — method extraction, immediate receivers, and nested-function context loss.
4. [[05 - this Binding/04 - Arrow Functions and Lexical this|Arrow Functions and Lexical this]] — why `call`/`apply`/`bind` cannot change an arrow's `this`.
5. [[05 - this Binding/05 - call apply bind|call apply bind]] — explicit binding, partial arguments, and the bind-twice rule.
6. [[05 - this Binding/06 - Constructor and Class this|Constructor and Class this]] — what `new` does, constructor return override, and `super()` before `this`.
7. [[05 - this Binding/07 - React this Examples|React this Examples]] — class handler binding fixes and why function components drop `this` entirely.
8. [[05 - this Binding/08 - this Checklist|this Checklist]] — active self-test with trace snippets and production drills.

## You're Done When

- [ ] I can define `this` as a special binding determined by the call site for regular functions, and identify all five binding rules.
- [ ] I can explain why method extraction (`const fn = obj.method; fn()`) loses the receiver and fix it with wrappers, `bind`, or arrows.
- [ ] I can explain strict vs sloppy default binding and top-level `this` in browser scripts vs ES modules.
- [ ] I can explain lexical arrow `this` and why `call`, `apply`, and `bind` cannot override it.
- [ ] I can compare `call`, `apply`, and `bind`, and explain why binding twice keeps the first `this`.
- [ ] I can explain what `new` does, constructor object-return override, and why derived class constructors need `super()` before `this`.
- [ ] I can fix React class handler `this` bugs with constructor binding or arrow fields and state the identity tradeoffs.
- [ ] I can solve every checklist snippet without running it, using call-site language.
