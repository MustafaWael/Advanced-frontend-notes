---
tags: [testing, async, msw, network]
module: "24 - Testing and Quality"
priority: must-know
status: not-started
aliases: [MSW, findBy, waitFor]
verified_on: 2026-07-12
version_scope: "MSW 2.x, Testing Library"
---

# Async UI, Network Boundaries and MSW

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: test loading → success/error flows without real network, and explain why request-level mocking beats module-mocking fetch wrappers.
- Production signal: async tests are deterministic — no sleeps, no "increase the timeout," no flake.
- Dependencies: [[24 - Testing and Quality/03 - React Component Testing Through User Behavior|Component Testing]], [[08 - Async JavaScript/07 - API Integration Examples|API Integration]], [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling]]

## Source Anchors

- [MSW: documentation](https://mswjs.io/docs/)
- [MSW: Comparison with alternatives](https://mswjs.io/docs/comparison)
- [Testing Library: Async methods](https://testing-library.com/docs/dom-testing-library/api-async/)
- [Testing Library: user-event](https://testing-library.com/docs/user-event/intro/)

## 1. Concept

Async UI has observable *phases* — idle, loading, then data or error ([[23 - TypeScript Deep Dive/03 - Narrowing and Discriminated Unions|the discriminated union]] made visible). Testing it means controlling the network boundary and asserting each phase.

**MSW (Mock Service Worker)** intercepts requests at the network level: your app runs its real `fetch` code — real URL construction, headers, JSON parsing, error branches — and MSW answers. Contrast with `vi.mock("./api")`, which replaces your own module and silently exempts everything inside it from testing ([[24 - Testing and Quality/10 - Mocking Seams and False Confidence|mock seams]]).

```ts
// handlers.ts — the network contract, shared by tests and dev
import { http, HttpResponse, delay } from "msw";

export const handlers = [
  http.get("/api/users/:id", ({ params }) =>
    HttpResponse.json({ id: params.id, name: "Ada Lovelace" })
  ),
];
```

```tsx
// UserProfile.test.tsx
import { setupServer } from "msw/node";
server = setupServer(...handlers);   // beforeAll: listen, afterEach: resetHandlers, afterAll: close

it("shows a spinner, then the user", async () => {
  render(<UserProfile id="42" />);

  expect(screen.getByRole("status")).toBeInTheDocument();            // loading phase
  expect(await screen.findByText("Ada Lovelace")).toBeInTheDocument(); // findBy = retry until it appears
  expect(screen.queryByRole("status")).not.toBeInTheDocument();       // spinner gone
});

it("shows a recoverable error state on 500", async () => {
  server.use(http.get("/api/users/:id", () => HttpResponse.json(null, { status: 500 })));

  render(<UserProfile id="42" />);
  expect(await screen.findByRole("alert")).toHaveTextContent(/could not load/i);
  expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
});
```

The async toolkit, by contract:

- `findBy*` — "this element will appear": retries the query until timeout. The default for anything after an await point.
- `waitFor(cb)` — "this assertion will become true": retries arbitrary assertions. Use when there's no single element to find (e.g., a callback got called).
- `waitForElementToBeRemoved` — "this will disappear": the loading-spinner tool.
- Never `await new Promise(r => setTimeout(r, 100))` — a guess about timing that becomes a flake on slow CI and dead weight on fast machines.

## 2. Why It Matters

- Loading and error phases are where real apps embarrass themselves (spinners that never resolve, errors swallowed silently, [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|stale results]]). They only get tested if the test controls the network.
- Per-test handler overrides (`server.use`) make failure-path testing trivial — the 500, the timeout, the malformed payload. Untested error branches are the branches that page you at night ([[11 - Error Handling/06 - API Error Handling Patterns|error patterns]]).

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a test suite mocks the API module directly, and a URL bug ships.

```ts
// Bug: the app's real code builds the wrong URL...
export async function fetchUser(id: string) {
  const res = await fetch(`/api/user/${id}`);        // ❌ singular — server route is /api/users/:id
  if (!res.ok) throw new ApiError(res.status);
  return UserSchema.parse(await res.json());
}

// ...but the test replaces that entire module, so the bug is unreachable:
vi.mock("./api", () => ({ fetchUser: vi.fn().mockResolvedValue({ id: "42", name: "Ada" }) }));
```

Trace: `vi.mock` swaps out `fetchUser` wholesale — URL construction, `res.ok` handling, schema parsing are all skipped. Every test is green; production 404s on every profile.

```ts
// Fix: mock at the network boundary — the real fetchUser runs.
server.use(http.get("/api/users/:id", ({ params }) => HttpResponse.json({ id: params.id, name: "Ada" })));

it("loads the user", async () => {
  render(<UserProfile id="42" />);
  expect(await screen.findByText("Ada")).toBeInTheDocument();  // ❌ fails: request went to /api/user/42
});
```

With MSW, the unhandled `/api/user/42` request surfaces immediately (configure `onUnhandledRequest: "error"` to make this loud). The whole client-side pipeline — URL, status handling, parsing, state transitions — is inside the tested surface.

Tradeoffs: MSW handlers are more setup than a one-line module mock, and the handler set is itself a *claim about the server contract* that can drift from the real API — pair it with schema validation at the boundary ([[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|runtime validation]]) and a few E2E tests against a real backend ([[24 - Testing and Quality/06 - Integration vs End-to-End Tests|integration vs E2E]]). For genuinely non-network seams (a WebSocket wrapper, module-level config), module mocks remain the right tool.

> [!tip] Reuse the handlers beyond tests
> The same MSW handlers can run in the browser (service worker) for development without a backend, and in Storybook. One network contract, three consumers — and when the contract changes, one place to update.

## Real-World Use Cases

### Infinite scroll / "load more" pagination

Order history loads page 1, then appends page 2 on demand. The classic regression is *replacing* instead of *appending* — and because the MSW handler reads the real request URL, the page-param serialization your app does is inside the tested surface:

```ts
server.use(http.get("/api/orders", ({ request }) => {
  const page = Number(new URL(request.url).searchParams.get("page") ?? "1");
  return HttpResponse.json({ orders: pagesFixture[page - 1] ?? [], hasMore: page < 2 });
}));

it("appends page 2 below page 1 instead of replacing it", async () => {
  const user = userEvent.setup();
  render(<OrderHistory />);
  await screen.findByText("Order #1001");                       // page 1 rendered
  await user.click(screen.getByRole("button", { name: /load more/i }));
  await screen.findByText("Order #2001");                       // page 2 arrived
  expect(screen.getByText("Order #1001")).toBeInTheDocument();  // page 1 still present
});
```

If the app forgets to bump `page`, the handler serves page 1 twice and the `#2001` `findBy` times out — a module mock returning canned pages could never see that.

### Optimistic update with rollback

Liking a comment updates the count instantly, then rolls back if the POST fails. The test asserts *both phases* — possible only because the test decides how the network answers:

```tsx
it("rolls back the optimistic like when the server rejects", async () => {
  server.use(http.post("/api/comments/:id/like", () => HttpResponse.json(null, { status: 500 })));
  const user = userEvent.setup();
  render(<Comment comment={{ id: "c1", likes: 3 }} />);

  await user.click(screen.getByRole("button", { name: /like/i }));
  expect(screen.getByText("4")).toBeInTheDocument();                       // optimistic phase
  await waitFor(() => expect(screen.getByText("3")).toBeInTheDocument()); // rolled back
});
```

This is the phase model from section 1 with an extra state: idle → optimistic → confirmed *or* rolled back. The rollback branch is exactly the code that never runs in happy-path dev clicking.

### 401 → token refresh → transparent retry

A fetch wrapper is supposed to catch 401s, refresh the token once, and replay the request. Handlers that inspect real headers verify the interceptor actually attaches the new token:

```ts
let refreshCalls = 0;
server.use(
  http.get("/api/me", ({ request }) =>
    request.headers.get("authorization") === "Bearer fresh-token"
      ? HttpResponse.json({ name: "Ada" })
      : HttpResponse.json(null, { status: 401 })),
  http.post("/api/auth/refresh", () => {
    refreshCalls++;
    return HttpResponse.json({ token: "fresh-token" });
  }),
);

it("recovers from an expired token without surfacing an error", async () => {
  render(<AccountMenu />);
  expect(await screen.findByText("Ada")).toBeInTheDocument();  // retry succeeded
  expect(refreshCalls).toBe(1);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument(); // user never saw the 401
});
```

> [!warning] Test the single-flight guarantee too
> Two components fetching concurrently with an expired token should trigger *one* refresh, not two (the second invalidates the first's token on many backends). Render both, assert `refreshCalls === 1` — this pins the refresh-queue behavior, a cousin of [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|race-condition]] handling.

## 4. Interview Answer

Short answer:

> I mock at the network boundary with MSW, so the app's real fetch code — URLs, headers, status handling, parsing — executes in tests, and I override handlers per test to force 500s, timeouts, and malformed payloads. Assertions follow the UI phases: spinner appears, data replaces it (`findBy`), spinner is gone, or an alert with a retry appears. No sleeps — `findBy`/`waitFor` retry until the condition holds, which is deterministic.

Deeper answer:

> The reason network-level beats module-level mocking is the tested surface: `vi.mock('./api')` exempts your own integration code from testing, and that code — URL construction, error branching, schema parsing — is where bugs live. MSW keeps it inside the test while still eliminating the real network. Two residual risks I manage: handler drift from the real API (mitigated by boundary schema validation and a thin E2E layer) and unhandled requests passing silently (set `onUnhandledRequest: 'error'`). Error paths get first-class tests because per-test `server.use` overrides make them cheap.

## 5. Practice

1. <details><summary>`getByText` vs `findByText` vs `waitFor(() => getByText(...))` — when each?</summary>`getByText`: element must exist *now* — synchronous phases. `findByText`: element will appear — the default after any async trigger; it's exactly `waitFor` + `getBy` with better errors. Explicit `waitFor` is for assertions that aren't element queries (spy called, URL changed) or for grouping multiple assertions to retry together. If you're writing `waitFor(() => getByText(...))`, just use `findByText`.</details>

2. <details><summary>How do you test "the search box debounces and shows results for the LAST keystroke only"?</summary>Combine MSW with fake timers or a controllable delay: type "re", then "react" with `userEvent`; have the handler echo the query; assert results for "react" appear (`findByText`) and results for "re" never render (`queryByText` after settling). This pins the [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|race-condition]] fix — ignore/abort stale responses — at the UI level. Detailed timer mechanics: [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|deterministic tests]].</details>

3. <details><summary>Why should the "500 response" test assert on a retry button, not just the error text?</summary>The error text proves the failure was *displayed*; the retry button proves it was made *recoverable* — the actual UX requirement ([[11 - Error Handling/06 - API Error Handling Patterns|error patterns]]). A strong version continues: click retry, restore the success handler, assert data renders — proving the state machine exits the error state. Error-path tests should assert the contract of the error state, not merely its existence.</details>

4. <details><summary>What does `onUnhandledRequest: "error"` protect you from?</summary>Silent passthrough: a request your handlers don't match (typo'd URL, forgotten endpoint, an SDK phoning home) would otherwise hit the real network or fail invisibly, letting tests pass for the wrong reason — or flake in CI where the network differs. Failing loudly turns "the app requested something the contract doesn't define" into a test failure, which is precisely the URL-bug class module mocks can't catch.</details>

## Related Notes

- [[24 - Testing and Quality/05 - Timers Races Cancellation and Deterministic Tests|Timers, Races, Cancellation and Deterministic Tests]]
- [[08 - Async JavaScript/07 - API Integration Examples|API Integration Examples]]
- [[11 - Error Handling/06 - API Error Handling Patterns|API Error Handling Patterns]]
- [[23 - TypeScript Deep Dive/05 - unknown Runtime Validation and Boundaries|unknown, Runtime Validation and Boundaries]]
- [[24 - Testing and Quality/10 - Mocking Seams and False Confidence|Mocking: Seams and False Confidence]]
