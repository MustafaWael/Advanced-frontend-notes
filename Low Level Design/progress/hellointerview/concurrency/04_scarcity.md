# Scarcity

**Source:** https://www.hellointerview.com/learn/low-level-design/concurrency/scarcity

> **Premium note:** This page is premium-locked. Only "The Problem" section and the article outline are freely visible. Locked sections are listed at the bottom; supplemental details come from the free Introduction page.

---

**Scarcity** is about managing limited resources when demand exceeds supply. Finite database connections, limited memory for buffers, expensive resources that should only be created once. The constraint isn't correctness — **there simply aren't enough resources for everyone who wants one**.

## The Problem (free content)

Scenario: a **connection pool** managing database connections. Each query needs a connection, and connections are expensive:

- They consume memory on the database server.
- They hold file descriptors.
- They take time to establish.

So you create a pool of **5 connections at startup** and reuse them across requests.

**What should happen:** each request takes a connection from the pool, runs its query, and returns it. Five requests run simultaneously; the sixth waits until someone returns a connection.

**What goes wrong — connection leaks:** a request grabs a connection and never gives it back — a bug in the code, or a slow query that takes forever. Either way it blocks the pool.

- The database is fine — it's handling five queries without issue.
- **Your service is dead.** Every new request blocks indefinitely waiting for a connection that's never coming back.
- Users see timeouts. **Monitoring shows zero errors** because nothing crashed — requests are just stuck waiting forever.

**Framing:** unlike correctness problems where the danger is data corruption, here the issue is **limited capacity**. 5 connections, 100 concurrent requests → most requests must wait. The question is how to **manage that waiting without the system falling over**.

Every scarcity problem comes down to: **enforce a capacity limit and decide what happens when you hit it.** You need to (1) track how many resources are in use, (2) block new requests at the limit, and (3) wake waiting threads when resources free up.

## Solutions (article outline — details premium-locked)

1. **Semaphores** — limit how many threads can hold a resource simultaneously (grants *permission*, not the resource itself). Sub-section: *Challenges*.
2. **Resource Pooling (with Blocking Queue)** — gives you **actual resource objects, not just permission**. Sub-section: *Challenges*.

Key distinction stated in the free text: a semaphore controls *how many* may proceed; a pool hands out the concrete reusable objects (connections, buffers).

## Common Problems (article outline — details premium-locked)

The four patterns where scarcity appears most often in interviews:

1. **Limit concurrent operations** — e.g., download managers, API rate limiters.
2. **Limit aggregate consumption** — e.g., bandwidth limiting, memory budgets.
3. **Reuse expensive objects** — e.g., connection pools, GPU schedulers.
4. **Maximize utilization** — e.g., work stealing, batching, adaptive pool sizing.

## Supplemental context (from the free Introduction page)

- **Semaphores** are counting locks: N permits instead of binary locked/unlocked. Acquire before proceeding, release when done; at zero permits, threads block.

```python
import threading

permits = threading.Semaphore(5)  # Allow 5 concurrent operations
permits.acquire()  # Block if no permits available
try:
    do_work()
finally:
    permits.release()  # Always release, even on exception
```

  Note the `try/finally` — releasing in `finally` is exactly what prevents the leak scenario above (a thrown exception must not eat a permit forever).

- **Blocking queues** double as resource pools: pre-fill a bounded queue with the resource objects; `get()` blocks when the pool is empty, `put()` returns a resource and wakes a waiter.

```python
import queue

q = queue.Queue(maxsize=100)
q.put(task)   # Blocks if queue is full
t = q.get()   # Blocks if queue is empty
```

- Language mapping: Java `Semaphore`, Python `threading.Semaphore`, Go `x/sync/semaphore`, C++ `std::counting_semaphore`, C# `SemaphoreSlim`.
- Summary row from the intro's problem-type table:

| Problem Type | What Breaks | Solutions | Common Problems |
| --- | --- | --- | --- |
| Scarcity | Resources are limited | Semaphores, resource pools | Concurrent op limits, resource consumption, object reuse |

## Interview Takeaways

- Classify the ask: just capping concurrency → semaphore; handing out reusable objects → pool backed by a blocking queue.
- Always address the **leak** case: release permits/return resources in `finally`; consider acquisition **timeouts** so a stuck request fails fast instead of hanging forever (the free text's failure mode — service hangs with zero errors — is the trap interviewers probe).
- Scarcity is the classic follow-up to thread-pool / rate-limiter / connection-pool prompts (all listed in Hello Interview's problem breakdowns: Rate Limiter, Inventory Management, etc.).
- Distinguish from correctness explicitly in your answer: nothing gets corrupted here; the system fails by *starving*, not by producing wrong data.

---

### Locked sections (premium-only, not captured)

- Semaphores — full text and Challenges
- Resource Pooling (with Blocking Queue) — full text and Challenges
- Limit Concurrent Operations — full text and Examples
- Limit Aggregate Consumption — full text and Examples
- Reuse Expensive Objects — full text and Examples
- Maximizing Utilization — full text
- Conclusion
