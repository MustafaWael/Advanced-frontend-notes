# Introduction to Concurrency

**Source:** https://www.hellointerview.com/learn/low-level-design/concurrency/intro

Learn the fundamentals of concurrency and when it shows up in low-level design interviews.

---

## What Is Concurrency and Why It Matters

Concurrency is what happens when multiple things try to happen at the same time:

- Two users book the same flight seat.
- Three threads update the same counter.
- A dozen requests hit your cache while it's mid-refresh.

Code that worked perfectly in testing can suddenly produce impossible results in production.

**When it appears in interviews:**

- Concurrency doesn't necessarily show up in every LLD interview — it depends on company, team, and level. But once you interview for **senior roles**, it commonly shows up directly or gets added as a follow-up.
- LLD interviews focus on **single-process systems**: threads and shared memory within one program. System design interviews deal with concurrency across multiple servers — a different beast (see Hello Interview's "Dealing with Contention" in System Design for that).
- Two ways it shows up:
  1. **A classic LLD question gets harder:** a parking lot now has two cars racing for the same spot; an inventory system where two orders fight over the last item.
  2. **The prompt is built around concurrency from the start:** thread pools, rate limiters, connection pools, schedulers.
- Either way, the interviewer wants to see if you can **reason about what breaks when actions overlap and fix it without overcomplicating things**.

## Concurrency Fundamentals

Core fact: **threads in the same process share memory.**

- When a program runs, the OS creates a **process** — an isolated container with its own address space and resources.
- Inside that process, the OS or language runtime creates one or more **threads**. A thread is an independent execution path with its own program counter, registers, and stack — but it **shares the heap, globals, and open resources** with other threads in the same process.
- Concurrency exists whenever multiple threads can make progress independently and their execution can overlap:
  - On multi-core machines, threads may run in **parallel**.
  - On a single core, the OS rapidly **switches** between threads and interleaves their instructions.
  - From the program's point of view, both cases are the same: operations from different threads can interleave in unpredictable ways.

**Why bugs happen:**

- That unpredictability is the root of concurrency bugs. Code that looks atomic at the source level is often **multiple machine instructions**.
- If two threads read and write shared memory without coordination, the outcome depends on timing, scheduling, or load.
- This is why concurrency bugs are often **nondeterministic and hard to reproduce**.

**Language landscape:**

- Java, C++, Go, Rust, C#, and Python all run code concurrently in real systems — **assume concurrency any time shared state exists**.
- JavaScript/TypeScript are notable exceptions: user code runs on a single main thread, with concurrency expressed through **event loops and async callbacks** rather than shared-memory threads.

## The Toolbox (Primitives Quick Reference)

Concurrency problems are solved with a small set of primitives every language provides. You don't invent new synchronization mechanisms — you recognize which existing tool fits the problem. These handle the vast majority of interview scenarios.

### Atomics

Thread-safe operations on **single variables** without locks. Under the hood they use CPU instructions like **compare-and-swap (CAS)** that complete in one uninterruptible step.

Python is a corner case that lacks native atomics, so you need locks to safely increment counters across threads:

```python
# atomics.py
import threading

lock = threading.Lock()
counter = 0

with lock:
    counter += 1  # Protected increment (Python lacks native atomics)
```

- **Use for:** counters, flags, simple statistics.
- **Limit:** fast but limited to single variables — the moment you need to update two things together, atomics no longer help.
- *Used in: Correctness — read-modify-write on single variables.*

### Locks (Mutexes)

Provide **mutual exclusion**. When a thread holds a lock, other threads trying to acquire it block until release. This creates a **critical section** where only one thread executes at a time.

```python
# locks.py
import threading

lock = threading.Lock()

with lock:
    # Only one thread can be here at a time
    balance += amount
```

- **Your default tool for protecting shared state.**
- Main variants: **coarse-grained** (one lock for everything), **fine-grained** (per-resource locks), **read-write** (multiple readers OR one writer).
- *Used in: Correctness — check-then-act and multi-field updates.*

### Semaphores

**Counting locks.** Instead of binary locked/unlocked, a semaphore has **N permits**. Threads acquire permits before proceeding and release when done. When permits hit zero, threads block until someone releases.

```python
# semaphores.py
import threading

permits = threading.Semaphore(5)  # Allow 5 concurrent operations
permits.acquire()  # Block if no permits available
try:
    do_work()
finally:
    permits.release()  # Always release, even on exception
```

- **Use for:** limiting concurrent operations — e.g., at most 5 downloads or at most 10 API calls at a given time.
- *Used in: Scarcity — limiting concurrent operations and resource budgets.*

### Condition Variables

Let threads **wait efficiently for a condition to become true**. A thread acquires a lock, checks a condition, and if not satisfied, waits — which **atomically releases the lock and puts the thread to sleep**. When another thread signals, waiters wake up and **re-check**.

```python
# condition_variables.py
import threading

condition = threading.Condition()

with condition:
    while not ready:
        condition.wait()  # Release lock and sleep
    # Condition is now true
```

- The building block for blocking queues, but **rarely used directly in interviews**.
- Note the `while` loop (re-check after waking) — the canonical usage pattern.
- *Used in: Coordination — foundation for blocking queues.*

### Blocking Queues

Combine a queue with condition variables to provide **thread-safe producer-consumer handoff**. Producers call `put()` (block if full); consumers call `take()`/`get()` (block if empty).

```python
# blocking_queues.py
import queue

q = queue.Queue(maxsize=100)
q.put(task)   # Blocks if queue is full
t = q.get()   # Blocks if queue is empty
```

- The queue handles all synchronization internally — **your go-to tool for handing work between threads**.
- *Used in: Coordination — producer-consumer and async processing. Also in Scarcity — resource pooling.*

## Language Reference

| Concept | Java | Python | Go | C++ | C# |
| --- | --- | --- | --- | --- | --- |
| Lock/Mutex | synchronized / ReentrantLock | threading.Lock | sync.Mutex | std::mutex | lock / Monitor |
| Read-write lock | ReentrantReadWriteLock | N/A (3rd party) | sync.RWMutex | std::shared_mutex | ReaderWriterLockSlim |
| Condition variable | Object.wait/notify | threading.Condition | sync.Cond | std::condition_variable | Monitor.Wait/Pulse |
| Semaphore | Semaphore | threading.Semaphore | x/sync/semaphore | std::counting_semaphore | SemaphoreSlim |
| Blocking queue | LinkedBlockingQueue | queue.Queue | buffered channel | manual | BlockingCollection |
| Atomic integer | AtomicInteger | N/A (use Lock) | sync/atomic | std::atomic\<int\> | Interlocked |
| Concurrent map | ConcurrentHashMap | N/A (GIL) | sync.Map | tbb::concurrent_hash_map | ConcurrentDictionary |

**Notes:**

- Python's **GIL** means CPU-bound code doesn't benefit from threads, but **I/O-bound code does**. Use `multiprocessing` for CPU parallelism.
- **Go channels** replace blocking queues and condition variables idiomatically. When in doubt, use a channel.
- **C++** often requires manual composition of primitives. Consider Intel TBB for higher-level abstractions.

## Three Problem Types

Most interview concurrency problems fall into three categories. Surface details change (inventory systems, booking systems, rate limiters) but the underlying failure modes don't. **Seeing past the domain to the problem type is the core skill.**

1. **Correctness** — shared state gets corrupted. Two threads both check that a seat is available, both see yes, both book it. One booking gets lost.
2. **Coordination** — threads need to hand off work or wait for each other. Producer adds tasks to a queue, consumers process them. Empty queue → consumers must wait efficiently without burning CPU. Full queue → producers must slow down.
3. **Scarcity** — resources are limited. 10 database connections, 100 concurrent requests. Some requests must wait.

| Problem Type | What Breaks | Solutions | Common Problems |
| --- | --- | --- | --- |
| Correctness | Shared state is updated concurrently | Locks, atomics, thread confinement | Check-then-act, read-modify-write |
| Coordination | Threads need ordering or handoff | Blocking queues, actors, event loops | Async request processing, bursty traffic |
| Scarcity | Resources are limited | Semaphores, resource pools | Concurrent op limits, resource consumption, object reuse |

- **Most questions start with correctness.** Coordination and scarcity often appear as follow-ups once shared state exists or throughput increases.
- Real systems frequently involve more than one category, but separating them makes it easier to reason about each concern in isolation.

## Interview Takeaways

- Diagnose the problem type first (correctness / coordination / scarcity), then pick the matching primitive.
- Locks are the default for shared state; atomics for single variables; blocking queues for handoff; semaphores for capacity limits.
- Goal is pattern recognition: diagnose concurrency risks early, pick the right tool, and explain your reasoning clearly — without overcomplicating.

**Study order:** Correctness (how shared state gets corrupted; locks and atomics) → Coordination (producer-consumer, async processing) → Scarcity (resource pooling, rate limiting).
