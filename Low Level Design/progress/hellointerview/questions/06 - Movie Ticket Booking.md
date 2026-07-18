# 06 - Movie Ticket Booking (BookMyShow)

**Source:** https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/bookmyshow
**Difficulty:** Medium · By Evan King (Hello Interview)

> **Note on completeness:** This page is premium-locked past the "Core Entities" section. Everything below under *Understanding the Problem*, *Requirements*, and the intro to *Core Entities* is captured verbatim-in-substance from the free portion. The locked sections are listed at the bottom with only their visible headings.

---

## Understanding the Problem

**What is a Movie Ticket Booking System?** A movie ticket booking system (like Fandango or BookMyShow) lets users search for movies, browse theaters and showtimes, select specific seats from a seat map, and reserve tickets. The system manages seat availability across multiple theaters, each with multiple screens, and prevents two people from booking the same seat.

## Requirements

The interview starts with this prompt:

> "Design a movie ticket booking system similar to BookMyShow that allows users to browse movies, select theaters and showtimes, book tickets, and manage reservations."

That's deliberately broad — narrow it down with targeted questions before writing a single requirement.

### Clarifying Questions (and what each answer tells you)

Focus questions on **core operations, scope boundaries, and constraints**.

1. **"When you say 'browse movies,' is that full-text search, fuzzy matching, or just simple title lookup?"**
   → *"Simple text matching on the movie title. Nothing fancy."*
   Takeaway: iterate the movie list, check if each title contains the search term, return matches. No Elasticsearch, inverted indexes, or ranking. A linear scan over a few hundred in-memory movies takes microseconds.

2. **"How does seat selection work? Does the user pick specific seats from a map, or does the system auto-assign? Can they book more than one seat at a time?"**
   → *"Users pick specific seats from a seat map. Yes, multiple seats in one transaction."*
   Takeaway: we're building a **seat picker, not a ticket counter** — per-seat availability tracking is required. The seat-map UI is out of scope, but the system must expose which seats are available so a frontend could render them.

3. **"Single theater or multiple? Do theaters have multiple screens?"**
   → *"Multiple theaters, each with multiple screens. A user can search for a movie and see where it's playing, or go to a specific theater and see what's on."*
   Takeaway: **two entry points** into the system — search by movie title globally, or browse a specific theater's offerings. Both paths funnel into picking a showtime, then picking seats. Support both directions efficiently.

4. **"Do different screens have different seat configurations, or can we standardize?"**
   → *"Standardize it. Every screen has the same layout: rows A through Z, seats 0 through 20."*
   Takeaway: big simplification — one constant seat layout for every screen; no per-screen configuration modeling.

5. **"What does 'manage reservations' include? Cancel, reschedule, modify?"**
   → *"Cancel only. If someone wants a different showtime, they cancel and rebook."*
   Takeaway: no rescheduling logic; simple reservation model.

6. **"Are there different seat types with different prices? Is payment processing in scope?"**
   → *"No to both. All seats are identical, and payment is out of scope. Assume it always succeeds."*
   Takeaway: no pricing tiers, no payment state machine.

7. **"What about concurrency? If two people try to book the same seat at the same time?"**
   → *"Handle it. Exactly one should succeed."*
   Takeaway: **concurrency is a core requirement**, not an afterthought.

### Final Requirements

```
Requirements:
1. Users can search for movies by title
2. Users can browse movies playing at a given theater
3. Theaters have multiple screens; all screens share the same seat layout (rows A-Z, seats 0-20)
4. Users can view available seats for a showtime and select specific ones
5. Users can book multiple seats in a single reservation; booking returns a confirmation ID
6. Concurrent booking of the same seat: exactly one succeeds
7. Users can cancel a reservation by confirmation ID, releasing the seats

Out of Scope:
- Payment processing (assume payment always succeeds)
- Variable seat layouts or seat types (all seats identical)
- Rescheduling (cancel and rebook instead)
- UI / rendering
```

## Core Entities and Relationships

Scanning the requirements gives a pool of candidate entities: **Theater, Movie, Screen, Seat, Showtime, Reservation**, and something to orchestrate it all (a **BookingSystem**). Not every candidate becomes its own class, but all are worth listing — each shows up somewhere in the design, whether as a class, a value object, a field, or a constant.

*(The final pruned entity list is premium-locked.)*

## Class Design (structure visible; content locked)

The breakdown designs these classes:

- **BookingSystem** — the orchestrator/facade (search movies, browse theaters, book, cancel)
- **Theater** — holds screens/showtimes for one location
- **Showtime** — a movie on a screen at a time; owns per-seat availability (the concurrency hot spot)
- **Movie** — title metadata for search
- **Reservation** — a booking of one or more seats, identified by a confirmation ID

Followed by a **Final Class Design** diagram. *(All method signatures and diagrams are premium-locked.)*

## Implementation (locked)

Per-class implementations (BookingSystem, Theater, Showtime, Movie, Reservation), a Complete Code Implementation, and **Verification** with four test cases whose names are visible:

1. Successful booking flow
2. Concurrent booking — exactly one succeeds
3. Cancellation releases seats correctly
4. Partial booking fails atomically

Note what the tests imply: multi-seat bookings must be **atomic** — if any requested seat is taken, the whole booking fails and no seats are held.

## Extensibility (headings visible; content locked)

- How would you support dynamically adding and removing showtimes, movies, and theaters?
- How would you handle temporary seat holds during checkout?

## What is Expected at Each Level? (locked)

The breakdown includes Junior / Mid-level / Senior expectation sections, all premium-locked.

---

## Premium-locked sections on this page

- Final Entities (pruned list)
- Class Design: BookingSystem, Theater, Showtime, Movie, Reservation + Final Class Design diagram
- Implementation: all code, Complete Code Implementation, Verification test bodies
- Extensibility: both follow-up answers
- What is Expected at Each Level: Junior / Mid-level / Senior
