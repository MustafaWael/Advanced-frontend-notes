---
tags: [testing, mental-model, strategy]
module: "24 - Testing and Quality"
priority: must-know
status: not-started
aliases: [testing trophy, test confidence]
---

# Testing Mental Model

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: reason about tests as confidence-per-cost, not coverage percentage; explain what signal a failing test should give.
- Production signal: your team's suite catches regressions you actually have, runs fast enough to be consulted, and rarely cries wolf.
- Dependencies: [[00 - Start Here|Start Here]] (the mechanism-first mindset applies to tests too)

## Source Anchors

- [Vitest: Why Vitest](https://vitest.dev/guide/why.html)
- [Testing Library: Guiding Principles](https://testing-library.com/docs/guiding-principles/)
- [Playwright: Best Practices](https://playwright.dev/docs/best-practices)
- [web.dev: Testing strategies](https://web.dev/articles/ta-strategies)

## 1. Concept — A Test Is a Failure Detector

A test is a machine that turns a class of bugs into a red signal before users see them. Judge every test by three properties:

- **Confidence**: if this passes, what am I entitled to believe? A unit test on `formatPrice` proves arithmetic and formatting; it says nothing about whether the price ever reaches the screen.
- **Cost**: writing, running, and — dominating everything long-term — *maintaining through refactors*. A test that breaks when behavior didn't change is negative-value: it trains people to ignore red.
- **Failure signal**: when it fails, how quickly does it tell you *what broke*? A unit test points at a function; an E2E failure points at "somewhere in the stack, possibly the test itself."

The classic layers trade these off:

| Layer                 | Proves                                      | Speed   | Failure signal | Fails falsely |
| --------------------- | ------------------------------------------- | ------- | -------------- | ------------- |
| Static (types, lint)  | Whole classes of bugs impossible            | instant | exact line     | almost never  |
| Unit                  | One function's logic                        | ms      | exact function | rarely        |
| Component/integration | Units cooperate; UI behaves per user action | ~100ms  | feature area   | sometimes     |
| E2E                   | The real stack works end to end             | seconds | "somewhere"    | most often    |

Two practical consequences. First, **push each failure class down to the cheapest layer that can catch it**: null-safety belongs to TypeScript ([[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|strictNullChecks]]), not to a test; pure logic belongs to unit tests; "does the form submit and show the success state" belongs to a component test; "does checkout work with the real backend" belongs to a handful of E2E paths. Second, **most frontend confidence lives in the middle**: component tests through user behavior hit the best confidence-per-cost for UI code (the "testing trophy" argument).

## 2. Why It Matters

- Interviewers ask "how would you test this?" to probe engineering judgment — the weak answer is a ritual ("write unit tests for everything, aim for 90% coverage"), the strong answer names the failure modes and picks detectors for them.
- Production incident postmortems constantly conclude "a test at layer X would have caught this" — knowing the layers means you can do that analysis *before* the incident.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a team has 94% coverage and still shipped a broken checkout. The bug: the submit button stayed disabled because a form-validity flag was inverted.

```ts
// The suite that missed it: implementation-detail unit tests.
it("sets isValid to false when validate() fails", () => {
  const form = new FormModel();
  form.validate = vi.fn().mockReturnValue(false);
  expect(form.isValid).toBe(false);   // ✅ passes — and asserts a tautology about internals
});
```

Trace: every function was tested in isolation against its own implementation, mocks stood in for every collaborator, and the one thing that mattered — *a user with valid input can submit* — was asserted nowhere. Coverage measured lines executed, not behaviors verified.

```tsx
// The detector that catches it: one behavior-level component test.
it("lets the user submit valid details", async () => {
  const user = userEvent.setup();
  render(<CheckoutForm />);
  await user.type(screen.getByLabelText(/card number/i), "4242424242424242");
  await user.type(screen.getByLabelText(/expiry/i), "12/28");
  expect(screen.getByRole("button", { name: /pay/i })).toBeEnabled();  // ❌ fails — bug found
});
```

Tradeoff: behavior tests are slower than micro-unit tests and localize failures less precisely (the assert says "submit is broken," not "flag inverted on line 40"). Accept that: the point of the suite is detecting broken *behavior*; you debug from the failing behavior inward. Keep micro-unit tests for genuinely complex pure logic where the precision pays.

> [!warning] Coverage is a floor-finder, not a target
> Coverage tells you what is *definitely untested*. It cannot tell you what is well tested — executing a line during a test with weak assertions counts the same as verifying it. Chasing a coverage number produces exactly the tautological suites that miss real bugs. Use it to find dark corners, never as a goal.

## Real-World Use Cases

### Allocating detectors before writing a feature: multi-step signup

You're about to build a 3-step signup wizard (account → profile → confirmation). Running the layer table *before* coding turns "write some tests" into an allocation:

```ts
// TypeScript: step-state discriminated union — step 2 can't render without step 1's data (compile-time)
// Unit:       validatePassword(), usernameToSlug() — pure rules, table-tested in milliseconds
// Component:  one test per user-visible transition:
it("carries the email from step 1 into the profile step", async () => {
  const user = userEvent.setup();
  render(<SignupWizard />);
  await user.type(screen.getByLabelText(/email/i), "ada@example.com");
  await user.click(screen.getByRole("button", { name: /continue/i }));
  expect(await screen.findByText("ada@example.com")).toBeInTheDocument();
});
// E2E (one): real signup against staging — the only place email verification is real
```

This is "push each failure class down to the cheapest layer" applied prospectively: wizards break in the wiring *between* steps, so the component test targets the transition, not `goToNextStep()` in isolation.

### CI budget renegotiation

The suite hits 20 minutes; teammates start merging without waiting. The fix isn't "delete tests" — it's re-reading the cost column and ordering gates so cheap detectors fail first:

```yaml
# ci.yml — fail-fast by cost, not by alphabet
jobs:
  static:          pnpm typecheck && pnpm lint        # ~1 min, whole bug classes
  unit-component:  pnpm vitest run                    # ~3 min, most of the confidence
  e2e:             pnpm playwright test --grep @critical  # ~6 min, a handful of flows only
```

Then demote: 20 form-validation E2E cases become component tests (same failure class, milliseconds each). Works because the layers are *substitutable per failure class* — the table tells you which demotions lose no confidence. See [[24 - Testing and Quality/11 - Typecheck Lint Format and CI Gates|CI Gates]] and [[24 - Testing and Quality/06 - Integration vs End-to-End Tests|Integration vs E2E]].

### Postmortem: converting an incident into the cheapest permanent detector

A feature-flag typo (`"new-chekout"`) silently disabled a launch — the flag lookup returned `undefined`, treated as off. The postmortem question "which layer should have caught this?" has a better answer than "add a test":

```ts
const FLAGS = { newCheckout: "new-checkout" } as const;
type FlagKey = keyof typeof FLAGS;
export function isEnabled(flag: FlagKey) { /* ... */ }   // the typo is now a compile error
```

The layer table isn't only for writing tests — sometimes the cheapest detector for an incident is a *type*, which runs instantly and never flakes ([[23 - TypeScript Deep Dive/08 - Modules tsconfig and Package Types|static layer]]).

> [!tip] Ask "which layer should catch this?" in code review, not just postmortems
> Reviewing a PR that adds retry logic? That's timer-controlled unit territory ([[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|deterministic tests]]). New API call? Component test over MSW ([[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|MSW]]). Running the allocation at review time is how the suite stays proportional to the risks.

## 4. Interview Answer

Short answer:

> I judge a test by confidence per cost: what failure class does it detect, how fast does it run, and does it survive refactors? Static analysis and types eliminate whole bug classes for free; unit tests own pure logic; component tests through user interactions carry most UI confidence; a few E2E tests prove the integrated critical paths. I push each failure class to the cheapest layer that can catch it.

Deeper answer:

> The dominant long-term cost is maintenance: tests coupled to implementation details break on every refactor without catching bugs, which erodes trust in red. So I assert user-visible behavior at component level, reserve mocks for real boundaries, and treat coverage as a tool for finding untested corners rather than a target — a high-coverage suite of tautologies happily ships a disabled checkout button. When production breaks, the postmortem question is "which layer *should* have caught this," and the suite evolves toward that.

## 5. Practice

1. <details><summary>Your team proposes "every function gets a unit test, 90% coverage gate." What do you push back with?</summary>The gate optimizes executed lines, not verified behaviors — it incentivizes tautological tests (mock all collaborators, assert the mock was called) that pass while behavior breaks. Counter-proposal: behavior-level component tests for UI, unit tests for genuinely complex pure logic, types/lint for whole bug classes, E2E for a few critical paths — plus coverage used diagnostically to find untested corners, not as a target number.</details>

2. <details><summary>Which layer should catch: (a) `parsePrice` mishandling "1.234,56", (b) submit staying disabled on valid input, (c) checkout failing against the real payment sandbox?</summary>(a) Unit — pure logic, needs a table of locale edge cases, milliseconds each. (b) Component test with Testing Library — user-visible behavior of one screen, no real backend needed. (c) E2E (Playwright) — only the integrated stack can prove it; it's a critical path, so it earns one of the few expensive slots.</details>

3. <details><summary>Why is a flaky test worse than a missing test?</summary>A missing test fails to detect one bug class. A flaky test corrodes the whole suite's signal: people retry until green, merge on red "because it's that test again," and eventually a real failure hides in the noise. Statistically it's a detector with unknown false-positive rate — you can no longer conclude anything from its output. Quarantine or fix flakes immediately.</details>

4. <details><summary>When is an E2E test the *wrong* tool even though it would catch the bug?</summary>When a cheaper layer detects the same failure: validating 20 form-field edge cases through a browser costs minutes per run and fails with vague signals, while a component test covers them in milliseconds each. E2E earns its cost only where integration itself is the risk — auth flows, payments, routing/caching interplay. The question is never "could E2E catch it" but "what's the cheapest reliable detector."</details>

## Related Notes

- [[24 - Testing and Quality/02 - Pure JavaScript Unit Tests|Pure JavaScript Unit Tests]]
- [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|React Component Testing Through User Behavior]]
- [[24 - Testing and Quality/06 - Integration vs End-to-End Tests|Integration vs End-to-End Tests]]
- [[24 - Testing and Quality/11 - Typecheck Lint Format and CI Gates|Typecheck, Lint, Format and CI Gates]]
- [[01 - Roadmap|Roadmap]]
