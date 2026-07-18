---
tags: [testing, mocking, test-doubles]
module: "24 - Testing and Quality"
priority: must-know
status: not-started
aliases: [mocks, test doubles, seams]
---

# Mocking: Seams and False Confidence

## Maturity Target

- Priority: #must-know
- Study time: 45-60 minutes
- Interview signal: explain where a mock belongs (real boundaries you don't own or can't control) and how over-mocking produces green suites over broken apps.
- Production signal: your mocks stand in for networks, clocks, and randomness — not for your own logic.
- Dependencies: [[24 - Testing and Quality/01 - Testing Mental Model|Testing Mental Model]], [[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|MSW]]

## Source Anchors

- [Vitest: Mocking guide](https://vitest.dev/guide/mocking.html)
- [Vitest: vi.mock API](https://vitest.dev/api/vi.html#vi-mock)
- [MSW: Comparison — mock vs intercept](https://mswjs.io/docs/comparison)
- [Martin Fowler: Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html)

## 1. Concept — Every Mock Removes Code From the Test

A test double replaces something real; whatever it replaces is, by definition, no longer tested *and* is now *asserted to behave as you guessed*. So each mock is a bet: "this seam's real behavior is well-understood, stable, and not what this test is about." Good bets sit at genuine boundaries:

- **Nondeterminism**: clock (`vi.useFakeTimers` — [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|timers]]), `Math.random`, `crypto.randomUUID`.
- **The network**: at the request level (MSW), so your own fetch/parse/error code stays tested ([[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|MSW]]).
- **Expensive/external effects**: payment SDKs, analytics, email — things a test must not really do.
- **Server-only seams in direct-invocation tests**: session/db in Server Action tests ([[24 - Testing and Quality/08 - Testing Nextjs Boundaries|Next boundaries]]).

Bad bets replace *your own code*: mocking your `utils/`, your components' children, your state store — the collaboration between your units is usually exactly what's under test.

Vocabulary that keeps designs honest: a **stub** supplies canned answers (state verification: assert outcomes); a **mock** records calls for interaction verification (assert "was called with"). Interaction verification couples the test to *how* the work is done — reserve it for cases where the call *is* the contract (an analytics event, `updateTag` after a mutation).

## 2. Why It Matters

- Over-mocked suites are the canonical false-confidence machine: every unit green, every seam guessed, integration broken. This is the #1 pathology of real-world test suites.
- The flip side is under-mocking nondeterminism — real timers and real randomness — which produces flake. The skill is placing the seam, not more/less mocking on a slider.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a checkout flow. The team mocks aggressively "for isolation":

```tsx
// Bug: everything interesting is mocked away.
vi.mock("./CartSummary", () => ({ CartSummary: () => <div>cart</div> }));
vi.mock("./useCheckout", () => ({
  useCheckout: () => ({ total: 4200, submit: vi.fn(), status: "idle" }),
}));

it("renders checkout and submits", async () => {
  render(<CheckoutPage />);
  await userEvent.click(screen.getByRole("button", { name: /pay/i }));
  // asserts... that the mocked submit was called. The real hook never ran.
});
```

Trace what's actually verified: a button calls a function the test itself provided, over children the test itself replaced. The real `useCheckout` had a bug — it computed `total` before applying the discount — and no test could ever see it. The suite verifies the *mocks' choreography*, a tautology.

```tsx
// Fix: mock only the genuine boundaries — network (MSW) and clock. Everything else is real.
server.use(
  http.get("/api/cart", () => HttpResponse.json(cartWithDiscount)),
  http.post("/api/checkout", async ({ request }) => {
    capturedOrder = await request.json();               // observe what the app really sends
    return HttpResponse.json({ id: "order_1" });
  }),
);

it("charges the discounted total", async () => {
  render(<CheckoutPage />);                              // real hook, real children
  await userEvent.click(await screen.findByRole("button", { name: /pay/i }));
  await waitFor(() => expect(capturedOrder.totalCents).toBe(3780)); // 4200 − 10% — the bug is caught
  expect(await screen.findByText(/order confirmed/i)).toBeInTheDocument();
});
```

One request-level seam; the entire client pipeline — hook, math, serialization, UI states — is inside the tested surface, and the discount bug fails the test.

Tradeoffs: real collaborators mean slower tests (still ~100ms) and less pinpoint failures — acceptable, per the [[24 - Testing and Quality/01 - Testing Mental Model|mental model]], because behavior is what must not break. Legitimate child-mocking exists: a `<Map>` that needs WebGL, a rich-text editor with jsdom-incompatible internals — replace them *because the environment can't run them*, and say so in a comment, not "for isolation."

> [!warning] Mock drift: the quiet killer
> A hand-written mock encodes today's guess about a dependency's behavior. The dependency evolves; the mock doesn't; tests keep passing against an API that no longer exists. Defenses: prefer request-level interception with schema-validated contracts ([[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|boundary validation]] makes drift loud in staging), keep `vi.mock` factories minimal and typed (`satisfies` the real module's type so signature drift is a compile error), and let a thin E2E layer arbitrate the truth ([[24 - Testing and Quality/06 - Integration vs End-to-End Tests|allocation]]).

## Real-World Use Cases

### Analytics events — the case where "was called with" IS the contract

A product team ships funnel dashboards off `track("checkout_started", {...})` events. There's no rendered output to assert — the call itself is the deliverable, so interaction verification is correct here:

```ts
vi.mock("@segment/analytics-next", () => ({
  analytics: { track: vi.fn() } satisfies Partial<typeof import("@segment/analytics-next").analytics>,
}));

it("fires checkout_started with the cart value", async () => {
  render(<CheckoutPage />);
  await userEvent.click(await screen.findByRole("button", { name: /pay/i }));
  expect(analytics.track).toHaveBeenCalledWith("checkout_started",
    expect.objectContaining({ valueCents: 3780 }));
});
```

This is the mock/stub distinction from section 1 in the wild: the event name and payload are a contract with the data team, so asserting the call is asserting behavior, not implementation.

### Stripe SDK — the boundary you must never really call

Payment tests replace `@stripe/stripe-js` because a test must not create real charges. The discipline: mock the SDK's documented surface only (`confirmPayment` resolving `{ error }` or `{ paymentIntent }`), and let your own retry, error-mapping, and UI-state code run for real. Both failure shapes get a test — Stripe's error object drives your user-facing messages, and guessing it wrong is exactly the mock-drift trap the warning above describes.

### The flaky ID collision that only unmocked randomness caught

A list component generated row keys with `Math.random().toString(16).slice(2, 6)` — four hex chars. Unit tests (randomness stubbed) were green forever; a property-style test that ran the real generator 10,000 times caught duplicate keys in one run. The seam placement lesson cuts both ways: stub randomness to make behavior deterministic, but keep one test where the real entropy runs if uniqueness is the requirement.

> [!tip]
> When a mock stands in for randomness, add the inverse test: real source, assert the *property* (uniqueness, range, format) rather than the value — see [[24 - Testing and Quality/02 - Pure JavaScript Unit Tests|Pure JavaScript Unit Tests]].

## 4. Interview Answer

Short answer:

> A mock removes code from the tested surface and replaces it with my guess, so I mock only genuine boundaries: the clock and randomness (determinism), the network at request level with MSW (so my own fetch/error/parsing code still runs), and external effects like payments that a test must not really perform. I don't mock my own modules or child components — the collaboration between my units is usually what the test exists to verify.

Deeper answer:

> The two failure modes are false confidence — over-mocked suites verifying their own choreography while the real integration is broken — and mock drift, where a hand-written double diverges from the evolved dependency and tests pass against an API that no longer exists. Defenses: typed mock factories (`satisfies typeof import(...)` turns signature drift into a compile error), request-level contracts validated by the same schemas the app uses at runtime, and a small E2E layer as the arbiter. I also separate stubbing (canned state, assert outcomes) from interaction verification (assert calls) and use the latter only where the call is itself the contract — analytics, cache invalidation — because "was called with" couples tests to implementation.

## 5. Practice

1. <details><summary>For each, mock or not: (a) `Date.now` in a "session expires" test, (b) your `formatCurrency` util inside a component test, (c) the Stripe JS SDK, (d) a `<RichTextEditor>` child that crashes in jsdom.</summary>(a) Mock (fake timers) — nondeterminism is the textbook seam. (b) No — it's your logic; letting it run tests the integration for free (it has its own unit tests for edge cases). (c) Mock — external effect you must not really perform; assert your code's interaction with its documented API. (d) Replace with a minimal stand-in *because the environment can't run it* — an environmental constraint, documented in a comment, plus a real-browser test elsewhere covering the editor integration.</details>

2. <details><summary>What does `vi.mock("./api", () => ({...}) satisfies typeof import("./api"))`-style typing buy you?</summary>Compile-time drift detection: if the real module adds a parameter, renames an export, or changes a return type, the mock factory no longer satisfies the module's type and the *build* fails — instead of tests silently passing against a stale shape. It converts the quietest mocking failure (drift) into the loudest signal (type error). It can't catch behavioral drift, only shape — contracts and E2E still cover semantics.</details>

3. <details><summary>A teammate asserts `expect(cartService.calculateTotal).toHaveBeenCalledTimes(1)` in a UI test. Interrogate it.</summary>Why is the call count the contract? If the concern is correctness, assert the displayed total — it survives refactors (memoizing, splitting the function) that break the call-count assertion without breaking behavior. If the concern is performance (expensive recomputation), a call-count test on a mocked service in a UI test is a weak proxy — profile or test the memoization directly. Interaction assertions on your own internals are almost always implementation coupling; save them for boundary contracts.</details>

4. <details><summary>How do you test code that uses `crypto.randomUUID()` for idempotency keys without mocking your own logic?</summary>Stub the randomness seam only: `vi.spyOn(crypto, "randomUUID").mockReturnValueOnce("test-uuid-1")`. Then assert the observable contract through the real code path — e.g., MSW captures two retried POSTs carrying the *same* idempotency key. The UUID source is nondeterministic (legitimate seam); the key's propagation through request logic is your code and stays real. Same pattern as the clock: stub the entropy, test the logic.</details>

## Related Notes

- [[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|Async UI, Network Boundaries and MSW]]
- [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Timers, Races, Cancellation and Deterministic Tests]]
- [[24 - Testing and Quality/08 - Testing Nextjs Boundaries|Testing Next.js Boundaries]]
- [[24 - Testing and Quality/01 - Testing Mental Model|Testing Mental Model]]
