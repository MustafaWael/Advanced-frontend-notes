# Elevator — LLD Problem Breakdown

**Source:** https://www.hellointerview.com/learn/low-level-design/problem-breakdowns/elevator
**Difficulty:** Medium

## Understanding the Problem

An elevator system manages multiple elevators serving different floors in a building. When someone requests an elevator, the system decides which one to dispatch. Once inside, passengers select their destination floors. The system needs to move elevators efficiently while handling multiple concurrent requests.

Initial prompt:

> "Design an elevator control system for a building. The system should handle multiple elevators, floor requests, and move elevators efficiently to service requests."

## Requirements (~5 minutes)

Structure clarifying questions around four areas: core actions, error handling, system boundaries, and future extensions. The back-and-forth takes 1–3 minutes — don't rush it.

### Clarifying Questions (key takeaways)

- **Scale:** 3 elevators serving 10 floors (0–9), fixed configuration. Scale matters — 3 elevators is very different from 300.
- **Hall calls:** Classic up/down hall calls (not destination dispatch). The system picks an elevator intelligently, but can start simple.
- **Inside the car:** Passengers can press multiple floor buttons (multiple destinations queued).
- **Two distinct stop types:** hall calls carry a direction (UP or DOWN); destination buttons inside carry no direction — just stop there. This distinction shapes the whole design.
- **Invalid requests:** Reject clearly (return `false`), never crash. Requesting the current floor is a no-op (already there).
- **Out of scope:** capacity/weight limits, door mechanics, emergency stops — "this question saved us from spending 15 minutes designing door state machines."
- **Simulation vs. control software:** Ask explicitly! "Are we building a simulation where I control time with a `step()` function, or modeling actual control software?" Real elevator software is asynchronous and hardware-driven (`onFloorReached(floor)` callbacks, motor controllers, floor sensors). LLD interviews almost always want the **simulation**: abstract away hardware, control time with `step()`/`tick()`. This keeps the problem tractable in 35 minutes, deterministic, and testable — and asking the question is a senior-level signal. Nine times out of ten they want the simulation.

### Final Requirements

```
Requirements:
1. System manages 3 elevators serving 10 floors (0-9)
2. Users can request an elevator from any floor (hall call). System decides which elevator to dispatch.
3. Once inside, users can select one or more destination floors
4. Simulation runs in discrete time steps (e.g., a step() or tick() call advances time)
5. Elevator stops come in two types:
    - Hall calls: Request from a floor with direction (UP or DOWN)
    - Destination: Request from inside elevator (no direction specified)
6. System handles multiple concurrent pickup requests across floors
7. Invalid requests should be rejected (return false)
    - Non-existent floor numbers
8. Requests for the current floor are treated as a no-op / already served (doors out of scope)

Out of scope:
- Weight capacity and passenger limits
- Door open/close mechanics
- Emergency stop functionality
- Dynamic floor/elevator configuration
- UI/rendering layer
```

## Core Entities and Relationships (~5 minutes)

Scan requirements for nouns that have behavior or state — but don't turn every noun into a class:

- **Floor** — NOT a class. Floors don't maintain state or enforce rules; they're just numbers identifying positions. Stays an `int`.
- **Request** — Deferred decision. Is it just a wrapped primitive, or does it have real behavior? Revisit during class design.
- **Elevator** — Clear entity. Maintains state (current floor, direction, floors to stop at) and enforces rules (service stops along the path, can't go below floor 0).
- **ElevatorController** — Clear entity. Receives hall calls and decides which elevator to dispatch; the orchestrator.

> Rule of thumb: whenever you build a tick-based simulation, you need a controller entity that owns the `step()` function — it advances time for the entire system and orchestrates all the actors.

| Entity | Responsibility |
|---|---|
| **ElevatorController** | The orchestrator. Receives hall calls, decides which elevator handles each request, coordinates the system. Doesn't know how elevators move internally — just dispatches requests and tells elevators to advance. |
| **Elevator** | One elevator. Maintains current floor, direction, and queue of requests. Executes movement: move one floor at a time, stop when needed, reverse when no more stops ahead. Doesn't know about other elevators. |
| **Request** | A stop the elevator needs to make. Undecided at this stage whether it's a class or just a floor number — decided during class design. |

It's fine to be on the fence about entity vs. primitive — communicate it and come back to it.

## Class Design (10–15 minutes)

Work **top-down**: start with `ElevatorController` (the entry point / public contract), then drill into `Elevator`. For each class ask: what does it need to remember, and what actions must it support? Derive state from requirements.

### ElevatorController

| Requirement | What ElevatorController must track |
|---|---|
| "System manages 3 elevators serving 10 floors" | The collection of elevators it controls |

```
class ElevatorController:
    - elevators: List<Elevator>

    + ElevatorController()
    + requestElevator(floor, type) -> boolean
    + step() -> void
```

Design choice: **immediate dispatch** — hall calls are assigned to an elevator the moment they arrive, so the controller stays stateless beyond holding elevators. Alternative: keep a queue of pending requests on the controller and have elevators pull from it. Both work; immediate dispatch is simpler for an interview, but if asked "what if all elevators are busy?" you'd want the queue model. Be ready to explain the tradeoff.

Type-safety note: `requestElevator` takes a `RequestType` (PICKUP_UP or PICKUP_DOWN), **not** a `Direction`. Hall calls are never IDLE — accepting `Direction` would let invalid values in and require runtime validation. `RequestType` makes it impossible at the type level.

```
ElevatorController()
    elevators = [Elevator(), Elevator(), Elevator()]
```

### Elevator

| Requirement | What Elevator must track |
|---|---|
| "Elevators serving 10 floors (0-9)" | Current floor position |
| "Continue in current direction servicing all requests" | Current direction of travel |
| "Users can select one or more destination floors" | Collection of floors to stop at |

```
class Elevator:
    - currentFloor: int
    - direction: Direction        // UP, DOWN, IDLE
    - requests: Set<???>
```

**Why an IDLE state?** With no requests, the elevator isn't moving up or down. Without an explicit "not moving" state, the elevator would drift forever; UP/DOWN alone can't cleanly handle "no requests."

**What type should `requests` be?** The deferred entity question:

#### Good Solution: Store just floor numbers (`Set<Integer>`)

```
addRequest(floor)
    requests.add(floor)

step()
    if requests.contains(currentFloor)
        requests.remove(currentFloor)
        // ... continue moving
```

Works, and deduplicates stops. **Challenge:** elevator at floor 5 going UP with requests [7, 8]; someone at 7 presses DOWN. The elevator stops at 7 going UP, the DOWN passenger boards and gets dragged up to 8 first. Confusing and inefficient — passengers watch the direction indicator. Acceptable at junior level; we can do better.

#### Great Solution: `Request` class with type (chosen)

```
enum RequestType:
    PICKUP_UP      // Hall call going up
    PICKUP_DOWN    // Hall call going down
    DESTINATION    // Destination button (stop regardless of elevator direction)

class Request:
    - floor: int
    - type: RequestType
    + Request(floor, type)

// equals() and hashCode() based on floor + type
// So Request(7, PICKUP_UP) != Request(7, PICKUP_DOWN) != Request(7, DESTINATION)
```

```
step()
    pickupType = (direction == UP) ? PICKUP_UP : PICKUP_DOWN
    pickupRequest = Request(currentFloor, pickupType)
    destinationRequest = Request(currentFloor, DESTINATION)

    if requests.contains(pickupRequest) || requests.contains(destinationRequest)
        requests.remove(pickupRequest)
        requests.remove(destinationRequest)
        // ... continue moving
```

Same scenario now: `Request(7, PICKUP_DOWN)` is added; passing floor 7 going UP the elevator checks only for `PICKUP_UP` / `DESTINATION`, doesn't stop, continues to 8, reverses, and stops at 7 going DOWN. Direction-aware stopping at the cost of one small class with equals/hashCode. Worth it.

Elevator interface:

```
class Elevator:
    - currentFloor: int
    - direction: Direction        // UP, DOWN, IDLE
    - requests: Set<Request>      // Request = (floor, RequestType)

    + Elevator()
    + addRequest(request) -> boolean
    + step() -> void
    + getCurrentFloor() -> int
    + getDirection() -> Direction

Elevator()
    currentFloor = 0  // all elevators start at ground floor
    direction = IDLE
    requests = HashSet()
```

`addRequest` is a unified interface for both the controller (hall calls) and passengers (destinations) — the elevator doesn't care *why* it stops at floor 5.

**Anti-pattern warning:** don't extract a shared `IRequestHandler` interface because `requestElevator(floor, type)` and `addRequest(request)` look similar. They do fundamentally different things — coordination (picking an elevator) vs. simple state mutation. The controller is not a type of elevator; there's no real polymorphism. Save interfaces for when multiple implementations of the same behavior must be substitutable.

### Request

```
class Request:
    - floor: int
    - type: RequestType

    + Request(floor, type)
    + getFloor() -> int
    + getType() -> RequestType

enum RequestType:
    PICKUP_UP
    PICKUP_DOWN
    DESTINATION
```

### Final Class Design

```
class ElevatorController:
    - elevators: List<Elevator>
    + ElevatorController()
    + requestElevator(floor, type) -> boolean
    + step() -> void

class Elevator:
    - currentFloor: int
    - direction: Direction        // UP, DOWN, IDLE
    - requests: Set<Request>
    + Elevator()
    + addRequest(request) -> boolean
    + step() -> void
    + getCurrentFloor() -> int
    + getDirection() -> Direction

class Request:
    - floor: int
    - type: RequestType
    + Request(floor, type)
    + getFloor() -> int
    + getType() -> RequestType

enum Direction: UP, DOWN, IDLE
enum RequestType: PICKUP_UP, PICKUP_DOWN, DESTINATION
```

Movement logic is encapsulated in `Elevator`; `ElevatorController` handles system-wide coordination; `Request` enables direction-aware stopping without coupling the algorithm to external details.

## Implementation (~10 minutes)

Check with the interviewer first — working code, pseudocode, or talk-through? For each method: (1) start with the main flow, (2) then handle edge cases. Aim for clarity over cleverness. The interesting methods are `ElevatorController.requestElevator()` (dispatch) and `Elevator.step()` (movement).

### ElevatorController.requestElevator — dispatch logic

Core logic: validate floor → pick an elevator → tell it to add the stop.
Edge cases: floor out of bounds (<0 or >9); invalid type.

```
requestElevator(floor, type)
    // Validate
    if floor < 0 || floor > 9
        return false
    if type == DESTINATION
        return false  // hall calls only

    // Create Request at the boundary, pass it through the system
    request = Request(floor, type)
    best = selectBestElevator(request)
    return best.addRequest(request)
```

`selectBestElevator` is where the tradeoff discussion lives. Start simple, then proactively offer: "This works, but I could make it more sophisticated by considering direction. Would you like me to implement that?"

#### Bad Solution: Nearest elevator (ignore direction)

```
selectBestElevator(request)
    floor = request.getFloor()
    nearest = elevators[0]
    minDistance = abs(elevators[0].getCurrentFloor() - floor)
    for e in elevators
        distance = abs(e.getCurrentFloor() - floor)
        if distance < minDistance
            minDistance = distance
            nearest = e
    return nearest
```

Correct, 30 seconds to write, fine for light traffic. **Challenge:** someone on floor 5 presses "up"; the nearest elevator is at 6 heading down to 1. We dispatch it anyway. Thanks to the Request types it won't wrongly pick them up mid-descent, but the passenger watches the nearest elevator ignore them — long wait, poor experience.

#### Good Solution: Direction-aware (basic)

```
selectBestElevator(request)
    // Priority 1: Elevators moving toward the floor in the right direction
    best = findMovingToward(request)
    if best != null return best
    // Priority 2: Idle elevators (pick nearest)
    best = findNearestIdle(request.getFloor())
    if best != null return best
    // Priority 3: Any elevator (pick nearest)
    return findNearest(request.getFloor())

findMovingToward(request)
    floor = request.getFloor()
    direction = (request.getType() == PICKUP_UP) ? UP : DOWN
    nearest = null; minDistance = Integer.MAX_VALUE
    for e in elevators
        if e.getDirection() != direction
            continue
        if (direction == UP && e.getCurrentFloor() > floor) ||
           (direction == DOWN && e.getCurrentFloor() < floor)
            continue
        distance = abs(e.getCurrentFloor() - floor)
        if distance < minDistance
            minDistance = distance
            nearest = e
    return nearest
```

**Challenge (subtle):** elevator at floor 3 going UP with a single stop at floor 4; someone at floor 7 presses UP. Direction matches and the elevator is below 7, so we dispatch — but it will reverse at floor 4. We checked current direction, not what its request queue commits it to.

#### Great Solution: Direction-aware with request queue analysis

Also check whether queued requests actually take the elevator to/past the requested floor before reversing:

```
selectBestElevator(request)
    // Priority 1: Elevators with stops extending to/past the requested floor
    best = findCommittedToFloor(request)
    if best != null return best
    // Priority 2: Idle elevators (nearest); Priority 3: Any elevator (nearest)
    ...

findCommittedToFloor(request)
    ... same as findMovingToward, plus:
        // NEW: Check if elevator has stops that will take it to/past this floor
        if !e.hasRequestsAtOrBeyond(floor, direction)
            continue

hasRequestsAtOrBeyond(floor, dir)   // on Elevator
    for request in requests
        if dir == UP && request.getFloor() >= floor
            if request.getType() == PICKUP_UP || request.getType() == DESTINATION
                return true
        if dir == DOWN && request.getFloor() <= floor
            if request.getType() == PICKUP_DOWN || request.getType() == DESTINATION
                return true
    return false
```

**Tradeoff:** better passenger experience, more complexity. In 35 minutes you likely won't implement this — the smart play is to implement the "good" version and proactively name the limitation: "In production I'd add a helper to verify the request queue."

**Design pattern — Strategy:** if different buildings need different scheduling (minimize wait time vs. energy efficiency), swap scheduling strategies, each implementing the same `selectBestElevator(request)` interface. That's the Strategy pattern in action.

`ElevatorController.step()` is trivial — movement is encapsulated in Elevator:

```
step()
    for e in elevators
        e.step()
```

### Elevator.step() — movement algorithm

The heart of the system. Explore alternatives before coding:

#### Bad Solution: FIFO (first-in-first-out queue)

```
step()
    if requestQueue.isEmpty()
        direction = IDLE
        return
    target = requestQueue.peek()      // oldest request
    if currentFloor < target.getFloor()  currentFloor++
    else if currentFloor > target.getFloor()  currentFloor--
    if currentFloor == target.getFloor()
        requestQueue.poll()
```

Example: at floor 5 with queue [8, 3, 7] → 5→8 (3 up), 8→3 (5 down), 3→7 (4 up) = 12 floors, two reversals. Constant direction changes, feels random, terrible wait times in a busy building.

#### Good Solution: Always go to nearest stop

```
step()
    if requests.isEmpty()
        direction = IDLE
        return
    // Find nearest request (lowest floor as tiebreaker for determinism)
    nearest = null; minDistance = MAX
    for request in requests
        distance = abs(currentFloor - request.getFloor())
        if distance < minDistance ||
           (distance == minDistance && (nearest == null || request.getFloor() < nearest.getFloor()))
            minDistance = distance
            nearest = request
    // move toward nearest; remove on arrival
```

Same scenario: 5→3 (2 down), 3→7 (4 up), 7→8 (1 up) = 7 floors. Better, but still reverses unnecessarily — at floor 5 with stops above (7, 8) and below (3), it goes down first even though it was positioned to sweep up. The passenger at 7 watches it head away.

#### Great Solution: SCAN — continue until clear, then reverse (chosen)

Continue in the current direction servicing all stops, reverse only when no stops remain ahead. Same algorithm as OS disk scheduling.

Same scenario: sweep up 5→7→8 (stops), reverse, down to 3 = 8 floors traveled — one more floor than nearest-first, yet better. The win isn't absolute distance; it's **minimizing direction changes and matching passenger intuition**: the person at floor 7 sees the elevator coming and it actually arrives. SCAN prevents "thrashing" in busy buildings by batching pickups per sweep — predictable, smooth, optimal for concurrent request patterns.

**Edge cases to handle:** empty requests (go IDLE); stopped at a floor (remove request, maybe reverse or idle); IDLE with requests (pick a direction first); no requests ahead (reverse).

Full pseudocode:

```
step()
    // Case 1: Nothing to do
    if requests.isEmpty()
        direction = IDLE
        return

    // Case 2: If idle, pick a direction based on nearest request
    if direction == IDLE
        nearest = null; minDistance = MAX
        for req in requests
            distance = abs(req.getFloor() - currentFloor)
            if distance < minDistance ||
               (distance == minDistance && (nearest == null || req.getFloor() < nearest.getFloor()))
                minDistance = distance
                nearest = req
        direction = (nearest.getFloor() > currentFloor) ? UP : DOWN

    // Case 3: Check if we should stop at current floor (direction-aware)
    pickupType = (direction == UP) ? PICKUP_UP : PICKUP_DOWN
    pickupRequest = Request(currentFloor, pickupType)
    destinationRequest = Request(currentFloor, DESTINATION)
    if requests.contains(pickupRequest) || requests.contains(destinationRequest)
        requests.remove(pickupRequest)
        requests.remove(destinationRequest)
        // Note: If Request(currentFloor, PICKUP_DOWN) exists but we're going UP,
        // it survives and is serviced on the return trip going DOWN. Correct:
        // we only pick up passengers going our direction.
        if requests.isEmpty()
            direction = IDLE
        return  // we stopped this tick, don't move

    // Case 4: Reverse if no requests ahead
    if !hasRequestsAhead(direction)
        direction = (direction == UP) ? DOWN : UP
        return  // don't move this tick; next tick checks for stops

    // Case 5: Move one floor
    if direction == UP        currentFloor++
    else if direction == DOWN currentFloor--

hasRequestsAhead(dir)
    for request in requests
        if dir == UP && request.getFloor() > currentFloor  return true
        if dir == DOWN && request.getFloor() < currentFloor return true
    return false
```

Why each case matters:

1. **Nothing to do** — without it, an idle elevator would drift.
2. **Pick direction if idle** — deterministic tiebreak (nearest, then lowest floor). **Never use `requests.iterator().next()` on a HashSet** — iteration order is non-deterministic, making the simulation unreproducible and undebuggable.
3. **Stopping** — after removing a request, go IDLE if empty; either way `return` — **don't move on the tick you stop**. Forgetting the return is a common bug.
4. **Reversal** — return without moving so the next tick can check for a stop at the current floor in the new direction.
5. **Move** one floor.

Key insight — stopping vs. traveling:
- **Stopping is direction-aware**: going UP, stop only for PICKUP_UP and DESTINATION.
- **Traveling is not**: `hasRequestsAhead` counts ANY request regardless of type — head toward all requests even if you won't stop until you reverse. Example: at floor 4 going UP with {6: PICKUP_DOWN, 8: DESTINATION} — the elevator *passes* floor 6, stops at 8, reverses, then picks up floor 6 going DOWN. Not a bug.

Boundary floors (0 and 9) need **no special cases** — `hasRequestsAhead` naturally returns false at the top/bottom and Case 4 reverses. Hardcoding "if currentFloor == 9 then direction = DOWN" is a common mistake that introduces bugs (it can force a reversal even when there's a stop at floor 9 itself).

```
addRequest(request)
    if request.getFloor() < 0 || request.getFloor() > 9
        return false
    if request.getFloor() == currentFloor
        return true  // already here; treat as no-op
    return requests.add(request)   // Set dedupes via Request.equals (floor + type)
```

### Verification — tick-by-tick trace

Elevator at floor 3, going UP, requests {Request(5, PICKUP_UP), Request(7, DESTINATION)}:

```
Tick 0: floor=3, UP  - not a stop, move up
Tick 1: floor=4, UP  - not a stop, move up
Tick 2: floor=5, UP  - Request(5, PICKUP_UP) found! Remove. Still requests ahead, stay UP. Don't move (just stopped)
Tick 3: floor=5, UP  - move up
Tick 4: floor=6, UP  - move up
Tick 5: floor=7, UP  - Request(7, DESTINATION) found! Remove. Empty -> IDLE. Don't move
Tick 6: floor=7, IDLE - stay idle
```

Then someone on floor 2 presses DOWN → `requestElevator(2, DOWN)` adds Request(2, PICKUP_DOWN):

```
Tick 7: floor=7, IDLE -> nearest request is 2 (<7) so direction=DOWN; requests ahead -> move down
Tick 8: floor=6, DOWN - move down
Tick 9: floor=5, DOWN - move down
...continues to floor 2...
```

The elevator doesn't move until tick 7, after receiving the new request — the IDLE state is crucial.

### Complete Code Implementation (Python reference)

```python
from enum import Enum

class Direction(Enum):
    UP = 1
    DOWN = 2
    IDLE = 3

class Elevator:
    def __init__(self):
        self.current_floor = 0
        self.direction = Direction.IDLE
        self.requests = set()

    def add_request(self, request):
        if request.get_floor() < 0 or request.get_floor() > 9:
            return False
        if request.get_floor() == self.current_floor:
            return True
        if request in self.requests:
            return False
        self.requests.add(request)
        return True

    def step(self):
        if not self.requests:
            self.direction = Direction.IDLE
            return

        if self.direction == Direction.IDLE:
            # Find nearest request to establish initial direction (deterministic)
            nearest = None
            min_distance = float('inf')
            for req in self.requests:
                distance = abs(req.get_floor() - self.current_floor)
                if distance < min_distance or (distance == min_distance and
                        (nearest is None or req.get_floor() < nearest.get_floor())):
                    min_distance = distance
                    nearest = req
            self.direction = Direction.UP if nearest.get_floor() > self.current_floor else Direction.DOWN

        pickup_type = RequestType.PICKUP_UP if self.direction == Direction.UP else RequestType.PICKUP_DOWN
        pickup_request = Request(self.current_floor, pickup_type)
        destination_request = Request(self.current_floor, RequestType.DESTINATION)

        if pickup_request in self.requests or destination_request in self.requests:
            self.requests.discard(pickup_request)
            self.requests.discard(destination_request)
            if not self.requests:
                self.direction = Direction.IDLE
            return

        if not self.has_requests_ahead(self.direction):
            self.direction = Direction.DOWN if self.direction == Direction.UP else Direction.UP
            return

        if self.direction == Direction.UP:
            self.current_floor += 1
        elif self.direction == Direction.DOWN:
            self.current_floor -= 1

    def has_requests_ahead(self, dir):
        for request in self.requests:
            if dir == Direction.UP and request.get_floor() > self.current_floor:
                return True
            if dir == Direction.DOWN and request.get_floor() < self.current_floor:
                return True
        return False

    def has_requests_at_or_beyond(self, floor, dir):
        for request in self.requests:
            if dir == Direction.UP and request.get_floor() >= floor:
                if request.get_type() in (RequestType.PICKUP_UP, RequestType.DESTINATION):
                    return True
            if dir == Direction.DOWN and request.get_floor() <= floor:
                if request.get_type() in (RequestType.PICKUP_DOWN, RequestType.DESTINATION):
                    return True
        return False

    def get_current_floor(self):
        return self.current_floor

    def get_direction(self):
        return self.direction
```

## Extensibility (5 minutes, if time and level allow)

You typically won't implement these — explain how the classes adapt. Juniors often get none, mid-level one or two, seniors go deeper.

### 1. "How would you add priority floors or an express elevator?"

Simplest: add a priority field to `Request` + priority queue — but this breaks the sweep-in-one-direction behavior. Better: keep standard movement logic and add an `isExpress` flag. The controller's dispatch sends priority-floor requests to the express elevator; that elevator's `addRequest` rejects non-express floors. `Request` doesn't change at all. Presenting multiple options and weighing them is the key to senior+ design.

```
class ElevatorController:
    - elevators: List<Elevator>
    - expressElevator: Elevator  // NEW

class Elevator:
    - isExpress: bool
    - expressFloors: Set<int> = {0, 5, 9}

addRequest(request)
    ...validation...
    // NEW: Reject non-express floors if this is an express elevator
    if isExpress && !expressFloors.contains(request.getFloor())
        return false
    return requests.add(request)

// In dispatch:
selectBestElevator(request)
    if request.getFloor() in {0, 5, 9} && expressElevator.getDirection() == IDLE
        return expressElevator
    // ... normal selection
```

### 2. "How would you add undo to cancel a floor request?"

Since all requests flow through `addRequest`, add the inverse: `removeRequest(request)` that removes the Request from the set. Cancel before arrival → elevator skips it. Cancel after it already stopped → no-op (already gone). `step()` doesn't change. Works because state changes were already isolated to a few methods.

```
removeRequest(request)
    requests.remove(request)  // That's it
```

(Fun fact: real elevators don't allow undo — a lit button signals others that a stop is queued; clearing it would silently drop their requests.)

### 3. "What if multiple hall calls come in at the same time?" (concurrency)

Two problems: (a) two concurrent `requestElevator` calls both see the same elevator as idle and both dispatch to it — select + add must be atomic; (b) `step()` iterates/removes from the set while `addRequest` adds — concurrent modification.

Two answers, both acceptable:

- **Lock around both** `requestElevator` and `step()`. Simple, correct, but they block each other.
- **Concurrent queue**: `addRequest` enqueues to a thread-safe queue (e.g., Java `BlockingQueue`); at the start of each tick, `step()` drains the queue into the working set. Writers only touch the queue, `step` only the set — no lock, no contention. More elegant.

```
addRequest(request)
    pendingRequests.enqueue(request)  // thread-safe queue

step()
    while !pendingRequests.isEmpty()
        activeRequests.add(pendingRequests.dequeue())
    // all logic uses activeRequests
```

## What is Expected at Each Level?

### Junior
Model the basic entities (Elevator tracking position/direction, a controller coordinating). Nearest-elevator dispatch is fine. Basic up/down movement; hints allowed for the "continue then reverse" pattern; inefficiency is OK as long as all floors get serviced eventually. Handle invalid floors. A working simulation (request, add destinations, step through time) meets expectations. No dispatch optimization or concurrency needed.

### Mid-level
SCAN-style "continue until clear, then reverse" implemented correctly with minimal hints. Clean state machine: IDLE / UP / DOWN with proper transitions. `step()` handles the subtle cases — no move on the stop tick, reversal check after removing a request, IDLE when empty. Reasonable dispatch: recognize the naive nearest-elevator flaws and discuss improvements (full priority-tier not required). Clear separation: controller coordinates, elevator moves itself. On extensibility, identify where changes live — e.g., hall-call direction handling changes the requests data structure, not the movement algorithm.

### Senior
Ask the simulation-vs-hardware question upfront. Tight entity design: stateless coordinator, well-encapsulated movement. Movement handles edge cases unprompted: boundary floors, stop-and-reverse on the same floor, going idle. Dispatch: priority-tier approach or equally sophisticated, with reasoning about why penalty scores are hacky. Proactively mention the "requests don't extend past the floor" limitation. Discuss tradeoffs fluently: immediate dispatch vs. request queuing, floor-only vs. floor+direction requests, simple vs. predictive selection. Sketch express elevators / priority floors without restructuring.

## Key Design Patterns & Principles

- **Strategy pattern** — pluggable `selectBestElevator` dispatch strategies (wait time vs. energy efficiency) behind one interface.
- **State machine** — Direction enum (UP/DOWN/IDLE) with explicit, clean transitions in `step()`.
- **Encapsulation / separation of concerns** — controller coordinates, elevator owns movement; movement details never leak upward.
- **Type safety over runtime validation** — `RequestType` for hall calls instead of a reusable `Direction` that admits IDLE.
- **Avoid speculative abstraction** — no `IRequestHandler` interface just because two method signatures look alike; interfaces are for real polymorphism.
- **Determinism in simulations** — never rely on HashSet iteration order; use explicit tiebreakers.
- **SCAN algorithm** — same principle as OS disk scheduling; optimize for predictability and minimal reversals, not raw distance.
