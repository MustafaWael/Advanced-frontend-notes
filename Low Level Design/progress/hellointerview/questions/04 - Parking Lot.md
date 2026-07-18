# Parking Lot — LLD Problem Breakdown

**Source:** https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/parking-lot
**Difficulty:** Medium

> **Premium-locked note:** This breakdown is only partially free. The freely visible content covers **Understanding the Problem, Requirements (clarifying questions + final requirements), and the section outline**. The following sections are behind the Hello Interview Premium paywall and are NOT captured here (only their headings are visible): Core Entities and Relationships (body), Class Design (ParkingLot, ParkingSpot, Ticket, Final Class Design), Implementation (ParkingLot, ParkingSpot, Ticket, Complete Code Implementation, Verification), Extensibility answers, and the level-expectation write-ups (Junior / Mid-level / Senior).

## Understanding the Problem

A parking lot system manages vehicle parking across multiple spots. When a vehicle enters, the system assigns an available spot matching the vehicle type and issues a ticket. When the vehicle exits, the system calculates the parking fee based on time spent and frees up the spot for the next customer.

Initial prompt:

> "Design a parking lot system where different types of vehicles can park, and the system manages spot assignment and calculates fees upon exit."

Before thinking about classes, spend a few minutes turning this into something concrete.

## Requirements (~5 minutes)

Structure questions around: what the system does, how it handles mistakes, what's in scope, and what might change later.

### Clarifying Questions (key takeaways)

- **Spot assignment:** The *system* assigns a specific available spot matching the vehicle type at entry, and issues a ticket. (Real lots let you pick your own spot; the assigned-spot version is how the problem is asked because it forces you to design the allocation logic. "It's goofy, but roll with it.")
- **Vehicle types:** Three — motorcycles, regular cars, and large vehicles (SUVs/vans).
- **Entry flow:** Vehicle gets a ticket with a unique ID; the ticket is required to exit.
- **Pricing:** Keep it simple — hourly rate, same for all vehicles, rounded up to the nearest hour, paid on exit. When the interviewer says "keep it simple," don't over-engineer (no surge pricing/discounts unless asked).
- **Error handling:** Reject entry if no compatible spot is available. On exit, return an error if the ticket is invalid or already used.
- **Lost tickets:** Explicitly out of scope — assume tickets are never lost.
- **Out of scope:** Payment processing, entrance gates/hardware, cameras, UI. Focus on core logic: spot assignment, ticket management, fee calculation.

> Interview tip: interviewers notice edge-case questions ("what if they lose the ticket?", "what happens when the lot is full?"). Don't list 20 edge cases, but habitually asking "what can go wrong?" signals mature engineering thinking.

### Final Requirements

```
Requirements:
1. System supports three vehicle types: Motorcycle, Car, Large Vehicle
2. When a vehicle enters, system automatically assigns an available compatible spot
3. System issues a ticket at entry.
4. When a vehicle exits, user provides ticket ID
   - System validates the ticket
   - Calculates fee based on time spent (hourly, rounded up)
   - Frees the spot for next use
5. Pricing is hourly with same rate for all vehicles
6. System rejects entry if no compatible spot is available
7. System rejects exit if ticket is invalid or already used

Out of scope:
- Payment processing
- Physical gate hardware
- Security cameras or monitoring
- UI/display systems
- Reservations or pre-booking
```

## Core Entities and Relationships (~5 minutes)

Free preview guidance: look for nouns in the requirements, but **don't turn every noun into a class — some things are just data**.

*(Entity table and analysis are premium-locked.)*

From the visible structure, the core classes the breakdown lands on are:

- **ParkingLot** — the orchestrator (entry/exit, spot allocation)
- **ParkingSpot** — a spot with a size/type compatible with vehicle types
- **Ticket** — issued at entry with a unique ID and entry time; validated and consumed at exit

## Class Design (10–15 minutes) — locked

Premium sections (headings only): ParkingLot, ParkingSpot, Ticket, Final Class Design.

## Implementation (~10 minutes) — locked

Premium sections (headings only): ParkingLot, ParkingSpot, Ticket, Complete Code Implementation, Verification.

## Extensibility (5 minutes, if time and level allow) — locked

The follow-up questions asked (answers are premium-locked):

1. "How would you extend this to a multi-floor parking garage?"
2. "How would you add different pricing for different vehicle types?"
3. "How would you handle multiple entrances with concurrent access?"

## What is Expected at Each Level? — locked

The breakdown includes Junior / Mid-level / Senior expectation sections; their content is premium-locked.

---

## Study notes to fill the gaps (not from the article)

Since the design sections are paywalled, here's a standard approach consistent with the free requirements above and with the sibling breakdowns' conventions (derive state from requirements, top-down from the orchestrator, enums over class explosions):

- `enum VehicleType { MOTORCYCLE, CAR, LARGE }` and `enum SpotSize { SMALL, MEDIUM, LARGE }` — spot-vehicle compatibility as data/logic, not a subclass per vehicle.
- `ParkingLot` (entry point): `park(vehicleType) -> Ticket | null`, `unpark(ticketId) -> fee`, holds `List<ParkingSpot>` and `Map<ticketId, Ticket>`.
- `ParkingSpot`: `id`, `size`, `isOccupied`, `canFit(vehicleType)`, `occupy()/vacate()`.
- `Ticket`: `id`, `spot`, `entryTime`, `isPaid/used` flag; fee = ceil(hours) × hourlyRate.
- Errors: return null/false or throw on full lot, invalid or reused ticket.
- Extensibility hooks: Strategy pattern for pricing (per-vehicle rates), floors as `Floor` grouping of spots or a `floor` field on spots, and a lock or per-spot-type concurrent free-list for multiple entrances.
