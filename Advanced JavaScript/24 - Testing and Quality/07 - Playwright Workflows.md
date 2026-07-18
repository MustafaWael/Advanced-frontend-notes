---
tags: [testing, playwright, e2e]
module: "24 - Testing and Quality"
priority: important
status: not-started
aliases: [Playwright, web-first assertions, fixtures]
verified_on: 2026-07-12
version_scope: "Playwright 1.5x"
---

# Playwright Workflows

## Maturity Target

- Priority: #important
- Study time: 60-90 minutes
- Interview signal: explain *mechanically* why Playwright tests flake and how auto-waiting, web-first assertions, fixtures, and isolation prevent it.
- Production signal: your E2E suite gates merges and the team trusts red.
- Dependencies: [[24 - Testing and Quality/06 - Integration vs End-to-End Tests|Integration vs E2E]], [[09 - Event Loop Advanced/06 - Rendering and UI Responsiveness|Rendering]]

## Source Anchors

- [Playwright: Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright: Auto-waiting / Actionability](https://playwright.dev/docs/actionability)
- [Playwright: Fixtures](https://playwright.dev/docs/test-fixtures)
- [Playwright: Authentication](https://playwright.dev/docs/auth)
- [Playwright: Locators](https://playwright.dev/docs/locators)

## 1. Concept

Playwright drives a real browser; the core discipline is the same as [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|component testing]] — locate like a user (`getByRole`, `getByLabel`), interact like a user, assert visible outcomes — plus three mechanisms that exist because real browsers are asynchronous all the way down:

**Auto-waiting (actionability).** `locator.click()` isn't "click now"; it's "wait until the element is visible, stable (not animating), enabled, and receives events — then click." Most legacy-Selenium flake ("element not interactable") is this check done manually and badly. Corollary: don't wrap actions in manual waits; the action *is* the wait.

**Web-first assertions.** `await expect(locator).toHaveText("Saved")` retries until it passes or times out — it's a *convergence claim* ("the UI will reach this state"), matching how UIs actually behave (async, eventually consistent). `expect(await locator.textContent()).toBe("Saved")` is a *snapshot claim* about one racy instant — the flake pattern. The rule: assert with `expect(locator)`, never on values you extracted first.

**Fixtures and isolation.** Each test gets a fresh browser context (cookies, storage, cache) — cross-test contamination is designed out. Fixtures compose setup declaratively:

```ts
// fixtures.ts — a logged-in page, reusable across the suite
export const test = base.extend<{ userPage: Page }>({
  userPage: async ({ browser }, use) => {
    const context = await browser.newContext({ storageState: "auth/user.json" }); // pre-saved session
    await use(await context.newPage());
    await context.close();
  },
});
```

Auth via `storageState` — log in once in a setup project, save cookies/localStorage, reuse everywhere — cuts both minutes of runtime and the flakiest step (UI login) out of every test.

## 2. Why It Matters

- E2E flake is the tax that makes teams abandon their most expensive tests. The causes are mechanical, not mystical: racy assertions, shared state, animation timing, test-order coupling — each with a specific cure.
- "How do you keep E2E stable?" is a senior interview staple because it separates people who've operated a suite from people who've written a tutorial's worth.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a "rename project" E2E test passes locally, fails ~10% in CI.

```ts
// Flaky version — three races and a dependency on another test
test("rename project", async ({ page }) => {
  await page.goto("/projects");
  await page.waitForTimeout(2000);                          // ① sleep: guess about load time
  await page.click(".project-card:first-child .menu-btn");  // ② CSS class + assumes "first" is
  await page.click("text=Rename");                          //    the project another test created
  await page.fill("#rename-input", "Q3 Roadmap");
  await page.click("text=Save");
  const name = await page.locator(".project-title").textContent();
  expect(name).toBe("Q3 Roadmap");                          // ③ snapshot read: races the re-render
});
```

Trace the three races: ① the sleep is sometimes shorter than a slow CI load; ② `:first-child` depends on data another test happened to create earlier (order coupling), and `.menu-btn` may be mid-animation when clicked; ③ `textContent()` reads once — if the optimistic UI hasn't reconciled or the save round-trip is slow, it reads the old name.

```ts
// Deterministic version — own your data, locate semantically, assert convergently
test("rename project", async ({ userPage: page, testProject }) => {   // fixture creates+deletes its own project
  await page.goto(`/projects/${testProject.id}`);

  await page.getByRole("button", { name: /project actions/i }).click();
  await page.getByRole("menuitem", { name: /rename/i }).click();
  await page.getByRole("textbox", { name: /project name/i }).fill("Q3 Roadmap");
  await page.getByRole("button", { name: /save/i }).click();

  await expect(page.getByRole("heading", { name: "Q3 Roadmap" })).toBeVisible(); // retries until true
});
```

Every fix is a named mechanism: fixture-owned data kills order coupling; `goto` + auto-waiting kills the sleep; role locators kill selector rot and double as an a11y check; the web-first assertion kills the snapshot race.

Tradeoffs: fixtures that create real data need teardown discipline (and an API/seed path — creating data through the UI in every test is slow and re-tests the same screens); `storageState` auth means the login flow itself must have its own dedicated test; and role locators require the app to have proper semantics — which, as with Testing Library, is a feature disguised as a constraint.

> [!warning] The forbidden list, and why
> `waitForTimeout` (a guess — see [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|sleeps]]); assertions on pre-extracted values (races the render); tests depending on other tests' data or order (parallel-unsafe, unrunnable alone); conditional flow (`if visible then click` — a test that adapts to the bug it should catch); CSS/XPath structural selectors (rot on every redesign). Each is banned because it converts a deterministic detector into a probabilistic one.

## 4. Interview Answer

Short answer:

> Playwright's stability comes from using its model fully: locators by role/label, actions that auto-wait for actionability (visible, stable, enabled), and web-first assertions that retry until the UI converges — plus per-test isolated contexts and fixtures that own their data. Flake almost always traces to breaking the model: sleeps, extracted-value assertions, shared or order-dependent data, structural selectors.

Deeper answer:

> I keep the suite small (critical paths — [[24 - Testing and Quality/06 - Integration vs End-to-End Tests|allocation]]), authenticate via a saved storageState from a setup project so UI login isn't re-run and re-flaked in every test, and create test data through an API fixture with teardown so tests are parallel-safe and runnable alone. Debugging is trace-first: Playwright's trace viewer records DOM snapshots, network, and console per step, so a CI failure is diagnosable without local reproduction. And a persistent flake is treated as a real bug with a mechanism to find — often it's the app's race, not the test's.

## 5. Practice

1. <details><summary>Why is `await expect(locator).toHaveText(x)` fundamentally different from `expect(await locator.textContent()).toBe(x)`?</summary>The first passes the *locator* to an assertion that re-queries and retries until match or timeout — a claim the UI converges to a state. The second awaits one DOM read, then compares a frozen string — a claim about a racy instant; if the render lands 10ms later, it fails. Same words, different semantics: convergence vs snapshot. Web-first assertions are the single biggest anti-flake lever.</details>

2. <details><summary>Design the auth strategy for a 50-test suite with three user roles.</summary>A setup project logs in once per role (admin, member, viewer) and saves three `storageState` JSON files; fixtures expose `adminPage`/`memberPage`/`viewerPage` creating contexts from those states. Tests never see the login UI except the dedicated login-flow tests. Wins: minutes of runtime, the flakiest flow removed from 50 tests, roles composable per test. Cost: state files must be refreshed when sessions expire — automate that in the setup project.</details>

3. <details><summary>A test needs a project with 3 tasks to exist. Compare creating it via UI clicks vs via API call in a fixture.</summary>UI creation re-executes (and re-flakes) the project-creation screens in every test that needs the data, costs seconds each, and couples this test to that UI's stability. API/seed creation is fast, deterministic, and scoped — with teardown in the fixture so parallel tests don't collide (unique names/ids per test). Rule: go through the UI only in the tests *about* that UI; everywhere else, arrange state by the fastest reliable path.</details>

4. <details><summary>CI shows a failure you can't reproduce locally. Walk your diagnosis.</summary>Open the trace (screenshots, DOM snapshots, network log, console per action) — it usually names the race: an assertion that read before convergence, a request that returned differently, an animation mid-flight. Check for test interdependence (run the test alone vs after its CI predecessors), environment differences (viewport, timezone, locale, CI throttling), and data collisions from parallel workers. If the trace shows the app briefly rendering a wrong state, you may have found a real product race ([[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|races]]) — the best kind of E2E catch.</details>

## Related Notes

- [[24 - Testing and Quality/06 - Integration vs End-to-End Tests|Integration vs End-to-End Tests]]
- [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Timers, Races, Cancellation and Deterministic Tests]]
- [[25 - Accessibility and Inclusive UX/09 - Accessibility Testing and Manual Checks|Accessibility Testing and Manual Checks]]
- [[20 - Network and Security/04 - Cookies and Auth Patterns|Cookies and Auth Patterns]]
