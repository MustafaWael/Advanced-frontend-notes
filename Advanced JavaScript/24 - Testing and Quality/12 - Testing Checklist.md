---
tags: [testing, checklist]
module: "24 - Testing and Quality"
priority: must-know
status: not-started
---

# Testing Checklist

Use this checklist as an active test. Mark an item complete only when you can explain, predict, debug, and refactor without looking.

## Source Anchors

- [Vitest documentation](https://vitest.dev/guide/)
- [Testing Library documentation](https://testing-library.com/docs/)
- [MSW documentation](https://mswjs.io/docs/)
- [Playwright documentation](https://playwright.dev/docs/intro)

## Mental Model

- [ ] I can judge a test by confidence, cost, and failure signal — and say why coverage is a floor-finder, not a target.
- [ ] I can push a given failure class to the cheapest layer that reliably detects it.
- [ ] I can explain why a flaky test is worse than a missing one.

## Unit and Component

- [ ] I can derive unit-test cases from a function's hazards: boundaries, invalid input, representation traps, policies.
- [ ] I can write a component test that queries by role/name, interacts with `userEvent`, and asserts visible outcomes.
- [ ] I can explain `getBy` vs `queryBy` vs `findBy` and `toBe` vs `toEqual` as different claims.
- [ ] I can say when testing a hook directly is justified and why it never replaces one integrated behavior test.

## Async, Timers and Races

- [ ] I can test loading → success and loading → error flows with MSW and per-test handler overrides.
- [ ] I can test a debounce boundary exactly (nothing at N−1 ms, fires at N) with fake timers.
- [ ] I can force an out-of-order response interleaving to pin a race-condition fix.
- [ ] I can assert that unmount aborts the in-flight request (AbortController cleanup).
- [ ] I can replace any sleep in a test with the condition it was approximating.

## Integration, E2E and Playwright

- [ ] I can draw the integration/E2E line by "what is real" and allocate failure classes across it.
- [ ] I can explain auto-waiting, web-first assertions, and why extracted-value assertions race.
- [ ] I can design fixture-owned test data and storageState auth for a parallel-safe suite.
- [ ] I can diagnose a CI-only failure from a Playwright trace.

## Next.js and Mocking

- [ ] I can test an async Server Component feature by extraction: pure logic, sync view, thin shell, E2E for the pipeline.
- [ ] I can directly invoke a Server Action with hostile inputs and assert authN/authZ/validation *and* that the mutation didn't run.
- [ ] I can say which Next.js claims are unfalsifiable below E2E (caching, revalidation, streaming) and why.
- [ ] I can name the legitimate mock seams (clock, randomness, network edge, external effects) and the illegitimate ones (my own logic).
- [ ] I can explain mock drift and two defenses against it.

## Quality Gates

- [ ] I can state what typecheck, lint, format, tests, and build each uniquely catch.
- [ ] I can explain why `tsc --noEmit` must run in CI even though the dev server "works."
- [ ] I can map `no-floating-promises` and `exhaustive-deps` to the production bugs they prevent.

## Exit Test

- [ ] Design the full test plan for the debounced, cancellable, accessible search flow of [[17 - Practical Frontend Scenarios/09 - Debounced Search|Debounced Search]]: which claims at which layer, and why.
- [ ] Take the race-condition scenario from [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|module 17]] and write the test that fails before the fix and passes after.
- [ ] Review a colleague's over-mocked suite and rewrite one test to shrink the mocked surface while keeping determinism.
- [ ] Sketch the CI pipeline for a Next.js app and justify every stage and its position.

## Related Notes

- [[24 - Testing and Quality/00 - Testing and Quality MOC|Testing and Quality MOC]]
- [[17 - Practical Frontend Scenarios/00 - Practical Frontend Scenarios MOC|Practical Frontend Scenarios MOC]]
- [[18 - Revision Plans/01 - Complete Advanced JavaScript Checklist|Complete Advanced JavaScript Checklist]]
- [[01 - Roadmap|Roadmap]]
