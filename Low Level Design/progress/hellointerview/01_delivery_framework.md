# Delivery Framework for Low-Level Design Interviews

**Source:** https://www.hellointerview.com/learn/low-level-design/in-a-hurry/delivery

## Why a Framework?

LLD interviews move fast: roughly **~35 minutes** to clarify requirements, define the object model, design class APIs, and walk through core logic. Most candidates lose points from poor time management, not lack of knowledge.

**Predictable failure modes:**
- Diving straight into code and getting bogged down in edge cases before the interviewer understands your structure.
- Moving too slowly through setup, defining every tiny detail, then running out of time before showing any meaningful design.

The framework gives you a clear sequence and pacing: what to cover first, next, and how long each section should take. It keeps you grounded when nerves kick in.

**Important:** If the interviewer pulls you off the framework with questions or extensions, follow their lead. Don't fight the interviewer — gently guide the interview back to cover the important bits.

## The Framework at a Glance

| Step | Time |
|---|---|
| 1. Requirements | ~5 min |
| 2. Entities & Relationships | ~3 min |
| 3. Class Design | ~10–15 min |
| 4. Implementation | ~10 min |
| 5. Extensibility | ~5 min (if time/level allow) |

---

## 1) Requirements (~5 minutes)

Interviews start with an intentionally minimal one-line prompt:
- "Design Tic Tac Toe."
- "Design a parking lot system where cars are assigned to spots as they pull in."
- "Design a coffee machine that dispenses coffee and makes espresso."

Your job: turn the prompt into a spec you can design around. Spend the first minute or two asking questions to make the prompt unambiguous.

**Question themes to prime your thinking (work down this list):**
- **Primary capabilities** — What operations must the system support?
- **Rules and completion** — What conditions define success, failure, or when the system stops or transitions state?
- **Error handling** — How should the system respond to invalid inputs or actions?
- **Scope boundaries** — What's *in* scope (core logic, business rules) vs. explicitly *out* (UI, storage, networking, concurrency, extensibility)?

These themes work across every domain — games, devices, workflows, transaction systems.

Confirm the resulting spec with your interviewer. **Write down out-of-scope items too** — it keeps the design focused and prevents scope creep.

**Example — Tic Tac Toe requirements on the whiteboard:**

```
Requirements:
1. Two players alternate placing X and O on a 3x3 grid.
2. A player wins by completing a row, column, or diagonal.
3. The game ends in a draw if all nine cells are filled with no winner.
4. Invalid moves should be rejected (placing on an occupied cell, acting after the game is over).
5. The system should provide a way to query current game state and reset the game.

Out of Scope:
- UI/rendering layer
- AI opponent or move suggestions
- Networked multiplayer
- Variable board sizes (NxN grids)
- Undo/redo functionality
```

---

## 2) Entities and Relationships (~3 minutes)

Translate requirements into a few core entities with clean ownership boundaries. You're shaping the structure of the system before worrying about any one class.

### Identify Entities

Scan requirements and pull out the meaningful **nouns** — the "things" that clearly need to exist. Capture state and behavior that matter; don't model every word in the prompt.

**Simple filter:**
- If something **maintains changing state or enforces rules** → it likely deserves to be its own entity.
- If it's **just information attached to something else** → it's probably a field on another class.

This prevents the design from ballooning into micro-objects while still giving structure.

### Define Relationships

Think through how entities interact — this establishes the system's shape:
- Which entity is the **orchestrator** — the one driving the main workflow?
- Which entities **own durable state**?
- How do they depend on each other? (has-a, uses, contains)
- Where should specific rules logically live?

### Whiteboard Representation

Don't overthink it. A simple list of entities plus a few arrows showing ownership/usage is enough. **You're not drawing a full UML diagram.** Don't fixate on rigid notation — the whiteboard exists to communicate. Simple boxes, arrows, and labels work fine.

**Tic Tac Toe example:**

```
Entities:
- Game
- Board
- Player

Relationships:
- Game -> Board
- Game -> Player (2x)
```

---

## 3) Class Design (~10–15 minutes)

Turn each entity into an outline of an actual class: what it **stores** and what it **does**. Work **top-down**: start with the orchestrator (`Game` for Tic Tac Toe), then supporting entities (`Board`, `Player`, ...).

For each entity, answer two questions:
1. **State** — What does this class need to remember to enforce the requirements?
2. **Behavior** — What operations or queries does this class need to provide?

Tie both back to requirements to avoid guessing and avoid bloat.

### Deriving State from Requirements

For each entity, ask: Which requirements does it own? What must it keep in memory to satisfy them? Build a mental table: *Requirement → What this class must track.*

**Example for `Game`:**

| Requirement | What Game must track |
|---|---|
| "Two players alternate placing X and O on a 3x3 grid." | The two players, whose turn it is, and the Board |
| "The game ends when a player wins or the board is full." | Game state (in progress, won, draw) and the winner (if any) |

Whiteboard result:

```
Game – State:
- board: Board
- playerX: Player
- playerO: Player
- currentPlayer: Player
- state: GameState (IN_PROGRESS, WON, DRAW)
- winner: Player? (null if no winner)
```

### Deriving Behavior from Requirements

Ask what operations the outside world needs and which requirements they satisfy. Aim for a **small, focused API** where each method maps to a real action or question implied by the problem.

| Need from requirements | Method on Game |
|---|---|
| Players need to make moves | `makeMove(player, row, col) -> bool` |
| Ask whose turn it is | `getCurrentPlayer() -> Player` |
| Check game state | `getGameState() -> GameState` |
| See who won | `getWinner() -> Player?` |
| Inspect the board | `getBoard() -> Board` |

**Key principle: keep rules with the entity that owns the relevant state** (encapsulation, aka "Tell, Don't Ask"). Objects should manage their own state and expose behavior — not getters that force callers to make decisions.
- **Workflow/lifecycle rules** ("can this operation run right now?") → belong in the **orchestrator**.
- **Data-specific rules** ("is this cell already occupied?") → belong in the **entity that owns that data**.

This keeps APIs small and the design predictable — when something breaks, you know which class to check.

**Combined class outline:**

```
class Game:
  - board: Board
  - playerX: Player
  - playerO: Player
  - currentPlayer: Player
  - state: GameState (IN_PROGRESS, WON, DRAW)
  - winner: Player? (null if no winner)

  + makeMove(player, row, col) -> bool
  + getCurrentPlayer() -> Player
  + getGameState() -> GameState
  + getWinner() -> Player?
  + getBoard() -> Board
```

Don't get caught up in syntax — it doesn't matter. Use whatever notation is clear and close to your language of choice.

### What About UML Diagrams?

Hello Interview explicitly **does not use UML**:
- UML is outdated and rarely used in production. Modern engineers design in code — stubbed classes, interfaces in design reviews. (Microsoft removed UML tooling from Visual Studio in 2016 because usage had dropped to effectively zero.)
- UML was designed for an era when inspecting/running code was expensive; that tradeoff no longer holds.
- In an interview, its formality slows you down without adding clarity.

The simplified class notation above shows structure, relationships, and key methods without ceremony. If an interviewer explicitly asks for UML, **ask whether simplified class notation is acceptable** — usually it is.

---

## 4) Implementation (~10 minutes)

Implement the **major methods** of the classes you designed.

**Always ask your interviewer what level of detail they prefer.** Expectations vary:
- Most interviews: pseudo-code for the key methods.
- Some companies: near-complete code in a specific language.
- Others: just talk through the logic.

Focus on the most interesting methods — the ones that truly define system behavior. Unless specified otherwise, default to pseudo-code.

**Order of operations:**
1. **Happy path first** — walk the method linearly: inputs, sequence of steps, internal calls to other classes, return value / state changes. Let the interviewer see how the system actually moves.
2. **Edge cases second** — enumerate failure modes: invalid inputs, illegal operations, out-of-range values, calls that violate current system state. This demonstrates production-code thinking, not toy logic.

Then convert the verbal walkthrough into simple, indentation-based pseudo-code (or a real language if asked). **Use the language you use daily** — don't pick an unfamiliar language to please one interviewer; that backfires.

**Example (Tic Tac Toe):**

```
makeMove(player, row, col)
    if state != IN_PROGRESS
        return false
    if player != currentPlayer
        return false
    if !board.canPlace(row, col)
        return false

    board.placeMark(row, col, player.mark)

    if board.checkWin(row, col, player.mark)
        state = WON
        winner = player
    else if board.isFull()
        state = DRAW
    else
        currentPlayer = (player == playerX) ? playerO : playerX

    return true
```

Pick methods that show: how classes cooperate, how state transitions occur, how edge cases are handled cleanly, and how logic is isolated in the right classes. Interviewers usually tell you which methods to implement — follow their lead.

**Pattern pitfall:** Singleton, Factory, Builder, etc. can be impactful — but candidates **over-engineer by forcing patterns** far more often than they under-use them. Think before introducing a pattern.

### Verification: Walk Through a Specific Scenario

After implementing core methods, spend **1–2 minutes tracing a concrete example**. Goal: catch logical errors before the interviewer does, and demonstrate self-verification (many interviewers explicitly grade this).

Pick a simple but non-trivial scenario and step through it, showing:
- Initial state
- What happens on each operation
- How state changes at each step
- Edge cases or transitions (e.g., in-progress → completed)

```
Initial: board empty, currentPlayer = X
makeMove(X, 0, 0) → board[0][0] = X, currentPlayer = O
makeMove(O, 1, 1) → board[1][1] = O, currentPlayer = X
...
```

**Bugs this catches:**
- Forgot to switch turns
- Win detection doesn't trigger
- State transitions happen in the wrong order
- Edge-case handling breaks the flow

If you find a bug, **fix it on the spot** — a positive signal about your debugging ability, and far better than the interviewer finding it.

---

## 5) Extensibility (~5 minutes, if time and level allow)

Usually interviewer-led: they propose a twist to see whether your design can **evolve cleanly**, not whether you can bolt on hacks.

**Expectations by level:**
- **Junior:** little or no extensibility discussion.
- **Mid-level:** one, at most two, small follow-ups.
- **Senior:** several "what if we…" questions in a row.

The pattern is always the same: interviewer proposes a change; you show how your design handles it **without major restructuring**.

**Example — "How would you add undo functionality?"**

> "All state transitions flow through a single action method — `makeMove` in this case. To add undo, I'd introduce a command history stack. Each successful action records the previous state before modifying anything. An `undo()` method pops the stack, reverts to that state, and the rest of the system doesn't need to change."

This works because state mutations are isolated — the interviewer sees clean boundaries.

**Stay high level here.** You're not rewriting code; you're pointing to the parts of your design that make the change clean. The goal: show the initial design is extensible and robust — it handles natural follow-ups without falling apart or turning into a pile of special cases.
