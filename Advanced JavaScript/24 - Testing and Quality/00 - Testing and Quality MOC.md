---
tags: [testing, moc, quality]
module: "24 - Testing and Quality"
priority: must-know
status: not-started
---

# Testing and Quality MOC

This module teaches testing as an engineering decision: what failure a test can detect, what it costs to maintain, and how much confidence it actually buys. It reuses the failure modes taught earlier — race conditions ([[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|module 14]]), stale closures, cancellation ([[08 - Async JavaScript/06 - AbortController|AbortController]]), cache staleness ([[22 - Next.js Deep Dive/02 - The Caching Layers|module 22]]) — and shows how to pin each one down with a deterministic test. Tools referenced: Vitest, Testing Library, MSW, Playwright.

## Prerequisites

- [[08 - Async JavaScript/00 - Async JavaScript MOC|Async JavaScript]] — most flaky tests are async misunderstandings.
- [[21 - React Internals and Patterns/00 - React Internals and Patterns MOC|React Internals]] — you can't test render behavior you can't predict.
- [[23 - TypeScript Deep Dive/00 - TypeScript Deep Dive MOC|TypeScript Deep Dive]] — types and tests split the quality work between them.

## Reading Order

1. [[24 - Testing and Quality/01 - Testing Mental Model|Testing Mental Model]] — confidence, cost, and failure signals.
2. [[24 - Testing and Quality/02 - Pure JavaScript Unit Tests|Pure JavaScript Unit Tests]] — Vitest, edge cases, what's worth a unit test.
3. [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|React Component Testing Through User Behavior]] — Testing Library's model.
4. [[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|Async UI, Network Boundaries and MSW]] — findBy, waitFor, request-level mocking.
5. [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Timers, Races, Cancellation and Deterministic Tests]] — fake timers, testing the module 08/14 failure modes.
6. [[24 - Testing and Quality/06 - Integration vs End-to-End Tests|Integration vs End-to-End Tests]] — where each failure class is caught cheapest.
7. [[24 - Testing and Quality/07 - Playwright Workflows|Playwright Workflows]] — critical paths, fixtures, web-first assertions, anti-flake discipline.
8. [[24 - Testing and Quality/08 - Testing Nextjs Boundaries|Testing Next.js Boundaries]] — Server Components, actions, route handlers, proxy logic.
9. [[24 - Testing and Quality/09 - Accessibility Testing|Accessibility Testing]] — automated checks and the manual half they can't do.
10. [[24 - Testing and Quality/10 - Mocking Seams and False Confidence|Mocking: Seams and False Confidence]] — useful seams, dangerous mocks.
11. [[24 - Testing and Quality/11 - Typecheck Lint Format and CI Gates|Typecheck, Lint, Format and CI Gates]] — the quality pipeline around the tests.
12. [[24 - Testing and Quality/13 - Frontend Observability and Error Reporting|Frontend Observability and Error Reporting]] — the after-shipping leg of quality: capture surfaces, context and source maps, RUM, alert discipline.
13. [[24 - Testing and Quality/12 - Testing Checklist|Testing Checklist]] — active self-test.

## You're Done When

- [ ] I can say what each test type (unit, component, integration, E2E) can and cannot detect, and pick per failure mode.
- [ ] I can test a debounced async search with fake timers, MSW, and cancellation — deterministically.
- [ ] I can write component tests that survive refactors because they assert user-visible behavior, not implementation.
- [ ] I can explain why a mock made a test pass while production failed, and where the seam should have been.
- [ ] I can keep a Playwright suite non-flaky and explain every anti-flake rule mechanically.
- [ ] I can design a CI quality gate (typecheck, lint, test, build) and defend its ordering and cost.

## Related Notes

- [[17 - Practical Frontend Scenarios/00 - Practical Frontend Scenarios MOC|Practical Frontend Scenarios]] — the bugs these tests are designed to catch.
- [[25 - Accessibility and Inclusive UX/00 - Accessibility and Inclusive UX MOC|Accessibility and Inclusive UX]]
- [[22 - Next.js Deep Dive/00 - Next.js Deep Dive MOC|Next.js Deep Dive]]
- [[01 - Roadmap|Roadmap]]
