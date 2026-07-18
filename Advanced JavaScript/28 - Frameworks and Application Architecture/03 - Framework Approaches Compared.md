---
tags: [frameworks, react, angular, svelte, solid, architecture]
module: "28 - Frameworks and Application Architecture"
priority: important
status: not-started
aliases: [VDOM vs signals, React vs Angular vs Svelte]
verified_on: 2026-07-17
version_scope: "React 19, Angular 19/20 era, Svelte 5, SolidJS 1.x, Vue 3.5"
---

# Framework Approaches Compared

## Maturity Target

- Priority: #important
- Study time: 50 minutes
- Interview signal: Compare frameworks by *update model* (how does a state change become a DOM update?) rather than by syntax or popularity — VDOM diffing vs fine-grained signals vs compiled reactivity — with an honest tradeoff for each.
- Production signal: You can predict each model's failure modes (React re-render storms; signal graphs' dependency surprises) and evaluate a framework choice by team and product, not fashion.
- Dependencies: [[28 - Frameworks and Application Architecture/01 - The Problem Frameworks Solve|The Problem Frameworks Solve]], [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]]

## Source Anchors

- [React - Render and Commit](https://react.dev/learn/render-and-commit)
- [Angular - Signals](https://angular.dev/guide/signals)
- [SolidJS - Fine-Grained Reactivity](https://docs.solidjs.com/advanced-concepts/fine-grained-reactivity)
- [Svelte 5 - Runes](https://svelte.dev/docs/svelte/what-are-runes)

## 1. Concept

Simple version: all frameworks implement `UI = f(state)`; they differ in *how they find out what changed* and *how much work they redo*. Three families:

**1. VDOM re-render + diff (React; Vue partially).** On state change, re-run the component function → new element tree → diff against previous → patch DOM ([[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation]]). Change detection is *coarse*: React doesn't know what changed inside your state, it re-derives everything below the changed component and diffs.
   - Cost model: CPU on re-render + diff; correctness needs referential-equality discipline ([[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]).
   - Failure mode: re-render storms from unstable props/context; fixed by memoization or, in React 19+, the **React Compiler** auto-memoizing — an admission that manual memo was the tax of this model.

**2. Fine-grained signals, no VDOM (SolidJS; Vue's reactivity core; now Angular & Svelte 5).** State is **signals** — reactive containers that *track which computations read them*. Components run **once** to build the DOM; template expressions subscribe to exactly the signals they read. A signal write updates exactly the text nodes/attributes that depend on it. No re-render, no diff.
   - Cost model: dependency-graph bookkeeping per signal; near-optimal updates.
   - Failure mode: reactivity is *opt-in per read* — destructure a signal (`const { name } = user()`) and you've read it once and lost tracking; conditional reads change the dependency graph at runtime. Mental model shifts from "everything re-runs" to "only tracked reads update."

**3. Compiler-heavy (Svelte; Angular AOT; React Compiler as convergence).** Push work from runtime to build: Svelte 5 compiles rune-annotated code (`$state`, `$derived`) into direct signal-wired DOM updates — the framework mostly *disappears* from the bundle. Angular compiles templates AOT and pairs **zoneless change detection** with signals, layered on its full-platform design: DI, RxJS, router, forms included.

```tsx
// The same counter, three update models:
// React: setCount re-runs Counter, diffs <span>, patches text
function Counter() { const [n, setN] = useState(0);
  return <button onClick={() => setN(n + 1)}><span>{n}</span></button>; }
```

```tsx
// Solid: Counter runs ONCE; only the text node updates on n()
function Counter() { const [n, setN] = createSignal(0);
  return <button onClick={() => setN(n() + 1)}><span>{n()}</span></button>; }
```

```svelte
<!-- Svelte 5: compiler wires $state to the exact DOM mutation -->
<script> let n = $state(0); </script>
<button onclick={() => n++}><span>{n}</span></button>
```

The 2020s convergence is the headline: **everyone is moving toward signals + compilers** — Vue had it, Solid proved it, Angular and Svelte adopted it, React chose the compiler half while keeping its re-render semantics.

## 2. Why It Matters

- "How is Angular/Svelte different from React?" answered at the update-model level is a senior answer; answered at the syntax level ("Angular uses templates") is a junior one.
- The models explain each ecosystem's idioms: React's memoization culture, Solid's "don't destructure props" rule, Angular's `OnPush`→signals journey, Svelte's tiny bundles.
- Framework choice is a *team and product* decision: React's ecosystem/hiring pool, Angular's batteries-included consistency for large orgs, Solid/Svelte's performance ceiling for interaction-heavy UIs.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

The same bug, two models — a live-updating price ticker:

```tsx
// React: parent re-renders 10×/sec; EVERY row re-renders even though
// only one price changed — unstable callback prop defeats memo.
<Row key={r.id} data={r} onSelect={() => select(r.id)} />   // new fn identity each render
```

Trace (VDOM model): coarse invalidation — parent re-render re-creates all children's props; `memo` bails out only on shallow-equal props, and the inline closure breaks it. Fix: stable callbacks (`useCallback`/item-level handlers) or React Compiler. The *model* made you do identity bookkeeping.

```tsx
// Solid: same UI — rows never re-run; each price cell subscribes to its own signal.
// The equivalent bug can't happen… but a different one can:
const [user] = createResource(fetchUser);
const { name } = user() ?? {};        // ❌ read once, tracking lost
return <span>{name}</span>;           // never updates when user() resolves
```

Trace (signal model): fine-grained invalidation — but only *tracked reads inside reactive scopes* update. Destructuring reads eagerly, outside any tracking context. Fix: keep reads in the JSX/`createMemo` (`<span>{user()?.name}</span>`).

Tradeoffs, honestly: VDOM buys "just JavaScript, re-run everything" simplicity and pays in identity discipline and CPU; signals buy minimal updates and pay in read-tracking discipline and a subtler mental model. Neither is free — the discipline just moves.

## 4. Interview Answer

Short answer:

> Frameworks differ in their update model. React re-runs component functions and diffs a virtual DOM — coarse-grained, simple mental model, but you manage referential equality and memoization, which the React Compiler now automates. Solid — and now Angular and Svelte 5 via signals — track which expressions read which state, run components once, and update exactly the affected DOM nodes with no diffing. Svelte and Angular also lean on compilation to move framework work to build time. The industry is converging on signals plus compilers from different directions.

Deeper answer:

> Tradeoffs per family: VDOM's costs are re-render CPU and identity bugs (unstable props defeating memo), its win is that plain JavaScript semantics apply. Signals' costs are read-tracking rules — destructuring breaks reactivity, dependencies are dynamic — their win is near-optimal updates without memoization. Angular is less an update model than a platform: DI, router, forms, RxJS conventions — its value is consistency at organizational scale, its cost is framework surface area. And the choice is rarely performance-first: ecosystem, hiring, SSR story, and team experience dominate for most products.

## 5. Practice

1. <details><summary>Why does React need `memo`/`useCallback` while Solid doesn't have an equivalent culture?</summary>React's invalidation is per-component-subtree: a parent re-render re-runs children unless memo + stable props stop it, so identity management is load-bearing. Solid's components run once; updates flow through signal subscriptions directly to DOM nodes — there's no re-render to prevent, hence nothing to memoize at the component level.</details>
2. <details><summary>In a signals framework, why does `const { name } = props.user` (or `user()`) break updates, and what's the rule?</summary>Destructuring performs the read immediately, once, outside a tracking scope — the extracted value is a snapshot with no subscription. Rule: keep signal reads inside reactive contexts (JSX expressions, effects, memos) so the tracking system records the dependency.</details>
3. <details><summary>What does the React Compiler concede about the VDOM model, and what does it *not* change?</summary>It concedes that manual memoization was a systematic tax of coarse re-rendering — the compiler auto-memoizes components and values. It does not change the semantics: React still re-renders and diffs; it doesn't become fine-grained. Rules-of-React violations still break it.</details>

## Related Notes

- [[21 - React Internals and Patterns/01 - Render and Commit Phases|Render and Commit Phases]]
- [[21 - React Internals and Patterns/02 - Reconciliation and Keys|Reconciliation and Keys]]
- [[14 - JavaScript in React and Next.js/05 - Referential Equality|Referential Equality]]
- [[28 - Frameworks and Application Architecture/04 - Meta-Frameworks|Meta-Frameworks]]
