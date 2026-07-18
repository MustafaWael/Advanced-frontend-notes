---
tags: [react, moc, internals, patterns]
module: "21 - React Internals and Patterns"
priority: must-know
status: not-started
---

# React Internals and Patterns MOC

This module opens the box: why frameworks exist at all, what an element and a "render" actually are, how reconciliation and keys decide state identity, how Fiber makes rendering interruptible, how the event system and portals really work, how batching and effect timing behave, and the modern patterns — context performance, refs, external stores, Suspense, React 19 Actions, custom hooks, controlled vs uncontrolled. It complements folder 14 (which applies JavaScript semantics to React) by going one level deeper into React's own mechanisms — it links to folder 14 rather than repeating it. After this module, React behavior is mechanism you can reason about, not magic you memorize.

## Prerequisites

- [[14 - JavaScript in React and Next.js/00 - JavaScript in React and Next.js MOC|JavaScript in React and Next.js MOC]] — closures, dependency arrays, referential equality, and immutability are assumed.
- [[21 - React Internals and Patterns/14 - Why React Exists|Why React Exists]] — start here for the *why*; then [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]] for the core mechanism.

## Reading Order

(Notes 14–16 were added later; numbers are file names, not sequence.)

1. [[21 - React Internals and Patterns/14 - Why React Exists|Why React Exists]] — the problem frameworks solve; UI = f(state); the honest VDOM story.
2. [[21 - React Internals and Patterns/15 - Elements JSX and Component Identity|Elements, JSX and Component Identity]] — what JSX compiles to; element vs component vs fiber.
3. [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]] — what a render is; purity.
4. [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]] — diffing and why index keys corrupt state.
5. [[21 - React Internals and Patterns/16 - Synthetic Events and Portals|Synthetic Events and Portals]] — delegation to the root; portal bubbling.
6. [[21 - React Internals and Patterns/03 - Fiber and Scheduling Overview|Fiber and Scheduling Overview]] — interruptible rendering, lanes, MessageChannel yielding.
7. [[21 - React Internals and Patterns/04 - State Batching and Updater Queues|State Batching and Updater Queues]] — automatic batching and functional updates.
8. [[21 - React Internals and Patterns/05 - Context Mechanics and Performance|Context: Mechanics and Performance]] — propagation and re-render control.
9. [[21 - React Internals and Patterns/06 - Refs Beyond DOM|Refs Beyond DOM]] — refs as instance variables, callback refs, React 19 ref-as-prop, `useEffectEvent`.
10. [[21 - React Internals and Patterns/07 - useLayoutEffect useInsertionEffect and Effect Timing|Effect Timing]] — the full render-to-paint timeline.
11. [[21 - React Internals and Patterns/08 - useSyncExternalStore|useSyncExternalStore]] — tearing and external store binding.
12. [[21 - React Internals and Patterns/09 - Suspense and Concurrent Features|Suspense and Concurrent Features]] — suspending, transitions, streaming.
13. [[21 - React Internals and Patterns/10 - React 19|React 19]] — Actions, new hooks, `use()`, 19.2 (`<Activity>`, Performance Tracks), the React Compiler.
14. [[21 - React Internals and Patterns/11 - Custom Hook Design Patterns|Custom Hook Design Patterns]] — reusable, stable, cleanup-correct hooks.
15. [[21 - React Internals and Patterns/12 - Controlled vs Uncontrolled Components|Controlled vs Uncontrolled Components]] — form value ownership.
16. [[21 - React Internals and Patterns/13 - React Internals Checklist|React Internals Checklist]] — active self-test.

## You're Done When

- [ ] I can explain why UI frameworks exist (state–DOM sync), state UI = f(state), and give the honest virtual-DOM-vs-signals tradeoff.
- [ ] I can say what JSX compiles to, what an element object contains, and separate element vs component vs fiber.
- [ ] I can explain event delegation to the root container, SyntheticEvent, and why portal events bubble through the React tree.
- [ ] I can separate render from commit and explain why render must be pure.
- [ ] I can explain reconciliation heuristics and why index keys corrupt stateful lists.
- [ ] I can explain Fiber, interruptible rendering, and lane priority at overview depth.
- [ ] I can explain automatic batching and choose value vs updater form correctly.
- [ ] I can control context re-renders by splitting contexts and stabilizing values.
- [ ] I can use refs as instance variables and expose imperative handles.
- [ ] I can place every effect hook on the render-to-paint timeline and choose correctly.
- [ ] I can explain tearing and bind an external store with `useSyncExternalStore`.
- [ ] I can use Suspense, transitions, and deferred values, and connect them to streaming SSR.
- [ ] I can use React 19 Actions and hooks, and explain the Compiler's impact on memoization.
- [ ] I can use `useEffectEvent` only for effect-fired logic, never as a dependency workaround or a callback passed to children.
- [ ] I can choose `<Activity mode="hidden">` when preserving state while unmounting effects is worth more than conditional-rendering state loss or CSS-hidden background work.
- [ ] I can design clean custom hooks and choose controlled vs uncontrolled per form.

## Related Notes

- [[14 - JavaScript in React and Next.js/00 - JavaScript in React and Next.js MOC|JavaScript in React and Next.js MOC]]
- [[22 - Next.js Deep Dive/00 - Next.js Deep Dive MOC|Next.js Deep Dive MOC]]
- [[13 - Performance and Memory/07 - React Performance Examples|React Performance Examples]]
- [[01 - Roadmap|Roadmap]]
- [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|React Component Testing Through User Behavior]]
- [[23 - TypeScript Deep Dive/09 - React and Next TypeScript Patterns|React and Next TypeScript Patterns]]
