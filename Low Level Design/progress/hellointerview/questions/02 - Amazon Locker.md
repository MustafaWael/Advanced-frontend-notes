# Amazon Locker — LLD Breakdown

**Source:** https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/amazon-locker
**Difficulty:** Easy · Author: Evan King (Hello Interview)

## Understanding the Problem

Amazon Locker is a self-service package pickup system. A delivery driver deposits a package into an available compartment, the system generates an access token, and the customer uses that code to retrieve their package.

Prompt: *"Design a locker system like Amazon Locker where delivery drivers can deposit packages and customers can pick them up using a code."*

## Requirements (3–5 min)

### Clarifying Questions

Structure around four areas: **core operations, what can go wrong, scope boundaries, future extensions.** (If you haven't used an Amazon locker, say so and ask for a primer.)

Key clarifications:
- Compartments come in small/medium/large. **Match size exactly** for now — if no matching size available, reject the deposit (no fallback).
- Scope is locker operations only. Delivery routing/driver assignment out of scope.
- System **returns** the code; notification (SMS/email) is downstream, someone else's problem.
- Wrong code → return an error. No lockout logic (identified, but scoped out).
- One access token per package (1:1). A customer can have multiple packages, each with its own code and compartment.
- Codes expire after **7 days**. Expired codes are rejected; package stays in the compartment until staff removes it.
- All compartments of a size full → return an error. No queueing or reservations.

### Final Requirements

```
Requirements:
1. Carrier deposits a package by specifying size (small, medium, large)
   - System assigns an available compartment of matching size
   - Opens compartment and returns access token, or error if no space
2. Upon successful deposit, an access token is generated and returned
   - One access token per package
3. User retrieves package by entering access token
   - System validates code and opens compartment
   - Throws specific error if code is invalid or expired
4. Access tokens expire after 7 days
   - Expired codes are rejected if used for pickup
   - Package remains in compartment until staff removes it
5. Staff can open all expired compartments to manually handle packages
6. Invalid access tokens are rejected with clear error messages

Out of scope:
- Delivery logistics (how the package arrives)
- Notification (how the token reaches the customer)
- Lockout after failed attempts
- UI/rendering layer
- Multiple locker stations
- Payment or pricing
```

Interview tip: explicitly mention features you considered and chose not to build (lockout, token delivery). It shows forward thinking without over-engineering, and you can circle back in extensibility.

## Core Entities and Relationships (~5 min)

Look for nouns — but **not every noun deserves to be an entity.** Some belong as fields or input parameters.

- **Package** — seems obvious, but rejected. Packages are external; Amazon's fulfillment system tracks IDs/shipping/customers. Our system only cares about the package's **size**, which is just an input parameter to `depositPackage`.
- **Compartment** — a real physical container with a size and ID. Clear entity.
- **Locker** — the orchestrator/entry point: scans compartments, finds an available one, generates a code, ties it together.
- **AccessToken** — not just a string field. It's a **bearer token with an expiration** representing *the right to open a specific compartment*. Worth modeling so it can own expiration logic and the compartment mapping.

| Entity | Responsibility |
|---|---|
| **Locker** | Orchestrator. Owns all compartments and the AccessToken lookup map. Handles deposit and pickup. |
| **AccessToken** | Bearer token: code, expiration timestamp, reference to the compartment it unlocks. Enforces expiry. |
| **Compartment** | Physical slot: ID, size, its own occupancy state. |

You might not nail entities on the first try — design is iterative. If you notice awkward indirection or behavior-free classes, adjust.

## Class Design (~10–15 min)

For each class ask: what must it **remember** (state) and what operations must it **support** (public methods)? Start with the orchestrator.

### Locker

| Requirement | What Locker must track |
|---|---|
| "System assigns an available compartment of matching size" | All compartments and which are occupied |
| "User retrieves package by entering access token" | Map from code → AccessToken for fast lookup |

```
class Locker:
    - compartments: Compartment[]
    - accessTokenMapping: Map<string, AccessToken>

    + Locker(compartments)
    + depositPackage(size) -> string | error
    + pickup(tokenCode) -> void | error
    + openExpiredCompartments() -> void
```

Occupancy lives on `Compartment` itself (see tradeoff discussion below), so Locker just iterates and checks the flag.

**Where should state live? Physical vs relational.** Physical state (contains a package, is broken, needs maintenance) lives on the entity — it describes the entity's condition. Relational state (assigned to this token, reserved by this user) lives in the orchestrator — it describes system-managed relationships. Note: this isn't always clear-cut. The Parking Lot problem makes the opposite choice (occupancy as relational state in a Set on the orchestrator). Both work — **what matters is having a rationale you can defend**, e.g. "occupied is on Compartment because physical presence is intrinsic to it."

Design choices worth calling out:
- **`depositPackage` returns only the token code** — the compartment physically opens, so the driver just sees which door opened; the code goes to the customer.
- **`pickup` returns void** — the door opening is the feedback. Invalid/expired codes throw specific errors.

### AccessToken

| Requirement | What AccessToken must track |
|---|---|
| "An access token is generated and returned" | The code string |
| "Access tokens expire after 7 days" | Expiration timestamp |
| "System validates code and opens compartment" | Reference to the compartment it unlocks |

```
class AccessToken:
    - code: string
    - expiration: timestamp
    - compartment: Compartment

    + AccessToken(code, expiration, compartment)
    + isExpired() -> boolean
    + getCompartment() -> Compartment
    + getCode() -> string
```

### Compartment

```
class Compartment:
    - size: Size
    - occupied: boolean

    + Compartment(size)
    + getSize() -> Size
    + isOccupied() -> boolean
    + markOccupied() -> void
    + markFree() -> void
    + open() -> void

enum Size:
    SMALL
    MEDIUM
    LARGE
```

Compartment tracks its physical state only; no business logic.

### Final Class Design

Three entities with focused responsibilities: Locker orchestrates workflows, AccessToken enforces access control with expiry, Compartment manages its own physical state. The design follows **Information Expert** — the class that owns the data knows how to use it: AccessToken owns expiration logic, Compartment owns occupancy, Locker manages allocation and the token map.

## Implementation (~10 min)

Check what the interviewer wants (code vs pseudocode vs talk-through). Pattern per method: (1) core logic / happy path, (2) edge cases. Most interesting: `depositPackage` (allocation + tying compartments to tokens) and `pickup` (validation flow + cleanup).

### Locker.depositPackage

Core logic: find available compartment of size → open it → mark occupied → generate token → store in map → return code.
Edge cases: no compartment available; invalid size (handled inside `getAvailableCompartment`).

```
depositPackage(size)
    compartment = getAvailableCompartment(size)
    if compartment == null
        throw Error("No available compartment of size " + size)

    compartment.open()
    compartment.markOccupied()
    accessToken = generateAccessToken(compartment)
    accessTokenMapping[accessToken.getCode()] = accessToken

    return accessToken.getCode()
```

`compartment.open()` triggers the physical unlock; assume hardware auto-closes/locks after ~30s (like real lockers). This is fire-and-forget — it assumes the driver deposits. A production system might use two-phase confirm or sensors (see extensibility #3).

#### How to find an available compartment — three approaches

**Bad: derive occupancy from the access token map.** ("Compartment occupied iff a token references it.") Deriving state instead of storing it is normally great, but here there's a **semantic problem**: expired tokens can't be deleted immediately (needed so pickup can say "expired" rather than "invalid"), yet the package physically stays in the compartment until staff removes it. **Token validity and physical occupancy are different things that can diverge** — you can't reliably derive one from the other.

**Good (optimal performance): index available compartments by size.** `Map<Size, Queue<Compartment>>` — dequeue on deposit, enqueue on pickup/staff removal. O(1) for all operations; the Queue's FIFO ordering also distributes wear evenly across physical compartments.

```
getAvailableCompartment(size)
    queue = availableCompartmentsBySize[size]
    if queue == null or queue.isEmpty()
        return null
    return queue.dequeue()  // O(1)
```

Downside: state now lives in two places (compartments array + queues) → synchronization risk (forget to enqueue → compartment vanishes; double-enqueue → occupied compartment looks free). Worth it for hundreds/thousands of compartments with constant deposits; for a typical 20–50 compartment locker, O(50) vs O(1) is negligible and simpler wins.

**Great (chosen): occupied flag on Compartment.** Single source of truth, physical state where it belongs, linear scan is fine.

```
getAvailableCompartment(size)
    for compartment in compartments
        if compartment.size == size and !compartment.isOccupied()
            return compartment
```

### Locker.pickup

Core logic: look up token → validate expiry → open compartment → clean up.
Edge cases: null/empty code; token not in map; token expired.

```
pickup(tokenCode)
    if tokenCode == null || tokenCode.isEmpty()
        throw Error("Invalid access token code")

    accessToken = accessTokenMapping[tokenCode]
    if accessToken == null
        throw Error("Invalid access token code")

    if accessToken.isExpired()
        throw Error("Access token has expired")

    // Valid pickup - unlock door and clean up
    compartment = accessToken.getCompartment()
    compartment.open()
    clearDeposit(accessToken)
```

Notes:
- On expiry: throw, but **keep the token in the mapping** — the package is still physically there; staff handles it via `openExpiredCompartments()`.
- "Invalid access token code" covers both never-existed and already-used codes (after pickup the token is removed, so a reused code looks like a random one). Distinguishing "already used" would need a `usedTokens` set or `isUsed` flag — extra state for marginal UX benefit.
- Expired codes DO get a specific message because it's **actionable** — the user knows to contact support for a package still in the locker.

### Helpers

```
generateAccessToken(compartment)
    code = generateRandomCode()      // 6-digit number, UUID, etc.
    expiration = now() + 7.days()    // production: cryptographically secure RNG
    return AccessToken(code, expiration, compartment)

clearDeposit(accessToken)
    compartment = accessToken.getCompartment()
    compartment.markFree()
    accessTokenMapping.remove(accessToken.getCode())
```

`clearDeposit` must do **both** steps or state goes inconsistent (compartment looks occupied when free, or orphan token for a free compartment).

```
openExpiredCompartments()
    for tokenCode, accessToken in accessTokenMapping
        if accessToken.isExpired()
            compartment = accessToken.getCompartment()
            compartment.open()
```

Deliberately does **not** call `clearDeposit` — compartments stay occupied until staff physically removes packages; a separate (out-of-scope) method would then free compartments and remove expired tokens.

### AccessToken / Compartment methods

```
isExpired()        return now() >= expiration
getCompartment()   return compartment
getCode()          return code

getSize()          return size
isOccupied()       return occupied
markOccupied()     occupied = true
markFree()         occupied = false
```

The logic is simple because the hard work happened in design — each class has one job.

### Verification (trace)

Compartments A (SMALL), B (MEDIUM), C (LARGE), all free; token map empty.

1. `depositPackage(MEDIUM)` → picks B, opens, marks occupied, creates token "ABC123" (expires now+7d), stores in map, returns "ABC123". State: `B.occupied=true`, map has entry.
2. `pickup("ABC123")` (valid) → token found, not expired, B opens, `clearDeposit`: `B.occupied=false`, map empty.
3. `pickup("ABC123")` 8 days later (expired scenario) → token still exists, `isExpired()` true → throws "Access token has expired". B stays occupied, expired token stays in map; staff later calls `openExpiredCompartments()` + cleanup.

## Extensibility (~5 min, if time and level allow)

Juniors often get none, mid-level one or two, seniors more depth. Explain how classes adapt; full implementation rarely required.

### 1. Size fallback?
Try exact size first, then fall back to larger (never smaller — won't fit). MEDIUM → MEDIUM, LARGE; SMALL → SMALL, MEDIUM, LARGE.

```
getAvailableCompartment(requestedSize)
    sizesInOrder = [SMALL, MEDIUM, LARGE]
    startIndex = sizesInOrder.indexOf(requestedSize)
    for i from startIndex to sizesInOrder.length
        size = sizesInOrder[i]
        for c in compartments
            if c.getSize() == size && !c.isOccupied()
                return c
    return null
```

Only the scanning logic changes — allocation is encapsulated in one method; fallback order is implicit in the size ordering.

### 2. Broken / under-maintenance compartments?
Replace the binary occupied boolean with a status enum:

```
enum CompartmentStatus:
    AVAILABLE
    OCCUPIED
    OUT_OF_SERVICE

class Compartment:
    - size: Size
    - status: CompartmentStatus
    + isAvailable() -> boolean       // status == AVAILABLE
    + markOccupied() / markAvailable() / markOutOfService() / markInService()
```

Allocation automatically skips out-of-service compartments because `isAvailable()` returns false.

### 3. Verify packages are actually deposited before generating tokens?
Current design is fire-and-forget (open + assume deposit). Fix with a **two-phase commit pattern**: split `depositPackage` into `reserveCompartment` and `confirmDeposit`.

```
class Locker:
    + reserveCompartment(size) -> reservationId
    + confirmDeposit(reservationId) -> tokenCode
    + cancelReservation(reservationId) -> void

enum CompartmentStatus: AVAILABLE, RESERVED, OCCUPIED, OUT_OF_SERVICE

reserveCompartment(size)
    compartment = getAvailableCompartment(size)
    if compartment == null: throw Error("No available compartment")
    compartment.markReserved()
    compartment.open()
    reservationId = generateReservationId()
    reservationMapping[reservationId] = compartment
    return reservationId

confirmDeposit(reservationId)
    compartment = reservationMapping[reservationId]
    if compartment == null: throw Error("Invalid reservation")
    compartment.markOccupied()
    accessToken = generateAccessToken(compartment)
    accessTokenMapping[accessToken.getCode()] = accessToken
    reservationMapping.remove(reservationId)
    return accessToken.getCode()
```

Needs a RESERVED state, separate reservation tracking, and timeout logic (auto-cancel if not confirmed within 2–3 minutes). Tradeoff: complexity. Single-phase is cleaner for interview scope; two-phase (with sensors or confirmation) is essential in production where physical presence must be guaranteed.

## What Is Expected at Each Level?

### Junior
Break the problem into sensible classes: identify Locker, Compartment, AccessToken and their relationships. Deposit and pickup work for the happy path. Awareness that edge cases exist (not necessarily all handled). Getting stuck on entity design is fine if you reason and adjust with hints.

### Mid-level
Cleaner decisions with less hand-holding. **Recognize Package isn't a useful entity** and reach the three-class model through reasoning. Clear separation of concerns (Locker orchestrates, AccessToken handles expiry, Compartment owns physical state). Handle key edge cases: invalid codes, expired codes, full compartments. Explain design choices (e.g., why occupancy is on Compartment vs a Locker-managed set). Discuss at least one extensibility scenario without detailed guidance.

### Senior
Drive the conversation with minimal prompting. Quickly reject Package with justification. Demonstrate **Information Expert** (AccessToken enforces expiry because it owns the timestamp; Compartment manages its physical state because it's a physical entity). Proactively discuss tradeoffs: occupancy on Compartment vs centralized set, whether lazy cleanup of expired tokens is acceptable, when a Package entity would earn its place (multiple packages per compartment). Anticipate questions — expiration handling, size fallback, compartment failure states, multi-package scenarios — before being asked.

## Key Takeaways

- Not every noun is an entity — Package is just a size parameter; AccessToken is more than a string (it owns expiry).
- Physical vs relational state: physical belongs on the entity, relational on the orchestrator — and either occupancy choice is defensible if you can justify it.
- Don't derive physical occupancy from token validity — they diverge (expired token, package still inside).
- Index-by-size gives O(1) but two sources of truth; a simple occupied flag wins at small scale.
- Give specific errors only when actionable ("expired" yes, "already used vs never existed" no).
