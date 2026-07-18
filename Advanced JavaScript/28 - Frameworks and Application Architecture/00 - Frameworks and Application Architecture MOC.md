---
tags: [frameworks, architecture, react, moc]
module: "28 - Frameworks and Application Architecture"
priority: must-know
status: not-started
---

# Frameworks and Application Architecture MOC

This module answers the "why" layer above React: what problem frameworks solve, how the major approaches differ (React, Angular, Svelte/Solid, Web Components), and how to structure applications — state, components, folders — once a framework is chosen. It complements [[21 - React Internals and Patterns/00 - React Internals and Patterns MOC|React Internals]]: that module goes *down* into React's machinery; this one goes *up* into design decisions and *across* into the landscape. After it, "why React?", "how would you structure state?", and "have you seen other approaches?" get answers with tradeoffs, not tribal loyalty.

## Prerequisites

- [[21 - React Internals and Patterns/14 - Why React Exists|Why React Exists]] — the React-specific origin story; this module generalizes it.
- [[19 - DOM and Browser APIs/00 - DOM and Browser APIs MOC|DOM and Browser APIs MOC]] — imperative DOM is the baseline everything improves on.

## Reading Order

1. [[28 - Frameworks and Application Architecture/01 - The Problem Frameworks Solve|The Problem Frameworks Solve]] — state/UI synchronization, from first principles.
2. [[28 - Frameworks and Application Architecture/02 - Web Components|Web Components]] — the platform's own component model, and why it didn't win apps.
3. [[28 - Frameworks and Application Architecture/03 - Framework Approaches Compared|Framework Approaches Compared]] — VDOM vs compiler vs fine-grained signals.
4. [[28 - Frameworks and Application Architecture/04 - Meta-Frameworks|Meta-Frameworks]] — Next/Remix/Angular-SSR; what the app framework doesn't do.
5. [[28 - Frameworks and Application Architecture/05 - State Management Taxonomy|State Management Taxonomy]] — local, lifted, shared, global; the decision tree.
6. [[28 - Frameworks and Application Architecture/06 - Server State|Server State]] — why fetched data is a cache, not state.
7. [[28 - Frameworks and Application Architecture/07 - Component Design Patterns|Component Design Patterns]] — compound components, composition over configuration.
8. [[28 - Frameworks and Application Architecture/08 - Application Architectures|Application Architectures]] — FSD, Clean, Atomic — and when they're overkill.
9. [[28 - Frameworks and Application Architecture/09 - Frameworks and Architecture Checklist|Frameworks and Architecture Checklist]] — active self-test.

## You're Done When

- [ ] I can derive the framework value proposition from the state-sync problem, without buzzwords.
- [ ] I can explain Web Components fairly: what they standardize, where they shine, why apps chose frameworks.
- [ ] I can compare VDOM diffing, AOT compilation + signals, and fine-grained reactivity — with a tradeoff each.
- [ ] I can classify any piece of state (local/lifted/shared/global/server) and pick storage with reasons.
- [ ] I can argue why server state belongs in a cache library, naming staleness, invalidation, and deduping.
- [ ] I can build a compound component and say what API problem it removes.
- [ ] I can describe FSD, Clean, and Atomic — and articulate when each is the wrong choice.

## Related Notes

- [[21 - React Internals and Patterns/00 - React Internals and Patterns MOC|React Internals and Patterns MOC]]
- [[22 - Next.js Deep Dive/00 - Next.js Deep Dive MOC|Next.js Deep Dive MOC]]
- [[27 - Frontend Tooling and Build Systems/00 - Frontend Tooling and Build Systems MOC|Frontend Tooling and Build Systems MOC]]
- [[01 - Roadmap|Roadmap]]
