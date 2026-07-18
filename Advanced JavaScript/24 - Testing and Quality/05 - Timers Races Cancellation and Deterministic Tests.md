---
tags: [testing, timers, race-conditions, async]
module: "24 - Testing and Quality"
priority: must-know
status: not-started
aliases: [fake timers, deterministic tests, flaky tests]
verified_on: 2026-07-12
version_scope: "Vitest 3.x"
---

# Timers, Races, Cancellation and Deterministic Tests

## Maturity Target

- Priority: #must-know
- Study time: 60-90 minutes
- Interview signal: explain why time-dependent tests flake and how fake timers + explicit orchestration make them deterministic.
- Production signal: your suite pins the race-condition and cancellation fixes from modules 08/14/17 so they can't silently regress.
- Dependencies: [[09 - Event Loop Advanced/04 - Timers|Timers]], [[08 - Async JavaScript/06 - AbortController|AbortController]], [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]

## Source Anchors

- [Vitest: Fake Timers (vi.useFakeTimers)](https://vitest.dev/api/vi.html#vi-usefaketimers)
- [Vitest: Mocking timers guide](https://vitest.dev/guide/mocking.html#timers)
- [MDN: AbortController](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [Testing Library: user-event advanceTimers](https://testing-library.com/docs/user-event/options/#advancetimers)

## 1. Concept

A test is deterministic when its outcome depends only on its inputs — never on machine speed, scheduler moods, or wall-clock time. Time-dependent code (debounce, polling, timeouts, retry backoff) is deterministic in *logic* but nondeterministic in *when*, so tests must take control of "when."

**Fake timers** replace `setTimeout`/`setInterval`/`Date` with a virtual clock you advance explicitly:

```ts
import { vi, it, expect, beforeEach, afterEach } from "vitest";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

it("debounce fires once, with the last arguments, after the wait", () => {
  const spy = vi.fn();
  const debounced = debounce(spy, 300);          // from [[04 - Functions Deep Dive/07 - Debounce and Throttle|module 04]]

  debounced("a"); debounced("ab"); debounced("abc");
  vi.advanceTimersByTime(299);
  expect(spy).not.toHaveBeenCalled();            // boundary: not yet

  vi.advanceTimersByTime(1);
  expect(spy).toHaveBeenCalledExactlyOnceWith("abc");  // once, last args
});
```

No waiting 300 real milliseconds, no "maybe CI was slow" — the clock moves exactly when the test says. Key API distinctions: `advanceTimersByTime(n)` (move the clock n ms), `runAllTimers` (drain every pending timer — loops forever on `setInterval` unless bounded), `advanceTimersByTimeAsync` (also lets pending microtasks run between timers — needed when timer callbacks are async, because promise jobs and timer tasks interleave — [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|tasks vs microtasks]]).

**Races and cancellation** are tested by making the orchestration explicit — resolve promises in the order the bug requires:

```ts
it("ignores the stale response when a newer request supersedes it", async () => {
  const resolvers: Array<(v: unknown) => void> = [];
  server.use(http.get("/api/search", () => new Promise(r => resolvers.push(r))
    .then(v => HttpResponse.json(v))));           // requests hang until WE resolve them

  const user = userEvent.setup();
  render(<Search />);
  await user.type(screen.getByRole("searchbox"), "re");     // request #1 (hangs)
  await user.clear(screen.getByRole("searchbox"));
  await user.type(screen.getByRole("searchbox"), "react");  // request #2 (hangs)

  resolvers[1]({ results: ["react docs"] });     // #2 resolves FIRST
  expect(await screen.findByText("react docs")).toBeInTheDocument();

  resolvers[0]({ results: ["stale answer"] });   // #1 arrives LATE — the bug's trigger
  await waitFor(() => expect(screen.queryByText("stale answer")).not.toBeInTheDocument());
});
```

This *forces* the out-of-order arrival that only sometimes happens in production — turning "sometimes wrong search results" ([[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|race conditions]]) into a repeatable red/green signal. The AbortController variant asserts the abort itself: spy on the signal, or have the handler fail the test if a second un-aborted request completes ([[14 - JavaScript in React and Next.js/08 - AbortController in Effects|AbortController in effects]]).

## 2. Why It Matters

- Races, missed cleanups, and cancellation bugs are the highest-value things to pin with tests precisely *because* they're intermittent in production — a test that forces the bad interleaving is often the only reliable reproduction you'll ever have.
- Flaky tests are almost always unowned time: real timers, sleeps, ordering assumptions. Knowing the mechanics (virtual clock, microtask draining, explicit resolution order) is what separates "increase the timeout" from an actual fix.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a session-expiry warning appears 5 minutes before logout. Its test passes locally, fails on CI once a week.

```ts
// Bug: real time + sleep = machine-dependent
it("warns before expiry", async () => {
  render(<Session expiresInMs={600} warnBeforeMs={500} />);   // shrunk times to "make it testable"
  await new Promise(r => setTimeout(r, 150));                 // hope 150ms is enough...
  expect(screen.getByRole("alert")).toBeInTheDocument();      // flakes when CI stalls >100ms
});
```

Trace: the test races the component's real 100ms timer against its own real 150ms sleep. Any GC pause, CI throttling, or parallel-suite contention flips the order. The shrunken durations also mean the test no longer exercises production values.

```ts
// Fix: virtual clock, production values, boundary assertions
it("warns exactly 5 minutes before expiry", () => {
  vi.useFakeTimers();
  render(<Session expiresInMs={30 * 60_000} warnBeforeMs={5 * 60_000} />);

  vi.advanceTimersByTime(25 * 60_000 - 1);
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();  // one ms early: nothing

  vi.advanceTimersByTime(1);
  expect(screen.getByRole("alert")).toBeInTheDocument();        // exactly on time
});
```

Tradeoffs: fake timers virtualize the clock, so anything *actually* asynchronous-outside-the-clock (MSW responses, `userEvent` internal delays) can deadlock waiting for real time that never comes — configure `userEvent.setup({ advanceTimers: vi.advanceTimersByTime })` and use the async advance variants when mixing. Fake timers are global per test file, so mixing faked and real async in one test demands care. The discipline cost is real; the alternative is a suite whose red/green depends on the weather.

> [!warning] A sleep in a test is a confession
> `await new Promise(r => setTimeout(r, N))` says: "I don't know what I'm waiting for, so I'll wait N ms and hope." Every sleep is either too long (wasted suite time, forever) or too short (flake, eventually). Replace it with the actual condition: `findBy*`, `waitFor`, an advanced fake clock, or an explicitly resolved promise. If you can't name the condition you're waiting for, you don't understand the code's async flow yet — which is the real problem.

## Real-World Use Cases

### Pinning retry-with-backoff without waiting for it

Your fetch wrapper retries failed requests at 1s, 2s, 4s (see [[08 - Async JavaScript/02 - Promises|Promises]]). Tested with real timers, the suite would spend 7+ seconds per case; with a virtual clock, each boundary is asserted in microseconds.

```ts
it("retries at 1s, 2s, 4s then gives up", async () => {
  vi.useFakeTimers();
  const attempt = vi.fn().mockRejectedValue(new Error("503"));
  const result = fetchWithRetry(attempt, { retries: 3 });

  await vi.advanceTimersByTimeAsync(1_000);
  expect(attempt).toHaveBeenCalledTimes(2);      // initial + first retry
  await vi.advanceTimersByTimeAsync(2_000);
  expect(attempt).toHaveBeenCalledTimes(3);
  await vi.advanceTimersByTimeAsync(4_000);
  await expect(result).rejects.toThrow("503");   // exhausted
});
```

Works because the async advance drains promise jobs between timer tasks — the retry's `await` and its `setTimeout` interleave exactly as in [[09 - Event Loop Advanced/02 - Tasks vs Microtasks|Tasks vs Microtasks]].

> [!warning]
> The plain `advanceTimersByTime` variant would move the clock but never let the rejection's `.then` run — the test deadlocks. Async timer callbacks need the async advance.

### Toast auto-dismiss with paused timers on hover

A notification toast dismisses after 5s but pauses its countdown while hovered. The spec is pure "when" logic — advance 3s, hover, advance 10s (nothing happens), unhover, advance 2s (dismissed). Fake timers plus `userEvent.setup({ advanceTimers: vi.advanceTimersByTime })` make each branch an exact assertion instead of a screenshot-and-pray e2e test.

### CI-only flake reproduced by forcing the interleaving

A "works on my machine" bug: autosave (debounced 2s) and form submit racing — submitting during the debounce window sent stale data once a month in production. The deterministic test advances the clock to 1,999ms, submits, then advances past 2,000ms and asserts the debounced save was cancelled rather than firing over the submitted payload. The test is the only reliable reproduction the team has — exactly the "pin the interleaving" value from [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]].

## 4. Interview Answer

Short answer:

> Time-dependent tests flake because they race real timers against real sleeps. I use fake timers — a virtual clock advanced explicitly — so debounce/polling/timeout tests assert exact boundaries (nothing at 299ms, fires at 300ms) and run in microseconds. For race conditions, I keep responses pending and resolve them out of order deliberately, which forces the interleaving the bug needs and turns an intermittent production failure into a repeatable test.

Deeper answer:

> The subtleties are event-loop mechanics: timer callbacks that are async need `advanceTimersByTimeAsync` so pending microtasks drain between timer tasks, and `userEvent` needs its `advanceTimers` option wired to the fake clock or it deadlocks on its internal delays. Cancellation tests assert the mechanism — the AbortController fired, the stale response's UI never rendered — pinning the fixes for stale-closure and race bugs so refactors can't silently remove them. And any sleep in a test gets replaced with the condition it was approximating; if I can't name that condition, the code's async flow isn't understood yet.

## 5. Practice

1. <details><summary>Test a `poll(fn, everyMs, { maxAttempts })` utility: which cases?</summary>With fake timers: fn called immediately or after first interval (pin which — it's a contract); called again per interval (`advanceTimersByTime(everyMs)` × n); stops after success (advance further, assert call count froze); stops at maxAttempts and rejects/reports; cancellation (call the returned cancel/abort, advance, assert no further calls). Async fn ⇒ use `advanceTimersByTimeAsync`. Every case is exact-count assertable because the clock is owned by the test.</details>

2. <details><summary>Why can `vi.runAllTimers()` hang, and what's the safer default?</summary>It drains until no timers remain — but `setInterval` (or timers that reschedule themselves, like retry-with-backoff loops) always leaves one more, so it loops until Vitest's iteration cap kills it. `advanceTimersByTime(n)` moves the clock a bounded amount and is the right default; `runOnlyPendingTimers` runs what's currently queued without new recursions. Choose by the claim: "after N ms, X" wants a bounded advance.</details>

3. <details><summary>How do you assert "the effect aborted the in-flight request on unmount"?</summary>Have the MSW handler return a never-resolving promise and capture the request's `signal`... or simpler: render, trigger the fetch, `unmount()`, then assert the abort happened — e.g., the handler observed `request.signal.aborted === true` (stash it in a variable), or a `fetch` spy's AbortSignal is aborted. Also assert the negative space: no state-update-after-unmount warning, no error UI flash. This pins [[14 - JavaScript in React and Next.js/08 - AbortController in Effects|the cleanup contract]] itself.</details>

4. <details><summary>A test passes alone but fails when the whole suite runs. Name three likely causes and the diagnostic.</summary>(1) Shared module state — a module-level cache/singleton mutated by an earlier test (reset in `beforeEach` or isolate modules). (2) Unrestored globals — fake timers, mocked `Date`/`fetch`, or MSW handlers leaking (`afterEach` restore/reset discipline). (3) Timing/order dependence — the test relies on something an earlier test left warm. Diagnostic: run the failing test with its predecessors bisected (`--shard`/manual bisect) to find the polluting pair, then look for what crosses test boundaries. Order-dependence is always a bug in the tests, not in the runner.</details>

## Related Notes

- [[09 - Event Loop Advanced/04 - Timers|Timers]]
- [[04 - Functions Deep Dive/07 - Debounce and Throttle|Debounce and Throttle]]
- [[08 - Async JavaScript/06 - AbortController|AbortController]]
- [[14 - JavaScript in React and Next.js/07 - Async Effects and Race Conditions|Async Effects and Race Conditions]]
- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[24 - Testing and Quality/04 - Async UI Network Boundaries and MSW|Async UI, Network Boundaries and MSW]]
