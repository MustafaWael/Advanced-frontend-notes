# Correctness

**Source:** https://www.hellointerview.com/learn/low-level-design/concurrency/correctness

> **Premium note:** This page is premium-locked. Only "The Problem" section and the article outline are freely visible. The locked sections (listed at the bottom) are summarized here only by their headings; details below the outline supplement from the free Introduction page where the same primitives are described.

---

**Correctness** is about preventing data corruption when multiple threads access shared state. Two threads both book the same seat. A counter that should be 1000 reads 847. A bank balance missing deposits. The danger isn't deadlock or performance — it's **silently producing wrong results**.

## The Problem (free content)

Scenario: a ticket booking system for a concert venue. Users browse available seats and book them. What happens when two users try to book the same seat at the same time?

- Alice wants seat 7A. Bob also wants seat 7A.
- **What should happen:** Alice gets the seat, Bob gets an error.
- **What can happen concurrently:** Both users checked availability before either completed their booking. Both saw the seat as available. Both proceeded to book it. Bob's write overwrote Alice's — Alice thinks she has a ticket but will find Bob in her seat.

**Why it broke:** the check ("is the seat available?") and the action ("book it") happened as **two separate steps**. Another thread snuck in between them and invalidated the assumption. Alice checked, the answer was yes, but by the time she acted on that answer it was no longer true.

**The same pattern appears throughout LLD interviews:**

- Rate limiters checking if under the limit before allowing a request.
- Connection pools checking if a connection is free before handing it out.
- Caches checking if there's room before adding an item.

> **Rule of thumb:** whenever the validity of a check can change before you act on it, you have a correctness problem.

## The Solutions (article outline — details premium-locked)

The article presents four solutions, ordered simplest to most complex (and by frequency in interviews):

1. **Coarse-grained locking** — protects all related state with one lock.
   - Sub-sections: *Challenges*, *Read-Write Locks*.
2. **Fine-grained locking** — allows concurrent access to independent resources while protecting related ones (per-resource locks).
   - Sub-section: *Challenges*.
3. **Atomic variables** — work for single variables but **fail for multi-field invariants**.
   - Sub-section: *Challenges*.
4. **Thread confinement (shared nothing)** — eliminates concurrency entirely for related data.

## Common Bugs (article outline — details premium-locked)

The two patterns where correctness bugs appear most often in interviews:

1. **Check-then-act** — e.g., booking a seat *if available*. The check and the act are separate steps; the world can change in between. Fix by making check+act one atomic unit (hold a lock across both, or use an atomic compare-and-swap).
2. **Read-modify-write** — e.g., incrementing a counter. `counter += 1` is really read → add → write (multiple machine instructions); interleaved threads lose updates. Fix with atomics (single variable) or locks.

## Supplemental context (from the free Introduction page)

These points from the free intro article map directly onto this page's topics:

- **Locks (mutexes)** are the default tool for protecting shared state. Variants: coarse-grained (one lock for everything), fine-grained (per-resource locks), read-write (multiple readers OR one writer).

```python
import threading

lock = threading.Lock()

with lock:
    # Only one thread can be here at a time
    balance += amount
```

- **Atomics** use CPU compare-and-swap (CAS) — one uninterruptible step. Great for counters/flags; useless the moment two things must update together. Python lacks native atomics — use a `threading.Lock`:

```python
import threading

lock = threading.Lock()
counter = 0

with lock:
    counter += 1  # Protected increment (Python lacks native atomics)
```

- Summary row from the intro's problem-type table:

| Problem Type | What Breaks | Solutions | Common Problems |
| --- | --- | --- | --- |
| Correctness | Shared state is updated concurrently | Locks, atomics, thread confinement | Check-then-act, read-modify-write |

## Interview Takeaways

- Spot the failure mode by name: "this is a check-then-act race" or "this is a lost update from read-modify-write."
- Start with the simplest fix (coarse-grained lock); only move to fine-grained locking or atomics if contention/performance is raised as a follow-up.
- Atomics don't compose — a multi-field invariant (e.g., debit one account, credit another) needs a lock or confinement.
- Thread confinement (shared nothing) sidesteps the problem entirely: if only one thread ever touches the data, there is nothing to corrupt.

---

### Locked sections (premium-only, not captured)

- Coarse-Grained Locking (full text) — Challenges; Read-Write Locks
- Fine-Grained Locking (full text) — Challenges
- Atomic Variables (full text) — Challenges
- Thread Confinement (Shared Nothing) (full text)
- Check-Then-Act (full text) — Examples
- Read-Modify-Write (full text) — Examples
- Conclusion
