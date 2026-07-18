---
tags: [react, internals, checklist]
module: "21 - React Internals and Patterns"
priority: must-know
status: not-started
---

# React Internals Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, predict, debug, and refactor without looking.

## Source Anchors

- [react.dev - Reference](https://react.dev/reference/react)
- [react.dev - Learn](https://react.dev/learn)
- [react.dev - Rules of React](https://react.dev/reference/rules)
- [react.dev - React v19](https://react.dev/blog/2024/12/05/react-19)

## Why React Exists

- [ ] I can explain the state–DOM synchronization problem and UI = f(state), including when the platform is a better choice.
- [ ] I can give the honest virtual-DOM tradeoff and distinguish Solid/Svelte/Vue reactivity models without claiming they are identical.

## Elements and Identity

- [ ] I can separate JSX, element, component, and fiber, and trace type/key/position to preserved or reset state.
- [ ] I can explain the `$$typeof` JSON-object-injection defense while treating its exact Symbol as an implementation detail.

## Render and Commit

- [ ] I can define a render as calling the component to compute an element tree, separate from commit.
- [ ] I can explain why render must be pure and what StrictMode's double-invoke catches.
- [ ] I can explain state-as-a-snapshot and why batched `setN(n+1)` collapse.
- [ ] I can explain why a re-render is not automatically a DOM update or a performance problem.

## Reconciliation and Keys

- [ ] I can state the diffing heuristics: type change remounts, same type updates, lists match by key.
- [ ] I can explain precisely why index keys corrupt state on reorder/delete.
- [ ] I can explain element type identity resetting state and the reset-with-key pattern.
- [ ] I can explain why `key={Math.random()}` is an anti-pattern.

## Fiber and Scheduling

- [ ] I can explain Fiber as interruptible units of work and why render pauses but commit can't.
- [ ] I can explain lanes/priority at overview depth and how transitions get preempted.
- [ ] I can explain that transitions reorder work by urgency, not make it cheaper.
- [ ] I can explain MessageChannel scheduling and `shouldYield`, and why React does not schedule render work with `requestIdleCallback`.

## Batching and Updaters

- [ ] I can explain React 18 automatic batching across timeouts and promises.
- [ ] I can choose value vs updater form and explain the batching boundary at `await`.
- [ ] I can use `flushSync` and explain its cost.

## Context

- [ ] I can explain that changing a provider value re-renders all consumers.
- [ ] I can fix the unstable-value-identity and one-context-many-concerns traps.
- [ ] I can explain why `React.memo` doesn't stop context re-renders.
- [ ] I can say when context is the wrong tool and reach for an external store.

## Refs

- [ ] I can explain `useRef` as a non-render-triggering mutable instance variable.
- [ ] I can use callback refs, the latest-value ref, and `useImperativeHandle`.
- [ ] I can explain `ref` as a prop in React 19 and forwardRef deprecation.
- [ ] I can choose ref vs state by whether the value appears in render.

## Effect Timing

- [ ] I can order the reliable timeline: render → commit → layout effect → paint → passive effect, and place insertion effects only as “before layout effects; DOM-mutation order unspecified”.
- [ ] I can choose useEffect vs useLayoutEffect by flicker vs paint-blocking.
- [ ] I can explain the SSR/hydration warning for useLayoutEffect.
- [ ] I can explain why useInsertionEffect exists (style injection before layout reads).

## External Stores

- [ ] I can define tearing and why external stores need `useSyncExternalStore` under concurrency.
- [ ] I can explain the subscribe/getSnapshot contract and the stability trap.
- [ ] I can explain `getServerSnapshot` and its hydration-mismatch tradeoff.

## Suspense and Concurrent

- [ ] I can explain suspending as throwing a promise caught by a boundary.
- [ ] I can choose useTransition vs useDeferredValue.
- [ ] I can explain the streaming SSR + selective hydration relationship.
- [ ] I can explain why Suspense needs an Error Boundary alongside it.

## React 19

- [ ] I can explain Actions and what they auto-manage (pending, error, optimistic, form reset).
- [ ] I can use `useActionState`, `useOptimistic`, `useFormStatus`, and `use()`.
- [ ] I can explain the React Compiler and when manual memoization still matters.
- [ ] I can state the `useEffectEvent` rules: effect-only invocation, not a dependency, and never passed to another component or Hook.
- [ ] I can choose `<Activity>` versus conditional rendering and CSS hiding by state retention, effect cleanup, and background-priority behavior.

## Synthetic Events and Portals

- [ ] I can explain root-container event delegation, SyntheticEvent/`nativeEvent`, and the React 17 pooling change.
- [ ] I can trace a portal click through the React tree and distinguish it from DOM containment and native propagation.

## Hooks and Forms

- [ ] I can explain what a custom hook shares (logic, not state) and design a clean API.
- [ ] I can build a race-safe, cleanup-correct `useFetch` and say why React Query is usually better.
- [ ] I can define controlled vs uncontrolled and choose per requirement.
- [ ] I can explain and fix the uncontrolled-to-controlled warning and the `value={0}` trap.

## Exit Test

- [ ] Explain why a list's checkboxes scramble after a delete, tracing keys and instance identity.
- [ ] Build a responsive search over 50k items using a transition or deferred value, and say why memo/worker may still be needed.
- [ ] Split a bloated app context to eliminate unrelated re-renders.
- [ ] Refactor a hand-rolled optimistic-update handler into React 19 Actions + useOptimistic.
- [ ] Decide controlled vs uncontrolled for three forms and defend each.
- [ ] A modal rendered in a portal closes when clicking inside it: trace the DOM and React event paths, then fix the containment/listener design without blanket `stopPropagation`.

## Related Notes

- [[21 - React Internals and Patterns/00 - React Internals and Patterns MOC|React Internals and Patterns MOC]]
- [[14 - JavaScript in React and Next.js/11 - React and Next Checklist|React and Next Checklist]]
- [[22 - Next.js Deep Dive/09 - Next.js Deep Dive Checklist|Next.js Deep Dive Checklist]]
- [[01 - Roadmap|Roadmap]]
