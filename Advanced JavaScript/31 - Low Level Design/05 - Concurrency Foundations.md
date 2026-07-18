---
tags: [low-level-design, concurrency, interview]
module: "31 - Low Level Design"
priority: important
status: not-started
aliases: [locks, mutex, semaphore, race condition, producer consumer]
verified_on: 2026-07-17
version_scope: "Browser concurrency APIs as of 2026 — Web Locks API (navigator.locks, Baseline since 2022), SharedArrayBuffer/Atomics (Baseline since 2021, requires cross-origin isolation)"
---

# Concurrency Foundations

## Maturity Target

- Priority: #important
- Study time: 40 minutes
- Interview signal: Name the concurrency primitives, the three problem types, and the lock failure modes (deadlock/livelock/starvation), and explain how JS's single-threaded model changes the toolkit — async locks for await-spanning critical sections, `navigator.locks`, and Web Workers + message passing — without overclaiming "no mutual exclusion needed."
- Production signal: You reason about client races correctly, know why JS avoids *low-level* shared-memory bugs yet still needs async mutual exclusion, and reach for the right primitive.
- Dependencies: [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]], [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]

## Source Anchors

- [HelloInterview — Concurrency](https://www.hellointerview.com/learn/low-level-design/concurrency/intro)
- [MDN — Web Workers](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API)

> [!warning] Source coverage: HelloInterview's concurrency solution articles (correctness/coordination/scarcity) were premium-locked; the free scrape captured the primitives and problem framing. This note teaches those plus the JS-specific angle; deeper solution patterns should be verified against the source. `status` stays `not-started` until that pass.

## 1. Concept

Concurrency is multiple things happening at once over shared state — two threads incrementing one counter, two orders racing for the last item. In classic (multi-threaded) LLD, the **primitives** are:

- **Atomic** — an indivisible operation (compare-and-swap); lock-free updates to a single value.
- **Lock / Mutex** — mutual exclusion around a critical section; one thread at a time.
- **Semaphore** — allow up to N concurrent holders; bounds a scarce resource (a pool).
- **Condition variable** — wait until a condition holds, get signaled (avoids busy-waiting).
- **Blocking queue** — thread-safe hand-off buffer; the backbone of producer/consumer.

**Three problem types:** *correctness* (races, torn reads → locks/atomics/immutability), *coordination* (producer/consumer, avoid busy-wait and sleep-poll → blocking queue + condition signaling), *scarcity* (bounded pools, rate limiters → semaphores).

**The failure modes locks introduce** (name these — they're standard follow-ups): **deadlock** (two holders each wait on a lock the other holds; avoid with lock ordering or timeouts), **livelock** (threads keep reacting to each other and make no progress — busy but stuck), and **starvation** (a thread never gets the resource because others keep winning; fair scheduling fixes it). Deadlock is easiest to see in four lines:

```text
Thread 1: lock(A); … lock(B)   // holds A, waits for B
Thread 2: lock(B); … lock(A)   // holds B, waits for A
→ each waits forever for a lock the other owns. Fix: always acquire A before B.
```

Related axis: **pessimistic locking** (lock first, then act — safe, lower throughput under contention) vs **optimistic locking** (act on a version/timestamp, commit only if unchanged, retry on conflict — better under low contention; this is the compare-and-swap / `SELECT ... version` idea, and the direct sibling of the client-side "check the request is still the latest before applying" guard). **Mutex vs semaphore:** a mutex is a semaphore of count 1 with ownership (only the holder releases); a semaphore of count N just bounds concurrency and any party can signal.

**How JavaScript differs — the key insight for this vault.** JS runs your code on a **single thread** with an event loop ([[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]), so a *synchronous* block runs to completion without another thread interleaving — most low-level shared-memory data races (torn reads, `count++` lost updates) *can't happen*. But that does **not** mean "no mutual exclusion needed." What you get instead are **interleaving-of-async-tasks** races: any critical section that spans an `await` can be interleaved by another task, because the event loop is free to run other code while you're suspended ([[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]). A read-modify-write like *"check the cache is empty → `await` fetch → write the cache"* or *"if no request is in flight, start one"* is exactly a critical section, and two calls can both pass the check before either writes:

```ts
let cache: User | null = null;
// BROKEN: the guard spans an await, so two concurrent callers both pass the
// `if` and both fetch — the check-then-act critical section was interleaved.
async function loadOnce(): Promise<User> {
  if (cache) return cache;
  const user = await fetch("/me").then(r => r.json()); // ← suspends; other caller runs
  cache = user;
  return user;
}

// FIX: dedupe on the in-flight *promise*, not the resolved value — one fetch, shared result.
let pending: Promise<User> | null = null;
function loadDeduped(): Promise<User> {
  if (cache) return Promise.resolve(cache);
  pending ??= fetch("/me")
    .then(r => r.json() as Promise<User>)
    .then(u => { cache = u; pending = null; return u; });
  return pending;
}
```

The fix is **async mutual exclusion** — serialize with a promise queue, an `async-mutex` library, or dedupe the in-flight promise (as above) — not sequence-check-and-cancel alone (that handles *last-write-wins* races, not *serialize-this-section* ones).

The platform also ships real locking primitives: the **Web Locks API** (`navigator.locks.request(name, cb)`) gives named mutual exclusion **across tabs, windows, and workers of the same origin** (Baseline since 2022) — the literal browser mutex. True parallelism uses **Web Workers**, which by default don't share memory — they communicate by **message passing** (structured clone), so there's nothing to lock. The exception is **`SharedArrayBuffer` + `Atomics`**, the one place JS has real shared-memory concurrency: `Atomics.wait`/`Atomics.notify` even let you build blocking mutexes and condition variables in workers. `SharedArrayBuffer` requires a **secure, cross-origin-isolated context** (`crossOriginIsolated === true`, set via COOP + COEP headers) — without those headers the constructor is unavailable.

> [!tip] So the mapping is: multi-threaded mutex → for a critical section that spans an `await`, use an **async lock / promise queue** (or `navigator.locks` for cross-tab/worker exclusion) — *not* "nothing needed"; atomic compare-and-swap → optimistic version check / in-flight promise dedup; producer/consumer blocking queue → an async queue / stream; semaphore-bounded pool → a concurrency limiter around `fetch` (e.g. "max 5 in flight"); distributed lock → a server concern ([[30 - Backend System Design/10 - The Seven Access Patterns|Dealing with Contention]]).

## 2. Why It Matters

If an LLD prompt adds concurrency ("two users book the same seat"), you need the primitives. But as a frontend engineer the deeper payoff is understanding *why your bugs look different*: JS trades shared-memory races for async-ordering races, and offloads CPU work to workers that pass messages instead of sharing state. That's the whole reason the vault's race-condition note is about `AbortController` and sequence checks, not mutexes.

## 3. Real Frontend Example: Bug → Fix → Tradeoff

Scenario: a page fires 60 image-analysis `fetch`es at once; the browser/network chokes and some fail.

Trace: unbounded concurrency — the **scarcity** problem. In threaded code you'd bound it with a **semaphore**; in JS there's no thread to block, but the same idea applies as an async concurrency limiter.

```ts
// Semaphore-style limiter: at most `n` promises in flight (scarcity, JS-style)
async function pool<T>(tasks: (() => Promise<T>)[], n: number): Promise<T[]> {
  const results: T[] = []; let i = 0;
  async function worker() {
    while (i < tasks.length) { const idx = i++; results[idx] = await tasks[idx](); }
  }
  await Promise.all(Array.from({ length: n }, worker));  // n "workers" drain the queue
  return results;
}
// Note: one task rejecting rejects Promise.all while other in-flight tasks keep running,
// and their results are discarded. For overload-resistance you'd catch per task
// (Promise.allSettled semantics) so a single failure doesn't waste the batch.
```

Tradeoff: limiting concurrency trades peak throughput for stability and fairness. Too low wastes bandwidth; too high reproduces the overload. The right `n` comes from the resource limit — the same sizing logic as a server connection pool.

## 4. Interview Answer

Short answer:

> The classic primitives are atomics, mutexes, semaphores, condition variables, and blocking queues, addressing three problems: correctness (races), coordination (producer/consumer), and scarcity (bounded resources). JavaScript is different because it's single-threaded with an event loop — synchronous code can't be interleaved by another thread, so ordinary shared-memory races don't occur. Instead I deal with async-ordering races, and use Web Workers with message passing for real parallelism, which share no memory to lock.

Deeper answer:

> The single-thread model is why frontend concurrency bugs are about async interleaving — awaited responses resolving out of order — not torn reads. For *last-write-wins* races the fix is sequence checks and cancellation (`AbortController`), not locks. But a critical section that spans an `await` still needs mutual exclusion: two calls can both pass a "no request in flight?" check before either writes, so I serialize with a promise queue / async-mutex, or dedupe the in-flight promise — and for cross-tab exclusion the browser gives me `navigator.locks`. When I need CPU parallelism I use Web Workers, which communicate by structured-clone message passing, so there's no shared state; the exception is SharedArrayBuffer + Atomics (which needs cross-origin isolation and can even build real blocking locks via `Atomics.wait`). And the primitives still map: a semaphore becomes an async concurrency limiter around fetch, producer/consumer becomes an async queue or stream, optimistic-vs-pessimistic locking shows up as version checks vs serialized writes, and a distributed lock is the server-side version of the same contention problem.

## 5. Practice

1. <details><summary>Why don't low-level shared-memory data races happen in normal JS — and what race replaces them?</summary>JS executes on a single thread via the event loop; a synchronous run-to-completion can't be preempted by another thread mutating the same memory, so torn reads and lost `count++` updates don't occur. What replaces them is async interleaving: any critical section spanning an `await` can be interrupted by another task, so a check-then-act (e.g. "no request in flight? → start one") can be entered twice. That still needs mutual exclusion — an async lock / promise queue — even though there's only one thread.</details>
2. <details><summary>What's the JS analog of a semaphore-bounded resource pool?</summary>An async concurrency limiter — cap the number of in-flight promises (e.g., max 5 concurrent fetches), draining a queue with N "workers." Same purpose as a semaphore (bound a scarce resource) without a thread to block, since JS uses cooperative async scheduling.</details>
3. <details><summary>How do Web Workers avoid the need for locks, and what are the exceptions?</summary>By default they don't share memory — main thread and worker communicate by passing messages (structured clone / transfer), so there's no shared mutable state to protect. Exceptions: (1) `SharedArrayBuffer` + `Atomics` reintroduces real shared-memory concurrency (and needs a cross-origin-isolated context; `Atomics.wait`/`notify` can build genuine blocking locks); (2) even without workers, the **Web Locks API** (`navigator.locks`) exists for coordinating across an origin's tabs/workers. So "no locks in JS" is wrong — it's "no *thread* preemption, but you still coordinate async sections and cross-context access."</details>

## 6. Real-World Use Cases

### Token-refresh queue — async mutex against a stampede

A 401 means the access token expired. If ten requests fail at once and each fires its own refresh, you get ten refreshes, rate-limit errors, and possibly ten *different* new tokens. The critical section "refresh once, everyone waits" spans an `await`, so it needs mutual exclusion.

```ts
let refreshing: Promise<string> | null = null;
async function getFreshToken(): Promise<string> {
  refreshing ??= fetch("/auth/refresh", { method: "POST" })
    .then(r => r.json() as Promise<{ token: string }>)
    .then(({ token }) => { refreshing = null; return token; });
  return refreshing;      // all concurrent 401s await the single in-flight refresh
}
```

One refresh serves every waiter — the client analog of a server single-flight against cache stampede ([[30 - Backend System Design/05 - Caching|Caching]]).

> [!warning] Reset `refreshing = null` on rejection too (a `.catch`), or a failed refresh permanently poisons the queue — every later call awaits a promise that already rejected.

### Web Locks — one leader tab does the background work

Five open tabs shouldn't each run the same polling/sync loop. `navigator.locks` grants an exclusive, origin-scoped lock; whichever tab holds it is the leader, and the lock auto-releases if that tab closes.

```ts
navigator.locks.request("sync-leader", { mode: "exclusive" }, async () => {
  // only one tab reaches here at a time; held until this callback resolves
  await runBackgroundSyncLoop();   // keep the lock while leading
});
```

This is a real mutex the platform ships — the cross-tab version of "one holder at a time." See [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]].

### Serialized write queue — ordering without a lock

Autosave or optimistic edits must hit the server *in order*, but `await`ed calls can resolve out of order. Chain each task onto the previous one's promise — a one-slot queue that guarantees sequential execution.

```ts
let tail: Promise<unknown> = Promise.resolve();
function enqueue<T>(task: () => Promise<T>): Promise<T> {
  const run = tail.then(task, task);   // run after whatever is ahead, success or fail
  tail = run.catch(() => {});          // keep the chain alive on error
  return run;
}
// enqueue(() => save(v1)); enqueue(() => save(v2)); // v2 never overtakes v1
```

Same intent as a blocking queue / producer-consumer, expressed with promise chaining — see [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]].

## Related Notes

- [[17 - Practical Frontend Scenarios/03 - Handling Race Conditions|Handling Race Conditions]]
- [[19 - DOM and Browser APIs/09 - Web Workers and Offloading Work|Web Workers and Offloading Work]]
- [[09 - Event Loop Advanced/01 - Event Loop Overview|Event Loop Overview]]
- [[30 - Backend System Design/10 - The Seven Access Patterns|The Seven Access Patterns]] (Dealing with Contention)
