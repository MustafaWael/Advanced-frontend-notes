# Dealing with Contention

**Source:** https://www.hellointerview.com/learn/system-design/patterns/dealing-with-contention

> Note: This page is premium-locked. Everything below is the free/visible content captured on 2026-07-17. Locked sections are listed at the bottom.

## What This Pattern Is

**Contention** occurs when multiple processes compete for the same resource at the same time — like booking the last concert ticket or bidding on an auction item. Without proper handling, you get race conditions, double-bookings, and inconsistent state.

## The Problem: The Race Condition (free content)

Consider buying concert tickets online. There's one seat left for The Weeknd, and Alice and Bob both want it. They each hit "Buy Now" in the same instant. The naive approach: read the current seat count, check that it's above zero, and if it is, decrement it and sell the ticket.

```sql
-- Read the current count
SELECT available_seats FROM concerts WHERE concert_id = 'weeknd_tour';

-- The app checks available_seats > 0, then writes the new value back
UPDATE concerts
SET available_seats = available_seats - 1
WHERE concert_id = 'weeknd_tour';
```

For a single buyer this is exactly right. The trouble starts when Alice and Bob run it at the same moment:

1. Alice's request reads one seat available.
2. A fraction of a millisecond later — before Alice has written anything back — Bob's request reads the same count and also sees one seat.
3. Both check the number they just read, both conclude there's a seat to sell, and both charge a card.
4. Alice's update commits first; the count drops to zero. Bob's update commits right after, decrements again, and the count slides to **negative one**.

Result: both cards charged $500, both buyers get a confirmation email for the same seat (Row 5, Seat 12). One gets kicked out at the venue; the business eats a refund and two angry customers.

The core issue is the **read–check–write gap**: any check performed in application code on stale data can be invalidated by a concurrent writer.

## The Solution: Approaches Covered (section headings — details premium-locked)

The page walks through these techniques, then a "Choosing the Right Approach" comparison:

- **Conditional Writes** — e.g., atomic compare-and-set style updates (`UPDATE ... WHERE available_seats > 0`) so the check and write happen atomically in the database
- **Pessimistic Locking** (including a "Common Failure Modes" subsection) — lock the row up front (e.g., `SELECT ... FOR UPDATE`)
- **Optimistic Concurrency Control** — version numbers; retry on conflict
- **Isolation Levels** — leaning on database transaction isolation (e.g., serializable)
- **Distributed Locks** — coordination outside a single database (e.g., Redis/ZooKeeper)
- **Choosing the Right Approach** — comparison/tradeoffs

(Only the headings are visible; the tradeoff discussion for each is behind the paywall.)

## When to Use in Interviews (headings — details locked)

- Recognition Signals
- Common Interview Scenarios
- When NOT to overcomplicate

Typical contention-heavy problems on the site include Ticketmaster, Online Auction, and similar "many users, one scarce resource" designs (the page itself does not list a problem-breakdown box in the free portion).

## Common Deep Dives (headings — details locked)

- "How do you prevent deadlocks with pessimistic locking?"
- "How do you handle the ABA problem with optimistic concurrency?"
- "What about performance when everyone wants the same resource?"

## Locked Sections (premium-only, not captured)

- Conditional Writes (details)
- Pessimistic Locking + Common Failure Modes (details)
- Optimistic Concurrency Control (details)
- Isolation Levels (details)
- Distributed Locks (details)
- Choosing the Right Approach
- When to Use in Interviews: Recognition Signals, Common Interview Scenarios, When NOT to overcomplicate
- All three Common Deep Dives listed above
- Conclusion
