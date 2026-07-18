# Coordination

**Source:** https://www.hellointerview.com/learn/low-level-design/concurrency/coordination

> **Premium note:** This page is premium-locked. Only "The Problem" section and the article outline are freely visible. Locked sections are listed at the bottom; supplemental details come from the free Introduction page.

---

**Coordination** is about threads communicating and handing off work. One thread produces tasks, another consumes them. A service sends a request, another service processes it. The core question: **how do independent execution paths signal each other without burning CPU or corrupting state?**

## The Problem (free content)

Scenario: a task scheduler for a web app. Some work doesn't belong on the request path — it takes too long, and run inline it would block every API call. So you push it into the background:

- Users sign up → welcome emails.
- Profile photo uploads → resizing.
- Admin monthly reports → minutes to generate.

API handlers **produce** tasks, a pool of worker threads **consumes** them, and something in between coordinates the handoff. Works well under steady load — cracks show at the edges.

### Failure mode 1: workers ready, no work — busy-waiting (anti-pattern)

```python
while True:
    if queue:
        task = queue.pop(0)
        execute(task)
```

Each worker spins in a tight loop, burning CPU while doing no useful work. With eight workers on an eight-core machine you can consume **100% of compute capacity just checking an empty queue** — when tasks arrive, there's no CPU left to run them.

### Failure mode 2: sleep-polling (anti-pattern)

```python
import time

while True:
    if queue:
        task = queue.pop(0)
        execute(task)
    else:
        time.sleep(0.1)
```

Reduces CPU usage but **trades waste for latency**: a task arriving 1 ms after a worker sleeps waits nearly 100 ms. Sleep longer → sluggish system. Sleep shorter → back to burning CPU. There's no good sleep value.

### Failure mode 3: producers faster than consumers

A marketing email goes out; 50,000 users click at once, each request enqueueing background work:

```
09:00:00.000 - Queue size: 0
09:00:00.100 - Queue size: 5,000
09:00:00.200 - Queue size: 12,000
09:00:00.300 - Queue size: 23,000
09:00:00.400 - Queue size: 38,000
09:00:00.500 - Queue size: 50,000
```

Eight workers processing ~100 tasks/second take minutes to drain thousands. The delay isn't the killer — **memory is**. Every queued task is a heap object. An unbounded queue grows until **OutOfMemoryError**, crashing the *entire service* — not just background processing. Your API goes down and everything stops.

### The three requirements

This is a coordination problem. Threads need to signal each other ("work is ready"), wait efficiently, and handle one side being faster than the other:

1. **Efficient waiting** — consumers sleep when there's no work, waking immediately when work arrives.
2. **Backpressure** — producers slow down when consumers can't keep up, preventing memory exhaustion (bounded queues).
3. **Thread safety** — the coordination mechanism itself must handle concurrent access without corruption.

## The Solutions (article outline — details premium-locked)

Two fundamentally different approaches:

- **Shared state coordination** — data structures that multiple threads access directly, like a queue producers push to and consumers pull from.
  - **Wait/Notify (Condition Variables)** — the low-level mechanism for efficient waiting.
  - **Blocking Queues** — the practical, packaged tool.
- **Message passing coordination** — avoids shared state entirely. Each component has its own inbox and communicates by sending messages.
  - **The Actor Model**.

## Common Problems (article outline — details premium-locked)

1. **Process Requests Asynchronously** — the task-scheduler pattern above (with Examples).
2. **Handle Bursty Traffic** — absorbing spikes without dying (with Examples).

## Supplemental context (from the free Introduction page)

- **Condition variables** — thread acquires a lock, checks a condition, and if not satisfied, waits. Wait **atomically releases the lock and sleeps**; on signal, waiters wake and **re-check** (hence the `while` loop). Building block for blocking queues; rarely used directly in interviews.

```python
import threading

condition = threading.Condition()

with condition:
    while not ready:
        condition.wait()  # Release lock and sleep
    # Condition is now true
```

- **Blocking queues** — queue + condition variables = thread-safe producer-consumer handoff. `put()` blocks if full (this is your backpressure), `get()` blocks if empty (this is your efficient waiting). All synchronization handled internally — the go-to tool for handing work between threads.

```python
import queue

q = queue.Queue(maxsize=100)  # bounded — gives backpressure
q.put(task)   # Blocks if queue is full
t = q.get()   # Blocks if queue is empty
```

- **Go channels** replace blocking queues and condition variables idiomatically (a buffered channel is a bounded blocking queue). Java: `LinkedBlockingQueue`; C#: `BlockingCollection`.
- Summary row from the intro's problem-type table:

| Problem Type | What Breaks | Solutions | Common Problems |
| --- | --- | --- | --- |
| Coordination | Threads need ordering or handoff | Blocking queues, actors, event loops | Async request processing, bursty traffic |

## Interview Takeaways

- Name the anti-patterns: busy-waiting (burns CPU) and sleep-polling (adds latency, still wastes CPU). The interviewer wants you to reach for blocking waits instead.
- Always mention **bounded** queues — an unbounded queue is a memory leak under bursty load. Bounding the queue is how you get backpressure.
- Default answer for producer-consumer: a bounded blocking queue with a worker pool. Mention condition variables as what powers it under the hood; mention actors/message passing as the shared-nothing alternative.
- Coordination questions often appear as follow-ups ("now make it async" / "what if traffic spikes 100x?") after a correctness discussion.

---

### Locked sections (premium-only, not captured)

- Shared State Coordination: Wait/Notify (Condition Variables) — full text
- Shared State Coordination: Blocking Queues — full text
- Message Passing Coordination: The Actor Model — full text
- Process Requests Asynchronously — full text and Examples
- Handle Bursty Traffic — full text and Examples
- Conclusion
