---
tags: [frameworks, architecture, checklist]
module: "28 - Frameworks and Application Architecture"
priority: must-know
status: not-started
---

# Frameworks and Architecture Checklist

Use this checklist as an active test. Do not mark an item complete because you read it once. Mark it complete when you can explain, predict, debug, and refactor without looking.

## Source Anchors

- [React - Thinking in React](https://react.dev/learn/thinking-in-react)
- [Feature-Sliced Design](https://feature-sliced.design/)
- [TanStack Query - docs](https://tanstack.com/query/latest)

## The Problem Frameworks Solve

- [ ] I can state the M×N state–UI sync argument and trace the forgotten-update bug in imperative code.
- [ ] I can explain `UI = f(state)` and what reconciliation replaces.
- [ ] I can name when a framework is overkill and why (no shared mutable state → no sync problem).

## Web Components

- [ ] I can name the three specs and write a minimal custom element with shadow DOM and a slot.
- [ ] I can explain attributes-vs-properties and `bubbles`/`composed` for events crossing the shadow boundary.
- [ ] I can give the fair account: encapsulation/interop problem — not the state-sync problem — and where WCs win (design systems, embeds).

## Framework Approaches

- [ ] I can compare update models: VDOM re-render+diff vs fine-grained signals vs compiled reactivity.
- [ ] I can name each model's characteristic bug (identity-broken memo vs destructured-signal tracking loss).
- [ ] I can describe the convergence: signals in Angular/Svelte/Vue, compiler in React.
- [ ] I can argue a framework choice from team/product constraints, not benchmarks.

## Meta-Frameworks

- [ ] I can list what a meta-framework owns beyond the UI library: routing, rendering strategy, data loading, mutations, build/deploy.
- [ ] I can contrast Next (server-first, RSC, caching) with Remix/RR7 (web standards, loaders/actions) and Astro (islands).
- [ ] I can say when a plain Vite SPA is the right call, and what Redwood's failure teaches.

## State Management

- [ ] I can classify state: local, lifted, shared/context, global store, server, URL — with the two questions (who reads/who writes).
- [ ] I can explain why context isn't a state manager (no selectors) and when it's exactly right.
- [ ] I can contrast Redux (event log), Zustand (selector store), Jotai (atom graph) by model, not popularity.
- [ ] I can spot the smells: server data in a client store; derived state stored; URL state in useState.

## Server State

- [ ] I can argue that server data is a cache: keys/identity, staleness, invalidation, lifecycle.
- [ ] I can list what useEffect-fetching lacks: dedupe, cache, races, retries, invalidation.
- [ ] I can design query keys that include their parameters and explain the race that prevents.
- [ ] I can implement optimistic update with rollback and say when not to.

## Component Design

- [ ] I can diagnose prop explosion and rebuild a config-API component as compound parts.
- [ ] I can wire the pattern: parent context + memoized value + guarded consumer hook + `Parent.Part`.
- [ ] I can place the alternatives: children/slots, render props, headless hooks — with one use case each.

## Application Architecture

- [ ] I can state each architecture's slicing axis: Atomic (visual), Clean (distance from I/O), FSD (business domain).
- [ ] I can recite FSD's two load-bearing rules: downward imports, per-slice public API — and what enforces them.
- [ ] I can explain why type-based folders fail (no dependency rule) and plan an incremental FSD migration.
- [ ] I can argue when each architecture is the *wrong* choice.

## Exit Test

- [ ] Whiteboard "why React over vanilla JS?" from the sync problem, without saying "reusable components" first.
- [ ] Given six pieces of state in a feature spec, classify each and defend the homes in 2 minutes.
- [ ] Design a reusable Modal API live: compound parts, controlled/uncontrolled, a11y hooks.
- [ ] Sketch the folder structure for a 15-dev e-commerce app and state the import rules that make it stick.
- [ ] Answer "Angular vs React?" with update models and org tradeoffs — no tribalism.

## Related Notes

- [[28 - Frameworks and Application Architecture/00 - Frameworks and Application Architecture MOC|Frameworks and Application Architecture MOC]]
- [[21 - React Internals and Patterns/13 - React Internals Checklist|React Internals Checklist]]
- [[01 - Roadmap|Roadmap]]
