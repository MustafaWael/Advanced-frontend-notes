---
tags: [testing, integration, e2e, strategy]
module: "24 - Testing and Quality"
priority: important
status: not-started
aliases: [integration tests, E2E]
---

# Integration vs End-to-End Tests

## Maturity Target

- Priority: #important
- Study time: 45-60 minutes
- Interview signal: draw the line between integration and E2E by *what is real*, and allocate failure classes to the cheapest reliable detector.
- Production signal: your E2E suite is small, critical-path-only, and trusted; everything it doesn't need to prove lives lower.
- Dependencies: [[24 - Testing and Quality/01 - Testing Mental Model|Testing Mental Model]], [[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|Async UI and MSW]]

## Source Anchors

- [Playwright: Best Practices](https://playwright.dev/docs/best-practices)
- [Testing Library: Guiding Principles](https://testing-library.com/docs/guiding-principles/)
- [web.dev: Pyramid or Crab? Finding a testing strategy that fits](https://web.dev/articles/ta-strategies)
- [Vitest: Browser Mode](https://vitest.dev/guide/browser/)

## 1. Concept — The Question Is "What Is Real?"

"Integration" and "E2E" are points on a dial of realness:

| Dimension | Component/Integration test | E2E test |
| --- | --- | --- |
| Browser | Simulated DOM (jsdom) or Vitest browser mode | Real browser (Chromium/Firefox/WebKit) |
| Network | MSW handlers (contract you wrote) | Real backend (staging/sandbox) or MSW at most |
| App boundary | A component tree, routed page, or feature | The deployed app through its URL |
| Auth/state | Injected/faked | Real session, real cookies |
| Speed / stability | ~100ms, stable | seconds, inherently flakier |

An **integration test** proves *your* units cooperate: form + validation + submit flow + client cache render the right states, against a network contract you control. An **E2E test** proves *the system* works: real browser, real HTTP, real backend behavior including auth, CORS ([[20 - Network and Security/03 - CORS Correctly Explained|CORS]]), cookies ([[20 - Network and Security/04 - Cookies and Auth Patterns|auth patterns]]), caching ([[22 - Next.js Deep Dive/02 - The Caching Layers|Next caching]]), redirects, and deployment config.

Allocation rule: **a failure class belongs to the cheapest layer that can reliably produce it.** Form validation permutations — integration (fast, no real server needed to prove client behavior). "Login sets the session cookie and protected pages render" — E2E (the bug space *is* the integration: Set-Cookie flags, proxy redirects, session storage). "Checkout charges the card" — E2E against a payment sandbox; nothing lower can prove it.

The E2E suite should read like the product's list of unacceptable embarrassments: sign up, log in, core workflow, pay. Ten-ish scenarios, not hundreds. Everything else has a cheaper detector.

## 2. Why It Matters

- Teams fail in both directions: all-unit suites that pass while the integrated app is broken ("all gears verified, machine doesn't turn"), and thousand-test E2E suites that take an hour, flake constantly, and get ignored. The allocation skill is what interviews probe with "how would you test this feature?"
- The boundary also decides *debuggability*: an integration failure points at your code; an E2E failure could be code, data, environment, or the test. Reserve the vague-signal tool for claims only it can make.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a team puts "all 24 form-validation cases" into Playwright E2E. The suite takes 40 minutes; two cases flake weekly. Meanwhile a login redirect-loop bug (misconfigured cookie `SameSite` on the staging domain) ships — there was no E2E slot spent on auth.

```ts
// Wrong allocation: browser + backend + network for a client-only claim
test("shows error for invalid expiry month", async ({ page }) => {
  await page.goto("/checkout");                       // full stack boot...
  await page.getByLabel("Expiry").fill("13/28");      // ...to test a regex
  await expect(page.getByRole("alert")).toContainText("Invalid month");
});
```

Fix — reallocate by failure class:

```tsx
// The 24 validation cases: integration tests, ~2s total, no flake surface
it.each(invalidExpiryCases)("rejects %s", async (value, message) => {
  const user = userEvent.setup();
  render(<CheckoutForm />);
  await user.type(screen.getByLabelText(/expiry/i), value);
  await user.tab();                                    // blur triggers validation
  expect(await screen.findByRole("alert")).toHaveTextContent(message);
});
```

```ts
// The freed E2E budget: claims only E2E can make
test("login persists across navigation and protects /account", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(user.email);
  await page.getByLabel(/password/i).fill(user.password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/account/);           // real cookie, real redirect
  await page.reload();                                 // session survives reload
  await expect(page.getByRole("heading", { name: /account/i })).toBeVisible();
});
```

The cookie-flag bug is now inside a tested surface, and the validation cases run three orders of magnitude faster with exact failure signals.

Tradeoffs: integration tests inherit the fidelity limits of their environment — jsdom has no real layout, no real navigation; MSW handlers can drift from the real API. That residual risk is exactly what the small E2E layer covers. The two layers are complements: integration for breadth, E2E for the truth of the seams.

> [!tip] When jsdom fidelity runs out
> Focus traps, scroll behavior, sticky headers, `IntersectionObserver`-driven UI ([[19 - DOM and Browser APIs/06 - Observers|observers]]) — jsdom fakes or omits these. Before promoting such a test all the way to full E2E, consider a real-browser *component* runner (Vitest browser mode, Playwright component testing): real rendering engine, still no backend. The dial has more positions than its two endpoints.

## 4. Interview Answer

Short answer:

> Integration tests prove my units cooperate — component trees against a controlled network contract, fast and precise. E2E tests prove the system works — real browser, real backend, real auth/cookies/caching. I allocate by failure class to the cheapest reliable detector: validation permutations are integration; login, payment, and the handful of critical paths are E2E. The E2E suite stays small enough to stay trusted.

Deeper answer:

> The dial is "what is real": DOM, network, backend, session. Each step toward real buys fidelity and costs speed, stability, and failure-signal precision — an E2E failure could be anywhere in the stack. So E2E spends its slots only on claims about the seams themselves: Set-Cookie flags, redirects, CORS, cache invalidation after mutation. Integration's residual risk is contract drift (my MSW handlers vs the real API) and environment fidelity (jsdom has no layout) — the first is covered by boundary validation and the E2E layer, the second by real-browser component runners before jumping to full E2E.

## 5. Practice

1. <details><summary>Allocate: (a) "cart badge updates when items are added," (b) "user stays logged in after browser restart," (c) "price formats per locale."</summary>(a) Integration — component tree + state, no real backend needed; the claim is about your UI logic. (b) E2E — the claim is about real cookie persistence attributes and session handling across real browser lifecycles; use Playwright's storage state/context restart. (c) Unit — pure `Intl.NumberFormat` logic, a table of locales in milliseconds ([[12 - Advanced Language Concepts/16 - Intl|Intl]]).</details>

2. <details><summary>Your integration tests all pass but staging is broken: the API returns `snake_case`, your MSW handlers used `camelCase`. What does this failure teach?</summary>Handler drift: integration tests verify against *your claim* about the contract, and the claim was wrong. Mitigations: generate handler types from the API's OpenAPI/schema, validate real responses at the boundary with the same schema types ([[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|runtime validation]]) so drift fails loudly in staging, and keep at least one E2E path per contract area. Integration and E2E are complements precisely because of this failure mode.</details>

3. <details><summary>Why does an E2E suite degrade as it grows, in a way integration suites mostly don't?</summary>Each E2E test multiplies real-world nondeterminism (network, backend state, animations, shared test data) — so flake probability compounds with suite size, wall time grows linearly at seconds per test, and failures need human triage since the signal is vague. Past a threshold, the suite stops gating merges in practice. Integration tests add milliseconds and fail precisely, so they scale to thousands. This asymmetry is *why* allocation matters, not just taste.</details>

4. <details><summary>You need to verify "after the admin updates a price, the product page shows it without redeploy" in a Next.js app. Which layer, and why?</summary>E2E — the claim is about the deployed caching/revalidation pipeline: Data Cache, tags, `updateTag`/`revalidateTag`, CDN behavior ([[22 - Next.js Deep Dive/03 - Revalidation|revalidation]]). No lower layer runs that stack for real. Design it deterministically: dedicated test product, explicit wait on the new price text, cleanup after. This is exactly the kind of seam-truth claim the small E2E budget exists for.</details>

## Related Notes

- [[24 - Testing and Quality/01 - Testing Mental Model|Testing Mental Model]]
- [[24 - Testing and Quality/07 - Playwright Workflows|Playwright Workflows]]
- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
- [[22 - Next.js Deep Dive/03 - Revalidation|Revalidation]]
